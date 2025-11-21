/**
 * Week 5: Style DNA Encoding - DNA Blender
 *
 * Blends and interpolates DNA across tiers.
 * Creative interpolation for style mixing.
 */

import type {
  StrokeDNA,
  ImageDNA,
  TemporalDNA,
  CompositeDNA,
  DNABlender as IDNABlender
} from './types';
import { ulid } from '../../utils/ulid';

/**
 * Blending Mode
 */
export type BlendingMode = 'linear' | 'ease_in' | 'ease_out' | 'ease_in_out';

/**
 * DNA Blender
 * Interpolates between DNA encodings
 */
export class DNABlender {
  /**
   * Blend two stroke DNAs
   */
  blendStrokeDNA(dna_a: StrokeDNA, dna_b: StrokeDNA, alpha: number): StrokeDNA {
    const features = new Float32Array(dna_a.features.length);

    for (let i = 0; i < features.length; i++) {
      features[i] = this.lerp(dna_a.features[i], dna_b.features[i], alpha);
    }

    return {
      dna_id: ulid(),
      stroke_id: ulid(),
      session_id: dna_a.session_id,
      features,
      normalized_bounds: dna_a.normalized_bounds
        ? {
            x: this.lerp(
              dna_a.normalized_bounds.x,
              dna_b.normalized_bounds?.x || 0,
              alpha
            ),
            y: this.lerp(
              dna_a.normalized_bounds.y,
              dna_b.normalized_bounds?.y || 0,
              alpha
            ),
            width: this.lerp(
              dna_a.normalized_bounds.width,
              dna_b.normalized_bounds?.width || 0,
              alpha
            ),
            height: this.lerp(
              dna_a.normalized_bounds.height,
              dna_b.normalized_bounds?.height || 0,
              alpha
            )
          }
        : undefined,
      tool: alpha < 0.5 ? dna_a.tool : dna_b.tool,
      color: this.blendColors(dna_a.color, dna_b.color, alpha),
      timestamp: Date.now(),
      encoding_time_ms: 0
    };
  }

  /**
   * Blend two image DNAs
   */
  blendImageDNA(dna_a: ImageDNA, dna_b: ImageDNA, alpha: number): ImageDNA {
    const features = new Float32Array(dna_a.features.length);

    for (let i = 0; i < features.length; i++) {
      features[i] = this.lerp(dna_a.features[i], dna_b.features[i], alpha);
    }

    // Blend texture features
    const texture_features = {
      complexity: this.lerp(
        dna_a.texture_features.complexity,
        dna_b.texture_features.complexity,
        alpha
      ),
      contrast: this.lerp(
        dna_a.texture_features.contrast,
        dna_b.texture_features.contrast,
        alpha
      ),
      energy: this.lerp(
        dna_a.texture_features.energy,
        dna_b.texture_features.energy,
        alpha
      )
    };

    // Mix dominant colors
    const dominant_colors = this.mixColorArrays(
      dna_a.dominant_colors,
      dna_b.dominant_colors,
      alpha
    );

    return {
      dna_id: ulid(),
      session_id: dna_a.session_id,
      snapshot_id: ulid(),
      features,
      dominant_colors,
      texture_features,
      width: Math.round(this.lerp(dna_a.width, dna_b.width, alpha)),
      height: Math.round(this.lerp(dna_a.height, dna_b.height, alpha)),
      timestamp: Date.now(),
      encoding_time_ms: 0
    };
  }

  /**
   * Blend two temporal DNAs
   */
  blendTemporalDNA(
    dna_a: TemporalDNA,
    dna_b: TemporalDNA,
    alpha: number
  ): TemporalDNA {
    const features = new Float32Array(dna_a.features.length);

    for (let i = 0; i < features.length; i++) {
      features[i] = this.lerp(dna_a.features[i], dna_b.features[i], alpha);
    }

    // Blend scalar properties
    const fatigue_level = this.lerp(dna_a.fatigue_level, dna_b.fatigue_level, alpha);
    const focus_score = this.lerp(dna_a.focus_score, dna_b.focus_score, alpha);
    const skill_progression = this.lerp(
      dna_a.skill_progression,
      dna_b.skill_progression,
      alpha
    );

    // Choose learning phase from dominant DNA
    const learning_phase = alpha < 0.5 ? dna_a.learning_phase : dna_b.learning_phase;

    return {
      dna_id: ulid(),
      session_id: dna_a.session_id,
      artist_id: dna_a.artist_id,
      features,
      learning_phase,
      skill_progression,
      fatigue_level,
      focus_score,
      flow_state: dna_a.flow_state || dna_b.flow_state,
      total_sessions: Math.round(
        this.lerp(dna_a.total_sessions, dna_b.total_sessions, alpha)
      ),
      total_strokes: Math.round(
        this.lerp(dna_a.total_strokes, dna_b.total_strokes, alpha)
      ),
      timestamp: Date.now(),
      encoding_time_ms: 0
    };
  }

