/**
 * RendererSurface - Abstraction layer for dual renderer system
 *
 * IMPROVEMENT #4: RendererSurface abstraction
 *
 * Routes to either:
 * - GPUDrawingSurface (if WebGPU available)
 * - Canvas2DDrawingSurface (fallback)
 *
 * Ensures only ONE renderer is active (prevents ghosting)
 */

import React from 'react';
import { useRenderer } from '../context/RendererContext';
import { GPUDrawingSurface } from './GPUDrawingSurface';
import { Canvas2DDrawingSurface } from './Canvas2DDrawingSurface';
import { ArtistProfile } from '../types/calibration';

export interface RendererSurfaceProps {
  /** Canvas width (CSS pixels) */
  width?: number;

  /** Canvas height (CSS pixels) */
  height?: number;

  /** Whether GPU is available */
  gpuAvailable: boolean | null;

  /** Artist profile for GPU rendering */
  profile?: ArtistProfile | null;

  /** Current drawing color */
  color?: string;

  /** Callback when clear is requested */
  onClear?: () => void;
}

/**
 * RendererSurface - Routes to appropriate renderer based on GPU availability
 *
 * CRITICAL: Only renders ONE component to prevent ghosting
 */
export function RendererSurface(props: RendererSurfaceProps) {
  const {
    width = 800,
    height = 600,
    gpuAvailable,
    profile,
    color = '#000000',
    onClear
  } = props;

  const { state } = useRenderer();

  // Still initializing GPU detection
  if (gpuAvailable === null) {
    return (
      <div style={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px'
      }}>
        <p style={{ color: '#666' }}>Detecting GPU...</p>
      </div>
    );
  }

  // GPU available and mode is GPU - use GPUDrawingSurface
  if (gpuAvailable && state.mode === 'gpu') {
    console.log('[RendererSurface] Using GPU renderer');

    return (
      <GPUDrawingSurface
        width={width}
        height={height}
        profile={profile}
        color={color}
        onError={(error) => {
          console.error('[RendererSurface] GPU error:', error);
        }}
      />
    );
  }

  // Fallback to Canvas2D
  console.log('[RendererSurface] Using Canvas2D renderer');

  return (
    <Canvas2DDrawingSurface
      width={width}
      height={height}
      color={color}
      onClear={onClear}
    />
  );
}
