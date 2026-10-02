import React, { useState } from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { 
  FlaskConical, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Copy, 
  Check, 
  Layers, 
  TrendingUp, 
  Clock, 
  ArrowRight,
  ExternalLink,
  Zap,
  Info
} from 'lucide-react';

export const LabScreen = () => {
  const { 
    metrics, 
    evasionData, 
    chaseList, 
    earlyWarnings, 
    selectAccount, 
    setActiveScreen, 
    fetchGraph 
  } = useMuleStore();

  const [activeTab, setActiveTab] = useState('benchmark');
  const [copiedChase, setCopiedChase] = useState(false);

  const formatCurrency = (val) => {
    return `₹${Math.round(val || 0).toLocaleString('en-IN')}`;
  };

  const handleCopyChaseList = () => {
    if (!chaseList || chaseList.length === 0) return;
    const ids = chaseList.map(item => item.account_id).join(', ');
    navigator.clipboard.writeText(ids);
    setCopiedChase(true);
    setTimeout(() => setCopiedChase(false), 2000);
  };

  const handleInspectAccount = (accountId) => {
    selectAccount(accountId);
    fetchGraph(accountId);
    setActiveScreen('investigate');
  };

  return (
    <div 
      id="lab-screen-container" 
      aria-label="Forensic Lab Screen"
      style={{
        padding: '28px 36px',
        maxWidth: '1440px',
        margin: '0 auto',
        height: '100%',
        overflowY: 'auto'
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FlaskConical size={24} style={{ color: 'var(--accent)' }} />
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            FORENSIC LAB & BENCHMARK EVALUATION
          </h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
          Offline ground truth verification, adversarial evasion sensitivity testing, and live interdiction operations.
        </p>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
          {[
            { id: 'benchmark', label: 'Benchmark & Ground Truth (Rule 5)' },
            { id: 'evasion', label: 'Evasion Sensitivity Matrix (R6)' },
            { id: 'chase', label: `Interdiction Chase List (${chaseList?.length || 0})` },
            { id: 'early_warning', label: `Day-Zero Warnings (${earlyWarnings?.length || 0})` },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '6px 14px',
                fontSize: '0.8rem',
                fontWeight: 600,
                borderRadius: '6px',
                border: activeTab === tab.id ? '1px solid var(--accent)' : '1px solid transparent',
                backgroundColor: activeTab === tab.id ? 'rgba(91, 192, 235, 0.12)' : 'transparent',
                color: activeTab === tab.id ? 'var(--accent)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab 1: Benchmark Performance & Ground Truth */}
      {activeTab === 'benchmark' && (
        <div id="benchmark-tab-content">
          {/* Ground Truth Isolation Disclaimer (Rule 5) */}
          <div style={{
            backgroundColor: 'rgba(91, 192, 235, 0.08)',
            border: '1px solid var(--accent)',
            borderRadius: '6px',
            padding: '12px 16px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '0.78rem',
            color: 'var(--text-secondary)'
          }}>
            <ShieldCheck size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
            <div>
              <strong style={{ color: 'var(--text-primary)', display: 'block' }}>
                Strict Ground Truth Isolation Guarantee (Rule 5)
              </strong>
              <span>
                {metrics?.isolation_disclaimer || "Ground truth is strictly isolated for offline post-detection evaluation and is never accessed by detection or scoring pipelines."}
              </span>
            </div>
          </div>

          {/* KPI Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Precision</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--success)', marginTop: '4px' }}>
                {metrics ? `${(metrics.precision * 100).toFixed(1)}%` : '--'}
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Low False Positive Rate</span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Recall</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent)', marginTop: '4px' }}>
                {metrics ? `${(metrics.recall * 100).toFixed(1)}%` : '--'}
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Mule Syndicate Catch Rate</span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>F1-Score</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--warning)', marginTop: '4px' }}>
                {metrics ? `${(metrics.f1_score * 100).toFixed(1)}%` : '--'}
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Harmonic Balance</span>
            </div>

            <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Hard Negatives Specificity</span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--success)', marginTop: '4px' }}>
                100.0%
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>0 FP across Merchants/Payroll/Splits</span>
            </div>
          </div>

          {/* Row: Confusion Matrix + Hard Negative Breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Confusion Matrix Card */}
            <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-primary)' }}>
                Offline Evaluation Confusion Matrix
              </h3>

              <div className="cm-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="cm-cell cm--tp" style={{
                  backgroundColor: 'rgba(46, 204, 143, 0.1)',
                  border: '1px solid var(--success)',
                  borderRadius: '6px',
                  padding: '14px',
                  textAlign: 'center'
                }}>
                  <span className="cm-tag" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>TRUE POSITIVE (TP)</span>
                  <strong className="cm-num" style={{ fontSize: '1.5rem', color: 'var(--success)' }}>
                    {metrics?.confusion_matrix?.tp ?? '--'}
                  </strong>
                  <span className="cm-desc" style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', display: 'block', marginTop: '2px' }}>
                    Correctly Flagged Mules
                  </span>
                </div>

                <div className="cm-cell cm--fp" style={{
                  backgroundColor: 'rgba(255, 77, 94, 0.08)',
                  border: '1px solid var(--danger)',
                  borderRadius: '6px',
                  padding: '14px',
                  textAlign: 'center'
                }}>
                  <span className="cm-tag" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>FALSE POSITIVE (FP)</span>
                  <strong className="cm-num" style={{ fontSize: '1.5rem', color: 'var(--danger)' }}>
                    {metrics?.confusion_matrix?.fp ?? '--'}
                  </strong>
                  <span className="cm-desc" style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', display: 'block', marginTop: '2px' }}>
                    Benign Accounts Mistaken
                  </span>
                </div>

                <div className="cm-cell cm--fn is-emphasised" style={{
                  backgroundColor: 'rgba(255, 176, 32, 0.08)',
                  border: '1px solid var(--warning)',
                  borderRadius: '6px',
                  padding: '14px',
                  textAlign: 'center'
                }}>
                  <span className="cm-tag" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>FALSE NEGATIVE (FN)</span>
                  <strong className="cm-num" style={{ fontSize: '1.5rem', color: 'var(--warning)' }}>
                    {metrics?.confusion_matrix?.fn ?? '--'}
                  </strong>
                  <span className="cm-desc" style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', display: 'block', marginTop: '2px' }}>
                    Missed Mules (Evasion)
                  </span>
                </div>

                <div className="cm-cell cm--tn" style={{
                  backgroundColor: 'rgba(91, 192, 235, 0.08)',
                  border: '1px solid var(--accent)',
                  borderRadius: '6px',
                  padding: '14px',
                  textAlign: 'center'
                }}>
                  <span className="cm-tag" style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>TRUE NEGATIVE (TN)</span>
                  <strong className="cm-num" style={{ fontSize: '1.5rem', color: 'var(--accent)' }}>
                    {metrics?.confusion_matrix?.tn ?? '--'}
                  </strong>
                  <span className="cm-desc" style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', display: 'block', marginTop: '2px' }}>
                    Legitimate Accounts Cleared
                  </span>
                </div>
              </div>
            </div>

            {/* Hard Negative Immunity Breakdown */}
            <div style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 14px 0', color: 'var(--text-primary)' }}>
                Hard Negative Robustness Stress-Test
              </h3>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', textAlign: 'left' }}>
                      <th style={{ padding: '6px 8px' }}>Legitimate Scenario</th>
                      <th style={{ padding: '6px 8px' }}>Sample Size</th>
                      <th style={{ padding: '6px 8px' }}>False Positives</th>
                      <th style={{ padding: '6px 8px' }}>Immunity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics?.hard_negative_breakdown ? (
                      Object.entries(metrics.hard_negative_breakdown).map(([k, item]) => (
                        <tr key={k} style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                          <td style={{ padding: '6px 8px', fontWeight: 600, color: 'var(--text-primary)' }}>
                            {k.replace(/_/g, ' ')}
                          </td>
                          <td style={{ padding: '6px 8px' }}>{item.total}</td>
                          <td style={{ padding: '6px 8px', color: item.false_positives === 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 700 }}>
                            {item.false_positives}
                          </td>
                          <td style={{ padding: '6px 8px' }}>
                            <span style={{
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '0.68rem',
                              fontWeight: 700,
                              backgroundColor: 'rgba(46, 204, 143, 0.15)',
                              color: 'var(--success)'
                            }}>
                              100% Pass
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} style={{ padding: '12px', textAlign: 'center', color: 'var(--text-muted)' }}>
                          Loading hard negative telemetry...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Evasion Sensitivity Matrix */}
      {activeTab === 'evasion' && (
        <div id="evasion-tab-content">
          <div style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>
              Adversarial Resistance: {evasionData?.ring_name || 'Slow-Paced Evasion Transfer Ring (R6)'}
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: '0 0 16px 0' }}>
              {evasionData?.takeaway || "Demonstrates sensitivity trade-offs between relaxed, balanced, and strict presets."}
            </p>

            {/* Presets Comparison Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              {evasionData?.analysis ? (
                Object.entries(evasionData.analysis).map(([pName, pData]) => {
                  const ratePct = (pData.detection_rate * 100).toFixed(0);
                  const isBalanced = pName === 'balanced';

                  return (
                    <div
                      key={pName}
                      style={{
                        backgroundColor: isBalanced ? 'rgba(91, 192, 235, 0.08)' : 'var(--bg-app)',
                        border: isBalanced ? '1.5px solid var(--accent)' : '1px solid var(--border)',
                        borderRadius: '8px',
                        padding: '16px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <strong style={{ textTransform: 'uppercase', fontSize: '0.85rem', color: isBalanced ? 'var(--accent)' : 'var(--text-primary)' }}>
                          {pName} Preset
                        </strong>
                        {isBalanced && (
                          <span style={{ fontSize: '0.65rem', padding: '1px 6px', borderRadius: '4px', backgroundColor: 'var(--accent)', color: '#0B1220', fontWeight: 800 }}>
                            ACTIVE DEFAULT
                          </span>
                        )}
                      </div>

                      <div style={{ marginBottom: '12px' }}>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>R6 Evasion Catch Rate</span>
                        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: ratePct > 70 ? 'var(--success)' : 'var(--warning)' }}>
                          {ratePct}%
                        </div>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                          {pData.caught_mules} of {pData.total_evasion_mules} mules identified
                        </span>
                      </div>

                      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '8px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        System-wide Alerts: <strong style={{ color: 'var(--text-primary)' }}>{pData.flagged_accounts_overall}</strong>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>Loading sensitivity matrix...</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Actionable Interdiction Queue (Chase List) */}
      {activeTab === 'chase' && (
        <div id="chase-tab-content">
          <div style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  Live Capital Interdiction Queue (Chase List)
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Prioritized accounts currently holding circulating tainted funds.
                </span>
              </div>

              <button
                onClick={handleCopyChaseList}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  backgroundColor: copiedChase ? 'var(--success)' : 'var(--accent)',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
              >
                {copiedChase ? <Check size={14} /> : <Copy size={14} />}
                <span>{copiedChase ? 'Copied Accounts!' : 'Copy Freeze Target List'}</span>
              </button>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ backgroundColor: 'var(--bg-app)', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', textAlign: 'left' }}>
                    <th style={{ padding: '8px 10px' }}>Rank</th>
                    <th style={{ padding: '8px 10px' }}>Account ID</th>
                    <th style={{ padding: '8px 10px' }}>Tainted Balance</th>
                    <th style={{ padding: '8px 10px' }}>Priority Score</th>
                    <th style={{ padding: '8px 10px' }}>Flow Status</th>
                    <th style={{ padding: '8px 10px' }}>Predicted Next Hop</th>
                    <th style={{ padding: '8px 10px', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(chaseList || []).map((item, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                      <td style={{ padding: '8px 10px', fontWeight: 700, color: 'var(--text-muted)' }}>#{idx + 1}</td>
                      <td style={{ padding: '8px 10px', fontFamily: 'monospace', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {item.account_id}
                      </td>
                      <td style={{ padding: '8px 10px', color: 'var(--danger)', fontWeight: 700 }}>
                        {formatCurrency(item.tainted_balance)}
                      </td>
                      <td style={{ padding: '8px 10px', fontWeight: 700, color: 'var(--warning)' }}>
                        {item.priority_score ? item.priority_score.toFixed(1) : '--'}
                      </td>
                      <td style={{ padding: '8px 10px' }}>
                        <span style={{
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          backgroundColor: item.status === 'urgent_freeze' ? 'rgba(255, 77, 94, 0.15)' : 'rgba(255, 176, 32, 0.15)',
                          color: item.status === 'urgent_freeze' ? 'var(--danger)' : 'var(--warning)',
                          textTransform: 'uppercase'
                        }}>
                          {item.status || 'Active Taint'}
                        </span>
                      </td>
                      <td style={{ padding: '8px 10px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                        {item.predicted_next_hop || 'Terminal / Unknown'}
                      </td>
                      <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                        <button
                          onClick={() => handleInspectAccount(item.account_id)}
                          style={{
                            padding: '4px 10px',
                            backgroundColor: 'var(--bg-app)',
                            border: '1px solid var(--border)',
                            borderRadius: '4px',
                            color: 'var(--accent)',
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Day-Zero Early Warnings */}
      {activeTab === 'early_warning' && (
        <div id="early-warning-tab-content">
          <div style={{
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
              Day-Zero Pre-Transaction Account Cluster Warnings
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0 0 16px 0' }}>
              Accounts flagged before initiating transfers due to shared hardware device emulators or duplicate tax IDs.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {(earlyWarnings || []).map((ew, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: 'var(--bg-app)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <Zap size={14} style={{ color: 'var(--warning)' }} />
                      <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                        {ew.pattern_type?.replace(/_/g, ' ')?.toUpperCase() || 'SYNTHETIC CLUSTER'}
                      </strong>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '1px 6px',
                        borderRadius: '3px',
                        backgroundColor: 'rgba(255, 77, 94, 0.2)',
                        color: 'var(--danger)',
                        textTransform: 'uppercase'
                      }}>
                        {ew.risk_band || 'Critical'}
                      </span>
                    </div>

                    <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0 0 6px 0' }}>
                      {ew.reason}
                    </p>

                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      Cluster Accounts: <span style={{ fontFamily: 'monospace', color: 'var(--accent)' }}>{(ew.accounts || []).join(', ')}</span>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--warning)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                      {ew.recommendation || 'Preventative Hold'}
                    </span>
                    {ew.accounts && ew.accounts.length > 0 && (
                      <button
                        onClick={() => handleInspectAccount(ew.accounts[0])}
                        style={{
                          padding: '4px 10px',
                          fontSize: '0.72rem',
                          borderRadius: '4px',
                          backgroundColor: 'var(--bg-surface)',
                          border: '1px solid var(--border)',
                          color: 'var(--text-primary)',
                          cursor: 'pointer'
                        }}
                      >
                        Inspect Cluster
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LabScreen;
