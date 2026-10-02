import React from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { fmtINR, fmtPct } from '../lib/format';
import { 
  X, 
  Printer, 
  FileText, 
  ShieldAlert, 
  CheckCircle, 
  AlertTriangle,
  Building,
  Calendar,
  Layers
} from 'lucide-react';

export const SARDossierModal = () => {
  const { isDossierModalOpen, currentDossier, closeDossierModal } = useMuleStore();

  if (!isDossierModalOpen || !currentDossier) {
    return null;
  }

  const d = currentDossier;

  const handlePrint = () => {
    window.print();
  };



  return (
    <div
      id="sar-dossier-modal-backdrop"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 10, 20, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div
        id="sar-dossier-container"
        style={{
          width: '840px',
          maxWidth: '100%',
          maxHeight: '90vh',
          backgroundColor: '#ffffff',
          color: '#0F172A',
          borderRadius: '8px',
          boxShadow: '0 24px 64px rgba(0,0,0,0.7)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Top Control Bar (Non-printable) */}
        <div 
          className="no-print"
          style={{
            padding: '12px 20px',
            backgroundColor: '#1E293B',
            color: '#F8FAFC',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} style={{ color: '#5BC0EB' }} />
            <strong style={{ fontSize: '0.9rem' }}>Regulatory SAR Dossier Viewer</strong>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={handlePrint}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--brand)',
                border: 'none',
                color: 'var(--bg-0)',
                fontWeight: 700,
                fontSize: 'var(--fs-xs)',
                cursor: 'pointer'
              }}
            >
              <Printer size={14} />
              Print / Save PDF
            </button>

            <button
              onClick={closeDossierModal}
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
        </div>

        {/* Printable Document Body */}
        <div 
          id="printable-sar-document"
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '36px 44px',
            backgroundColor: '#ffffff',
            fontFamily: 'serif',
            lineHeight: 1.5
          }}
        >
          {/* Official Document Header */}
          <div style={{ borderBottom: '2px solid #0F172A', paddingBottom: '16px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h1 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, letterSpacing: '0.02em', textTransform: 'uppercase' }}>
                  Suspicious Activity Report (SAR)
                </h1>
                <div style={{ fontSize: '0.85rem', color: '#475569', marginTop: '4px', fontStyle: 'italic' }}>
                  Special Syndicate Forensic Case File • AML Typology Disclosure
                </div>
              </div>

              <div style={{ textAlign: 'right', fontFamily: 'monospace', fontSize: 'var(--fs-xs)' }}>
                <div><strong>REF:</strong> {d.sar_reference_id}</div>
                <div><strong>DATE:</strong> {d.generated_at ? d.generated_at.slice(0, 10) : '2026-10-02'}</div>
              </div>
            </div>

            {/* Mandatory Rule 7 Disclaimer Banner */}
            <div style={{
              marginTop: '14px',
              padding: '8px 12px',
              backgroundColor: '#FEF2F2',
              border: '1px solid #FCA5A5',
              borderRadius: 'var(--radius-sm)',
              color: '#991B1B',
              fontSize: 'var(--fs-xs)',
              fontWeight: 700,
              textAlign: 'center',
              textTransform: 'uppercase',
              letterSpacing: '0.04em'
            }}>
              ⚠ {d.disclaimer_synthetic || "Synthetic demonstration data. Not a real case."}
            </div>
          </div>

          {/* Section 1: Syndicate Overview */}
          <div style={{ marginBottom: '22px' }}>
            <h2 style={{ fontSize: '1rem', textTransform: 'uppercase', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '10px' }}>
              1. Syndicate Classification & Parameters
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.82rem' }}>
              <div>
                <span style={{ color: '#64748B', display: 'block' }}>Target Ring Identifier</span>
                <strong>{d.target_ring_name} ({d.target_ring_id})</strong>
              </div>

              <div>
                <span style={{ color: '#64748B', display: 'block' }}>Typology Classification</span>
                <strong>{d.typology_classification} ({fmtPct(d.typology_similarity)})</strong>
              </div>

              <div>
                <span style={{ color: '#64748B', display: 'block' }}>Total Laundered Volume</span>
                <strong style={{ color: '#B91C1C' }}>{d.total_layered_volume_formatted}</strong>
              </div>

              <div>
                <span style={{ color: '#64748B', display: 'block' }}>Preserved Capital (Estimated)</span>
                <strong style={{ color: '#15803D' }}>{d.disclaimer_saved_money}</strong>
              </div>
            </div>
          </div>

          {/* Section 2: Investigative Narrative */}
          <div style={{ marginBottom: '22px' }}>
            <h2 style={{ fontSize: '1rem', textTransform: 'uppercase', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '10px' }}>
              2. Forensic Narrative & Modus Operandi
            </h2>

            <div style={{ fontSize: '0.85rem', color: '#1E293B', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(d.executive_narrative || []).map((paragraph, idx) => (
                <p key={idx} style={{ margin: 0, textIndent: '16px' }}>
                  {paragraph}
                </p>
              ))}
            </div>
          </div>

          {/* Section 3: Recommended Action */}
          <div style={{ marginBottom: '22px' }}>
            <h2 style={{ fontSize: '1rem', textTransform: 'uppercase', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '10px' }}>
              3. Recommended Interdiction Action
            </h2>

            <div style={{
              padding: '10px 14px',
              backgroundColor: '#F8FAFC',
              borderLeft: '4px solid #0F172A',
              fontSize: '0.82rem',
              fontWeight: 600
            }}>
              {d.recommended_action}
            </div>
          </div>

          {/* Section 4: Member Entities */}
          <div style={{ marginBottom: '22px' }}>
            <h2 style={{ fontSize: '1rem', textTransform: 'uppercase', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '10px' }}>
              4. Subject Accounts & Syndicate Members ({d.subject_accounts?.length || 0})
            </h2>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-xs)' }}>
              <thead>
                <tr style={{ backgroundColor: '#F1F5F9', borderBottom: '1px solid #94A3B8', textAlign: 'left' }}>
                  <th style={{ padding: '6px 8px' }}>Account ID</th>
                  <th style={{ padding: '6px 8px' }}>Name</th>
                  <th style={{ padding: '6px 8px' }}>Role</th>
                  <th style={{ padding: '6px 8px' }}>Score</th>
                  <th style={{ padding: '6px 8px' }}>KYC</th>
                  <th style={{ padding: '6px 8px' }}>Inflow</th>
                  <th style={{ padding: '6px 8px' }}>Outflow</th>
                </tr>
              </thead>
              <tbody>
                {(d.subject_accounts || []).map((acc, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #E2E8F0' }}>
                    <td style={{ padding: '6px 8px', fontFamily: 'monospace' }}>{acc.account_id}</td>
                    <td style={{ padding: '6px 8px' }}>{acc.display_name}</td>
                    <td style={{ padding: '6px 8px', textTransform: 'uppercase', fontWeight: 600 }}>{acc.role}</td>
                    <td style={{ padding: '6px 8px', fontWeight: 700 }}>{Math.round(acc.risk_score)}</td>
                    <td style={{ padding: '6px 8px' }}>{acc.kyc_verified ? 'Verified' : 'Unverified'}</td>
                    <td style={{ padding: '6px 8px' }}>{fmtINR(acc.total_inflow)}</td>
                    <td style={{ padding: '6px 8px' }}>{fmtINR(acc.total_outflow)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Section 5: Audit Transfer Ledger */}
          <div style={{ marginBottom: '22px' }}>
            <h2 style={{ fontSize: '1rem', textTransform: 'uppercase', borderBottom: '1px solid #CBD5E1', paddingBottom: '4px', marginBottom: '10px' }}>
              5. Chronological Transfer Ledger Sample ({d.transfer_ledger?.length || 0} transfers)
            </h2>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-xs)' }}>
              <thead>
                <tr style={{ backgroundColor: '#F1F5F9', borderBottom: '1px solid #94A3B8', textAlign: 'left' }}>
                  <th style={{ padding: '5px 8px' }}>Timestamp</th>
                  <th style={{ padding: '5px 8px' }}>Sender</th>
                  <th style={{ padding: '5px 8px' }}>Receiver</th>
                  <th style={{ padding: '5px 8px' }}>Amount</th>
                  <th style={{ padding: '5px 8px' }}>Channel</th>
                </tr>
              </thead>
              <tbody>
                {(d.transfer_ledger || []).slice(0, 15).map((t, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #E2E8F0' }}>
                    <td style={{ padding: '5px 8px', fontFamily: 'monospace' }}>{t.timestamp ? t.timestamp.slice(0, 19) : '--'}</td>
                    <td style={{ padding: '5px 8px', fontFamily: 'monospace' }}>{t.src || t.source_account}</td>
                    <td style={{ padding: '5px 8px', fontFamily: 'monospace' }}>{t.dest || t.dest_account}</td>
                    <td style={{ padding: '5px 8px', fontWeight: 700 }}>{fmtINR(t.amount)}</td>
                    <td style={{ padding: '5px 8px', textTransform: 'uppercase' }}>{t.channel}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Footer Sign-off */}
          <div style={{ marginTop: '30px', borderTop: '1px solid #0F172A', paddingTop: '16px', display: 'flex', justifyContent: 'space-between', fontSize: 'var(--fs-xs)', color: '#475569' }}>
            <div>
              <strong>PREPARED BY:</strong> Autonomous MuleTrace Forensic Engine<br />
              <strong>CASE STATUS:</strong> FLAGGED FOR REGULATORY FILING
            </div>
            <div style={{ textAlign: 'right' }}>
              <strong>DISCLAIMER:</strong> {d.disclaimer_synthetic || "Synthetic demonstration data. Not a real case."}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SARDossierModal;
