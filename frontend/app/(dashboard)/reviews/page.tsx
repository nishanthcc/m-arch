'use client';

import React, { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api/client';
import { Project, Review, AIMode } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { EmptyState } from '@/components/ui/EmptyState';

function ReviewsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const defaultProjectId = searchParams.get('project_id') || '';

  const [projects, setProjects] = useState<Project[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [selectedProjectId, setSelectedProjectId] = useState(defaultProjectId);
  const [question, setQuestion] = useState('Is this project ready for production?');
  const [scope, setScope] = useState('full');
  const [providerMode, setProviderMode] = useState<AIMode>('Auto');
  const [selectedAgents, setSelectedAgents] = useState<string[]>([
    'code_agent',
    'security_agent',
    'documentation_agent',
    'dependency_agent',
  ]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([api.getProjects(), api.getReviews()])
      .then(([projs, revs]) => {
        setProjects(projs);
        setReviews(revs);
        if (!selectedProjectId && projs.length > 0) {
          setSelectedProjectId(projs[0].id);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleAgentToggle = (agentId: string) => {
    if (selectedAgents.includes(agentId)) {
      if (selectedAgents.length === 1) return; // Keep at least one
      setSelectedAgents(selectedAgents.filter((a) => a !== agentId));
    } else {
      setSelectedAgents([...selectedAgents, agentId]);
    }
  };

  const handleStartReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) {
      alert('Please select or create a project first.');
      return;
    }
    setSubmitting(true);
    try {
      const review = await api.createReview({
        project_id: selectedProjectId,
        question,
        scope,
        selected_agents: selectedAgents,
        provider_mode: providerMode,
      });
      router.push(`/reviews/${review.id}`);
    } catch (err: any) {
      alert(err.message || 'Failed to start review');
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Engineering Reviews</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Dispatch A2A specialist agents to inspect repository code and generate evidence-verified reviews.
        </p>
      </div>

      {/* New Review Launch Card */}
      <Card
        title="Start Multi-Agent Project Review"
        subtitle="Configure the inquiry scope, select active specialist agents, and choose inference routing."
      >
        <form onSubmit={handleStartReview} style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Project Selector */}
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Target Project
              </label>
              {projects.length === 0 ? (
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  No projects available.{' '}
                  <Link href="/projects" style={{ textDecoration: 'underline' }}>
                    Create or import one first →
                  </Link>
                </div>
              ) : (
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  style={{
                    width: '100%',
                    backgroundColor: 'var(--bg-primary)',
                    border: '1px solid var(--border-strong)',
                    borderRadius: 'var(--radius-md)',
                    padding: '8px 12px',
                    fontSize: '14px',
                    color: 'var(--text-primary)',
                    outline: 'none',
                  }}
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.source_count} sources{p.current_commit_sha ? ` • ${p.current_commit_sha.slice(0, 7)}` : ''})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* AI Provider Mode */}
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                AI Inference Routing Mode
              </label>
              <select
                value={providerMode}
                onChange={(e) => setProviderMode(e.target.value as AIMode)}
                style={{
                  width: '100%',
                  backgroundColor: 'var(--bg-primary)',
                  border: '1px solid var(--border-strong)',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 12px',
                  fontSize: '14px',
                  color: 'var(--text-primary)',
                  outline: 'none',
                }}
              >
                <option value="Auto">Auto (Gemini for Code Agent + Groq Primary → Ollama Fallback)</option>
                <option value="Groq">Groq (Cloud Accelerated Only)</option>
                <option value="Ollama">Ollama (100% Local Inference Only)</option>
                <option value="Hybrid">Hybrid (Role-Based Task Routing)</option>
              </select>
            </div>
          </div>

          {/* Question / Inquiry */}
          <Input
            label="Review Question or Scope Prompt"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Is this project ready for production? Are there any security or test gaps?"
            required
          />

          {/* Specialist Agents Selector */}
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
              Active A2A Specialist Agents
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
              {[
                { id: 'code_agent', name: 'Code & Testing Specialist', desc: 'Architecture, tests, and resilience', providerTag: 'Google Gemini (gemini-3.1-flash-lite)' },
                { id: 'security_agent', name: 'Security Specialist', desc: 'Secrets, CWE patterns, and config review', providerTag: 'Groq Cloud' },
                { id: 'documentation_agent', name: 'Documentation Specialist', desc: 'README, deployment, ops readiness', providerTag: 'Groq Cloud' },
                { id: 'dependency_agent', name: 'Dependency Specialist', desc: 'Manifests, unpinned versions, lockfiles', providerTag: 'Groq Cloud' },
              ].map((ag) => {
                const checked = selectedAgents.includes(ag.id);
                return (
                  <div
                    key={ag.id}
                    onClick={() => handleAgentToggle(ag.id)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: checked ? 'var(--bg-elevated)' : 'var(--bg-primary)',
                      border: checked ? '1px solid var(--border-strong)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {}}
                      style={{ marginTop: '3px' }}
                    />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '13px', fontWeight: 600 }}>{ag.name}</span>
                        {ag.id === 'code_agent' && (
                          <span
                            className="mono"
                            style={{
                              fontSize: '10px',
                              padding: '1px 6px',
                              borderRadius: '4px',
                              backgroundColor: 'rgba(16, 185, 129, 0.15)',
                              color: '#10b981',
                              fontWeight: 600,
                            }}
                          >
                            Gemini API
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {ag.desc} • <span className="mono" style={{ color: 'var(--text-muted)' }}>{ag.providerTag}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '8px' }}>
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={submitting}
              disabled={projects.length === 0}
            >
              Launch Review →
            </Button>
          </div>
        </form>
      </Card>

      {/* Review History */}
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Review History</h3>
        {loading ? (
          <p className="mono">Loading reviews...</p>
        ) : reviews.length === 0 ? (
          <EmptyState
            title="No Reviews Found"
            description="Launch a new engineering review above to inspect code and see agent traces."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {reviews.map((rev) => (
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
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--border-strong)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <Badge variant="status" value={rev.status}>
                        {rev.status}
                      </Badge>
                      {rev.commit_sha && (
                        <Badge variant="outline">
                          <span className="mono">sha:{rev.commit_sha.slice(0, 7)}</span>
                        </Badge>
                      )}
                      <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        Mode: {rev.provider_mode}
                      </span>
                      {rev.fallback_occurred && (
                        <span className="mono" style={{ fontSize: '11px', color: 'var(--status-partial)' }}>
                          [FALLBACK OCCURRED]
                        </span>
                      )}
                    </div>
                    <h4 style={{ fontSize: '15px', fontWeight: 600 }}>{rev.question}</h4>
                    {rev.evidence_verification_summary && (
                      <p className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Gate: {rev.evidence_verification_summary.verified_count || rev.total_findings} verified,{' '}
                        {rev.evidence_verification_summary.rejected_count || 0} claims filtered
                      </p>
                    )}
                  </div>

                  <div className="mono" style={{ textAlign: 'right', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <div>
                      <strong style={{ color: 'var(--text-primary)' }}>{rev.total_findings}</strong> verified findings
                    </div>
                    <div>{rev.elapsed_seconds > 0 ? `${rev.elapsed_seconds}s` : 'Processing'}</div>
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

export default function ReviewsPage() {
  return (
    <Suspense fallback={<p className="mono">Loading reviews...</p>}>
      <ReviewsContent />
    </Suspense>
  );
}