  /**
   * Blend multiple DNAs with weights
   */
  blendMultipleStrokeDNAs(dnas: StrokeDNA[], weights: number[]): StrokeDNA {
    if (dnas.length === 0) {
      throw new Error('Cannot blend empty array');
    }

    if (dnas.length !== weights.length) {
      throw new Error('DNAs and weights arrays must have same length');
    }

    // Normalize weights
    const total_weight = weights.reduce((a, b) => a + b, 0);
    const normalized_weights = weights.map((w) => w / total_weight);

    // Weighted average of features
    const features = new Float32Array(dnas[0].features.length);
    for (let i = 0; i < features.length; i++) {
      let weighted_sum = 0;
      for (let j = 0; j < dnas.length; j++) {
        weighted_sum += dnas[j].features[i] * normalized_weights[j];
      }
      features[i] = weighted_sum;
    }

    // Choose tool and color from highest weight DNA
    const max_weight_index = weights.indexOf(Math.max(...weights));

    return {
      dna_id: ulid(),
      stroke_id: ulid(),
      session_id: dnas[0].session_id,
      features,
      normalized_bounds: dnas[max_weight_index].normalized_bounds,
      tool: dnas[max_weight_index].tool,
      color: dnas[max_weight_index].color,
      timestamp: Date.now(),
      encoding_time_ms: 0
    };
  }

  /**
   * Apply easing function to alpha
   */
  applyEasing(alpha: number, mode: BlendingMode): number {
    switch (mode) {
      case 'linear':
        return alpha;
      case 'ease_in':
        return alpha * alpha;
      case 'ease_out':
        return alpha * (2 - alpha);
      case 'ease_in_out':
        return alpha < 0.5 ? 2 * alpha * alpha : -1 + (4 - 2 * alpha) * alpha;
    }
  }

  /**
   * Interpolate with easing
   */
  blendWithEasing(
    dna_a: StrokeDNA,
    dna_b: StrokeDNA,
    alpha: number,
    mode: BlendingMode
  ): StrokeDNA {
    const eased_alpha = this.applyEasing(alpha, mode);
    return this.blendStrokeDNA(dna_a, dna_b, eased_alpha);
  }

  /**
   * Linear interpolation
   */
  private lerp(a: number, b: number, t: number): number {
    return a * (1 - t) + b * t;
  }

  /**
   * Blend two hex colors
   */
  private blendColors(color_a: string, color_b: string, alpha: number): string {
    const rgb_a = this.hexToRgb(color_a);
    const rgb_b = this.hexToRgb(color_b);

    if (!rgb_a || !rgb_b) return color_a;

    const r = Math.round(this.lerp(rgb_a.r, rgb_b.r, alpha));
    const g = Math.round(this.lerp(rgb_a.g, rgb_b.g, alpha));
    const b = Math.round(this.lerp(rgb_a.b, rgb_b.b, alpha));

    return this.rgbToHex(r, g, b);
  }

  /**
   * Mix color arrays
   */
  private mixColorArrays(
    colors_a: string[],
    colors_b: string[],
    alpha: number
  ): string[] {
    const max_length = Math.max(colors_a.length, colors_b.length);
    const result: string[] = [];

    for (let i = 0; i < max_length; i++) {
      const color_a = colors_a[i] || colors_a[0];
      const color_b = colors_b[i] || colors_b[0];
      result.push(this.blendColors(color_a, color_b, alpha));
    }

    return result;
  }

  /**
   * Hex to RGB
   */
  private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        }
      : null;
  }

  /**
   * RGB to Hex
   */
  private rgbToHex(r: number, g: number, b: number): string {
    return (
      '#' +
      [r, g, b]
        .map((x) => Math.round(x).toString(16).padStart(2, '0'))
        .join('')
    );
  }
}

/**
 * Global blender instance
 */
export const globalDNABlender = new DNABlender();
