'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/client';
import { Project, GitHubImportJob } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [sourceType, setSourceType] = useState<'github' | 'zip' | 'files'>('github');
  const [filterTab, setFilterTab] = useState<'all' | 'active' | 'attention'>('all');
  const [cleaningTests, setCleaningTests] = useState(false);

  // GitHub Import state
  const [repoUrl, setRepoUrl] = useState('');
  const [refName, setRefName] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [githubProjectName, setGithubProjectName] = useState('');
  const [githubDescription, setGithubDescription] = useState('');
  const [importing, setImporting] = useState(false);
  const [importJob, setImportJob] = useState<GitHubImportJob | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  // Upload ZIP state
  const [zipName, setZipName] = useState('');
  const [zipDescription, setZipDescription] = useState('');
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [zipDragOver, setZipDragOver] = useState(false);
  const [zipUploading, setZipUploading] = useState(false);
  const [zipProgress, setZipProgress] = useState<{ stage: string; percent: number; done: boolean; projectId?: string; sourcesCount?: number } | null>(null);
  const [zipError, setZipError] = useState<string | null>(null);
  const zipInputRef = useRef<HTMLInputElement | null>(null);

  // Upload Files state
  const [filesName, setFilesName] = useState('');
  const [filesDescription, setFilesDescription] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [filesDragOver, setFilesDragOver] = useState(false);
  const [filesUploading, setFilesUploading] = useState(false);
  const [filesProgress, setFilesProgress] = useState<{ stage: string; percent: number; done: boolean; projectId?: string; sourcesCount?: number } | null>(null);
  const [filesError, setFilesError] = useState<string | null>(null);
  const filesInputRef = useRef<HTMLInputElement | null>(null);
  const folderInputRef = useRef<HTMLInputElement | null>(null);

  const loadProjects = () => {
    setLoading(true);
    api.getProjects()
      .then(setProjects)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const resetModalState = () => {
    setImportJob(null);
    setImportError(null);
    setZipProgress(null);
    setZipError(null);
    setFilesProgress(null);
    setFilesError(null);
  };

  // --- GitHub Import ---
  const handleGitHubImport = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedUrl = repoUrl.trim();
    if (!trimmedUrl) return;

    if (!trimmedUrl.startsWith('https://github.com/')) {
      setImportError('Invalid URL. Only official HTTPS GitHub URLs are accepted (e.g. https://github.com/owner/repo)');
      return;
    }

    setImporting(true);
    setImportError(null);
    setImportJob(null);

    try {
      const job = await api.importGitHub({
        repo_url: trimmedUrl,
        ref_name: refName.trim() || undefined,
        access_token: accessToken.trim() || undefined,
        project_name: githubProjectName.trim() || undefined,
        description: githubDescription.trim() || undefined,
      });
      setImportJob(job);

      const pollInterval = setInterval(async () => {
        try {
          const updated = await api.getImportJob(job.id);
          setImportJob(updated);
          if (updated.status === 'completed') {
            clearInterval(pollInterval);
            setImporting(false);
            loadProjects();
          } else if (updated.status === 'failed') {
            clearInterval(pollInterval);
            setImporting(false);
            setImportError(updated.error_message || 'Import failed.');
          }
        } catch (pollErr: any) {
          clearInterval(pollInterval);
          setImporting(false);
          setImportError(pollErr.message || 'Error tracking import progress');
        }
      }, 1000);
    } catch (err: any) {
      setImporting(false);
      setImportError(err.message || 'Failed to start GitHub import');
    }
  };

  // --- ZIP Upload Handlers ---
  const handleZipFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      processSelectedZip(file);
    }
  };

  const processSelectedZip = (file: File) => {
    setZipError(null);
    if (!file.name.toLowerCase().endsWith('.zip')) {
      setZipError('Selected file is not a .zip archive. Please select a valid ZIP file.');
      return;
    }
    const maxBytes = 100 * 1024 * 1024; // 100MB
    if (file.size > maxBytes) {
      setZipError(`File size (${formatBytes(file.size)}) exceeds maximum limit of 100MB.`);
      return;
    }
    setZipFile(file);
    if (!zipName.trim()) {
      const baseName = file.name.replace(/\.zip$/i, '');
      setZipName(baseName);
    }
  };

  const handleZipDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setZipDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedZip(e.dataTransfer.files[0]);
    }
  };

  const handleZipSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!zipFile) {
      setZipError('Please select a .zip archive to upload.');
      return;
    }
    if (!zipName.trim()) {
      setZipError('Please enter a project name.');
      return;
    }

    setZipUploading(true);
    setZipError(null);
    setZipProgress({ stage: 'Creating project container...', percent: 20, done: false });

    try {
      // 1. Create Project
      const project = await api.createProject({
        name: zipName.trim(),
        description: zipDescription.trim() || undefined,
      });

      setZipProgress({ stage: 'Uploading & extracting archive...', percent: 50, done: false, projectId: project.id });

      // 2. Upload ZIP via multipart FormData
      const createdSources = await api.uploadSources(project.id, [zipFile]);

      setZipProgress({ stage: 'Computing hashes & indexing vectors...', percent: 85, done: false, projectId: project.id, sourcesCount: createdSources.length });

      // 3. Trigger semantic indexing
      await api.triggerIndexing(project.id);

      setZipProgress({ stage: 'Ingestion and indexing complete!', percent: 100, done: true, projectId: project.id, sourcesCount: createdSources.length });
      loadProjects();
    } catch (err: any) {
      setZipError(err.message || 'ZIP upload and ingestion failed.');
    } finally {
      setZipUploading(false);
    }
  };

  // --- Multi-Files Upload Handlers ---
  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
    e.target.value = '';
  };

  const addFiles = (newFiles: File[]) => {
    setFilesError(null);
    // Deduplicate by name/webkitRelativePath and size
    const existingKeys = new Set(selectedFiles.map((f) => `${(f as any).webkitRelativePath || f.name}_${f.size}`));
    const uniqueFiles: File[] = [];

    for (const f of newFiles) {
      const key = `${(f as any).webkitRelativePath || f.name}_${f.size}`;
      if (!existingKeys.has(key)) {
        uniqueFiles.push(f);
        existingKeys.add(key);
      }
    }

    if (uniqueFiles.length === 0 && newFiles.length > 0) {
      setFilesError('The selected files are already in the list.');
      return;
    }

    const merged = [...selectedFiles, ...uniqueFiles];
    setSelectedFiles(merged);

    if (!filesName.trim() && merged.length > 0) {
      const firstPath = (merged[0] as any).webkitRelativePath || merged[0].name;
      const rootFolder = firstPath.includes('/') ? firstPath.split('/')[0] : merged[0].name.replace(/\.[^/.]+$/, '');
      setFilesName(rootFolder || 'Source Project');
    }
  };

  const removeFile = (index: number) => {
    const updated = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updated);
  };

  const handleFilesDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setFilesDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFilesSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      setFilesError('Please select at least one source file to upload.');
      return;
    }
    if (!filesName.trim()) {
      setFilesError('Please enter a project name.');
      return;
    }

    setFilesUploading(true);
    setFilesError(null);
    setFilesProgress({ stage: 'Creating project container...', percent: 20, done: false });

    try {
      // 1. Create Project
      const project = await api.createProject({
        name: filesName.trim(),
        description: filesDescription.trim() || undefined,
      });

      setFilesProgress({
        stage: `Uploading and validating ${selectedFiles.length} source files...`,
        percent: 50,
        done: false,
        projectId: project.id,
      });

      // 2. Upload files via multipart FormData
      const createdSources = await api.uploadSources(project.id, selectedFiles);

      setFilesProgress({
        stage: 'Computing SHA-256 hashes & indexing vectors...',
        percent: 85,
        done: false,
        projectId: project.id,
        sourcesCount: createdSources.length,
      });

      // 3. Trigger semantic indexing
      await api.triggerIndexing(project.id);

      setFilesProgress({
        stage: 'Ingestion and indexing complete!',
        percent: 100,
        done: true,
        projectId: project.id,
        sourcesCount: createdSources.length,
      });
      loadProjects();
    } catch (err: any) {
      setFilesError(err.message || 'File upload and ingestion failed.');
    } finally {
      setFilesUploading(false);
    }
  };

  // --- Project Deletion ---
  const handleDelete = async (id: string, projName: string) => {
    if (!confirm(`Are you sure you want to permanently delete "${projName}" and all of its sources, snapshots, chunks, vectors, and review findings?`)) {
      return;
    }
    try {
      await api.deleteProject(id);
      loadProjects();
    } catch (err: any) {
      alert(err.message || 'Error deleting project');
    }
  };

  // --- Index Trigger ---
  const handleIndex = async (id: string) => {
    try {
      await api.triggerIndexing(id);
      loadProjects();
    } catch (err: any) {
      alert(err.message || 'Error starting indexing');
    }
  };

  // --- Safe Cleanup of Test Fixture Records ---
  const handleCleanupTests = async () => {
    if (!confirm('This will safely delete automated test fixture projects (such as "Verifier Test Suite" and "Stuck Project") while strictly preserving your authentic projects and snapshots. Continue?')) {
      return;
    }
    setCleaningTests(true);
    try {
      const res = await api.cleanupTestProjects();
      alert(res.message);
      loadProjects();
    } catch (err: any) {
      alert(err.message || 'Error cleaning up test data');
    } finally {
      setCleaningTests(false);
    }
  };

  const isModalBusy = importing || zipUploading || filesUploading;
  const filesTotalBytes = selectedFiles.reduce((acc, f) => acc + f.size, 0);

  const filteredProjects = projects.filter((p) => {
    if (filterTab === 'active') return p.status === 'ready' || p.status === 'indexing';
    if (filterTab === 'attention') return p.status === 'needs_attention' || p.status === 'error';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Project Catalog</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Source repositories, immutable snapshots, and project-specific review histories.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Button
            variant="secondary"
            onClick={handleCleanupTests}
            disabled={cleaningTests}
            title="Clean up leftover test projects while preserving all user projects"
          >
            {cleaningTests ? 'Cleaning...' : 'Clean Test Data'}
          </Button>
          <Button
            id="add-project-button"
            variant="primary"
            onClick={() => {
              setIsCreateOpen(true);
              resetModalState();
            }}
          >
            + Add Project
          </Button>
        </div>
      </div>

      {/* Filter Tabs Bar */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', gap: '8px' }}>
        {[
          { id: 'all', label: 'All Projects', count: projects.length },
          { id: 'active', label: 'Active Projects', count: projects.filter((p) => p.status === 'ready' || p.status === 'indexing').length },
          { id: 'attention', label: 'Needs Attention', count: projects.filter((p) => p.status === 'needs_attention' || p.status === 'error').length },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilterTab(tab.id as any)}
            style={{
              padding: '8px 16px',
              background: 'none',
              border: 'none',
              borderBottom: filterTab === tab.id ? '2px solid var(--text-primary)' : '2px solid transparent',
              color: filterTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              fontWeight: filterTab === tab.id ? 600 : 400,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>{tab.label}</span>
            <span
              className="mono"
              style={{
                fontSize: '10px',
                padding: '1px 6px',
                borderRadius: '10px',
                backgroundColor: 'var(--bg-elevated)',
                color: 'var(--text-muted)',
              }}
            >
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <p className="mono" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Loading projects from local SQLite database...
        </p>
      ) : filteredProjects.length === 0 ? (
        <EmptyState
          title={filterTab === 'all' ? 'No Projects in Catalog' : `No Projects in '${filterTab}' status`}
          description={filterTab === 'all' ? 'Import a GitHub repository or create a project to build RAG vector indexes and run multi-agent reviews.' : 'Switch back to All Projects or add a new repository.'}
          actionText={filterTab === 'all' ? 'Import or Create Project' : undefined}
          onAction={filterTab === 'all' ? () => {
            setIsCreateOpen(true);
            resetModalState();
          } : undefined}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '20px' }}>
          {filteredProjects.map((p) => (
            <Card
              key={p.id}
              title={
                <Link href={`/projects/${p.id}`} style={{ textDecoration: 'none' }}>
                  <span style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {p.name}
                  </span>
                </Link>
              }
              headerAction={
                <div style={{ display: 'flex', gap: '6px' }}>
                  {p.current_commit_sha && (
                    <Badge variant="outline">
                      <span className="mono">sha:{p.current_commit_sha.slice(0, 7)}</span>
                    </Badge>
                  )}
                  <Badge variant="status" value={p.status}>
                    {p.status}
                  </Badge>
                </div>
              }
              subtitle={
                <div>
                  <p>{p.description || 'No description provided.'}</p>
                  {p.repo_url && (
                    <p className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      {p.repo_url}
                    </p>
                  )}
                </div>
              }
            >
              <div
                className="mono"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '12px 0',
                  borderTop: '1px solid var(--border-subtle)',
                  borderBottom: '1px solid var(--border-subtle)',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  margin: '14px 0',
                }}
              >
                <div>
                  Sources: <strong style={{ color: 'var(--text-primary)' }}>{p.source_count}</strong>
                </div>
                <div>
                  Chunks: <strong style={{ color: 'var(--text-primary)' }}>{p.chunk_count}</strong>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                <Link href={`/projects/${p.id}`}>
                  <Button size="sm" variant="secondary">
                    View Sources
                  </Button>
                </Link>

                <div style={{ display: 'flex', gap: '6px' }}>
                  {p.source_count > 0 && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleIndex(p.id)}
                      disabled={p.status === 'indexing'}
                    >
                      {p.status === 'indexing' ? 'Indexing...' : 'Index'}
                    </Button>
                  )}
                  <Link href={`/reviews?project_id=${p.id}`}>
                    <Button size="sm" variant="primary">
                      Review
                    </Button>
                  </Link>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => handleDelete(p.id, p.name)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Project Sources Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => {
          if (!isModalBusy) setIsCreateOpen(false);
        }}
        title="Add Project Sources"
        width="640px"
      >
        {/* Source Navigation Tabs */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            marginBottom: '20px',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: '12px',
          }}
        >
          <button
            id="tab-github"
            type="button"
            onClick={() => setSourceType('github')}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: sourceType === 'github' ? '1px solid var(--border-strong)' : '1px solid transparent',
              backgroundColor: sourceType === 'github' ? 'var(--bg-elevated)' : 'transparent',
              color: 'var(--text-primary)',
              cursor: isModalBusy ? 'not-allowed' : 'pointer',
            }}
            disabled={isModalBusy}
          >
            GitHub Repository
          </button>
          <button
            id="tab-zip"
            type="button"
            onClick={() => setSourceType('zip')}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: sourceType === 'zip' ? '1px solid var(--border-strong)' : '1px solid transparent',
              backgroundColor: sourceType === 'zip' ? 'var(--bg-elevated)' : 'transparent',
              color: 'var(--text-primary)',
              cursor: isModalBusy ? 'not-allowed' : 'pointer',
            }}
            disabled={isModalBusy}
          >
            Upload ZIP
          </button>
          <button
            id="tab-files"
            type="button"
            onClick={() => setSourceType('files')}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: sourceType === 'files' ? '1px solid var(--border-strong)' : '1px solid transparent',
              backgroundColor: sourceType === 'files' ? 'var(--bg-elevated)' : 'transparent',
              color: 'var(--text-primary)',
              cursor: isModalBusy ? 'not-allowed' : 'pointer',
            }}
            disabled={isModalBusy}
          >
            Upload Files
          </button>
        </div>

        {/* Tab 1: GitHub Repository */}
        {sourceType === 'github' && (
          <div>
            {!importJob || importJob.status === 'failed' ? (
              <form onSubmit={handleGitHubImport} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <Input
                  id="github-repo-url"
                  label="GitHub Repository URL"
                  placeholder="https://github.com/owner/repository"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  required
                />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <Input
                    id="github-project-name"
                    label="Project Name (Optional)"
                    placeholder="Defaults to repo name"
                    value={githubProjectName}
                    onChange={(e) => setGithubProjectName(e.target.value)}
                  />
                  <Input
                    id="github-ref"
                    label="Branch, Tag, or Commit SHA (Optional)"
                    placeholder="main, master, v1.0.0, or specific 40-char SHA"
                    value={refName}
                    onChange={(e) => setRefName(e.target.value)}
                  />
                </div>
                <div>
                  <Input
                    id="github-token"
                    label="Personal Access Token (Private Repositories Only)"
                    type="password"
                    placeholder="github_pat_... (fine-grained token, read-only)"
                    value={accessToken}
                    onChange={(e) => setAccessToken(e.target.value)}
                  />
                  <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Strict Isolation: Token is used only in memory for this session and is never persisted, logged, or exported.
                  </p>
                </div>

                {importError && (
                  <div
                    className="mono"
                    style={{
                      padding: '10px 14px',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid #ef4444',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                      color: '#f87171',
                    }}
                  >
                    Error: {importError}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                  <Button type="button" variant="ghost" onClick={() => setIsCreateOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    id="submit-github-import"
                    type="submit"
                    variant="primary"
                    loading={importing}
                    disabled={!repoUrl.trim()}
                  >
                    Import Repository
                  </Button>
                </div>
              </form>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ padding: '16px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: 600 }}>{importJob.repo_url}</span>
                    <Badge variant="status" value={importJob.status}>{importJob.status}</Badge>
                  </div>

                  <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-subtle)', borderRadius: '3px', margin: '12px 0', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${importJob.progress_percent}%`,
                        height: '100%',
                        backgroundColor: importJob.status === 'completed' ? '#10b981' : 'var(--text-primary)',
                        transition: 'width 0.3s ease',
                      }}
                    />
                  </div>
                  <p className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    {importJob.status_message}
                  </p>
                </div>

                {importJob.status === 'completed' && (
                  <div className="mono" style={{ padding: '12px', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>Resolved Commit: <strong style={{ color: 'var(--text-primary)' }}>{importJob.resolved_commit_sha?.slice(0, 10)}</strong></div>
                    <div>Files Accepted: <strong style={{ color: 'var(--text-primary)' }}>{importJob.files_accepted}</strong></div>
                    <div>Files Skipped: <strong style={{ color: 'var(--text-secondary)' }}>{importJob.files_skipped}</strong></div>
                    <div>Total Extracted Size: <strong style={{ color: 'var(--text-primary)' }}>{Math.round(importJob.total_size_bytes / 1024)} KB</strong></div>
                    <div>Status: <span style={{ color: '#10b981' }}>Indexed & Ready for Review</span></div>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                  {importJob.status === 'completed' ? (
                    <Button id="github-done-button" variant="primary" onClick={() => setIsCreateOpen(false)}>
                      Done
                    </Button>
                  ) : null}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Upload ZIP */}
        {sourceType === 'zip' && (
          <div>
            {!zipProgress?.done ? (
              <form onSubmit={handleZipSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <Input
                  id="zip-project-name"
                  label="Project Name"
                  placeholder="e.g. Core Payment Engine"
                  value={zipName}
                  onChange={(e) => setZipName(e.target.value)}
                  required
                />
                <Input
                  id="zip-description"
                  label="Description (Optional)"
                  placeholder="Technical scope, architectural boundaries, or review focus"
                  value={zipDescription}
                  onChange={(e) => setZipDescription(e.target.value)}
                />

                {/* Accessible hidden file input */}
                <input
                  id="zip-file-input"
                  ref={zipInputRef}
                  type="file"
                  accept=".zip"
                  onChange={handleZipFileChange}
                  style={{ display: 'none' }}
                  disabled={zipUploading}
                />

                {/* Drag and Drop Box */}
                <div
                  id="zip-dropzone"
                  onDragOver={(e) => { e.preventDefault(); setZipDragOver(true); }}
                  onDragLeave={() => setZipDragOver(false)}
                  onDrop={handleZipDrop}
                  style={{
                    border: zipDragOver ? '2px dashed var(--accent-primary, #6366f1)' : '1px dashed var(--border-strong)',
                    borderRadius: 'var(--radius-md)',
                    padding: '24px 16px',
                    backgroundColor: zipDragOver ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                    textAlign: 'center',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '10px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {zipFile ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', width: '100%' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '18px' }}>📦</span>
                        <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {zipFile.name}
                        </span>
                        <Badge variant="outline">
                          <span className="mono">{formatBytes(zipFile.size)}</span>
                        </Badge>
                        <Badge variant="outline">
                          <span style={{ color: '#10b981' }}>Valid ZIP</span>
                        </Badge>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setZipFile(null);
                          if (zipInputRef.current) zipInputRef.current.value = '';
                        }}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#f87171',
                          fontSize: '12px',
                          cursor: 'pointer',
                          marginTop: '4px',
                          textDecoration: 'underline',
                        }}
                      >
                        ✕ Remove ZIP
                      </button>
                    </div>
                  ) : (
                    <>
                      <div style={{ fontSize: '28px', opacity: 0.8 }}>📦</div>
                      <div>
                        <p style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)' }}>
                          Drag and drop a project .zip archive here
                        </p>
                        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Archives up to 100MB are uncompressed, sanitized, and indexed securely
                        </p>
                      </div>
                      <Button
                        id="browse-zip-button"
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => zipInputRef.current?.click()}
                        disabled={zipUploading}
                      >
                        Browse ZIP
                      </Button>
                    </>
                  )}
                </div>

                {zipUploading && zipProgress && (
                  <div style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {zipProgress.stage}
                      </span>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
                        {zipProgress.percent}%
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-subtle)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${zipProgress.percent}%`,
                          height: '100%',
                          backgroundColor: 'var(--text-primary)',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </div>
                )}

                {zipError && (
                  <div
                    className="mono"
                    style={{
                      padding: '10px 14px',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid #ef4444',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                      color: '#f87171',
                    }}
                  >
                    Error: {zipError}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setIsCreateOpen(false)}
                    disabled={zipUploading}
                  >
                    Cancel
                  </Button>
                  <Button
                    id="submit-zip-upload"
                    type="submit"
                    variant="primary"
                    loading={zipUploading}
                    disabled={!zipFile || !zipName.trim() || zipUploading}
                  >
                    Create Project & Upload ZIP
                  </Button>
                </div>
              </form>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ padding: '16px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: 600 }}>{zipName}</span>
                    <Badge variant="status" value="ready">ready</Badge>
                  </div>
                  <div className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>Source Archive: <strong style={{ color: 'var(--text-primary)' }}>{zipFile?.name}</strong></div>
                    <div>Extracted Sources: <strong style={{ color: 'var(--text-primary)' }}>{zipProgress?.sourcesCount}</strong></div>
                    <div>Semantic Indexing: <span style={{ color: '#10b981' }}>Active & Ready</span></div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                  {zipProgress?.projectId && (
                    <Link href={`/projects/${zipProgress.projectId}`}>
                      <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
                        View Project
                      </Button>
                    </Link>
                  )}
                  <Button
                    id="zip-done-button"
                    variant="primary"
                    onClick={() => {
                      setIsCreateOpen(false);
                      setZipFile(null);
                      setZipProgress(null);
                    }}
                  >
                    Done
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Upload Files */}
        {sourceType === 'files' && (
          <div>
            {!filesProgress?.done ? (
              <form onSubmit={handleFilesSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <Input
                  id="files-project-name"
                  label="Project Name"
                  placeholder="e.g. Order Processing Service"
                  value={filesName}
                  onChange={(e) => setFilesName(e.target.value)}
                  required
                />
                <Input
                  id="files-description"
                  label="Description (Optional)"
                  placeholder="Technical scope, architectural boundaries, or review focus"
                  value={filesDescription}
                  onChange={(e) => setFilesDescription(e.target.value)}
                />

                {/* Accessible hidden file & folder inputs */}
                <input
                  id="multi-files-input"
                  ref={filesInputRef}
                  type="file"
                  multiple
                  onChange={handleFilesChange}
                  style={{ display: 'none' }}
                  disabled={filesUploading}
                />
                <input
                  id="folder-input"
                  ref={folderInputRef}
                  type="file"
                  multiple
                  {...({ webkitdirectory: '', directory: '' } as any)}
                  onChange={handleFilesChange}
                  style={{ display: 'none' }}
                  disabled={filesUploading}
                />

                {/* Drag and Drop Box & Actions */}
                <div
                  id="files-dropzone"
                  onDragOver={(e) => { e.preventDefault(); setFilesDragOver(true); }}
                  onDragLeave={() => setFilesDragOver(false)}
                  onDrop={handleFilesDrop}
                  style={{
                    border: filesDragOver ? '2px dashed var(--accent-primary, #6366f1)' : '1px dashed var(--border-strong)',
                    borderRadius: 'var(--radius-md)',
                    padding: '20px 16px',
                    backgroundColor: filesDragOver ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                    textAlign: 'center',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '10px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontSize: '28px', opacity: 0.8 }}>📁</div>
                  <div>
                    <p style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)' }}>
                      Drag and drop local source files or project folders here
                    </p>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Supports code, configuration, scripts, and Markdown (e.g. .py, .ts, .js, .json, .yaml, .md)
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
                    <Button
                      id="browse-files-button"
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => filesInputRef.current?.click()}
                      disabled={filesUploading}
                    >
                      Browse Files
                    </Button>
                    <Button
                      id="browse-folder-button"
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => folderInputRef.current?.click()}
                      disabled={filesUploading}
                    >
                      Upload Folder
                    </Button>
                  </div>
                </div>

                {/* Selected Files Inventory */}
                {selectedFiles.length > 0 && (
                  <div
                    style={{
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--bg-elevated)',
                      padding: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span className="mono" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        Selected Files: {selectedFiles.length} ({formatBytes(filesTotalBytes)})
                      </span>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          type="button"
                          onClick={() => filesInputRef.current?.click()}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-primary)',
                            fontSize: '11px',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                          }}
                        >
                          + Add More
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedFiles([])}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#f87171',
                            fontSize: '11px',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                          }}
                        >
                          Clear All
                        </button>
                      </div>
                    </div>

                    <div
                      style={{
                        maxHeight: '160px',
                        overflowY: 'auto',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      {selectedFiles.map((file, idx) => {
                        const path = (file as any).webkitRelativePath || file.name;
                        return (
                          <div
                            key={`${path}_${idx}`}
                            className="mono"
                            style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              fontSize: '11px',
                              padding: '4px 6px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--bg-surface)',
                            }}
                          >
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '380px' }}>
                              {path}
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ color: 'var(--text-muted)' }}>{formatBytes(file.size)}</span>
                              <button
                                type="button"
                                onClick={() => removeFile(idx)}
                                style={{
                                  background: 'transparent',
                                  border: 'none',
                                  color: '#f87171',
                                  cursor: 'pointer',
                                  fontSize: '13px',
                                  lineHeight: 1,
                                }}
                              >
                                ✕
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {filesUploading && filesProgress && (
                  <div style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {filesProgress.stage}
                      </span>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
                        {filesProgress.percent}%
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-subtle)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${filesProgress.percent}%`,
                          height: '100%',
                          backgroundColor: 'var(--text-primary)',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </div>
                )}

                {filesError && (
                  <div
                    className="mono"
                    style={{
                      padding: '10px 14px',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid #ef4444',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                      color: '#f87171',
                    }}
                  >
                    Error: {filesError}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setIsCreateOpen(false)}
                    disabled={filesUploading}
                  >
                    Cancel
                  </Button>
                  <Button
                    id="submit-files-upload"
                    type="submit"
                    variant="primary"
                    loading={filesUploading}
                    disabled={selectedFiles.length === 0 || !filesName.trim() || filesUploading}
                  >
                    Create Project & Upload Files
                  </Button>
                </div>
              </form>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ padding: '16px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: 600 }}>{filesName}</span>
                    <Badge variant="status" value="ready">ready</Badge>
                  </div>
                  <div className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>Files Ingested: <strong style={{ color: 'var(--text-primary)' }}>{filesProgress?.sourcesCount}</strong></div>
                    <div>Total Size: <strong style={{ color: 'var(--text-primary)' }}>{formatBytes(filesTotalBytes)}</strong></div>
                    <div>Semantic Indexing: <span style={{ color: '#10b981' }}>Active & Ready</span></div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                  {filesProgress?.projectId && (
                    <Link href={`/projects/${filesProgress.projectId}`}>
                      <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>
                        View Project
                      </Button>
                    </Link>
                  )}
                  <Button
                    id="files-done-button"
                    variant="primary"
                    onClick={() => {
                      setIsCreateOpen(false);
                      setSelectedFiles([]);
                      setFilesProgress(null);
                    }}
                  >
                    Done
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
