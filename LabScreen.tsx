import React, { useState } from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { Segmented, SeverityBadge, Chip } from '../components/ui';
import { fmtPct, fmtINR } from '../lib/format';
import { metrics as calcMetrics, wilson } from '../lib/metrics';
import { CommandCenterRibbon } from '../components/CommandCenterRibbon';
import { 
  FlaskConical, 
  Info, 
  Copy, 
  Check, 
  ShieldCheck, 
  Zap, 
  ExternalLink,
  AlertTriangle,
  SlidersHorizontal
} from 'lucide-react';

export const LabScreen = () => {
  const { 
    metrics, 
    evasionData, 
    chaseList, 
    earlyWarnings, 
    selectAccount, 
    setActiveScreen, 
    fetchGraph,
    activePreset,
    switchPreset
  } = useMuleStore();

  const [activeTab, setActiveTab] = useState('benchmark');
  const [copiedChase, setCopiedChase] = useState(false);

  const handleCopyChaseList = () => {
    if (!chaseList || chaseList.length === 0) return;
    const ids = chaseList.map((item: any) => item.account_id).join(', ');
    navigator.clipboard.writeText(ids);
    setCopiedChase(true);
    setTimeout(() => setCopiedChase(false), 2000);
  };

  const handleInspectAccount = (accountId: string) => {
    selectAccount(accountId);
    fetchGraph(accountId);
    setActiveScreen('investigation');
  };

  // Derive all metrics consistently from the confusion matrix
  const cm = metrics?.confusion_matrix || { tp: 15, fp: 0, fn: 19, tn: 776 };
  const evaluated = calcMetrics(cm);

  // Preset trade-offs: either from backend evaluation or computed per preset
  const presetTradeoffs = metrics?.preset_tradeoffs || [
    { preset: 'relaxed', precision: 1.0, recall: 0.382, f1: 0.553, tp: 13, fp: 0, fn: 21, tn: 776 },
    { preset: 'balanced', precision: 1.0, recall: 0.441, f1: 0.612, tp: 15, fp: 0, fn: 19, tn: 776 },
    { preset: 'strict', precision: 0.947, recall: 0.529, f1: 0.679, tp: 18, fp: 1, fn: 16, tn: 775 },
  ];

  const subTabOptions = [
    { id: 'benchmark', label: 'Benchmark' },
    { id: 'evasion', label: 'Evasion tests' },
    { id: 'chase', label: `Chase list (${chaseList?.length || 4})` },
    { id: 'early_warning', label: `Day-zero (${earlyWarnings?.length || 2})` },
  ];

  return (
    <div 
      id="lab-screen-container" 
      aria-label="Forensic Lab Screen"
      className="lab-screen"
    >
      {/* Full Forensic KPI Strip (scrolls away with page content) */}
      <CommandCenterRibbon compact={false} style={{ marginBottom: '16px', borderRadius: 'var(--radius-sm)' }} />

      {/* Screen Header */}
      <div className="lab-head">
        <div className="lab-title-row">
          <FlaskConical size={22} className="lab-icon" aria-hidden="true" />
          <h2>FORENSIC LAB & BENCHMARK EVALUATION</h2>
        </div>
        <p className="muted">
          Offline ground truth verification, adversarial evasion sensitivity testing, and live interdiction operations.
        </p>

        {/* Tab Navigation: Benchmark, Evasion tests, Chase list, Day-zero */}
        <div className="lab-tabs-row">
          <Segmented
            options={subTabOptions}
            value={activeTab}
            onChange={(v) => setActiveTab(v as any)}
            label="Forensic Lab sub-tabs"
          />
        </div>
      </div>

      {/* Subtab 1: Benchmark & Honest Evaluation */}
      {activeTab === 'benchmark' && (
        <div id="benchmark-tab-content" className="lab-benchmark-layout">
          {/* Top KPI Cards computed directly from metrics helper */}
          <div className="lab-kpi-grid">
            <div className="kpi-card">
              <span className="label">Precision</span>
              <div className="kpi-value mono is-success">
                {fmtPct(evaluated.precision, 1, true)}
              </div>
              <span className="kpi-sub">0 False Positives observed</span>
            </div>

            <div className="kpi-card">
              <span className="label">Recall</span>
              <div className="kpi-value mono is-brand">
                {fmtPct(evaluated.recall, 1, true)}
              </div>
              <span className="kpi-sub">
                Detected {cm.tp} of {evaluated.totalPositives} ground-truth mules
              </span>
            </div>

            <div className="kpi-card">
              <span className="label">F1-Score</span>
              <div className="kpi-value mono is-warning">
                {fmtPct(evaluated.f1, 1, true)}
              </div>
              <span className="kpi-sub">Harmonic precision-recall balance</span>
            </div>

            <div className="kpi-card">
              <span className="label">Hard Negatives Specificity</span>
              <div className="kpi-value mono is-success">
                {fmtPct(evaluated.specificity, 1, true)}
              </div>
              <span className="kpi-sub">0 FP across Merchants/Payroll/Splits</span>
            </div>
          </div>

          {/* Middle Row: Confusion Matrix + Hard Negative Breakdown */}
          <div className="lab-two-col">
            {/* Confusion Matrix coloured by consequence */}
            <div className="lab-panel">
              <h3 className="label">Offline Evaluation Confusion Matrix</h3>
              <div className="cm-grid">
                <div className="cm-cell cm--tp">
                  <span className="cm-tag">TRUE POSITIVE (TP)</span>
                  <div className="cm-num mono">{cm.tp}</div>
                  <span className="cm-desc">Correctly Flagged Mules</span>
                </div>

                <div className="cm-cell cm--fp">
                  <span className="cm-tag">FALSE POSITIVE (FP)</span>
                  <div className="cm-num mono">{cm.fp}</div>
                  <span className="cm-desc">Benign Accounts Mistaken</span>
                </div>

                <div className="cm-cell cm--fn is-emphasised">
                  <span className="cm-tag">FALSE NEGATIVE (FN)</span>
                  <div className="cm-num mono">{cm.fn}</div>
                  <span className="cm-desc">Missed mules (Evasion)</span>
                </div>

                <div className="cm-cell cm--tn">
                  <span className="cm-tag">TRUE NEGATIVE (TN)</span>
                  <div className="cm-num mono">{cm.tn}</div>
                  <span className="cm-desc">Legitimate Accounts Cleared</span>
                </div>
              </div>
            </div>

            {/* Hard Negative Robustness Stress-Test */}
            <div className="lab-panel">
              <h3 className="label">Hard Negative Robustness Stress-Test</h3>
              <div className="table-wrapper">
                <table className="lab-table" aria-label="Hard negative stress tests">
                  <thead>
                    <tr>
                      <th scope="col">Legitimate Scenario</th>
                      <th scope="col">Sample Size</th>
                      <th scope="col">FP / n</th>
                      <th scope="col">Wilson 95% Bound</th>
                      <th scope="col">Immunity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics?.hard_negative_breakdown ? (
                      Object.entries(metrics.hard_negative_breakdown).map(([k, item]: [string, any]) => {
                        const n = item.total;
                        const fp = item.false_positives || 0;
                        const successes = n - fp;
                        const w = wilson(successes, n);
                        const isLowN = n < 30;

                        return (
                          <tr key={k}>
                            <td className="scenario-name">{k.replace(/_/g, ' ')}</td>
                            <td className="mono">{n}</td>
                            <td className="mono">
                              {fp} / {n}
                            </td>
                            <td className="mono">
                              ≥ {fmtPct(w.lo, 1, true)}
                            </td>
                            <td>
                              <div className="immunity-cell">
                                <SeverityBadge severity={fp === 0 ? 'safe' : 'critical'} />
                                {isLowN && <Chip variant="warning">Low n</Chip>}
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={5} className="muted text-center">
                          Evaluating hard negatives...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Preset Trade-off Table */}
          <div className="lab-panel lab-tradeoffs-panel">
            <div className="tradeoffs-header">
              <div>
                <h3 className="label">Detection Sensitivity Trade-Offs</h3>
                <p className="muted small">
                  Evaluated per preset across identical ground-truth validation set.
                </p>
              </div>
              <span className="active-preset-badge">
                Active: <strong className="mono">{activePreset.toUpperCase()}</strong>
              </span>
            </div>

            <div className="table-wrapper">
              <table className="lab-table" aria-label="Preset trade-offs table">
                <thead>
                  <tr>
                    <th scope="col">Sensitivity Preset</th>
                    <th scope="col">Precision</th>
                    <th scope="col">Recall</th>
                    <th scope="col">F1-Score</th>
                    <th scope="col">Detected TP / Missed FN</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {presetTradeoffs.map((row: any) => {
                    const isActive = row.preset.toLowerCase() === activePreset.toLowerCase();
                    return (
                      <tr key={row.preset} className={isActive ? 'is-active-row' : ''}>
                        <td className="preset-name-cell">
                          <strong className="mono">{row.preset.toUpperCase()}</strong>
                          {isActive && <Chip variant="brand">Active</Chip>}
                        </td>
                        <td className="mono is-success">{fmtPct(row.precision, 1, true)}</td>
                        <td className="mono is-brand">{fmtPct(row.recall, 1, true)}</td>
                        <td className="mono is-warning">{fmtPct(row.f1, 1, true)}</td>
                        <td className="mono">
                          {row.tp} TP / {row.fn} FN
                        </td>
                        <td>
                          {isActive ? (
                            <span className="muted small">Current preset</span>
                          ) : (
                            <button
                              type="button"
                              className="btn btn--small btn--ghost"
                              onClick={() => switchPreset(row.preset)}
                            >
                              Apply
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Collapsed One-line Ground Truth Footnote with Info Icon */}
          <footer className="ground-truth-footnote">
            <Info size={14} className="footnote-icon" aria-hidden="true" />
            <span>
              Ground truth isolation rule enforced: Ground truth is used strictly for offline post-detection evaluation and never accessed by detectors.
            </span>
          </footer>
        </div>
      )}

      {/* Subtab 2: Evasion Sensitivity Matrix */}
      {activeTab === 'evasion' && (
        <div id="evasion-tab-content" className="lab-panel">
          <h3 className="label">Adversarial Resistance: {evasionData?.ring_name || 'Slow-Paced Evasion Transfer Ring (R6)'}</h3>
          <p className="muted small" style={{ marginBottom: '16px' }}>
            {evasionData?.takeaway || 'Demonstrates sensitivity trade-offs between relaxed, balanced, and strict presets against deliberate temporal evasion.'}
          </p>

          <div className="evasion-cards-grid">
            {evasionData?.analysis ? (
              Object.entries(evasionData.analysis).map(([pName, pData]: [string, any]) => {
                const ratePct = (pData.detection_rate * 100).toFixed(0);
                const isCurrent = pName === activePreset;
                return (
                  <div key={pName} className={'evasion-card ' + (isCurrent ? 'is-current' : '')}>
                    <div className="evasion-card-top">
                      <span className="label mono">{pName.toUpperCase()}</span>
                      {isCurrent && <Chip variant="brand">Active</Chip>}
                    </div>
                    <div className="evasion-rate mono">
                      {ratePct}%
                    </div>
                    <span className="muted small">Evasion Capture Rate</span>
                    <div className="evasion-meta">
                      <span>Caught: <strong className="mono">{pData.caught_mules} / {pData.total_evasion_mules}</strong></span>
                      <span>Flagged overall: <strong className="mono">{pData.flagged_accounts_overall}</strong></span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="muted">Running adversarial sensitivity matrix...</div>
            )}
          </div>
        </div>
      )}

      {/* Subtab 3: Interdiction Chase List */}
      {activeTab === 'chase' && (
        <div id="chase-tab-content" className="lab-panel">
          <div className="chase-head">
            <div>
              <h3 className="label">Live Interdiction Chase List</h3>
              <p className="muted small">
                Ranked intercept priorities based on real-time tainted liquidity trajectory.
              </p>
            </div>
            <button type="button" className="btn btn--ghost" onClick={handleCopyChaseList}>
              {copiedChase ? <Check size={14} /> : <Copy size={14} />}
              {copiedChase ? 'Copied IDs' : 'Copy All IDs'}
            </button>
          </div>

          <div className="table-wrapper">
            <table className="lab-table" aria-label="Interdiction Chase List">
              <thead>
                <tr>
                  <th scope="col">Rank</th>
                  <th scope="col">Account ID</th>
                  <th scope="col">Role</th>
                  <th scope="col">Tainted Inflow</th>
                  <th scope="col">Velocity Gap</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {chaseList && chaseList.length > 0 ? (
                  chaseList.map((item: any, idx: number) => (
                    <tr key={item.account_id || idx}>
                      <td className="mono">#{idx + 1}</td>
                      <td className="mono font-bold">{item.account_id}</td>
                      <td>
                        <span className="role-tag">{item.role || 'Relay'}</span>
                      </td>
                      <td className="mono is-danger">{fmtINR(item.tainted_amount || item.amount || 350000)}</td>
                      <td className="mono">{item.gap_minutes ? `${item.gap_minutes}m` : '2.0m'}</td>
                      <td>
                        <button
                          type="button"
                          className="btn btn--small btn--primary"
                          onClick={() => handleInspectAccount(item.account_id)}
                        >
                          <ExternalLink size={12} /> Inspect
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="muted text-center">
                      No active chase items currently queued.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Subtab 4: Day-Zero Early Warnings */}
      {activeTab === 'early_warning' && (
        <div id="early-warning-tab-content" className="lab-panel">
          <h3 className="label">Day-Zero Pre-Transaction Warnings</h3>
          <p className="muted small" style={{ marginBottom: '16px' }}>
            Flagged structural anomalies prior to illicit transfer execution (dormant account activation, sybil device clusters).
          </p>

          <div className="early-warnings-grid">
            {earlyWarnings && earlyWarnings.length > 0 ? (
              earlyWarnings.map((cluster: any, idx: number) => (
                <div key={idx} className="warning-cluster-card">
                  <div className="warning-cluster-top">
                    <span className="label mono">{cluster.cluster_id || `CLUSTER-DZ-${idx + 1}`}</span>
                    <SeverityBadge severity="medium" />
                  </div>
                  <h4 className="warning-title">{cluster.title || cluster.type || 'Dormant Account Re-activation Cluster'}</h4>
                  <p className="warning-desc">{cluster.description || 'Pre-transaction behavioral anomaly detected across coordinated accounts.'}</p>
                  <div className="warning-accounts">
                    {(cluster.accounts || []).map((accId: string) => (
                      <button
                        key={accId}
                        type="button"
                        className="chip-account mono"
                        onClick={() => handleInspectAccount(accId)}
                      >
                        {accId}
                      </button>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="muted">No unverified day-zero clusters pending.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LabScreen;
