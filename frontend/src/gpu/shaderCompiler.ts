/**
 * Shader Compiler - Converts artist profile to WGSL shaders.
 *
 * This module generates GPU shaders dynamically based on calibration data.
 * The generated shaders include:
 * - Bezier curve evaluation functions
 * - Pressure-to-radius mapping
 * - Pressure-to-density mapping
 * - Stamp rendering with semantic weighting
 */

import { ShaderConstants } from '../services/ProfileContext';

/**
 * Generate WGSL compute shader for stamp rendering.
 *
 * This shader:
 * 1. Reads stamp data (position, pressure, semantic weight)
 * 2. Evaluates Bezier curves to map pressure -> radius/density
 * 3. Renders circular stamps with soft edges
 * 4. Applies semantic weighting for facial features
 *
 * @param constants - Shader constants from artist profile
 * @returns WGSL shader source code
 */
export function compileComputeShader(constants: ShaderConstants): string {
  return `
// Uniform buffer - artist profile constants (256 bytes, aligned)
struct Uniforms {
  canvasSize: vec2<f32>,        // Canvas dimensions
  devicePixelRatio: f32,        // Device pixel ratio
  _padding1: f32,

  // Pressure -> Radius Bezier curve
  pressureToRadius_p0: vec2<f32>,
  pressureToRadius_p1: vec2<f32>,
  pressureToRadius_p2: vec2<f32>,
  pressureToRadius_p3: vec2<f32>,

  // Pressure -> Density Bezier curve
  pressureToDensity_p0: vec2<f32>,
  pressureToDensity_p1: vec2<f32>,
  pressureToDensity_p2: vec2<f32>,
  pressureToDensity_p3: vec2<f32>,

  // Nib parameters
  nib_baseRadiusPx: f32,
  nib_minRadiusPx: f32,
  nib_maxRadiusPx: f32,
  nib_avgTiltDeg: f32,

  // Stabilizer parameters
  stabilizer_microJitterRadiusPx: f32,
  stabilizer_curveSmoothMin: f32,
  stabilizer_curveSmoothMax: f32,
  stabilizer_velocityMin: f32,
  stabilizer_velocityMax: f32,

  _padding2: f32,
  _padding3: f32,
  _padding4: f32,
}

// Stamp data structure
struct Stamp {
  position: vec2<f32>,      // XY position
  radius: f32,              // Stamp radius
  color: vec4<f32>,         // RGBA color
  density: f32,             // Opacity/density
  softness: f32,            // Edge softness
  semanticWeight: f32,      // Semantic multiplier
  _padding: f32,
}

@group(0) @binding(0) var<uniform> uniforms: Uniforms;
@group(0) @binding(1) var<storage, read> stamps: array<Stamp>;
@group(0) @binding(2) var outputTexture: texture_storage_2d<rgba8unorm, write>;

// Evaluate cubic Bezier curve at parameter t
fn evaluateBezier(p0: vec2<f32>, p1: vec2<f32>, p2: vec2<f32>, p3: vec2<f32>, t: f32) -> vec2<f32> {
  let t_clamped = clamp(t, 0.0, 1.0);
  let u = 1.0 - t_clamped;

  // Cubic Bezier formula: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
  return u * u * u * p0 +
         3.0 * u * u * t_clamped * p1 +
         3.0 * u * t_clamped * t_clamped * p2 +
         t_clamped * t_clamped * t_clamped * p3;
}

// Map pressure to radius using calibration curve
fn pressureToRadius(pressure: f32, semanticWeight: f32) -> f32 {
  let result = evaluateBezier(
    uniforms.pressureToRadius_p0,
    uniforms.pressureToRadius_p1,
    uniforms.pressureToRadius_p2,
    uniforms.pressureToRadius_p3,
    pressure
  );

  // Y component is the radius (0-1 normalized)
  let normalizedRadius = result.y;

  // Scale by nib parameters and semantic weight
  let radius = mix(
    uniforms.nib_minRadiusPx,
    uniforms.nib_maxRadiusPx,
    normalizedRadius
  ) * semanticWeight;

  return clamp(radius, uniforms.nib_minRadiusPx, uniforms.nib_maxRadiusPx);
}

// Map pressure to density using calibration curve
fn pressureToDensity(pressure: f32, semanticWeight: f32) -> f32 {
  let result = evaluateBezier(
    uniforms.pressureToDensity_p0,
    uniforms.pressureToDensity_p1,
    uniforms.pressureToDensity_p2,
    uniforms.pressureToDensity_p3,
    pressure
  );

  // Y component is the density (0-1 normalized)
  let density = result.y * semanticWeight;

  return clamp(density, 0.0, 1.0);
}

// Render a single stamp (circular brush mark)
fn renderStamp(pixelPos: vec2<f32>, stamp: Stamp) -> vec4<f32> {
  // Calculate distance from stamp center
  let dx = pixelPos.x - stamp.position.x;
  let dy = pixelPos.y - stamp.position.y;
  let dist = sqrt(dx * dx + dy * dy);

  // Soft falloff based on radius and softness
  let softRadius = stamp.radius * (1.0 + stamp.softness);
  let falloff = 1.0 - smoothstep(stamp.radius, softRadius, dist);

  // Apply density
  let alpha = falloff * stamp.density;

  // Return color with alpha
  return vec4<f32>(stamp.color.rgb, alpha);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) globalId: vec3<u32>) {
  let pixelPos = vec2<f32>(f32(globalId.x), f32(globalId.y));
  let canvasSize = vec2<u32>(uniforms.canvasSize);

  // Bounds check
  if (globalId.x >= canvasSize.x || globalId.y >= canvasSize.y) {
    return;
  }

  // Accumulate color from all stamps
  var finalColor = vec4<f32>(0.0, 0.0, 0.0, 0.0);

  let stampCount = arrayLength(&stamps);
  for (var i = 0u; i < stampCount; i++) {
    let stamp = stamps[i];
    let stampColor = renderStamp(pixelPos, stamp);

    // Alpha blend
    finalColor = finalColor + stampColor * (1.0 - finalColor.a);
  }

  // Write to output texture
  textureStore(outputTexture, vec2<i32>(globalId.xy), finalColor);
}
`;
}

