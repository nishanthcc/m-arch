import React from 'react';
import { Finding, EvidenceItem } from '@/lib/types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface FindingCardProps {
  finding: Finding;
  onViewEvidence: (evidence: EvidenceItem[], title: string) => void;
  mode?: 'technical_review' | 'simplified_version';
}

export function simplifyFindingForUI(f: Finding) {
  const corpus = `${f.title} ${f.explanation} ${f.impact} ${f.remediation}`.toLowerCase();

  // 1. Lockfile / Reproducible Builds
  if (corpus.includes('lockfile')) {
    return {
      title: 'Missing Exact Recipe for Software Building Blocks (Lockfile)',
      problem:
        "The project does not save a frozen 'lockfile' recording the exact copies of libraries used. Without this recipe, installing the app on a new computer might pull in slightly different, untested versions that cause unexpected crashes.",
      whyMatters:
        'If an outside software company updates a library tomorrow, your app could suddenly stop working the next time you reinstall or deploy it.',
      fix: 'Save an official frozen lockfile (such as requirements.txt with pinned versions) so every computer installs the exact same copies.',
    };
  }

  // 2. Authentication & Rate Limiting
  if (corpus.includes('authentication') || corpus.includes('rate limit')) {
    return {
      title: 'Anyone Can Access the App Without Logging In or Limits',
      problem:
        'There is no digital lock on the front door. Visitors do not have to sign in or prove who they are, and there is no speed limit on how many requests one person can send.',
      whyMatters:
        'Anyone on the internet could flood your server with millions of automated requests, overloading your system, crashing the website, or racking up expensive hosting bills.',
      fix: 'Add a login screen or secret access key, and set a speed limit (rate limiting) so each visitor can only make a sensible number of requests per minute.',
    };
  }

  // 3. Scanner Prototype / Synthetic Calibration
  if (
    corpus.includes('synthetic') ||
    corpus.includes('explicit limitations') ||
    corpus.includes('statistical') ||
    corpus.includes('heuristic')
  ) {
    return {
      title: 'Image Scanner Was Only Tested on Artificial Samples, Not Real Photos',
      problem:
        'The core scanner was only tested on computer-generated test pictures. The creators explicitly note that it is an early prototype and not a reliable tool for detecting hidden messages in everyday photos.',
      whyMatters:
        'In real life, the scanner frequently makes mistakes—either raising false alarms on innocent everyday photos or missing truly hidden files. Relying on it in serious situations could lead to incorrect decisions.',
      fix: 'Put a clear warning label on the screen explaining that the scanner is an experimental prototype, and train it on thousands of genuine camera photographs before serious use.',
    };
  }

  // 4. Unpinned Dependencies
  if (corpus.includes('unpinned')) {
    const isFrontend = corpus.includes('frontend') || corpus.includes('package.json') || corpus.includes('javascript');
    const comp = isFrontend ? 'Frontend Web Interface' : 'Backend Programming';
    return {
      title: `${comp} Libraries Don't Have Locked Version Numbers`,
      problem: `The ${comp.toLowerCase()} lists its external libraries with open version ranges instead of exact, tested version numbers.`,
      whyMatters:
        'Automatic minor updates from third parties can quietly introduce bugs, visual glitches, or unexpected breaking changes into your website without warning.',
      fix: 'Lock every external library to a single exact version number that you have tested and verified.',
    };
  }

  // 5. Undocumented Environment Variables
  if (corpus.includes('environment variable') || corpus.includes('stego_model_path') || corpus.includes('undocumented')) {
    return {
      title: 'Missing Setup Instructions for Important Server Settings',
      problem:
        'The app depends on hidden background configuration settings, but the guide never explains what values to set, what they mean, or what happens if they are omitted.',
      whyMatters:
        'When trying to host the app online, the server might fail to start or crash randomly because required setup numbers were never provided.',
      fix: "Add a clear 'Server Setup Checklist' to the documentation explaining every setting, its purpose, and safe default values.",
    };
  }

  // 6. Worker Configuration Conflict
  if (corpus.includes('worker') && corpus.includes('contradictory')) {
    return {
      title: 'Conflicting Instructions on How Many Helper Processes to Run',
      problem:
        'The setup manual gives two opposite instructions: one section says to start helper workers automatically, while another section insists on running exactly one worker.',
      whyMatters:
        'Running multiple workers when the code expects only one can cause the app to lose track of temporary files and produce inconsistent results.',
      fix: 'Update the setup guide so both local testing and live deployment use the exact same worker configuration.',
    };
  }

  // 7. CORS
  if (corpus.includes('cors')) {
    return {
      title: 'Missing Rules on Which Websites Can Talk to Your Server',
      problem:
        'The instructions do not clearly explain how to list approved website addresses that are permitted to connect to your backend.',
      whyMatters:
        'A small mistake here could accidentally block your own website from working, or unintentionally leave the door open to unauthorized websites.',
      fix: 'Add a simple example in the documentation showing the exact format for listing allowed website addresses (URLs).',
    };
  }

  // 8. License Missing
  if (corpus.includes('license')) {
    const isFe = corpus.includes('frontend') || corpus.includes('package.json');
    const target = isFe ? 'Frontend Code' : 'Third-Party Libraries';
    return {
      title: `Missing Legal License Information for ${target}`,
      problem: `The project does not explicitly state what legal license covers the ${target.toLowerCase()}.`,
      whyMatters:
        'Without clear licensing, companies and developers might be legally prohibited from using, contributing to, or sharing your software.',
      fix: 'Add an official open-source license statement (such as the standard MIT License) so everyone knows they can safely use your code.',
    };
  }

  // 9. Clean Scan: Credentials
  if (corpus.includes('credential') || corpus.includes('password')) {
    return {
      title: 'No Passwords or Secret Keys Left in Plain Sight (Safe)',
      problem:
        'Our automated scan checked all project files and confirmed that developers did not accidentally leave any secret passwords, access tokens, or security keys written directly in the code.',
      whyMatters:
        'Leaving passwords in code is like leaving your front-door key under the mat. Keeping them out prevents unauthorized access.',
      fix: 'Keep following this good practice by storing any future passwords in secure server settings.',
    };
  }

  // 10. Clean Scan: Dynamic Code Execution
  if (corpus.includes('dynamic code') || corpus.includes('eval') || corpus.includes('exec')) {
    return {
      title: 'No Dangerous Command Execution Found (Safe)',
      problem:
        'The project avoids dangerous programming shortcuts that would let visitors run raw system commands directly on your server.',
      whyMatters: 'This protects your server against malicious users attempting to run harmful software remotely.',
      fix: 'Keep following this standard and avoid adding dynamic command execution in future updates.',
    };
  }

  // 11. Clean Scan: SQL
  if (corpus.includes('sql') || corpus.includes('orm')) {
    return {
      title: 'No Database Queries Detected',
      problem: 'The analyzed files do not interact with a database system.',
      whyMatters:
        'Because there is no database connected yet, there is no risk of database theft, but future storage features will need proper protections.',
      fix: 'When you add a database later, make sure to use safe, parameterized connections.',
    };
  }

  // 12. Extraction Format
  if (corpus.includes('extraction') || corpus.includes('svai')) {
    return {
      title: 'Can Only Read One Custom Type of Hidden File',
      problem:
        'The software can only decode a single, custom format made specifically for this tool. It cannot read or unpack files hidden by standard, popular tools.',
      whyMatters:
        'In practical use, most hidden messages will be invisible to this software because they use different file formats.',
      fix: 'Add support for common, widely used file formats so the tool can extract messages from more sources.',
    };
  }

  // Generic fallback cleanup
  const cleanTitle = f.title.replace(/\(code_agent\)|\(documentation_agent\)|\(dependency_agent\)|\(security_agent\)/gi, '').trim();
  const cleanProb = f.explanation.replace(/(backend|frontend|src)\/[^\s,]+/gi, 'the codebase').replace(/CWE-\d+/gi, '').trim();
  const cleanWhy = f.impact.replace(/(backend|frontend|src)\/[^\s,]+/gi, 'the application').trim();
  const cleanFix = f.remediation.replace(/(backend|frontend|src)\/[^\s,]+/gi, 'the project').trim();

  return {
    title: cleanTitle || 'General System Observation',
    problem: cleanProb || 'A code quality or architectural improvement was noted.',
    whyMatters: cleanWhy || 'Addressing this item ensures a smoother, more reliable user experience.',
    fix: cleanFix || 'Review and update this component according to standard software practices.',
  };
}

