import React, { useState, useMemo } from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { Segmented, SeverityBadge, Chip } from './ui';
import { fmtINR } from '../lib/format';
import { 
  ArrowDownLeft, 
  ArrowUpRight, 
  ChevronDown, 
  ChevronRight, 
  Network 
} from 'lucide-react';

export type Sev = 'critical' | 'medium' | 'safe';

export interface AlertItem {
  id: string;
  name: string;
  severity: Sev;
  score: number;
  inflow: number;
  outflow: number;
  ring?: string | null;
  raw?: any;
}

export function AlertList({
  alerts: propAlerts,
  selectedId: propSelectedId,
  onSelect: propOnSelect,
}: {
  alerts?: AlertItem[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
}) {
  const store = useMuleStore();

  // Connect to Zustand store if props not explicitly passed
  const rawAlerts = propAlerts ?? store.alerts;
  const selectedId = propSelectedId !== undefined ? propSelectedId : store.selectedAccountId;
  const onSelect = propOnSelect ?? store.selectAccount;

  // Normalize alerts from backend or prop format
  const normalizedAlerts: AlertItem[] = useMemo(() => {
    return (rawAlerts || []).map((a: any) => {
      // Find ring id from hits or associated rings
      let ringId = a.ring_id || a.ring || a.syndicate_id || null;
      if (!ringId && store.rings && store.rings.length > 0) {
        const found = store.rings.find((r: any) => {
          const members = r.members || [];
          return members.includes(a.account_id || a.id);
        });
        if (found) ringId = found.ring_id || found.id;
      }
      if (!ringId && a.hits) {
        const rHit = a.hits.find((h: any) => h.ring_key || h.ring_id);
        if (rHit) {
          ringId = rHit.ring_id || (rHit.ring_key ? rHit.ring_key.split('_')[1] : null);
        }
      }

      const id = a.account_id || a.id || '';
      const name = a.display_name || a.name || id;
      const severity = ((a.risk_band || a.severity || 'medium').toLowerCase()) as Sev;
      const score = Math.round(a.risk_score ?? a.score ?? 0);
      const inflow = a.total_inflow ?? a.inflow ?? 0;
      const outflow = a.total_outflow ?? a.outflow ?? 0;

      return {
        id,
        name,
        severity,
        score,
        inflow,
        outflow,
        ring: ringId,
        raw: a,
      };
    });
  }, [rawAlerts, store.rings]);

  const [sev, setSev] = useState<'all' | Sev>('all');
  const [query, setQuery] = useState('');
  const [collapsedRings, setCollapsedRings] = useState<Record<string, boolean>>({});

  const toggleRing = (ringId: string) => {
    setCollapsedRings((prev) => ({
      ...prev,
      [ringId]: !prev[ringId],
    }));
  };

  // Derive visible list from (alerts, severity filter, search query) with useMemo; never store a second copy
  const visible = useMemo(() => {
    return normalizedAlerts
      .filter((a) => sev === 'all' || a.severity === sev)
      .filter((a) => (a.id + ' ' + a.name).toLowerCase().includes(query.toLowerCase()));
  }, [normalizedAlerts, sev, query]);

  // If selected account is filtered out, pin it at the top of the list instead of silently desyncing
  const selected = normalizedAlerts.find((a) => a.id === selectedId);
  const rows = selected && !visible.some((a) => a.id === selected.id)
    ? [selected, ...visible]
    : visible;

  const count = (s: Sev) => normalizedAlerts.filter((a) => a.severity === s).length;

  // Group repeated members of the same ring
  const groupedContent = useMemo(() => {
    // Count occurrences of each ring in current rows
    const ringCounts: Record<string, number> = {};
    rows.forEach((r) => {
      if (r.ring) {
        ringCounts[r.ring] = (ringCounts[r.ring] || 0) + 1;
      }
    });

    // Group rows: rings with 2+ members grouped, others standalone
    const items: Array<
      | { type: 'standalone'; alert: AlertItem }
      | { type: 'ring_group'; ringId: string; alerts: AlertItem[] }
    > = [];

    const processedRings = new Set<string>();

    rows.forEach((row) => {
      if (row.ring && ringCounts[row.ring] > 1) {
        if (!processedRings.has(row.ring)) {
          processedRings.add(row.ring);
          const members = rows.filter((r) => r.ring === row.ring);
          items.push({
            type: 'ring_group',
            ringId: row.ring,
            alerts: members,
          });
        }
      } else {
        items.push({
          type: 'standalone',
          alert: row,
        });
      }
    });

    return items;
  }, [rows]);

  return (
    <aside className="alerts" aria-label="Mule alerts">
      <header className="alerts-head">
        <h2 className="label">Mule alerts</h2>
        <span className="muted" aria-live="polite">
          Showing {visible.length} of {normalizedAlerts.length}
        </span>
      </header>

      <div className="alerts-controls">
        <Segmented
          label="Filter by severity"
          value={sev}
          onChange={(v) => setSev(v as any)}
          options={[
            { id: 'all', label: 'All', count: normalizedAlerts.length },
            { id: 'critical', label: 'Critical', count: count('critical') },
            { id: 'medium', label: 'Medium', count: count('medium') },
            { id: 'safe', label: 'Safe', count: count('safe') },
          ]}
        />

        <input
          className="search"
          type="search"
          placeholder="Search account ID or name"
          aria-label="Search accounts"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <ul className="alert-list" role="list">
        {rows.length === 0 ? (
          <li className="alerts-empty muted">No alerts match criteria</li>
        ) : (
          groupedContent.map((item, idx) => {
            if (item.type === 'standalone') {
              return (
                <AlertRow
                  key={item.alert.id}
                  a={item.alert}
                  selected={item.alert.id === selectedId}
                  onSelect={onSelect}
                />
              );
            }

            const isCollapsed = !!collapsedRings[item.ringId];
            const hasSelected = item.alerts.some((a) => a.id === selectedId);

            return (
              <li key={'ring-' + item.ringId} className="ring-group-section">
                <button
                  type="button"
                  className="ring-group-header"
                  onClick={() => toggleRing(item.ringId)}
                  aria-expanded={!isCollapsed}
                >
                  <span className="ring-group-title">
                    {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                    <Network size={14} />
                    <span className="mono">{item.ringId}</span>
                  </span>
                  <span className="ring-group-badge">{item.alerts.length} members</span>
                </button>

                {(!isCollapsed || hasSelected) && (
                  <ul className="ring-group-members" role="list">
                    {item.alerts.map((a) => {
                      // If collapsed, only show the selected one
                      if (isCollapsed && a.id !== selectedId) return null;
                      return (
                        <AlertRow
                          key={a.id}
                          a={a}
                          selected={a.id === selectedId}
                          onSelect={onSelect}
                        />
                      );
                    })}
                  </ul>
                )}
              </li>
            );
          })
        )}
      </ul>

      <footer className="alerts-foot">
        <span>Keyboard: <strong className="mono">J / K</strong></span>
        <span className="muted">Showing {visible.length} of {normalizedAlerts.length}</span>
      </footer>
    </aside>
  );
}

function AlertRow({
  a,
  selected,
  onSelect,
}: {
  a: AlertItem;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <li className="alert-item">
      <button
        type="button"
        className={'alert-row sev-' + a.severity + (selected ? ' is-selected' : '')}
        onClick={() => onSelect(a.id)}
        aria-current={selected ? 'true' : undefined}
      >
        <span className="alert-top">
          <span className="mono alert-id">{a.id}</span>
          <SeverityBadge severity={a.severity} />
          <span className="mono alert-score">
            {a.score}<small>/100</small>
          </span>
        </span>

        <span className="alert-name">{a.name}</span>

        <span className="alert-flow mono">
          <span title="Money in" aria-label={'Money in ' + fmtINR(a.inflow)} className="flow-in">
            <ArrowDownLeft size={12} aria-hidden="true" /> {fmtINR(a.inflow)}
          </span>
          <span title="Money out" aria-label={'Money out ' + fmtINR(a.outflow)} className="flow-out">
            <ArrowUpRight size={12} aria-hidden="true" /> {fmtINR(a.outflow)}
          </span>
          {a.ring && <Chip variant="brand">{a.ring}</Chip>}
        </span>
      </button>
    </li>
  );
}

// Export for backward compatibility with AlertQueue
export const AlertQueue = AlertList;
export default AlertList;
