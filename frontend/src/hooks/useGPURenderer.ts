/**
 * useGPURenderer - React hook for GPU stamp renderer.
 *
 * Manages renderer lifecycle:
 * - Renderer initialization with artist profile
 * - Stamp rendering and drawing
 * - Canvas resizing
 * - Cleanup on unmount
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { GPUDeviceContext, CanvasContext, StampData } from '../gpu/types';
import { StampRenderer } from '../gpu/stampRenderer';
import { profileContext } from '../services/ProfileContext';
import { ArtistProfile } from '../types/calibration';
import { FaceTag } from '../types/semantic';

export interface UseGPURendererOptions {
  /** GPU device context */
  deviceContext: GPUDeviceContext | null;

  /** Canvas width */
  canvasWidth: number;

  /** Canvas height */
  canvasHeight: number;

  /** Artist profile (if null, waits for profile to be loaded) */
  profile?: ArtistProfile | null;
}

export interface UseGPURendererResult {
  /** Stamp renderer instance (null if not initialized) */
  renderer: StampRenderer | null;

  /** Whether renderer is ready */
  isReady: boolean;

  /** Initialization error (if any) */
  error: Error | null;

  /** Add a stamp to render */
  addStamp: (stamp: StampData) => void;

  /** Add multiple stamps */
  addStamps: (stamps: StampData[]) => void;

  /** Clear all stamps */
  clearStamps: () => void;

  /** Clear render texture */
  clearCanvas: () => void;

  /** Trigger a render frame */
  render: (canvasContext: CanvasContext) => void;

  /** Resize renderer */
  resize: (width: number, height: number) => void;
}

/**
 * Hook to initialize and manage GPU stamp renderer.
 *
 * @param options - Renderer configuration
 * @returns Renderer instance and control functions
 */
export function useGPURenderer(options: UseGPURendererOptions): UseGPURendererResult {
  const { deviceContext, canvasWidth, canvasHeight, profile } = options;

  const [renderer, setRenderer] = useState<StampRenderer | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const rendererRef = useRef<StampRenderer | null>(null);

  // Initialize renderer when device and profile are ready
  useEffect(() => {
    if (!deviceContext) {
      setIsReady(false);
      return;
    }

    // Load profile into ProfileContext
    if (profile) {
      profileContext.setProfile(profile);
    }

    // Check if profile is loaded
    if (!profileContext.hasProfile()) {
      console.warn('[useGPURenderer] Waiting for profile...');
      setIsReady(false);
      return;
    }

    // Get shader constants
    const shaderConstants = profileContext.getShaderConstants();
    if (!shaderConstants) {
      setError(new Error('Failed to get shader constants from profile'));
      return;
    }

    const initRenderer = async () => {
      try {
        console.log('[useGPURenderer] Initializing renderer...');

        const newRenderer = new StampRenderer({
          deviceContext,
          shaderConstants,
          canvasWidth,
          canvasHeight
        });

        await newRenderer.initialize();

        rendererRef.current = newRenderer;
        setRenderer(newRenderer);
        setIsReady(true);
        setError(null);

        console.log('[useGPURenderer] Renderer ready');
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        setIsReady(false);
        console.error('[useGPURenderer] Initialization failed:', error);
      }
    };

    initRenderer();

    // Cleanup on unmount
    return () => {
      if (rendererRef.current) {
        rendererRef.current.destroy();
        rendererRef.current = null;
      }
    };
  }, [deviceContext, canvasWidth, canvasHeight, profile]);

  // Add a stamp
  const addStamp = useCallback((stamp: StampData) => {
    if (rendererRef.current) {
      rendererRef.current.addStamp(stamp);
    }
  }, []);

  // Add multiple stamps
  const addStamps = useCallback((stamps: StampData[]) => {
    if (rendererRef.current) {
      rendererRef.current.addStamps(stamps);
    }
  }, []);

  // Clear stamps
  const clearStamps = useCallback(() => {
    if (rendererRef.current) {
      rendererRef.current.clearStamps();
    }
  }, []);

  // Clear canvas
  const clearCanvas = useCallback(() => {
    if (rendererRef.current) {
      rendererRef.current.clear();
    }
  }, []);

  // Render frame
  const render = useCallback((canvasContext: CanvasContext) => {
    if (rendererRef.current && isReady) {
      rendererRef.current.render(canvasContext);
    }
  }, [isReady]);

  // Resize renderer
  const resize = useCallback((width: number, height: number) => {
    if (rendererRef.current) {
      rendererRef.current.resize(width, height);
    }
  }, []);

  return {
    renderer,
    isReady,
    error,
    addStamp,
    addStamps,
    clearStamps,
    clearCanvas,
    render,
    resize
  };
}

/**
 * Helper: Create a stamp from stroke point with semantic weighting.
 *
 * @param x - X position
 * @param y - Y position
 * @param pressure - Pressure (0-1)
 * @param color - RGBA color
 * @param semanticTag - Optional semantic tag for weighting
 * @returns StampData
 */
export function createStampFromPoint(
  x: number,
  y: number,
  pressure: number,
  color: [number, number, number, number],
  semanticTag?: FaceTag
): StampData {
  const semanticWeight = semanticTag
    ? profileContext.getSemanticWeight(semanticTag)
    : 1.0;

  const radius = profileContext.evaluatePressureToRadius(pressure, semanticWeight);
  const density = profileContext.evaluatePressureToDensity(pressure, semanticWeight);

  return {
    x,
    y,
    radius,
    color,
    density,
    softness: 0.5, // Default softness
    semanticWeight
  };
}
