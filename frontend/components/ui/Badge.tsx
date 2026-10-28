import React from 'react';
import { Severity, TaskStatus, VerificationStatus } from '@/lib/types';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'severity' | 'status' | 'verification' | 'neutral' | 'outline';
  value?: Severity | TaskStatus | VerificationStatus | string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  value,
  className = '',
}) => {
  let style: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 8px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '11px',
    fontWeight: 600,
    fontFamily: 'var(--font-mono)',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    border: '1px solid var(--border-subtle)',
    backgroundColor: 'var(--bg-surface)',
    color: 'var(--text-secondary)',
  };

  const val = (value || children)?.toString().toLowerCase();

  if (variant === 'severity') {
    if (val === 'critical') {
      style = { ...style, backgroundColor: 'rgba(220, 38, 38, 0.15)', color: 'var(--severity-critical)', borderColor: 'rgba(220, 38, 38, 0.3)' };
    } else if (val === 'high') {
      style = { ...style, backgroundColor: 'rgba(234, 88, 12, 0.15)', color: 'var(--severity-high)', borderColor: 'rgba(234, 88, 12, 0.3)' };
    } else if (val === 'medium') {
      style = { ...style, backgroundColor: 'rgba(217, 119, 6, 0.15)', color: 'var(--severity-medium)', borderColor: 'rgba(217, 119, 6, 0.3)' };
    } else if (val === 'low') {
      style = { ...style, backgroundColor: 'rgba(37, 99, 235, 0.15)', color: 'var(--severity-low)', borderColor: 'rgba(37, 99, 235, 0.3)' };
    } else {
      style = { ...style, backgroundColor: 'rgba(100, 116, 139, 0.15)', color: 'var(--severity-info)', borderColor: 'rgba(100, 116, 139, 0.3)' };
    }
  } else if (variant === 'status') {
    if (val === 'completed' || val === 'ready') {
      style = { ...style, backgroundColor: 'rgba(22, 163, 74, 0.15)', color: 'var(--status-completed)', borderColor: 'rgba(22, 163, 74, 0.3)' };
    } else if (val === 'running' || val === 'indexing') {
      style = { ...style, backgroundColor: 'rgba(2, 132, 199, 0.15)', color: 'var(--status-running)', borderColor: 'rgba(2, 132, 199, 0.3)' };
    } else if (val === 'failed' || val === 'error') {
      style = { ...style, backgroundColor: 'rgba(220, 38, 38, 0.15)', color: 'var(--status-failed)', borderColor: 'rgba(220, 38, 38, 0.3)' };
    } else if (val === 'partial') {
      style = { ...style, backgroundColor: 'rgba(202, 138, 4, 0.15)', color: 'var(--status-partial)', borderColor: 'rgba(202, 138, 4, 0.3)' };
    } else {
      style = { ...style, backgroundColor: 'rgba(113, 113, 122, 0.15)', color: 'var(--status-waiting)', borderColor: 'rgba(113, 113, 122, 0.3)' };
    }
  } else if (variant === 'verification') {
    if (val === 'verified') {
      style = { ...style, backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.3)' };
    } else if (val === 'partially_supported') {
      style = { ...style, backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', borderColor: 'rgba(245, 158, 11, 0.3)' };
    } else if (val === 'unsupported') {
      style = { ...style, backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.3)' };
    } else if (val === 'duplicate') {
      style = { ...style, backgroundColor: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', borderColor: 'rgba(168, 85, 247, 0.3)' };
    } else if (val === 'not_verifiable') {
      style = { ...style, backgroundColor: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', borderColor: 'rgba(148, 163, 184, 0.3)' };
    } else {
      style = {
        ...style,
        backgroundColor: 'transparent',
        borderColor: 'var(--border-strong)',
        color: 'var(--text-primary)',
        fontSize: '10px',
      };
    }
  } else if (variant === 'outline') {
    style = {
      ...style,
      backgroundColor: 'transparent',
      borderColor: 'var(--border-strong)',
      color: 'var(--text-primary)',
      fontSize: '10px',
    };
  }

  return (
    <span style={style} className={className}>
      {children}
    </span>
  );
};
