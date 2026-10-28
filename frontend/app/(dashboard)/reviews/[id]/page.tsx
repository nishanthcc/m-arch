'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api/client';
import { Review, Finding, EvidenceItem, ReviewReport } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ReviewProgressTimeline } from '@/components/reviews/ReviewProgressTimeline';
import { FindingCard } from '@/components/reviews/FindingCard';
import { EvidenceDrawer } from '@/components/reviews/EvidenceDrawer';
import { ExportReportModal } from '@/components/reviews/ExportReportModal';
import { EmptyState } from '@/components/ui/EmptyState';

export default function ReviewDetailPage() {
  const params = useParams();
  const reviewId = params.id as string;

  const [review, setReview] = useState<Review | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

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
    } catch (err) {
      console.error('Error fetching review:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!reviewId) return;
    fetchReviewAndFindings();

    // Setup Server-Sent Events (SSE) live progress listener
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
      const report = await api.getReviewReport(reviewId);
      setReportData(report);
      setIsExportOpen(true);
    } catch (err: any) {
      alert(err.message || 'Failed to fetch report');
    }
  };

  if (loading && !review) {
    return <p className="mono">Connecting to review stream...</p>;
  }

  if (!review) {
    return <p>Review not found.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <Link href="/reviews" style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              ← All Reviews
            </Link>
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

        <div style={{ display: 'flex', gap: '12px' }}>
          <Button variant="secondary" onClick={fetchReviewAndFindings}>
            ↻ Refresh
          </Button>
          <Button variant="primary" onClick={handleOpenExport}>
            Export Technical Report
          </Button>
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
          Snapshot Commit SHA:{' '}
          <strong style={{ color: 'var(--text-primary)' }}>
            {review.commit_sha ? review.commit_sha.slice(0, 10) : 'Local Workspace Snapshot'}
          </strong>
        </div>
        <div>
          Source Snapshot ID:{' '}
          <span style={{ color: 'var(--text-secondary)' }}>
            {review.source_snapshot_id || 'snap_local_v1'}
          </span>
        </div>
        <div>
          Provider Executed:{' '}
          <strong style={{ color: 'var(--text-primary)' }}>
            {review.provider_used || 'Groq'} ({review.model_used || 'llama-3.3-70b'})
          </strong>
        </div>
      </div>

      {/* Evidence Verifier Quality Gate Summary Banner */}
      {review.evidence_verification_summary && (
        <div
          className="mono"
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            fontSize: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Badge variant="outline">Quality Gate v1.1.0</Badge>
            <span style={{ fontWeight: 600 }}>Evidence & Citation Verifier</span>
          </div>
          <div>
            Verified Findings:{' '}
            <strong style={{ color: '#10b981' }}>
              {review.evidence_verification_summary.verified_count || review.total_findings}
            </strong>
          </div>
          <div>
            Filtered Claims (Insufficient Citation):{' '}
            <strong style={{ color: review.evidence_verification_summary.rejected_count ? '#f87171' : 'var(--text-muted)' }}>
              {review.evidence_verification_summary.rejected_count || 0}
            </strong>
          </div>
          <div>
            Citation Coverage:{' '}
            <strong style={{ color: 'var(--text-primary)' }}>
              {Math.round((review.evidence_verification_summary.citation_coverage_score || 1.0) * 100)}%
            </strong>
          </div>
        </div>
      )}

      {/* A2A Task Progress Timeline */}
      <ReviewProgressTimeline tasks={review.tasks || []} overallStatus={review.status} />

      {/* Synthesis Summary & Limitations */}
      {(review.summary || review.limitations) && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
          <Card title="Executive Architectural Synthesis">
            <div style={{ fontSize: '14px', lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
              {review.summary}
            </div>
          </Card>

          <Card title="Scope & Explicit Limitations">
            <div
              className="mono"
              style={{ fontSize: '12px', lineHeight: 1.5, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}
            >
              {review.limitations || 'Static inspection conducted. Runtime test execution was not run.'}
            </div>
          </Card>
        </div>
      )}

      {/* Findings Section */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '17px', fontWeight: 600 }}>
            Grounded Findings ({findings.length})
          </h3>
        </div>

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
            <option value="static_analysis">Static Analysis</option>
            <option value="inference">Inference</option>
            <option value="manual_review_required">Manual Review Required</option>
            <option value="tested">Tested</option>
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
        {findings.length === 0 ? (
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
        report={reportData}
      />
    </div>
  );
}
