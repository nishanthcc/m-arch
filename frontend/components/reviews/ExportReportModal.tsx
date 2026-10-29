'use client';

import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { ReviewReport } from '@/lib/types';
import { api } from '@/lib/api/client';

export type PresentationMode = 'technical_review' | 'simplified_version' | 'developer' | 'simple' | 'professional' | 'executive';

interface ExportReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  reviewId?: string;
  report: ReviewReport | null;
  initialMode?: PresentationMode;
}

export const ExportReportModal: React.FC<ExportReportModalProps> = ({
  isOpen,
  onClose,
  reviewId,
  report: initialReport,
  initialMode = 'technical_review',
}) => {
  const [currentMode, setCurrentMode] = useState<PresentationMode>(initialMode);
  const [report, setReport] = useState<ReviewReport | null>(initialReport);
  const [loadingMode, setLoadingMode] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (initialReport) {
      setReport(initialReport);
    }
  }, [initialReport]);

  useEffect(() => {
    setCurrentMode(initialMode);
  }, [initialMode]);

  const handleModeChange = async (newMode: PresentationMode) => {
    setCurrentMode(newMode);
    if (!reviewId) return;
    setLoadingMode(true);
    try {
      const rep = await api.getReviewReport(reviewId, newMode);
      setReport(rep);
    } catch (err: any) {
      console.error('Failed to fetch presentation report mode:', err);
    } finally {
      setLoadingMode(false);
    }
  };

  if (!report) return null;

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(report.markdown_report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    const blob = new Blob([report.markdown_report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `m-arch-review-${report.project_name.toLowerCase().replace(/\s+/g, '-')}-${currentMode}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrintHTML = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(report.html_report);
      printWindow.document.close();
      printWindow.focus();
      printWindow.print();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Export Canonical Review Report" width="650px">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Export this evidence-backed review. Both persona views share the exact same verified findings, adapting vocabulary and structure according to strict audience constraints.
        </p>

        {/* Dual-Mode Presentation Selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Select Persona Architecture Mode
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {(
              [
                {
                  id: 'technical_review' as const,
                  label: 'Technical Review',
                  desc: 'Root cause analysis, line numbers & explicit remediation',
                },
                {
                  id: 'simplified_version' as const,
                  label: 'Simplified Version',
                  desc: 'Real-world impact, plain language, zero technical jargon',
                },
              ] as const
            ).map((m) => {
              const isSelected = currentMode === m.id || (m.id === 'technical_review' && currentMode === 'developer') || (m.id === 'simplified_version' && currentMode === 'simple');
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => handleModeChange(m.id)}
                  style={{
                    padding: '12px 14px',
                    backgroundColor: isSelected ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                    border: isSelected ? '2px solid var(--text-primary)' : '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{m.label}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>{m.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Button variant="primary" onClick={handleDownloadMarkdown} disabled={loadingMode}>
            Download Markdown (.md)
          </Button>
          <Button variant="secondary" onClick={handleCopyMarkdown} disabled={loadingMode}>
            {copied ? 'Copied to Clipboard!' : 'Copy Markdown'}
          </Button>
          <Button variant="secondary" onClick={handlePrintHTML} disabled={loadingMode}>
            Open Printable HTML
          </Button>
        </div>

        {/* Preview Container */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Markdown Preview ({currentMode.toUpperCase()} mode):
            </span>
            {loadingMode && (
              <span className="mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                Formatting presentation view...
              </span>
            )}
          </div>
          <pre
            className="mono"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              padding: '12px',
              borderRadius: 'var(--radius-md)',
              fontSize: '11px',
              maxHeight: '160px',
              overflowY: 'auto',
              color: 'var(--text-primary)',
              whiteSpace: 'pre-wrap',
            }}
          >
            {report.markdown_report.slice(0, 700)}...
          </pre>
        </div>
      </div>
    </Modal>
  );
};
