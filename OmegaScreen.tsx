// src/screens/OmegaScreen.tsx
import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import cytoscape from 'cytoscape';
import { useMuleStore } from '../store/useMuleStore';
import { fmtINR, fmtPct } from '../lib/format';
import { 
  Sparkles, 
  Play, 
  Pause, 
  ChevronRight, 
  ChevronLeft, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  AlertCircle, 
  Layers, 
  HelpCircle, 
  CheckCircle2, 
  Eye, 
  RefreshCw, 
  SlidersHorizontal,
  Info
} from 'lucide-react';

interface QuantumWalkData {
  ring_id: string;
  ring_name: string;
  entry_account: string;
  nodes: string[];
  metadata: Record<string, any>;
  time_steps: number[];
  quantum_probabilities: Record<string, number[]>;
  classical_probabilities: Record<string, number[]>;
  flow_quantum: Record<string, number>;
  flow_classical: Record<string, number>;
  t_90_quantum?: number | null;
  t_90_classical?: number | null;
  top_predictions_quantum: string[];
  top_predictions_classical: string[];
  real_exit_accounts: string[];
  overlap_score_quantum: number;
  overlap_score_classical: number;
  disclaimer: string;
}

interface InterdictionData {
  budget_K: number;
  greedy_list: {
    accounts: string[];
    count_frozen: number;
    count_low_risk_frozen: number;
    estimated_saved: number;
    estimated_saved_formatted: string;
  };
  optimized_set: {
    accounts: string[];
    count_frozen: number;
    count_low_risk_frozen: number;
    estimated_saved: number;
    estimated_saved_formatted: string;
  };
  winner: 'optimized' | 'greedy' | 'tie' | string;
  comparison_summary: string;
  solver_diagnostics: Record<string, any>;
  disclaimer: string;
}

interface FidelityData {
  rings: Array<{ ring_id: string; ring_name: string; ring_type: string }>;
  typologies: Array<{ typology_id: string; name: string; description: string }>;
  ring_typology_matrix: number[][];
  ring_ring_matrix: number[][];
  highest_matches: Array<{
    ring_id: string;
    ring_name: string;
    matched_typology_id: string;
    matched_typology_name: string;
    fidelity: number;
    fidelity_pct: string;
    plain_language_reading: string;
  }>;
  disclaimer: string;
}

const STEPS = [
  { id: 1, title: 'Where will the money go?' },
  { id: 2, title: 'Which accounts should we freeze?' },
  { id: 3, title: 'Which rings behave alike?' },
  { id: 4, title: 'Where this goes next.' },
];

/**
 * Maps probability p in [0, 1] to a single-hue sequential scale.
 * Uses brand blue with varying lightness and saturation.
 */
function probToColor(p: number): string {
  const clamped = Math.max(0.0, Math.min(1.0, p));
  // Light tint for low prob -> Deep vivid brand blue for high prob
  if (clamped < 0.01) return 'rgba(56, 189, 248, 0.08)';
  if (clamped < 0.05) return 'rgba(56, 189, 248, 0.25)';
  if (clamped < 0.15) return 'rgba(56, 189, 248, 0.50)';
  if (clamped < 0.30) return 'rgba(56, 189, 248, 0.75)';
  if (clamped < 0.60) return '#0284C7'; // Deep sky blue
  return '#0369A1'; // Dense oceanic blue
}

