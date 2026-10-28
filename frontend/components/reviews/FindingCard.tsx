import React from 'react';
import { Finding, EvidenceItem } from '@/lib/types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface FindingCardProps {
  finding: Finding;
  onViewEvidence: (evidence: EvidenceItem[], title: string) => void;
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding, onViewEvidence }) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Badge variant="severity" value={finding.severity}>
              {finding.severity}
            </Badge>
            <Badge variant="verification" value={finding.verification_status}>
              {finding.verification_status}
            </Badge>
            <span
              className="mono"
              style={{ fontSize: '11px', color: 'var(--text-secondary)' }}
            >
              Agent: {finding.agent_id}
            </span>
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {finding.title}
          </h4>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <span
            className="mono"
            style={{ fontSize: '11px', color: 'var(--text-secondary)' }}
            title={finding.confidence_interpretation}
          >
            Conf: {Math.round(finding.confidence * 100)}%
          </span>
          {finding.evidence_items && finding.evidence_items.length > 0 && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => onViewEvidence(finding.evidence_items, finding.title)}
            >
              Evidence ({finding.evidence_items.length})
            </Button>
          )}
        </div>
      </div>

      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
        {finding.explanation}
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px',
          padding: '12px',
          backgroundColor: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-md)',
          fontSize: '12px',
        }}
      >
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>Impact: </strong>
          <span style={{ color: 'var(--text-secondary)' }}>{finding.impact}</span>
        </div>
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>Remediation: </strong>
          <span style={{ color: 'var(--text-secondary)' }}>{finding.remediation}</span>
        </div>
      </div>

      {finding.limitations && (
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          LIMITATIONS: {finding.limitations}
        </div>
      )}
    </div>
  );
};
