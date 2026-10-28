'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { EvaluationDataset, EvaluationRun, SystemMetrics } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';

export default function EvaluationsPage() {
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([]);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);

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

  const loadData = () => {
    setLoading(true);
    Promise.all([
      api.getEvaluationDatasets(),
      api.getEvaluationRuns(),
      api.getSystemMetrics().catch(() => null)
    ])
      .then(([dSets, rns, metrics]) => {
        setDatasets(dSets);
        setRuns(rns);
        setSystemMetrics(metrics);
        if (dSets.length > 0 && !selectedDatasetId) {
          setSelectedDatasetId(dSets[0].id);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

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
      loadData();
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
      loadData();
    } catch (err: any) {
      alert(err.message || 'Evaluation run failed');
    } finally {
      setRunningEval(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Evaluation & System Audits</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Empirical quality gate metrics, citation coverage, agent completion rates, and benchmark runs.
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

      {/* Real Review Data Evaluation Section */}
      <Card
        title="Production Multi-Agent Audit Metrics"
        headerAction={
          systemMetrics?.has_enough_data ? (
            <Badge variant="status" value="ready">{systemMetrics.total_reviews} Reviews Analyzed</Badge>
          ) : (
            <Badge variant="outline">No Reviews Yet</Badge>
          )
        }
        subtitle="Calculated strictly from persisted reviews, verification gates, and provider traces."
      >
        {!systemMetrics || !systemMetrics.has_enough_data ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <p className="mono" style={{ fontSize: '13px' }}>
              not enough evaluation data
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
              Execute at least one project review to generate live metrics for citation coverage, correctness, and agent resilience.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '14px',
              padding: '12px 0',
            }}
          >
            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>CITATION COVERAGE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{systemMetrics.citation_coverage}%</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Grounded in code snippets</div>
            </div>

            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>CITATION CORRECTNESS</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{systemMetrics.citation_correctness}%</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Verified against excerpts</div>
            </div>

            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>UNSUPPORTED CLAIMS</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: systemMetrics.unsupported_claim_count ? '#f87171' : 'var(--text-primary)' }}>
                {systemMetrics.unsupported_claim_count}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Filtered by Evidence Verifier</div>
            </div>

            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>AGENT COMPLETION RATE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{systemMetrics.agent_completion_rate}%</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>A2A task success</div>
            </div>

            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>PARTIAL-FAILURE RECOVERY</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{systemMetrics.agent_partial_failure_recovery_rate}%</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Resilient synthesis</div>
            </div>

            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>PROVIDER FALLBACK RATE</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{systemMetrics.provider_fallback_rate}%</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Groq to Ollama routing</div>
            </div>

            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>GITHUB IMPORT SUCCESS</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{systemMetrics.import_success_rate}%</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Tarball extraction rate</div>
            </div>

            <div className="mono" style={{ padding: '12px 14px', backgroundColor: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>AVG REVIEW DURATION</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{systemMetrics.avg_review_duration_seconds}s</div>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>End-to-end multi-agent</div>
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
                    {d.sample_count} queries
                  </span>
                </div>
                {d.description && (
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {d.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Benchmark Runs Table */}
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>Benchmark Execution Runs</h3>
        {loading ? (
          <p className="mono">Loading evaluation runs...</p>
        ) : runs.length === 0 ? (
          <EmptyState
            title="No Benchmark Runs Recorded"
            description="Execute a benchmark run against a configured dataset to compute factual retrieval precision, citation coverage, and latency."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {runs.map((r) => (
              <Card
                key={r.id}
                title={r.name}
                headerAction={<Badge variant="status" value={r.status}>{r.status}</Badge>}
                subtitle={`Provider: ${r.provider_mode} | Elapsed: ${r.elapsed_seconds}s | Metric Ver: ${r.metrics?.metric_version || '1.1'}`}
              >
                {/* Metric Summary Grid */}
                <div
                  className="mono"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: '12px',
                    padding: '14px',
                    backgroundColor: 'var(--bg-elevated)',
                    borderRadius: 'var(--radius-md)',
                    margin: '12px 0',
                    fontSize: '12px',
                  }}
                >
                  <div>
                    Retrieval Precision:{' '}
                    <strong style={{ color: 'var(--text-primary)' }}>
                      {r.metrics?.retrieval_precision ? `${Math.round(r.metrics.retrieval_precision * 100)}%` : 'N/A'}
                    </strong>
                  </div>
                  <div>
                    Citation Coverage:{' '}
                    <strong style={{ color: 'var(--text-primary)' }}>
                      {r.metrics?.citation_coverage ? `${Math.round(r.metrics.citation_coverage * 100)}%` : 'N/A'}
                    </strong>
                  </div>
                  <div>
                    Avg Latency:{' '}
                    <strong style={{ color: 'var(--text-primary)' }}>
                      {r.metrics?.mean_latency_ms ? `${Math.round(r.metrics.mean_latency_ms)}ms` : `${Math.round(r.elapsed_seconds * 1000)}ms`}
                    </strong>
                  </div>
                  <div>
                    Samples Evaluated:{' '}
                    <strong style={{ color: 'var(--text-primary)' }}>
                      {r.sample_results?.length || 0}
                    </strong>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Dataset Modal */}
      <Modal isOpen={isDatasetOpen} onClose={() => setIsDatasetOpen(false)} title="Create Benchmark Dataset">
        <form onSubmit={handleCreateDataset} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input
            label="Dataset Name"
            value={datasetName}
            onChange={(e) => setDatasetName(e.target.value)}
            placeholder="e.g. Security Vulnerability Golden Set"
            required
          />
          <Input
            label="Description (Optional)"
            value={datasetDesc}
            onChange={(e) => setDatasetDesc(e.target.value)}
            placeholder="Benchmarking ground-truth retrieval for API injection flaws"
          />
          <div>
            <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '6px' }}>
              JSON Query Samples
            </label>
            <textarea
              value={jsonPayload}
              onChange={(e) => setJsonPayload(e.target.value)}
              rows={8}
              className="mono"
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                padding: '10px 12px',
                fontSize: '12px',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
              required
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <Button type="button" variant="ghost" onClick={() => setIsDatasetOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Create Dataset
            </Button>
          </div>
        </form>
      </Modal>

      {/* Run Benchmark Modal */}
      <Modal isOpen={isRunOpen} onClose={() => setIsRunOpen(false)} title="Execute Benchmark Run">
        <form onSubmit={handleCreateRun} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input
            label="Run Name"
            value={runName}
            onChange={(e) => setRunName(e.target.value)}
            placeholder="e.g. Groq vs Ollama Comparison Run"
          />
          <div>
            <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '6px' }}>
              Select Evaluation Dataset
            </label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 12px',
                fontSize: '14px',
                color: 'var(--text-primary)',
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
          <div>
            <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '6px' }}>
              Provider Mode
            </label>
            <select
              value={runProviderMode}
              onChange={(e) => setRunProviderMode(e.target.value)}
              style={{
                width: '100%',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 12px',
                fontSize: '14px',
                color: 'var(--text-primary)',
              }}
            >
              <option value="Auto">Auto (Primary with Fallback)</option>
              <option value="Groq">Groq Cloud (llama-3.3-70b)</option>
              <option value="Ollama">Ollama Local (qwen2.5-coder:7b)</option>
            </select>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <Button type="button" variant="ghost" onClick={() => setIsRunOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={runningEval}>
              Start Benchmark
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
