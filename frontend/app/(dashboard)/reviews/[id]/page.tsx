'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api/client';
import { Review, Finding, EvidenceItem, ReviewReport, Project, ProjectProfile } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ReviewProgressTimeline } from '@/components/reviews/ReviewProgressTimeline';
import { FindingCard } from '@/components/reviews/FindingCard';
import { EvidenceDrawer } from '@/components/reviews/EvidenceDrawer';
import { ExportReportModal } from '@/components/reviews/ExportReportModal';
import { EmptyState } from '@/components/ui/EmptyState';
import { StructuredMarkdownViewer } from '@/components/ui/StructuredMarkdownViewer';

export default function ReviewDetailPage() {
  const params = useParams();
  const reviewId = params.id as string;

  const [review, setReview] = useState<Review | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [profile, setProfile] = useState<ProjectProfile | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [auditing, setAuditing] = useState(false);
  const [auditMessage, setAuditMessage] = useState<string | null>(null);

  // Presentation Mode: 'developer' | 'simple' | 'professional' | 'executive'
  const [presentationMode, setPresentationMode] = useState<'developer' | 'simple' | 'professional' | 'executive'>('developer');

  // Filters
  const [severityFilter, setSeverityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [agentFilter, setAgentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [manualReviewOnly, setManualReviewOnly] = useState(false);

  // Modals & Drawers
  const [activeEvidence, setActiveEvidence] = useState<{ items: EvidenceItem[]; title: string } | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [reportData, setReportData] = useState<ReviewReport | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  const fetchReviewAndFindings = async () => {
    try {
      const [rev, fnd] = await Promise.all([
        api.getReview(reviewId),
        api.getReviewFindings(reviewId, {
          severity: severityFilter || undefined,
          category: categoryFilter || undefined,
          agent_id: agentFilter || undefined,
          verification_status: statusFilter || undefined,
          manual_review_only: manualReviewOnly || undefined,
        }),
      ]);
      setReview(rev);
      setFindings(fnd);

      if (rev && rev.project_id) {
        Promise.all([
          api.getProject(rev.project_id).catch(() => null),
          api.getProjectProfile(rev.project_id).catch(() => null),
        ]).then(([p, prof]) => {
          if (p) setProject(p);
          if (prof) setProfile(prof);
        });
      }
    } catch (err) {
      console.error('Error fetching review:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!reviewId) return;
    fetchReviewAndFindings();

    // Server-Sent Events (SSE) live progress listener
    const sseUrl = api.getReviewEventsUrl(reviewId);
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('SSE Review Event:', data);
        fetchReviewAndFindings();
      } catch (_) {}
    };

    es.addEventListener('task_completed', () => fetchReviewAndFindings());
    es.addEventListener('verification_completed', () => fetchReviewAndFindings());
    es.addEventListener('review_completed', () => {
      fetchReviewAndFindings();
      es.close();
    });

    es.onerror = () => {
      fetchReviewAndFindings();
    };

    return () => {
      es.close();
    };
  }, [reviewId, severityFilter, categoryFilter, agentFilter, statusFilter, manualReviewOnly]);

  const handleOpenExport = async () => {
    try {
      const report = await api.getReviewReport(reviewId, presentationMode);
      setReportData(report);
      setIsExportOpen(true);
    } catch (err: any) {
      alert(err.message || 'Failed to fetch report');
    }
  };

  const handleTriggerAudit = async () => {
    setAuditing(true);
    setAuditMessage(null);
    try {
      const res = await api.verifyReviewAudit(reviewId, presentationMode);
      setReportData(res);
      await fetchReviewAndFindings();
      setAuditMessage('Review snapshot audit completed! Findings and evidence re-verified.');
      setTimeout(() => setAuditMessage(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Audit failed');
    } finally {
      setAuditing(false);
    }
  };

  if (loading && !review) {
    return <p className="mono" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Connecting to review stream...</p>;
  }

  if (!review) {
    return <p>Review not found.</p>;
  }

  // Active Presentation View Content
  const activeView = review.presentation_views ? review.presentation_views[presentationMode] : null;

  // Severity Counts
  const severityCounts = {
    critical: findings.filter((f) => f.severity === 'critical').length,
    high: findings.filter((f) => f.severity === 'high').length,
    medium: findings.filter((f) => f.severity === 'medium').length,
    low: findings.filter((f) => f.severity === 'low').length,
    informational: findings.filter((f) => f.severity === 'informational').length,
  };

  // Specialist Breakdown
  const specialistCounts: Record<string, number> = {};
  findings.forEach((f) => {
    const agents = f.agent_id.split(',').map((a) => a.trim());
    agents.forEach((ag) => {
      specialistCounts[ag] = (specialistCounts[ag] || 0) + 1;
    });
  });

  const verificationSummary = review.evidence_verification_summary || {};
  const totalProjectFiles = verificationSummary.total_files ?? (project?.source_count || 0);
  const filesAnalyzed = verificationSummary.files_analyzed ?? 0;
  const filesSkipped = verificationSummary.files_skipped ?? Math.max(0, totalProjectFiles - filesAnalyzed);

  // Top risks for lead section
  const mainRisks = findings.filter((f) => ['critical', 'high', 'medium'].includes(f.severity)).slice(0, 3);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Link href="/reviews" style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              ← All Reviews
            </Link>
            {project && (
              <>
                <span style={{ color: 'var(--border-subtle)' }}>/</span>
                <Link href={`/projects/${project.id}`} style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                  {project.name}
                </Link>
              </>
            )}
            <Badge variant="status" value={review.status}>
              {review.status}
            </Badge>
            <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              Mode: {review.provider_mode}
            </span>
            {review.fallback_occurred && (
              <span className="mono" style={{ fontSize: '11px', color: 'var(--status-partial)' }}>
                [FALLBACK TRIGGERED]
              </span>
            )}
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 700 }}>{review.question}</h1>
          <p className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Review ID: {review.id} | Elapsed: {review.elapsed_seconds > 0 ? `${review.elapsed_seconds}s` : 'Active'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Button variant="secondary" onClick={handleTriggerAudit} disabled={auditing}>
            {auditing ? 'Auditing Snapshot...' : 'Audit & Verify Snapshot'}
          </Button>
          <Button variant="secondary" onClick={fetchReviewAndFindings}>
            ↻ Refresh
          </Button>
          <Button variant="primary" onClick={handleOpenExport}>
            Export Technical Report
          </Button>
        </div>
      </div>

      {auditMessage && (
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 16px',
            fontSize: '13px',
            color: '#10b981',
          }}
        >
          ✓ {auditMessage}
        </div>
      )}

      {/* LEAD SECTION 1: WHAT THE PROJECT APPEARS TO DO & SNAPSHOT CONTEXT */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: '20px 24px',
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: '24px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Badge variant="outline">Project Purpose & Scope</Badge>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              {profile?.likely_purpose ? `(${profile.likely_purpose.length > 50 ? 'Extracted' : 'Determined'})` : 'Snapshot Evaluation'}
            </span>
          </div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            {profile?.application_type || 'Software Application Snapshot'}
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
            {profile?.likely_purpose ||
              project?.description ||
              'Software project inspected through immutable snapshot sources and multi-agent retrieval.'}
          </p>

          {profile?.frameworks && profile.frameworks.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '12px' }}>
              {profile.frameworks.map((fw, idx) => (
                <span
                  key={idx}
                  className="mono"
                  style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                  }}
                >
                  {fw.name} {fw.version ? `(${fw.version})` : ''}
                </span>
              ))}
            </div>
          )}
        </div>

        <div
          className="mono"
          style={{
            borderLeft: '1px solid var(--border-subtle)',
            paddingLeft: '20px',
            fontSize: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            justifyContent: 'center',
          }}
        >
          <div>
            Snapshot Commit:{' '}
            <strong style={{ color: 'var(--text-primary)' }}>
              {review.commit_sha ? review.commit_sha.slice(0, 10) : 'Local Workspace Snapshot'}
            </strong>
          </div>
          <div>
            Snapshot ID:{' '}
            <span style={{ color: 'var(--text-secondary)' }}>
              {review.source_snapshot_id || 'snap_active'}
            </span>
          </div>
          <div>
            AI Providers:{' '}
            <strong style={{ color: 'var(--text-primary)' }}>
              {review.provider_used || review.provider_mode}
            </strong>{' '}
            <span style={{ color: 'var(--text-muted)' }}>
              ({review.model_used || 'Standard'})
            </span>
            {review.tasks?.some((t) => t.provider_used === 'Gemini' || t.agent_id === 'code_agent') && (
              <span
                style={{
                  marginLeft: '8px',
                  fontSize: '10px',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  color: '#10b981',
                  fontWeight: 600,
                }}
              >
                ● Gemini Code Agent
              </span>
            )}
          </div>
          <div>
            Verification Gate:{' '}
            <strong style={{ color: '#10b981' }}>
              {verificationSummary.verified_count ?? review.total_findings} verified
            </strong>{' '}
            <span style={{ color: 'var(--text-muted)' }}>
              ({verificationSummary.unsupported_count ?? 0} filtered)
            </span>
          </div>
        </div>
      </div>

      {/* FOCUSED METRIC CARDS (Tesla Dashboard Inspiration: Matte, Clean 1px Borders, Restrained) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        {/* Card 1: Findings by Severity */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Findings by Severity
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, margin: '8px 0 12px 0', color: 'var(--text-primary)' }}>
            {findings.length}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#ef4444' }}>Critical</span>
              <strong className="mono">{severityCounts.critical}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#f97316' }}>High</span>
              <strong className="mono">{severityCounts.high}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#eab308' }}>Medium</span>
              <strong className="mono">{severityCounts.medium}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#3b82f6' }}>Low / Informational</span>
              <strong className="mono">{severityCounts.low + severityCounts.informational}</strong>
            </div>
          </div>
        </div>

        {/* Card 2: Source Coverage */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Source Coverage
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, margin: '8px 0 12px 0', color: 'var(--text-primary)' }}>
            {totalProjectFiles > 0 ? `${filesAnalyzed}/${totalProjectFiles}` : `${filesAnalyzed} Files`}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Code Files Analyzed</span>
              <strong className="mono" style={{ color: '#10b981' }}>{filesAnalyzed}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Media/Binary Skipped</span>
              <strong className="mono">{filesSkipped}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Coverage Ratio</span>
              <strong className="mono">
                {totalProjectFiles > 0 ? `${Math.round((filesAnalyzed / totalProjectFiles) * 100)}%` : '100%'}
              </strong>
            </div>
          </div>
        </div>

        {/* Card 3: Findings by Specialist */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Specialist Contributions
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, margin: '8px 0 12px 0', color: 'var(--text-primary)' }}>
            {review.tasks?.filter((t) => t.status === 'completed').length || 0} Agents
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11px' }}>
            {Object.keys(specialistCounts).length > 0 ? (
              Object.entries(specialistCounts).map(([ag, count]) => (
                <div key={ag} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{ag.replace('_', ' ')}</span>
                  <strong className="mono">{count}</strong>
                </div>
              ))
            ) : (
              <span style={{ color: 'var(--text-muted)' }}>No specialist findings</span>
            )}
          </div>
        </div>

        {/* Card 4: Quality & Verification Gate */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
          }}
        >
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Citation Coverage
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, margin: '8px 0 12px 0', color: '#10b981' }}>
            {typeof verificationSummary.citation_coverage_score === 'number'
              ? `${Math.round(verificationSummary.citation_coverage_score * 100)}%`
              : '100%'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Verified Grounded</span>
              <strong className="mono" style={{ color: '#10b981' }}>
                {verificationSummary.verified_count ?? review.total_findings}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Filtered / Drifted</span>
              <strong className="mono" style={{ color: verificationSummary.unsupported_count ? '#ef4444' : 'var(--text-muted)' }}>
                {verificationSummary.unsupported_count ?? 0}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Execution Time</span>
              <strong className="mono">{review.elapsed_seconds}s</strong>
            </div>
          </div>
        </div>
      </div>

      {/* LEAD SECTION 2 & 3: WHAT WAS REVIEWED & MAIN RISKS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* What was reviewed */}
        <Card title="Source Analysis & File Coverage">
          <p style={{ fontSize: '13px', lineHeight: 1.6, color: 'var(--text-secondary)', margin: 0 }}>
            {verificationSummary.coverage_statement ||
              `Static inspection analyzed code files belonging to snapshot ${review.source_snapshot_id || 'active'}.`}
          </p>
          <div
            className="mono"
            style={{
              marginTop: '12px',
              padding: '10px 14px',
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11px',
              color: 'var(--text-muted)',
            }}
          >
            NOTE: Non-code media assets (.jpg, .png, datasets, outputs) are indexed for metadata but skipped during static AST/code analysis.
          </div>
        </Card>

        {/* Main Risks Found */}
        <Card title="Primary Risks Identified">
          {mainRisks.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {mainRisks.map((risk) => (
                <div
                  key={risk.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    backgroundColor: 'var(--bg-elevated)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '12px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge variant="severity" value={risk.severity}>
                      {risk.severity}
                    </Badge>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{risk.title}</span>
                  </div>
                  <Badge variant="verification" value={risk.verification_status}>
                    {risk.verification_status}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              No critical or high severity defects identified during static inspection.
            </div>
          )}
        </Card>
      </div>

      {/* A2A Agent Coordination Timeline */}
      <ReviewProgressTimeline tasks={review.tasks || []} overallStatus={review.status} />

      {/* PRESENTATION MODE TABS WITH ZERO RAW MARKDOWN */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', gap: '8px' }}>
          {(
            [
              { id: 'developer', label: 'Developer Review', subtitle: 'Technical & Remediation' },
              { id: 'simple', label: 'Simple English', subtitle: 'Plain Language' },
              { id: 'professional', label: 'Professional Report', subtitle: 'Stakeholder & Audit' },
              { id: 'executive', label: 'Executive Summary', subtitle: 'Risk & Strategy' },
            ] as const
          ).map((m) => (
            <button
              key={m.id}
              onClick={() => setPresentationMode(m.id)}
              style={{
                padding: '10px 16px',
                background: 'none',
                border: 'none',
                borderBottom: presentationMode === m.id ? '2px solid var(--text-primary)' : '2px solid transparent',
                color: presentationMode === m.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: presentationMode === m.id ? 600 : 400,
                cursor: 'pointer',
                fontSize: '13px',
                textAlign: 'left',
              }}
            >
              <div>{m.label}</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{m.subtitle}</div>
            </button>
          ))}
        </div>

        {/* Synthesis & Limitations Display (Structured rendering, zero raw hashes/asterisks) */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
          <Card title={`${presentationMode.toUpperCase()} SYNTHESIS`}>
            {/* Structured markdown parser: renders real HTML elements */}
            <StructuredMarkdownViewer
              content={
                activeView && activeView.markdown
                  ? activeView.markdown
                  : activeView?.summary || review.summary || 'Review synthesis complete.'
              }
            />
          </Card>

          <Card title="Scope & Explicit Limitations">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div
                style={{
                  padding: '10px 14px',
                  backgroundColor: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  color: '#f87171',
                  lineHeight: 1.5,
                }}
              >
                <strong>Production Certification Notice:</strong>
                <p style={{ margin: '4px 0 0 0' }}>
                  Static code and configuration review cannot certify an application as fully secure or production-ready. Dynamic runtime vulnerabilities, infrastructure security, and live environment configurations require manual verification.
                </p>
              </div>

              <StructuredMarkdownViewer
                content={
                  review.limitations ||
                  'Evaluated strictly through static inspection and RAG retrieval over project snapshot. Code was not dynamically executed.'
                }
              />
            </div>
          </Card>
        </div>
      </div>

      {/* CANONICAL FINDINGS SECTION */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 600 }}>
            Canonical Verified Findings ({findings.length})
          </h3>
        </div>

        {/* Clean scan notice when no findings */}
        {findings.length === 0 && review.status === 'completed' && (
          <div
            style={{
              padding: '20px 24px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Badge variant="status" value="ready">Clean Scan</Badge>
              <strong style={{ fontSize: '15px' }}>No critical static findings detected.</strong>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '8px', lineHeight: 1.5 }}>
              The multi-agent inspection found no critical defects or ungrounded vulnerabilities within the evaluated snapshot source files.
              Static analysis cannot certify the software as entirely secure or production-ready, as runtime interactions, dynamic data handling, and external hosting configurations require separate validation.
            </p>
          </div>
        )}

        {/* Filters Bar */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '12px',
            alignItems: 'center',
            padding: '12px 16px',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '16px',
            fontSize: '13px',
          }}
        >
          <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            FILTERS:
          </span>

          {/* Severity */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 8px',
              fontSize: '12px',
              color: 'var(--text-primary)',
            }}
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="informational">Informational</option>
          </select>

          {/* Agent */}
          <select
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 8px',
              fontSize: '12px',
              color: 'var(--text-primary)',
            }}
          >
            <option value="">All Agents</option>
            <option value="code_agent">Code Agent</option>
            <option value="security_agent">Security Agent</option>
            <option value="documentation_agent">Documentation Agent</option>
            <option value="dependency_agent">Dependency Agent</option>
          </select>

          {/* Verification Status */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 8px',
              fontSize: '12px',
              color: 'var(--text-primary)',
            }}
          >
            <option value="">All Verification Statuses</option>
            <option value="verified">Verified</option>
            <option value="partially_supported">Partially Supported</option>
            <option value="unsupported">Unsupported</option>
            <option value="duplicate">Duplicate</option>
            <option value="not_verifiable">Not Verifiable</option>
          </select>

          {/* Manual Review Only */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '12px' }}>
            <input
              type="checkbox"
              checked={manualReviewOnly}
              onChange={(e) => setManualReviewOnly(e.target.checked)}
            />
            <span>Manual Review Required</span>
          </label>

          {(severityFilter || categoryFilter || agentFilter || statusFilter || manualReviewOnly) && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setSeverityFilter('');
                setCategoryFilter('');
                setAgentFilter('');
                setStatusFilter('');
                setManualReviewOnly(false);
              }}
            >
              Clear Filters
            </Button>
          )}
        </div>

        {/* Findings List */}
        {findings.length === 0 && review.status !== 'completed' ? (
          <EmptyState
            title="No Findings Match Filter"
            description="Adjust your filters or allow the specialist agents to finish retrieving evidence."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {findings.map((finding) => (
              <FindingCard
                key={finding.id}
                finding={finding}
                onViewEvidence={(evItems, title) => setActiveEvidence({ items: evItems, title })}
              />
            ))}
          </div>
        )}
      </div>

      {/* Side Evidence Drawer */}
      <EvidenceDrawer
        isOpen={Boolean(activeEvidence)}
        onClose={() => setActiveEvidence(null)}
        title={activeEvidence?.title || 'Evidence Viewer'}
        evidence={activeEvidence?.items || []}
      />

      {/* Export Report Modal */}
      <ExportReportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        reviewId={review.id}
        report={reportData}
        initialMode={presentationMode}
      />
    </div>
  );
}
