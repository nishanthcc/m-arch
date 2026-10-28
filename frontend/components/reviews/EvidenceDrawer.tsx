import React from 'react';
import { EvidenceItem } from '@/lib/types';

interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  evidence: EvidenceItem[];
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  isOpen,
  onClose,
  title,
  evidence,
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1100,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        backdropFilter: 'blur(2px)',
        display: 'flex',
        justifyContent: 'flex-end',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '650px',
          height: '100%',
          backgroundColor: 'var(--bg-surface)',
          borderLeft: '1px solid var(--border-strong)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-10px 0 25px rgba(0, 0, 0, 0.4)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <span
              className="mono"
              style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}
            >
              Grounded Retrieval Evidence
            </span>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginTop: '2px' }}>{title}</h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '18px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Evidence List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {evidence.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              No direct excerpts attached to this observation.
            </p>
          ) : (
            evidence.map((item, idx) => (
              <div
                key={idx}
                style={{
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-elevated)',
                  overflow: 'hidden',
                }}
              >
                <div
                  className="mono"
                  style={{
                    padding: '8px 14px',
                    backgroundColor: 'rgba(0, 0, 0, 0.2)',
                    borderBottom: '1px solid var(--border-subtle)',
                    fontSize: '11px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {item.display_path}
                    {item.line_start ? ` (L${item.line_start}-${item.line_end})` : ''}
                  </span>
                  <span style={{ color: 'var(--text-muted)' }}>
                    Method: {item.retrieval_method} {item.score ? `| Score: ${item.score}` : ''}
                  </span>
                </div>
                <div style={{ padding: '14px', overflowX: 'auto' }}>
                  <pre
                    className="mono"
                    style={{
                      fontSize: '12px',
                      lineHeight: 1.5,
                      color: 'var(--text-primary)',
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                    }}
                  >
                    {item.excerpt}
                  </pre>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