/**
 * Generate WGSL vertex shader for full-screen quad rendering.
 *
 * This shader is used to composite the final image to the canvas.
 */
export function compileVertexShader(): string {
  return `
struct VertexOutput {
  @builtin(position) position: vec4<f32>,
  @location(0) texCoord: vec2<f32>,
}

@vertex
fn main(@builtin(vertex_index) vertexIndex: u32) -> VertexOutput {
  var output: VertexOutput;

  // Full-screen quad (two triangles)
  var positions = array<vec2<f32>, 6>(
    vec2<f32>(-1.0, -1.0),  // Bottom-left
    vec2<f32>( 1.0, -1.0),  // Bottom-right
    vec2<f32>(-1.0,  1.0),  // Top-left
    vec2<f32>(-1.0,  1.0),  // Top-left
    vec2<f32>( 1.0, -1.0),  // Bottom-right
    vec2<f32>( 1.0,  1.0)   // Top-right
  );

  var texCoords = array<vec2<f32>, 6>(
    vec2<f32>(0.0, 1.0),  // Bottom-left
    vec2<f32>(1.0, 1.0),  // Bottom-right
    vec2<f32>(0.0, 0.0),  // Top-left
    vec2<f32>(0.0, 0.0),  // Top-left
    vec2<f32>(1.0, 1.0),  // Bottom-right
    vec2<f32>(1.0, 0.0)   // Top-right
  );

  output.position = vec4<f32>(positions[vertexIndex], 0.0, 1.0);
  output.texCoord = texCoords[vertexIndex];

  return output;
}
`;
}

/**
 * Generate WGSL fragment shader for compositing.
 *
 * This shader samples the rendered texture and outputs to the canvas.
 */
export function compileFragmentShader(): string {
  return `
@group(0) @binding(0) var textureSampler: sampler;
@group(0) @binding(1) var inputTexture: texture_2d<f32>;

@fragment
fn main(@location(0) texCoord: vec2<f32>) -> @location(0) vec4<f32> {
  return textureSample(inputTexture, textureSampler, texCoord);
}
`;
}

/**
 * Compile all shaders for the rendering pipeline.
 *
 * @param device - GPU device
 * @param constants - Shader constants from artist profile
 * @returns Compiled shader modules
 */
export function compileShaders(
  device: GPUDevice,
  constants: ShaderConstants
): {
  computeShader: GPUShaderModule;
  vertexShader: GPUShaderModule;
  fragmentShader: GPUShaderModule;
} {
  const computeSource = compileComputeShader(constants);
  const vertexSource = compileVertexShader();
  const fragmentSource = compileFragmentShader();

  console.log('[GPU] Compiling shaders...');

  const computeShader = device.createShaderModule({
    label: 'Stamp Compute Shader',
    code: computeSource
  });

  const vertexShader = device.createShaderModule({
    label: 'Fullscreen Vertex Shader',
    code: vertexSource
  });

  const fragmentShader = device.createShaderModule({
    label: 'Composite Fragment Shader',
    code: fragmentSource
  });

  console.log('[GPU] Shaders compiled successfully');

  return {
    computeShader,
    vertexShader,
    fragmentShader
  };
}
