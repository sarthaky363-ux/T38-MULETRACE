// src/components/GraphPane.tsx
import React, { useEffect, useLayoutEffect, useRef, useState, useCallback } from 'react';
import cytoscape from 'cytoscape';
import { useMuleStore } from '../store/useMuleStore';
import { SeverityBadge } from './ui';
import { fmtINR } from '../lib/format';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  RotateCw, 
  Play, 
  Layers, 
  ShieldAlert, 
  AlertTriangle,
  CheckCircle,
  X,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Eye,
  Circle,
  Target,
  Network
} from 'lucide-react';

type Status = "loading" | "ready" | "empty" | "error";

export type GraphLayoutType = 'circle' | 'concentric' | 'cose';

export interface GraphPaneProps {
  data?: { nodes: any[]; edges: any[] };
  selectedId?: string | null;
  onSelectNode?: (nodeId: string) => void;
}

export function getLayoutConfig(
  layoutType: GraphLayoutType,
  centerId?: string | null,
  animate = false
): any {
  if (centerId) {
    return {
      name: 'concentric',
      concentric: (node: any) => (node.id() === centerId ? 10 : 2),
      levelWidth: () => 1,
      fit: true,
      padding: 40,
      animate,
      animationDuration: 400,
    };
  }

  if (layoutType === 'circle') {
    return {
      name: 'circle',
      fit: true,
      padding: 45,
      avoidOverlap: true,
      animate,
      animationDuration: 400,
      sort: (a: any, b: any) => {
        const order: Record<string, number> = { hub: 1, victim: 2, relay: 3, exit: 4, member: 5 };
        const rA = order[a.data('role')] || 99;
        const rB = order[b.data('role')] || 99;
        if (rA !== rB) return rA - rB;
        return (b.data('risk_score') || 0) - (a.data('risk_score') || 0);
      },
    };
  }

  if (layoutType === 'concentric') {
    return {
      name: 'concentric',
      concentric: (node: any) => {
        const role = node.data('role');
        if (role === 'hub' || role === 'victim') return 4;
        if (role === 'relay') return 3;
        if (role === 'exit') return 1;
        const score = node.data('risk_score') || 0;
        return score >= 60 ? 3 : 2;
      },
      levelWidth: () => 1,
      fit: true,
      padding: 45,
      minNodeSpacing: 35,
      animate,
      animationDuration: 400,
    };
  }

  // cose force-directed
  return {
    name: 'cose',
    fit: true,
    padding: 40,
    nodeRepulsion: () => 12000,
    idealEdgeLength: () => 60,
    animate,
    animationDuration: 400,
    randomize: false,
  };
}

/**
 * Initializes and renders the Cytoscape graph.
 * Returns a cleanup function that invokes cy.destroy().
 */
