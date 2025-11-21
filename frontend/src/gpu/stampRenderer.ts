/**
 * Stamp Renderer - GPU-accelerated stamp-based rendering.
 *
 * This module handles:
 * - Render pipeline creation
 * - Buffer management (uniforms, stamps)
 * - Stamp rendering at 60 FPS
 * - Texture compositing to canvas
 */

import { GPUDeviceContext, CanvasContext, StampData, shaderConstantsToUniformData, uniformDataToFloat32Array } from './types';
import { ShaderConstants } from '../services/ProfileContext';
import { compileShaders } from './shaderCompiler';
import { createBuffer, createTexture, writeBuffer, clearTexture } from './device';

export interface StampRendererConfig {
  /** GPU device context */
  deviceContext: GPUDeviceContext;

  /** Shader constants from artist profile */
  shaderConstants: ShaderConstants;

  /** Canvas width in pixels */
  canvasWidth: number;

  /** Canvas height in pixels */
  canvasHeight: number;
}

export class StampRenderer {
  private deviceContext: GPUDeviceContext;
  private shaderConstants: ShaderConstants;
  private canvasWidth: number;
  private canvasHeight: number;

  // GPU resources
  private computePipeline: GPUComputePipeline | null = null;
  private renderPipeline: GPURenderPipeline | null = null;
  private uniformBuffer: GPUBuffer | null = null;
  private stampBuffer: GPUBuffer | null = null;
  private renderTexture: GPUTexture | null = null;
  private computeBindGroup: GPUBindGroup | null = null;
  private renderBindGroup: GPUBindGroup | null = null;
  private sampler: GPUSampler | null = null;

  // Stamp data
  private stamps: StampData[] = [];
  private maxStamps: number = 10000;

  constructor(config: StampRendererConfig) {
    this.deviceContext = config.deviceContext;
    this.shaderConstants = config.shaderConstants;
    this.canvasWidth = config.canvasWidth;
    this.canvasHeight = config.canvasHeight;
  }

  /**
   * Initialize GPU resources (pipelines, buffers, textures).
   */
  async initialize(): Promise<void> {
    const { device, format } = this.deviceContext;

    console.log('[StampRenderer] Initializing GPU resources...');

    // Compile shaders
    const { computeShader, vertexShader, fragmentShader } = compileShaders(
      device,
      this.shaderConstants
    );

    // Create uniform buffer (256 bytes, aligned)
    this.uniformBuffer = createBuffer(
      device,
      256,
      GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST
    );

    // Write initial uniform data
    this.updateUniforms();

    // Create stamp buffer (storage buffer, resizable)
    const stampStride = 48; // 12 floats * 4 bytes = 48 bytes per stamp
    this.stampBuffer = createBuffer(
      device,
      this.maxStamps * stampStride,
      GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST
    );

    // Create render texture
    this.renderTexture = createTexture(
      device,
      this.canvasWidth,
      this.canvasHeight,
      'rgba8unorm',
      GPUTextureUsage.STORAGE_BINDING | GPUTextureUsage.TEXTURE_BINDING | GPUTextureUsage.RENDER_ATTACHMENT
    );

    // Clear render texture
    clearTexture(device, this.renderTexture);

    // Create sampler
    this.sampler = device.createSampler({
      magFilter: 'linear',
      minFilter: 'linear',
      addressModeU: 'clamp-to-edge',
      addressModeV: 'clamp-to-edge'
    });

    // Create compute pipeline
    this.computePipeline = device.createComputePipeline({
      label: 'Stamp Compute Pipeline',
      layout: 'auto',
      compute: {
        module: computeShader,
        entryPoint: 'main'
      }
    });

    // Create compute bind group
    this.computeBindGroup = device.createBindGroup({
      label: 'Compute Bind Group',
      layout: this.computePipeline.getBindGroupLayout(0),
      entries: [
        {
          binding: 0,
          resource: { buffer: this.uniformBuffer }
        },
        {
          binding: 1,
          resource: { buffer: this.stampBuffer }
        },
        {
          binding: 2,
          resource: this.renderTexture.createView()
        }
      ]
    });

    // Create render pipeline (for compositing to canvas)
    this.renderPipeline = device.createRenderPipeline({
      label: 'Composite Render Pipeline',
      layout: 'auto',
      vertex: {
        module: vertexShader,
        entryPoint: 'main'
      },
      fragment: {
        module: fragmentShader,
        entryPoint: 'main',
        targets: [
          {
            format,
            blend: {
              color: {
                srcFactor: 'src-alpha',
                dstFactor: 'one-minus-src-alpha',
                operation: 'add'
              },
              alpha: {
                srcFactor: 'one',
                dstFactor: 'one-minus-src-alpha',
                operation: 'add'
              }
            }
          }
        ]
      },
      primitive: {
        topology: 'triangle-list'
      }
    });

    // Create render bind group
    this.renderBindGroup = device.createBindGroup({
      label: 'Render Bind Group',
      layout: this.renderPipeline.getBindGroupLayout(0),
      entries: [
        {
          binding: 0,
          resource: this.sampler
        },
        {
          binding: 1,
          resource: this.renderTexture.createView()
        }
      ]
    });

    console.log('[StampRenderer] Initialization complete');
  }

