import React from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { SeverityBadge } from './ui';
import { fmtINR, fmtPct, fmtMin } from '../lib/format';
import { 
  X, 
  Snowflake, 
  Clock, 
  TrendingDown, 
  AlertCircle, 
  ShieldCheck, 
  DollarSign,
  ArrowRight
} from 'lucide-react';

export const FreezeModal = () => {
  const { isFreezeModalOpen, freezeSimulationData, closeFreezeModal } = useMuleStore();

  if (!isFreezeModalOpen || !freezeSimulationData) {
    return null;
  }

  const d = freezeSimulationData;
  const curve = d.curve || [];
  const initialAmount = d.initial_amount || 100000;



  return (
    <div
      id="freeze-modal-backdrop"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 10, 20, 0.75)',
        backdropFilter: 'blur(6px)',
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div
        id="freeze-modal-container"
        style={{
          width: '680px',
          maxWidth: '100%',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Modal Header */}
        <div style={{
          padding: '16px 20px',
          backgroundColor: 'var(--bg-card)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Snowflake size={20} style={{ color: 'var(--brand)' }} />
            <div>
              <strong style={{ fontSize: '1rem', color: 'var(--text-1)' }}>
                Freeze Intervention Timeline Simulator
              </strong>
              <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-3)' }}>
                Capital recovery decay curve across delayed interdiction horizons
              </div>
            </div>
          </div>

          <button
            onClick={closeFreezeModal}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-3)',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Content */}
        <div style={{ padding: '20px', maxHeight: 'calc(80vh - 120px)', overflowY: 'auto' }}>
          
          {/* Simulation Header Banner */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: '12px',
            marginBottom: '20px'
          }}>
            <div style={{
              backgroundColor: 'var(--bg-2)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px'
            }}>
              <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-3)', display: 'block' }}>Source Target</span>
              <strong style={{ fontFamily: 'monospace', fontSize: 'var(--fs-xs)', color: 'var(--text-1)' }}>
                {d.source_account}
              </strong>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-2)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px'
            }}>
              <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-3)', display: 'block' }}>Total Stolen Principal</span>
              <strong style={{ fontSize: '0.95rem', color: 'var(--warning)' }}>
                {fmtINR(initialAmount)}
              </strong>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-2)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px'
            }}>
              <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-3)', display: 'block' }}>Max Preservation</span>
              <strong style={{ fontSize: '0.95rem', color: 'var(--success)' }}>
                {fmtINR(initialAmount)} ({fmtPct(100, 0)})
              </strong>
            </div>
          </div>

          {/* Recovery Curve Visual Bar Chart */}
          <div style={{
            backgroundColor: 'var(--bg-2)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            padding: '16px',
            marginBottom: '20px'
          }}>
            <span style={{ fontSize: 'var(--fs-xs)', fontWeight: 700, color: 'var(--text-1)', display: 'block', marginBottom: '14px' }}>
              RECOVERY VS INTERVENTION DELAY
            </span>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {curve.map((pt, idx) => {
                const pctSaved = Math.min(100, Math.max(0, (pt.recovered / initialAmount) * 100));
                const barColor = pctSaved > 70 ? 'var(--success)' : pctSaved > 30 ? 'var(--warning)' : 'var(--danger)';

                return (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: 'var(--fs-xs)' }}>
                    <span style={{ width: '80px', fontFamily: 'monospace', color: 'var(--text-3)' }}>
                      +{pt.freeze_delay_min} mins
                    </span>

                    <div style={{
                      flex: 1,
                      height: '20px',
                      backgroundColor: 'var(--bg-0)',
                      borderRadius: 'var(--radius-sm)',
                      overflow: 'hidden',
                      position: 'relative'
                    }}>
                      <div style={{
                        width: `${pctSaved}%`,
                        height: '100%',
                        backgroundColor: barColor,
                        borderRadius: 'var(--radius-sm)',
                        transition: 'width 0.4s ease'
                      }} />
                    </div>

                    <span style={{ width: '130px', textAlign: 'right', fontWeight: 700, color: barColor, fontFamily: 'monospace' }}>
                      {fmtINR(pt.recovered)} ({fmtPct(pctSaved, 0)})
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detailed Data Table */}
          <div style={{
            backgroundColor: 'var(--bg-2)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            overflow: 'hidden',
            marginBottom: '20px'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-xs)' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-0)', borderBottom: '1px solid var(--border)', color: 'var(--text-3)', textAlign: 'left' }}>
                  <th style={{ padding: '8px 12px' }}>Response Time</th>
                  <th style={{ padding: '8px 12px' }}>Amount Preserved</th>
                  <th style={{ padding: '8px 12px' }}>Escaped to Crypto/Cash</th>
                  <th style={{ padding: '8px 12px' }}>Operational Impact</th>
                </tr>
              </thead>
              <tbody>
                {curve.map((pt, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-2)' }}>
                    <td style={{ padding: '8px 12px', fontFamily: 'monospace', fontWeight: 600 }}>
                      {pt.freeze_delay_min === 0 ? 'T = 0 (Real-time)' : `+${pt.freeze_delay_min} minutes`}
                    </td>
                    <td style={{ padding: '8px 12px', color: 'var(--success)', fontWeight: 700 }}>
                      {fmtINR(pt.recovered)}
                    </td>
                    <td style={{ padding: '8px 12px', color: 'var(--danger)', fontWeight: 700 }}>
                      {fmtINR(pt.cashed_out)}
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      {pt.freeze_delay_min === 0 ? (
                        <SeverityBadge severity="SAFE" label={`${fmtPct(100, 0)} Capital Recovery`} size="sm" />
                      ) : pt.freeze_delay_min <= 15 ? (
                        <SeverityBadge severity="MEDIUM" label="Substantial Recovery" size="sm" />
                      ) : (
                        <SeverityBadge severity="CRITICAL" label="Critical Laundering Loss" size="sm" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mandatory Rule 8 Disclaimer Notice */}
          <div style={{
            padding: '12px 14px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--sev-medium-bg)',
            border: '1px solid var(--warning)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: 'var(--fs-xs)',
            color: 'var(--warning)'
          }}>
            <AlertCircle size={16} />
            <div>
              <strong style={{ display: 'block' }}>Mandatory Compliance Notice (Rule 8)</strong>
              <span>Estimated amount saved: {fmtINR(initialAmount * 0.75)}. Synthetic demonstration data. Not a real case.</span>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '12px 20px',
          backgroundColor: 'var(--bg-app)',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <button
            onClick={closeFreezeModal}
            style={{
              padding: '6px 16px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close Simulator
          </button>
        </div>
      </div>
    </div>
  );
};

export default FreezeModal;
