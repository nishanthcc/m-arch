'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/overview', label: 'Overview', icon: '⌘' },
  { href: '/projects', label: 'Projects', icon: '◫' },
  { href: '/reviews', label: 'Reviews', icon: '◎' },
  { href: '/agents', label: 'Agents (A2A)', icon: '◈' },
  { href: '/knowledge', label: 'Knowledge (MCP)', icon: '▤' },
  { href: '/evaluations', label: 'Evaluations', icon: '⚑' },
  { href: '/settings', label: 'Settings', icon: '⚙' },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('m-arch-sidebar-collapsed');
    if (saved !== null) {
      setCollapsed(saved === 'true');
    }
    setMounted(true);
  }, []);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem('m-arch-sidebar-collapsed', String(next));
  };

  if (!mounted) return <aside style={{ width: '250px' }} />;

  return (
    <aside
      style={{
        width: collapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
        backgroundColor: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        flexShrink: 0,
        height: '100vh',
        position: 'sticky',
        top: 0,
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          height: 'var(--topbar-height)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          padding: collapsed ? '0' : '0 18px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontWeight: 700,
                fontSize: '15px',
                letterSpacing: '0.08em',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-primary)',
              }}
            >
              M-ARCH
            </span>
            <span
              style={{
                fontSize: '10px',
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                padding: '1px 5px',
                borderRadius: '3px',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              v1.0
            </span>
          </div>
        )}
        <button
          onClick={toggleCollapse}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '14px',
            padding: '6px',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      {/* Navigation Items */}
      <nav style={{ padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/overview' && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: collapsed ? '10px 0' : '8px 12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                borderRadius: 'var(--radius-md)',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                backgroundColor: isActive ? 'var(--bg-elevated)' : 'transparent',
                border: isActive ? '1px solid var(--border-subtle)' : '1px solid transparent',
                transition: 'all 0.15s ease',
              }}
              title={collapsed ? item.label : undefined}
            >
              <span style={{ fontSize: '15px', fontFamily: 'var(--font-mono)' }}>{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Protocol Badges */}
      {!collapsed && (
        <div
          style={{
            padding: '14px 18px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
          }}
        >
          <div>A2A: Connected</div>
          <div>MCP: Registered (9 tools)</div>
        </div>
      )}
    </aside>
  );
};
