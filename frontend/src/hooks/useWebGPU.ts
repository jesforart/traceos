/**
 * useWebGPU - React hook for WebGPU device initialization.
 *
 * Manages GPU device lifecycle:
 * - Device initialization
 * - Error handling
 * - Device lost recovery
 * - Cleanup on unmount
 */

import { useState, useEffect, useCallback } from 'react';
import { GPUDeviceContext } from '../gpu/types';
import { initializeGPUDevice, isWebGPUSupported } from '../gpu/device';

export interface UseWebGPUResult {
  /** GPU device context (null if not initialized) */
  deviceContext: GPUDeviceContext | null;

  /** Whether GPU is currently initializing */
  isInitializing: boolean;

  /** Initialization error (if any) */
  error: Error | null;

  /** Whether WebGPU is supported */
  isSupported: boolean;

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

  const initialize = useCallback(async () => {
    if (!isSupported) {
      setError(new Error('WebGPU is not supported in this browser'));
      return;
    }

    setIsInitializing(true);
    setError(null);

    try {
      const ctx = await initializeGPUDevice();

      if (!ctx) {
        throw new Error('Failed to initialize GPU device');
      }

      setDeviceContext(ctx);
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

  // Handle device lost
  useEffect(() => {
    if (!deviceContext) return;

    const handleDeviceLost = async (info: GPUDeviceLostInfo) => {
      console.warn('[useWebGPU] Device lost:', info.reason, info.message);

      if (info.reason !== 'destroyed') {
        // Attempt to recover
        await reinitialize();
      }
    };

    deviceContext.device.lost.then(handleDeviceLost);
  }, [deviceContext, reinitialize]);

  return {
    deviceContext,
    isInitializing,
    error,
    isSupported,
    reinitialize
  };
}
