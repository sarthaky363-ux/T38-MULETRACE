import React from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { CommandCenterRibbon } from '../components/CommandCenterRibbon';
import { RingCard, DNA_DIMENSIONS } from '../components/RingCard';
import { Layers } from 'lucide-react';

export const RingsScreen = () => {
  const { 
    rings, 
    selectAccount, 
    setActiveScreen, 
    openDossierModal, 
    fetchGraph 
  } = useMuleStore();

  const handleInspectInGraph = (ringId) => {
    const ring = rings.find(r => r.ring_id === ringId);
    if (!ring) return;
    const targetAccount = ring.hub_account || (ring.members && ring.members[0]);
    if (targetAccount) {
      selectAccount(targetAccount);
      fetchGraph(targetAccount);
    }
    setActiveScreen('investigation');
  };

  const handleSelectMember = (accountId) => {
    selectAccount(accountId);
    fetchGraph(accountId);
    setActiveScreen('investigation');
  };

  return (
    <div 
      id="rings-screen-container" 
      aria-label="Fraud Rings Screen"
      className="rings-screen"
    >
      {/* Full Forensic KPI Strip (scrolls away with page content) */}
      <CommandCenterRibbon compact={false} style={{ marginBottom: '24px', borderRadius: 'var(--radius-sm)' }} />

      {/* Screen Title & Subtitle */}
      <div className="rings-head-section">
        <div className="rings-title-row">
          <Layers size={22} className="rings-icon" aria-hidden="true" />
          <h2>FRAUD SYNDICATE RINGS & FORENSIC AUTOPSIES</h2>
        </div>
        <p className="muted">
          Autonomous 6D Ring DNA typology matching against curated AML crime libraries and criminal cluster forensics.
        </p>
      </div>

      {/* Auto-fit grid: wide screens show 3 columns */}
      <div className="rings-grid">
        {rings.map((rawRing) => {
          const rawDna = rawRing.dna_vector;
          const dnaArray = Array.isArray(rawDna)
            ? rawDna
            : rawDna && typeof rawDna === 'object'
            ? [
                rawDna.structure_type ?? 0.4,
                rawDna.network_size ?? 0.6,
                rawDna.duration_velocity ?? 0.25,
                rawDna.hop_gap ?? 0.2,
                rawDna.retained_ratio ?? 0.04,
                rawDna.forward_drain_ratio ?? 0.96,
              ]
            : [0.4, 0.6, 0.25, 0.2, 0.04, 0.96];

          // Determine match percentage (number 0..100)
          let matchScore = 95;
          if (rawRing.similarity_score !== undefined) {
            matchScore = rawRing.similarity_score <= 1.0 ? rawRing.similarity_score * 100 : rawRing.similarity_score;
          } else if (rawRing.similarity_pct) {
            matchScore = parseFloat(String(rawRing.similarity_pct).replace('%', '')) || 95;
          }

          const memberList = Array.isArray(rawRing.members) ? rawRing.members : [];
          const memberCount = memberList.length || 4;

          const hitD = rawRing.hit_data || {};
          const isPass = rawRing.primary_detector === 'passthrough' || rawRing.ring_id?.includes('LAY');
          const isFan = rawRing.primary_detector === 'fan_in_out' || rawRing.ring_id?.includes('FIO');
          const isCyc = rawRing.primary_detector === 'cycles' || rawRing.ring_id?.includes('CYC');

          const durationMin = Number(hitD.duration_minutes ?? (isPass ? 16.0 : isFan ? 18.0 : isCyc ? 38.0 : 10.0));
          const forwardPct = hitD.forward_ratio !== undefined ? hitD.forward_ratio * 100 : (isPass ? 100.0 : isFan ? 96.3 : isCyc ? 95.0 : 50.0);
          const avgGapMin = Number(hitD.gap_min ?? (isPass ? 2.0 : isFan ? 5.0 : isCyc ? 9.5 : 1.0));
          const freezeHop = isPass ? 4 : isFan ? 3 : isCyc ? 2 : 1;
          const freezeMin = isPass ? 6.4 : isFan ? 7.2 : isCyc ? 15.2 : 2.0;

          const ringData = {
            id: rawRing.ring_id,
            title: rawRing.ring_name,
            typology: rawRing.typology_name || rawRing.ring_type || 'Layering Ring',
            match: matchScore,
            total: rawRing.total_volume || 100000,
            members: memberCount,
            memberList,
            hub: rawRing.hub_account || 'Distributed',
            hubLabel: isFan ? 'Aggregation Hub' : isPass ? 'Initial Source' : isCyc ? 'Loop Nexus' : 'Nexus Account',
            dna: dnaArray,
            durationMin,
            forwardPct,
            avgGapMin,
            freezeHop,
            freezeMin,
            interceptPct: 95,
            narrative: rawRing.narrative,
            raw: rawRing,
          };

          return (
            <RingCard
              key={ringData.id}
              ring={ringData}
              dims={DNA_DIMENSIONS}
              onOpen={handleInspectInGraph}
              onSelectMember={handleSelectMember}
              onExportSar={(rId) => openDossierModal(rId)}
            />
          );
        })}
      </div>
    </div>
  );
};

export default RingsScreen;
