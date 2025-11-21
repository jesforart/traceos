/**
 * GPU device initialization and management.
 *
 * Handles WebGPU adapter and device request, feature detection,
 * and initialization of GPU resources.
 */

import { GPUDeviceContext, CanvasContext } from './types';

/**
 * Check if WebGPU is supported in the current browser.
 */
export function isWebGPUSupported(): boolean {
  return 'gpu' in navigator;
}

/**
 * Initialize WebGPU device and context.
 *
 * @returns GPUDeviceContext or null if initialization fails
 * @throws Error with details if WebGPU is not supported
 */
export async function initializeGPUDevice(): Promise<GPUDeviceContext | null> {
  // Check WebGPU support
  if (!isWebGPUSupported()) {
    throw new Error(
      'WebGPU is not supported in this browser. ' +
      'Please use Chrome 113+, Edge 113+, or Safari 18+'
    );
  }

  try {
    // Request GPU adapter (physical device)
    const adapter = await navigator.gpu.requestAdapter({
      powerPreference: 'high-performance'
    });

    if (!adapter) {
      throw new Error('Failed to get GPU adapter. WebGPU may be disabled.');
    }

    // Log adapter info
    console.log('[GPU] Adapter found:', {
      vendor: adapter.info?.vendor || 'unknown',
      architecture: adapter.info?.architecture || 'unknown',
      device: adapter.info?.device || 'unknown',
      description: adapter.info?.description || 'unknown'
    });

    // Request GPU device (logical device)
    const device = await adapter.requestDevice({
      requiredFeatures: [],
      requiredLimits: {}
    });

    if (!device) {
      throw new Error('Failed to get GPU device.');
    }

    // Handle device lost errors
    device.lost.then((info) => {
      console.error('[GPU] Device lost:', info.reason, info.message);
      if (info.reason !== 'destroyed') {
        // Attempt to re-initialize
        console.warn('[GPU] Attempting to re-initialize device...');
      }
    });

    // Handle uncaptured errors
    device.onuncapturederror = (event) => {
      console.error('[GPU] Uncaptured error:', event.error);
    };

    // Get preferred canvas format
    const format = navigator.gpu.getPreferredCanvasFormat();

    // Get device pixel ratio
    const devicePixelRatio = window.devicePixelRatio || 1;

    console.log('[GPU] Device initialized successfully', {
      format,
      devicePixelRatio,
      limits: {
        maxTextureDimension2D: device.limits.maxTextureDimension2D,
        maxBufferSize: device.limits.maxBufferSize,
        maxBindGroups: device.limits.maxBindGroups
      }
    });

    return {
      adapter,
      device,
      format,
      devicePixelRatio
    };
  } catch (error) {
    console.error('[GPU] Initialization failed:', error);
    return null;
  }
}

/**
 * Configure canvas for WebGPU rendering.
 *
 * @param canvas - HTML canvas element
 * @param deviceContext - GPU device context
 * @returns Configured canvas context or null if configuration fails
 */
export function configureCanvas(
  canvas: HTMLCanvasElement,
  deviceContext: GPUDeviceContext
): CanvasContext | null {
  try {
    const context = canvas.getContext('webgpu');

    if (!context) {
      console.error('[GPU] Failed to get WebGPU canvas context');
      return null;
    }

    // Get canvas dimensions in physical pixels
    const width = canvas.width;
    const height = canvas.height;

    // Configure canvas context
    context.configure({
      device: deviceContext.device,
      format: deviceContext.format,
      alphaMode: 'premultiplied',
      usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.COPY_DST
    });

    console.log('[GPU] Canvas configured', {
      width,
      height,
      format: deviceContext.format
    });

    return {
      canvas,
      context,
      width,
      height
    };
  } catch (error) {
    console.error('[GPU] Canvas configuration failed:', error);
    return null;
  }
}

/**
 * Resize canvas to match display size with device pixel ratio.
 *
 * @param canvas - HTML canvas element
 * @param devicePixelRatio - Device pixel ratio
 */
export function resizeCanvas(
  canvas: HTMLCanvasElement,
  devicePixelRatio: number = window.devicePixelRatio || 1
): void {
  const displayWidth = canvas.clientWidth;
  const displayHeight = canvas.clientHeight;

  const width = Math.floor(displayWidth * devicePixelRatio);
  const height = Math.floor(displayHeight * devicePixelRatio);

  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;

    console.log('[GPU] Canvas resized', {
      displayWidth,
      displayHeight,
      physicalWidth: width,
      physicalHeight: height,
      devicePixelRatio
    });
  }
}

/**
 * Create a GPU buffer.
 *
 * @param device - GPU device
 * @param size - Buffer size in bytes
 * @param usage - Buffer usage flags
 * @param mappedAtCreation - Whether buffer should be mapped at creation
 * @returns GPUBuffer
 */
export function createBuffer(
  device: GPUDevice,
  size: number,
  usage: GPUBufferUsageFlags,
  mappedAtCreation: boolean = false
): GPUBuffer {
  return device.createBuffer({
    size,
    usage,
    mappedAtCreation
  });
}

/**
 * Create a GPU texture.
 *
 * @param device - GPU device
 * @param width - Texture width
 * @param height - Texture height
 * @param format - Texture format
 * @param usage - Texture usage flags
 * @returns GPUTexture
 */
export function createTexture(
  device: GPUDevice,
  width: number,
  height: number,
  format: GPUTextureFormat,
  usage: GPUTextureUsageFlags
): GPUTexture {
  return device.createTexture({
    size: { width, height },
    format,
    usage
  });
}

/**
 * Write data to a GPU buffer.
 *
 * @param device - GPU device
 * @param buffer - Target buffer
 * @param data - Data to write (typed array or ArrayBuffer)
 * @param offset - Byte offset in buffer
 */
export function writeBuffer(
  device: GPUDevice,
  buffer: GPUBuffer,
  data: BufferSource | ArrayBufferView | ArrayBuffer,
  offset: number = 0
): void {
  device.queue.writeBuffer(buffer, offset, data as BufferSource);
}

/**
 * Clear a texture by rendering a clear color.
 * NOTE: Do NOT use clearBuffer on textures - it's invalid in WebGPU.
 *
 * @param device - GPU device
 * @param texture - Texture to clear
 * @param clearColor - RGBA clear color (each component 0-1)
 */
export function clearTexture(
  device: GPUDevice,
  texture: GPUTexture,
  clearColor: [number, number, number, number] = [0, 0, 0, 0]
): void {
  const commandEncoder = device.createCommandEncoder();

  const renderPass = commandEncoder.beginRenderPass({
    colorAttachments: [
      {
        view: texture.createView(),
        clearValue: {
          r: clearColor[0],
          g: clearColor[1],
          b: clearColor[2],
          a: clearColor[3]
        },
        loadOp: 'clear',
        storeOp: 'store'
      }
    ]
  });

  renderPass.end();

  device.queue.submit([commandEncoder.finish()]);
}
