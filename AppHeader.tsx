// src/components/AppHeader.tsx
import React from 'react';
import { 
  ShieldCheck, 
  Activity, 
  Network, 
  FlaskConical, 
  Search, 
  HelpCircle, 
  RefreshCw, 
  Presentation,
  Sparkles 
} from 'lucide-react';
import { Segmented } from './ui';
import { useMuleStore } from '../store/useMuleStore';

const TABS = [
  { id: "investigation", label: "Investigation", Icon: Activity },
  { id: "rings",         label: "Fraud rings",   Icon: Network },
  { id: "lab",           label: "Forensic lab",  Icon: FlaskConical },
  { id: "omega",         label: "MuleTrace Ω",   Icon: Sparkles },
];

const MOD = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Ctrl";

export interface AppHeaderProps {
  tab?: string;
  setTab?: (tab: string) => void;
  preset?: string;
  setPreset?: (preset: string) => void;
  theme?: string;
  setTheme?: (theme: string) => void;
  presenter?: boolean;
  setPresenter?: (presenter: boolean) => void;
  openPalette?: () => void;
  onRefresh?: () => void;
  openShortcuts?: () => void;
}

const PRESET_OPTIONS = [
  { 
    id: "relaxed", 
    value: "relaxed",
    label: "Relaxed",
    title: "Relaxed sensitivity: 60m window, min 3 hops, >=80% pass-through, ₹3K post-balance. Broadest recall detecting slow-paced evasion rings."
  },
  { 
    id: "balanced", 
    value: "balanced",
    label: "Balanced",
    title: "Balanced sensitivity: 45m window, min 4 senders, >=85% pass-through, ₹2K post-balance. Optimal production balance of precision and recall."
  },
  { 
    id: "strict", 
    value: "strict",
    label: "Strict",
    title: "Strict sensitivity: 30m window, >=₹1L inflow, min 5 senders, >=90% pass-through, ₹1K post-balance. High precision eliminating false positives."
  }
];

export function AppHeader({
  tab,
  setTab,
  preset,
  setPreset,
  theme,
  setTheme,
  presenter,
  setPresenter,
  openPalette,
  onRefresh,
  openShortcuts,
}: AppHeaderProps) {
  const store = useMuleStore();

  // Support both direct props and store fallback
  const activeTab = tab ?? store.activeScreen;
  const handleSetTab = (newTab: string) => {
    if (setTab) {
      setTab(newTab);
    } else {
      store.setActiveScreen(newTab);
    }
  };

  const activePreset = preset ?? store.activePreset;
  const handleSetPreset = (newPreset: string) => {
    if (setPreset) {
      setPreset(newPreset);
    } else {
      store.switchPreset(newPreset);
    }
  };

  const rawTheme = theme ?? store.theme;
  // Normalize theme value for select box
  const activeTheme = rawTheme === 'light' ? 'paper' : rawTheme === 'colorblind' ? 'hc' : rawTheme;
  const handleSetTheme = (newTheme: string) => {
    if (setTheme) {
      setTheme(newTheme);
    } else {
      store.setTheme(newTheme);
    }
  };

  const isPresenter = presenter !== undefined ? presenter : store.presenterMode;
  const handleSetPresenter = (val: boolean) => {
    if (setPresenter) {
      setPresenter(val);
    } else {
      if (val !== store.presenterMode) {
        store.togglePresenterMode();
      }
    }
  };

  const handleOpenPalette = openPalette ?? store.openCommandPalette;
  const handleRefresh = onRefresh ?? store.loadDemoData;
  const handleOpenShortcuts = openShortcuts ?? store.openShortcuts;
  const isLoading = store.isLoading;

  return (
    <header className="app-header-container">
      {/* 1. Brand in Top-Left Corner (Outside the pill-shaped bar) */}
      <div 
        className="brand brand-standalone"
        onClick={() => handleSetTab('investigation')}
        role="button"
        tabIndex={0}
        aria-label="MuleTrace Home"
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleSetTab('investigation'); }}
      >
        <span className="brand-mark" aria-hidden="true">
          <img src="/muletrace-logo.png" alt="MuleTrace Logo" className="brand-logo-img" />
        </span>
        <div className="brand-text">
          <h1 className="mule-trace-title">MuleTrace</h1>
          <p>Money-mule and layering-ring forensics</p>
        </div>
      </div>

      {/* 2. Centered Nav & Tools Capsule Bar */}
      <div className="app-header">
        {/* Tabs Column */}
        <nav className="tabs" role="tablist" aria-label="Workspaces">
          {TABS.map(({ id, label, Icon }) => {
            const isSelected = activeTab === id || (id === "investigation" && activeTab === "investigate");
            return (
              <button
                key={id}
                role="tab"
                className="tab"
                aria-selected={isSelected}
                onClick={() => handleSetTab(id)}
              >
                <Icon size={16} aria-hidden="true" />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>

        {/* Toolbar Column */}
        <div className="toolbar">
          {/* Global Command Palette & Search Trigger */}
          <button
            type="button"
            className="btn btn-search-trigger"
            onClick={handleOpenPalette}
            aria-keyshortcuts="Control+K"
            title="Open Command Palette & Global Search (Ctrl+K)"
          >
            <Search size={18} aria-hidden="true" />
            <span>Search</span>
            <kbd>{MOD} K</kbd>
          </button>

          {/* Shortcuts Help Modal */}
          <button
            type="button"
            className="icon-btn btn-help"
            aria-label="Help"
            title="Help — Keyboard shortcuts cheat sheet (Press '?')"
            onClick={handleOpenShortcuts}
          >
            <HelpCircle size={18} aria-hidden="true" />
          </button>

          {/* Re-run analysis & Reload demo data */}
          <button
            type="button"
            className="icon-btn btn-refresh"
            aria-label="Re-run analysis"
            title="Re-run analysis — Reload demo forensic dataset"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} aria-hidden="true" />
          </button>

          {/* Theme Select Dropdown */}
          <label className="sr-only" htmlFor="theme">Theme</label>
          <select
            id="theme"
            className="btn theme-select"
            value={activeTheme}
            onChange={(e) => handleSetTheme(e.target.value)}
            aria-label="Theme selection"
          >
            <option value="dark">Dark cyber-defense</option>
            <option value="calm">Calm slate</option>
            <option value="paper">Paper light</option>
            <option value="hc">High-contrast (colourblind)</option>
          </select>

          {/* Presenter Pill Indicator */}
          {isPresenter && (
            <span className="presenter-pill" role="status">
              Presenter · Esc to exit
            </span>
          )}

          {/* Presenter Mode Toggle */}
          <button
            type="button"
            className={"btn btn-presenter" + (isPresenter ? " is-active" : "")}
            aria-pressed={isPresenter}
            onClick={() => handleSetPresenter(!isPresenter)}
            title="Toggle High-Visibility Presenter Mode (Press 'P')"
          >
            <Presentation size={16} aria-hidden="true" />
            <span>Presenter</span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default AppHeader;
