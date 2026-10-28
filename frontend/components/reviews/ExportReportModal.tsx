'use client';

import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { ReviewReport } from '@/lib/types';

interface ExportReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: ReviewReport | null;
}

export const ExportReportModal: React.FC<ExportReportModalProps> = ({
  isOpen,
  onClose,
  report,
}) => {
  const [copied, setCopied] = useState(false);

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
    a.download = `m-arch-review-${report.project_name.toLowerCase().replace(/\s+/g, '-')}.md`;
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
    <Modal isOpen={isOpen} onClose={onClose} title="Export Engineering Review Report" width="600px">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Export this evidence-backed technical review for sharing with engineering leadership or compliance archives.
        </p>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Button variant="primary" onClick={handleDownloadMarkdown}>
            Download Markdown (.md)
          </Button>
          <Button variant="secondary" onClick={handleCopyMarkdown}>
            {copied ? 'Copied to Clipboard!' : 'Copy Markdown'}
          </Button>
          <Button variant="secondary" onClick={handlePrintHTML}>
            Open Printable HTML
          </Button>
        </div>

        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
          <span className="mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Markdown Preview (first 500 chars):
          </span>
          <pre
            className="mono"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              padding: '12px',
              borderRadius: 'var(--radius-md)',
              fontSize: '11px',
              marginTop: '8px',
              maxHeight: '150px',
              overflowY: 'auto',
              color: 'var(--text-primary)',
            }}
          >
            {report.markdown_report.slice(0, 500)}...
          </pre>
        </div>
      </div>
    </Modal>
  );
};
