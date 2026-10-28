'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api/client';
import { Project, Source, SourceSnapshot, GitHubImportJob } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [snapshots, setSnapshots] = useState<SourceSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);

  // Refresh Snapshot state
  const [refreshing, setRefreshing] = useState(false);
  const [refreshJob, setRefreshJob] = useState<GitHubImportJob | null>(null);
  const [isSnapshotsModalOpen, setIsSnapshotsModalOpen] = useState(false);

  // Excerpt Modal
  const [selectedExcerpt, setSelectedExcerpt] = useState<{ path: string; content: string } | null>(null);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      api.getProject(projectId),
      api.getProjectSources(projectId),
      api.getProjectSnapshots(projectId).catch(() => [])
    ])
      .then(([proj, srcs, snaps]) => {
        setProject(proj);
        setSources(srcs);
        setSnapshots(snaps);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (projectId) loadData();
  }, [projectId]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    try {
      const filesArray = Array.from(e.target.files);
      await api.uploadSources(projectId, filesArray);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleRefreshSnapshot = async () => {
    if (!project?.repo_url) return;
    setRefreshing(true);
    setRefreshJob(null);
    try {
      const job = await api.refreshGitHubSnapshot(projectId);
      setRefreshJob(job);

      const interval = setInterval(async () => {
        try {
          const updated = await api.getImportJob(job.id);
          setRefreshJob(updated);
          if (updated.status === 'completed' || updated.status === 'failed') {
            clearInterval(interval);
            setRefreshing(false);
            loadData();
          }
        } catch (_) {
          clearInterval(interval);
          setRefreshing(false);
        }
      }, 1000);
    } catch (err: any) {
      alert(err.message || 'Failed to trigger snapshot refresh');
      setRefreshing(false);
    }
  };

  const handleIndex = async () => {
    setIndexing(true);
    try {
      await api.triggerIndexing(projectId);
      const interval = setInterval(async () => {
        const stat = await api.getIndexingStatus(projectId);
        if (stat.status === 'ready' || stat.status === 'error') {
          clearInterval(interval);
          setIndexing(false);
          loadData();
        }
      }, 1000);
    } catch (err: any) {
      alert(err.message || 'Indexing failed');
      setIndexing(false);
    }
  };

  const handleViewExcerpt = async (sourceId: string, path: string) => {
    try {
      const res = await api.getSourceExcerpt(sourceId, 1, 100);
      setSelectedExcerpt({ path: res.file_path, content: res.content });
    } catch (err: any) {
      alert(err.message || 'Failed to load excerpt');
    }
  };

  if (loading && !project) {
    return <p className="mono">Loading project data...</p>;
  }

  if (!project) {
    return <p>Project not found.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Link href="/projects" style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              ← All Projects
            </Link>
            <Badge variant="status" value={project.status}>
              {project.status}
            </Badge>
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>{project.name}</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {project.description || 'No description provided.'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {project.repo_url && (
            <Button
              variant="secondary"
              onClick={handleRefreshSnapshot}
              loading={refreshing}
            >
              ↻ Refresh Snapshot
            </Button>
          )}

          <input
            id="source-file-input"
            type="file"
            multiple
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            disabled={uploading}
          />
          <Button
            variant="secondary"
            loading={uploading}
            onClick={() => document.getElementById('source-file-input')?.click()}
          >
            + Upload Files
          </Button>

          <Button
            variant="secondary"
            onClick={handleIndex}
            loading={indexing || project.status === 'indexing'}
            disabled={sources.length === 0}
          >
            Run Indexing
          </Button>

          <Link href={`/reviews?project_id=${project.id}`}>
            <Button variant="primary">Start Review</Button>
          </Link>
        </div>
      </div>

      {/* Snapshot and Commit Provenance Banner */}
      {project.repo_url && (
        <div
          className="mono"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            fontSize: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            GitHub Repository: <strong style={{ color: 'var(--text-primary)' }}>{project.repo_url}</strong>
          </div>
          <div>
            Active Commit: <strong style={{ color: 'var(--text-primary)' }}>{project.current_commit_sha ? project.current_commit_sha.slice(0, 10) : 'HEAD'}</strong>
          </div>
          <div>
            Snapshot ID: <span style={{ color: 'var(--text-secondary)' }}>{project.current_snapshot_id || 'snap_active'}</span>
          </div>
          {snapshots.length > 0 && (
            <button
              onClick={() => setIsSnapshotsModalOpen(true)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-primary)',
                textDecoration: 'underline',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              View History ({snapshots.length})
            </button>
          )}
        </div>
      )}

      {/* Refresh Job Progress Banner */}
      {refreshJob && refreshJob.status !== 'completed' && (
        <div style={{ padding: '14px 18px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600 }}>Refreshing Source Snapshot</span>
            <Badge variant="status" value={refreshJob.status}>{refreshJob.status}</Badge>
          </div>
          <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ width: `${refreshJob.progress_percent}%`, height: '100%', backgroundColor: 'var(--text-primary)', transition: 'width 0.3s ease' }} />
          </div>
          <p className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px' }}>
            {refreshJob.status_message}
          </p>
        </div>
      )}

      {/* Indexing Metadata card if available */}
      {project.indexing_metadata && (
        <div
          className="mono"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 18px',
            fontSize: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            Embedding Model: <strong style={{ color: 'var(--text-primary)' }}>{project.indexing_metadata.embedding_model || 'Local 384-d'}</strong>
          </div>
          <div>
            Indexed: <strong style={{ color: 'var(--text-primary)' }}>{project.chunk_count}</strong> chunks
          </div>
          <div>
            Last Indexed: <span style={{ color: 'var(--text-secondary)' }}>{project.indexing_metadata.indexed_at || 'Just now'}</span>
          </div>
        </div>
      )}

      {/* Source Inventory Table */}
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>
          Source Files & Documentation Inventory ({sources.length})
        </h3>

        {sources.length === 0 ? (
          <EmptyState
            title="No Sources Ingested Yet"
            description="Upload source code files or an archive (.zip) of your repository to extract text and prepare for RAG analysis."
          />
        ) : (
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-elevated)' }}>
                  <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>File Path</th>
                  <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>Type</th>
                  <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>Size</th>
                  <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>Lines</th>
                  <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr
                    key={s.id}
                    style={{ borderBottom: '1px solid var(--border-subtle)' }}
                  >
                    <td style={{ padding: '12px 16px' }} className="mono">
                      {s.file_path}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <Badge variant="outline">{s.file_type}</Badge>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }} className="mono">
                      {Math.round(s.file_size / 1024)} KB
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }} className="mono">
                      {s.line_count}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleViewExcerpt(s.id, s.file_path)}
                      >
                        Preview
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Snapshot History Modal */}
      <Modal
        isOpen={isSnapshotsModalOpen}
        onClose={() => setIsSnapshotsModalOpen(false)}
        title="Immutable Snapshot History"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {snapshots.map((snap) => (
            <div
              key={snap.id}
              className="mono"
              style={{
                padding: '12px 16px',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: snap.is_current ? 'var(--bg-elevated)' : 'transparent',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '12px',
              }}
            >
              <div>
                <div><strong>Commit: {snap.commit_sha ? snap.commit_sha.slice(0, 10) : 'HEAD'}</strong> {snap.is_current && <Badge variant="outline">Current</Badge>}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '11px', marginTop: '4px' }}>
                  Sources: {snap.source_count} | Size: {Math.round(snap.total_size_bytes / 1024)} KB
                </div>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                {new Date(snap.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </Modal>

      {/* Excerpt Modal */}
      <Modal
        isOpen={!!selectedExcerpt}
        onClose={() => setSelectedExcerpt(null)}
        title={selectedExcerpt?.path || 'Source Excerpt'}
      >
        <pre
          className="mono"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            padding: '16px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '12px',
            overflowX: 'auto',
            maxHeight: '400px',
            whiteSpace: 'pre-wrap',
            color: 'var(--text-primary)',
          }}
        >
          {selectedExcerpt?.content}
        </pre>
      </Modal>
    </div>
  );
}
