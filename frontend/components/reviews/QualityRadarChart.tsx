'use client';

import React, { useState } from 'react';

export interface QualityScores {
  security_score?: number;
  performance_score?: number;
  maintainability_score?: number;
  reliability_score?: number;
  test_coverage_score?: number;
  overall_architecture_score?: number;
}

interface QualityRadarChartProps {
  scores?: QualityScores;
}

interface MetricAxis {
  key: keyof QualityScores;
  label: string;
  shortLabel: string;
}

const METRICS: MetricAxis[] = [
  { key: 'security_score', label: 'Security', shortLabel: 'SEC' },
  { key: 'performance_score', label: 'Performance', shortLabel: 'PERF' },
  { key: 'maintainability_score', label: 'Maintainability', shortLabel: 'MAINT' },
  { key: 'reliability_score', label: 'Reliability', shortLabel: 'REL' },
  { key: 'test_coverage_score', label: 'Test Coverage', shortLabel: 'TEST' },
];

export const QualityRadarChart: React.FC<QualityRadarChartProps> = ({ scores }) => {
  const [activeMetric, setActiveMetric] = useState<MetricAxis | null>(null);

  // Defaults if scores not provided yet (scale 1 to 10)
  const resolvedScores: Record<string, number> = {
    security_score: Math.min(10, Math.max(1, scores?.security_score ?? 8)),
    performance_score: Math.min(10, Math.max(1, scores?.performance_score ?? 8)),
    maintainability_score: Math.min(10, Math.max(1, scores?.maintainability_score ?? 7)),
    reliability_score: Math.min(10, Math.max(1, scores?.reliability_score ?? 8)),
    test_coverage_score: Math.min(10, Math.max(1, scores?.test_coverage_score ?? 6)),
    overall_architecture_score: Math.min(10, Math.max(1, scores?.overall_architecture_score ?? 8)),
  };

  const overallScore = resolvedScores.overall_architecture_score;

  // Radar geometry
  const size = 260;
  const center = size / 2;
  const radius = size * 0.38;
  const numAxes = METRICS.length;
  const angleStep = (2 * Math.PI) / numAxes;

  // Grid levels (2, 4, 6, 8, 10)
  const levels = [2, 4, 6, 8, 10];

  const getCoordinates = (axisIndex: number, score: number) => {
    // Start from top (-PI / 2)
    const angle = axisIndex * angleStep - Math.PI / 2;
    const r = (score / 10) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  // Polygon points for resolved scores
  const polygonPoints = METRICS.map((m, idx) => {
    const val = resolvedScores[m.key] || 1;
    const coords = getCoordinates(idx, val);
    return `${coords.x},${coords.y}`;
  }).join(' ');

  const getScoreColor = (score: number) => {
    if (score >= 8) return '#10b981'; // Emerald
    if (score >= 5) return '#eab308'; // Amber
    return '#ef4444'; // Red
  };

  return (
    <div
      style={{
        backgroundColor: '#222222',
        border: '1px solid #2e2e2e',
        borderRadius: '6px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span
            className="mono"
            style={{
              fontSize: '11px',
              color: '#a1a1aa',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            ARCHITECTURE HYGIENE RADAR
          </span>
          <div
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: '#f4f4f5',
              marginTop: '2px',
              fontFamily: 'Space Grotesk, sans-serif',
            }}
          >
            Code Quality Evaluation
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '6px',
            backgroundColor: '#161616',
            border: '1px solid #2e2e2e',
            padding: '6px 12px',
            borderRadius: '4px',
          }}
        >
          <span style={{ fontSize: '11px', color: '#a1a1aa' }}>Overall:</span>
          <span
            className="mono"
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: getScoreColor(overallScore),
            }}
          >
            {overallScore}
          </span>
          <span className="mono" style={{ fontSize: '11px', color: '#71717a' }}>
            /10
          </span>
        </div>
      </div>

      {/* Main Grid: Radar on left, Granular Bars on right */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(240px, 1fr) minmax(260px, 1.2fr)',
          gap: '20px',
          alignItems: 'center',
        }}
      >
        {/* SVG Radar */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <svg
            viewBox={`0 0 ${size} ${size}`}
            style={{ width: '100%', maxWidth: '260px', height: 'auto', overflow: 'visible' }}
          >
            {/* Concentric Grid Polygons */}
            {levels.map((lvl) => {
              const pts = METRICS.map((_, idx) => {
                const c = getCoordinates(idx, lvl);
                return `${c.x},${c.y}`;
              }).join(' ');
              return (
                <polygon
                  key={lvl}
                  points={pts}
                  fill="none"
                  stroke="#2e2e2e"
                  strokeWidth={lvl === 10 ? 1.5 : 0.75}
                  strokeDasharray={lvl % 4 !== 0 ? '2 2' : undefined}
                />
              );
            })}

            {/* Axes Lines */}
            {METRICS.map((m, idx) => {
              const outer = getCoordinates(idx, 10);
              const labelPos = getCoordinates(idx, 12);
              return (
                <g key={m.key}>
                  <line
                    x1={center}
                    y1={center}
                    x2={outer.x}
                    y2={outer.y}
                    stroke="#2e2e2e"
                    strokeWidth="1"
                  />
                  <text
                    x={labelPos.x}
                    y={labelPos.y + 4}
                    fill={activeMetric?.key === m.key ? '#10b981' : '#a1a1aa'}
                    fontSize="10"
                    fontFamily="Space Mono, monospace"
                    textAnchor="middle"
                  >
                    {m.shortLabel}
                  </text>
                </g>
              );
            })}

            {/* Data Polygon */}
            <polygon
              points={polygonPoints}
              fill="rgba(16, 185, 129, 0.2)"
              stroke="#10b981"
              strokeWidth="2"
            />

            {/* Data Points */}
            {METRICS.map((m, idx) => {
              const val = resolvedScores[m.key] || 1;
              const coords = getCoordinates(idx, val);
              const isHovered = activeMetric?.key === m.key;
              return (
                <circle
                  key={m.key}
                  cx={coords.x}
                  cy={coords.y}
                  r={isHovered ? 5 : 3.5}
                  fill={isHovered ? '#f4f4f5' : '#10b981'}
                  stroke="#161616"
                  strokeWidth="1.5"
                  style={{ cursor: 'pointer', transition: 'r 0.2s ease' }}
                  onMouseEnter={() => setActiveMetric(m)}
                  onMouseLeave={() => setActiveMetric(null)}
                />
              );
            })}
          </svg>
        </div>

        {/* Granular Metric Bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {METRICS.map((m) => {
            const val = resolvedScores[m.key] || 1;
            const pct = (val / 10) * 100;
            const col = getScoreColor(val);
            const isHovered = activeMetric?.key === m.key;

            return (
              <div
                key={m.key}
                onMouseEnter={() => setActiveMetric(m)}
                onMouseLeave={() => setActiveMetric(null)}
                style={{
                  padding: '8px 12px',
                  backgroundColor: isHovered ? '#282828' : '#161616',
                  border: isHovered ? '1px solid #10b981' : '1px solid #2e2e2e',
                  borderRadius: '4px',
                  transition: 'all 0.15s ease',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span
                    style={{
                      fontSize: '12px',
                      color: isHovered ? '#f4f4f5' : '#d4d4d8',
                      fontWeight: 500,
                    }}
                  >
                    {m.label}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                    <span
                      className="mono"
                      style={{
                        fontSize: '12px',
                        fontWeight: 700,
                        color: col,
                      }}
                    >
                      {val}
                    </span>
                    <span className="mono" style={{ fontSize: '10px', color: '#71717a' }}>
                      /10
                    </span>
                  </div>
                </div>

                {/* Progress Track */}
                <div
                  style={{
                    width: '100%',
                    height: '4px',
                    backgroundColor: '#2e2e2e',
                    borderRadius: '2px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${pct}%`,
                      height: '100%',
                      backgroundColor: col,
                      borderRadius: '2px',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

