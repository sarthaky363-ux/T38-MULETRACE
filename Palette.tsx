import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { 
  Search, 
  Activity, 
  Network, 
  FlaskConical, 
  Sliders, 
  RefreshCw, 
  Moon, 
  CloudMoon, 
  SunMedium, 
  Eye, 
  ShieldAlert, 
  User, 
  Layers,
  Sparkles 
} from 'lucide-react';

const GROUP_ORDER = ['Navigate', 'Detection', 'Theme', 'Accounts', 'Rings'];

export interface PaletteCommand {
  id: string;
  title: string;
  group: 'Navigate' | 'Detection' | 'Theme' | 'Accounts' | 'Rings';
  Icon: React.ComponentType<{ size?: number; className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;
  hint?: string;
  keywords?: string;
  run: () => void;
}

function score(hay: string, needle: string) {
  if (hay.startsWith(needle)) return 3;
  if (hay.includes(needle)) return 2;
  let i = 0;
  for (const ch of hay) {
    if (ch === needle[i]) i++;
  }
  return i === needle.length ? 1 : 0;
}

function rank(cmds: PaletteCommand[], q: string) {
  const s = q.trim().toLowerCase();
  if (!s) return cmds;
  return cmds
    .map((c) => ({
      c,
      sc: score((c.title + ' ' + (c.keywords ?? '')).toLowerCase(), s),
    }))
    .filter((x) => x.sc > 0)
    .sort((a, b) => b.sc - a.sc)
    .map((x) => x.c);
}

export function Palette({
  open,
  onClose,
  commands: propCommands,
}: {
  open: boolean;
  onClose: () => void;
  commands?: PaletteCommand[];
}) {
  const store = useMuleStore();
  const [q, setQ] = useState('');
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);
  const modKey = isMac ? '⌘' : 'Ctrl';

  // Build commands dynamically if not provided
  const commands: PaletteCommand[] = useMemo(() => {
    if (propCommands) return propCommands;

    const list: PaletteCommand[] = [
      // Navigate
      {
        id: 'nav-investigation',
        title: 'Go to Investigation Workspace',
        group: 'Navigate',
        Icon: Activity,
        hint: `${modKey} 1`,
        keywords: 'investigation alerts graph transfer',
        run: () => store.setActiveScreen('investigation'),
      },
      {
        id: 'nav-rings',
        title: 'Go to Fraud Rings Catalog',
        group: 'Navigate',
        Icon: Network,
        hint: `${modKey} 2`,
        keywords: 'rings syndicates typologies autopsy',
        run: () => store.setActiveScreen('rings'),
      },
      {
        id: 'nav-lab',
        title: 'Go to Forensic Benchmark Lab',
        group: 'Navigate',
        Icon: FlaskConical,
        hint: `${modKey} 3`,
        keywords: 'lab metrics benchmark ground truth evasion',
        run: () => store.setActiveScreen('lab'),
      },
      {
        id: 'nav-omega',
        title: 'Go to MuleTrace Ω Simulation',
        group: 'Navigate',
        Icon: Sparkles,
        hint: `${modKey} 4`,
        keywords: 'omega quantum walk interdiction simulation qubo fidelity physics',
        run: () => store.setActiveScreen('omega'),
      },

      // Detection
      {
        id: 'preset-relaxed',
        title: 'Switch Sensitivity: Relaxed',
        group: 'Detection',
        Icon: Sliders,
        keywords: 'relaxed sensitivity low false positives',
        run: () => store.switchPreset('relaxed'),
      },
      {
        id: 'preset-balanced',
        title: 'Switch Sensitivity: Balanced',
        group: 'Detection',
        Icon: Sliders,
        keywords: 'balanced sensitivity recommended standard',
        run: () => store.switchPreset('balanced'),
      },
      {
        id: 'preset-strict',
        title: 'Switch Sensitivity: Strict',
        group: 'Detection',
        Icon: Sliders,
        keywords: 'strict high recall aggressive catch',
        run: () => store.switchPreset('strict'),
      },
      {
        id: 'action-refresh',
        title: 'Reset / Refresh Demo Data',
        group: 'Detection',
        Icon: RefreshCw,
        keywords: 'reset reload refresh demo dataset',
        run: () => store.loadDemoData(),
      },

      // Theme
      {
        id: 'theme-dark',
        title: 'Theme: Dark Cyber-Defense',
        group: 'Theme',
        Icon: Moon,
        keywords: 'dark theme cyber defense black navy',
        run: () => store.setTheme('dark'),
      },
      {
        id: 'theme-calm',
        title: 'Theme: Calm Slate',
        group: 'Theme',
        Icon: CloudMoon,
        keywords: 'calm slate grey cool subdued',
        run: () => store.setTheme('calm'),
      },
      {
        id: 'theme-light',
        title: 'Theme: Paper Light',
        group: 'Theme',
        Icon: SunMedium,
        keywords: 'light paper clean bright white',
        run: () => store.setTheme('light'),
      },
      {
        id: 'theme-colorblind',
        title: 'Theme: High-Contrast Colorblind',
        group: 'Theme',
        Icon: Eye,
        keywords: 'colorblind accessibility high contrast accessible',
        run: () => store.setTheme('colorblind'),
      },
    ];

    // Add flagged accounts to palette
    (store.alerts || []).forEach((a: any) => {
      const id = a.account_id || a.id;
      const name = a.display_name || a.name || id;
      const sev = (a.risk_band || a.severity || 'medium').toUpperCase();
      const score = Math.round(a.risk_score || a.score || 0);
      list.push({
        id: `account-${id}`,
        title: `${id} · ${name} (${sev} ${score}/100)`,
        group: 'Accounts',
        Icon: ShieldAlert,
        keywords: `${id} ${name} ${sev} account mule`,
        run: () => {
          store.selectAccount(id);
          store.fetchGraph(id);
          store.setActiveScreen('investigation');
        },
      });
    });

    // Add detected rings to palette
    (store.rings || []).forEach((r: any) => {
      const rId = r.ring_id || r.id;
      const title = r.ring_name || r.title || rId;
      list.push({
        id: `ring-${rId}`,
        title: `${rId} · ${title}`,
        group: 'Rings',
        Icon: Network,
        keywords: `${rId} ${title} ring syndicate`,
        run: () => {
          const target = r.hub_account || (r.members && r.members[0]);
          if (target) {
            store.selectAccount(target);
            store.fetchGraph(target);
          }
          store.setActiveScreen('investigation');
        },
      });
    });

    return list;
  }, [propCommands, store.alerts, store.rings, modKey]);

