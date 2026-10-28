import React from 'react';

interface StructuredMarkdownViewerProps {
  content: string;
  className?: string;
}

function renderInlineText(text: string): React.ReactNode[] {
  // Regex pattern for bold (**text**), inline code (`code`), italic (*text* or _text_)
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={match.index} style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={match.index}
          className="mono"
          style={{
            backgroundColor: 'rgba(255, 255, 255, 0.06)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '2px 5px',
            fontSize: '0.9em',
            color: '#38bdf8',
          }}
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith('*') && token.endsWith('*')) {
      parts.push(
        <em key={match.index} style={{ color: 'var(--text-secondary)' }}>
          {token.slice(1, -1)}
        </em>
      );
    } else if (token.startsWith('[') && token.includes('](')) {
      const closingBracket = token.indexOf('](');
      const linkText = token.slice(1, closingBracket);
      const linkUrl = token.slice(closingBracket + 2, -1);
      parts.push(
        <a
          key={match.index}
          href={linkUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#38bdf8', textDecoration: 'underline' }}
        >
          {linkText}
        </a>
      );
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts;
}

export const StructuredMarkdownViewer: React.FC<StructuredMarkdownViewerProps> = ({ content, className = '' }) => {
  if (!content) return null;

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Empty lines
    if (!trimmed) {
      i++;
      continue;
    }

    // Fenced Code Block
    if (trimmed.startsWith('```')) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(
        <pre
          key={`code-${elements.length}`}
          className="mono"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            fontSize: '12px',
            overflowX: 'auto',
            margin: '12px 0',
            lineHeight: 1.5,
            color: 'var(--text-primary)',
          }}
        >
          <code>{codeLines.join('\n')}</code>
        </pre>
      );
      continue;
    }

    // Headings
    if (trimmed.startsWith('#### ')) {
      elements.push(
        <h5
          key={`h4-${elements.length}`}
          style={{
            fontSize: '14px',
            fontWeight: 600,
            marginTop: '16px',
            marginBottom: '6px',
            color: 'var(--text-primary)',
          }}
        >
          {renderInlineText(trimmed.slice(5))}
        </h5>
      );
      i++;
      continue;
    }
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h4
          key={`h3-${elements.length}`}
          style={{
            fontSize: '15px',
            fontWeight: 600,
            marginTop: '18px',
            marginBottom: '8px',
            color: 'var(--text-primary)',
          }}
        >
          {renderInlineText(trimmed.slice(4))}
        </h4>
      );
      i++;
      continue;
    }
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h3
          key={`h2-${elements.length}`}
          style={{
            fontSize: '17px',
            fontWeight: 700,
            marginTop: '22px',
            marginBottom: '10px',
            color: 'var(--text-primary)',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: '4px',
          }}
        >
          {renderInlineText(trimmed.slice(3))}
        </h3>
      );
      i++;
      continue;
    }
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h2
          key={`h1-${elements.length}`}
          style={{
            fontSize: '20px',
            fontWeight: 700,
            marginTop: '24px',
            marginBottom: '12px',
            color: 'var(--text-primary)',
          }}
        >
          {renderInlineText(trimmed.slice(2))}
        </h2>
      );
      i++;
      continue;
    }

    // Horizontal Rule
    if (trimmed === '---' || trimmed === '***') {
      elements.push(
        <hr
          key={`hr-${elements.length}`}
          style={{
            border: 'none',
            borderTop: '1px solid var(--border-subtle)',
            margin: '18px 0',
          }}
        />
      );
      i++;
      continue;
    }

    // Blockquote / Callout
    if (trimmed.startsWith('>')) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
        i++;
      }
      elements.push(
        <div
          key={`quote-${elements.length}`}
          style={{
            borderLeft: '3px solid #38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.06)',
            padding: '10px 16px',
            borderRadius: '0 var(--radius-md) var(--radius-md) 0',
            margin: '12px 0',
            fontSize: '13px',
            color: 'var(--text-primary)',
          }}
        >
          {quoteLines.map((ql, qIdx) => (
            <p key={qIdx} style={{ margin: qIdx > 0 ? '6px 0 0 0' : '0', lineHeight: 1.5 }}>
              {renderInlineText(ql)}
            </p>
          ))}
        </div>
      );
      continue;
    }

    // Markdown Table
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const headerRow = tableLines[0].split('|').slice(1, -1).map((c) => c.trim());
        const dataRows = tableLines
          .slice(2)
          .map((row) => row.split('|').slice(1, -1).map((c) => c.trim()));

        elements.push(
          <div
            key={`table-${elements.length}`}
            style={{
              overflowX: 'auto',
              margin: '14px 0',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-subtle)' }}>
                  {headerRow.map((h, hIdx) => (
                    <th
                      key={hIdx}
                      style={{
                        padding: '8px 12px',
                        textAlign: 'left',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                      }}
                    >
                      {renderInlineText(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dataRows.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    style={{
                      borderBottom: rIdx < dataRows.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                    }}
                  >
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>
                        {renderInlineText(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Unordered List (- or *)
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const listItems: string[] = [];
      while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
        listItems.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul
          key={`ul-${elements.length}`}
          style={{
            paddingLeft: '20px',
            margin: '8px 0',
            fontSize: '13px',
            lineHeight: 1.6,
            color: 'var(--text-secondary)',
          }}
        >
          {listItems.map((item, idx) => (
            <li key={idx} style={{ marginBottom: '4px' }}>
              {renderInlineText(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Ordered List (1. 2. etc.)
    if (/^\d+\.\s/.test(trimmed)) {
      const listItems: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ''));
        i++;
      }
      elements.push(
        <ol
          key={`ol-${elements.length}`}
          style={{
            paddingLeft: '22px',
            margin: '8px 0',
            fontSize: '13px',
            lineHeight: 1.6,
            color: 'var(--text-secondary)',
          }}
        >
          {listItems.map((item, idx) => (
            <li key={idx} style={{ marginBottom: '4px' }}>
              {renderInlineText(item)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Standard Paragraph
    elements.push(
      <p
        key={`p-${elements.length}`}
        style={{
          fontSize: '13px',
          lineHeight: 1.6,
          color: 'var(--text-primary)',
          margin: '8px 0',
        }}
      >
        {renderInlineText(trimmed)}
      </p>
    );
    i++;
  }

  return <div className={className}>{elements}</div>;
};

