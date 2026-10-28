export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'informational';
export type VerificationStatus = 'tested' | 'runtime_confirmed' | 'static_analysis' | 'inference' | 'manual_review_required' | 'not_tested';
export type TaskStatus = 'waiting' | 'running' | 'completed' | 'failed' | 'timed_out';
export type AIMode = 'Auto' | 'Groq' | 'Ollama' | 'Hybrid';
export type AgentRuntimeState = 'available' | 'busy' | 'unavailable' | 'paused' | 'misconfigured';

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'created' | 'indexing' | 'ready' | 'error';
  source_count: number;
  chunk_count: number;
  indexing_metadata?: Record<string, any>;
  current_snapshot_id?: string;
  repo_url?: string;
  current_commit_sha?: string;
  created_at: string;
  updated_at: string;
}

export interface SourceSnapshot {
  id: string;
  project_id: string;
  snapshot_type: string;
  commit_sha?: string;
  ref_name?: string;
  repo_url?: string;
  repo_owner?: string;
  repo_name?: string;
  source_hash: string;
  source_count: number;
  total_size_bytes: number;
  is_current: boolean;
  created_at: string;
}

export interface GitHubImportJob {
  id: string;
  project_id: string;
  importer_type: string;
  status: 'pending' | 'validating' | 'fetching' | 'extracting' | 'indexing' | 'completed' | 'failed';
  progress_percent: number;
  status_message: string;
  repo_url: string;
  ref_name?: string;
  resolved_commit_sha?: string;
  files_accepted: number;
  files_skipped: number;
  total_size_bytes: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  id: string;
  project_id: string;
  file_path: string;
  file_name: string;
  file_type: string;
  file_size: number;
  content_hash: string;
  line_count: number;
  snapshot_id?: string;
  created_at: string;
}

export interface EvidenceItem {
  id?: string;
  source_id: string;
  display_path: string;
  line_start?: number;
  line_end?: number;
  section?: string;
  excerpt: string;
  evidence_type: string;
  retrieval_method: string;
  score?: number;
  content_hash?: string;
}

export interface Finding {
  id: string;
  review_id: string;
  project_id: string;
  agent_id: string;
  title: string;
  explanation: string;
  severity: Severity;
  category: string;
  impact: string;
  remediation: string;
  confidence: number;
  confidence_interpretation: string;
  verification_status: VerificationStatus;
  limitations?: string;
  manual_review_required: boolean;
  first_seen_at: string;
  evidence_items: EvidenceItem[];
}

export interface AgentTask {
  id: string;
  review_id: string;
  agent_id: string;
  task_name: string;
  status: TaskStatus;
  provider_used?: string;
  model_used?: string;
  execution_time_seconds: number;
  tools_called?: Array<{ tool: string; timestamp: number }>;
  error_message?: string;
  prompt_id?: string;
  prompt_version?: string;
  prompt_hash?: string;
}

export interface Review {
  id: string;
  project_id: string;
  question: string;
  scope: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial';
  provider_mode: AIMode;
  provider_used?: string;
  model_used?: string;
  fallback_occurred: boolean;
  summary?: string;
  limitations?: string;
  total_findings: number;
  elapsed_seconds: number;
  trace_metadata?: Record<string, any>;
  source_snapshot_id?: string;
  commit_sha?: string;
  evidence_verification_summary?: {
    verified_count?: number;
    rejected_count?: number;
    citation_coverage_score?: number;
    conflicts_identified?: Array<any>;
    prompt_version?: string;
  };
  tasks: AgentTask[];
  created_at: string;
  updated_at: string;
}

export interface ReviewReport {
  review_id: string;
  project_name: string;
  question: string;
  status: string;
  commit_sha?: string;
  source_snapshot_id?: string;
  summary?: string;
  limitations?: string;
  total_findings: number;
  findings_by_severity: Record<string, number>;
  findings: Finding[];
  agent_traces: AgentTask[];
  evidence_verification_summary?: Record<string, any>;
  markdown_report: string;
  html_report: string;
}

export interface AgentCard {
  agent_id: string;
  name: string;
  role: string;
  description: string;
  endpoint: string;
  skills: string[];
  allowed_mcp_tools: string[];
  configured_provider: string;
  configured_model: string;
  status: AgentRuntimeState;
  current_state?: AgentRuntimeState;
  a2a_connectivity?: string;
  prompt_version?: string;
  actual_model_used?: string;
  fallback_history?: string[];
  last_task_time?: string;
  last_error?: string;
}

export interface ProviderStatus {
  name: string;
  available: boolean;
  configured: boolean;
  latency_ms?: number;
  active_model: string;
  installed_models?: string[];
  error?: string;
}

export interface ProvidersHealth {
  mode: string;
  primary_provider: string;
  fallback_provider: string;
  providers: {
    Groq: ProviderStatus;
    Ollama: ProviderStatus;
  };
}

export interface AppSettings {
  ai_mode: AIMode;
  primary_provider: 'Groq' | 'Ollama';
  fallback_provider: 'Groq' | 'Ollama';
  groq_configured: boolean;
  groq_model: string;
  ollama_base_url: string;
  ollama_model: string;
  embedding_model: string;
  embedding_dimension: number;
  upload_max_mb: number;
  rerank_enabled: boolean;
  hybrid_policy: Record<string, string>;
}

export interface SecurityKnowledgeSource {
  id: string;
  name: string;
  organization: string;
  canonical_url: string;
  version_date: string;
  license?: string;
  record_count: number;
  coverage_category: string;
  is_enabled: boolean;
  source_type: string;
  agent_ids: string[];
  records: Array<{
    id: string;
    title: string;
    category: string;
    severity: string;
    patterns?: string[];
    guidance: string;
  }>;
  version_hash: string;
  created_at: string;
  updated_at: string;
}

export interface SystemMetrics {
  has_enough_data: boolean;
  message?: string;
  total_reviews: number;
  total_agent_tasks?: number;
  total_import_jobs?: number;
  citation_coverage?: number;
  citation_correctness?: number;
  unsupported_claim_count?: number;
  agent_completion_rate?: number;
  agent_partial_failure_recovery_rate?: number;
  provider_fallback_rate?: number;
  import_success_rate?: number;
  avg_review_duration_seconds?: number;
}

export interface EvaluationDataset {
  id: string;
  name: string;
  description?: string;
  sample_count: number;
  created_at: string;
}

export interface EvaluationRun {
  id: string;
  dataset_id: string;
  name: string;
  status: string;
  provider_mode: string;
  metrics: Record<string, any>;
  sample_results: Array<Record<string, any>>;
  elapsed_seconds: number;
  created_at: string;
}