  const grouped = useMemo(() => {
    const hits = rank(commands, q);
    return GROUP_ORDER.map((g) => [g, hits.filter((h) => h.group === g)] as const).filter(
      ([, items]) => items.length > 0
    );
  }, [commands, q]);

  const flat = useMemo(() => grouped.flatMap(([, items]) => items), [grouped]);

  useEffect(() => {
    setActive(0);
  }, [q]);

  useEffect(() => {
    if (open) {
      setQ('');
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Keep active option visible on arrow navigation
  useEffect(() => {
    if (!open) return;
    const el = document.getElementById(`pal-${active}`);
    if (el) {
      el.scrollIntoView({ block: 'nearest' });
    }
  }, [active, open]);

  if (!open) return null;

  const run = (cmd: PaletteCommand) => {
    cmd.run();
    onClose();
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, flat.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && flat[active]) {
      e.preventDefault();
      run(flat[active]);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    } else if (e.key === 'Tab') {
      // Trap Tab key inside palette
      e.preventDefault();
    }
  };

  let idx = -1;

  return (
    <div className="pal-overlay" onMouseDown={onClose}>
      <div
        className="pal"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onMouseDown={(e) => e.stopPropagation()}
        onKeyDown={onKey}
      >
        <div className="pal-input">
          <Search size={18} aria-hidden="true" />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search accounts, rings, commands"
            role="combobox"
            aria-expanded="true"
            aria-controls="pal-list"
            aria-activedescendant={flat[active] ? `pal-${active}` : undefined}
            aria-autocomplete="list"
          />
        </div>

        <ul id="pal-list" ref={listRef} role="listbox" className="pal-list" aria-label="Suggestions">
          {grouped.length === 0 && <li className="pal-empty">No results for "{q}"</li>}
          {grouped.map(([group, items]) => (
            <li key={group} role="presentation" className="pal-group-item">
              <div className="pal-group" role="presentation">
                {group}
              </div>
              <ul role="presentation" className="pal-sublist">
                {items.map((cmd) => {
                  idx += 1;
                  const i = idx;
                  const isSelected = i === active;
                  return (
                    <li
                      key={cmd.id}
                      id={'pal-' + i}
                      role="option"
                      aria-selected={isSelected}
                      className={'pal-item' + (isSelected ? ' is-active' : '')}
                      onMouseMove={() => setActive(i)}
                      onClick={() => run(cmd)}
                    >
                      <cmd.Icon size={16} aria-hidden="true" />
                      <span className="pal-title">{cmd.title}</span>
                      {cmd.hint && <kbd>{cmd.hint}</kbd>}
                    </li>
                  );
                })}
              </ul>
            </li>
          ))}
        </ul>

        <footer className="pal-foot">
          <span>↑ ↓ navigate</span>
          <span>↵ select</span>
          <span>Esc close</span>
        </footer>
      </div>
    </div>
  );
}

// Export for backwards compatibility with CommandPalette
export const CommandPalette = Palette;
export default Palette;
