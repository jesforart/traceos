/**
 * useWebGPU - React hook for WebGPU device initialization.
 *
 * Now uses centralized WebGPUManager with retry limits.
 *
 * Changes:
 * - Uses WebGPUManager for centralized device management
 * - Automatic retry with max 3 attempts
 * - Fallback to Canvas2D after failures
 * - Device lost recovery handled globally
 */

import { useState, useEffect, useCallback } from 'react';
import { GPUDeviceContext } from '../gpu/types';
import { WebGPUManager } from '../gpu/WebGPUManager';
import { isWebGPUSupported } from '../gpu/device';

export interface UseWebGPUResult {
  /** GPU device context (null if not initialized) */
  deviceContext: GPUDeviceContext | null;

  /** Whether GPU is currently initializing */
  isInitializing: boolean;

  /** Initialization error (if any) */
  error: Error | null;

  /** Whether WebGPU is supported */
  isSupported: boolean;

  /** Current retry attempts */
  retryAttempts: number;

  /** Manually trigger re-initialization */
  reinitialize: () => Promise<void>;
}

/**
 * Hook to initialize and manage WebGPU device.
 *
 * @returns GPU device context and initialization state
 */
export function useWebGPU(): UseWebGPUResult {
  const [deviceContext, setDeviceContext] = useState<GPUDeviceContext | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isSupported] = useState(() => isWebGPUSupported());
  const [retryAttempts, setRetryAttempts] = useState(0);

  const initialize = useCallback(async () => {
    if (!isSupported) {
      setError(new Error('WebGPU is not supported in this browser'));
      return;
    }

    setIsInitializing(true);
    setError(null);

    try {
      const ctx = await WebGPUManager.initialize();

      if (!ctx) {
        throw new Error('Failed to initialize GPU device');
      }

      setDeviceContext(ctx);
      setRetryAttempts(WebGPUManager.getRetryAttempts());
      console.log('[useWebGPU] Device initialized successfully');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      console.error('[useWebGPU] Initialization failed:', error);
    } finally {
      setIsInitializing(false);
    }
  }, [isSupported]);

  const reinitialize = useCallback(async () => {
    console.log('[useWebGPU] Re-initializing GPU device...');
    setDeviceContext(null);
    await initialize();
  }, [initialize]);

  // Initialize on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Subscribe to WebGPUManager state changes
  useEffect(() => {
    const unsubscribe = WebGPUManager.subscribe((context) => {
      setDeviceContext(context);
      setRetryAttempts(WebGPUManager.getRetryAttempts());
    });

    return unsubscribe;
  }, []);

  // Listen for fallback events
  useEffect(() => {
    const handleFallback = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.warn('[useWebGPU] Falling back to Canvas2D:', customEvent.detail);
      setDeviceContext(null);
      setError(new Error('GPU device lost after max retries'));
    };

    window.addEventListener('webgpu-fallback', handleFallback);

    return () => {
      window.removeEventListener('webgpu-fallback', handleFallback);
    };
  }, []);

  return {
    deviceContext,
    isInitializing,
    error,
    isSupported,
    retryAttempts,
    reinitialize
  };
}
