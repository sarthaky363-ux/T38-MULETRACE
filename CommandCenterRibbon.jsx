import React, { useState } from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { Kpi } from './Kpi';
import { fmtINRCompact, fmtPct } from '../lib/format';
import { 
  Users, 
  AlertTriangle, 
  Network, 
  IndianRupee, 
  ShieldCheck, 
  Zap,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export const CommandCenterRibbon = ({
  compact = false,
  collapsible = false,
  className = '',
  style = {},
}) => {
  const { summary, earlyWarnings, setActiveScreen } = useMuleStore();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const saved = summary.estimated_amount_saved || 0;
  const illicitFlow = summary.estimated_amount_at_risk || 0;
  const savedSharePct = illicitFlow > 0 ? fmtPct((saved / illicitFlow) * 100, 0) : '0%';
  const interceptionCaption = `${savedSharePct} of illicit flow · early-freeze what-if`;

  const earlyWarningsCount = summary.early_warnings_count || earlyWarnings.length || 0;

  const handleNavigateToDayZero = () => {
    setActiveScreen('lab');
  };

  const handleNavigateToRings = () => {
    setActiveScreen('rings');
  };

  if (collapsible && isCollapsed) {
    return (
      <div 
        className="kpi-strip kpi-strip--collapsed"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '4px 16px',
          backgroundColor: 'var(--bg-1)',
          borderBottom: '1px solid var(--border)',
          ...style
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: 'var(--fs-xs)', color: 'var(--text-3)' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-2)' }}>FORENSIC KPI SUMMARY:</span>
          <span>{summary.total_accounts.toLocaleString()} Entities</span>
          <span style={{ color: 'var(--sev-critical)' }}>{summary.flagged_accounts} Flagged Mules</span>
          <span>{summary.rings_detected} Rings</span>
          <span>{fmtINRCompact(illicitFlow)} Illicit Vol</span>
          <span style={{ color: 'var(--sev-safe)' }}>Saved: {fmtINRCompact(saved)} ({savedSharePct})</span>
        </div>
        <button
          type="button"
          onClick={() => setIsCollapsed(false)}
          className="kpi-collapse-btn"
          title="Expand KPI Strip"
          aria-label="Expand KPI Strip"
        >
          <ChevronDown size={16} />
        </button>
      </div>
    );
  }

  return (
    <div 
      className={`kpi-strip ${compact ? 'kpi-strip--compact' : ''} ${className}`}
      style={{
        position: 'relative',
        ...style
      }}
    >
      <div className={`kpi-grid ${compact ? 'kpi-grid--compact' : ''}`}>
        {/* 1. Audited Entities */}
        <Kpi
          Icon={Users}
          tone="neutral"
          label="Audited Entities"
          value={summary.total_accounts.toLocaleString()}
          caption={`${summary.total_transactions.toLocaleString()} transactions`}
          compact={compact}
        />

        {/* 2. Flagged Mules */}
        <Kpi
          Icon={AlertTriangle}
          tone="danger"
          label="Flagged Mules"
          value={summary.flagged_accounts}
          caption={`${summary.critical_accounts} Critical / ${summary.flagged_accounts - summary.critical_accounts} Medium`}
          compact={compact}
        />

        {/* 3. Syndicate Rings */}
        <Kpi
          Icon={Network}
          tone="neutral"
          label="Syndicate Rings"
          value={summary.rings_detected}
          caption="Layering, Hubs, Cycles, Sybil"
          compact={compact}
          onClick={handleNavigateToRings}
          title="View Syndicate Fraud Rings Catalog"
        />

        {/* 4. Illicit Flow Volume */}
        <Kpi
          Icon={IndianRupee}
          tone="neutral"
          label="Illicit Flow Vol"
          value={fmtINRCompact(illicitFlow)}
          caption="Active in flagged accounts"
          compact={compact}
        />

        {/* 5. Estimated Amount Saved (Rule 8 Interception) */}
        <Kpi
          Icon={ShieldCheck}
          tone="success"
          label="Estimated amount saved"
          value={fmtINRCompact(saved)}
          caption={interceptionCaption}
          compact={compact}
        />

        {/* 6. Day-Zero Early Warnings (Amber warning button with chevron) */}
        <Kpi
          Icon={Zap}
          tone="warning"
          label="Day-Zero Warnings"
          value={`${earlyWarningsCount} Clusters`}
          caption="Flagged pre-transaction"
          compact={compact}
          onClick={handleNavigateToDayZero}
          showChevron={true}
          title="Inspect Day-Zero warnings in Forensic Lab"
        />
      </div>

      {collapsible && (
        <button
          type="button"
          onClick={() => setIsCollapsed(true)}
          className="kpi-collapse-btn"
          title="Collapse KPI Strip"
          aria-label="Collapse KPI Strip"
        >
          <ChevronUp size={16} />
        </button>
      )}
    </div>
  );
};

export default CommandCenterRibbon;
