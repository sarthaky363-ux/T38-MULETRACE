import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { SeverityBadge, Chip } from './ui';
import { fmtINR } from '../lib/format';
import { X, Play, Snowflake, ShieldCheck } from 'lucide-react';

export interface EvidenceItem {
  label: string;
  value: number;
  unit: string;
  op: '>=' | '<=';
  threshold: number;
  max: number;
}

export interface DossierAccount {
  id: string;
  name?: string;
  severity: 'critical' | 'medium' | 'safe';
  score: number;
  confidence: string;
  ring?: string | null;
  hop?: number;
  hops?: number;
  justification: string;
  counterfactual: string;
  evidence: EvidenceItem[];
  raw?: any;
}

export function Dossier({
  acct: propAcct,
  onClose: propOnClose,
  onReplay: propOnReplay,
  onFreeze: propOnFreeze,
}: {
  acct?: DossierAccount | null;
  onClose?: () => void;
  onReplay?: () => void;
  onFreeze?: () => void;
}) {
  const store = useMuleStore();
  const [confirm, setConfirm] = useState(false);

  const selectedDetail = store.selectedAccountDetail;
  const selectedId = store.selectedAccountId;

  // Resolve acct from props or store
  const acct: DossierAccount | null = useMemo(() => {
    if (propAcct) return propAcct;
    if (!selectedId || !selectedDetail) return null;

    const d = selectedDetail;
    const severity = ((d.risk_band || 'medium').toLowerCase()) as 'critical' | 'medium' | 'safe';
    const score = Math.round(d.risk_score || 0);
    const confidence = (d.confidence || 'medium').toLowerCase();

    // Determine associated ring and hop positions
    let ringId = d.associated_ring?.ring_id || null;
    let hop = d.associated_ring?.hop;
    let hops = d.associated_ring?.hops;

    if (!ringId && store.rings) {
      const foundRing = store.rings.find((r: any) => (r.members || []).includes(selectedId));
      if (foundRing) {
        ringId = foundRing.ring_id || foundRing.id;
        const members = foundRing.members || [];
        const idx = members.indexOf(selectedId);
        if (idx >= 0) {
          hop = idx + 1;
          hops = members.length;
        }
      }
    } else if (ringId && (!hop || !hops) && store.rings) {
      const foundRing = store.rings.find((r: any) => r.ring_id === ringId || r.id === ringId);
      if (foundRing) {
        const members = foundRing.members || [];
        const idx = members.indexOf(selectedId);
        if (idx >= 0) {
          hop = idx + 1;
          hops = members.length;
        }
      }
    }

    // Extract structured evidence rows with threshold comparisons
    const evList: EvidenceItem[] = [];
    const hit = (d.hits && d.hits[0]) || null;
    const pat = hit?.pattern || (d.role === 'relay' ? 'passthrough' : 'general');
    const ev = hit?.evidence || {};

    if (pat === 'passthrough' || d.role === 'relay') {
      const fwdRatio = ev.forward_ratio !== undefined
        ? Math.round(ev.forward_ratio * 100)
        : Math.round(((d.total_outflow || 0) / (d.total_inflow || 1)) * 100);
      evList.push({
        label: 'Forwarding Drain Ratio',
        value: fwdRatio,
        unit: '%',
        op: '>=',
        threshold: 90,
        max: 100,
      });

      evList.push({
        label: 'Transfer Time Gap',
        value: ev.hop_gap_minutes !== undefined ? Number(ev.hop_gap_minutes) : 2.0,
        unit: ' min',
        op: '<=',
        threshold: 15,
        max: 30,
      });

      const residual = ev.post_balance !== undefined
        ? Number(ev.post_balance)
        : Math.max(0, Math.round((d.total_inflow || 0) - (d.total_outflow || 0)));
      evList.push({
        label: 'Post-Transfer Residual',
        value: residual,
        unit: ' ₹',
        op: '<=',
        threshold: 1000,
        max: 5000,
      });
    } else if (pat === 'fan_in_out' || d.role === 'hub') {
      evList.push({
        label: 'Aggregated Outflow Drain',
        value: Math.round((ev.forward_ratio || 0.96) * 100),
        unit: '%',
        op: '>=',
        threshold: 80,
        max: 100,
      });
      evList.push({
        label: 'Dispersion Time Window',
        value: Number(ev.window_minutes || 18.0),
        unit: ' min',
        op: '<=',
        threshold: 30,
        max: 60,
      });
      evList.push({
        label: 'Fan-In Contributing Accounts',
        value: Number(ev.inflow_count || 5),
        unit: ' accts',
        op: '>=',
        threshold: 3,
        max: 10,
      });
    } else if (pat === 'cycles' || pat === 'cycle') {
      evList.push({
        label: 'Cycle Loop Length',
        value: Number(ev.cycle_length || 4),
        unit: ' hops',
        op: '>=',
        threshold: 3,
        max: 8,
      });
      evList.push({
        label: 'Round-trip Velocity',
        value: Number(ev.cycle_duration_minutes || 38.0),
        unit: ' min',
        op: '<=',
        threshold: 60,
        max: 120,
      });
    } else if (pat === 'sybil') {
      evList.push({
        label: 'Shared Device Hardware Cluster',
        value: Number(ev.cluster_size || 4),
        unit: ' accts',
        op: '>=',
        threshold: 2,
        max: 8,
      });
      evList.push({
        label: 'Hardware Fingerprint Match',
        value: 100,
        unit: '%',
        op: '>=',
        threshold: 100,
        max: 100,
      });
    } else {
      evList.push({
        label: 'Turnover Velocity',
        value: Number((d.turnover_ratio || 1.0).toFixed(1)),
        unit: 'x',
        op: '>=',
        threshold: 2.0,
        max: 10,
      });
      evList.push({
        label: 'Composite Risk Score',
        value: score,
        unit: '/100',
        op: '>=',
        threshold: 70,
        max: 100,
      });
    }

    return {
      id: d.account_id,
      name: d.display_name,
      severity,
      score,
      confidence,
      ring: ringId,
      hop,
      hops,
      justification: d.primary_reason || 'Unusual rapid pass-through or layering activity detected.',
      counterfactual: d.counterfactual || 'Slowing transfer velocity and retaining legitimate account reserves clears this classification.',
      evidence: evList,
      raw: d,
    };
  }, [propAcct, selectedId, selectedDetail, store.rings]);

  const onClose = propOnClose ?? (() => store.selectAccount(null));
  const onReplay = propOnReplay ?? (() => {
    if (acct) store.triggerReplay(acct.id);
  });
  const onFreeze = propOnFreeze ?? (() => {
    if (acct) store.triggerFreezeSimulation(acct.id);
  });

  if (!acct) return null;

  return (
    <aside className="dossier dossier-panel" aria-label={'Dossier for ' + acct.id}>
      <header className="dossier-head">
        <div>
          <span className="label">Account dossier</span>
          <h2 className="mono">{acct.id}</h2>
          {acct.ring && (
            <Chip variant="brand">
              {acct.ring}
              {acct.hop && acct.hops ? ` · hop ${acct.hop}/${acct.hops}` : ''}
            </Chip>
          )}
        </div>
        <button className="icon-btn" aria-label="Close dossier" onClick={onClose}>
          <X size={16} />
        </button>
      </header>

      <section className={'score-card sev-' + acct.severity}>
        <div className="score-main">
          {(() => {
            const scoreColor = acct.severity === 'critical' ? 'var(--danger)' : acct.severity === 'safe' ? 'var(--brand)' : 'var(--warn)';
            const scorePct = Math.min(100, Math.max(0, acct.score));
            return (
              <div 
                className="score mono"
                style={{
                  background: `radial-gradient(circle at center, #06110d 54%, transparent 56%), conic-gradient(${scoreColor} 0% ${scorePct}%, rgba(255, 255, 255, 0.08) ${scorePct}% 100%)`
                }}
              >
                {acct.score}<small>/100</small>
              </div>
            );
          })()}
          <SeverityBadge severity={acct.severity} />
        </div>
        <span 
          className="muted"
          title={acct.severity === 'safe' || acct.confidence === 'low' ? "Confidence in this assessment is low because little activity data exists." : undefined}
          aria-label={acct.severity === 'safe' || acct.confidence === 'low' ? "Confidence in this assessment is low because little activity data exists." : undefined}
        >
          Confidence: <strong>{acct.confidence}</strong>
        </span>
        <div className="score-bar" aria-hidden="true">
          <span style={{ width: acct.score + '%' }} />
        </div>
      </section>

      <section className="dossier-section">
        <h3 className="label">{acct.severity === 'safe' ? "Why it's safe" : "Why it was flagged"}</h3>
        <p className="justification">{acct.justification}</p>
        <ul className="evidence">
          {acct.evidence.map((e) => (
            <EvidenceRow key={e.label} e={e} />
          ))}
        </ul>
      </section>

      <section className="counterfactual">
        <h3>What would clear this account</h3>
        <p>{acct.counterfactual}</p>
      </section>

      <footer className="dossier-actions">
        <button type="button" className="btn btn--primary" onClick={onReplay}>
          <Play size={16} />Replay flows
        </button>
        <button type="button" className="btn btn--danger-outline" onClick={() => setConfirm(true)}>
          <Snowflake size={16} />Simulate freeze
        </button>
      </footer>

      {confirm && (
        <ConfirmFreeze
          acct={acct}
          onCancel={() => setConfirm(false)}
          onConfirm={() => {
            onFreeze();
            setConfirm(false);
          }}
        />
      )}
    </aside>
  );
}

