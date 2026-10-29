# M-ARCH Project Data

## Current Status

- Current version: 1.3.0
- Last updated: 2026-10-29
- Current focus: Strict Dual-Mode Persona Architecture (Technical Review vs Simplified Version), Granular Quantitative Scoring (1-10) with SVG Radar & Bar Charting, Topology Graph Extraction, Dedicated Google Gemini Provider for Code Review Agent, Multi-Agent Architecture Review & Code Hygiene with Project-Adaptive Profiling.
- Overall state: Fully implemented, migrated, and verified across both backend (Python/FastAPI) and frontend (Next.js 14/TypeScript). Automated test suites (`test_v1_3_dual_mode_and_scoring.py`, `test_gemini_code_agent.py`, `test_v1_2_improvements.py`, `test_pipeline.py`, `test_upload_pipeline.py`) pass 100%. Next.js production build (`npm run build`) compiles cleanly across all routes. Live health checks on Groq, Ollama, and Gemini active.

---

## Completed in Version 1.3.0 (2026-10-29)

### 1. Strict Dual-Mode Persona Architecture
- [x] **Discarded 4-Tab Model:** Fully replaced the legacy 4-tab model with a strict dual-mode presentation architecture:
  - `Technical Review`: Root cause analysis, exact file paths, line numbers, and explicit remediation steps. Pure code-centric technical vocabulary for senior engineers. Analogies, filler text, and introductory explanations strictly forbidden.
  - `Simplified Version`: Real-world impact, general concepts, plain everyday language, simple analogies. Architectural and code jargon (AST parsing, sanitization, dependency injection, exact file paths, line numbers, code snippets) strictly forbidden.
- [x] **Versioned Prompt `dual_mode_synthesis_v1_3` (`backend/app/prompts/registry.py`):**
  - Templatized with strict `# ROLE`, `# TARGET AUDIENCE MODE`, `# STRICT AUDIENCE CONSTRAINTS`, and `# RAW FINDINGS DATA`.
- [x] **Report Exporter Dual-Mode Formatting (`backend/app/services/reports/exporter.py`):**
  - Standardized `format_finding_item`, `generate_markdown_report`, and `generate_html_report`.
  - In `simplified_version`: Line references replaced with "General System Concept", evidence excerpts suppressed, sections formatted as "What is the problem?", "Why does it matter?", "How do we fix it?".
  - In `technical_review`: Formatted as "Issue Identified", "Technical Root Cause", "Specific Remediation Steps", authentic file:line references, and syntax-highlighted code excerpts.
  - Backward compatibility aliases preserved (`developer` -> `technical_review`, `simple` -> `simplified_version`).
- [x] **Export Report Modal (`frontend/components/reviews/ExportReportModal.tsx`):**
  - Redesigned with dual-mode selectors for `Technical Review` and `Simplified Version`.
- [x] **Review Detail Page (`frontend/app/(dashboard)/reviews/[id]/page.tsx`):**
  - Replaced legacy 4 tabs with 2 Dual-Mode buttons.
  - FindingCard dynamically adapts to active mode (displays Technical Root Cause & Remediation Steps vs Real-World Impact & Plain Fixes).

### 2. Evidence-Based Visualization & Quantitative Granular Scoring
- [x] **Quantitative Integer Scoring (1-10) (`backend/app/agents/verifier/agent.py`):**
  - Computes 6 granular code hygiene and architecture metrics (1-10 scale): `security_score`, `performance_score`, `maintainability_score`, `reliability_score`, `test_coverage_score`, and `overall_architecture_score`.
  - Stored in `review.evidence_verification_summary.quality_scores`.
- [x] **Bespoke Quality Radar & Bar Chart (`frontend/components/reviews/QualityRadarChart.tsx`):**
  - Pure React/TypeScript SVG 5-axis Radar chart and granular progress bars.
  - Zero external chart dependencies, zero hydration mismatch.
  - Strict matte dark theme (`#161616` background, `#222222` surface, `#2e2e2e` borders) with `Space Grotesk` and `Space Mono` typography.
- [x] **Native Architecture Graph Topology Extraction (`backend/app/prompts/registry.py` & `orchestrator/agent.py`):**
  - Registered `topology_extraction_v1_0` prompt outputting native `{nodes: [...], edges: [...]}` graph schema.
  - Implemented `orchestrator.extract_architecture_topology()` with deterministic fallbacks.
  - Traceable node evidence and provenance badges (`detected`, `inferred`, `unverified`).

### 3. Automated Test Verification (100% Passed)
- [x] **`backend/tests/test_v1_3_dual_mode_and_scoring.py`**:
  - Test 1: Registered Prompts v1.3.0 -> **Passed [OK]**
  - Test 2: Dual-Mode Persona Exporter Strict Constraints -> **Passed [OK]**
  - Test 3: Verifier Quantitative Granular Scoring (1-10) -> **Passed [OK]**
  - Test 4: Architecture Topology Extraction ({nodes, edges}) -> **Passed [OK]**
  - **Result: 4/4 Tests Passed (100%)**
