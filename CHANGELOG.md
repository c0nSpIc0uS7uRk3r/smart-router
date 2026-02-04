# Changelog

All notable changes to Smart-Router are documented here.

## [2.1.1] - 2026-02-04

### Added
- POINTER MODE protocol for gateway overflow prevention
- Canonical project state file (`memory/JARVIS_PROJECT_STATE_2026.md`)
- SAFE_EXPORT_V1 protocol for segmented exports
- COLD_BOOT_V1 recovery protocol

### Changed
- Context-Armor thresholds documented: 150K (JIT compaction), 180K (force Gemini)
- Silent retry handler for 422/400 context overflow errors
- executor.py uses `agentId` instead of `model` parameter

### Fixed
- Grok agent switched from grok-2-latest (404) to grok-3
- Moltbook API endpoints corrected to /api/v1/*

## [2.1.0] - 2026-02-04

### Added
- Context-Armor (Phase H): Pre-flight token audit, JIT compaction, silent retry
- `context_guard.py` module for token budgeting
- `calculate_budget()` with tiktoken/heuristic fallback

### Changed
- Payloads >180K tokens force Gemini Pro automatically
- Payloads 150K-180K trigger preventative JIT compaction

## [2.0.0] - 2026-02-03

### Added
- Semantic domain detection (Phase G)
- Expertise-weighted scoring (0-100) based on Feb 2026 benchmarks
- `semantic_router.py` engine
- `expert_matrix.json` with model benchmarks
- Risk-based mandatory routing (Medical→GPT-5, Terminal→Opus, Concurrency→Gemini)
- HITL gate for low-confidence (<75%) routing
- Cross-provider fallback chain: opus → haiku → gemini-2.5-pro → gpt-5

### Changed
- Routing decisions now factor domain expertise, not just intent/complexity

## [1.0.0] - 2026-02-01

### Added
- Initial release
- Intent classification (CODE, ANALYSIS, CREATIVE, REALTIME, GENERAL)
- Complexity estimation (SIMPLE, MEDIUM, COMPLEX)
- Basic cost-tier routing
- Circuit breaker for model availability
- Input sanitization (API key blocking)
