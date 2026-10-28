'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api/client';
import { Project, Source, SourceSnapshot, GitHubImportJob, ProjectProfile } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { Input } from '@/components/ui/Input';
import { ArchitectureGraphView } from '@/components/projects/ArchitectureGraphView';

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [profile, setProfile] = useState<ProjectProfile | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [snapshots, setSnapshots] = useState<SourceSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);

  // Tabs
  const [activeTab, setActiveTab] = useState<'architecture' | 'sources' | 'snapshots' | 'reviews'>('architecture');
  const [projectReviews, setProjectReviews] = useState<any[]>([]);

  // Search & Filter in Sources
  const [searchQuery, setSearchQuery] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState('');

  // User Context Editor Modal
  const [isContextModalOpen, setIsContextModalOpen] = useState(false);
  const [savingContext, setSavingContext] = useState(false);
  const [contextForm, setContextForm] = useState({
    purpose: '',
    deployment_env: '',
    sensitive_data: '',
    intended_users: '',
    review_goals: '',
  });

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
      api.getProjectSnapshots(projectId).catch(() => []),
      api.getProjectProfile(projectId).catch(() => null),
      api.getReviews(projectId).catch(() => []),
    ])
      .then(([proj, srcs, snaps, prof, revs]) => {
        setProject(proj);
        setSources(srcs);
        setSnapshots(snaps);
        setProfile(prof);
        setProjectReviews(revs || []);
        if (proj?.user_context) {
          setContextForm({
            purpose: proj.user_context.purpose || '',
            deployment_env: proj.user_context.deployment_env || '',
            sensitive_data: proj.user_context.sensitive_data || '',
            intended_users: proj.user_context.intended_users || '',
            review_goals: proj.user_context.review_goals || '',
          });
        }
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

  const handleRetryIngestion = async () => {
    try {
      await api.retryProjectIngestion(projectId);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Retry failed');
    }
  };

  const handleCancelImport = async (jobId: string) => {
    try {
      await api.cancelImportJob(jobId);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Cancel failed');
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

  const handleSaveContext = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingContext(true);
    try {
      const updatedProfile = await api.updateProjectUserContext(projectId, contextForm);
      setProfile(updatedProfile);
      setProject((prev) => prev ? { ...prev, user_context: contextForm } : null);
      setIsContextModalOpen(false);
    } catch (err: any) {
      alert(err.message || 'Failed to update user context');
    } finally {
      setSavingContext(false);
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
    return <p className="mono">Loading project data and deterministic profile...</p>;
  }

  if (!project) {
    return <p>Project not found.</p>;
  }

  // Filter sources
  const filteredSources = sources.filter((s) => {
    const matchesSearch = searchQuery === '' || s.file_path.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = fileTypeFilter === '' || s.file_type.toLowerCase() === fileTypeFilter.toLowerCase();
    return matchesSearch && matchesType;
  });

  const uniqueFileTypes = Array.from(new Set(sources.map((s) => s.file_type))).filter(Boolean);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Link href="/projects" style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              ← All Projects
            </Link>
            <Badge variant="status" value={project.status}>
              {project.status}
            </Badge>
            {(project.status === 'error' || project.status === 'needs_attention') && (
              <Button size="sm" variant="secondary" onClick={handleRetryIngestion}>
                ↻ Retry Ingestion
              </Button>
            )}
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>{project.name}</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {project.description || 'No description provided.'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <Button
            variant="secondary"
            onClick={() => setIsContextModalOpen(true)}
          >
            ⚙ Context & Goals
          </Button>

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
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          Source Mode:{' '}
          <strong style={{ color: 'var(--text-primary)' }}>
            {project.repo_url ? `GitHub (${project.repo_url})` : 'Local / Archive Upload'}
          </strong>
        </div>
        <div>
          Active Commit:{' '}
          <strong style={{ color: 'var(--text-primary)' }}>
            {project.current_commit_sha ? project.current_commit_sha.slice(0, 10) : 'HEAD'}
          </strong>
        </div>
        <div>
          Immutable Snapshot:{' '}
          <span style={{ color: 'var(--text-secondary)' }}>
            {project.current_snapshot_id || 'snap_local_v1'}
          </span>
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

      {/* In-Flight Refresh / Ingestion Job Banner */}
      {refreshJob && refreshJob.status !== 'completed' && (
        <div style={{ padding: '14px 18px', backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600 }}>
              Ingestion Job: {refreshJob.current_step || refreshJob.status}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Badge variant="status" value={refreshJob.status}>{refreshJob.status}</Badge>
              {refreshJob.status !== 'failed' && (
                <Button size="sm" variant="ghost" onClick={() => handleCancelImport(refreshJob.id)}>
                  Cancel
                </Button>
              )}
            </div>
          </div>
          <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ width: `${refreshJob.progress_percent}%`, height: '100%', backgroundColor: 'var(--text-primary)', transition: 'width 0.3s ease' }} />
          </div>
          <p className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px' }}>
            {refreshJob.status_message} (Accepted: {refreshJob.files_accepted || 0}, Skipped: {refreshJob.files_skipped || 0}, Failed: {refreshJob.files_failed || 0})
          </p>
        </div>
      )}

      {/* Tabs Bar */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', gap: '8px' }}>
        <button
          onClick={() => setActiveTab('architecture')}
          style={{
            padding: '10px 18px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'architecture' ? '2px solid var(--text-primary)' : '2px solid transparent',
            color: activeTab === 'architecture' ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'architecture' ? 600 : 400,
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Architecture & Profile
        </button>
        <button
          onClick={() => setActiveTab('sources')}
          style={{
            padding: '10px 18px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'sources' ? '2px solid var(--text-primary)' : '2px solid transparent',
            color: activeTab === 'sources' ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'sources' ? 600 : 400,
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Source Inventory ({sources.length})
        </button>
        <button
          onClick={() => setActiveTab('snapshots')}
          style={{
            padding: '10px 18px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'snapshots' ? '2px solid var(--text-primary)' : '2px solid transparent',
            color: activeTab === 'snapshots' ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'snapshots' ? 600 : 400,
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Snapshot Provenance ({snapshots.length})
        </button>
        <button
          onClick={() => setActiveTab('reviews')}
          style={{
            padding: '10px 18px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'reviews' ? '2px solid var(--text-primary)' : '2px solid transparent',
            color: activeTab === 'reviews' ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'reviews' ? 600 : 400,
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Reviews & History ({projectReviews.length})
        </button>
      </div>

      {/* TAB 1: ARCHITECTURE & DETECTED PROFILE */}
      {activeTab === 'architecture' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* User Context & Review Adaptation Card */}
          <div
            style={{
              padding: '16px 20px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '14px', fontWeight: 600 }}>Project Context & Review Adaptation</span>
                <Badge variant="outline">Optional User Scope</Badge>
              </div>
              <Button size="sm" variant="ghost" onClick={() => setIsContextModalOpen(true)}>
                Edit Context
              </Button>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '12px',
                fontSize: '12px',
              }}
            >
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Purpose / Scope:</span>
                <p style={{ marginTop: '2px', fontWeight: 500 }}>
                  {project.user_context?.purpose || 'Not specified (will infer from code profile)'}
                </p>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Target Environment:</span>
                <p style={{ marginTop: '2px', fontWeight: 500 }}>
                  {project.user_context?.deployment_env || 'Not specified'}
                </p>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Review Goals:</span>
                <p style={{ marginTop: '2px', fontWeight: 500 }}>
                  {project.user_context?.review_goals || 'Standard comprehensive architecture & security review'}
                </p>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Sensitive Data Notes:</span>
                <p style={{ marginTop: '2px', fontWeight: 500 }}>
                  {project.user_context?.sensitive_data || 'None declared'}
                </p>
              </div>
            </div>
          </div>

          {/* Profile Overview Summary Cards */}
          {profile ? (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '14px',
              }}
            >
              {/* App Type */}
              <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>APPLICATION TYPE</span>
                  <Badge variant="outline">{profile.app_type_status || 'inferred'}</Badge>
                </div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {profile.application_type || 'General Software'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {profile.likely_purpose ? profile.likely_purpose : 'Derived from source files'}
                </div>
              </div>

              {/* Languages */}
              <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>LANGUAGES</span>
                  <Badge variant="outline">detected</Badge>
                </div>
                <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {Object.entries(profile.languages || {})
                    .slice(0, 3)
                    .map(([lang, stat]) => `${lang} (${stat.line_percentage || 0}%)`)
                    .join(', ') || 'None detected'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Total: {Object.keys(profile.languages || {}).length} detected languages
                </div>
              </div>

              {/* Frameworks */}
              <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>FRAMEWORKS</span>
                  <Badge variant="outline">manifest</Badge>
                </div>
                <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {profile.frameworks && profile.frameworks.length > 0
                    ? profile.frameworks.map((f) => `${f.name}${f.version ? ` @ ${f.version}` : ''}`).join(', ')
                    : 'Standard / Vanilla'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {profile.frameworks && profile.frameworks[0]?.evidence?.file_path ? `From ${profile.frameworks[0].evidence.file_path}` : 'Manifest scanned'}
                </div>
              </div>

              {/* Database & Storage */}
              <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>DATABASE & STORAGE</span>
                  <Badge variant="outline">{profile.database_technologies && profile.database_technologies.length > 0 ? 'detected' : 'none'}</Badge>
                </div>
                <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {profile.database_technologies && profile.database_technologies.length > 0
                    ? profile.database_technologies.map((d) => d.name).join(', ')
                    : 'No persistent database configured'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {profile.database_technologies && profile.database_technologies[0]?.evidence?.file_path ? profile.database_technologies[0].evidence.file_path : 'Checked ORMs & configs'}
                </div>
              </div>

              {/* Test Inventory */}
              <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>TEST INVENTORY</span>
                  <Badge variant="outline">{profile.test_frameworks && profile.test_frameworks.length > 0 ? 'detected' : 'missing'}</Badge>
                </div>
                <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {profile.test_frameworks && profile.test_frameworks.length > 0
                    ? profile.test_frameworks.map((t) => t.framework).join(', ')
                    : 'No automated tests detected'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {profile.test_frameworks && profile.test_frameworks.length > 0 ? 'Automated test suite identified' : 'Review flagged test suite absence'}
                </div>
              </div>

              {/* Routes & Endpoints */}
              <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>ROUTES & API</span>
                  <Badge variant="outline">{profile.routes?.length ? `${profile.routes.length} routes` : 'none'}</Badge>
                </div>
                <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>
                  {profile.routes && profile.routes.length > 0
                    ? profile.routes.slice(0, 2).map((r) => `${r.method} ${r.path}`).join(', ') + (profile.routes.length > 2 ? '...' : '')
                    : 'No web endpoints detected'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Deterministic route extractor
                </div>
              </div>
            </div>
          ) : (
            <div style={{ padding: '16px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
              <p className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Project profile is generating or pending source indexing.
              </p>
            </div>
          )}

          {/* Interactive Evidence-Backed Architecture Graph */}
          <ArchitectureGraphView graph={profile?.architecture_graph || { nodes: [], edges: [] }} />
        </div>
      )}

      {/* TAB 2: SOURCE FILES INVENTORY & SEARCH */}
      {activeTab === 'sources' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Search & Filter Toolbar */}
          <div
            style={{
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
              flexWrap: 'wrap',
              padding: '12px 16px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <input
              type="text"
              placeholder="Search file path or name (e.g. app/models)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="mono"
              style={{
                flex: 1,
                minWidth: '220px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 12px',
                fontSize: '12px',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />

            <select
              value={fileTypeFilter}
              onChange={(e) => setFileTypeFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 12px',
                fontSize: '12px',
                color: 'var(--text-primary)',
              }}
            >
              <option value="">All File Types</option>
              {uniqueFileTypes.map((ft) => (
                <option key={ft} value={ft}>
                  .{ft}
                </option>
              ))}
            </select>

            {(searchQuery || fileTypeFilter) && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setSearchQuery('');
                  setFileTypeFilter('');
                }}
              >
                Clear Search
              </Button>
            )}

            <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
              Showing {filteredSources.length} of {sources.length} files
            </span>
          </div>

          {filteredSources.length === 0 ? (
            <EmptyState
              title="No Files Found"
              description="No files match your search criteria. Ingest files using the upload button above."
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
                  {filteredSources.map((s) => (
                    <tr key={s.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
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
      )}

      {/* TAB 3: SNAPSHOT HISTORY */}
      {activeTab === 'snapshots' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Each snapshot is an immutable point-in-time record of your source files. Historical reviews are bound to the specific snapshot they audited.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {snapshots.map((snap) => (
              <div
                key={snap.id}
                className="mono"
                style={{
                  padding: '16px 20px',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: snap.is_current ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '13px',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <strong>Commit: {snap.commit_sha ? snap.commit_sha.slice(0, 10) : 'Local HEAD'}</strong>
                    {snap.is_current && <Badge variant="outline">Active Snapshot</Badge>}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '4px' }}>
                    Snapshot ID: {snap.id} | Sources: {snap.source_count} | Size: {Math.round(snap.total_size_bytes / 1024)} KB
                  </div>
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                  Created: {new Date(snap.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: REVIEWS & QUALITY HISTORY (SCOPED EXCLUSIVELY TO THIS PROJECT) */}
      {activeTab === 'reviews' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Project Reviews ({projectReviews.length})</h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Multi-agent reviews conducted strictly for this project snapshot.
              </p>
            </div>
            <Link href={`/reviews?project_id=${project.id}`}>
              <Button variant="primary">+ Run New Review</Button>
            </Link>
          </div>

          {projectReviews.length === 0 ? (
            <EmptyState
              title="No Reviews Run Yet"
              description="No multi-agent reviews have been conducted for this project yet. Start a review to inspect code hygiene, security risks, and architecture."
              actionText="Start Project Review"
              onAction={() => { window.location.href = `/reviews?project_id=${project.id}`; }}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {projectReviews.map((rev) => (
                <div
                  key={rev.id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '16px',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Badge variant="status" value={rev.status}>
                        {rev.status}
                      </Badge>
                      <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        {rev.provider_used ? `AI: ${rev.provider_used}` : `Mode: ${rev.provider_mode}`}
                      </span>
                      {rev.commit_sha && (
                        <span className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          sha:{rev.commit_sha.slice(0, 7)}
                        </span>
                      )}
                    </div>
                    <Link
                      href={`/reviews/${rev.id}`}
                      style={{
                        fontSize: '15px',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                        textDecoration: 'none',
                      }}
                    >
                      {rev.question}
                    </Link>
                    <div className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                      Findings: <strong style={{ color: 'var(--text-primary)' }}>{rev.total_findings}</strong> | Citation Coverage:{' '}
                      <strong style={{ color: '#10b981' }}>
                        {typeof rev.evidence_verification_summary?.citation_coverage_score === 'number'
                          ? `${Math.round(rev.evidence_verification_summary.citation_coverage_score * 100)}%`
                          : '100%'}
                      </strong>{' '}
                      | Elapsed: {rev.elapsed_seconds}s
                    </div>
                  </div>

                  <Link href={`/reviews/${rev.id}`}>
                    <Button variant="secondary" size="sm">
                      View Review Report →
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* User Context Editor Modal */}
      <Modal
        isOpen={isContextModalOpen}
        onClose={() => setIsContextModalOpen(false)}
        title="Project Context & Review Adaptation Scope"
        width="650px"
      >
        <form onSubmit={handleSaveContext} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Provide optional domain context to tailor specialist agent queries and risk scoring. These user-provided details remain distinct from automatically detected code profiles.
          </p>

          <Input
            label="Project Purpose / Application Domain"
            placeholder="e.g. Healthcare patient portal handling sensitive telemetry"
            value={contextForm.purpose}
            onChange={(e) => setContextForm({ ...contextForm, purpose: e.target.value })}
          />

          <Input
            label="Target Deployment Environment"
            placeholder="e.g. AWS ECS Fargate, Kubernetes cluster, or Local CLI"
            value={contextForm.deployment_env}
            onChange={(e) => setContextForm({ ...contextForm, deployment_env: e.target.value })}
          />

          <Input
            label="Review Goals / Focus Areas"
            placeholder="e.g. Focus on OWASP Top 10 API security and dependency vulnerabilities"
            value={contextForm.review_goals}
            onChange={(e) => setContextForm({ ...contextForm, review_goals: e.target.value })}
          />

          <Input
            label="Sensitive Data Handled"
            placeholder="e.g. PII, HIPAA medical records, API keys, Payment tokens"
            value={contextForm.sensitive_data}
            onChange={(e) => setContextForm({ ...contextForm, sensitive_data: e.target.value })}
          />

          <Input
            label="Intended Users / Access Tiers"
            placeholder="e.g. Public unauthenticated users and enterprise administrators"
            value={contextForm.intended_users}
            onChange={(e) => setContextForm({ ...contextForm, intended_users: e.target.value })}
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
            <Button type="button" variant="ghost" onClick={() => setIsContextModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={savingContext}>
              Save Context
            </Button>
          </div>
        </form>
      </Modal>

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
                <div>
                  <strong>Commit: {snap.commit_sha ? snap.commit_sha.slice(0, 10) : 'HEAD'}</strong>{' '}
                  {snap.is_current && <Badge variant="outline">Current</Badge>}
                </div>
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