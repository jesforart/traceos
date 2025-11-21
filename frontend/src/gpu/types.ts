/**
 * WebGPU types for TraceOS rendering engine.
 *
 * Defines GPU device context, buffers, pipelines, and shader data structures.
 */

import { ShaderConstants } from '../services/ProfileContext';

/**
 * GPU device context - holds initialized WebGPU resources.
 */
export interface GPUDeviceContext {
  /** GPU adapter (physical device) */
  adapter: GPUAdapter;

  /** GPU device (logical device) */
  device: GPUDevice;

  /** Preferred canvas texture format */
  format: GPUTextureFormat;

  /** Device pixel ratio (for high-DPI displays) */
  devicePixelRatio: number;
}

/**
 * Canvas context wrapper - wraps HTML canvas for GPU rendering.
 */
export interface CanvasContext {
  /** HTML canvas element */
  canvas: HTMLCanvasElement;

  /** WebGPU canvas context */
  context: GPUCanvasContext;

  /** Canvas width in physical pixels */
  width: number;

  /** Canvas height in physical pixels */
  height: number;
}

/**
 * Stamp data - a single brush stamp at a point.
 */
export interface StampData {
  /** Position X (screen space) */
  x: number;

  /** Position Y (screen space) */
  y: number;

  /** Radius in pixels */
  radius: number;

  /** Color (RGBA, each component 0-1) */
  color: [number, number, number, number];

  /** Density/opacity (0-1) */
  density: number;

  /** Softness (0-1, affects edge falloff) */
  softness: number;

  /** Semantic weight multiplier */
  semanticWeight: number;
}

/**
 * Uniform data for GPU shaders.
 * Must be 256-byte aligned for WebGPU uniform buffers.
 */
export interface UniformData {
  // Canvas dimensions (vec2, 8 bytes)
  canvasWidth: number;
  canvasHeight: number;

  // Device pixel ratio (f32, 4 bytes)
  devicePixelRatio: number;

  // Padding (4 bytes to align to 16)
  _padding1: number;

  // Bezier curve control points for pressure -> radius (16 vec2 = 128 bytes)
  pressureToRadius_p0: [number, number];
  pressureToRadius_p1: [number, number];
  pressureToRadius_p2: [number, number];
  pressureToRadius_p3: [number, number];

  // Bezier curve control points for pressure -> density (16 vec2 = 128 bytes)
  pressureToDensity_p0: [number, number];
  pressureToDensity_p1: [number, number];
  pressureToDensity_p2: [number, number];
  pressureToDensity_p3: [number, number];

  // Nib parameters (4 f32 = 16 bytes)
  nib_baseRadiusPx: number;
  nib_minRadiusPx: number;
  nib_maxRadiusPx: number;
  nib_avgTiltDeg: number;

  // Stabilizer parameters (5 f32 = 20 bytes)
  stabilizer_microJitterRadiusPx: number;
  stabilizer_curveSmoothMin: number;
  stabilizer_curveSmoothMax: number;
  stabilizer_velocityMin: number;
  stabilizer_velocityMax: number;

  // Padding to reach 256 bytes total
  _padding2: number;
  _padding3: number;
  _padding4: number;
}

/**
 * Render pipeline configuration.
 */
export interface RenderPipelineConfig {
  /** Shader module */
  shaderModule: GPUShaderModule;

  /** Texture format */
  format: GPUTextureFormat;

  /** Blend mode */
  blendMode: 'normal' | 'multiply' | 'add';

  /** Sample count (for MSAA) */
  sampleCount?: number;
}

/**
 * Texture configuration.
 */
export interface TextureConfig {
  /** Width in pixels */
  width: number;

  /** Height in pixels */
  height: number;

  /** Texture format */
  format: GPUTextureFormat;

  /** Usage flags */
  usage: GPUTextureUsageFlags;

  /** Sample count (for MSAA) */
  sampleCount?: number;
}

/**
 * Buffer configuration.
 */
export interface BufferConfig {
  /** Buffer size in bytes */
  size: number;

  /** Usage flags */
  usage: GPUBufferUsageFlags;

  /** Whether buffer is mappable */
  mappedAtCreation?: boolean;
}

/**
 * Stamp rendering pipeline - complete GPU pipeline for stamp-based rendering.
 */
export interface StampRenderPipeline {
  /** GPU device context */
  deviceContext: GPUDeviceContext;

  /** Render pipeline */
  pipeline: GPURenderPipeline;