- [x] **`backend/tests/test_gemini_code_agent.py`**:
  - 6/6 Dedicated Gemini Provider tests -> **Passed [OK] (100%)**
- [x] **`backend/tests/test_v1_2_improvements.py`**:
  - 9/9 Comprehensive verification tests -> **Passed [OK] (100%)**

---

## Completed in Version 1.2.2 (2026-10-28)

### 0. Dedicated Google Gemini Provider for Code Review Agent
- [x] **Dedicated Gemini Provider (`backend/app/providers/gemini.py`):**
  - Implements `BaseLLMProvider` using Google Generative Language API (`v1beta`).
  - Targeted high-performance free model `gemini-3.1-flash-lite` with automatic fallback to `gemini-flash-lite-latest` and `gemini-3.1-flash-lite-preview`.
  - Supports structured JSON schema generation (`responseMimeType: "application/json"`), prompt and candidate token counting, and credential sanitization via `redact_secrets()`.
  - Live connectivity health check returning round-trip latency and active model availability.
- [x] **Strict Role-Scoped Model Routing (`backend/app/providers/router.py`):**
  - Strictly routes requests with `agent_role="code_agent"` to the dedicated Gemini provider.
  - Strict isolation: All other agents (`security_agent`, `documentation_agent`, `dependency_agent`, `orchestrator`, `evidence_verifier`) remain exclusively routed to Groq (`openai/gpt-oss-120b`) and local Ollama (`qwen2.5-coder:3b`).
  - Graceful fallback: If Gemini reaches quota or transient error states, falls back to default router provider.
- [x] **Configuration & Secrets (`backend/app/core/config.py` & `backend/.env`):**
  - Added `GEMINI_API_KEY`, `GEMINI_MODEL`, and `GEMINI_BASE_URL` settings.
- [x] **UI Health Diagnostics (`frontend/app/(dashboard)/settings/page.tsx`, `frontend/components/layout/TopBar.tsx`):**
  - Exposes live Gemini status on `/settings` page alongside Groq and Ollama.
- [x] **Automated Verification (`backend/tests/test_gemini_code_agent.py`):**
  - 6/6 automated test checks passing for dedicated routing and isolation.

---

## Completed in Version 1.2.0 (2026-10-28)

### 1. Project-Adaptive Reviews & Profiling Engine
- [x] **Deterministic Project Profiler Engine (`backend/app/services/profiling/profiler.py`):**
  - Analyzes immutable source snapshots directly from code files without code execution.
  - Computes language distributions, line percentages, and byte weights.
  - Manifest parsing (`package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`).
  - Framework detection with versions (`FastAPI`, `Flask`, `Django`, `Express`, `React`, `Vue`, `Next.js`, `SQLAlchemy`, `Pytest`, `Jest`, `Docker`).
  - Deterministic route extractor for FastAPI/Flask (`@app.get`, `@router.post`) and Express (`app.get`, `router.post`).
  - Database usage signatures (`SQLite`, `PostgreSQL`, `MySQL`, `MongoDB`, `Redis`).
  - Test inventory inspection (frameworks, test directories, test file counts).
  - Deployment configuration detection (`Dockerfile`, `docker-compose`, GitHub Actions workflows).
  - Generates evidence-backed `ArchitectureGraph` with typed nodes (`application`, `framework`, `routes`, `database`, `testing`, `deployment`), relationships (`exposes_routes`, `uses_orm`, `orchestrates_service`), and source citations.
- [x] **Database Model & Table: `ProjectProfile` (`backend/app/db/models/__init__.py`):**
  - Stores immutable snapshot profile separately from historical snapshots.
  - Preserves user context (`purpose`, `deployment_env`, `sensitive_data`, `intended_users`, `review_goals`) in a dedicated column, isolating user-provided intent from deterministic detection.
- [x] **API Endpoints (`backend/app/api/v1/endpoints/sources.py`):**
  - `GET /api/v1/projects/{id}/profile`: Returns detected project profile with snapshot evidence.
  - `PATCH /api/v1/projects/{id}/context`: Updates user review goals without re-indexing.
  - `GET /api/v1/projects/{id}/architecture-graph`: Returns graph nodes, edges, and citations.

### 2. Ingestion & Indexing Pipeline Upgrades
- [x] **Unified Ingestion State Machine (`backend/app/services/ingestion/unified_pipeline.py`):**
  - Enforces 7-step persisted lifecycle: `queued -> validating -> extracting -> profiling -> snapshotting -> indexing -> ready`.
  - Idempotent retries: checks for existing snapshots, preventing duplicate chunks and vector stores.
  - Archive safety: defenses against ZIP bombs (max extraction ratio 100x), path traversal (`..` guards), unreadable binaries, and Windows path delimiters.
- [x] **Endpoints for Ingestion Controls (`backend/app/api/v1/endpoints/projects.py`):**
  - `POST /api/v1/projects/imports/{id}/cancel`: Immediately marks in-flight job cancelled.
  - `POST /api/v1/projects/{id}/ingest/retry`: Safely retries failed ingestion jobs.
