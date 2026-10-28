import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  description?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  description,
  id,
  style = {},
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{
            fontSize: '13px',
            fontWeight: 500,
            color: 'var(--text-primary)',
          }}
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        style={{
          backgroundColor: 'var(--bg-primary)',
          border: error ? '1px solid var(--severity-critical)' : '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-md)',
          padding: '8px 12px',
          fontSize: '14px',
          color: 'var(--text-primary)',
          outline: 'none',
          fontFamily: 'inherit',
          width: '100%',
          ...style,
        }}
        {...props}
      />
      {description && !error && (
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{description}</span>
      )}
      {error && (
        <span style={{ fontSize: '12px', color: 'var(--severity-critical)' }}>{error}</span>
      )}
    </div>
  );
};
