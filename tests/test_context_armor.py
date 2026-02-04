#!/usr/bin/env python3
"""
Context-Armor Regression Tests (v2.1.1)

Validates Strike 1/2/3 behavior without generating large payloads.
Uses monkeypatching to simulate token counts.

Run: pytest tests/test_context_armor.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Import targets (adjust path if needed)
import sys
sys.path.insert(0, '..')

from router_gateway import (
    calculate_budget,
    context_guard_check,
    jit_compact,
    execute_with_silent_retry,
    CONTEXT_SAFETY_THRESHOLD,
    GEMINI_PRO_MODEL,
)


class TestStrike1PreFlightAudit:
    """Strike 1: >180K tokens forces Gemini Pro."""

    def test_threshold_constant(self):
        """Verify threshold is 180,000."""
        assert CONTEXT_SAFETY_THRESHOLD == 180_000

    def test_gemini_model_constant(self):
        """Verify Gemini model ID."""
        assert GEMINI_PRO_MODEL == "google/gemini-2.5-pro"

    @patch('router_gateway.calculate_budget')
    def test_force_gemini_above_180k(self, mock_budget):
        """Tokens > 180K should force Gemini Pro."""
        mock_budget.return_value = 185_000
        messages = [{"role": "user", "content": "test"}]
        
        model, overridden, result_msgs = context_guard_check(messages, "opus")
        
        assert model == GEMINI_PRO_MODEL
        assert overridden is True

    @patch('router_gateway.calculate_budget')
    def test_no_override_below_150k(self, mock_budget):
        """Tokens < 150K should not trigger any action."""
        mock_budget.return_value = 100_000
        messages = [{"role": "user", "content": "test"}]
        
        model, overridden, result_msgs = context_guard_check(messages, "opus")
        
        assert model == "opus"
        assert overridden is False


class TestStrike2SilentRetry:
    """Strike 2: Context overflow errors retry with Gemini."""

    @pytest.mark.asyncio
    async def test_retry_on_context_length_exceeded(self):
        """Error containing 'context_length_exceeded' triggers retry."""
        call_count = 0
        
        async def mock_call(messages, model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("context_length_exceeded: too many tokens")
            return "success"
        
        result = await execute_with_silent_retry(mock_call, [], "opus")
        
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_422_status(self):
        """Status code 422 triggers retry."""
        call_count = 0
        
        async def mock_call(messages, model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                err = Exception("Request failed")
                err.status_code = 422
                raise err
            return "success"
        
        result = await execute_with_silent_retry(mock_call, [], "opus")
        
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_400_status(self):
        """Status code 400 triggers retry."""
        call_count = 0
        
        async def mock_call(messages, model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                err = Exception("Bad request")
                err.status_code = 400
                raise err
            return "success"
        
        result = await execute_with_silent_retry(mock_call, [], "opus")
        
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_other_errors(self):
        """Non-overflow errors should propagate."""
        async def mock_call(messages, model):
            raise ValueError("Unrelated error")
        
        with pytest.raises(ValueError):
            await execute_with_silent_retry(mock_call, [], "opus")


class TestStrike3JITCompaction:
    """Strike 3: 150K-180K triggers JIT compaction."""

    @patch('router_gateway.calculate_budget')
    def test_compaction_triggered_at_160k(self, mock_budget):
        """Tokens between 150K-180K should trigger compaction."""
        mock_budget.return_value = 160_000
        messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
        
        model, overridden, result_msgs = context_guard_check(messages, "opus")
        
        assert model == "opus"
        assert overridden is False
        assert len(result_msgs) < len(messages)

    def test_compaction_ratio_30_percent(self):
        """JIT compaction summarizes oldest 30%."""
        messages = [{"role": "user", "content": f"message {i}"} for i in range(10)]
        
        compacted = jit_compact(messages)
        
        # 30% of 10 = 3 messages compacted into 1 summary
        # Result: 1 summary + 7 recent = 8 messages
        assert len(compacted) == 8
        assert "[Compacted History]" in compacted[0]["content"]

    def test_compaction_preserves_recent(self):
        """Recent 70% of messages should be preserved."""
        messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
        
        compacted = jit_compact(messages)
        
        # Last 7 messages should be preserved
        assert compacted[-1]["content"] == "msg9"
        assert compacted[-2]["content"] == "msg8"

    def test_no_compaction_under_4_messages(self):
        """Less than 4 messages should not be compacted."""
        messages = [{"role": "user", "content": "test"}] * 3
        
        compacted = jit_compact(messages)
        
        assert len(compacted) == 3


class TestCalculateBudget:
    """Token budget calculation."""

    def test_empty_messages(self):
        """Empty message list returns 0."""
        assert calculate_budget([]) == 0

    def test_basic_calculation(self):
        """Basic token estimation."""
        messages = [{"role": "user", "content": "Hello world"}]
        tokens = calculate_budget(messages)
        assert tokens > 0
        assert tokens < 100  # Sanity check


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
