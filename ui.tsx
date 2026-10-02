// src/components/ui.tsx
import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react';

export interface SegmentedOption {
  value?: string;
  id?: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  count?: number | string;
  badge?: React.ReactNode;
  title?: string;
}

export interface SegmentedProps {
  options: (string | SegmentedOption)[];
  value: string;
  onChange: (value: string) => void;
  size?: 'sm' | 'md';
  variant?: 'pills' | 'tabs' | 'brand';
  label?: string;
  ariaLabel?: string;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Segmented control component to replace ad-hoc tabs, filter pills, and preset switches.
 * Fully accessible and token-aligned.
 */
export const Segmented: React.FC<SegmentedProps> = ({
  options,
  value,
  onChange,
  size = 'sm',
  variant = 'pills',
  label,
  ariaLabel,
  className = '',
  style = {},
}) => {
  const isSm = size === 'sm';
  const paddingContainer = isSm ? '2px' : '4px';
  const paddingBtn = isSm ? '4px 10px' : '6px 14px';
  const fontSize = isSm ? 'var(--fs-xs)' : 'var(--fs-sm)';

  const control = (
    <div
      role="tablist"
      aria-label={ariaLabel || label}
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        backgroundColor: 'var(--bg-2)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)',
        padding: paddingContainer,
        gap: '2px',
        ...style,
      }}
    >
      {options.map((opt) => {
        const optionObj: SegmentedOption =
          typeof opt === 'string'
            ? { value: opt, label: opt }
            : opt;

        const optValue = optionObj.value ?? optionObj.id ?? '';
        const isSelected = value === optValue;

        let activeBg = 'var(--bg-3)';
        let activeColor = 'var(--text-1)';
        let activeBorder = '1px solid var(--border-strong)';

        if (variant === 'brand') {
          activeBg = 'var(--brand)';
          activeColor = 'var(--bg-0)';
          activeBorder = '1px solid var(--brand)';
        }

        return (
          <button
            key={optValue}
            role="tab"
            type="button"
            title={optionObj.title}
            aria-label={typeof optionObj.label === 'string' ? optionObj.label : optionObj.title}
            aria-selected={isSelected}
            onClick={() => onChange(optValue)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              padding: paddingBtn,
              fontSize,
              fontWeight: isSelected ? 600 : 500,
              borderRadius: 'calc(var(--radius-sm) - 2px)',
              border: isSelected ? activeBorder : '1px solid transparent',
              backgroundColor: isSelected ? activeBg : 'transparent',
              color: isSelected ? activeColor : 'var(--text-2)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
              lineHeight: 1.2,
            }}
          >
            {optionObj.icon && (
              <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                {optionObj.icon}
              </span>
            )}
            <span>{optionObj.label}</span>
            {optionObj.count !== undefined && (
              <span
                style={{
                  fontSize: 'calc(var(--fs-xs) - 1px)',
                  padding: '1px 5px',
                  borderRadius: '10px',
                  backgroundColor: isSelected ? 'var(--brand-bg)' : 'var(--bg-0)',
                  color: isSelected ? 'var(--text-1)' : 'var(--text-3)',
                  fontWeight: 700,
                }}
              >
                {optionObj.count}
              </span>
            )}
            {optionObj.badge}
          </button>
        );
      })}
    </div>
  );

  if (label) {
    return (
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-3)', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
          {label}
        </span>
        {control}
      </div>
    );
  }

  return control;
};

export interface SeverityBadgeProps {
  severity: 'CRITICAL' | 'MEDIUM' | 'SAFE' | 'critical' | 'medium' | 'safe' | string;
  label?: string;
  score?: number | string;
  icon?: React.ReactNode;
  size?: 'sm' | 'md';
  style?: React.CSSProperties;
}

/**
 * Standard Severity Badge component.
 * Adheres to rule: always pair with an icon + label, never colour alone.
 */
export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  label,
  score,
  icon,
  size = 'sm',
  style = {},
}) => {
  const sev = (severity || 'SAFE').toUpperCase();
  const isSm = size === 'sm';
  const iconSize = isSm ? 12 : 14;

  let bg = 'var(--sev-safe-bg)';
  let color = 'var(--sev-safe)';
  let border = 'rgba(52, 211, 153, 0.35)';
  let defaultIcon = <CheckCircle2 size={iconSize} />;
  let defaultLabel = 'SAFE';

  if (sev === 'CRITICAL' || sev === 'DANGER' || sev === 'HIGH') {
    bg = 'var(--sev-critical-bg)';
    color = 'var(--sev-critical)';
    border = 'rgba(255, 92, 108, 0.35)';
    defaultIcon = <AlertCircle size={iconSize} />;
    defaultLabel = 'CRITICAL';
  } else if (sev === 'MEDIUM' || sev === 'WARNING') {
    bg = 'var(--sev-medium-bg)';
    color = 'var(--sev-medium)';
    border = 'rgba(255, 176, 32, 0.35)';
    defaultIcon = <AlertTriangle size={iconSize} />;
    defaultLabel = 'MEDIUM';
  }

  const displayLabel = label || defaultLabel;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: 'var(--fs-xs)',
        fontWeight: 700,
        letterSpacing: '0.04em',
        padding: isSm ? '2px 7px' : '4px 9px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: bg,
        color,
        border: `1px solid ${border}`,
        lineHeight: 1.2,
        textTransform: 'uppercase',
        ...style,
      }}
    >
      {icon || defaultIcon}
      <span>{displayLabel}</span>
      {score !== undefined && (
        <span
          style={{
            marginLeft: '2px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 800,
            opacity: 0.9,
          }}
        >
          {score}
        </span>
      )}
    </span>
  );
};

export interface ChipProps {
  children: React.ReactNode;
  variant?: 'brand' | 'neutral' | 'warning' | 'danger' | 'success';
  className?: string;
  style?: React.CSSProperties;
}

export const Chip: React.FC<ChipProps> = ({
  children,
  variant = 'brand',
  className = '',
  style = {},
}) => {
  let bg = 'var(--brand-bg)';
  let color = 'var(--brand)';
  let border = 'var(--brand)';

  if (variant === 'neutral') {
    bg = 'var(--bg-2)';
    color = 'var(--text-2)';
    border = 'var(--border)';
  } else if (variant === 'warning') {
    bg = 'var(--sev-medium-bg)';
    color = 'var(--sev-medium)';
    border = 'var(--sev-medium)';
  } else if (variant === 'danger') {
    bg = 'var(--sev-critical-bg)';
    color = 'var(--sev-critical)';
    border = 'var(--sev-critical)';
  } else if (variant === 'success') {
    bg = 'var(--sev-safe-bg)';
    color = 'var(--sev-safe)';
    border = 'var(--sev-safe)';
  }

  return (
    <span
      className={`chip ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: 'var(--fs-xs)',
        fontWeight: 600,
        padding: '2px 8px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: bg,
        color,
        border: `1px solid ${border}`,
        lineHeight: 1.2,
        ...style,
      }}
    >
      {children}
    </span>
  );
};

