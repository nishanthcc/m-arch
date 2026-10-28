'use client';

import React, { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { useTheme } from '@/lib/theme/ThemeProvider';
import { api } from '@/lib/api/client';
import { ProvidersHealth } from '@/lib/types';

export const TopBar: React.FC = () => {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const [health, setHealth] = useState<ProvidersHealth | null>(null);

  useEffect(() => {
    api.getProvidersHealth()
      .then(setHealth)
      .catch(() => {});
  }, []);

  const getPageTitle = () => {
    if (pathname.includes('/projects/')) return 'Projects / Detail';
    if (pathname.includes('/projects')) return 'Project Catalog';
    if (pathname.includes('/reviews/')) return 'Review Trace & Findings';
    if (pathname.includes('/reviews')) return 'Engineering Reviews';
    if (pathname.includes('/agents')) return 'Specialist Agents (A2A)';
    if (pathname.includes('/knowledge')) return 'Security Knowledge (MCP)';
    if (pathname.includes('/evaluations')) return 'Benchmark Evaluations';
    if (pathname.includes('/settings')) return 'System Settings';
    return 'Dashboard Overview';
  };

  return (
    <header
      style={{
        height: 'var(--topbar-height)',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600 }}>{getPageTitle()}</h2>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Live Provider Health Status Indicator */}
        {health && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: health.providers.Groq.available || health.providers.Ollama.available
                  ? 'var(--status-completed)'
                  : 'var(--severity-critical)',
              }}
            />
            <span style={{ color: 'var(--text-secondary)' }}>MODE:</span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{health.mode}</span>
          </div>
        )}

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 12px',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span>{theme === 'dark' ? '☀ LIGHT' : '☾ DARK'}</span>
        </button>
      </div>
    </header>
  );
};
