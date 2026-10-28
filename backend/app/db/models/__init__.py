from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="created")  # "created", "indexing", "ready", "error"
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    indexing_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # v1.1.0 GitHub & Snapshot Fields
    current_snapshot_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    repo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    current_commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    sources: Mapped[List["Source"]] = relationship("Source", back_populates="project", cascade="all, delete-orphan")
    chunks: Mapped[List["Chunk"]] = relationship("Chunk", back_populates="project", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="project", cascade="all, delete-orphan")
    snapshots: Mapped[List["SourceSnapshot"]] = relationship("SourceSnapshot", back_populates="project", cascade="all, delete-orphan")
    import_jobs: Mapped[List["ProjectImportJob"]] = relationship("ProjectImportJob", back_populates="project", cascade="all, delete-orphan")
    profiles: Mapped[List["ProjectProfile"]] = relationship("ProjectProfile", back_populates="project", cascade="all, delete-orphan")

class SourceSnapshot(Base, TimestampMixin):
    __tablename__ = "source_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(50), default="github")  # "github", "zip_upload", "file_upload"
    commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ref_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    repo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    repo_owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    repo_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    project: Mapped["Project"] = relationship("Project", back_populates="snapshots")
    profile: Mapped[Optional["ProjectProfile"]] = relationship("ProjectProfile", back_populates="snapshot", uselist=False, cascade="all, delete-orphan")

class ProjectProfile(Base, TimestampMixin):
    __tablename__ = "project_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("source_snapshots.id", ondelete="CASCADE"), nullable=False)

    languages: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    frameworks: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    application_type: Mapped[str] = mapped_column(String(100), default="Unknown")
    app_type_status: Mapped[str] = mapped_column(String(50), default="inferred")  # detected, inferred, user_provided, unknown
    likely_purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entrypoints: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    modules: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    services: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    routes: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    database_technologies: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    dependency_manifests: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    test_frameworks: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    deployment_config: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    architecture_graph: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    unsupported_technologies: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    user_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship("Project", back_populates="profiles")
    snapshot: Mapped["SourceSnapshot"] = relationship("SourceSnapshot", back_populates="profile")

class ProjectImportJob(Base, TimestampMixin):
    __tablename__ = "project_import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    importer_type: Mapped[str] = mapped_column(String(50), default="github")
    status: Mapped[str] = mapped_column(String(50), default="pending")  # "pending", "validating", "fetching", "extracting", "indexing", "completed", "failed"
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    status_message: Mapped[str] = mapped_column(String(255), default="Job initialized")
    repo_url: Mapped[str] = mapped_column(String(512), nullable=False)
    ref_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolved_commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    files_accepted: Mapped[int] = mapped_column(Integer, default=0)
    files_skipped: Mapped[int] = mapped_column(Integer, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, default=0)
    chunks_created: Mapped[int] = mapped_column(Integer, default=0)
    snapshot_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    skipped_details: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="import_jobs")

class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), default="code")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    snapshot_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="sources")
    chunks: Mapped[List["Chunk"]] = relationship("Chunk", back_populates="source", cascade="all, delete-orphan")

class Chunk(Base, TimestampMixin):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, default=1)
    end_line: Mapped[int] = mapped_column(Integer, default=1)
    section_heading: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="chunks")
    source: Mapped["Source"] = relationship("Source", back_populates="chunks")

class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(50), default="full")  # "full", "security_only", "code_only", "architecture"
    status: Mapped[str] = mapped_column(String(50), default="pending")  # "pending", "running", "completed", "failed", "partial"
    provider_mode: Mapped[str] = mapped_column(String(50), default="Auto")
    provider_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fallback_occurred: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    elapsed_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    trace_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    # v1.1.0 Snapshot & Evidence Verifier linkage
    source_snapshot_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence_verification_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    skipped_agents: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    presentation_views: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship("Project", back_populates="reviews")
    tasks: Mapped[List["AgentTask"]] = relationship("AgentTask", back_populates="review", cascade="all, delete-orphan", lazy="selectin")
    findings: Mapped[List["Finding"]] = relationship("Finding", back_populates="review", cascade="all, delete-orphan", lazy="selectin")

class AgentTask(Base, TimestampMixin):
    __tablename__ = "agent_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    review_id: Mapped[str] = mapped_column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="waiting")  # "waiting", "running", "completed", "failed", "timed_out"
    input_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    output_artifact: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    provider_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tools_called: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list)
    execution_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # v1.1.0 Prompt Registry Traceability
    prompt_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    prompt_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    review: Mapped["Review"] = relationship("Review", back_populates="tasks")

class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    review_id: Mapped[str] = mapped_column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)  # critical, high, medium, low, informational
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    confidence_interpretation: Mapped[str] = mapped_column(String(255), default="High confidence based on direct source evidence")
    verification_status: Mapped[str] = mapped_column(String(50), default="static_analysis")  # tested, runtime_confirmed, static_analysis, inference, manual_review_required, not_tested
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manual_review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    review: Mapped["Review"] = relationship("Review", back_populates="findings")
    project: Mapped["Project"] = relationship("Project", back_populates="findings")
    evidence_items: Mapped[List["Evidence"]] = relationship("Evidence", back_populates="finding", cascade="all, delete-orphan")

class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    finding_id: Mapped[str] = mapped_column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    display_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    line_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    line_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), default="code_snippet")
    retrieval_method: Mapped[str] = mapped_column(String(50), default="hybrid")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    finding: Mapped["Finding"] = relationship("Finding", back_populates="evidence_items")

class SecurityKnowledgeSource(Base, TimestampMixin):
    __tablename__ = "security_knowledge_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(100), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(512), nullable=False)
    version_date: Mapped[str] = mapped_column(String(50), nullable=False)
    license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    coverage_category: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    source_type: Mapped[str] = mapped_column(String(50), default="bundled_baseline")  # "bundled_baseline", "user_imported"
    agent_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    records: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    version_hash: Mapped[str] = mapped_column(String(64), nullable=False)

class ProviderConfiguration(Base, TimestampMixin):
    __tablename__ = "provider_configurations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default="default")
    mode: Mapped[str] = mapped_column(String(50), default="Auto")
    primary_provider: Mapped[str] = mapped_column(String(50), default="Groq")
    fallback_provider: Mapped[str] = mapped_column(String(50), default="Ollama")
    groq_model: Mapped[str] = mapped_column(String(100), default="llama-3.3-70b-versatile")
    ollama_model: Mapped[str] = mapped_column(String(100), default="qwen2.5-coder:7b")
    hybrid_policy: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

class EvaluationDataset(Base, TimestampMixin):
    __tablename__ = "evaluation_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    dataset_payload: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

    runs: Mapped[List["EvaluationRun"]] = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")

class EvaluationRun(Base, TimestampMixin):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False)
    snapshot_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    dataset_version: Mapped[Optional[str]] = mapped_column(String(20), default="1.0.0")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running")  # running, completed, completed_with_limitations, cancelled, needs_attention
    provider_mode: Mapped[str] = mapped_column(String(50), default="Auto")
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    sample_results: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    execution_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    elapsed_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    dataset: Mapped["EvaluationDataset"] = relationship("EvaluationDataset", back_populates="runs")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
