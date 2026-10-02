import React, { useEffect } from 'react';
import { useMuleStore } from './store/useMuleStore';
import { AppHeader } from './components/AppHeader';
import { CommandCenterRibbon } from './components/CommandCenterRibbon';
import { AlertList } from './components/AlertList';
import { GraphPane } from './components/GraphPane';
import { Dossier } from './components/Dossier';
import { TimelineScrubber } from './components/TimelineScrubber';
import { FreezeModal } from './components/FreezeModal';
import { SARDossierModal } from './components/SARDossierModal';
import { RingsScreen } from './screens/RingsScreen';
import { LabScreen } from './screens/LabScreen';
import { OmegaScreen } from './screens/OmegaScreen';
import { Palette } from './components/Palette';
import { KeyboardShortcutsModal } from './components/KeyboardShortcutsModal';

export const App = () => {
  const { 
    initDashboard, 
    activeScreen, 
    setActiveScreen, 
    togglePresenterMode, 
    presenterMode, 
    switchPreset, 
    activePreset, 
    loadDemoData, 
    theme, 
    setTheme, 
    selectNextAlert, 
    selectPrevAlert, 
    selectAccount, 
    closeFreezeModal, 
    closeDossierModal, 
    stopReplay, 
    toggleReplayPlay, 
    replayState, 
    isCommandPaletteOpen, 
    openCommandPalette, 
    closeCommandPalette, 
    isShortcutsOpen, 
    openShortcuts, 
    closeShortcuts, 
    toggleShortcuts 
  } = useMuleStore();

  // Presenter mode: reflect on root element
  useEffect(() => {
    document.documentElement.dataset.presenter = String(presenterMode);
  }, [presenterMode]);

  // Presenter mode exit handler on Escape (does not fire if palette or modal is open)
  useEffect(() => {
    const handlePresenterEscape = (e) => {
      if (e.key !== 'Escape' || isCommandPaletteOpen || document.querySelector('dialog[open]')) return;
      if (presenterMode) {
        togglePresenterMode();
      }
    };
    window.addEventListener('keydown', handlePresenterEscape);
    return () => window.removeEventListener('keydown', handlePresenterEscape);
  }, [presenterMode, isCommandPaletteOpen]);

  // Hash-based routing synchronization (supports /#investigation, /#rings, /#lab)
  useEffect(() => {
    const syncFromHash = () => {
      const hash = window.location.hash.replace('#', '').toLowerCase();
      if (hash === 'investigation' || hash === 'investigate') {
        setActiveScreen('investigation');
      } else if (hash === 'rings') {
        setActiveScreen('rings');
      } else if (hash === 'lab') {
        setActiveScreen('lab');
      } else if (hash === 'omega') {
        setActiveScreen('omega');
      }
    };
    syncFromHash();
    window.addEventListener('hashchange', syncFromHash);
    return () => window.removeEventListener('hashchange', syncFromHash);
  }, []);

  const handleTabChange = (newTab) => {
    setActiveScreen(newTab);
    window.location.hash = '#' + newTab;
  };

  // Load initial data once on mount
  useEffect(() => {
    window.useMuleStore = useMuleStore;
    initDashboard();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Universal shortcut: Ctrl+K or Cmd+K
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        if (isCommandPaletteOpen) {
          closeCommandPalette();
        } else {
          openCommandPalette();
        }
        return;
      }

      // Don't intercept single-key commands when user is typing in an input
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

      if (e.key === 'p' || e.key === 'P') {
        togglePresenterMode();
      } else if (e.key === '1') {
        switchPreset('relaxed');
      } else if (e.key === '2') {
        switchPreset('balanced');
      } else if (e.key === '3') {
        switchPreset('strict');
      } else if (e.key === 'j' || e.key === 'J') {
        selectNextAlert();
      } else if (e.key === 'k' || e.key === 'K') {
        selectPrevAlert();
      } else if (e.key === '?') {
        toggleShortcuts();
      } else if (e.key === ' ') {
        if (replayState.active) {
          e.preventDefault();
          toggleReplayPlay();
        }
      } else if (e.key === 'Escape') {
        closeFreezeModal();
        closeDossierModal();
        closeCommandPalette();
        closeShortcuts();
        if (replayState.active) {
          stopReplay();
        } else {
          selectAccount(null);
        }
      } else if (e.key === 't' || e.key === 'T') {
        const order = ['dark', 'calm', 'light', 'colorblind'];
        const nextIdx = (order.indexOf(theme) + 1) % order.length;
        setTheme(order[nextIdx]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [theme, replayState.active, isCommandPaletteOpen, isShortcutsOpen]);

  return (
    <div className="app" style={{ backgroundColor: 'var(--bg-0)' }}>
      <AppHeader
        tab={activeScreen}
        setTab={handleTabChange}
        preset={activePreset}
        setPreset={switchPreset}
        theme={theme}
        setTheme={setTheme}
        presenter={presenterMode}
        setPresenter={togglePresenterMode}
        openPalette={openCommandPalette}
        onRefresh={loadDemoData}
        openShortcuts={openShortcuts}
      />
      {/* Main Forensic Shell */}
      <main id="workspace-root" className="app-main" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {(activeScreen === 'investigate' || activeScreen === 'investigation') && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, width: '100%', overflow: 'hidden' }}>
            {/* Compact KPI strip on Investigation tab with collapse chevron */}
            <CommandCenterRibbon compact={true} collapsible={true} />

            {/* 3-Column Workspace Grid with min-height: 0 on every column */}
            <div id="investigate-screen" className="workspace-grid">
              <div className="workspace-col workspace-col--alerts">
                <AlertList />
              </div>
              <div className="workspace-col workspace-col--graph">
                <GraphPane />
              </div>
              <div className="workspace-col workspace-col--inspector">
                <Dossier />
              </div>
              <TimelineScrubber />
            </div>
          </div>
        )}

        {activeScreen === 'rings' && (
          <div id="rings-screen" style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
            <RingsScreen />
          </div>
        )}

        {activeScreen === 'lab' && (
          <div id="lab-screen" style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
            <LabScreen />
          </div>
        )}

        {activeScreen === 'omega' && (
          <div id="omega-screen" style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
            <OmegaScreen />
          </div>
        )}
      </main>

      {/* Modals & Overlays */}
      <FreezeModal />
      <SARDossierModal />
      <Palette open={isCommandPaletteOpen} onClose={closeCommandPalette} />
      <KeyboardShortcutsModal isOpen={isShortcutsOpen} onClose={closeShortcuts} />
    </div>
  );
};

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[MuleTrace ErrorBoundary caught error]:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '32px',
          backgroundColor: '#0A0F1E',
          color: '#EAF0FF',
          fontFamily: 'Inter, system-ui, sans-serif',
          textAlign: 'center'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '12px', color: '#F87171' }}>
            Application Error Caught
          </h2>
          <p style={{ maxWidth: '500px', color: '#94A3B8', marginBottom: '24px', fontSize: '15px' }}>
            {this.state.error?.message || 'An unexpected rendering issue occurred.'}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.hash = '';
              window.location.reload();
            }}
            style={{
              padding: '10px 20px',
              backgroundColor: '#38BDF8',
              color: '#0A0F1E',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 700,
              fontSize: '15px',
              cursor: 'pointer'
            }}
          >
            Reload MuleTrace
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function SafeApp() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}
