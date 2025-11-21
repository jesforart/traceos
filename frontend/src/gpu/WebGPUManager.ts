/**
 * WebGPU Manager - Centralized device management with retry logic
 *
 * Features:
 * - Single source of truth for WebGPU state
 * - Automatic retry with limit (max 3 attempts)
 * - Fallback to Canvas2D after failures
 * - Device lost recovery
 */

import { initializeGPUDevice, isWebGPUSupported } from './device';
import type { GPUDeviceContext } from './types';

// Global state (outside React)
let currentAdapter: GPUAdapter | null = null;
let currentDevice: GPUDevice | null = null;
let deviceContext: GPUDeviceContext | null = null;
let reinitAttempts = 0;

const MAX_REINIT_ATTEMPTS = 3;

// Listeners for state changes
type DeviceStateListener = (context: GPUDeviceContext | null) => void;
const stateListeners: Set<DeviceStateListener> = new Set();

// Notification callback
type NotificationCallback = (notification: {
  type: 'success' | 'warning' | 'error';
  message: string;
  duration: number;
}) => void;
let notificationCallback: NotificationCallback | null = null;

/**
 * WebGPU Manager - Centralized device lifecycle
 */
export class WebGPUManager {
  /**
   * Initialize WebGPU device
   */
  static async initialize(): Promise<GPUDeviceContext | null> {
    if (!isWebGPUSupported()) {
      console.error('[WebGPUManager] WebGPU not supported');
      return null;
    }

    try {
      const ctx = await initializeGPUDevice();

      if (!ctx) {
        throw new Error('Failed to initialize GPU device');
      }

      // Store references
      currentDevice = ctx.device;
      deviceContext = ctx;

      // Attach device lost handler
      currentDevice.lost.then((info) => {
        console.warn('[WebGPUManager] Device lost:', info.reason, info.message);

        if (info.reason !== 'destroyed') {
          this.showNotification({
            type: 'warning',
            message: 'Graphics device lost. Reconnecting...',
            duration: 3000
          });

          void this.reinitialize();
        }
      });

      // Reset attempts on successful init
      reinitAttempts = 0;

      console.log('[WebGPUManager] Device initialized successfully');
      this.notifyListeners(ctx);

      return ctx;
    } catch (error) {
      console.error('[WebGPUManager] Initialization failed:', error);
      return null;
    }
  }

  /**
   * Reinitialize after device lost
   */
  static async reinitialize(): Promise<void> {
    reinitAttempts++;

    if (reinitAttempts > MAX_REINIT_ATTEMPTS) {
      console.error(
        `[WebGPUManager] Failed to reinitialize after ${MAX_REINIT_ATTEMPTS} attempts`
      );

      this.showNotification({
        type: 'error',
        message: 'GPU unstable. Using fallback renderer.',
        duration: 5000
      });

      this.useFallbackRenderer();
      return;
    }

    try {
      // Clear old references
      currentDevice = null;
      currentAdapter = null;
      deviceContext = null;

      // Recreate device
      const ctx = await this.initialize();

      if (ctx) {
        // Success
        this.showNotification({
          type: 'success',
          message: 'Graphics device reconnected',
          duration: 2000
        });

        console.log(`[WebGPUManager] Reinitialized successfully (attempt ${reinitAttempts})`);
      } else {
        throw new Error('Reinitialization returned null context');
      }
    } catch (error) {
      console.error(`[WebGPUManager] Reinit attempt ${reinitAttempts} failed:`, error);

      this.showNotification({
        type: 'error',
        message: `Reconnection attempt ${reinitAttempts}/${MAX_REINIT_ATTEMPTS} failed`,
        duration: 3000
      });

      // Will retry on next device.lost event or fall back after MAX_REINIT_ATTEMPTS
    }
  }

  /**
   * Get current device context
   */
  static getContext(): GPUDeviceContext | null {
    return deviceContext;
  }

  /**
   * Get current device
   */
  static getDevice(): GPUDevice | null {
    return currentDevice;
  }

  /**
   * Subscribe to device state changes
   */
  static subscribe(listener: DeviceStateListener): () => void {
    stateListeners.add(listener);

    // Return unsubscribe function
    return () => {
      stateListeners.delete(listener);
    };
  }

  /**
   * Notify all listeners of state change
   */
  private static notifyListeners(context: GPUDeviceContext | null): void {
    stateListeners.forEach((listener) => listener(context));
  }

  /**
   * Set notification callback
   */
  static setNotificationCallback(callback: NotificationCallback): void {
    notificationCallback = callback;
  }

  /**
   * Show notification
   */
  private static showNotification(notification: {
    type: 'success' | 'warning' | 'error';
    message: string;
    duration: number;
  }): void {
    if (notificationCallback) {
      notificationCallback(notification);
    } else {
      // Fallback to console
      console.log(`[WebGPUManager] ${notification.type.toUpperCase()}: ${notification.message}`);
    }
  }

  /**
   * Switch to Canvas2D fallback renderer
   */
  private static useFallbackRenderer(): void {
    console.log('[WebGPUManager] Switching to Canvas2D fallback');

    // Notify listeners with null context (triggers Canvas2D mode)
    this.notifyListeners(null);

    // Dispatch custom event for app-level handling
    window.dispatchEvent(
      new CustomEvent('webgpu-fallback', {
        detail: { reason: 'max_retries_exceeded', attempts: reinitAttempts }
      })
    );
  }

  /**
   * Destroy device (cleanup)
   */
  static destroy(): void {
    if (currentDevice) {
      currentDevice.destroy();
      currentDevice = null;
    }

    currentAdapter = null;
    deviceContext = null;
    reinitAttempts = 0;

    console.log('[WebGPUManager] Device destroyed');
    this.notifyListeners(null);
  }

  /**
   * Get current retry attempts
   */
  static getRetryAttempts(): number {
    return reinitAttempts;
  }

  /**
   * Reset retry counter (for testing)
   */
  static resetRetryCounter(): void {
    reinitAttempts = 0;
  }
}
