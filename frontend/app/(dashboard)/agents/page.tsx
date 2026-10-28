'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { AgentCard as AgentCardType } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentCardType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAgents()
      .then(setAgents)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const getStatusBadge = (status: AgentCardType['status']) => {
    switch (status) {
      case 'available':
        return <Badge variant="status" value="ready">Available</Badge>;
      case 'busy':
        return <Badge variant="status" value="running">Busy</Badge>;
      case 'unavailable':
        return <Badge variant="status" value="failed">Unavailable</Badge>;
      case 'misconfigured':
        return <Badge variant="status" value="partial">Misconfigured</Badge>;
      case 'paused':
        return <Badge variant="outline">Paused</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      <div>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>A2A Specialist Agents</h1>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Real runtime state, versioned Prompt Registry tracking, A2A connectivity, and role-based MCP tools.
        </p>
      </div>

      {loading ? (
        <p className="mono" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Probing agent health and querying A2A registry...
        </p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
          {agents.map((ag) => (
            <Card
              key={ag.agent_id}
              title={ag.name}
              subtitle={ag.role}
              headerAction={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Badge variant="outline">
                    <span className="mono">Prompt v{ag.prompt_version || '1.1.0'}</span>
                  </Badge>
                  {getStatusBadge(ag.status)}
                </div>
              }
            >
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '10px 0 14px 0' }}>
                {ag.description}
              </p>

              {/* Provenance & Runtime State Grid */}
              <div
                className="mono"
                style={{
                  padding: '12px 14px',
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>A2A Endpoint:</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{ag.endpoint}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Connectivity:</span>
                  <span style={{ color: '#10b981' }}>● {ag.a2a_connectivity || 'connected'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Default Profile:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{ag.configured_provider}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Model Used:</span>
                  <strong style={{ color: 'var(--text-primary)' }}>{ag.actual_model_used || ag.configured_model}</strong>
                </div>
                {ag.last_task_time && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Last Active:</span>
                    <span style={{ color: 'var(--text-muted)' }}>{new Date(ag.last_task_time).toLocaleTimeString()}</span>
                  </div>
                )}
                {ag.fallback_history && ag.fallback_history.length > 0 && (
                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '6px', color: 'var(--text-muted)' }}>
                    Fallback History: {ag.fallback_history.join('; ')}
                  </div>
                )}
                {ag.last_error && (
                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '6px', color: '#f87171' }}>
                    Last Error: {ag.last_error}
                  </div>
                )}
              </div>

              {/* Skills */}
              <div style={{ marginBottom: '14px' }}>
                <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                  ASSIGNED SKILLS ({ag.skills.length})
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {ag.skills.map((s, i) => (
                    <span
                      key={i}
                      style={{
                        padding: '3px 8px',
                        backgroundColor: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '11px',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              {/* MCP Tools - Muted Neutral Outline Chips */}
              <div>
                <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
                  PERMITTED MCP TOOLS ({ag.allowed_mcp_tools.length})
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {ag.allowed_mcp_tools.map((t, i) => (
                    <span
                      key={i}
                      className="mono"
                      style={{
                        padding: '2px 8px',
                        backgroundColor: 'transparent',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '11px',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