function renderCytoscape(
  container: HTMLElement,
  data: { nodes: any[]; edges: any[] },
  options: {
    width: number;
    height: number;
    selectedId?: string | null;
    onSelectNode?: (nodeId: string) => void;
    onSelectEdge?: (edgeData: any) => void;
    centerId?: string | null;
    layoutType?: GraphLayoutType;
  }
): { destroy: () => void; cy: cytoscape.Core } {
  const stylesheet: cytoscape.Stylesheet[] = [
    // Base node
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'color': '#EAF0FF',
        'font-size': '12px',
        'font-weight': 600,
        'font-family': 'Inter, system-ui, sans-serif',
        'text-valign': 'bottom',
        'text-margin-y': 6,
        'text-outline-color': '#0A0F1E',
        'text-outline-width': 2,
        'background-color': '#38BDF8',
        'width': 28,
        'height': 28,
        'transition-property': 'background-color, border-color, border-width, width, height, opacity',
        'transition-duration': '0.2s',
      }
    },
    // Node role shapes
    {
      selector: 'node[role = "hub"]',
      style: {
        'shape': 'hexagon',
        'width': 36,
        'height': 36,
      }
    },
    {
      selector: 'node[role = "relay"]',
      style: {
        'shape': 'rectangle',
        'width': 30,
        'height': 30,
      }
    },
    {
      selector: 'node[role = "exit"]',
      style: {
        'shape': 'diamond',
        'width': 34,
        'height': 34,
      }
    },
    {
      selector: 'node[role = "victim"]',
      style: {
        'shape': 'round-diamond',
        'width': 32,
        'height': 32,
      }
    },
    {
      selector: 'node[role = "member"]',
      style: {
        'shape': 'ellipse',
      }
    },
    // Node risk band colors
    {
      selector: 'node[risk_band = "critical"]',
      style: {
        'background-color': '#FF5C6C',
      }
    },
    {
      selector: 'node[risk_band = "medium"]',
      style: {
        'background-color': '#FFB020',
      }
    },
    {
      selector: 'node[risk_band = "safe"]',
      style: {
        'background-color': '#34D399',
      }
    },
    // Selected node state
    {
      selector: 'node:selected, node.selected',
      style: {
        'border-width': 4,
        'border-color': '#FFFFFF',
        'underlay-color': '#38BDF8',
        'underlay-padding': 4,
        'underlay-opacity': 0.45,
      }
    },
    // Neighbourhood focus and fade
    {
      selector: 'node.highlighted',
      style: {
        'opacity': 1,
      }
    },
    {
      selector: 'node.faded',
      style: {
        'opacity': 0.2,
      }
    },
    // Edges
    {
      selector: 'edge',
      style: {
        'width': 'mapData(amount, 1000, 500000, 1.5, 6)',
        'line-color': 'rgba(91, 192, 235, 0.45)',
        'target-arrow-color': 'rgba(91, 192, 235, 0.65)',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'arrow-scale': 0.85,
        'transition-property': 'line-color, opacity, width',
        'transition-duration': '0.2s',
      }
    },
    {
      selector: 'edge[?tainted]',
      style: {
        'line-color': '#FF5C6C',
        'target-arrow-color': '#FF5C6C',
        'line-style': 'solid',
        'width': 'mapData(amount, 1000, 500000, 2, 7)',
      }
    },
    {
      selector: 'edge.highlighted',
      style: {
        'opacity': 1,
        'line-color': '#38BDF8',
        'target-arrow-color': '#38BDF8',
      }
    },
    {
      selector: 'edge.faded',
      style: {
        'opacity': 0.12,
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#FFFFFF',
        'target-arrow-color': '#FFFFFF',
        'width': 5,
      }
    }
  ];

  const cy = cytoscape({
    container,
    elements: [
      ...(data.nodes || []),
      ...(data.edges || [])
    ],
    style: stylesheet,
    layout: { name: 'preset' },
    minZoom: 0.15,
    maxZoom: 4.0,
    wheelSensitivity: 0.25,
  });

  // Run layout with reference to stop on unmount
  let activeLayout: any = null;
  try {
    const layoutConfig = getLayoutConfig(options.layoutType || 'circle', options.centerId, false);
    activeLayout = cy.layout(layoutConfig);
    activeLayout.run();
  } catch (err) {
    console.warn("[GraphPane] layout run error", err);
  }

  // Tap node
  cy.on('tap', 'node', (evt) => {
    const node = evt.target;
    if (options.onSelectNode) {
      options.onSelectNode(node.id());
    }
  });

  // Tap edge
  cy.on('tap', 'edge', (evt) => {
    const edge = evt.target;
    if (options.onSelectEdge) {
      options.onSelectEdge(edge.data());
    }
  });

  // Background tap
  cy.on('tap', (evt) => {
    if (evt.target === cy && options.onSelectEdge) {
      options.onSelectEdge(null);
    }
  });

  // Apply neighborhood highlight if selectedId present
  if (options.selectedId) {
    const target = cy.getElementById(options.selectedId);
    if (target.length > 0) {
      target.select();
      const neighborhood = target.neighborhood().add(target);
      cy.elements().difference(neighborhood).addClass('faded');
      neighborhood.addClass('highlighted');
    }
  }

  return {
    cy,
    destroy: () => {
      try {
        if (activeLayout) {
          activeLayout.stop();
        }
        cy.stop();
        cy.elements().stop();
        cy.removeAllListeners();
        cy.destroy();
      } catch (err) {
        // ignore already destroyed
      }
    }
  };
}