  /**
   * Update uniform buffer with current canvas dimensions and profile constants.
   */
  private updateUniforms(): void {
    if (!this.uniformBuffer) return;

    const uniformData = shaderConstantsToUniformData(
      this.shaderConstants,
      this.canvasWidth,
      this.canvasHeight,
      this.deviceContext.devicePixelRatio
    );

    const uniformArray = uniformDataToFloat32Array(uniformData);

    writeBuffer(this.deviceContext.device, this.uniformBuffer, uniformArray);
  }

  /**
   * Add a stamp to the render queue.
   */
  addStamp(stamp: StampData): void {
    if (this.stamps.length >= this.maxStamps) {
      console.warn('[StampRenderer] Max stamps reached, dropping oldest');
      this.stamps.shift();
    }

    this.stamps.push(stamp);
  }

  /**
   * Add multiple stamps to the render queue.
   */
  addStamps(stamps: StampData[]): void {
    stamps.forEach(stamp => this.addStamp(stamp));
  }

  /**
   * Clear all stamps.
   */
  clearStamps(): void {
    this.stamps = [];
  }

  /**
   * Update stamp buffer with current stamp data.
   */
  private updateStampBuffer(): void {
    if (!this.stampBuffer || this.stamps.length === 0) return;

    // Stamp struct layout (must match WGSL shader):
    // - position: vec2<f32> (2 floats)
    // - radius: f32 (1 float)
    // - _padding1: f32 (1 float)
    // - color: vec4<f32> (4 floats)
    // - density: f32 (1 float)
    // - softness: f32 (1 float)
    // - semanticWeight: f32 (1 float)
    // - _padding2: f32 (1 float)
    // Total: 12 floats per stamp
    const stampStride = 12;
    const stampArray = new Float32Array(this.stamps.length * stampStride);

    for (let i = 0; i < this.stamps.length; i++) {
      const stamp = this.stamps[i];
      const offset = i * stampStride;

      // Position (vec2)
      stampArray[offset + 0] = stamp.x;
      stampArray[offset + 1] = stamp.y;

      // Radius (f32)
      stampArray[offset + 2] = stamp.radius;

      // Padding (f32)
      stampArray[offset + 3] = 0;

      // Color (vec4)
      stampArray[offset + 4] = stamp.color[0];
      stampArray[offset + 5] = stamp.color[1];
      stampArray[offset + 6] = stamp.color[2];
      stampArray[offset + 7] = stamp.color[3];

      // Density (f32)
      stampArray[offset + 8] = stamp.density;

      // Softness (f32)
      stampArray[offset + 9] = stamp.softness;

      // Semantic weight (f32)
      stampArray[offset + 10] = stamp.semanticWeight;

      // Padding (f32)
      stampArray[offset + 11] = 0;
    }

    writeBuffer(this.deviceContext.device, this.stampBuffer, stampArray);
  }

