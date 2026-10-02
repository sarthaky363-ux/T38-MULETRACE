// src/components/Kpi.tsx
import React from 'react';
import { LucideIcon, ChevronRight } from 'lucide-react';

export type KpiTone = "neutral" | "danger" | "success" | "warning";

export interface KpiProps {
  Icon: LucideIcon;
  label: string;
  value: string | number;
  caption?: string;
  tone?: KpiTone;
  compact?: boolean;
  onClick?: () => void;
  showChevron?: boolean;
  title?: string;
}

/**
 * Standard Kpi tile component.
 * Anatomy: icon, label, big value, caption.
 * Supports compact mode (single row, no captions) and clickable button mode.
 */
export function Kpi({
  Icon,
  label,
  value,
  caption,
  tone = "neutral",
  compact = false,
  onClick,
  showChevron = false,
  title,
}: KpiProps) {
  const Tag: any = onClick ? "button" : "div";

  return (
    <Tag
      className={`kpi kpi--${tone} ${compact ? 'kpi--compact' : ''} ${onClick ? 'kpi--clickable' : ''}`}
      onClick={onClick}
      title={title}
      type={onClick ? "button" : undefined}
    >
      <span className="kpi-icon" aria-hidden="true">
        <Icon size={compact ? 16 : 18} />
      </span>
      <span className="kpi-body">
        <span className="label">{label}</span>
        <span className="kpi-value mono">{value}</span>
        {!compact && caption && (
          <span className="kpi-caption">{caption}</span>
        )}
      </span>
      {showChevron && (
        <span className="kpi-chevron" aria-hidden="true">
          <ChevronRight size={16} />
        </span>
      )}
    </Tag>
  );
}

export default Kpi;