export const OmegaScreen: React.FC = () => {
  const { rings, presenterMode } = useMuleStore();

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [selectedRingId, setSelectedRingId] = useState<string>('');
  
  // Simulation states
  const [walkData, setWalkData] = useState<QuantumWalkData | null>(null);
  const [interdictData, setInterdictData] = useState<InterdictionData | null>(null);
  const [fidelityData, setFidelityData] = useState<FidelityData | null>(null);
  
  // UI states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTimeIdx, setCurrentTimeIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [budgetK, setBudgetK] = useState<number>(5);
  const [showOnMap, setShowOnMap] = useState<boolean>(false);
  const [showDetails, setShowDetails] = useState<boolean>(false);

  // Cytoscape DOM container refs
  const classicalContainerRef = useRef<HTMLDivElement>(null);
  const quantumContainerRef = useRef<HTMLDivElement>(null);
  const classicalCyRef = useRef<cytoscape.Core | null>(null);
  const quantumCyRef = useRef<cytoscape.Core | null>(null);
  const step2ContainerRef = useRef<HTMLDivElement>(null);
  const step2CyRef = useRef<cytoscape.Core | null>(null);

  // Initialize selected ring
  useEffect(() => {
    if (rings && rings.length > 0 && !selectedRingId) {
      setSelectedRingId(rings[0].ring_id);
    }
  }, [rings, selectedRingId]);

  // Fetch Step 1 & 2 data whenever selected ring changes
  const fetchRingSimulations = useCallback(async (ringId: string, budget: number) => {
    setLoading(true);
    setError(null);
    try {
      const walkUrl = ringId 
        ? `/api/quantum/walk?ring_id=${encodeURIComponent(ringId)}&steps=60`
        : '/api/quantum/walk?steps=60';
      const walkRes = await fetch(walkUrl);
      if (!walkRes.ok) throw new Error(`Walk simulation error (${walkRes.status})`);
      const walkJson = await walkRes.json();
      setWalkData(walkJson);
      setCurrentTimeIdx(0);

      const interdictUrl = ringId
        ? `/api/quantum/interdiction?ring_id=${encodeURIComponent(ringId)}&budget=${budget}`
        : `/api/quantum/interdiction?budget=${budget}`;
      const interdictRes = await fetch(interdictUrl);
      if (!interdictRes.ok) throw new Error(`Interdiction error (${interdictRes.status})`);
      const interdictJson = await interdictRes.json();
      setInterdictData(interdictJson);

      const fidRes = await fetch('/api/quantum/ring-fidelity');
      if (fidRes.ok) {
        const fidJson = await fidRes.json();
        setFidelityData(fidJson);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to compute quantum simulation.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRingSimulations(selectedRingId, budgetK);
  }, [selectedRingId, budgetK, fetchRingSimulations]);

  // Step 1: Animation loop for shared time slider
  useEffect(() => {
    let timer: any = null;
    if (isPlaying && walkData && walkData.time_steps) {
      timer = setInterval(() => {
        setCurrentTimeIdx((prev) => {
          if (prev >= walkData.time_steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 120);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, walkData]);

  // Keyboard navigation for stepper and play toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement)?.tagName)) return;
      if (e.key === 'ArrowRight') {
        setCurrentStep((prev) => Math.min(4, prev + 1));
      } else if (e.key === 'ArrowLeft') {
        setCurrentStep((prev) => Math.max(1, prev - 1));
      } else if (e.key === ' ' && currentStep === 1) {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep]);

  // Cytoscape initialization helper
  const initCytoscape = useCallback((
    container: HTMLElement,
    nodes: string[],
    entryAcc: string,
    metadata: Record<string, any>
  ): cytoscape.Core => {
    const elements: cytoscape.ElementDefinition[] = [];

    nodes.forEach((acc) => {
      const isEntry = acc === entryAcc;
      const isExit = acc.includes('EXIT') || acc.includes('CRYPTO') || acc.includes('ATM');
      elements.push({
        group: 'nodes',
        data: {
          id: acc,
          label: isEntry ? `[Entry] ${acc}` : acc,
          isEntry: isEntry ? 'true' : 'false',
          isExit: isExit ? 'true' : 'false',
        },
      });
    });

    // Ring chain/flow edges
    for (let i = 0; i < nodes.length - 1; i++) {
      elements.push({
        group: 'edges',
        data: {
          id: `e-${nodes[i]}-${nodes[i + 1]}`,
          source: nodes[i],
          target: nodes[i + 1],
        },
      });
    }

    const cy = cytoscape({
      container,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#EAF0FF',
            'font-size': '11px',
            'font-weight': 600,
            'font-family': 'Inter, system-ui, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'text-outline-color': '#0A0F1E',
            'text-outline-width': 2,
            'background-color': 'rgba(56, 189, 248, 0.15)',
            'border-color': 'var(--border-strong)',
            'border-width': 1.5,
            'width': 26,
            'height': 26,
            'transition-property': 'background-color, border-color, border-width, width, height, opacity',
            'transition-duration': '0.15s',
          },
        },
        {
          selector: 'node[isEntry = "true"]',
          style: {
            'shape': 'hexagon',
            'border-color': '#F59E0B',
            'border-width': 2.5,
            'width': 32,
            'height': 32,
          },
        },
        {
          selector: 'node[isExit = "true"]',
          style: {
            'shape': 'diamond',
            'border-color': '#EF4444',
            'border-width': 2,
            'width': 28,
            'height': 28,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': 'var(--border)',
            'target-arrow-color': 'var(--border)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.6,
          },
        },
      ],
      layout: {
        name: 'concentric',
        concentric: (node) => (node.data('isEntry') === 'true' ? 3 : node.data('isExit') === 'true' ? 1 : 2),
        levelWidth: () => 1,
        padding: 20,
        animate: false,
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
    });

    return cy;
  }, []);

  // Initialize both Cytoscape canvases when walk data is ready (Step 1)
  useEffect(() => {
    if (currentStep !== 1) {
      if (classicalCyRef.current) {
        try { classicalCyRef.current.destroy(); } catch (_) {}
        classicalCyRef.current = null;
      }
      if (quantumCyRef.current) {
        try { quantumCyRef.current.destroy(); } catch (_) {}
        quantumCyRef.current = null;
      }
      return;
    }
    if (!walkData || !walkData.nodes || walkData.nodes.length === 0) return;

    if (classicalContainerRef.current) {
      if (classicalCyRef.current) {
        try { classicalCyRef.current.destroy(); } catch (_) {}
      }
      classicalCyRef.current = initCytoscape(
        classicalContainerRef.current,
        walkData.nodes,
        walkData.entry_account,
        walkData.metadata
      );
    }

    if (quantumContainerRef.current) {
      if (quantumCyRef.current) {
        try { quantumCyRef.current.destroy(); } catch (_) {}
      }
      quantumCyRef.current = initCytoscape(
        quantumContainerRef.current,
        walkData.nodes,
        walkData.entry_account,
        walkData.metadata
      );
    }

    return () => {
      if (classicalCyRef.current) {
        try { classicalCyRef.current.destroy(); } catch (_) {}
        classicalCyRef.current = null;
      }
      if (quantumCyRef.current) {
        try { quantumCyRef.current.destroy(); } catch (_) {}
        quantumCyRef.current = null;
      }
    };
  }, [currentStep, walkData, initCytoscape]);

  // Update Cytoscape node colors based on current time step probability (Step 1)
  useEffect(() => {
    if (currentStep !== 1 || !walkData) return;

    // Classical update
    if (classicalCyRef.current && typeof (classicalCyRef.current as any).batch === 'function') {
      try {
        classicalCyRef.current.batch(() => {
          walkData.nodes.forEach((acc) => {
            const probs = walkData.classical_probabilities[acc] || [];
            const p = probs[currentTimeIdx] || 0.0;
            const node = classicalCyRef.current?.getElementById(acc);
            if (node) {
              node.style('background-color', probToColor(p));
              node.style('opacity', Math.max(0.3, Math.min(1.0, 0.35 + p * 1.5)));
            }
          });
        });
      } catch (_) {}
    }

    // Quantum update
    if (quantumCyRef.current && typeof (quantumCyRef.current as any).batch === 'function') {
      try {
        quantumCyRef.current.batch(() => {
          walkData.nodes.forEach((acc) => {
            const probs = walkData.quantum_probabilities[acc] || [];
            const p = probs[currentTimeIdx] || 0.0;
            const node = quantumCyRef.current?.getElementById(acc);
            if (node) {
              node.style('background-color', probToColor(p));
              node.style('opacity', Math.max(0.3, Math.min(1.0, 0.35 + p * 1.5)));
            }
          });
        });
      } catch (_) {}
    }
  }, [currentTimeIdx, walkData, currentStep]);

  // Step 2 Cytoscape map for "Show on map"
  useEffect(() => {
    if (currentStep !== 2 || !showOnMap || !walkData) {
      if (step2CyRef.current) {
        try { step2CyRef.current.destroy(); } catch (_) {}
        step2CyRef.current = null;
      }
      return;
    }

    if (step2ContainerRef.current) {
      if (step2CyRef.current) {
        try { step2CyRef.current.destroy(); } catch (_) {}
      }
      const cy = initCytoscape(
        step2ContainerRef.current,
        walkData.nodes,
        walkData.entry_account,
        walkData.metadata
      );
      step2CyRef.current = cy;
      const optFrozenSet = new Set(interdictData?.optimized_set?.accounts || []);
      try {
        cy.batch(() => {
          walkData.nodes.forEach((acc) => {
            const node = cy.getElementById(acc);
            if (node && optFrozenSet.has(acc)) {
              node.style('border-color', '#F97316');
              node.style('border-width', 3);
              node.style('background-color', 'rgba(249, 115, 22, 0.35)');
            }
          });
        });
      } catch (_) {}
    }

    return () => {
      if (step2CyRef.current) {
        try { step2CyRef.current.destroy(); } catch (_) {}
        step2CyRef.current = null;
      }
    };
  }, [currentStep, showOnMap, walkData, interdictData, initCytoscape]);

  // Selected ring reading for Step 3
  const currentFidelityMatch = useMemo(() => {
    if (!fidelityData || !fidelityData.highest_matches) return null;
    return (
      fidelityData.highest_matches.find((m) => m.ring_id === selectedRingId) ||
      fidelityData.highest_matches[0]
    );
  }, [fidelityData, selectedRingId]);

  return (
    <div 
      className="omega-screen"
      style={{
        width: '100%',
        minHeight: '100%',
        backgroundColor: 'var(--bg-0)',
        color: 'var(--text-1)',
        padding: 'var(--s-5) var(--s-4)',
        overflowY: 'auto',
      }}
    >
      <div 
        style={{
          maxWidth: '1100px',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '28px',
        }}
      >
        {/* ================================================================= */}
        {/* TOP SECTION: Title, Premise, Disclaimer, Ring Selector             */}
        {/* ================================================================= */}
        <header 
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            borderBottom: '1px solid var(--border)',
            paddingBottom: '20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '36px',
                  height: '36px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--brand-bg)',
                  color: 'var(--brand)',
                  fontWeight: 800,
                  fontSize: '20px',
                }}
              >
                Ω
              </div>
              <div>
                <h1 style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-1)' }}>
                  MuleTrace Ω
                </h1>
                <p style={{ fontSize: '16px', color: 'var(--text-2)', marginTop: '2px' }}>
                  What if we could see where stolen money will go before it gets there?
                </p>
              </div>
            </div>

            {/* Ring Selector Dropdown */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label htmlFor="omega-ring-select" style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-3)' }}>
                Investigation Target:
              </label>
              <select
                id="omega-ring-select"
                value={selectedRingId}
                onChange={(e) => setSelectedRingId(e.target.value)}
                style={{
                  backgroundColor: 'var(--bg-2)',
                  color: 'var(--text-1)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '6px 12px',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {rings && rings.length > 0 ? (
                  rings.map((r) => (
                    <option key={r.ring_id} value={r.ring_id}>
                      {r.ring_id}: {r.ring_name}
                    </option>
                  ))
                ) : (
                  <option value="">Default Investigation Ring</option>
                )}
              </select>
            </div>
          </div>

          {/* Mandatory Honesty Rule Disclaimer */}
          <div 
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13px',
              fontWeight: 500,
              color: 'var(--text-3)',
              backgroundColor: 'var(--bg-1)',
              padding: '6px 12px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border)',
              width: 'fit-content',
            }}
          >
            <Info size={14} style={{ color: 'var(--brand)' }} />
            <span>Simulated on a classical computer. Synthetic demonstration data. Not a real case.</span>
          </div>
        </header>

        {/* ================================================================= */}
        {/* HORIZONTAL 4-STEP STEPPER                                         */}
        {/* ================================================================= */}
        <nav 
          role="tablist" 
          aria-label="Omega Analysis Steps"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px',
            backgroundColor: 'var(--bg-1)',
            padding: '6px',
            borderRadius: 'var(--radius)',
            border: '1px solid var(--border)',
          }}
        >
          {STEPS.map((step) => {
            const isActive = currentStep === step.id;
            return (
              <button
                key={step.id}
                role="tab"
                type="button"
                aria-selected={isActive}
                onClick={() => setCurrentStep(step.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 14px',
                  borderRadius: 'calc(var(--radius) - 4px)',
                  backgroundColor: isActive ? 'var(--brand-bg)' : 'transparent',
                  border: isActive ? '1px solid var(--brand)' : '1px solid transparent',
                  color: isActive ? 'var(--text-1)' : 'var(--text-2)',
                  fontSize: '15px',
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                }}
              >
                <span 
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '22px',
                    height: '22px',
                    borderRadius: '50%',
                    backgroundColor: isActive ? 'var(--brand)' : 'var(--bg-2)',
                    color: isActive ? 'var(--bg-0)' : 'var(--text-3)',
                    fontSize: '12px',
                    fontWeight: 800,
                  }}
                >
                  {step.id}
                </span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {step.title}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Loading / Error States */}
        {loading && (
          <div 
            style={{
              padding: '48px',
              textAlign: 'center',
              backgroundColor: 'var(--bg-1)',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <RefreshCw size={24} className="spin-slow" style={{ color: 'var(--brand)' }} />
            <p style={{ fontSize: '16px', color: 'var(--text-2)' }}>
              Computing graph simulation and probability distributions...
            </p>
          </div>
        )}

        {error && !loading && (
          <div 
            style={{
              padding: '24px',
              backgroundColor: 'var(--bg-1)',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--sev-critical)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={20} style={{ color: 'var(--sev-critical)' }} />
              <p style={{ fontSize: '15px', color: 'var(--text-1)' }}>{error}</p>
            </div>
            <button
              type="button"
              onClick={() => fetchRingSimulations(selectedRingId, budgetK)}
              style={{
                padding: '6px 14px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--brand)',
                color: 'var(--bg-0)',
                fontWeight: 600,
                fontSize: '14px',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* ================================================================= */}
        {/* STEP 1: "Where will the money go?"                                */}
        {/* ================================================================= */}
        {!loading && !error && currentStep === 1 && walkData && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Control Row: Time Slider & Legend */}
            <div 
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
                backgroundColor: 'var(--bg-1)',
                padding: '12px 16px',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: '260px' }}>
                <button
                  type="button"
                  aria-label={isPlaying ? 'Pause simulation' : 'Play simulation'}
                  onClick={() => setIsPlaying(!isPlaying)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '36px',
                    height: '36px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--brand)',
                    color: 'var(--bg-0)',
                    border: 'none',
                    cursor: 'pointer',
                  }}
                >
                  {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                </button>

                <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-1)' }}>
                      Simulation Time: {walkData.time_steps[currentTimeIdx] || 0}s
                    </span>
                    <span style={{ color: 'var(--text-3)' }}>
                      Step {currentTimeIdx + 1} of {walkData.time_steps.length}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={walkData.time_steps.length - 1}
                    value={currentTimeIdx}
                    onChange={(e) => {
                      setIsPlaying(false);
                      setCurrentTimeIdx(Number(e.target.value));
                    }}
                    aria-label="Simulation time slider"
                    style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--brand)' }}
                  />
                </div>
              </div>

              {/* Single-hue sequential scale legend */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-3)' }}>
                <span>0.0 (low)</span>
                <div 
                  style={{
                    width: '90px',
                    height: '10px',
                    borderRadius: '4px',
                    background: 'linear-gradient(to right, rgba(56, 189, 248, 0.1), #0369A1)',
                    border: '1px solid var(--border)',
                  }}
                />
                <span>1.0 (concentrated)</span>
              </div>
            </div>

            {/* Primary Visual: Side-by-side Cytoscape Canvases */}
            <div 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '16px',
              }}
            >
              {/* Classical Pane */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <div 
                  style={{
                    padding: '10px 16px',
                    borderBottom: '1px solid var(--border)',
                    backgroundColor: 'var(--bg-2)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-1)' }}>
                    Classical Method (Laplacian Diffusion)
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>Baseline flow</span>
                </div>
                <div 
                  ref={classicalContainerRef}
                  style={{ width: '100%', height: '320px', position: 'relative' }}
                />
              </div>

              {/* Quantum Walk Pane */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <div 
                  style={{
                    padding: '10px 16px',
                    borderBottom: '1px solid var(--border)',
                    backgroundColor: 'var(--bg-2)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--brand)' }}>
                    Quantum Walk (Continuous-Time Simulation)
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>Wave propagation</span>
                </div>
                <div 
                  ref={quantumContainerRef}
                  style={{ width: '100%', height: '320px', position: 'relative' }}
                />
              </div>
            </div>

            {/* Exactly 3 KPI Cards under the canvases */}
            <div 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '16px',
              }}
            >
              {/* Card 1: Predicted Exit Accounts */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <span className="label">Predicted Exit Accounts</span>
                <div style={{ fontSize: '15px', color: 'var(--text-1)', fontWeight: 600 }}>
                  <div>Quantum: {walkData.top_predictions_quantum.slice(0, 3).join(', ') || 'None'}</div>
                  <div style={{ color: 'var(--text-3)', fontWeight: 500, marginTop: '2px' }}>
                    Classical: {walkData.top_predictions_classical.slice(0, 3).join(', ') || 'None'}
                  </div>
                </div>
              </div>

              {/* Card 2: Overlap with Real Exits */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <span className="label">Overlap with Real Exits</span>
                <div style={{ fontSize: '18px', color: 'var(--text-1)', fontWeight: 800 }}>
                  <span style={{ color: 'var(--brand)' }}>
                    {(walkData.overlap_score_quantum * 100).toFixed(1)}% (Quantum)
                  </span>
                  <span style={{ color: 'var(--text-3)', fontSize: '14px', fontWeight: 500, marginLeft: '8px' }}>
                    vs {(walkData.overlap_score_classical * 100).toFixed(1)}% (Classical)
                  </span>
                </div>
                <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>
                  Computed against {walkData.real_exit_accounts.length} actual exit accounts in data
                </span>
              </div>

              {/* Card 3: Dispersion Speed (Time to 90% Mass) */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <span className="label">Dispersion Speed (90% Mass)</span>
                <div style={{ fontSize: '18px', color: 'var(--text-1)', fontWeight: 800 }}>
                  <span>
                    Quantum: {walkData.t_90_quantum != null ? `${walkData.t_90_quantum}s` : 'Not reached'}
                  </span>
                </div>
                <span style={{ fontSize: '13px', color: 'var(--text-3)' }}>
                  Classical: {walkData.t_90_classical != null ? `${walkData.t_90_classical}s` : 'Not reached'}
                </span>
              </div>
            </div>

            {/* Collapsed "How it works" panel */}
            {!presenterMode && (
              <details 
                className="omega-how-it-works"
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '14px 18px',
                  fontSize: '14px',
                  color: 'var(--text-2)',
                }}
              >
                <summary style={{ fontWeight: 700, cursor: 'pointer', color: 'var(--text-1)' }}>
                  How it works (Technical formulation & theory)
                </summary>
                <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', lineHeight: 1.6 }}>
                  <p>
                    <strong>Continuous-Time Quantum Walk:</strong> The Hamiltonian <code>H = A</code> is set to the symmetric weighted adjacency matrix, where edge weights equal <code>log(1 + amount)</code>. The state evolves unitarily via <code>U(t) = V exp(-i·Λ·t) V†</code>, where <code>V</code> and <code>Λ</code> are obtained from <code>numpy.linalg.eigh</code>. Probability per account is <code>p_i(t) = |ψ_i(t)|²</code>.
                  </p>
                  <p>
                    <strong>Classical Comparison:</strong> Continuous diffusion obeys <code>p(t) = exp(-L·t)·p0</code>, where <code>L = D - A</code> is the graph Laplacian.
                  </p>
                  <p style={{ fontStyle: 'italic', color: 'var(--text-3)' }}>
                    Theoretical note: In theory, continuous-time quantum walks on ideal fault-tolerant quantum hardware can traverse specific graph structures quadratically or exponentially faster than classical random walks. However, this implementation is a classical simulation; in physical quantum architectures, loading classical transaction matrices into quantum RAM (QRAM) remains an open hardware challenge.
                  </p>
                </div>
              </details>
            )}
          </section>
        )}

        {/* ================================================================= */}
        {/* STEP 2: "Which accounts should we freeze?"                          */}
        {/* ================================================================= */}
        {!loading && !error && currentStep === 2 && interdictData && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Control Row: Budget Slider & Map Highlight Toggle */}
            <div 
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
                backgroundColor: 'var(--bg-1)',
                padding: '12px 16px',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1, minWidth: '280px' }}>
                <SlidersHorizontal size={18} style={{ color: 'var(--brand)' }} />
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', fontWeight: 600 }}>
                    <span>Freeze Intervention Budget (K):</span>
                    <span style={{ color: 'var(--brand)' }}>{budgetK} accounts</span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={12}
                    value={budgetK}
                    onChange={(e) => setBudgetK(Number(e.target.value))}
                    aria-label="Account freeze budget K"
                    style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--brand)' }}
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={() => setShowOnMap(!showOnMap)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: showOnMap ? 'var(--brand)' : 'var(--bg-2)',
                  color: showOnMap ? 'var(--bg-0)' : 'var(--text-1)',
                  border: '1px solid var(--border)',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                <Eye size={16} />
                <span>{showOnMap ? 'Hide map highlights' : 'Show on map'}</span>
              </button>
            </div>

            {/* Optional Map Visual if toggled */}
            {showOnMap && walkData && (
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  overflow: 'hidden',
                  padding: '12px',
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px', color: 'var(--text-2)' }}>
                  Highlighted accounts in orange border represent the simulated annealing freeze set:
                </div>
                <div ref={step2ContainerRef} style={{ width: '100%', height: '260px' }} />
              </div>
            )}

            {/* Two simple columns: Greedy List vs Optimized Set */}
            <div 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '20px',
              }}
            >
              {/* Column 1: Greedy List */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-1)' }}>
                    Greedy List
                  </h3>
                  {interdictData.winner === 'greedy' && (
                    <span 
                      style={{
                        fontSize: '12px',
                        fontWeight: 700,
                        backgroundColor: 'var(--brand-bg)',
                        color: 'var(--brand)',
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--brand)',
                      }}
                    >
                      Recommended by funds saved
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-1)' }}>
                    {interdictData.greedy_list.estimated_saved_formatted}
                  </div>
                  <div style={{ fontSize: '14px', color: 'var(--text-2)' }}>
                    Accounts frozen: <strong>{interdictData.greedy_list.count_frozen}</strong>
                  </div>
                  <div style={{ fontSize: '14px', color: 'var(--text-2)' }}>
                    Low-risk accounts frozen: <strong>{interdictData.greedy_list.count_low_risk_frozen}</strong>
                  </div>
                </div>

                <div style={{ fontSize: '13px', color: 'var(--text-3)', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
                  Targeted accounts: {interdictData.greedy_list.accounts.join(', ') || 'None'}
                </div>
              </div>

              {/* Column 2: Optimized Set */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: interdictData.winner === 'optimized' ? '1px solid var(--brand)' : '1px solid var(--border)',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--brand)' }}>
                    Optimized Set (QUBO)
                  </h3>
                  {interdictData.winner === 'optimized' && (
                    <span 
                      style={{
                        fontSize: '12px',
                        fontWeight: 700,
                        backgroundColor: 'var(--brand-bg)',
                        color: 'var(--brand)',
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--brand)',
                      }}
                    >
                      Recommended: Better trade-off
                    </span>
                  )}
                  {interdictData.winner === 'tie' && (
                    <span 
                      style={{
                        fontSize: '12px',
                        fontWeight: 600,
                        backgroundColor: 'var(--bg-2)',
                        color: 'var(--text-2)',
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-sm)',
                      }}
                    >
                      Methods tied
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-1)' }}>
                    {interdictData.optimized_set.estimated_saved_formatted}
                  </div>
                  <div style={{ fontSize: '14px', color: 'var(--text-2)' }}>
                    Accounts frozen: <strong>{interdictData.optimized_set.count_frozen}</strong>
                  </div>
                  <div style={{ fontSize: '14px', color: 'var(--text-2)' }}>
                    Low-risk accounts frozen: <strong>{interdictData.optimized_set.count_low_risk_frozen}</strong>
                  </div>
                </div>

                <div style={{ fontSize: '13px', color: 'var(--text-3)', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
                  Targeted accounts: {interdictData.optimized_set.accounts.join(', ') || 'None'}
                </div>
              </div>
            </div>

            {/* Diagnostic Details Toggle */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setShowDetails(!showDetails)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--brand)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  width: 'fit-content',
                }}
              >
                {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                <span>{showDetails ? 'Hide solver diagnostics' : 'Show solver diagnostics'}</span>
              </button>

              {showDetails && (
                <div 
                  style={{
                    backgroundColor: 'var(--bg-2)',
                    padding: '12px 16px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '13px',
                    color: 'var(--text-2)',
                    display: 'flex',
                    gap: '24px',
                    flexWrap: 'wrap',
                  }}
                >
                  <span>Initial Energy: {interdictData.solver_diagnostics?.initial_energy}</span>
                  <span>Final Energy: {interdictData.solver_diagnostics?.final_energy}</span>
                  <span>Iterations: {interdictData.solver_diagnostics?.iterations}</span>
                  <span>Seed: {interdictData.solver_diagnostics?.seed} (Deterministic)</span>
                  <span>Summary: {interdictData.comparison_summary}</span>
                </div>
              )}
            </div>

            {/* Collapsed "How it works" panel */}
            {!presenterMode && (
              <details 
                className="omega-how-it-works"
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '14px 18px',
                  fontSize: '14px',
                  color: 'var(--text-2)',
                }}
              >
                <summary style={{ fontWeight: 700, cursor: 'pointer', color: 'var(--text-1)' }}>
                  How it works (QUBO formulation & simulated annealing)
                </summary>
                <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', lineHeight: 1.6 }}>
                  <p>
                    <strong>Binary Optimization:</strong> Each account has a binary choice <code>x_i in {'{0, 1}'}</code>, where 1 means freeze. The objective minimizes escaping flow plus collateral damage on low-risk accounts:
                  </p>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', padding: '6px 10px', backgroundColor: 'var(--bg-2)', borderRadius: '4px' }}>
                    min E(x) = λ1·Σ(1 - x_i)·flow_i + λ2·Σ x_i·innocence_cost_i + μ·(Σ x_i - K)²
                  </p>
                  <p>
                    <strong>Victim Protection Invariant:</strong> Victim accounts are strictly constrained to <code>x_victim = 0</code> and can never be selected for freezing.
                  </p>
                  <p>
                    <strong>Deterministic Solver:</strong> Solved on classical CPU via simulated annealing with a fixed seed (42) and Metropolis acceptance criterion.
                  </p>
                </div>
              </details>
            )}
          </section>
        )}

        {/* ================================================================= */}
        {/* STEP 3: "Which rings behave alike?"                                */}
        {/* ================================================================= */}
        {!loading && !error && currentStep === 3 && fidelityData && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ fontSize: '16px', color: 'var(--text-2)' }}>
              Compare behavioral signatures between detected fraud syndicates and standardized crime patterns.
            </div>

            {/* Fidelity Heat Table */}
            <div 
              style={{
                backgroundColor: 'var(--bg-1)',
                borderRadius: 'var(--radius)',
                border: '1px solid var(--border)',
                overflowX: 'auto',
                padding: '16px',
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center', fontSize: '14px' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '10px 14px', color: 'var(--text-3)', fontWeight: 600 }}>
                      Fraud Ring
                    </th>
                    {fidelityData.typologies.map((t) => (
                      <th 
                        key={t.typology_id}
                        title={t.description}
                        style={{ padding: '10px 14px', color: 'var(--text-2)', fontWeight: 600, maxWidth: '140px' }}
                      >
                        {t.name.split(' (')[0]}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {fidelityData.rings.map((ring, rIdx) => {
                    const rowVals = fidelityData.ring_typology_matrix[rIdx] || [];
                    const isSelected = ring.ring_id === selectedRingId;
                    return (
                      <tr 
                        key={ring.ring_id}
                        onClick={() => setSelectedRingId(ring.ring_id)}
                        style={{
                          backgroundColor: isSelected ? 'var(--brand-bg)' : 'transparent',
                          cursor: 'pointer',
                          borderTop: '1px solid var(--border)',
                          transition: 'background-color 0.15s ease',
                        }}
                      >
                        <td style={{ textAlign: 'left', padding: '12px 14px', fontWeight: 600, color: isSelected ? 'var(--brand)' : 'var(--text-1)' }}>
                          {ring.ring_name}
                        </td>
                        {rowVals.map((val, cIdx) => {
                          const pct = (val * 100).toFixed(1) + '%';
                          const alpha = Math.max(0.08, val * 0.45);
                          return (
                            <td 
                              key={cIdx}
                              style={{
                                padding: '12px 14px',
                                fontFamily: 'var(--font-mono)',
                                fontWeight: 700,
                                backgroundColor: `rgba(56, 189, 248, ${alpha})`,
                                color: 'var(--text-1)',
                              }}
                            >
                              {pct}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* One-sentence plain-language reading of highest match */}
            {currentFidelityMatch && (
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                }}
              >
                <CheckCircle2 size={20} style={{ color: 'var(--brand)', flexShrink: 0 }} />
                <p style={{ fontSize: '15px', color: 'var(--text-1)', lineHeight: 1.5 }}>
                  {currentFidelityMatch.plain_language_reading}
                </p>
              </div>
            )}

            {/* Collapsed "How it works" panel */}
            {!presenterMode && (
              <details 
                className="omega-how-it-works"
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '14px 18px',
                  fontSize: '14px',
                  color: 'var(--text-2)',
                }}
              >
                <summary style={{ fontWeight: 700, cursor: 'pointer', color: 'var(--text-1)' }}>
                  How it works (Quantum state fidelity & cosine² identity)
                </summary>
                <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', lineHeight: 1.6 }}>
                  <p>
                    <strong>State Fidelity:</strong> In quantum information, the transition probability between two pure quantum states |a⟩ and |b⟩ is given by fidelity <code>F(|a⟩, |b⟩) = |⟨a|b⟩|²</code>.
                  </p>
                  <p>
                    <strong>Equivalence to Cosine²:</strong> Because each ring’s 6D Ring DNA features (network size, duration velocity, hop gap, retained ratio, drain ratio) are non-negative real numbers, normalizing them to unit length yields <code>|⟨a|b⟩|² = (cos θ)²</code>. This measures geometric alignment in state space with quadratic contrast against spurious correlations.
                  </p>
                </div>
              </details>
            )}
          </section>
        )}

        {/* ================================================================= */}
        {/* STEP 4: "Where this goes next."                                   */}
        {/* ================================================================= */}
        {!loading && !error && currentStep === 4 && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ fontSize: '16px', color: 'var(--text-2)' }}>
              Future engineering horizons for anti-money laundering and graph analytics.
            </div>

            {/* Three short text-only cards */}
            <div 
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '20px',
              }}
            >
              {/* Card A: Why quantum */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-1)' }}>
                  Why Quantum
                </h3>
                <p style={{ fontSize: '15px', color: 'var(--text-2)', lineHeight: 1.6 }}>
                  For N accounts, an ideal quantum state needs about <strong>log₂(N) qubits</strong>. A national banking network of 100 million accounts maps to roughly <strong>27 qubits</strong>. However, loading classical transaction ledgers into quantum states (QRAM) and reading out results without collapsing the state remain unsolved hardware engineering problems.
                </p>
              </div>

              {/* Card B: Detector that can't be gamed */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-1)' }}>
                  Detector That Can't Be Gamed
                </h3>
                <p style={{ fontSize: '15px', color: 'var(--text-2)', lineHeight: 1.6 }}>
                  Today's syndicates reverse-engineer deterministic rule thresholds (like waiting 31 minutes to beat a 30-minute window). Randomized quantum probes could detect cyclic routing and fan-outs based on continuous wave interference rather than static cutoffs. <em>(Described as a research exploration, not currently implemented).</em>
                </p>
              </div>

              {/* Card C: The arms race */}
              <div 
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-1)' }}>
                  The Arms Race
                </h3>
                <p style={{ fontSize: '15px', color: 'var(--text-2)', lineHeight: 1.6 }}>
                  Financial defense systems must prepare now: criminal syndicates and nation-state laundering networks will eventually deploy quantum optimization algorithms to compute minimum-detectability dispersal pathways through legitimate payment rails.
                </p>
              </div>
            </div>

            {/* Collapsed "How it works" panel */}
            {!presenterMode && (
              <details 
                className="omega-how-it-works"
                style={{
                  backgroundColor: 'var(--bg-1)',
                  borderRadius: 'var(--radius)',
                  border: '1px solid var(--border)',
                  padding: '14px 18px',
                  fontSize: '14px',
                  color: 'var(--text-2)',
                }}
              >
                <summary style={{ fontWeight: 700, cursor: 'pointer', color: 'var(--text-1)' }}>
                  How it works (Complexity theory & timeline context)
                </summary>
                <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px', lineHeight: 1.6 }}>
                  <p>
                    Graph isomorphism, Hamiltonian cycles, and optimal network interdiction belong to hard complexity classes. While quantum algorithms (such as QAOA and quantum walks) offer polynomial or quadratic speedups for certain graph problems, practical deployment depends on fault-tolerant quantum error correction and coherent quantum memory.
                  </p>
                </div>
              </details>
            )}
          </section>
        )}

        {/* Stepper Navigation Footer */}
        <footer 
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderTop: '1px solid var(--border)',
            paddingTop: '20px',
            marginTop: '8px',
          }}
        >
          <button
            type="button"
            disabled={currentStep === 1}
            onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--bg-2)',
              color: currentStep === 1 ? 'var(--text-3)' : 'var(--text-1)',
              border: '1px solid var(--border)',
              fontWeight: 600,
              fontSize: '14px',
              cursor: currentStep === 1 ? 'not-allowed' : 'pointer',
              opacity: currentStep === 1 ? 0.5 : 1,
            }}
          >
            <ChevronLeft size={16} />
            <span>Previous Step</span>
          </button>

          <span style={{ fontSize: '14px', color: 'var(--text-3)', fontWeight: 500 }}>
            Step {currentStep} of 4 — Use arrow keys to navigate
          </span>

          <button
            type="button"
            disabled={currentStep === 4}
            onClick={() => setCurrentStep((prev) => Math.min(4, prev + 1))}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: currentStep === 4 ? 'var(--bg-2)' : 'var(--brand)',
              color: currentStep === 4 ? 'var(--text-3)' : 'var(--bg-0)',
              border: 'none',
              fontWeight: 600,
              fontSize: '14px',
              cursor: currentStep === 4 ? 'not-allowed' : 'pointer',
              opacity: currentStep === 4 ? 0.5 : 1,
            }}
          >
            <span>Next Step</span>
            <ChevronRight size={16} />
          </button>
        </footer>
      </div>
    </div>
  );
};

export default OmegaScreen;
