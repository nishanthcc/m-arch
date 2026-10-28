import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  loading = false,
  disabled,
  style = {},
  ...props
}) => {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    borderRadius: 'var(--radius-md)',
    fontWeight: 500,
    fontSize: size === 'sm' ? '12px' : size === 'lg' ? '15px' : '13px',
    padding: size === 'sm' ? '6px 12px' : size === 'lg' ? '10px 20px' : '8px 16px',
    transition: 'all 0.15s ease',
    border: '1px solid transparent',
    outline: 'none',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.6 : 1,
  };

  let variantStyle: React.CSSProperties = {};
  if (variant === 'primary') {
    variantStyle = {
      backgroundColor: 'var(--accent)',
      color: 'var(--accent-contrast)',
      borderColor: 'var(--accent)',
    };
  } else if (variant === 'secondary') {
    variantStyle = {
      backgroundColor: 'var(--bg-elevated)',
      color: 'var(--text-primary)',
      borderColor: 'var(--border-strong)',
    };
  } else if (variant === 'danger') {
    variantStyle = {
      backgroundColor: 'rgba(220, 38, 38, 0.15)',
      color: 'var(--severity-critical)',
      borderColor: 'rgba(220, 38, 38, 0.4)',
    };
  } else if (variant === 'ghost') {
    variantStyle = {
      backgroundColor: 'transparent',
      color: 'var(--text-secondary)',
      borderColor: 'transparent',
    };
  }

  return (
    <button
      disabled={disabled || loading}
      style={{ ...baseStyle, ...variantStyle, ...style }}
      {...props}
    >
      {loading ? (
        <span className="mono" style={{ fontSize: '11px' }}>
          Processing...
        </span>
      ) : (
        children
      )}
    </button>
  );
};
