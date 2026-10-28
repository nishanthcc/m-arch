'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/client';
import { Project, Review } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';

export default function OverviewPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getProjects(), api.getReviews()])
      .then(([projs, revs]) => {
        setProjects(projs);
        setReviews(revs);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const totalSources = projects.reduce((acc, p) => acc + (p.source_count || 0), 0);
  const totalFindings = reviews.reduce((acc, r) => acc + (r.total_findings || 0), 0);
  const completedReviews = reviews.filter((r) => r.status === 'completed' || r.status === 'partial').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>System Overview</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Multi-agent project review telemetry and verified engineering findings.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Link href="/projects">
            <Button variant="secondary">Catalog Projects</Button>
          </Link>
          <Link href="/reviews">
            <Button variant="primary">New Review</Button>
          </Link>
        </div>
      </div>

      {/* Real Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
        }}
      >
        <Card>
          <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            ACTIVE PROJECTS
          </span>
          <div className="mono" style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {loading ? '-' : projects.length}
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Configured in local SQLite
          </span>
        </Card>

        <Card>
          <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            INGESTED SOURCES
          </span>
          <div className="mono" style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {loading ? '-' : totalSources}
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Indexed into FTS5 & Vectors
          </span>
        </Card>

        <Card>
          <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            REVIEWS EXECUTED
          </span>
          <div className="mono" style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {loading ? '-' : completedReviews}
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            A2A multi-agent traces
          </span>
        </Card>

        <Card>
          <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            VERIFIED FINDINGS
          </span>
          <div className="mono" style={{ fontSize: '32px', fontWeight: 700, marginTop: '8px' }}>
            {loading ? '-' : totalFindings}
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Grounded in code evidence
          </span>
        </Card>
      </div>

      {/* Main Content: Recent Reviews or Empty State */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Recent Engineering Reviews</h3>
          {reviews.length > 0 && (
            <Link href="/reviews">
              <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                View All Reviews →
              </span>
            </Link>
          )}
        </div>

        {loading ? (
          <p className="mono" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Loading reviews from local database...
          </p>
        ) : reviews.length === 0 ? (
          <EmptyState
            title="No Reviews Run Yet"
            description="Add a repository or project files, and execute a multi-agent review to produce evidence-backed findings."
            actionText="Go to Projects"
            onAction={() => window.location.href = '/projects'}
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {reviews.slice(0, 5).map((rev) => (
              <Link key={rev.id} href={`/reviews/${rev.id}`}>
                <div
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px 20px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                      <Badge variant="status" value={rev.status}>
                        {rev.status}
                      </Badge>
                      <span className="mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Mode: {rev.provider_mode}
                      </span>
                      {rev.fallback_occurred && (
                        <span className="mono" style={{ fontSize: '11px', color: 'var(--status-partial)' }}>
                          [FALLBACK OCCURRED]
                        </span>
                      )}
                    </div>
                    <h4 style={{ fontSize: '15px', fontWeight: 600 }}>{rev.question}</h4>
                  </div>

                  <div className="mono" style={{ textAlign: 'right', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <div>
                      <strong style={{ color: 'var(--text-primary)' }}>{rev.total_findings}</strong> findings
                    </div>
                    <div>{rev.elapsed_seconds > 0 ? `${rev.elapsed_seconds}s` : 'In progress'}</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
