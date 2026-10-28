# M-ARCH Project Data

## Current Status

- Current version: 1.2.2
- Last updated: 2026-10-28
- Current focus: Dedicated Google Gemini Provider for Code Review Agent, Multi-Agent Architecture Review & Code Hygiene with Project-Adaptive Profiling, Evidence-Backed Visualizations, End-to-End Grounding Quality Gates, and 4 Canonical Presentation Modes.
- Overall state: Fully implemented, migrated, and verified across both backend (Python/FastAPI) and frontend (Next.js 14/TypeScript). Automated test suites (`test_gemini_code_agent.py`, `test_v1_2_improvements.py`, `test_pipeline.py`, `test_upload_pipeline.py`) pass 100%. Next.js production build (`npm run build`) compiles cleanly across all routes. Live health checks on Groq, Ollama, and Gemini active.

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
  - Persists all 4 presentation views (`developer`, `simple`, `professional`, `executive`) in `Review.presentation_views`.
- [x] **Export Engine (`backend/app/services/reports/exporter.py`):**
  - Generates Markdown and printable HTML reports tailored to the selected presentation mode without modifying canonical verified findings.
- [x] **Frontend Review View & Export Modal (`frontend/app/(dashboard)/reviews/[id]/page.tsx` & `ExportReportModal.tsx`):**
  - Added 4 presentation mode tabs switching display dynamically.
  - Added `skipped_agents` adaptation banner.
  - Updated export modal to allow downloading and printing in any presentation mode.

### 7. Database Integrity & Packaging
- [x] Database backed up to `backend/data/m_arch.db.backup_v1_1` (80.6 MB preserved).
- [x] Added SQLite columns dynamically in `session.py` (`user_context`, `skipped_agents`, `presentation_views`, `execution_summary`, etc.).
- [x] Sanitized `.env.example` at root and backend; verified no credentials in git or packaging.
- [x] Uploaded code remains isolated in `data/storage/` and is strictly inspected statically, never executed.

### 8. Universal Review Accuracy, Structured Presentation & Project-Scoped Evaluation (v1.2.1)
- [x] **Snapshot Evidence Grounding & Verification Gate (`backend/app/agents/verifier/agent.py`):**
  - Standardized finding status labels: `verified`, `partially_supported`, `unsupported`, `duplicate`, `not_verifiable`.
  - Exact file existence, line bounds, and disk excerpt matching with safe whitespace normalization and line drift correction.
  - Dependency vulnerability de-escalation: unpinned dependencies in manifests are calibrated to `low`/`informational` hygiene risks rather than critical security exploits.
  - Negative assertion filtering: non-findings ("Credentials Not Detected") are rejected or marked `unsupported`.
  - Cross-agent deduplication with attribution merging (`code_agent, dependency_agent`) and consolidated package listings.
  - Source coverage tracking: accurately counts `files_analyzed`, `files_skipped` (media, datasets, outputs), `files_unsupported`, and `total_files` with truthful coverage statements.
  - Real-time audit API `POST /api/v1/reviews/{id}/verify-audit` for on-demand re-auditing against authentic project snapshots on disk.
- [x] **Multi-Project Profiling Adaptation (`backend/app/services/profiling/profiler.py`):**
  - Added framework signatures for Machine Learning and Computer Vision: `Streamlit`, `PyTorch`, `OpenCV`, `Ultralytics YOLO`, `Pandas`, `Pillow`, `Scikit-Learn`, `NumPy`.
  - Provenance tracking: distinguishes purpose `detected from README.md`, `detected from docstring`, `inferred from entrypoint`, `user_supplied`, or `unknown`.
  - Verified across two meaningfully different project types: `project_complete` (FastAPI backend service) and `swethankarthik/pothole-detection` (ML/Vision Streamlit application).
- [x] **Zero Raw Markdown Structured Review UI (`frontend/components/ui/StructuredMarkdownViewer.tsx`):**
  - Semantic HTML renderer converting headings, lists, callouts, blockquotes, code blocks, and markdown tables into clean React components without raw symbols (`##`, `**`, `|`).
  - Redesigned `ReviewDetailPage` leading with project purpose, what was reviewed, main risks, next actions, what was not analyzed, detailed findings, and agent traces.
  - Tesla-dashboard inspired matte metric cards and focused visuals: finding counts by severity, specialist breakdown, source coverage, and citation accuracy.
  - Clean scan notice when zero findings are detected.
  - Interactive "Audit & Verify Snapshot" button.
- [x] **Project Catalog & Dedicated Detail Views (`frontend/app/(dashboard)/projects/`):**
  - Project Catalog filter tabs (`All Projects`, `Active Projects`, `Needs Attention`).
  - Safe automated test fixture cleanup endpoint (`DELETE /api/v1/projects/cleanup-tests`) and UI button.
  - Added dedicated "Reviews & History" tab in `ProjectDetailPage` isolating reviews belonging strictly to the selected project snapshot.
- [x] **Project-Scoped Evaluations (`frontend/app/(dashboard)/evaluations/page.tsx` & Backend):**
  - Added `project_id` query parameter to `GET /api/v1/evaluations/metrics`.
  - Top-level Project Selector allowing scoped inspection of individual projects alongside global system-wide aggregates.
  - Mathematical ratios displayed as `numerator/denominator (percentage)` (e.g. `18/22 (81.8%)`).
  - Empty state when insufficient review data exists for a project.

---

## Verification Evidence

All automated test suites executed and verified:

1. **`backend/tests/test_v1_2_improvements.py`**:
   - Test 1: Database Initialization & Column Migrations -> **Passed [OK]**
   - Test 2: Deterministic Project Profiling Engine (App Type, Routes, Graph) -> **Passed [OK]**
   - Test 3: Versioned Prompts Registry v1.2.0 (SHA-256 hashes) -> **Passed [OK]**
   - Test 4: Evidence Verifier Quality Gate v1.2.0 (Grounded vs ungrounded vs duplicate) -> **Passed [OK]**
   - Test 5: Orchestrator Clean Scan & 4 Presentation Modes -> **Passed [OK]**
   - Test 6: Report Exporter in Canonical Presentation Modes -> **Passed [OK]**
   - Test 7: Evaluator True Metrics & Terminal Statuses (0.5 completion rate) -> **Passed [OK]**
   - Test 8: Server Restart In-Flight Job Recovery (recovering stuck jobs) -> **Passed [OK]**
   - Test 9: Security & Packaging Sanity (.env.example sanitized) -> **Passed [OK]**
   - **Result: 9/9 Tests Passed (100%)**

2. **`backend/tests/test_pipeline.py`**:
   - URL validation, v1.1.0 prompts, source ingestion, FTS5/vector hybrid RAG, quality gate -> **Passed [OK] (10/10)**

3. **`backend/tests/test_upload_pipeline.py`**:
   - ZIP extraction, multipart folder preservation, corrupt archive rejection, binary rejection -> **Passed [OK]**

4. **Frontend Production Build (`cd frontend; npm run build`)**:
   - Compiled successfully with 0 errors across all 11 static/dynamic pages.

---

## Remaining Incomplete / User Actions Required

1. **Student Academic Details (`DOCUMENTATION.md`):**
   - Insert student name(s), registration/roll number(s), department, and project supervisor's designation in Section 1.
2. **Workstation Hardware Specifications (`DOCUMENTATION.md`):**
   - Insert host workstation CPU model, installed RAM, and GPU model in Section 17.
3. **Application UI Screenshots (`DOCUMENTATION.md`):**
   - Capture live screenshots of the new Architecture Graph, User Context Editor, 4 Presentation Mode tabs, and Evaluations page for final thesis submission.
