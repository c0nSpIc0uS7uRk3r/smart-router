# Postmortem: Gateway Overflow (v2.1.1)

**Date:** 2026-02-04  
**Severity:** High (session disruption)  
**Status:** Resolved

## Symptoms

- Chat responses truncated or failed mid-output
- Gateway saturated despite model context being under limits
- Mismatch between model brain (200K tokens) and Telegram gateway pipe (narrow)

## Root Cause

Phase H Context-Armor protects the **model's context window** (150K/180K thresholds), but does not protect the **chat gateway output pipe**.

Contributing factors:
- Telegram gateway has narrow output bandwidth
- Conversation history re-sent with each turn
- Large synthesis requests (MEMORY.md, project state) exceeded gateway capacity
- Model attempted to output full file contents inline

## Fix

1. **POINTER MODE**: Write to disk first, output only metadata (filepath, word count, first/last N lines)
2. **Staged Export**: Break large tasks into steps (1/4, 2/4, etc.)
3. **SYNC_POINTER.txt**: Canonical identity pointer for recovery
4. **reset_context**: Clean session restart protocol

## Operational Pattern

- **STOP / NEXT**: Complete one step, halt, await explicit continuation
- **One responsibility per step**: Never combine read + large output
- **Verify before commit**: Confirm file contents via pointer before git operations
- **PRE-FLIGHT**: Estimate output size; if >300 tokens, switch to POINTER MODE

## Verification

| Test | Result |
|------|--------|
| `test_pointer.txt` creation | ✓ Pointer output only |
| Staged export (1/4..4/4) | ✓ Each step isolated |
| `JARVIS_PROJECT_STATE_2026.md` | ✓ 508 words, pointer output |
| Clean reset acknowledged | ✓ Identity recovered from pointer |

## Security Note

Static analysis (ClawHub Sentinel) treats all code as text:
- No execution of scanned code
- No function calls or imports
- Pattern matching only (regex, string search)
- Safe for untrusted skill inspection