export const FindingCard: React.FC<FindingCardProps> = ({ finding, onViewEvidence, mode = 'technical_review' }) => {
  const isSimplified = mode === 'simplified_version';
  const simplified = isSimplified ? simplifyFindingForUI(finding) : null;

  return (
    <div
      style={{
        backgroundColor: '#222222',
        border: '1px solid #2e2e2e',
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
            {!isSimplified && (
              <>
                <Badge variant="verification" value={finding.verification_status}>
                  {finding.verification_status}
                </Badge>
                <span
                  className="mono"
                  style={{ fontSize: '11px', color: 'var(--text-secondary)' }}
                >
                  Agent: {finding.agent_id}
                </span>
                {finding.agent_id === 'code_agent' && (
                  <span
                    className="mono"
                    style={{
                      fontSize: '10px',
                      padding: '1px 6px',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(16, 185, 129, 0.15)',
                      color: '#10b981',
                      fontWeight: 600,
                    }}
                  >
                    Gemini
                  </span>
                )}
              </>
            )}
            {isSimplified && (
              <span
                style={{
                  fontSize: '11px',
                  color: '#10b981',
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontWeight: 500,
                }}
              >
                Plain English
              </span>
            )}
          </div>
          <h4
            style={{
              fontSize: '15px',
              fontWeight: 600,
              color: '#f4f4f5',
              fontFamily: 'Space Grotesk, sans-serif',
              margin: '2px 0 0 0',
            }}
          >
            {isSimplified ? simplified!.title : finding.title}
          </h4>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          {!isSimplified && (
            <span
              className="mono"
              style={{ fontSize: '11px', color: 'var(--text-secondary)' }}
              title={finding.confidence_interpretation}
            >
              Conf: {Math.round(finding.confidence * 100)}%
            </span>
          )}
          {!isSimplified && finding.evidence_items && finding.evidence_items.length > 0 && (
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

      <div style={{ fontSize: '13px', color: isSimplified ? '#e4e4e7' : 'var(--text-secondary)', lineHeight: 1.6 }}>
        {isSimplified ? (
          <div>
            <strong style={{ color: '#f4f4f5', display: 'block', marginBottom: '4px' }}>
              What is the problem?
            </strong>
            <span>{simplified!.problem}</span>
          </div>
        ) : (
          <div>
            <strong style={{ color: '#f4f4f5', display: 'block', marginBottom: '4px' }}>
              Issue Identified:
            </strong>
            <span>{finding.explanation}</span>
          </div>
        )}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px',
          padding: '14px',
          backgroundColor: '#161616',
          border: '1px solid #2e2e2e',
          borderRadius: 'var(--radius-md)',
          fontSize: '12px',
          lineHeight: 1.5,
        }}
      >
        <div>
          <strong style={{ color: '#f4f4f5', display: 'block', marginBottom: '4px' }}>
            {isSimplified ? 'Why does it matter?' : 'Technical Root Cause:'}
          </strong>
          <span style={{ color: '#a1a1aa' }}>
            {isSimplified ? simplified!.whyMatters : finding.impact}
          </span>
        </div>
        <div>
          <strong style={{ color: '#10b981', display: 'block', marginBottom: '4px' }}>
            {isSimplified ? 'How do we fix it?' : 'Specific Remediation Steps:'}
          </strong>
          <span style={{ color: '#d4d4d8' }}>
            {isSimplified ? simplified!.fix : finding.remediation}
          </span>
        </div>
      </div>

      {!isSimplified && finding.limitations && (
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'Space Mono, monospace' }}>
          LIMITATIONS: {finding.limitations}
        </div>
      )}
    </div>
  );
};
