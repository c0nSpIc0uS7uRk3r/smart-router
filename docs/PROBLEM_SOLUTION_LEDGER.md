# Problem-Solution Ledger

## Phase H: Context-Armor

### Strike 1: Pre-Flight Token Audit

| Field | Value |
|-------|-------|
| **Challenge** | Context overflow errors (422/400) crashed requests |
| **Cause** | Payloads exceeded Claude's 200K limit without detection |
| **Fix** | Pre-flight `calculate_budget()` checks tokens before API call; >180K forces Gemini |
| **Files** | `router_gateway.py` (L49, L95), `context_guard.py` (L81) |
| **Verify** | `grep "CONTEXT_SAFETY_THRESHOLD" router_gateway.py` |

### Strike 2: Silent Retry

| Field | Value |
|-------|-------|
| **Challenge** | 422 errors surfaced to user, breaking experience |
| **Cause** | No error interception for context overflow responses |
| **Fix** | `execute_with_silent_retry()` catches overflow errors, retries with Gemini |
| **Files** | `router_gateway.py` (L138-165), `context_guard.py` (L363) |
| **Verify** | `grep -n "422" router_gateway.py context_guard.py` |

### Strike 3: JIT Compaction

| Field | Value |
|-------|-------|
| **Challenge** | Payloads near limit caused unpredictable failures |
| **Cause** | No preventative action in 150K-180K range |
| **Fix** | `jit_compact()` summarizes oldest 30% when 150K-180K |
| **Files** | `router_gateway.py` (L100-130) |
| **Verify** | `grep -n "jit_compact\|150_000" router_gateway.py` |

## Operational Protocols

### POINTER MODE Workflow

| Field | Value |
|-------|-------|
| **Challenge** | Gateway overflow on large chat outputs |
| **Cause** | Unbounded text responses saturated narrow pipe |
| **Fix** | Write to disk first; output only filepath, word count, first/last lines |
| **Files** | `memory/JARVIS_PROJECT_STATE_2026.md`, `memory/SYNC_POINTER.txt` |
| **Verify** | Protocol definition in session directives |

### agentId Executor Fix

| Field | Value |
|-------|-------|
| **Challenge** | `sessions_spawn` rejected model parameter |
| **Cause** | OpenClaw uses `agentId`, not raw model names |
| **Fix** | Updated `executor.py` to use `AGENT_IDS` dict and `agentId` param |
| **Files** | `executor.py` (L80, L284-293) |
| **Verify** | `grep -n "agentId" executor.py` |

### Grok Model Switch

| Field | Value |
|-------|-------|
| **Challenge** | Grok-2-latest returned 404 |
| **Cause** | API key lacks access to grok-2-latest |
| **Fix** | Switched to `xai/grok-3` |
| **Files** | `executor.py`, `~/.openclaw/openclaw.json` |
| **Verify** | `grep "grok-3" executor.py` |

## System Hardening

### CUPS Disabled

| Field | Value |
|-------|-------|
| **Challenge** | Port 631 open — unnecessary attack surface |
| **Cause** | CUPS installed by default on Ubuntu |
| **Fix** | `systemctl stop/disable snap.cups.cupsd snap.cups.cups-browsed` |
| **Files** | System services |
| **Verify** | `ss -tunlp | grep 631` returns empty |

### Fail2Ban Installed

| Field | Value |
|-------|-------|
| **Challenge** | SSH brute-force risk |
| **Cause** | No rate limiting on failed login attempts |
| **Fix** | Fail2Ban with sshd jail: bantime=1h, findtime=10m, maxretry=5 |
| **Files** | `/etc/fail2ban/jail.local` |
| **Verify** | `fail2ban-client status sshd` |
