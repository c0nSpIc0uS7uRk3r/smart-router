# Smart-Router v2.1.1 Verification

## Thresholds

| Threshold | Value | File | Location |
|-----------|-------|------|----------|
| JIT Compaction | 150,000 tokens | `router_gateway.py` | Line 101: `if tokens > 150_000` |
| Force Gemini | 180,000 tokens | `router_gateway.py` | Line 49: `CONTEXT_SAFETY_THRESHOLD = 180_000` |
| Context Override | 150,000 tokens | `expert_matrix.json` | `routing_rules.context_override_threshold` |
| HITL Gate | 75% confidence | `expert_matrix.json` | `routing_rules.confidence_threshold` |

## Gemini Model ID

| Alias | Full ID | File | Location |
|-------|---------|------|----------|
| gemini-pro | `google/gemini-2.5-pro` | `context_guard.py` | Line 81: `HIGH_CONTEXT_MODEL_ID` |
| flash | `google/gemini-2.5-flash` | `context_guard.py` | Line 65 |
| Fallback target | `google/gemini-2.5-pro` | `router_gateway.py` | Line 52: `GEMINI_PRO_MODEL` |

## Silent Retry

| Status Codes | File | Location |
|--------------|------|----------|
| 400, 413, 422 | `router_gateway.py` | Line 158: `if status in [400, 413, 422]` |
| 400, 413, 422 | `context_guard.py` | Line 363: `if error.status_code in [400, 413, 422]` |

| Error Patterns | File | Location |
|----------------|------|----------|
| `context_length_exceeded` | `router_gateway.py` | Line 152 |
| `context window` | `router_gateway.py` | Line 152 |
| `too many tokens` | `router_gateway.py` | Line 152 |
| `maximum context length` | `router_gateway.py` | Line 153 |
| `input too long` | `router_gateway.py` | Line 153 |

## JIT Compaction

| Parameter | Value | File | Location |
|-----------|-------|------|----------|
| Compaction ratio | 30% oldest | `router_gateway.py` | Line 118: `int(len(messages) * 0.3)` |
| Min messages | 4 | `router_gateway.py` | Line 114: `if len(messages) < 4` |
| Summary format | `[Compacted History]` | `router_gateway.py` | Line 127 |

## agentId Configuration

| Agent | Model | File | Location |
|-------|-------|------|----------|
| grok | `xai/grok-3` | `executor.py` | `AGENT_IDS` dict |
| gemini | `google/gemini-2.5-pro` | `executor.py` | `AGENT_IDS` dict |
| flash | `google/gemini-2.5-flash` | `executor.py` | `AGENT_IDS` dict |
| gpt | `openai/gpt-5` | `executor.py` | `AGENT_IDS` dict |

## Verification Status

- [x] Thresholds consistent across files
- [x] Gemini model ID standardized
- [x] Silent retry handles 422/400/413
- [x] Compaction ratio documented
- [x] agentId executor confirmed