- [x] **Non-Destructive GitHub Snapshot Refresh (`backend/app/services/ingestion/github_importer.py`):**
  - Refreshing repository snapshot marks prior snapshot `is_current = False` while preserving historical `Source` rows to maintain citation integrity for prior reviews.

### 3. Evidence-Based Project Architecture Visualization
- [x] **Interactive Graph & Matrix View (`frontend/components/projects/ArchitectureGraphView.tsx`):**
  - SVG node graph with distinct color coding for application roots, web routes, ORMs, databases, and deployment configs.
  - Node selection drawer showing exact source file path, line numbers, and extracted code excerpts.
  - Searchable evidence matrix fallback table for large codebases or low-resolution displays.
- [x] **Project Detail Redesign (`frontend/app/(dashboard)/projects/[id]/page.tsx`):**
  - Three distinct tabs: `Architecture & Profile`, `Source Inventory`, `Snapshot Provenance`.
  - Profile summary cards with detection badges (`detected`, `inferred`, `manifest`).
  - Accessible user context editor modal allowing domain adjustments.
  - Searchable, filterable source file inventory table with type filtering and excerpt previews.

### 4. Reliable Versioned Prompts & Evidence Verifier Quality Gate
- [x] **Prompt Registry v1.2.0 (`backend/app/prompts/registry.py`):**
  - Registered prompts: `orchestrator_synthesis_v1_2`, `code_specialist_v1_2`, `security_specialist_v1_2`, `documentation_specialist_v1_2`, `dependency_specialist_v1_2`, `evidence_verifier_v1_2`.
  - Enforces strict JSON schemas, exact file and line bounds, practical language-specific remediations, and rejection of hallucinated findings.
- [x] **Evidence Verifier Agent v1.2.0 (`backend/app/agents/verifier/agent.py`):**
  - Validates that cited file paths belong to the authentic source snapshot.
  - Checks line ranges exist and are within bounds.
  - Compares raw code excerpts against disk using safe whitespace normalization (`normalize_whitespace`).
  - Performs line drift correction if excerpt is authentic but shifted by minor edits.
  - Deduplicates cross-agent findings (e.g. Code Agent and Security Agent finding the same issue), merging agent attributions.
  - Rejects ungrounded or fabricated claims with descriptive reasons.

### 5. Mathematically Honest Evaluations & In-Flight Job Recovery
- [x] **Evaluation Runner Audit (`backend/app/services/evaluation/evaluator.py`):**
  - Removed hardcoded `completion_rate: 1.0` defaults.
  - Computes true completion rates, retrieval precision, and citation coverage based on evaluated samples.
  - Emits honest terminal states: `completed`, `completed_with_limitations`, `needs_attention`.
  - Implements bounded retries with exponential backoff for provider timeouts.
- [x] **System Metrics Audit (`backend/app/api/v1/endpoints/evaluations.py`):**
  - Replaced fallback calculations that implied 100% citation coverage with `None` ("not measured").
  - Evaluates actual partial failure recovery rates.
- [x] **Server Restart Recovery Service (`backend/app/db/recovery.py`):**
  - `recover_dangling_jobs()` executes on application startup lifespan.
  - Detects projects stuck in `indexing` -> marks `needs_attention`.
  - Detects reviews stuck in `running` -> marks `needs_attention` with limitation notes.
  - Detects tasks stuck in `running` -> marks `failed`.

### 6. Four Canonical Presentation Modes
- [x] **Multi-View Synthesis (`backend/app/agents/orchestrator/agent.py`):**
  - Adapts active specialists based on profile; records `skipped_agents` with explicit reasons.
  - Clean scans emit truthful notice: `"No critical static findings detected. The analyzed source files comply with baseline quality and security standards within the scope of static analysis."` along with explicit static limitations (cannot certify production readiness).
  - Persists all presentation views in `Review.presentation_views`.
- [x] **Export Engine (`backend/app/services/reports/exporter.py`):**
  - Generates Markdown and printable HTML reports tailored to the selected presentation mode without modifying canonical verified findings.

### 7. Database Integrity & Packaging
- [x] Database backed up to `backend/data/m_arch.db.backup_v1_1` (80.6 MB preserved).
- [x] Added SQLite columns dynamically in `session.py` (`user_context`, `skipped_agents`, `presentation_views`, `execution_summary`, etc.).
- [x] Sanitized `.env.example` at root and backend; verified no credentials in git or packaging.
- [x] Uploaded code remains isolated in `data/storage/` and is strictly inspected statically, never executed.

---

## Remaining Incomplete / User Actions Required

1. **Student Academic Details (`DOCUMENTATION.md`):**
   - Insert student name(s), registration/roll number(s), department, and project supervisor's designation in Section 1.
2. **Workstation Hardware Specifications (`DOCUMENTATION.md`):**
   - Insert host workstation CPU model, installed RAM, and GPU model in Section 17.
3. **Application UI Screenshots (`DOCUMENTATION.md`):**
   - Capture live screenshots of the new Architecture Graph, Quality Radar Chart, Dual-Mode Persona views, and Evaluations page for final thesis submission.
