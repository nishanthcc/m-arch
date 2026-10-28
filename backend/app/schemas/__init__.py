from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

# ----------------- GitHub & Snapshot Schemas -----------------
class GitHubImportRequest(BaseModel):
    repo_url: str = Field(..., description="HTTPS GitHub repository URL (e.g. https://github.com/owner/repo)")
    ref_name: Optional[str] = Field(None, description="Branch, tag, or commit SHA")
    access_token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token (PAT) for private repo; session only, never persisted")
    project_name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None

class GitHubImportJobResponse(BaseModel):
    id: str
    project_id: str
    importer_type: str
    status: str
    progress_percent: int
    status_message: str
    repo_url: str
    ref_name: Optional[str] = None
    resolved_commit_sha: Optional[str] = None
    files_accepted: int = 0
    files_skipped: int = 0
    total_size_bytes: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SourceSnapshotResponse(BaseModel):
    id: str
    project_id: str
    snapshot_type: str
    commit_sha: Optional[str] = None
    ref_name: Optional[str] = None
    repo_url: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    source_hash: str
    source_count: int
    total_size_bytes: int
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Project Schemas -----------------
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectUserContextUpdate(BaseModel):
    purpose: Optional[str] = None
    deployment_env: Optional[str] = None
    sensitive_data: Optional[str] = None
    intended_users: Optional[str] = None
    review_goals: Optional[str] = None

class ProjectProfileResponse(BaseModel):
    id: str
    project_id: str
    snapshot_id: str
    languages: Dict[str, Any] = {}
    frameworks: List[Dict[str, Any]] = []
    application_type: str = "Unknown"
    app_type_status: str = "inferred"
    likely_purpose: Optional[str] = None
    entrypoints: List[Dict[str, Any]] = []
    modules: List[Dict[str, Any]] = []
    services: List[Dict[str, Any]] = []
    routes: List[Dict[str, Any]] = []
    database_technologies: List[Dict[str, Any]] = []
    dependency_manifests: List[Dict[str, Any]] = []
    test_frameworks: List[Dict[str, Any]] = []
    deployment_config: List[Dict[str, Any]] = []
    architecture_graph: Dict[str, Any] = {}
    unsupported_technologies: List[Dict[str, Any]] = []
    user_context: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    source_count: int
    chunk_count: int
    indexing_metadata: Optional[Dict[str, Any]] = None
    current_snapshot_id: Optional[str] = None
    repo_url: Optional[str] = None
    current_commit_sha: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Source Schemas -----------------
class SourceResponse(BaseModel):
    id: str
    project_id: str
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    content_hash: str
    line_count: int
    snapshot_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SourceExcerptResponse(BaseModel):
    source_id: str
    file_path: str
    line_start: int
    line_end: int
    content: str

# ----------------- Evidence Schemas -----------------
class EvidenceItem(BaseModel):
    id: Optional[str] = None
    source_id: str
    display_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    section: Optional[str] = None
    excerpt: str
    evidence_type: str = "code_snippet"
    retrieval_method: str = "hybrid"
    score: Optional[float] = None
    content_hash: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- Finding Schemas -----------------
class FindingCreate(BaseModel):
    agent_id: str
    title: str
    explanation: str
    severity: Literal["critical", "high", "medium", "low", "informational"]
    category: str
    impact: str
    remediation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_interpretation: str
    verification_status: Literal[
        "tested", "runtime_confirmed", "static_analysis", 
        "inference", "manual_review_required", "not_tested"
    ]
    limitations: Optional[str] = None
    manual_review_required: bool = False
    evidence_items: List[EvidenceItem] = []

class FindingResponse(BaseModel):
    id: str
    review_id: str
    project_id: str
    agent_id: str
    title: str
    explanation: str
    severity: str
    category: str
    impact: str
    remediation: str
    confidence: float
    confidence_interpretation: str
    verification_status: str
    limitations: Optional[str] = None
    manual_review_required: bool
    first_seen_at: datetime
    evidence_items: List[EvidenceItem] = []

    class Config:
        from_attributes = True

# ----------------- Agent & Task Schemas -----------------
class AgentCard(BaseModel):
    agent_id: str
    name: str
    role: str
    description: str
    endpoint: str
    skills: List[str]
    allowed_mcp_tools: List[str]
    configured_provider: str
    configured_model: str
    status: Literal["available", "busy", "unavailable", "paused", "misconfigured"]
    current_state: Literal["available", "busy", "unavailable", "paused", "misconfigured"] = "available"
    a2a_connectivity: str = "connected"
    prompt_version: str = "1.1.0"
    actual_model_used: Optional[str] = None
    fallback_history: List[str] = []
    last_task_time: Optional[str] = None
    last_error: Optional[str] = None

