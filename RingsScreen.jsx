import React from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { 
  Layers, 
  ShieldAlert, 
  FileText, 
  ExternalLink, 
  ArrowRight, 
  Users, 
  DollarSign, 
  Activity,
  Dna,
  CheckCircle,
  HelpCircle
} from 'lucide-react';

export const RingsScreen = () => {
  const { 
    rings, 
    selectAccount, 
    setActiveScreen, 
    openDossierModal, 
    fetchGraph 
  } = useMuleStore();

  const formatCurrency = (val) => {
    return `₹${Math.round(val || 0).toLocaleString('en-IN')}`;
  };

  const handleInspectInGraph = (ring) => {
    const targetAccount = ring.hub_account || (ring.members && ring.members[0]);
    if (targetAccount) {
      selectAccount(targetAccount);
      fetchGraph(targetAccount);
    }
    setActiveScreen('investigate');
  };

  return (
    <div 
      id="rings-screen-container" 
      aria-label="Fraud Rings Screen"
      style={{
        padding: '28px 36px',
        maxWidth: '1440px',
        margin: '0 auto',
        height: '100%',
        overflowY: 'auto'
      }}
    >
      {/* Screen Title & Subtitle */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Layers size={24} style={{ color: 'var(--accent)' }} />
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            FRAUD SYNDICATE RINGS & FORENSIC AUTOPSIES
          </h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
          Autonomous 6D Ring DNA typology matching against curated AML crime libraries and criminal cluster forensics.
        </p>
      </div>

      {/* Grid of Rings */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(440px, 1fr))',
        gap: '20px'
      }}>
        {rings.map((ring) => {
          const dna = ring.dna_vector || {};
          const similarity = ring.similarity_pct || 0;
          const matchColor = similarity > 85 ? 'var(--danger)' : similarity > 70 ? 'var(--warning)' : 'var(--accent)';

          return (
            <div
              key={ring.ring_id}
              style={{
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
                transition: 'border-color 0.2s ease',
              }}
            >
              {/* Card Header: Ring ID, Name and Typology Match */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div>
                  <span style={{ 
                    fontFamily: 'monospace', 
                    fontSize: '0.72rem', 
                    color: 'var(--accent)', 
                    fontWeight: 700, 
                    display: 'block' 
                  }}>
                    {ring.ring_id}
                  </span>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: '2px 0 0 0', color: 'var(--text-primary)' }}>
                    {ring.ring_name}
                  </h3>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    padding: '3px 8px',
                    borderRadius: '4px',
                    backgroundColor: `${matchColor}22`,
                    color: matchColor,
                    border: `1px solid ${matchColor}55`,
                    display: 'inline-block'
                  }}>
                    {similarity}% Typology Match
                  </span>
                  <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {ring.typology_name}
                  </span>
                </div>
              </div>

              {/* Key Metrics Strip */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                gap: '8px',
                backgroundColor: 'var(--bg-app)',
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                marginBottom: '14px',
                fontSize: '0.75rem'
              }}>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.68rem' }}>Total Laundered</span>
                  <strong style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>
                    {formatCurrency(ring.total_volume)}
                  </strong>
                </div>

                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.68rem' }}>Members Flagged</span>
                  <strong style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                    {ring.members?.length || 0} Accounts
                  </strong>
                </div>

                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.68rem' }}>Hub / Nexus</span>
                  <strong style={{ fontFamily: 'monospace', color: 'var(--accent)', fontSize: '0.85rem' }}>
                    {ring.hub_account || 'Distributed'}
                  </strong>
                </div>
              </div>

              {/* 6D Ring DNA Fingerprint Meters */}
              <div style={{ marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <Dna size={14} style={{ color: 'var(--accent)' }} />
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    6D Ring DNA Signature
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 14px', fontSize: '0.7rem' }}>
                  {Object.entries(dna).map(([dim, val]) => (
                    <div key={dim}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                          {dim.replace(/_/g, ' ')}
                        </span>
                        <span style={{ fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                          {(val * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div style={{ height: '4px', backgroundColor: 'var(--bg-app)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ width: `${Math.min(100, Math.max(0, val * 100))}%`, height: '100%', backgroundColor: 'var(--accent)' }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Forensic Autopsy Narrative */}
              <div style={{
                flex: 1,
                fontSize: '0.78rem',
                lineHeight: 1.45,
                color: 'var(--text-secondary)',
                backgroundColor: 'var(--bg-surface)',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                marginBottom: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {(ring.narrative || []).map((para, pIdx) => (
                  <p key={pIdx} style={{ margin: 0 }}>
                    {para}
                  </p>
                ))}
              </div>

              {/* Card Footer Actions */}
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={() => handleInspectInGraph(ring)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    backgroundColor: 'var(--accent)',
                    border: 'none',
                    color: '#ffffff',
                    fontWeight: 700,
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  <ExternalLink size={12} />
                  Inspect in Graph
                </button>

                <button
                  onClick={() => openDossierModal(ring.ring_id)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    backgroundColor: 'var(--bg-app)',
                    border: '1px solid var(--border)',
                    color: 'var(--text-primary)',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  <FileText size={12} />
                  Regulatory SAR
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RingsScreen;