  /** Uniform buffer */
  uniformBuffer: GPUBuffer;

  /** Bind group (connects uniforms to shaders) */
  bindGroup: GPUBindGroup;

  /** Stamp vertex buffer */
  stampBuffer: GPUBuffer;

  /** Canvas texture */
  canvasTexture: GPUTexture;

  /** Render target view */
  renderTargetView: GPUTextureView;
}

/**
 * Convert shader constants to uniform data.
 * Handles padding and alignment for GPU buffers.
 */
export function shaderConstantsToUniformData(
  constants: ShaderConstants,
  canvasWidth: number,
  canvasHeight: number,
  devicePixelRatio: number
): UniformData {
  return {
    canvasWidth,
    canvasHeight,
    devicePixelRatio,
    _padding1: 0,

    pressureToRadius_p0: constants.pressureToRadius.p0,
    pressureToRadius_p1: constants.pressureToRadius.p1,
    pressureToRadius_p2: constants.pressureToRadius.p2,
    pressureToRadius_p3: constants.pressureToRadius.p3,

    pressureToDensity_p0: constants.pressureToDensity.p0,
    pressureToDensity_p1: constants.pressureToDensity.p1,
    pressureToDensity_p2: constants.pressureToDensity.p2,
    pressureToDensity_p3: constants.pressureToDensity.p3,

    nib_baseRadiusPx: constants.nib.baseRadiusPx,
    nib_minRadiusPx: constants.nib.minRadiusPx,
    nib_maxRadiusPx: constants.nib.maxRadiusPx,
    nib_avgTiltDeg: constants.nib.avgTiltDeg,

    stabilizer_microJitterRadiusPx: constants.stabilizer.microJitterRadiusPx,
    stabilizer_curveSmoothMin: constants.stabilizer.curveSmoothMin,
    stabilizer_curveSmoothMax: constants.stabilizer.curveSmoothMax,
    stabilizer_velocityMin: constants.stabilizer.velocityMin,
    stabilizer_velocityMax: constants.stabilizer.velocityMax,

    _padding2: 0,
    _padding3: 0,
    _padding4: 0
  };
}

/**
 * Create Float32Array from UniformData.
 * WebGPU buffers require typed arrays.
 */
export function uniformDataToFloat32Array(data: UniformData): Float32Array {
  const array = new Float32Array(64); // 256 bytes / 4 bytes per float = 64 floats

  let offset = 0;

  // Canvas dimensions + DPR + padding
  array[offset++] = data.canvasWidth;
  array[offset++] = data.canvasHeight;
  array[offset++] = data.devicePixelRatio;
  array[offset++] = data._padding1;

  // Pressure to radius curve
  array[offset++] = data.pressureToRadius_p0[0];
  array[offset++] = data.pressureToRadius_p0[1];
  array[offset++] = data.pressureToRadius_p1[0];
  array[offset++] = data.pressureToRadius_p1[1];
  array[offset++] = data.pressureToRadius_p2[0];
  array[offset++] = data.pressureToRadius_p2[1];
  array[offset++] = data.pressureToRadius_p3[0];
  array[offset++] = data.pressureToRadius_p3[1];

  // Pressure to density curve
  array[offset++] = data.pressureToDensity_p0[0];
  array[offset++] = data.pressureToDensity_p0[1];
  array[offset++] = data.pressureToDensity_p1[0];
  array[offset++] = data.pressureToDensity_p1[1];
  array[offset++] = data.pressureToDensity_p2[0];
  array[offset++] = data.pressureToDensity_p2[1];
  array[offset++] = data.pressureToDensity_p3[0];
  array[offset++] = data.pressureToDensity_p3[1];

  // Nib parameters
  array[offset++] = data.nib_baseRadiusPx;
  array[offset++] = data.nib_minRadiusPx;
  array[offset++] = data.nib_maxRadiusPx;
  array[offset++] = data.nib_avgTiltDeg;

  // Stabilizer parameters
  array[offset++] = data.stabilizer_microJitterRadiusPx;
  array[offset++] = data.stabilizer_curveSmoothMin;
  array[offset++] = data.stabilizer_curveSmoothMax;
  array[offset++] = data.stabilizer_velocityMin;
  array[offset++] = data.stabilizer_velocityMax;

  // Padding
  array[offset++] = data._padding2;
  array[offset++] = data._padding3;
  array[offset++] = data._padding4;

  return array;
}
