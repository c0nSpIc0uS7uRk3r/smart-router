# Smart-Router v2.1.1 Release Notes

**Date:** 2026-02-04  
**Status:** Stable  
**License:** MIT

## Overview

v2.1.1 completes the Context-Armor implementation and adds operational protocols for gateway overflow prevention.

## Problems Solved

| Problem | Cause | Solution |
|---------|-------|----------|
| Context overflow errors (422/400) | Claude 200K limit exceeded | Pre-flight token audit; >180K forces Gemini Pro |
| Gateway saturation on large outputs | Unbounded chat responses | POINTER MODE: disk-first, metadata-only output |
| Session state lost on context reset | Chat history non-authoritative | Canonical state file: `JARVIS_PROJECT_STATE_2026.md` |
| sessions_spawn rejected model param | OpenClaw uses agentId | Updated executor.py to use agentId |
| Grok-2-latest returned 404 | API key lacks access | Switched to grok-3 |
| JIT compaction triggered too late | Single threshold | Two-tier: 150K (compact), 180K (force Gemini) |

## Key Features

### Context-Armor (Phase H/H+)
- **Pre-flight audit:** `calculate_budget()` estimates tokens before API call
- **150K threshold:** JIT compaction (summarize oldest 30%)
- **180K threshold:** Force pivot to Gemini Pro (1M context)
- **Silent retry:** Intercepts 422/400 errors, retries with Gemini automatically

### Semantic Routing (Phase G)
- Domain detection: SOFTWARE_ARCH, SECURITY, MEDICAL, CONCURRENCY, etc.
- Expertise scoring: 0-100 weighted scores per model per domain
- Mandatory routing: Medical→GPT-5, Terminal→Opus, Concurrency→Gemini
- Cross-provider fallback: opus → haiku → gemini-2.5-pro → gpt-5

### Operational Protocols
- **POINTER MODE:** Write to disk, output only filepath + word count + first/last lines
- **SAFE_EXPORT_V1:** Segmented steps, one responsibility each
- **COLD_BOOT_V1:** Recovery from context reset via canonical state file

## Configuration

```json
{
  "agents": {
    "list": [
      {"id": "grok", "model": {"primary": "xai/grok-3"}},
      {"id": "gemini", "model": {"primary": "google/gemini-2.5-pro"}},
      {"id": "flash", "model": {"primary": "google/gemini-2.5-flash"}},
      {"id": "gpt", "model": {"primary": "openai/gpt-5"}}
    ]
  }
}
```

## Thresholds

| Threshold | Action |
|-----------|--------|
| >150K tokens | JIT compaction (summarize oldest 30%) |
| >180K tokens | Force Gemini Pro |
| 422/400 error | Silent retry with Gemini Pro |
| Confidence <75% | HITL gate (Telegram notification) |

## Files Changed

- `router_gateway.py` — Context-Armor integration
- `semantic_router.py` — Domain detection engine
- `expert_matrix.json` — Feb 2026 benchmarks
- `executor.py` — agentId-based delegation
- `context_guard.py` — Token budgeting module
- `CHANGELOG.md` — Version history
- `README.md` — Updated documentation
