# Testing Guide

## Prerequisites

```bash
pip install pytest pytest-asyncio
```

## Run All Tests

```bash
cd skills/smart-router
pytest tests/ -v
```

## Run Context-Armor Tests Only

```bash
pytest tests/test_context_armor.py -v
```

## Run Specific Strike Tests

```bash
# Strike 1: Pre-flight audit (>180K forces Gemini)
pytest tests/test_context_armor.py::TestStrike1PreFlightAudit -v

# Strike 2: Silent retry (422/400 errors)
pytest tests/test_context_armor.py::TestStrike2SilentRetry -v

# Strike 3: JIT compaction (150K-180K)
pytest tests/test_context_armor.py::TestStrike3JITCompaction -v
```

## Test Coverage

| Test Class | Strike | Validates |
|------------|--------|-----------|
| `TestStrike1PreFlightAudit` | 1 | >180K tokens forces Gemini Pro |
| `TestStrike2SilentRetry` | 2 | 422/400/413 triggers silent retry |
| `TestStrike3JITCompaction` | 3 | 150K-180K compacts oldest 30% |
| `TestCalculateBudget` | — | Token estimation logic |

## Test Design

Tests use `unittest.mock.patch` to simulate token counts without generating large payloads. See `tests/test_context_armor.py` for implementation details.
