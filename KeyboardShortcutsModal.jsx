import React from 'react';
import { X, Keyboard, HelpCircle } from 'lucide-react';

export const KeyboardShortcutsModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const shortcuts = [
    { key: 'J / K', description: 'Browse next / previous account in alert queue' },
    { key: '1', description: 'Switch detection preset to Relaxed (low false alarms)' },
    { key: '2', description: 'Switch detection preset to Balanced (recommended default)' },
    { key: '3', description: 'Switch detection preset to Strict (maximum sensitivity)' },
    { key: 'P', description: 'Toggle Presenter Mode (large high-contrast screen display)' },
    { key: 'T', description: 'Cycle color themes (Dark, Calm Slate, Paper Light, Colorblind)' },
    { key: 'Ctrl + K', description: 'Open universal command palette & global search' },
    { key: 'Space', description: 'Play / Pause temporal transaction replay' },
    { key: 'Esc', description: 'Close modals, inspector drawer, or dismiss replay' },
    { key: '?', description: 'Open / close this keyboard shortcuts cheat sheet' },
  ];

  return (
    <div
      id="shortcuts-modal-backdrop"
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 10, 20, 0.75)',
        backdropFilter: 'blur(6px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div
        id="shortcuts-modal-box"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '520px',
          maxWidth: '92%',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: '10px',
          boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'var(--bg-card)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Keyboard size={18} style={{ color: 'var(--accent)' }} />
            <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              Keyboard Shortcuts Cheat Sheet
            </strong>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content list */}
        <div style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {shortcuts.map((s, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 0',
                borderBottom: idx < shortcuts.length - 1 ? '1px solid var(--border)' : 'none',
                fontSize: 'var(--fs-xs)'
              }}
            >
              <span style={{ color: 'var(--text-2)' }}>{s.description}</span>
              <kbd style={{
                fontFamily: 'monospace',
                fontSize: 'var(--fs-xs)',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-0)',
                border: '1px solid var(--border)',
                color: 'var(--brand)',
                boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
              }}>
                {s.key}
              </kbd>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{
          padding: '10px 18px',
          backgroundColor: 'var(--bg-0)',
          borderTop: '1px solid var(--border)',
          fontSize: 'var(--fs-xs)',
          color: 'var(--text-3)',
          textAlign: 'right'
        }}>
          Press <strong style={{ color: 'var(--text-1)' }}>Esc</strong> or <strong style={{ color: 'var(--text-1)' }}>?</strong> to dismiss
        </div>
      </div>
    </div>
  );
};

export default KeyboardShortcutsModal;