// evidence: { label, value, unit, op: ">=" | "<=", threshold, max }
function EvidenceRow({ e }: { e: EvidenceItem }) {
  const met = e.op === '>=' ? e.value >= e.threshold : e.value <= e.threshold;
  const fill = Math.min(100, Math.max(0, (e.value / (e.max || 1)) * 100));
  const rawTick = (e.threshold / (e.max || 1)) * 100;
  const tick = Math.min(100, Math.max(0, rawTick));

  return (
    <li className="ev">
      <span className="ev-label">{e.label}</span>
      <span className={'ev-flag ' + (met ? 'is-met' : 'not-met')}>
        {met ? 'Rule met' : 'Not met'}
      </span>
      <div className="ev-meta">
        <span className="mono ev-val">
          {e.value}{e.unit}
        </span>
        <span className="muted ev-rule">
          rule: {e.op} {e.threshold}{e.unit}
        </span>
      </div>
      <div className="ev-track">
        <span className={'ev-fill ' + (met ? 'ev-fill--met' : 'ev-fill--safe')} style={{ width: fill + '%' }} />
        <span 
          className="ev-tick" 
          style={{ left: `calc(${tick}% - 1px)` }} 
          title={'Threshold: ' + e.threshold + e.unit} 
        />
      </div>
    </li>
  );
}

function ConfirmFreeze({
  acct,
  onCancel,
  onConfirm,
}: {
  acct: DossierAccount;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);

  return (
    <dialog ref={ref} className="modal" onCancel={onCancel}>
      <h3>Simulate freezing {acct.id}?</h3>
      <p>This runs a what-if on the demo dataset. No real account is touched.</p>
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onCancel}>
          Cancel
        </button>
        <button type="button" className="btn btn--danger" autoFocus onClick={onConfirm}>
          Run simulation
        </button>
      </div>
    </dialog>
  );
}

// Export for InspectorDrawer backwards compatibility
export const InspectorDrawer = Dossier;
export default Dossier;
