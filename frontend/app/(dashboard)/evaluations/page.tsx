'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/client';
import { EvaluationDataset, EvaluationRun, SystemMetrics, Project, MetricRatio } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';

export default function EvaluationsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(''); // '' = All Projects
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [metricsLoading, setMetricsLoading] = useState(false);

  // New Dataset Modal
  const [isDatasetOpen, setIsDatasetOpen] = useState(false);
  const [datasetName, setDatasetName] = useState('');
  const [datasetDesc, setDatasetDesc] = useState('');
  const [jsonPayload, setJsonPayload] = useState('[\n  {\n    "id": "sample-1",\n    "query": "Is there SQL injection in database queries?",\n    "expected_sources": []\n  }\n]');

  // New Run Modal
  const [isRunOpen, setIsRunOpen] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [runName, setRunName] = useState('');
  const [runProviderMode, setRunProviderMode] = useState('Auto');
  const [runningEval, setRunningEval] = useState(false);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [projs, dSets, rns] = await Promise.all([
        api.getProjects().catch(() => []),
        api.getEvaluationDatasets().catch(() => []),
        api.getEvaluationRuns().catch(() => []),
      ]);
      setProjects(projs);
      setDatasets(dSets);
      setRuns(rns);
      if (dSets.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(dSets[0].id);
      }
      // If projects exist, default to first active project or global
      await loadMetrics(selectedProjectId);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async (projId: string) => {
    setMetricsLoading(true);
    try {
      const metrics = await api.getSystemMetrics(projId || undefined);
      setSystemMetrics(metrics);
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setSystemMetrics(null);
    } finally {
      setMetricsLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleProjectSelect = (projId: string) => {
    setSelectedProjectId(projId);
    loadMetrics(projId);
  };

  const handleCreateDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const parsed = JSON.parse(jsonPayload);
      if (!Array.isArray(parsed)) throw new Error('Payload must be an array of query samples');
      await api.createEvaluationDataset({
        name: datasetName,
        description: datasetDesc,
        dataset_payload: parsed,
      });
      setIsDatasetOpen(false);
      setDatasetName('');
      loadInitialData();
    } catch (err: any) {
      alert(err.message || 'Invalid JSON dataset payload');
    }
  };

  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDatasetId) return;
    setRunningEval(true);
    try {
      await api.createEvaluationRun({
        dataset_id: selectedDatasetId,
        name: runName || `Benchmark Run ${runs.length + 1}`,
        provider_mode: runProviderMode,
      });
      setIsRunOpen(false);
      loadInitialData();
    } catch (err: any) {
      alert(err.message || 'Evaluation run failed');
    } finally {
      setRunningEval(false);
    }
  };

  const formatRatio = (val: MetricRatio | number | null | undefined): string => {
    if (val === null || val === undefined) return 'Not Measured';
    if (typeof val === 'object' && val.formatted) {
      return val.formatted;
    }
    if (typeof val === 'number') {
      return `${Math.round(val * 10) / 10}%`;
    }
    return 'Not Measured';
  };

  const selectedProjectObj = projects.find((p) => p.id === selectedProjectId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Evaluation & System Audits</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Empirical quality gate metrics, sample-level numerators and denominators, and benchmark runs.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button variant="secondary" onClick={() => setIsDatasetOpen(true)}>
            + Create Dataset
          </Button>
          <Button variant="primary" onClick={() => setIsRunOpen(true)} disabled={datasets.length === 0}>
            Run Benchmark
          </Button>
        </div>
      </div>

      {/* PROJECT SELECTOR BAR */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '16px 20px',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Evaluation Scope:
          </span>
          <select
            value={selectedProjectId}
            onChange={(e) => handleProjectSelect(e.target.value)}
            style={{
              padding: '6px 14px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              minWidth: '260px',
            }}
          >
            <option value="">All Projects (Global System Audit)</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.source_count} sources)
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Badge variant="outline">
            Scope: {selectedProjectObj ? selectedProjectObj.name : 'All Projects'}
          </Badge>
          {selectedProjectObj && (
            <Link href={`/projects/${selectedProjectObj.id}`} style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Open Project →
            </Link>
          )}
        </div>
      </div>

      {/* REAL AUDIT METRICS CARD */}
      <Card
        title={
          selectedProjectObj
            ? `Production Audit Metrics: ${selectedProjectObj.name}`
            : 'Global System-Wide Audit Metrics'
        }
        headerAction={
          systemMetrics?.has_enough_data ? (
            <Badge variant="status" value="ready">
              {systemMetrics.total_reviews} Reviews Analyzed
            </Badge>
          ) : (
            <Badge variant="outline">Insufficient Data</Badge>
          )
        }
        subtitle="Sample counts, numerators, and denominators calculated strictly from persisted reviews and quality gates."
      >
        {metricsLoading ? (
          <p className="mono" style={{ fontSize: '13px', color: 'var(--text-secondary)', padding: '16px 0' }}>
            Computing project metrics...
          </p>
        ) : !systemMetrics || !systemMetrics.has_enough_data ? (
          <div style={{ padding: '32px 24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <p className="mono" style={{ fontSize: '14px', fontWeight: 600 }}>
              not enough evaluation data for {selectedProjectObj ? selectedProjectObj.name : 'the selected scope'}
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', maxWidth: '500px', margin: '8px auto 0 auto' }}>
              Execute at least one project review to generate live metrics for citation coverage, correctness, and agent resilience.
            </p>
            {selectedProjectObj && (
              <div style={{ marginTop: '16px' }}>
                <Link href={`/reviews?project_id=${selectedProjectObj.id}`}>
                  <Button variant="primary">Start Review for {selectedProjectObj.name}</Button>
                </Link>
              </div>
            )}
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '14px',
              padding: '12px 0',
            }}
          >
            {/* Metric 1: Citation Coverage with Numerator & Denominator */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>CITATION COVERAGE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {formatRatio(systemMetrics.citation_coverage)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Verified findings / total candidates</div>
            </div>

            {/* Metric 2: Citation Correctness with Numerator & Denominator */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>CITATION CORRECTNESS</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {formatRatio(systemMetrics.citation_correctness)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Grounding accuracy vs snapshot code</div>
            </div>

            {/* Metric 3: Filtered Unsupported Claims */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>UNSUPPORTED CLAIMS</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: systemMetrics.unsupported_claim_count ? '#f87171' : 'var(--text-primary)' }}>
                {systemMetrics.unsupported_claim_count || 0} Filtered
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Rejected by Evidence Verifier Gate</div>
            </div>

            {/* Metric 4: Agent Completion Rate */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>AGENT COMPLETION RATE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {formatRatio(systemMetrics.agent_completion_rate)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Completed A2A specialist tasks</div>
            </div>

            {/* Metric 5: Partial Failure Recovery */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>FAILURE RECOVERY</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {formatRatio(systemMetrics.agent_partial_failure_recovery_rate)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Resilient synthesis with partial tasks</div>
            </div>

            {/* Metric 6: Provider Fallback */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>PROVIDER FALLBACK RATE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {formatRatio(systemMetrics.provider_fallback_rate)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Groq to Ollama fallback transitions</div>
            </div>

            {/* Metric 7: Ingestion Success Rate */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>INGESTION SUCCESS RATE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {formatRatio(systemMetrics.import_success_rate)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Unified pipeline runs completed</div>
            </div>

            {/* Metric 8: Average Review Duration */}
            <div className="mono" style={{ padding: '14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>AVG REVIEW DURATION</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {systemMetrics.avg_review_duration_seconds !== null ? `${systemMetrics.avg_review_duration_seconds}s` : 'N/A'}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>End-to-end multi-agent execution</div>
            </div>
          </div>
        )}
      </Card>

      {/* Datasets Summary */}
      <Card title="Configured Evaluation Datasets">
        {loading ? (
          <p className="mono">Loading datasets...</p>
        ) : datasets.length === 0 ? (
          <EmptyState
            title="No Evaluation Datasets Created"
            description="Create or upload an evaluation set with sample queries and expected ground truth sources to benchmark RAG performance."
            actionText="Create Dataset"
            onAction={() => setIsDatasetOpen(true)}
          />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
            {datasets.map((d) => (
              <div
                key={d.id}
                style={{
                  padding: '14px',
                  backgroundColor: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong style={{ fontSize: '14px' }}>{d.name}</strong>
                  <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {d.sample_count} samples
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                  {d.description || 'Custom RAG benchmark dataset.'}
                </p>
                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      setSelectedDatasetId(d.id);
                      setIsRunOpen(true);
                    }}
                  >
                    Benchmark
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Benchmark Runs History */}
      <Card title="Evaluation Benchmark Runs">
        {runs.length === 0 ? (
          <EmptyState
            title="No Evaluation Runs Executed"
            description="Select an evaluation dataset and execute a benchmark to measure RAG retrieval accuracy and latency."
            actionText={datasets.length > 0 ? 'Run Benchmark' : undefined}
            onAction={datasets.length > 0 ? () => setIsRunOpen(true) : undefined}
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {runs.map((r) => (
              <div
                key={r.id}
                style={{
                  padding: '16px',
                  backgroundColor: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge variant="status" value={r.status}>
                      {r.status}
                    </Badge>
                    <strong style={{ fontSize: '14px' }}>{r.name}</strong>
                    <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                      Mode: {r.provider_mode}
                    </span>
                  </div>
                  <div className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                    Dataset Version: {r.dataset_version || '1.2.0'} | Elapsed: {r.elapsed_seconds}s | Samples: {r.sample_results?.length || 0}
                  </div>
                </div>

                <div className="mono" style={{ display: 'flex', gap: '16px', fontSize: '12px', alignItems: 'center' }}>
                  {r.metrics && (
                    <>
                      <div>
                        Acc:{' '}
                        <strong style={{ color: '#10b981' }}>
                          {typeof r.metrics.accuracy === 'number' ? `${Math.round(r.metrics.accuracy * 100)}%` : 'N/A'}
                        </strong>
                      </div>
                      <div>
                        Recall:{' '}
                        <strong style={{ color: 'var(--text-primary)' }}>
                          {typeof r.metrics.recall === 'number' ? `${Math.round(r.metrics.recall * 100)}%` : 'N/A'}
                        </strong>
                      </div>
                    </>
                  )}
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                    {new Date(r.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Create Dataset Modal */}
      <Modal isOpen={isDatasetOpen} onClose={() => setIsDatasetOpen(false)} title="Create Evaluation Dataset">
        <form onSubmit={handleCreateDataset} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <Input
            label="Dataset Name"
            placeholder="e.g. Authentication Security Benchmark"
            value={datasetName}
            onChange={(e) => setDatasetName(e.target.value)}
            required
          />
          <Input
            label="Description"
            placeholder="e.g. Tests RAG retrieval and specialist citation accuracy"
            value={datasetDesc}
            onChange={(e) => setDatasetDesc(e.target.value)}
          />
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Samples JSON Array
            </label>
            <textarea
              className="mono"
              rows={8}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 10px',
                color: 'var(--text-primary)',
                fontSize: '12px',
                lineHeight: 1.4,
              }}
              value={jsonPayload}
              onChange={(e) => setJsonPayload(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '10px' }}>
            <Button variant="secondary" onClick={() => setIsDatasetOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Save Dataset
            </Button>
          </div>
        </form>
      </Modal>

      {/* Run Benchmark Modal */}
      <Modal isOpen={isRunOpen} onClose={() => setIsRunOpen(false)} title="Run Evaluation Benchmark">
        <form onSubmit={handleCreateRun} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Select Dataset
            </label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: '13px',
              }}
              required
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.sample_count} samples)
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Run Name (Optional)"
            placeholder="e.g. Baseline RAG Accuracy"
            value={runName}
            onChange={(e) => setRunName(e.target.value)}
          />
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              AI Provider Mode
            </label>
            <select
              value={runProviderMode}
              onChange={(e) => setRunProviderMode(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: '13px',
              }}
            >
              <option value="Auto">Auto (Groq primary with Ollama fallback)</option>
              <option value="Groq">Groq Only</option>
              <option value="Ollama">Ollama Only</option>
            </select>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '10px' }}>
            <Button variant="secondary" onClick={() => setIsRunOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" loading={runningEval}>
              Start Benchmark
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
