import React, { useEffect } from 'react';
import { useMuleStore } from '../store/useMuleStore';
import { fmtINR } from '../lib/format';
import { 
  Play, 
  Pause, 
  Square, 
  SkipBack, 
  SkipForward, 
  Clock, 
  DollarSign, 
  Users, 
  ArrowUpRight,
  TrendingDown
} from 'lucide-react';

export const TimelineScrubber = () => {
  const { 
    replayState, 
    toggleReplayPlay, 
    setReplayFrame, 
    stopReplay 
  } = useMuleStore();

  const { isPlaying, currentFrameIndex, frames, speed, active } = replayState;

  // Auto-play timer
  useEffect(() => {
    let timer = null;
    if (active && isPlaying && frames.length > 0) {
      timer = setInterval(() => {
        const nextIdx = currentFrameIndex + 1;
        if (nextIdx < frames.length) {
          setReplayFrame(nextIdx);
        } else {
          toggleReplayPlay(); // Pause at end
        }
      }, speed);
    }
    return () => clearInterval(timer);
  }, [active, isPlaying, currentFrameIndex, frames.length, speed]);

  if (!active || frames.length === 0) {
    return null;
  }

  const currentFrame = frames[currentFrameIndex] || {};
  const activeTaintedAccounts = currentFrame.active_tainted_accounts || [];
  const inCirculation = currentFrame.total_tainted_in_circulation || 0;
  const cashedOut = currentFrame.cumulative_cashed_out || 0;



  return (
    <div
      id="timeline-scrubber-bar"
      aria-label="Replay Temporal Scrubber"
      style={{
        position: 'absolute',
        bottom: '16px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: 'calc(100% - 440px)',
        maxWidth: '820px',
        minWidth: '520px',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--accent)',
        borderRadius: '8px',
        padding: '12px 18px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        zIndex: 25,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Upper row: Controls & Live Stats */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Playback Button Group */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setReplayFrame(0)}
            title="Jump to Start"
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              padding: '6px',
              color: 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            <SkipBack size={14} />
          </button>

          <button
            onClick={toggleReplayPlay}
            title={isPlaying ? "Pause" : "Play"}
            style={{
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 12px',
              color: 'var(--bg-0)',
              backgroundColor: 'var(--brand)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontWeight: 700,
              fontSize: 'var(--fs-xs)'
            }}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
            <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
          </button>

          <button
            onClick={() => setReplayFrame(frames.length - 1)}
            title="Jump to End"
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px',
              color: 'var(--text-2)',
              cursor: 'pointer'
            }}
          >
            <SkipForward size={14} />
          </button>

          <button
            onClick={stopReplay}
            title="Close Replay"
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px',
              color: 'var(--danger)',
              cursor: 'pointer'
            }}
          >
            <Square size={14} />
          </button>

          <span style={{ fontSize: 'var(--fs-xs)', fontFamily: 'monospace', color: 'var(--text-3)', marginLeft: '6px' }}>
            Frame {currentFrameIndex + 1} / {frames.length}
          </span>
        </div>

        {/* Live Replay Metrics */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: 'var(--fs-xs)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Clock size={13} style={{ color: 'var(--text-3)' }} />
            <span style={{ fontFamily: 'monospace', color: 'var(--text-1)' }}>
              {currentFrame.timestamp ? currentFrame.timestamp.replace('T', ' ').slice(0, 19) : '--'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: 'var(--text-3)' }}>Circulating:</span>
            <strong style={{ color: 'var(--warning)', fontFamily: 'monospace' }}>
              {fmtINR(inCirculation)}
            </strong>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: 'var(--text-3)' }}>Cashed Out:</span>
            <strong style={{ color: 'var(--danger)', fontFamily: 'monospace' }}>
              {fmtINR(cashedOut)}
            </strong>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Users size={13} style={{ color: 'var(--text-3)' }} />
            <span style={{ color: 'var(--brand)', fontWeight: 700 }}>
              {activeTaintedAccounts.length} Mules Tainted
            </span>
          </div>
        </div>
      </div>

      {/* Scrubber Range Slider */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <input
          type="range"
          min="0"
          max={frames.length - 1}
          value={currentFrameIndex}
          onChange={(e) => setReplayFrame(parseInt(e.target.value, 10))}
          style={{
            flex: 1,
            cursor: 'pointer',
            accentColor: 'var(--brand)'
          }}
        />
      </div>

      {/* Frame Transfer Detail Summary */}
      {currentFrame.trigger_txn && (
        <div style={{
          fontSize: 'var(--fs-xs)',
          color: 'var(--text-2)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: 'var(--bg-0)',
          padding: '4px 8px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border)'
        }}>
          <strong style={{ color: 'var(--brand)' }}>Trigger Transfer:</strong>
          <span style={{ fontFamily: 'monospace' }}>{currentFrame.trigger_txn.src || currentFrame.trigger_txn.source_account}</span>
          <ArrowUpRight size={10} />
          <span style={{ fontFamily: 'monospace' }}>{currentFrame.trigger_txn.dest || currentFrame.trigger_txn.dest_account}</span>
          <span style={{ color: 'var(--danger)', fontWeight: 700 }}>
            {fmtINR(currentFrame.trigger_txn.amount)}
          </span>
          <span style={{ color: 'var(--text-muted)', marginLeft: 'auto' }}>
            Channel: {currentFrame.trigger_txn.channel}
          </span>
        </div>
      )}
    </div>
  );
};

export default TimelineScrubber;
