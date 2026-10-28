import {
  Project, Source, Review, Finding, ReviewReport,
  AgentCard, ProvidersHealth, AppSettings, EvaluationDataset, EvaluationRun,
  GitHubImportJob, SourceSnapshot, SecurityKnowledgeSource, SystemMetrics,
  ProjectProfile, ArchitectureGraph
} from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const err = await response.json();
      errorDetail = err.detail || JSON.stringify(err);
    } catch (_) {}
    throw new Error(`API Error (${response.status}): ${errorDetail}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Projects
  getProjects: () => request<Project[]>('/projects'),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (data: { name: string; description?: string }) =>
    request<Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  deleteProject: (id: string) =>
    request<void>(`/projects/${id}`, { method: 'DELETE' }),
  cleanupTestProjects: () =>
    request<{ message: string; deleted_count: number }>('/projects/cleanup-tests', { method: 'DELETE' }),

  // Project Profile & Architecture Visualization (v1.2.0)
  getProjectProfile: (projectId: string, snapshotId?: string) =>
    request<ProjectProfile>(snapshotId ? `/projects/${projectId}/profile?snapshot_id=${snapshotId}` : `/projects/${projectId}/profile`),

  updateProjectUserContext: (projectId: string, data: {
    purpose?: string;
    deployment_env?: string;
    sensitive_data?: string;
    intended_users?: string;
    review_goals?: string;
  }) => request<ProjectProfile>(`/projects/${projectId}/context`, { method: 'PATCH', body: JSON.stringify(data) }),

  getArchitectureGraph: (projectId: string, snapshotId?: string) =>
    request<ArchitectureGraph>(snapshotId ? `/projects/${projectId}/architecture-graph?snapshot_id=${snapshotId}` : `/projects/${projectId}/architecture-graph`),

  retryProjectIngestion: (projectId: string) =>
    request<GitHubImportJob>(`/projects/${projectId}/ingest/retry`, { method: 'POST' }),

  cancelImportJob: (importId: string) =>
    request<GitHubImportJob>(`/projects/imports/${importId}/cancel`, { method: 'POST' }),

  // GitHub Import & Immutable Snapshots (v1.1.0)
  importGitHub: (data: {
    repo_url: string;
    ref_name?: string;
    access_token?: string;
    project_name?: string;
    project_id?: string;
    description?: string;
  }) => request<GitHubImportJob>('/projects/imports/github', { method: 'POST', body: JSON.stringify(data) }),

  getImportJob: (jobId: string) =>
    request<GitHubImportJob>(`/projects/imports/${jobId}`),

  refreshGitHubSnapshot: (projectId: string) =>
    request<GitHubImportJob>(`/projects/${projectId}/sources/github/refresh`, { method: 'POST' }),

  getProjectSnapshots: (projectId: string) =>
    request<SourceSnapshot[]>(`/projects/${projectId}/snapshots`),

  // Sources & Ingestion
  getProjectSources: (projectId: string) =>
    request<Source[]>(`/projects/${projectId}/sources`),
  uploadSources: async (projectId: string, files: File[]): Promise<Source[]> => {
    const formData = new FormData();
    files.forEach((file) => {
      const path = (file as any).webkitRelativePath || file.name;
      formData.append('files', file, path);
    });
    const res = await fetch(`${API_BASE}/projects/${projectId}/sources`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },
  deleteSource: (projectId: string, sourceId: string) =>
    request<void>(`/projects/${projectId}/sources/${sourceId}`, { method: 'DELETE' }),
  getSourceExcerpt: (sourceId: string, lineStart: number = 1, lineEnd: number = 50) =>
    request<{ source_id: string; file_path: string; line_start: number; line_end: number; content: string }>(
      `/sources/${sourceId}/excerpt?line_start=${lineStart}&line_end=${lineEnd}`
    ),

  // Indexing
  triggerIndexing: (projectId: string) =>
    request<{ message: string; project_id: string; status: string }>(`/projects/${projectId}/index`, { method: 'POST' }),
  getIndexingStatus: (projectId: string) =>
    request<{ project_id: string; status: string; source_count: number; chunk_count: number; metadata: any }>(
      `/projects/${projectId}/index/status`
    ),

  // Reviews & Multi-Agent Execution
  getReviews: (projectId?: string) =>
    request<Review[]>(projectId ? `/reviews?project_id=${projectId}` : '/reviews'),
  getReview: (id: string) => request<Review>(`/reviews/${id}`),
  createReview: (data: {
    project_id: string;
    question?: string;
    scope?: string;
    selected_agents?: string[];
    provider_mode?: string;
  }) => request<Review>('/reviews', { method: 'POST', body: JSON.stringify(data) }),
  getReviewFindings: (
    reviewId: string,
    filters?: { severity?: string; category?: string; agent_id?: string; verification_status?: string; manual_review_only?: boolean }
  ) => {
    const params = new URLSearchParams();
    if (filters?.severity) params.append('severity', filters.severity);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.agent_id) params.append('agent_id', filters.agent_id);
    if (filters?.verification_status) params.append('verification_status', filters.verification_status);
    if (filters?.manual_review_only) params.append('manual_review_only', 'true');
    return request<Finding[]>(`/reviews/${reviewId}/findings?${params.toString()}`);
  },
  getReviewReport: (reviewId: string, mode: string = 'developer') =>
    request<ReviewReport>(`/reviews/${reviewId}/report?presentation_mode=${mode}`),
  verifyReviewAudit: (reviewId: string, mode: string = 'developer') =>
    request<ReviewReport>(`/reviews/${reviewId}/verify-audit?presentation_mode=${mode}`, { method: 'POST' }),

  // SSE Stream URL
  getReviewEventsUrl: (reviewId: string) => `${API_BASE}/reviews/${reviewId}/events`,

  // Agents & MCP
  getAgents: () => request<AgentCard[]>('/agents'),
  getAgentHealth: (agentId: string) => request<any>(`/agents/${agentId}/health`),

  // Security Knowledge Collection (v1.1.0)
  getKnowledgeCollections: () => request<SecurityKnowledgeSource[]>('/knowledge/collections'),
  getKnowledgeCollection: (id: string) => request<SecurityKnowledgeSource>(`/knowledge/collections/${id}`),
  toggleKnowledgeCollection: (id: string, isEnabled: boolean) =>
    request<SecurityKnowledgeSource>(`/knowledge/collections/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_enabled: isEnabled })
    }),
  createKnowledgeCollection: (data: any) =>
    request<SecurityKnowledgeSource>('/knowledge/collections', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  // Settings & Providers
  getSettings: () => request<AppSettings>('/settings'),
  updateSettings: (data: Partial<AppSettings>) =>
    request<{ message: string }>('/settings', { method: 'PATCH', body: JSON.stringify(data) }),
  getProvidersHealth: () => request<ProvidersHealth>('/settings/providers'),

  // Evaluations & Real System Metrics (v1.1.0)
  getSystemMetrics: (projectId?: string) =>
    request<SystemMetrics>(projectId ? `/evaluations/metrics?project_id=${projectId}` : '/evaluations/metrics'),
  getEvaluationDatasets: () => request<EvaluationDataset[]>('/evaluations/datasets'),
  createEvaluationDataset: (data: { name: string; description?: string; dataset_payload: any[] }) =>
    request<EvaluationDataset>('/evaluations/datasets', { method: 'POST', body: JSON.stringify(data) }),
  getEvaluationRuns: () => request<EvaluationRun[]>('/evaluations/runs'),
  createEvaluationRun: (data: { dataset_id: string; name: string; provider_mode: string }) =>
    request<EvaluationRun>('/evaluations/runs', { method: 'POST', body: JSON.stringify(data) }),
  getEvaluationRun: (runId: string) =>
    request<EvaluationRun>(`/evaluations/runs/${runId}`),
};