class AgentTaskResponse(BaseModel):
    id: str
    review_id: str
    agent_id: str
    task_name: str
    status: Literal["waiting", "running", "completed", "failed", "timed_out"]
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    execution_time_seconds: float = 0.0
    tools_called: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_version: Optional[str] = None
    prompt_hash: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- Review Schemas -----------------
class ReviewCreate(BaseModel):
    project_id: str
    question: str = "Is this project ready for production?"
    scope: Literal["full", "security_only", "code_only", "architecture", "supply_chain"] = "full"
    selected_agents: Optional[List[str]] = None
    provider_mode: Optional[Literal["Auto", "Groq", "Ollama", "Hybrid"]] = None

class ReviewResponse(BaseModel):
    id: str
    project_id: str
    question: str
    scope: str
    status: str
    provider_mode: str
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    fallback_occurred: bool
    summary: Optional[str] = None
    limitations: Optional[str] = None
    total_findings: int
    elapsed_seconds: float
    trace_metadata: Optional[Dict[str, Any]] = None
    source_snapshot_id: Optional[str] = None
    commit_sha: Optional[str] = None
    evidence_verification_summary: Optional[Dict[str, Any]] = None
    skipped_agents: Optional[List[Dict[str, Any]]] = None
    presentation_views: Optional[Dict[str, Any]] = None
    tasks: List[AgentTaskResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReviewReportResponse(BaseModel):
    review_id: str
    project_name: str
    question: str
    status: str
    commit_sha: Optional[str] = None
    source_snapshot_id: Optional[str] = None
    presentation_mode: str = "developer"
    summary: Optional[str] = None
    limitations: Optional[str] = None
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings: List[FindingResponse]
    agent_traces: List[AgentTaskResponse]
    evidence_verification_summary: Optional[Dict[str, Any]] = None
    presentation_views: Optional[Dict[str, Any]] = None
    markdown_report: str
    html_report: str

# ----------------- Provider & Settings Schemas -----------------
class ProviderStatus(BaseModel):
    name: Optional[str] = None
    available: bool
    configured: bool
    latency_ms: Optional[float] = None
    active_model: str
    error: Optional[str] = None
    installed_models: Optional[List[str]] = None
    model_available: Optional[bool] = None

    class Config:
        extra = "allow"

class ProvidersHealthResponse(BaseModel):
    mode: str
    primary_provider: str
    fallback_provider: str
    providers: Dict[str, ProviderStatus]

class SettingsUpdate(BaseModel):
    ai_mode: Optional[Literal["Auto", "Groq", "Ollama", "Hybrid"]] = None
    primary_provider: Optional[Literal["Groq", "Ollama"]] = None
    fallback_provider: Optional[Literal["Groq", "Ollama"]] = None
    groq_model: Optional[str] = None
    ollama_model: Optional[str] = None
    hybrid_policy: Optional[Dict[str, str]] = None
    rerank_enabled: Optional[bool] = None

# ----------------- Security Knowledge Schemas -----------------
class SecurityKnowledgeSourceCreate(BaseModel):
    id: str
    name: str
    organization: str
    canonical_url: str
    version_date: str
    license: Optional[str] = None
    coverage_category: str
    is_enabled: bool = True
    records: List[Dict[str, Any]] = []

class SecurityKnowledgeSourceResponse(BaseModel):
    id: str
    name: str
    organization: str
    canonical_url: str
    version_date: str
    license: Optional[str] = None
    record_count: int
    coverage_category: str
    is_enabled: bool
    source_type: str
    agent_ids: List[str]
    records: List[Dict[str, Any]]
    version_hash: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Evaluation Schemas -----------------
class EvaluationDatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_payload: List[Dict[str, Any]]

class EvaluationDatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sample_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class EvaluationRunCreate(BaseModel):
    dataset_id: str
    name: str
    provider_mode: Literal["Auto", "Groq", "Ollama", "Hybrid"] = "Auto"

class EvaluationRunResponse(BaseModel):
    id: str
    dataset_id: str
    name: str
    status: str
    provider_mode: str
    dataset_version: Optional[str] = "1.2.0"
    snapshot_id: Optional[str] = None
    metrics: Dict[str, Any]
    sample_results: List[Dict[str, Any]]
    execution_summary: Optional[Dict[str, Any]] = None
    elapsed_seconds: float
    created_at: datetime

    class Config:
        from_attributes = True
