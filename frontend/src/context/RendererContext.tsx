/**
 * RendererContext - Global renderer state management
 *
 * IMPROVEMENT #10: Provides global state for:
 * - Renderer mode (GPU vs Canvas2D)
 * - Adapter name (for debugging)
 * - Device pixel ratio
 * - Performance mode control
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface RendererState {
  mode: 'gpu' | 'canvas2d';
  adapterName: string | null;
  dpr: number;
  performanceMode: 'high' | 'balanced' | 'speed';
}

interface RendererContextValue {
  state: RendererState;
  setMode: (mode: 'gpu' | 'canvas2d') => void;
  setAdapterName: (name: string | null) => void;
  setPerformanceMode: (mode: 'high' | 'balanced' | 'speed') => void;
}

const RendererContext = createContext<RendererContextValue | null>(null);

export function RendererProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<RendererState>({
    mode: 'canvas2d',
    adapterName: null,
    dpr: window.devicePixelRatio || 1,
    performanceMode: 'high'
  });

  const setMode = (mode: 'gpu' | 'canvas2d') => {
    console.log(`[RendererContext] Switching to ${mode} mode`);
    setState(prev => ({ ...prev, mode }));
  };

  const setAdapterName = (name: string | null) => {
    console.log(`[RendererContext] GPU Adapter: ${name}`);
    setState(prev => ({ ...prev, adapterName: name }));
  };

  const setPerformanceMode = (mode: 'high' | 'balanced' | 'speed') => {
    // IMPROVEMENT #15: Adjust DPR based on performance mode
    const baseDpr = window.devicePixelRatio || 1;
    const dpr = mode === 'high' ? baseDpr :
                mode === 'balanced' ? baseDpr * 0.75 :
                baseDpr * 0.5;

    console.log(`[RendererContext] Performance mode: ${mode} (DPR: ${dpr.toFixed(2)}x)`);
    setState(prev => ({ ...prev, performanceMode: mode, dpr }));
  };

  return (
    <RendererContext.Provider value={{ state, setMode, setAdapterName, setPerformanceMode }}>
      {children}
    </RendererContext.Provider>
  );
}

export function useRenderer() {
  const context = useContext(RendererContext);
  if (!context) {
    throw new Error('useRenderer must be used within RendererProvider');
  }
  return context;
}
