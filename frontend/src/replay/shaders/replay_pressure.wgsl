/**
 * replay_pressure.wgsl - Pressure heatmap visualization
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 2: GPU Renderer
 *
 * Renders a heatmap showing pressure distribution:
 * - Low pressure (0.0-0.3): Blue/Cyan
 * - Medium pressure (0.3-0.7): Green/Yellow
 * - High pressure (0.7-1.0): Orange/Red
 */

struct Uniforms {
  canvasWidth: f32,
  canvasHeight: f32,
  devicePixelRatio: f32,
  time: f32,
  colorIntensity: f32,
  _padding1: f32,
  _padding2: f32,
  _padding3: f32,
}

struct StrokePoint {
  position: vec2<f32>,
  pressure: f32,
  radius: f32,
  normalizedTime: f32,
  _padding1: f32,
  _padding2: f32,
  _padding3: f32,
}

@group(0) @binding(0) var<uniform> uniforms: Uniforms;
@group(0) @binding(1) var<storage, read> points: array<StrokePoint>;
@group(0) @binding(2) var outputTexture: texture_storage_2d<rgba8unorm, write>;

/**
 * Pressure to color mapping (blue → cyan → green → yellow → orange → red)
 */
fn pressureToColor(pressure: f32) -> vec4<f32> {
  let p = clamp(pressure, 0.0, 1.0);

  var color: vec3<f32>;

  if (p < 0.3) {
    // Low pressure: Blue (0,0,1) → Cyan (0,1,1)
    let t = p / 0.3;
    color = mix(vec3<f32>(0.0, 0.0, 1.0), vec3<f32>(0.0, 1.0, 1.0), t);
  } else if (p < 0.5) {
    // Medium-low: Cyan (0,1,1) → Green (0,1,0)
    let t = (p - 0.3) / 0.2;
    color = mix(vec3<f32>(0.0, 1.0, 1.0), vec3<f32>(0.0, 1.0, 0.0), t);
  } else if (p < 0.7) {
    // Medium-high: Green (0,1,0) → Yellow (1,1,0)
    let t = (p - 0.5) / 0.2;
    color = mix(vec3<f32>(0.0, 1.0, 0.0), vec3<f32>(1.0, 1.0, 0.0), t);
  } else if (p < 0.85) {
    // High: Yellow (1,1,0) → Orange (1,0.5,0)
    let t = (p - 0.7) / 0.15;
    color = mix(vec3<f32>(1.0, 1.0, 0.0), vec3<f32>(1.0, 0.5, 0.0), t);
  } else {
    // Very high: Orange (1,0.5,0) → Red (1,0,0)
    let t = (p - 0.85) / 0.15;
    color = mix(vec3<f32>(1.0, 0.5, 0.0), vec3<f32>(1.0, 0.0, 0.0), t);
  }

  return vec4<f32>(color * uniforms.colorIntensity, 1.0);
}

/**
 * Smooth falloff function for brush stamps
 */
fn smoothFalloff(distance: f32, radius: f32) -> f32 {
  if (distance >= radius) {
    return 0.0;
  }

  let normalized = distance / radius;
  // Smooth hermite interpolation
  return 1.0 - normalized * normalized * (3.0 - 2.0 * normalized);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) globalId: vec3<u32>) {
  let pixelCoord = vec2<i32>(globalId.xy);
  let texSize = textureDimensions(outputTexture);

  if (pixelCoord.x >= texSize.x || pixelCoord.y >= texSize.y) {
    return;
  }

  let pixelPos = vec2<f32>(f32(pixelCoord.x), f32(pixelCoord.y)) / uniforms.devicePixelRatio;

  var accumulatedColor = vec3<f32>(0.0, 0.0, 0.0);
  var totalWeight = 0.0;

  // Iterate through all points and accumulate weighted pressure colors
  let pointCount = arrayLength(&points);

  for (var i = 0u; i < pointCount; i = i + 1u) {
    let point = points[i];

    // Skip points that haven't appeared yet (based on time)
    if (point.normalizedTime > uniforms.time) {
      continue;
    }

    let dx = pixelPos.x - point.position.x;
    let dy = pixelPos.y - point.position.y;
    let distance = sqrt(dx * dx + dy * dy);

    if (distance < point.radius) {
      let weight = smoothFalloff(distance, point.radius);
      let color = pressureToColor(point.pressure);

      accumulatedColor = accumulatedColor + color.rgb * weight;
      totalWeight = totalWeight + weight;
    }
  }

  var finalColor: vec4<f32>;

  if (totalWeight > 0.0) {
    finalColor = vec4<f32>(accumulatedColor / totalWeight, 1.0);
  } else {
    // Background color (white)
    finalColor = vec4<f32>(1.0, 1.0, 1.0, 1.0);
  }

  textureStore(outputTexture, pixelCoord, finalColor);
}
