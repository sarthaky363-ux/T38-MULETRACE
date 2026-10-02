import React from 'react';
import { fmtPct, fmtINR, fmtMin } from '../lib/format';
import { ExternalLink, FileText, Network } from 'lucide-react';

export const DNA_DIMENSIONS = [
  'Structure Type',
  'Network Size',
  'Duration Velocity',
  'Hop Transfer Gap',
  'Retained Ratio',
  'Forward Drain Ratio',
];

export interface RingData {
  id: string;
  title: string;
  typology: string;
  match: number;
  total: number;
  members: number;
  memberList?: string[];
  hub: string;
  hubLabel?: string;
  dna: number[];
  durationMin: number;
  forwardPct: number;
  avgGapMin: number;
  freezeHop: number;
  freezeMin: number;
  interceptPct: number;
  narrative?: string[];
  raw?: any;
}

export function RingCard({
  ring,
  dims = DNA_DIMENSIONS,
  onOpen,
  onSelectMember,
  onExportSar,
}: {
  ring: RingData;
  dims?: string[];
  onOpen: (ringId: string) => void;
  onSelectMember?: (memberId: string) => void;
  onExportSar?: (ringId: string) => void;
}) {
  return (
    <article className="ring-card" id={'ring-' + ring.id}>
      <header className="ring-head">
        <div>
          <span className="label mono">{ring.id}</span>
          <h3>{ring.title}</h3>
          <p className="ring-type">{ring.typology}</p>
        </div>
        <div className="match" aria-label={'Typology match ' + fmtPct(ring.match)}>
          <span className="match-val mono">{fmtPct(ring.match)}</span>
          <span className="label">typology match</span>
        </div>
      </header>

      <dl className="ring-stats">
        <div>
          <dt>Total laundered</dt>
          <dd className="mono">{fmtINR(ring.total)}</dd>
        </div>
        <div>
          <dt>Members flagged</dt>
          <dd className="mono">
            {onSelectMember && ring.memberList && ring.memberList.length > 0 ? (
              <button
                type="button"
                className="member-link"
                onClick={() => onSelectMember(ring.memberList![0])}
                title="View member in graph & dossier"
              >
                {ring.members} accounts
              </button>
            ) : (
              <span>{ring.members} accounts</span>
            )}
          </dd>
        </div>
        <div>
          <dt>{ring.hubLabel ?? 'Hub / Nexus'}</dt>
          <dd className="mono">
            {onSelectMember && ring.hub && ring.hub !== 'Distributed' ? (
              <button
                type="button"
                className="member-link"
                onClick={() => onSelectMember(ring.hub)}
                title="Inspect Hub account"
              >
                {ring.hub}
              </button>
            ) : (
              <span>{ring.hub}</span>
            )}
          </dd>
        </div>
      </dl>

      <h4 className="label">Ring DNA signature</h4>
      <DnaBars dims={dims} values={ring.dna} />

      <ul className="ring-findings">
        <li>
          Moved <strong>{fmtINR(ring.total)}</strong> across
          <strong> {ring.members} accounts</strong> in
          <strong> {fmtMin(ring.durationMin)}</strong>.
        </li>
        <li>
          Relays forwarded <strong>{fmtPct(ring.forwardPct)}</strong> of funds with an average gap of{' '}
          <strong>{fmtMin(ring.avgGapMin)}</strong>.
        </li>
        <li className="finding--win">
          Freezing at hop <strong>{ring.freezeHop}</strong> within
          <strong> {fmtMin(ring.freezeMin)}</strong> would have intercepted over
          <strong> {fmtPct(ring.interceptPct, 0)}</strong> of the money.
        </li>
      </ul>

      <div className="ring-card-actions">
        <button type="button" className="btn btn--primary" onClick={() => onOpen(ring.id)}>
          <ExternalLink size={14} aria-hidden="true" />
          Open ring in graph
        </button>
        {onExportSar && (
          <button type="button" className="btn btn--ghost" onClick={() => onExportSar(ring.id)}>
            <FileText size={14} aria-hidden="true" />
            Regulatory SAR
          </button>
        )}
      </div>
    </article>
  );
}

// values are 0..1. dims are real feature names read from backend/ringdna.py extractor
export function DnaBars({ dims, values }: { dims: string[]; values: number[] }) {
  return (
    <ul className="dna" aria-label="Ring DNA signature">
      {dims.map((name, i) => {
        const raw = values && values[i] !== undefined ? values[i] : 0;
        const v = Math.round(Number(raw) * 100);
        return (
          <li key={name} className="dna-row">
            <span className="dna-name">{name}</span>
            <span className="dna-track" role="img" aria-label={name + ' ' + v + ' percent'}>
              <span className="dna-fill" data-hot={v >= 80} style={{ width: v + '%' }} />
            </span>
            <span className="dna-val mono">{v}%</span>
          </li>
        );
      })}
    </ul>
  );
}

export default RingCard;
