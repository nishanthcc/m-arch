'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';
import { SecurityKnowledgeSource } from '@/lib/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';

export default function KnowledgePage() {
  const [collections, setCollections] = useState<SecurityKnowledgeSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Add / Import modal state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [name, setName] = useState('');
  const [organization, setOrganization] = useState('');
  const [canonicalUrl, setCanonicalUrl] = useState('');
  const [versionDate, setVersionDate] = useState('2026-10-27');
  const [license, setLicense] = useState('Internal / Custom');
  const [coverageCategory, setCoverageCategory] = useState('');
  const [ruleTitle, setRuleTitle] = useState('');
  const [ruleId, setRuleId] = useState('');
  const [ruleGuidance, setRuleGuidance] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadCollections = () => {
    setLoading(true);
    api.getKnowledgeCollections()
      .then(setCollections)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCollections();
  }, []);

  const handleToggle = async (id: string, currentStatus: boolean) => {
    try {
      await api.toggleKnowledgeCollection(id, !currentStatus);
      loadCollections();
    } catch (err: any) {
      alert(err.message || 'Error updating collection status');
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      const records = [];
      if (ruleTitle.trim() && ruleGuidance.trim()) {
        records.push({
          id: ruleId.trim() || `RULE-${Math.floor(Math.random() * 900 + 100)}`,
          title: ruleTitle.trim(),
          category: coverageCategory || 'General Security',
          severity: 'high',
          patterns: [],
          guidance: ruleGuidance.trim()
        });
      }

      await api.createKnowledgeCollection({
        id: `custom_${Date.now()}`,
        name: name.trim(),
        organization: organization.trim() || 'Internal Org',
        canonical_url: canonicalUrl.trim() || 'https://internal-compliance.local',
        version_date: versionDate.trim() || '2026-10-27',
        license: license.trim() || 'Proprietary',
        coverage_category: coverageCategory.trim() || 'Custom Guidelines',
        is_enabled: true,
        records: records
      });

      setIsAddOpen(false);
      setName('');
      setOrganization('');
      setCanonicalUrl('');
      setRuleTitle('');
      setRuleId('');
      setRuleGuidance('');
      loadCollections();
    } catch (err: any) {
      alert(err.message || 'Failed to import knowledge collection');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Security Knowledge Manager</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Versioned vulnerability catalogs, MITRE/OWASP standards, and provenance tracking for A2A specialists.
          </p>
        </div>
        <Button variant="primary" onClick={() => setIsAddOpen(true)}>
          + Import Knowledge Collection
        </Button>
      </div>

      {loading ? (
        <p className="mono" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Loading security knowledge collections from database...
        </p>
      ) : collections.length === 0 ? (
        <EmptyState
          title="No Knowledge Collections Active"
          description="Import or seed your security standards and compliance catalogs to power specialist agent grounding."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {collections.map((coll) => {
            const isExpanded = expandedId === coll.id;
            return (
              <Card
                key={coll.id}
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '16px', fontWeight: 600 }}>{coll.name}</span>
                    <Badge variant={coll.source_type === 'bundled_baseline' ? 'outline' : 'neutral'}>
                      {coll.source_type === 'bundled_baseline' ? 'Bundled Baseline' : 'User Imported'}
                    </Badge>
                  </div>
                }
                headerAction={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Badge variant="status" value={coll.is_enabled ? 'ready' : 'failed'}>
                      {coll.is_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleToggle(coll.id, coll.is_enabled)}
                    >
                      {coll.is_enabled ? 'Disable' : 'Enable'}
                    </Button>
                  </div>
                }
                subtitle={
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', marginTop: '6px' }} className="mono">
                    <span>Org: <strong style={{ color: 'var(--text-primary)' }}>{coll.organization}</strong></span>
                    <span>Version: <strong style={{ color: 'var(--text-primary)' }}>{coll.version_date}</strong></span>
                    <span>License: <strong style={{ color: 'var(--text-secondary)' }}>{coll.license || 'Public'}</strong></span>
                    <span>Records: <strong style={{ color: 'var(--text-primary)' }}>{coll.record_count}</strong></span>
                  </div>
                }
              >
                {/* Provenance Details */}
                <div
                  className="mono"
                  style={{
                    padding: '10px 14px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '11px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    margin: '12px 0',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Canonical URL:</span>
                    <a
                      href={coll.canonical_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: 'var(--text-primary)', textDecoration: 'underline' }}
                    >
                      {coll.canonical_url}
                    </a>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Content Hash:</span>
                    <span style={{ color: 'var(--text-muted)' }}>{coll.version_hash ? coll.version_hash.slice(0, 16) : 'N/A'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Assigned Agents:</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{coll.agent_ids.join(', ')}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Coverage Category:</span>
                    <strong style={{ color: 'var(--text-primary)' }}>{coll.coverage_category}</strong>
                  </div>
                </div>

                {/* Inspect Records Accordion */}
                <div>
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : coll.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-primary)',
                      fontSize: '12px',
                      cursor: 'pointer',
                      padding: 0,
                      fontWeight: 600,
                      textDecoration: 'underline',
                      marginBottom: '8px',
                    }}
                  >
                    {isExpanded ? 'Hide Standards Checklist ▲' : `Inspect Standards Checklist (${coll.records.length}) ▼`}
                  </button>

                  {isExpanded && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
                      {coll.records.map((rec: any, idx: number) => (
                        <div
                          key={idx}
                          style={{
                            padding: '10px 14px',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-sm)',
                            backgroundColor: 'var(--bg-elevated)',
                            fontSize: '12px',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                            <span style={{ fontWeight: 600 }} className="mono">{rec.id} - {rec.title}</span>
                            <Badge variant="severity" value={rec.severity || 'high'}>{rec.severity || 'high'}</Badge>
                          </div>
                          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                            {rec.guidance}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Import / Add Knowledge Collection Modal */}
      <Modal isOpen={isAddOpen} onClose={() => setIsAddOpen(false)} title="Import Security Standards Collection">
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input
            label="Collection Name"
            placeholder="e.g. NIST SP 800-53 Baseline, Cloud Security Alliance Controls"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            label="Source Organization"
            placeholder="e.g. NIST, Cloud Security Alliance, Internal SecOps"
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
            required
          />
          <Input
            label="Canonical Source URL"
            placeholder="https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final"
            value={canonicalUrl}
            onChange={(e) => setCanonicalUrl(e.target.value)}
            required
          />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <Input
              label="Version / Release Date"
              value={versionDate}
              onChange={(e) => setVersionDate(e.target.value)}
              placeholder="2026-10-27"
              required
            />
            <Input
              label="Licence"
              value={license}
              onChange={(e) => setLicense(e.target.value)}
              placeholder="e.g. CC BY 4.0, Proprietary"
              required
            />
          </div>
          <Input
            label="Coverage Category"
            placeholder="e.g. Cloud Infrastructure, Cryptography, Access Control"
            value={coverageCategory}
            onChange={(e) => setCoverageCategory(e.target.value)}
            required
          />

          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Initial Control / Standard Rule</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '8px', marginBottom: '8px' }}>
              <Input
                label="Control ID"
                placeholder="e.g. AC-3"
                value={ruleId}
                onChange={(e) => setRuleId(e.target.value)}
              />
              <Input
                label="Rule Title"
                placeholder="Access Enforcement"
                value={ruleTitle}
                onChange={(e) => setRuleTitle(e.target.value)}
              />
            </div>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '6px' }}>
                Remediation & Compliance Guidance
              </label>
              <textarea
                value={ruleGuidance}
                onChange={(e) => setRuleGuidance(e.target.value)}
                rows={3}
                style={{
                  width: '100%',
                  backgroundColor: 'var(--bg-primary)',
                  border: '1px solid var(--border-strong)',
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 12px',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  fontFamily: 'inherit',
                  outline: 'none',
                }}
                placeholder="Enforce approved authorizations for logical access to information and system resources in accordance with applicable access control policies."
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
            <Button type="button" variant="ghost" onClick={() => setIsAddOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={submitting}>
              Save Collection
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
