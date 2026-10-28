'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { AppSettings, ProvidersHealth, AIMode } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useTheme } from '@/lib/theme/ThemeProvider';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [health, setHealth] = useState<ProvidersHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [saving, setSaving] = useState(false);

  // Editable settings
  const [aiMode, setAiMode] = useState<AIMode>('Auto');
  const [primaryProvider, setPrimaryProvider] = useState<'Groq' | 'Ollama'>('Groq');
  const [fallbackProvider, setFallbackProvider] = useState<'Groq' | 'Ollama'>('Ollama');
  const [groqModel, setGroqModel] = useState('llama-3.3-70b-versatile');
  const [ollamaModel, setOllamaModel] = useState('qwen2.5-coder:7b');
  const [rerankEnabled, setRerankEnabled] = useState(true);

  const loadData = () => {
    setLoading(true);
    Promise.all([api.getSettings(), api.getProvidersHealth()])
      .then(([s, h]) => {
        setSettings(s);
        setHealth(h);
        setAiMode(s.ai_mode);
        setPrimaryProvider(s.primary_provider);
        setFallbackProvider(s.fallback_provider);
        setGroqModel(s.groq_model);
        setOllamaModel(s.ollama_model);
        setRerankEnabled(s.rerank_enabled);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateSettings({
        ai_mode: aiMode,
        primary_provider: primaryProvider,
        fallback_provider: fallbackProvider,
        groq_model: groqModel,
        ollama_model: ollamaModel,
        rerank_enabled: rerankEnabled,
      });
      alert('Settings updated successfully.');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestHealth = async () => {
    setChecking(true);
    try {
      const h = await api.getProvidersHealth();
      setHealth(h);
    } catch (err: any) {
      alert(err.message || 'Health check failed');
    } finally {
      setChecking(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      <div>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>System Settings</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Configure inference modes, local model fallbacks, theme preferences, and data privacy limits.
        </p>
      </div>

      {/* Live Provider Health & Connectivity */}
      <Card
        title="AI Provider Health & Connectivity"
        headerAction={
          <Button size="sm" variant="secondary" onClick={handleTestHealth} loading={checking}>
            ↻ Check Connectivity
          </Button>
        }
        subtitle="Live connection diagnostics for Cloud (Groq) and Local (Ollama) inference engines without revealing credentials."
      >
        {loading ? (
          <p className="mono">Checking provider status...</p>
        ) : health ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '12px' }}>
            {/* Groq Cloud */}
            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-elevated)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '15px' }}>Groq Cloud Inference</strong>
                <Badge variant="status" value={health.providers.Groq.available ? 'ready' : 'waiting'}>
                  {health.providers.Groq.available ? 'Connected' : 'Offline / Unconfigured'}
                </Badge>
              </div>
              <div className="mono" style={{ fontSize: '12px', marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div>Configured: <strong>{health.providers.Groq.configured ? 'YES (Key Present)' : 'NO (Key Missing)'}</strong></div>
                <div>Active Model: <strong>{health.providers.Groq.active_model}</strong></div>
                {health.providers.Groq.latency_ms && (
                  <div>Latency: <strong>{health.providers.Groq.latency_ms}ms</strong></div>
                )}
                {health.providers.Groq.error && (
                  <div style={{ color: 'var(--severity-critical)', marginTop: '4px' }}>
                    Notice: {health.providers.Groq.error}
                  </div>
                )}
              </div>
            </div>

            {/* Ollama Local */}
            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-elevated)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '15px' }}>Ollama Local Service</strong>
                <Badge variant="status" value={health.providers.Ollama.available ? 'ready' : 'waiting'}>
                  {health.providers.Ollama.available ? 'Connected' : 'Offline'}
                </Badge>
              </div>
              <div className="mono" style={{ fontSize: '12px', marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div>Base URL: <strong>{settings?.ollama_base_url || 'http://localhost:11434'}</strong></div>
                <div>Target Model: <strong>{health.providers.Ollama.active_model}</strong></div>
                {health.providers.Ollama.latency_ms && (
                  <div>Latency: <strong>{health.providers.Ollama.latency_ms}ms</strong></div>
                )}
                {health.providers.Ollama.error && (
                  <div style={{ color: 'var(--status-partial)', marginTop: '4px' }}>
                    Notice: {health.providers.Ollama.error}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : null}
      </Card>

      {/* Theme Settings */}
      <Card title="Visual Theme">
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginTop: '8px' }}>
          <Button
            variant={theme === 'dark' ? 'primary' : 'secondary'}
            onClick={() => setTheme('dark')}
          >
            ☾ Dark Mode (#161616)
          </Button>
          <Button
            variant={theme === 'light' ? 'primary' : 'secondary'}
            onClick={() => setTheme('light')}
          >
            ☀ Light Mode (#FFFFFF / #F4F4F5)
          </Button>
        </div>
      </Card>

      {/* Model & Routing Configuration */}
      <Card title="Inference Routing & Model Defaults">
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '12px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Global AI Mode
              </label>
              <select
                value={aiMode}
                onChange={(e) => setAiMode(e.target.value as AIMode)}
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
                <option value="Auto">Auto (Primary with automatic fallback)</option>
                <option value="Groq">Groq (Cloud Accelerated Only)</option>
                <option value="Ollama">Ollama (Local Private Only)</option>
                <option value="Hybrid">Hybrid (Role-Based Task Routing)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Primary Provider (Auto Mode)
              </label>
              <select
                value={primaryProvider}
                onChange={(e) => setPrimaryProvider(e.target.value as any)}
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
                <option value="Groq">Groq</option>
                <option value="Ollama">Ollama</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Fallback Provider (Auto Mode)
              </label>
              <select
                value={fallbackProvider}
                onChange={(e) => setFallbackProvider(e.target.value as any)}
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
                <option value="Ollama">Ollama</option>
                <option value="Groq">Groq</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Input
              label="Groq Model ID"
              value={groqModel}
              onChange={(e) => setGroqModel(e.target.value)}
              placeholder="e.g. llama-3.3-70b-versatile, mixtral-8x7b-32768"
              description="Configurable Groq inference model identifier"
            />
            <Input
              label="Ollama Model ID"
              value={ollamaModel}
              onChange={(e) => setOllamaModel(e.target.value)}
              placeholder="e.g. qwen2.5-coder:7b"
              description="Installed local Ollama model identifier"
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="checkbox"
              id="rerank"
              checked={rerankEnabled}
              onChange={(e) => setRerankEnabled(e.target.checked)}
            />
            <label htmlFor="rerank" style={{ fontSize: '13px', color: 'var(--text-primary)', cursor: 'pointer' }}>
              Enable Reciprocal Rank Fusion (RRF) dense + keyword hybrid ranking
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <Button type="submit" variant="primary" loading={saving}>
              Save Settings
            </Button>
          </div>
        </form>
      </Card>

      {/* Secret Configuration Guidance */}
      <Card title="Local Secret & Model Setup Guide">
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          <p>
            <strong>Configuring Groq:</strong> Open your local <code className="mono">backend/.env</code> file and add:
          </p>
          <pre
            className="mono"
            style={{
              padding: '10px 14px',
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: 'var(--radius-md)',
              margin: '8px 0 16px 0',
              color: 'var(--text-primary)',
            }}
          >
            GROQ_API_KEY=gsk_...
          </pre>
          <p>
            The key is kept strictly local on your machine and is never exposed through the API or frontend.
          </p>
          <p style={{ marginTop: '12px' }}>
            <strong>Configuring Ollama Model:</strong> On your RTX 3050 (6GB VRAM) laptop, install the recommended model:
          </p>
          <pre
            className="mono"
            style={{
              padding: '10px 14px',
              backgroundColor: 'var(--bg-elevated)',
              borderRadius: 'var(--radius-md)',
              margin: '8px 0 0 0',
              color: 'var(--text-primary)',
            }}
          >
            ollama pull qwen2.5-coder:7b
          </pre>
        </div>
      </Card>
    </div>
  );
}
