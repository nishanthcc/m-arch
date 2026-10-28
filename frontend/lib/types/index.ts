export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'informational';
export type VerificationStatus =
  | 'verified'
  | 'partially_supported'
  | 'unsupported'
  | 'duplicate'
  | 'not_verifiable'
  | 'tested'
  | 'runtime_confirmed'
  | 'static_analysis'
  | 'inference'
  | 'manual_review_required'
  | 'not_tested';
export type TaskStatus = 'waiting' | 'running' | 'completed' | 'failed' | 'timed_out';
export type AIMode = 'Auto' | 'Groq' | 'Ollama' | 'Hybrid';
export type AgentRuntimeState = 'available' | 'busy' | 'unavailable' | 'paused' | 'misconfigured';

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'created' | 'indexing' | 'ready' | 'error' | 'needs_attention';
  source_count: number;
  chunk_count: number;
  indexing_metadata?: Record<string, any>;
  current_snapshot_id?: string;
  repo_url?: string;
  current_commit_sha?: string;
  user_context?: {
    purpose?: string;
    deployment_env?: string;
    sensitive_data?: string;
    intended_users?: string;
    review_goals?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  status: 'detected' | 'inferred' | 'unverified';
  details?: string;
  evidence?: {
    file_path?: string;
    line?: number;
    excerpt?: string;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  status: 'detected' | 'inferred' | 'unverified';
  label: string;
}

export interface ArchitectureGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ProjectProfile {
  id: string;
  project_id: string;
  snapshot_id: string;
  languages: Record<string, {
    language: string;
    file_count: number;
    line_count: number;
    byte_count: number;
    line_percentage: number;
    byte_percentage: number;
    sample_files: string[];
  }>;
  frameworks: Array<{
    name: string;
    version: string;
    category: string;
    status: 'detected' | 'inferred' | 'unknown';
    evidence?: {
      file_path?: string;
      line?: number;
      excerpt?: string;
    };
  }>;
  application_type: string;
  app_type_status: 'detected' | 'inferred' | 'user_provided' | 'unknown';
  likely_purpose?: string;
  entrypoints: Array<{
    file_path: string;
    file_name: string;
    status: string;
    evidence?: any;
  }>;
  modules: any[];
  services: Array<{
    name: string;
    file_path: string;
    category: string;
    status: string;
    evidence?: any;
  }>;
  routes: Array<{
    method: string;
    path: string;
    handler_file: string;
    line: number;
    status: string;
    evidence?: any;
  }>;
  database_technologies: Array<{
    name: string;
    status: string;
    evidence?: any;
  }>;
  dependency_manifests: Array<{
    file_path: string;
    manifest_type: string;
    line_count: number;
    status: string;
    lockfile_present: boolean;
    evidence?: any;
  }>;
  test_frameworks: Array<{
    framework: string;
    status: string;
    test_directories: string[];
    evidence?: any;
  }>;
  deployment_config: Array<{
    type: string;
    file_path: string;
    status: string;
    evidence?: any;
  }>;
  architecture_graph: ArchitectureGraph;
  unsupported_technologies: any[];
  user_context?: {
    purpose?: string;
    deployment_env?: string;
    sensitive_data?: string;
    intended_users?: string;
    review_goals?: string;
  };
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
  current_step?: string;
  files_accepted: number;
  files_skipped: number;
  files_failed?: number;
  chunks_created?: number;
  snapshot_id?: string;
  skipped_details?: Array<any>;
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
    partially_supported_count?: number;
    unsupported_count?: number;
    duplicate_count?: number;
    not_verifiable_count?: number;
    rejected_count?: number;
    citation_coverage_score?: number;
    files_analyzed?: number;
    files_skipped?: number;
    total_files?: number;
    coverage_statement?: string;
    conflicts_identified?: Array<any>;
    prompt_version?: string;
    audited_at?: string;
  };
  tasks: AgentTask[];
  skipped_agents?: Array<{ agent_id?: string; agent?: string; name?: string; reason: string }>;
  presentation_views?: Record<string, { markdown: string; html: string; summary?: string; action_items?: string[] } | any>;
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
  presentation_mode?: 'simple' | 'developer' | 'professional' | 'executive';
  summary?: string;
  limitations?: string;
  total_findings: number;
  findings_by_severity: Record<string, number>;
  findings: Finding[];
  agent_traces: AgentTask[];
  evidence_verification_summary?: Record<string, any>;
  presentation_views?: Record<string, { markdown: string; html: string }>;
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
    Gemini?: ProviderStatus;
    [key: string]: ProviderStatus | undefined;
  };
}

export interface AppSettings {
  ai_mode: AIMode;
  primary_provider: 'Groq' | 'Ollama';
  fallback_provider: 'Groq' | 'Ollama';
  groq_configured: boolean;
  groq_model: string;
  gemini_configured?: boolean;
  gemini_model?: string;
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

export interface MetricRatio {
  numerator: number;
  denominator: number;
  percentage: number | null;
  formatted: string;
}

export interface SystemMetrics {
  has_enough_data: boolean;
  message?: string;
  project_id?: string | null;
  project_name?: string | null;
  total_reviews: number;
  total_agent_tasks?: number;
  total_import_jobs?: number;
  citation_coverage?: MetricRatio | number | null;
  citation_correctness?: MetricRatio | number | null;
  unsupported_claim_count?: number;
  agent_completion_rate?: MetricRatio | number | null;
  agent_partial_failure_recovery_rate?: MetricRatio | number | null;
  provider_fallback_rate?: MetricRatio | number | null;
  import_success_rate?: MetricRatio | number | null;
  avg_review_duration_seconds?: number | null;
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
  snapshot_id?: string;
  dataset_version?: string;
  name: string;
  status: string;
  provider_mode: string;
  metrics: Record<string, any>;
  sample_results: Array<Record<string, any>>;
  execution_summary?: Record<string, any>;
  elapsed_seconds: number;
  created_at: string;
}