  /**
   * Render stamps to canvas.
   *
   * @param canvasContext - Canvas context wrapper
   */
  render(canvasContext: CanvasContext): void {
    if (!this.computePipeline || !this.renderPipeline || !this.renderTexture) {
      console.warn('[StampRenderer] Not initialized');
      return;
    }

    const { device } = this.deviceContext;

    // Update stamp buffer
    this.updateStampBuffer();

    // Create command encoder
    const commandEncoder = device.createCommandEncoder({
      label: 'Stamp Render Commands'
    });

    // Compute pass - render stamps to texture
    if (this.stamps.length > 0 && this.computeBindGroup) {
      const computePass = commandEncoder.beginComputePass({
        label: 'Stamp Compute Pass'
      });

      computePass.setPipeline(this.computePipeline);
      computePass.setBindGroup(0, this.computeBindGroup);

      // Dispatch compute shader (8x8 workgroups)
      const workgroupsX = Math.ceil(this.canvasWidth / 8);
      const workgroupsY = Math.ceil(this.canvasHeight / 8);
      computePass.dispatchWorkgroups(workgroupsX, workgroupsY);

      computePass.end();
    }

    // Render pass - composite to canvas
    const canvasTexture = canvasContext.context.getCurrentTexture();
    const renderPass = commandEncoder.beginRenderPass({
      label: 'Composite Render Pass',
      colorAttachments: [
        {
          view: canvasTexture.createView(),
          loadOp: 'clear',
          clearValue: { r: 1, g: 1, b: 1, a: 1 }, // White background
          storeOp: 'store'
        }
      ]
    });

    if (this.renderBindGroup) {
      renderPass.setPipeline(this.renderPipeline);
      renderPass.setBindGroup(0, this.renderBindGroup);
      renderPass.draw(6); // 6 vertices for full-screen quad
    }

    renderPass.end();

    // Submit commands
    device.queue.submit([commandEncoder.finish()]);
  }

  /**
   * Resize renderer to new canvas dimensions.
   */
  resize(width: number, height: number): void {
    this.canvasWidth = width;
    this.canvasHeight = height;

    // Update uniforms
    this.updateUniforms();

    // Recreate render texture
    if (this.renderTexture) {
      this.renderTexture.destroy();
    }

    this.renderTexture = createTexture(
      this.deviceContext.device,
      width,
      height,
      'rgba8unorm',
      GPUTextureUsage.STORAGE_BINDING | GPUTextureUsage.TEXTURE_BINDING | GPUTextureUsage.RENDER_ATTACHMENT
    );

    // Clear new texture
    clearTexture(this.deviceContext.device, this.renderTexture);

    // Update compute bind group
    if (this.computePipeline && this.uniformBuffer && this.stampBuffer) {
      this.computeBindGroup = this.deviceContext.device.createBindGroup({
        label: 'Compute Bind Group',
        layout: this.computePipeline.getBindGroupLayout(0),
        entries: [
          {
            binding: 0,
            resource: { buffer: this.uniformBuffer }
          },
          {
            binding: 1,
            resource: { buffer: this.stampBuffer }
          },
          {
            binding: 2,
            resource: this.renderTexture.createView()
          }
        ]
      });
    }

    // Update render bind group
    if (this.renderPipeline && this.sampler) {
      this.renderBindGroup = this.deviceContext.device.createBindGroup({
        label: 'Render Bind Group',
        layout: this.renderPipeline.getBindGroupLayout(0),
        entries: [
          {
            binding: 0,
            resource: this.sampler
          },
          {
            binding: 1,
            resource: this.renderTexture.createView()
          }
        ]
      });
    }

    console.log('[StampRenderer] Resized to', width, 'x', height);
  }

  /**
   * Clear the render texture.
   */
  clear(): void {
    if (this.renderTexture) {
      clearTexture(this.deviceContext.device, this.renderTexture);
    }
    this.clearStamps();
  }

  /**
   * Destroy GPU resources.
   */
  destroy(): void {
    this.uniformBuffer?.destroy();
    this.stampBuffer?.destroy();
    this.renderTexture?.destroy();

    this.uniformBuffer = null;
    this.stampBuffer = null;
    this.renderTexture = null;
    this.computePipeline = null;
    this.renderPipeline = null;
    this.computeBindGroup = null;
    this.renderBindGroup = null;
    this.sampler = null;

    console.log('[StampRenderer] Destroyed');
  }
}
