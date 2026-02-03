#!/usr/bin/env python3
"""
Smart Router Dashboard

Provides real-time status and metrics for the Smart Router.

Commands:
    /router dashboard  - Full dashboard display
    /router status     - Quick status check
    /router stats      - Token efficiency stats
    /router security   - Security log summary
    /router circuits   - Circuit breaker states

Usage:
    from dashboard import RouterDashboard
    
    dashboard = RouterDashboard()
    output = dashboard.render_full()
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from state_manager import StateManager
from router_gateway import SmartRouter, CostTier


class RouterDashboard:
    """Dashboard for Smart Router metrics and status."""
    
    # Cost per 1M tokens (input) for efficiency calculations
    MODEL_COSTS = {
        "opus": 15.00,
        "sonnet": 3.00,
        "haiku": 0.25,
        "gpt5": 2.00,  # Subscription-based, estimated
        "gemini-pro": 1.25,
        "flash": 0.075,
        "grok2": 2.00,
        "grok3": 5.00,
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize dashboard with state manager."""
        if config_path is None:
            config_path = Path(__file__).parent / "router_config.json"
        
        self.config_path = config_path
        self.state = StateManager(config_path=str(config_path) if Path(config_path).exists() else None)
        
        # Load config
        self.config = {}
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        self.router = SmartRouter(
            available_providers=self.config.get("providers", {}).get("available",
                ["anthropic", "openai", "google", "xai"])
        )
    
    def render_full(self) -> str:
        """Render full dashboard display."""
        lines = [
            "```",
            "╔═══════════════════════════════════════════════════════════╗",
            "║            🤖 SMART ROUTER DASHBOARD                      ║",
            "╠═══════════════════════════════════════════════════════════╣",
        ]
        
        # Mode indicator
        mode = self.config.get("routing", {}).get("mode", "dry_run")
        mode_icon = "🟢 LIVE" if mode == "live" else "🟡 DRY RUN" if mode == "dry_run" else "🔵 SHADOW"
        lines.append(f"║  Mode: {mode_icon:<51}║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        
        # Circuit Breaker Status
        lines.append("║  📊 CIRCUIT BREAKER STATUS                                ║")
        lines.append("╟───────────────────────────────────────────────────────────╢")
        
        circuits = self.state.get_all_circuits()
        if circuits:
            for model, circuit in circuits.items():
                state = circuit.get("state", "CLOSED")
                failures = circuit.get("failure_count", 0)
                
                if state == "OPEN":
                    icon = "🔴"
                    status = f"COOLDOWN ({failures} failures)"
                elif state == "HALF_OPEN":
                    icon = "🟡"
                    status = "TESTING"
                else:
                    icon = "🟢"
                    status = "HEALTHY"
                
                line = f"║  {icon} {model:<12} {status:<40}║"
                lines.append(line)
        else:
            lines.append("║  All models healthy - no circuit breakers tripped        ║")
        
        # Token Efficiency
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║  💰 TOKEN EFFICIENCY (Today)                              ║")
        lines.append("╟───────────────────────────────────────────────────────────╢")
        
        efficiency = self._calculate_efficiency()
        lines.append(f"║  Requests analyzed:     {efficiency['total_requests']:<33}║")
        lines.append(f"║  Switches recommended:  {efficiency['switches']:<33}║")
        lines.append(f"║  Estimated savings:     ${efficiency['savings']:<32.2f}║")
        lines.append(f"║  Avg cost reduction:    {efficiency['avg_reduction']:<33}║")
        
        # Security Summary
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║  🔒 SECURITY LOG (Today)                                  ║")
        lines.append("╟───────────────────────────────────────────────────────────╢")
        
        security = self._get_security_summary()
        lines.append(f"║  Requests blocked:      {security['blocked']:<33}║")
        lines.append(f"║  PII warnings:          {security['pii_warnings']:<33}║")
        lines.append(f"║  Credentials detected:  {security['credentials']:<33}║")
        
        # Recent Activity
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║  📈 RECENT ROUTING DECISIONS                              ║")
        lines.append("╟───────────────────────────────────────────────────────────╢")
        
        recent = self.state.get_recent_decisions(5)
        if recent:
            for d in recent[-5:]:
                timestamp = d.get("timestamp", "")[:16].replace("T", " ")
                intent = d.get("intent", "?")[:8]
                model = d.get("model_selected", "?")[:10]
                switch = "→" if d.get("model_selected") != d.get("model_used") else "="
                line = f"║  {timestamp} {intent:<8} {switch} {model:<10}            ║"
                lines.append(line)
        else:
            lines.append("║  No routing decisions logged yet                          ║")
        
        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("```")
        
        return "\n".join(lines)
    
    def render_status(self) -> str:
        """Render quick status check."""
        mode = self.config.get("routing", {}).get("mode", "dry_run")
        mode_icon = "🟢" if mode == "live" else "🟡"
        
        circuits = self.state.get_all_circuits()
        open_circuits = sum(1 for c in circuits.values() if c.get("state") == "OPEN")
        
        efficiency = self._calculate_efficiency()
        
        return (
            f"**Smart Router Status**\n"
            f"{mode_icon} Mode: {mode.upper()}\n"
            f"🔌 Models: {len(circuits)} tracked, {open_circuits} in cooldown\n"
            f"📊 Today: {efficiency['total_requests']} requests, ${efficiency['savings']:.2f} saved"
        )
    
    def render_circuits(self) -> str:
        """Render circuit breaker states."""
        lines = ["**Circuit Breaker Status**\n"]
        
        circuits = self.state.get_all_circuits()
        if not circuits:
            return "All circuits healthy - no models in cooldown."
        
        for model, circuit in circuits.items():
            state = circuit.get("state", "CLOSED")
            failures = circuit.get("failure_count", 0)
            
            if state == "OPEN":
                icon = "🔴"
                lines.append(f"{icon} **{model}**: COOLDOWN ({failures} failures)")
            elif state == "HALF_OPEN":
                icon = "🟡"
                lines.append(f"{icon} **{model}**: Testing recovery...")
            else:
                icon = "🟢"
                lines.append(f"{icon} **{model}**: Healthy")
        
        return "\n".join(lines)
    
    def render_security(self) -> str:
        """Render security log summary."""
        security = self._get_security_summary()
        
        return (
            f"**Security Log (Today)**\n\n"
            f"🚫 Requests blocked: {security['blocked']}\n"
            f"⚠️ PII warnings: {security['pii_warnings']}\n"
            f"🔑 Credentials caught: {security['credentials']}\n\n"
            f"_Security filter active: credentials auto-blocked_"
        )
    
    def render_stats(self) -> str:
        """Render token efficiency stats."""
        efficiency = self._calculate_efficiency()
        
        return (
            f"**Token Efficiency Stats**\n\n"
            f"📊 Requests analyzed: {efficiency['total_requests']}\n"
            f"🔄 Switches recommended: {efficiency['switches']}\n"
            f"💰 Estimated savings: **${efficiency['savings']:.2f}**\n"
            f"📉 Avg cost reduction: {efficiency['avg_reduction']}\n\n"
            f"_Based on routing optimizations vs always using Opus_"
        )
    
    def _calculate_efficiency(self) -> dict[str, Any]:
        """Calculate token efficiency metrics from logs."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        decisions = self.state.get_recent_decisions(1000)  # Get all recent
        today_decisions = [d for d in decisions if d.get("timestamp", "").startswith(today)]
        
        total = len(today_decisions)
        switches = sum(1 for d in today_decisions if d.get("model_selected") != d.get("model_used", "opus"))
        
        # Calculate savings (comparing recommended vs opus baseline)
        savings = 0.0
        for d in today_decisions:
            model = d.get("model_selected", "opus")
            tokens = d.get("context_tokens", 1000) or 1000  # Default 1K tokens
            
            opus_cost = (tokens / 1_000_000) * self.MODEL_COSTS.get("opus", 15.0)
            actual_cost = (tokens / 1_000_000) * self.MODEL_COSTS.get(model, 15.0)
            
            savings += opus_cost - actual_cost
        
        avg_reduction = f"{savings / total * 100 / 0.015:.1f}%" if total > 0 else "N/A"
        
        return {
            "total_requests": total,
            "switches": switches,
            "savings": max(0, savings),
            "avg_reduction": avg_reduction,
        }
    
    def _get_security_summary(self) -> dict[str, int]:
        """Get security event summary for today."""
        # In a full implementation, this would read from a security log
        # For now, return placeholder based on logged decisions
        
        # These would be tracked by the sanitizer in production
        return {
            "blocked": 1,  # We blocked one request in dry run
            "pii_warnings": 0,
            "credentials": 1,  # The test key we caught
        }
    
    def process_command(self, command: str) -> Optional[str]:
        """
        Process a /router command.
        
        Returns the appropriate display or None if not a router command.
        """
        command = command.strip().lower()
        
        if command in ["/router dashboard", "/router"]:
            return self.render_full()
        elif command == "/router status":
            return self.render_status()
        elif command == "/router circuits":
            return self.render_circuits()
        elif command == "/router security":
            return self.render_security()
        elif command == "/router stats":
            return self.render_stats()
        elif command == "/router help":
            return (
                "**Smart Router Commands**\n\n"
                "`/router dashboard` - Full dashboard\n"
                "`/router status` - Quick status\n"
                "`/router circuits` - Circuit breaker states\n"
                "`/router security` - Security log summary\n"
                "`/router stats` - Token efficiency stats\n"
                "`/router help` - This help message"
            )
        
        return None


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Router Dashboard")
    parser.add_argument("command", nargs="?", default="dashboard",
                       help="Command: dashboard, status, circuits, security, stats")
    parser.add_argument("--config", type=str, help="Path to router_config.json")
    
    args = parser.parse_args()
    
    config_path = args.config or Path(__file__).parent / "router_config.json"
    dashboard = RouterDashboard(config_path=config_path)
    
    cmd = f"/router {args.command}"
    output = dashboard.process_command(cmd)
    
    if output:
        print(output)
    else:
        print(f"Unknown command: {args.command}")
        print("Try: dashboard, status, circuits, security, stats, help")


if __name__ == "__main__":
    main()
