'use client';

import React, { useState } from 'react';
import { ArchitectureGraph, GraphNode, GraphEdge } from '@/lib/types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface ArchitectureGraphViewProps {
  graph: ArchitectureGraph;
  onViewSourceExcerpt?: (filePath: string, line?: number) => void;
}

export const ArchitectureGraphView: React.FC<ArchitectureGraphViewProps> = ({
  graph,
  onViewSourceExcerpt
}) => {
  const [viewMode, setViewMode] = useState<'graph' | 'table'>('graph');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [searchFilter, setSearchFilter] = useState('');

  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  // Filtered nodes for table fallback
  const filteredNodes = nodes.filter((n) =>
    n.label.toLowerCase().includes(searchFilter.toLowerCase()) ||
    n.type.toLowerCase().includes(searchFilter.toLowerCase()) ||
    (n.details && n.details.toLowerCase().includes(searchFilter.toLowerCase()))
  );

  // Compute visual coordinates for nodes in a clean radial/layered arrangement
  const width = 800;
  const height = 480;
  const centerX = width / 2;
  const centerY = height / 2;

  const appNode = nodes.find((n) => n.type === 'application') || nodes[0];
  const peripheralNodes = nodes.filter((n) => n.id !== appNode?.id);

  const nodePositions: Record<string, { x: number; y: number }> = {};
  if (appNode) {
    nodePositions[appNode.id] = { x: centerX, y: centerY };
  }

  const radius = Math.min(width, height) * 0.36;
  peripheralNodes.forEach((node, idx) => {
    const angle = (idx / Math.max(1, peripheralNodes.length)) * 2 * Math.PI - Math.PI / 2;
    nodePositions[node.id] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'application': return 'var(--text-primary)';
      case 'framework': return '#38bdf8';
      case 'database': return '#fbbf24';
      case 'service': return '#a78bfa';
      case 'routes': return '#34d399';
      case 'testing': return '#4ade80';
      case 'deployment': return '#fb923c';
      default: return 'var(--text-secondary)';
    }
  };

  const getStatusBadgeVariant = (status: string): 'status' | 'outline' | 'neutral' => {
    if (status === 'detected') return 'status';
    if (status === 'inferred') return 'neutral';
    return 'outline';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Controls Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            size="sm"
            variant={viewMode === 'graph' ? 'primary' : 'secondary'}
            onClick={() => setViewMode('graph')}
          >
            Visual Architecture Graph ({nodes.length} nodes)
          </Button>
          <Button
            size="sm"
            variant={viewMode === 'table' ? 'primary' : 'secondary'}
            onClick={() => setViewMode('table')}
          >
            Evidence Matrix Table
          </Button>
        </div>

        {viewMode === 'table' && (
          <input
            type="text"
            placeholder="Search architecture components..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            style={{
              padding: '6px 12px',
              fontSize: '12px',
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              width: '240px',
            }}
          />
        )}
      </div>

      {nodes.length === 0 ? (
        <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
          No architecture nodes detected. Re-index source snapshot to generate relationship graph.
        </div>
      ) : viewMode === 'graph' ? (
        <div style={{ display: 'grid', gridTemplateColumns: selectedNode || selectedEdge ? '1fr 300px' : '1fr', gap: '16px' }}>
          {/* SVG Canvas */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <svg
              viewBox={`0 0 ${width} ${height}`}
              style={{ width: '100%', height: 'auto', display: 'block' }}
            >
              {/* Edges */}
              {edges.map((edge) => {
                const srcPos = nodePositions[edge.source];
                const tgtPos = nodePositions[edge.target];
                if (!srcPos || !tgtPos) return null;
                const isSelected = selectedEdge?.id === edge.id;

                return (
                  <g
                    key={edge.id}
                    onClick={() => {
                      setSelectedEdge(edge);
                      setSelectedNode(null);
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <line
                      x1={srcPos.x}
                      y1={srcPos.y}
                      x2={tgtPos.x}
                      y2={tgtPos.y}
                      stroke={isSelected ? 'var(--text-primary)' : 'var(--border-subtle)'}
                      strokeWidth={isSelected ? 2.5 : 1.5}
                      strokeDasharray={edge.status === 'inferred' ? '4 4' : undefined}
                    />
                    <text
                      x={(srcPos.x + tgtPos.x) / 2}
                      y={(srcPos.y + tgtPos.y) / 2 - 6}
                      fill="var(--text-muted)"
                      fontSize="10"
                      fontFamily="var(--font-mono)"
                      textAnchor="middle"
                    >
                      {edge.label}
                    </text>
                  </g>
                );
              })}

              {/* Nodes */}
              {nodes.map((node) => {
                const pos = nodePositions[node.id];
                if (!pos) return null;
                const isSelected = selectedNode?.id === node.id;
                const isApp = node.type === 'application';
                const nodeColor = getNodeColor(node.type);

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={() => {
                      setSelectedNode(node);
                      setSelectedEdge(null);
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <rect
                      x={isApp ? -80 : -65}
                      y={isApp ? -24 : -18}
                      width={isApp ? 160 : 130}
                      height={isApp ? 48 : 36}
                      rx="6"
                      fill="var(--bg-elevated)"
                      stroke={isSelected ? 'var(--text-primary)' : nodeColor}
                      strokeWidth={isSelected ? 2 : 1}
                      filter="drop-shadow(0 2px 4px rgba(0,0,0,0.3))"
                    />
                    <text
                      x="0"
                      y="-2"
                      fill="var(--text-primary)"
                      fontSize={isApp ? "12" : "11"}
                      fontWeight={isApp ? "700" : "600"}
                      textAnchor="middle"
                    >
                      {node.label.length > 18 ? node.label.slice(0, 16) + '...' : node.label}
                    </text>
                    <text
                      x="0"
                      y="12"
                      fill="var(--text-secondary)"
                      fontSize="9"
                      fontFamily="var(--font-mono)"
                      textAnchor="middle"
                    >
                      [{node.status.toUpperCase()}]
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Selected Item Evidence Sidebar */}
          {(selectedNode || selectedEdge) && (
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  {selectedNode ? 'COMPONENT EVIDENCE' : 'RELATIONSHIP EVIDENCE'}
                </span>
                <button
                  onClick={() => { setSelectedNode(null); setSelectedEdge(null); }}
                  style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '14px' }}
                >
                  ✕
                </button>
              </div>

              {selectedNode && (
                <>
                  <div>
                    <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {selectedNode.label}
                    </h4>
                    <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                      <Badge variant="outline">{selectedNode.type}</Badge>
                      <Badge variant={getStatusBadgeVariant(selectedNode.status)}>
                        {selectedNode.status}
                      </Badge>
                    </div>
                  </div>

                  {selectedNode.details && (
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                      {selectedNode.details}
                    </p>
                  )}

                  {selectedNode.evidence && (
                    <div
                      className="mono"
                      style={{
                        padding: '10px 12px',
                        backgroundColor: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '11px',
                      }}
                    >
                      <div style={{ color: 'var(--text-secondary)', marginBottom: '4px' }}>
                        Source File: <strong>{selectedNode.evidence.file_path || 'root'}</strong>
                        {selectedNode.evidence.line && ` (Line ${selectedNode.evidence.line})`}
                      </div>
                      {selectedNode.evidence.excerpt && (
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
                          {selectedNode.evidence.excerpt}
                        </pre>
                      )}
                    </div>
                  )}

                  {selectedNode.evidence?.file_path && onViewSourceExcerpt && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => onViewSourceExcerpt(selectedNode.evidence!.file_path!, selectedNode.evidence?.line)}
                    >
                      View Source File
                    </Button>
                  )}
                </>
              )}

              {selectedEdge && (
                <>
                  <div>
                    <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {selectedEdge.label}
                    </h4>
                    <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                      <Badge variant="outline">{selectedEdge.relationship}</Badge>
                      <Badge variant={getStatusBadgeVariant(selectedEdge.status)}>
                        {selectedEdge.status}
                      </Badge>
                    </div>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Connects <strong>{selectedEdge.source}</strong> to <strong>{selectedEdge.target}</strong>.
                  </p>
                </>
              )}
            </div>
          )}
        </div>
      ) : (
        /* Table Fallback View */
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', backgroundColor: 'var(--bg-elevated)' }}>
                <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>Component</th>
                <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>Type</th>
                <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>Status</th>
                <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)' }}>Details & Evidence</th>
                <th style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--text-secondary)', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredNodes.map((n) => (
                <tr key={n.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>{n.label}</td>
                  <td style={{ padding: '12px 16px' }}><Badge variant="outline">{n.type}</Badge></td>
                  <td style={{ padding: '12px 16px' }}><Badge variant={getStatusBadgeVariant(n.status)}>{n.status}</Badge></td>
                  <td style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <div>{n.details}</div>
                    {n.evidence?.file_path && (
                      <span className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {n.evidence.file_path} {n.evidence.line ? `(L${n.evidence.line})` : ''}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    {n.evidence?.file_path && onViewSourceExcerpt && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => onViewSourceExcerpt(n.evidence!.file_path!, n.evidence?.line)}
                      >
                        Inspect
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

