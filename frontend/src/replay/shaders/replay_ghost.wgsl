/**
 * replay_ghost.wgsl - Ghost trail visualization
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 2: GPU Renderer
 *
 * Renders strokes with alpha fade based on temporal distance:
 * - Recent strokes: Opaque (alpha = 1.0)
 * - Older strokes: Transparent (alpha fades to 0.0)
 * - Creates a "ghost trail" effect showing drawing progression
 */

struct Uniforms {
  canvasWidth: f32,
  canvasHeight: f32,
  devicePixelRatio: f32,
  time: f32,  // Current normalized time [0, 1]
  trailDuration: f32,  // How far back in time to show trail (normalized time)
  colorIntensity: f32,
  _padding1: f32,
  _padding2: f32,
}

struct StrokePoint {
  position: vec2<f32>,
  radius: f32,
  normalizedTime: f32,
  color: vec4<f32>,  // RGBA color (original stroke color)
}

@group(0) @binding(0) var<uniform> uniforms: Uniforms;
@group(0) @binding(1) var<storage, read> points: array<StrokePoint>;
@group(0) @binding(2) var outputTexture: texture_storage_2d<rgba8unorm, write>;

/**
 * Calculate alpha based on temporal distance
 *
 * Recent strokes (within trailDuration) fade from 1.0 → 0.0
 * Older strokes are invisible
 */
fn calculateAlpha(pointTime: f32, currentTime: f32, trailDuration: f32) -> f32 {
  let timeDelta = currentTime - pointTime;

  if (timeDelta < 0.0 || timeDelta > trailDuration) {
    return 0.0;  // Point hasn't appeared yet or is too old
  }

  // Linear fade: 1.0 at current time → 0.0 at trailDuration ago
  let fadeProgress = timeDelta / trailDuration;

  // Apply smooth ease-out for more natural fade
  let smoothFade = 1.0 - (fadeProgress * fadeProgress);

  return smoothFade;
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

/**
 * Alpha blending: src over dst
 */
fn alphaBlend(src: vec4<f32>, dst: vec4<f32>) -> vec4<f32> {
  let srcAlpha = src.a;
  let dstAlpha = dst.a;

  let outAlpha = srcAlpha + dstAlpha * (1.0 - srcAlpha);

  if (outAlpha == 0.0) {
    return vec4<f32>(0.0, 0.0, 0.0, 0.0);
  }

  let outRgb = (src.rgb * srcAlpha + dst.rgb * dstAlpha * (1.0 - srcAlpha)) / outAlpha;

  return vec4<f32>(outRgb, outAlpha);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) globalId: vec3<u32>) {
  let pixelCoord = vec2<i32>(globalId.xy);
  let texSize = textureDimensions(outputTexture);

  if (pixelCoord.x >= texSize.x || pixelCoord.y >= texSize.y) {
    return;
  }

  let pixelPos = vec2<f32>(f32(pixelCoord.x), f32(pixelCoord.y)) / uniforms.devicePixelRatio;

  var accumulatedColor = vec4<f32>(0.0, 0.0, 0.0, 0.0);

  // Iterate through all points and accumulate with alpha blending
  let pointCount = arrayLength(&points);

  for (var i = 0u; i < pointCount; i = i + 1u) {
    let point = points[i];

    // Calculate temporal alpha
    let temporalAlpha = calculateAlpha(point.normalizedTime, uniforms.time, uniforms.trailDuration);

    if (temporalAlpha <= 0.0) {
      continue;  // Point not visible
    }

    let dx = pixelPos.x - point.position.x;
    let dy = pixelPos.y - point.position.y;
    let distance = sqrt(dx * dx + dy * dy);

    if (distance < point.radius) {
      let spatialFalloff = smoothFalloff(distance, point.radius);
      let finalAlpha = temporalAlpha * spatialFalloff;

      if (finalAlpha > 0.0) {
        let stampColor = vec4<f32>(
          point.color.rgb * uniforms.colorIntensity,
          finalAlpha
        );

        // Alpha blend with accumulated color
        accumulatedColor = alphaBlend(stampColor, accumulatedColor);
      }
    }
  }

  var finalColor: vec4<f32>;

  if (accumulatedColor.a > 0.0) {
    // Blend with white background
    let backgroundColor = vec4<f32>(1.0, 1.0, 1.0, 1.0);
    finalColor = alphaBlend(accumulatedColor, backgroundColor);
  } else {
    // Background color (white)
    finalColor = vec4<f32>(1.0, 1.0, 1.0, 1.0);
  }

  textureStore(outputTexture, pixelCoord, finalColor);
}
