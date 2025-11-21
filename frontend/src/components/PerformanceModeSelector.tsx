/**
 * PerformanceModeSelector - Performance mode control UI
 *
 * IMPROVEMENT #15: Allows users to adjust rendering quality/performance
 * - High: Full device pixel ratio (best quality)
 * - Balanced: 75% DPR (good balance)
 * - Speed: 50% DPR (maximum performance)
 */

import React from 'react';
import { useRenderer } from '../context/RendererContext';

export function PerformanceModeSelector() {
  const { state, setPerformanceMode } = useRenderer();

  return (
    <div style={{
      display: 'flex',
      gap: '0.5rem',
      alignItems: 'center'
    }}>
      <span style={{ fontSize: '0.875rem', color: '#666' }}>
        Quality:
      </span>
      {(['high', 'balanced', 'speed'] as const).map((mode) => (
        <button
          key={mode}
          onClick={() => setPerformanceMode(mode)}
          style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '4px',
            border: state.performanceMode === mode ? '2px solid #0066FF' : '1px solid #ccc',
            background: state.performanceMode === mode ? '#e6f2ff' : 'white',
            color: state.performanceMode === mode ? '#0066FF' : '#666',
            fontSize: '0.75rem',
            fontWeight: state.performanceMode === mode ? 'bold' : 'normal',
            cursor: 'pointer',
            textTransform: 'capitalize'
          }}
        >
          {mode}
        </button>
      ))}
      <span style={{ fontSize: '0.75rem', color: '#999' }}>
        {state.dpr.toFixed(1)}x
      </span>
    </div>
  );
}