export function GraphPane({
  data: propData,
  selectedId: propSelectedId,
  onSelectNode: propOnSelectNode,
}: GraphPaneProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const cyInstanceRef = useRef<cytoscape.Core | null>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [status, setStatus] = useState<Status>("loading");
  const [attempt, setAttempt] = useState(0);
  const [showLegend, setShowLegend] = useState(true);
  const [selectedEdgeData, setSelectedEdgeData] = useState<any>(null);
  const [layoutType, setLayoutType] = useState<GraphLayoutType>('circle');

  const store = useMuleStore();
  const data = propData ?? store.graphData;
  const selectedId = propSelectedId !== undefined ? propSelectedId : store.selectedAccountId;
  const onSelectNode = propOnSelectNode ?? store.selectAccount;
  const graphCenterId = store.graphCenterId;

  // 1. Observe real pixel size
  useLayoutEffect(() => {
    const el = hostRef.current;
    if (!el) return;

    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) {
        setSize({ w: Math.round(width), h: Math.round(height) });
      }
    });

    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // 2. Cytoscape graph lifecycle
  useEffect(() => {
    if (!size.w || !size.h) return; // NEVER init a graph at 0x0

    if (!data || !data.nodes || data.nodes.length === 0) {
      setStatus("empty");
      return;
    }

    let cleanup: undefined | (() => void);
    try {
      setStatus("loading");
      const { destroy, cy } = renderCytoscape(hostRef.current!, data, {
        width: size.w,
        height: size.h,
        selectedId,
        onSelectNode,
        onSelectEdge: setSelectedEdgeData,
        centerId: graphCenterId,
        layoutType,
      });

      cyInstanceRef.current = cy;
      cleanup = destroy;
      setStatus("ready");
    } catch (err) {
      console.error("[GraphPane]", err);
      setStatus("error");
    }

    return () => {
      cleanup?.();
      cyInstanceRef.current = null;
    };
  }, [data, size.w, size.h, selectedId, graphCenterId, attempt, layoutType]);

  // Controls
  const handleZoomIn = () => {
    if (cyInstanceRef.current) {
      cyInstanceRef.current.zoom(cyInstanceRef.current.zoom() * 1.25);
    }
  };

  const handleZoomOut = () => {
    if (cyInstanceRef.current) {
      cyInstanceRef.current.zoom(cyInstanceRef.current.zoom() * 0.8);
    }
  };

  const handleFit = () => {
    if (cyInstanceRef.current) {
      cyInstanceRef.current.fit(undefined, 35);
    }
  };

  const applyLayout = (type: GraphLayoutType) => {
    if (cyInstanceRef.current) {
      try {
        const config = getLayoutConfig(type, graphCenterId, true);
        const layout = cyInstanceRef.current.layout(config);
        layout.run();
      } catch (err) {
        console.warn("[GraphPane] applyLayout error", err);
      }
    }
  };

  const handleSelectLayout = (type: GraphLayoutType) => {
    setLayoutType(type);
    applyLayout(type);
  };

  const handleReset = () => {
    applyLayout(layoutType);
  };

  const handleReplay = () => {
    if (selectedId) {
      store.triggerReplay(selectedId);
    } else if (data.nodes.length > 0) {
      store.triggerReplay(data.nodes[0].data.id);
    }
  };

  return (
    <section 
      id="graph-canvas-container"
      className="graph-pane" 
      aria-label="Transaction network"
      style={{
        width: '100%',
        height: '100%',
        minHeight: 0,
        position: 'relative',
        backgroundColor: 'var(--bg-0)',
        overflow: 'hidden'
      }}
    >
      {/* Cytoscape Canvas Host */}
      <div 
        ref={hostRef} 
        className="graph-host"
        style={{
          width: '100%',
          height: '100%',
          minHeight: 0,
          position: 'absolute',
          inset: 0,
        }} 
      />

      {/* Graph Visual State Overlays */}
      {status !== "ready" && (
        <div 
          className="graph-state" 
          role="status"
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(10, 15, 30, 0.75)',
            zIndex: 10,
            color: 'var(--text-1)',
            gap: '12px',
          }}
        >
          {status === "loading" && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--brand)' }} />
              <p style={{ fontSize: 'var(--fs-sm)', fontWeight: 500 }}>Building network…</p>
            </div>
          )}

          {status === "empty" && (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <Layers size={36} style={{ color: 'var(--text-3)', marginBottom: '8px', opacity: 0.6 }} />
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-2)', fontWeight: 600 }}>
                No transactions to draw for this selection.
              </p>
              <button 
                type="button"
                className="btn" 
                onClick={() => store.fetchGraph(null)}
                style={{ marginTop: '12px' }}
              >
                Reset to Global View
              </button>
            </div>
          )}

          {status === "error" && (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <AlertTriangle size={36} style={{ color: 'var(--sev-critical)', marginBottom: '8px' }} />
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--text-1)', fontWeight: 600 }}>
                The graph could not be drawn.
              </p>
              <button 
                type="button"
                className="btn" 
                onClick={() => setAttempt((a) => a + 1)}
                style={{ marginTop: '12px' }}
              >
                Retry
              </button>
            </div>
          )}
        </div>
      )}

      {/* Top Banner: Global Network Overview & Layout Controls */}
      <div 
        style={{
          position: 'absolute',
          top: '12px',
          left: '14px',
          zIndex: 5,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          backgroundColor: 'rgba(15, 23, 41, 0.88)',
          backdropFilter: 'blur(8px)',
          padding: '6px 14px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border)',
          fontSize: 'var(--fs-xs)',
          color: 'var(--text-2)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-1)' }}>
            {graphCenterId ? `Focused Subgraph: ${graphCenterId}` : 'Financial Transfer Network · Global View'}
          </span>
          {graphCenterId && (
            <button
              type="button"
              onClick={() => store.fetchGraph(null)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--brand)',
                cursor: 'pointer',
                fontSize: '11px',
                textDecoration: 'underline',
                padding: 0,
              }}
            >
              Clear focus
            </button>
          )}
        </div>
      </div>

      {/* Graph Floating Controls */}
      <div 
        className="graph-controls"
        style={{
          position: 'absolute',
          top: '12px',
          right: '14px',
          zIndex: 5,
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          backgroundColor: 'rgba(15, 23, 41, 0.85)',
          backdropFilter: 'blur(8px)',
          padding: '4px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border)',
        }}
      >
        <button
          type="button"
          onClick={handleZoomIn}
          title="Zoom In"
          aria-label="Zoom In"
          className="icon-btn"
          style={{ width: '28px', height: '28px' }}
        >
          <ZoomIn size={15} />
        </button>
        <button
          type="button"
          onClick={handleZoomOut}
          title="Zoom Out"
          aria-label="Zoom Out"
          className="icon-btn"
          style={{ width: '28px', height: '28px' }}
        >
          <ZoomOut size={15} />
        </button>
        <button
          type="button"
          onClick={handleFit}
          title="Fit Network"
          aria-label="Fit Network"
          className="icon-btn"
          style={{ width: '28px', height: '28px' }}
        >
          <Maximize2 size={15} />
        </button>
        <button
          type="button"
          onClick={handleReset}
          title="Re-layout Graph"
          aria-label="Re-layout Graph"
          className="icon-btn"
          style={{ width: '28px', height: '28px' }}
        >
          <RotateCw size={15} />
        </button>
        <button
          type="button"
          onClick={handleReplay}
          title="Forensic Flow Replay (Press Space)"
          aria-label="Forensic Flow Replay"
          className="icon-btn"
          style={{ width: '28px', height: '28px', color: 'var(--brand)' }}
        >
          <Play size={15} />
        </button>
      </div>

      {/* Edge Details Popover */}
      {selectedEdgeData && (
        <div 
          style={{
            position: 'absolute',
            bottom: '80px',
            right: '14px',
            zIndex: 10,
            width: '260px',
            backgroundColor: 'var(--bg-2)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px',
            boxShadow: 'var(--shadow-lg)',
            fontSize: 'var(--fs-xs)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontWeight: 700, color: 'var(--text-1)' }}>TRANSFER TRANSACTION</span>
            <button
              type="button"
              onClick={() => setSelectedEdgeData(null)}
              style={{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer' }}
            >
              <X size={14} />
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div>
              <span className="label">Amount: </span>
              <span className="mono" style={{ fontWeight: 700, color: 'var(--text-1)' }}>
                {fmtINR(selectedEdgeData.amount || 0)}
              </span>
            </div>
            <div>
              <span className="label">Origin: </span>
              <span className="mono" style={{ color: 'var(--text-2)' }}>{selectedEdgeData.source}</span>
            </div>
            <div>
              <span className="label">Target: </span>
              <span className="mono" style={{ color: 'var(--text-2)' }}>{selectedEdgeData.target}</span>
            </div>
            {selectedEdgeData.timestamp && (
              <div>
                <span className="label">Timestamp: </span>
                <span style={{ color: 'var(--text-3)' }}>{selectedEdgeData.timestamp}</span>
              </div>
            )}
            {selectedEdgeData.tainted && (
              <div style={{ marginTop: '4px' }}>
                <SeverityBadge severity="critical" label="TAINTED FLOW" size="sm" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Graph Legend */}
      <div 
        className="graph-legend"
        style={{
          position: 'absolute',
          bottom: '14px',
          left: '14px',
          zIndex: 5,
          backgroundColor: 'rgba(15, 23, 41, 0.90)',
          backdropFilter: 'blur(8px)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border)',
          padding: '8px 12px',
          fontSize: 'var(--fs-xs)',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        <div 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between', 
            gap: '12px',
            cursor: 'pointer' 
          }}
          onClick={() => setShowLegend(!showLegend)}
        >
          <span style={{ fontWeight: 700, letterSpacing: '0.04em', color: 'var(--text-2)' }}>
            TYPOLOGY LEGEND
          </span>
          <button
            type="button"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-3)',
              fontSize: '11px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
            }}
          >
            {showLegend ? 'Hide' : 'Show'}
            {showLegend ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
          </button>
        </div>

        {showLegend && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', paddingTop: '4px', borderTop: '1px solid var(--border)' }}>
            {/* Severity Colors with Badges */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <SeverityBadge severity="critical" label="Critical" size="sm" />
              <SeverityBadge severity="medium" label="Medium" size="sm" />
              <SeverityBadge severity="safe" label="Safe" size="sm" />
            </div>

            {/* Role Shapes */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px', color: 'var(--text-3)', fontSize: '11px' }}>
              <span>⬡ Hexagon: <strong style={{ color: 'var(--text-2)' }}>Hub</strong></span>
              <span>▭ Rectangle: <strong style={{ color: 'var(--text-2)' }}>Relay</strong></span>
              <span>◇ Diamond: <strong style={{ color: 'var(--text-2)' }}>Exit</strong></span>
              <span>◈ Rhombus: <strong style={{ color: 'var(--text-2)' }}>Victim</strong></span>
            </div>

            {/* Tainted Flow */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-3)' }}>
              <span style={{ width: '16px', height: '2px', backgroundColor: 'var(--sev-critical)' }} />
              <span>Red Line: <strong style={{ color: 'var(--sev-critical)' }}>Tainted Flow</strong></span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default GraphPane;
