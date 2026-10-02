import { create } from 'zustand';

export const useMuleStore = create((set, get) => ({
  // UI & Theme State
  theme: 'dark',
  presenterMode: false,
  activeScreen: 'investigate', // 'investigate', 'rings', 'lab'
  isLoading: false,
  error: null,

  // KPI Dashboard Summary
  summary: {
    total_accounts: 0,
    total_transactions: 0,
    flagged_accounts: 0,
    critical_accounts: 0,
    rings_detected: 0,
    estimated_amount_at_risk: 0,
    estimated_amount_at_risk_formatted: '₹0',
    estimated_amount_saved: 0,
    estimated_amount_saved_formatted: 'Estimated amount saved: ₹0',
    preset: 'balanced',
    early_warnings_count: 0,
  },

  // Alert Queue & Filters
  alerts: [],
  totalAlerts: 0,
  filterRisk: 'all',
  filterDetector: 'all',
  searchQuery: '',
  alertPage: 0,

  // Deep Investigation Target
  selectedAccountId: null,
  selectedAccountDetail: null,

  // Financial Graph Data
  graphData: { nodes: [], edges: [] },
  graphCenterId: null,

  // Rings & Typologies
  rings: [],
  selectedRingId: null,
  selectedRingDetail: null,
  currentDossier: null,

  // Forensics: Replay & Freeze
  replayState: {
    isPlaying: false,
    currentFrameIndex: 0,
    frames: [],
    flowEvents: [],
    speed: 1000,
    active: false,
    sourceAccount: null,
  },
  isFreezeModalOpen: false,
  freezeSimulationData: null,
  isDossierModalOpen: false,
  isCommandPaletteOpen: false,
  isShortcutsOpen: false,
  freezeCurve: [],
  chaseList: [],
  earlyWarnings: [],

  // Offline Benchmark Metrics & Evasion
  metrics: null,
  evasionData: null,

  // Presets
  activePreset: 'balanced',
  availablePresets: ['relaxed', 'balanced', 'strict'],

  // Actions
  setTheme: (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    set({ theme });
  },

  togglePresenterMode: () => {
    const next = !get().presenterMode;
    if (next) {
      document.body.classList.add('presenter-mode');
    } else {
      document.body.classList.remove('presenter-mode');
    }
    set({ presenterMode: next });
  },

  setActiveScreen: (screen) => set({ activeScreen: screen }),

  setFilterRisk: (risk) => {
    set({ filterRisk: risk });
    get().fetchAlerts();
  },

  setFilterDetector: (detector) => {
    set({ filterDetector: detector });
    get().fetchAlerts();
  },

  setSearchQuery: (search) => {
    set({ searchQuery: search });
    get().fetchAlerts();
  },

  fetchSummary: async () => {
    try {
      const res = await fetch('/api/summary');
      if (!res.ok) throw new Error('Failed to fetch summary');
      const data = await res.json();
      set({ summary: data, activePreset: data.preset });
    } catch (err) {
      console.error(err);
      set({ error: err.message });
    }
  },

  fetchAlerts: async () => {
    try {
      const { filterRisk, filterDetector, searchQuery } = get();
      const params = new URLSearchParams();
      if (filterRisk && filterRisk !== 'all') params.append('risk_band', filterRisk);
      if (filterDetector && filterDetector !== 'all') params.append('detector', filterDetector);
      if (searchQuery) params.append('search', searchQuery);
      params.append('limit', '50');

      const res = await fetch(`/api/alerts?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to fetch alerts');
      const data = await res.json();
      set({ alerts: data.alerts, totalAlerts: data.total });
    } catch (err) {
      console.error(err);
      set({ error: err.message });
    }
  },

  fetchGraph: async (centerId = null) => {
    try {
      const url = centerId
        ? `/api/graph?center_id=${encodeURIComponent(centerId)}&depth=2&max_nodes=100`
        : '/api/graph?max_nodes=100';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch graph');
      const data = await res.json();
      set({ graphData: data, graphCenterId: centerId });
    } catch (err) {
      console.error(err);
    }
  },

  selectAccount: async (accountId) => {
    if (!accountId) {
      set({ selectedAccountId: null, selectedAccountDetail: null });
      return;
    }
    set({ selectedAccountId: accountId });
    try {
      const res = await fetch(`/api/accounts/${encodeURIComponent(accountId)}`);
      if (!res.ok) throw new Error('Failed to fetch account detail');
      const data = await res.json();
      set({ selectedAccountDetail: data });
      get().fetchGraph(accountId);
    } catch (err) {
      console.error(err);
    }
  },

  selectNextAlert: () => {
    const { alerts, selectedAccountId } = get();
    if (!alerts || alerts.length === 0) return;
    const currentIndex = alerts.findIndex(a => a.account_id === selectedAccountId);
    const nextIndex = currentIndex < alerts.length - 1 ? currentIndex + 1 : 0;
    get().selectAccount(alerts[nextIndex].account_id);
  },

  selectPrevAlert: () => {
    const { alerts, selectedAccountId } = get();
    if (!alerts || alerts.length === 0) return;
    const currentIndex = alerts.findIndex(a => a.account_id === selectedAccountId);
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : alerts.length - 1;
    get().selectAccount(alerts[prevIndex].account_id);
  },

  submitVerdict: async (accountId, verdict, notes = '') => {
    try {
      const res = await fetch(`/api/accounts/${encodeURIComponent(accountId)}/verdict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verdict, analyst_notes: notes }),
      });
      if (!res.ok) throw new Error('Verdict submission failed');
      const data = await res.json();
      // Refresh current account and alerts
      await get().selectAccount(accountId);
      await get().fetchAlerts();
      await get().fetchSummary();
      return data;
    } catch (err) {
      console.error(err);
      throw err;
    }
  },

  fetchRings: async () => {
    try {
      const res = await fetch('/api/rings');
      if (!res.ok) throw new Error('Failed to fetch rings');
      const data = await res.json();
      set({ rings: data });
    } catch (err) {
      console.error(err);
    }
  },

  selectRing: async (ringId) => {
    set({ selectedRingId: ringId });
    try {
      const [rRes, dRes] = await Promise.all([
        fetch(`/api/rings/${encodeURIComponent(ringId)}`),
        fetch(`/api/case/${encodeURIComponent(ringId)}/dossier`),
      ]);
      const rData = await rRes.json();
      const dData = await dRes.json();
      set({ selectedRingDetail: rData, currentDossier: dData });
      if (rData.hub_account) {
        get().fetchGraph(rData.hub_account);
      }
    } catch (err) {
      console.error(err);
    }
  },

  openDossierModal: async (ringId) => {
    if (ringId) {
      await get().selectRing(ringId);
    }
    set({ isDossierModalOpen: true });
  },

  closeDossierModal: () => set({ isDossierModalOpen: false }),

  triggerReplay: async (sourceAccount) => {
    const { replayState } = get();
    // If replay is already active for this account, clicking replay again closes the replay bar
    if (replayState.active && (!sourceAccount || replayState.sourceAccount === sourceAccount)) {
      get().stopReplay();
      return;
    }

    try {
      const res = await fetch('/api/replay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_account: sourceAccount,
          start_time: '2026-10-01T00:00:00Z',
          initial_amount: 100000.0,
        }),
      });
      if (!res.ok) throw new Error('Replay fetch failed');
      const data = await res.json();
      set({
        replayState: {
          isPlaying: false,
          currentFrameIndex: 0,
          frames: data.frames || [],
          flowEvents: data.flow_events || [],
          speed: 1000,
          active: true,
          sourceAccount,
        },
      });
    } catch (err) {
      console.error(err);
    }
  },

  setReplayFrame: (index) => {
    const { replayState } = get();
    if (!replayState.frames.length) return;
    const clamped = Math.max(0, Math.min(replayState.frames.length - 1, index));
    set({
      replayState: {
        ...replayState,
        currentFrameIndex: clamped,
      },
    });
  },

  toggleReplayPlay: () => {
    const { replayState } = get();
    set({
      replayState: {
        ...replayState,
        isPlaying: !replayState.isPlaying,
      },
    });
  },

  stopReplay: () => {
    set({
      replayState: {
        isPlaying: false,
        currentFrameIndex: 0,
        frames: [],
        flowEvents: [],
        speed: 1000,
        active: false,
        sourceAccount: null,
      },
    });
  },

  triggerFreezeSimulation: async (sourceAccount) => {
    try {
      const res = await fetch('/api/freeze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_account: sourceAccount,
          start_time: '2026-10-01T00:00:00Z',
          initial_amount: 100000.0,
        }),
      });
      if (!res.ok) throw new Error('Freeze simulation failed');
      const data = await res.json();
      set({
        freezeSimulationData: data,
        isFreezeModalOpen: true,
      });
    } catch (err) {
      console.error(err);
    }
  },

  closeFreezeModal: () => set({ isFreezeModalOpen: false }),

  openCommandPalette: () => set({ isCommandPaletteOpen: true }),
  closeCommandPalette: () => set({ isCommandPaletteOpen: false }),
  toggleCommandPalette: () => set((s) => ({ isCommandPaletteOpen: !s.isCommandPaletteOpen })),

  openShortcuts: () => set({ isShortcutsOpen: true }),
  closeShortcuts: () => set({ isShortcutsOpen: false }),
  toggleShortcuts: () => set((s) => ({ isShortcutsOpen: !s.isShortcutsOpen })),

  switchPreset: async (presetName) => {
    set({ isLoading: true });
    try {
      const res = await fetch('/api/preset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset: presetName }),
      });
      if (!res.ok) throw new Error('Failed to switch preset');
      const data = await res.json();
      set({ activePreset: presetName, summary: data.summary, isLoading: false });
      // Refresh workspace
      await Promise.all([
        get().fetchAlerts(),
        get().fetchGraph(get().graphCenterId),
        get().fetchRings(),
      ]);
    } catch (err) {
      console.error(err);
      set({ isLoading: false, error: err.message });
    }
  },

  loadDemoData: async () => {
    set({ isLoading: true });
    try {
      const res = await fetch('/api/load-demo', { method: 'POST' });
      if (!res.ok) throw new Error('Failed to load demo data');
      const data = await res.json();
      set({ summary: data.summary, isLoading: false });
      await get().initDashboard();
    } catch (err) {
      console.error(err);
      set({ isLoading: false, error: err.message });
    }
  },

  fetchEarlyWarnings: async () => {
    try {
      const res = await fetch('/api/early-warning');
      if (!res.ok) throw new Error('Failed to fetch early warnings');
      const data = await res.json();
      set({ earlyWarnings: data });
    } catch (err) {
      console.error(err);
    }
  },

  fetchChaseList: async () => {
    try {
      const res = await fetch('/api/chase');
      if (!res.ok) throw new Error('Failed to fetch chase list');
      const data = await res.json();
      set({ chaseList: data });
    } catch (err) {
      console.error(err);
    }
  },

  fetchMetrics: async () => {
    try {
      const res = await fetch('/api/metrics');
      if (!res.ok) throw new Error('Failed to fetch metrics');
      const data = await res.json();
      set({ metrics: data });
    } catch (err) {
      console.error(err);
    }
  },

  fetchEvasionTest: async () => {
    try {
      const res = await fetch('/api/evasion-test');
      if (!res.ok) throw new Error('Failed to fetch evasion test');
      const data = await res.json();
      set({ evasionData: data });
    } catch (err) {
      console.error(err);
    }
  },

  initDashboard: async () => {
    set({ isLoading: true });
    try {
      await Promise.all([
        get().fetchSummary(),
        get().fetchAlerts(),
        get().fetchGraph(),
        get().fetchRings(),
        get().fetchEarlyWarnings(),
        get().fetchChaseList(),
        get().fetchMetrics(),
        get().fetchEvasionTest(),
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      set({ isLoading: false });
    }
  },
}));
