/**
 * Week 3 v1.2: Temporal Design Variations - Engine
 *
 * Keyframe-based design evolution engine.
 * Generates design animations through time-based interpolation.
 */

import type {
  TemporalSchema,
  DesignKeyframe,
  InterpolatedFrame,
  AnimationTimeline,
  TemporalVariationConfig,
  EasingFunction
} from './types';
import type { BaseSchema, SemanticNode } from '../schema/types';
import { ulid } from '../../utils/ulid';

/**
 * Temporal Variation Engine - Design evolution over time
 */
export class TemporalVariationEngine {
  /**
   * Create temporal schema from configuration
   */
  createTemporalSchema(config: TemporalVariationConfig): TemporalSchema {
    const keyframes: DesignKeyframe[] = [
      {
        keyframe_id: ulid(),
        time: 0,
        schema: config.start_schema,
        easing: config.easing || 'ease_in_out'
      },
      {
        keyframe_id: ulid(),
        time: config.duration,
        schema: config.end_schema,
        easing: config.easing || 'ease_in_out'
      }
    ];

    // Generate intermediate keyframes if requested
    if (config.intermediate_keyframes && config.intermediate_keyframes > 0) {
      const intermediates = this.generateIntermediateKeyframes(
        config.start_schema,
        config.end_schema,
        config.duration,
        config.intermediate_keyframes,
        config.easing || 'ease_in_out'
      );
      keyframes.splice(1, 0, ...intermediates);
    }

    return {
      temporal_id: ulid(),
      name: `${config.start_schema.intent} → Evolution`,
      base_schema: config.start_schema,
      keyframes,
      duration: config.duration,
      created_at: Date.now()
    };
  }

  /**
   * Generate animation timeline from temporal schema
   */
  generateTimeline(
    temporal_schema: TemporalSchema,
    fps: number = 30
  ): AnimationTimeline {
    const total_frames = Math.ceil((temporal_schema.duration / 1000) * fps);
    const frames: InterpolatedFrame[] = [];

    for (let i = 0; i < total_frames; i++) {
      const time = (i / fps) * 1000; // Convert to milliseconds
      const frame = this.interpolateAtTime(temporal_schema, time);
      frames.push(frame);
    }

    return {
      timeline_id: ulid(),
      temporal_schema,
      frame_rate: fps,
      total_frames,
      frames
    };
  }

  /**
   * Interpolate schema at specific time
   */
  interpolateAtTime(temporal_schema: TemporalSchema, time: number): InterpolatedFrame {
    // Clamp time to duration
    const clamped_time = Math.max(0, Math.min(time, temporal_schema.duration));

    // Find surrounding keyframes
    const { before, after } = this.findSurroundingKeyframes(
      temporal_schema.keyframes,
      clamped_time
    );

    // Calculate interpolation factor
    const time_span = after.time - before.time;
    const time_offset = clamped_time - before.time;
    const raw_factor = time_span > 0 ? time_offset / time_span : 0;

    // Apply easing
    const easing = before.easing || 'linear';
    const eased_factor = this.applyEasing(raw_factor, easing);

    // Interpolate schema
    const interpolated_schema = this.interpolateSchemas(
      before.schema,
      after.schema,
      eased_factor
    );

    return {
      frame_id: ulid(),
      time: clamped_time,
      schema: interpolated_schema,
      source_keyframes: { before, after },
      interpolation_factor: eased_factor
    };
  }

  /**
   * Find keyframes surrounding a time point
   */
  private findSurroundingKeyframes(
    keyframes: DesignKeyframe[],
    time: number
  ): { before: DesignKeyframe; after: DesignKeyframe } {
    // Sort keyframes by time
    const sorted = [...keyframes].sort((a, b) => a.time - b.time);

    // Find surrounding keyframes
    for (let i = 0; i < sorted.length - 1; i++) {
      if (time >= sorted[i].time && time <= sorted[i + 1].time) {
        return { before: sorted[i], after: sorted[i + 1] };
      }
    }

    // Default to first and last
    return { before: sorted[0], after: sorted[sorted.length - 1] };
  }

  /**
   * Interpolate between two schemas
   */
  private interpolateSchemas(
    schema_a: BaseSchema,
    schema_b: BaseSchema,
    factor: number
  ): BaseSchema {
    const result = JSON.parse(JSON.stringify(schema_a)) as BaseSchema;

    // Interpolate each semantic node
    for (let i = 0; i < result.semantic_nodes.length; i++) {
      const node_a = schema_a.semantic_nodes[i];
      const node_b = schema_b.semantic_nodes[i];

      if (!node_b) continue;

      result.semantic_nodes[i] = this.interpolateNodes(node_a, node_b, factor);
    }

    // Interpolate aesthetic profile
    result.aesthetic_profile = this.interpolateAestheticProfile(
      schema_a.aesthetic_profile,
      schema_b.aesthetic_profile,
      factor
    );

    return result;
  }

  /**
   * Interpolate between two nodes
   */
  private interpolateNodes(
    node_a: SemanticNode,
    node_b: SemanticNode,
    factor: number
  ): SemanticNode {
    const result = JSON.parse(JSON.stringify(node_a)) as SemanticNode;

    // Interpolate bounds
    result.bounds = {
      x: this.lerp(node_a.bounds.x, node_b.bounds.x, factor),
      y: this.lerp(node_a.bounds.y, node_b.bounds.y, factor),
      width: this.lerp(node_a.bounds.width, node_b.bounds.width, factor),
      height: this.lerp(node_a.bounds.height, node_b.bounds.height, factor)
    };

    // Interpolate numeric properties
    for (const [key, value_a] of Object.entries(node_a.properties)) {
      const value_b = node_b.properties[key];

      if (typeof value_a === 'number' && typeof value_b === 'number') {
        result.properties[key] = this.lerp(value_a, value_b, factor);
      } else if (
        typeof value_a === 'string' &&
        typeof value_b === 'string' &&
        this.isColor(value_a) &&
        this.isColor(value_b)
      ) {
        result.properties[key] = this.lerpColor(value_a, value_b, factor);
      } else {
        // Non-numeric: use threshold
        result.properties[key] = factor < 0.5 ? value_a : value_b;
      }
    }

    return result;
  }

  /**
   * Interpolate aesthetic profile
   */
  private interpolateAestheticProfile(
    profile_a: BaseSchema['aesthetic_profile'],
    profile_b: BaseSchema['aesthetic_profile'],
    factor: number
  ): BaseSchema['aesthetic_profile'] {
    return {
      style_embedding_id: profile_a.style_embedding_id,
      design_language: factor < 0.5 ? profile_a.design_language : profile_b.design_language,
      color_harmony: factor < 0.5 ? profile_a.color_harmony : profile_b.color_harmony,
      texture_density: this.lerp(profile_a.texture_density, profile_b.texture_density, factor),
      color_palette: {
        primary: this.lerpColor(
          profile_a.color_palette.primary,
          profile_b.color_palette.primary,
          factor
        ),
        secondary: this.lerpColor(
          profile_a.color_palette.secondary,
          profile_b.color_palette.secondary,
          factor
        ),
        accents: profile_a.color_palette.accents, // Keep from A
        neutrals: profile_a.color_palette.neutrals,
        harmony_rule: factor < 0.5 ? profile_a.color_palette.harmony_rule : profile_b.color_palette.harmony_rule
      },
      typography: {
        font_family_primary: profile_a.typography.font_family_primary,
        font_family_secondary: profile_a.typography.font_family_secondary,
        heading_size: this.lerp(
          profile_a.typography.heading_size,
          profile_b.typography.heading_size,
          factor
        ),
        body_size: this.lerp(
          profile_a.typography.body_size,
          profile_b.typography.body_size,
          factor
        ),
        line_height: this.lerp(
          profile_a.typography.line_height,
          profile_b.typography.line_height,
          factor
        ),
        letter_spacing: this.lerp(
          profile_a.typography.letter_spacing,
          profile_b.typography.letter_spacing,
          factor
        )
      },
      spacing_system: {
        base_unit: Math.round(
          this.lerp(
            profile_a.spacing_system.base_unit,
            profile_b.spacing_system.base_unit,
            factor
          )
        ),
        scale_factor: this.lerp(
          profile_a.spacing_system.scale_factor,
          profile_b.spacing_system.scale_factor,
          factor
        )
      },
      visual_language: {
        border_radius: Math.round(
          this.lerp(
            profile_a.visual_language.border_radius,
            profile_b.visual_language.border_radius,
            factor
          )
        ),
        border_width: Math.round(
          this.lerp(
            profile_a.visual_language.border_width,
            profile_b.visual_language.border_width,
            factor
          )
        ),
        shadow_intensity: this.lerp(
          profile_a.visual_language.shadow_intensity,
          profile_b.visual_language.shadow_intensity,
          factor
        )
      }
    };
  }

  /**
   * Generate intermediate keyframes
   */
  private generateIntermediateKeyframes(
    start_schema: BaseSchema,
    end_schema: BaseSchema,
    duration: number,
    count: number,
    easing: EasingFunction
  ): DesignKeyframe[] {
    const keyframes: DesignKeyframe[] = [];

    for (let i = 1; i <= count; i++) {
      const factor = i / (count + 1);
      const time = duration * factor;
      const eased_factor = this.applyEasing(factor, easing);

      const interpolated = this.interpolateSchemas(start_schema, end_schema, eased_factor);

      keyframes.push({
        keyframe_id: ulid(),
        time,
        schema: interpolated,
        easing
      });
    }

    return keyframes;
  }

  /**
   * Apply easing function
   */
  private applyEasing(t: number, easing: EasingFunction): number {
    switch (easing) {
      case 'linear':
        return t;
      case 'ease_in':
        return t * t;
      case 'ease_out':
        return t * (2 - t);
      case 'ease_in_out':
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      case 'cubic_bezier':
        return t * t * (3 - 2 * t);
      case 'spring':
        return 1 - Math.cos(t * Math.PI * 2) * Math.exp(-t * 4);
      case 'bounce':
        if (t < 1 / 2.75) {
          return 7.5625 * t * t;
        } else if (t < 2 / 2.75) {
          return 7.5625 * (t -= 1.5 / 2.75) * t + 0.75;
        } else if (t < 2.5 / 2.75) {
          return 7.5625 * (t -= 2.25 / 2.75) * t + 0.9375;
        } else {
          return 7.5625 * (t -= 2.625 / 2.75) * t + 0.984375;
        }
      default:
        return t;
    }
  }

  /**
   * Linear interpolation
   */
  private lerp(a: number, b: number, t: number): number {
    return a * (1 - t) + b * t;
  }

  /**
   * Color interpolation (hex)
   */
  private lerpColor(color_a: string, color_b: string, t: number): string {
    const rgb_a = this.hexToRgb(color_a);
    const rgb_b = this.hexToRgb(color_b);

    if (!rgb_a || !rgb_b) return color_a;

    const r = Math.round(this.lerp(rgb_a.r, rgb_b.r, t));
    const g = Math.round(this.lerp(rgb_a.g, rgb_b.g, t));
    const b = Math.round(this.lerp(rgb_a.b, rgb_b.b, t));

    return this.rgbToHex(r, g, b);
  }

  /**
   * Check if string is a color
   */
  private isColor(str: string): boolean {
    return /^#[0-9A-F]{6}$/i.test(str);
  }

  /**
   * Convert hex to RGB
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
   * Convert RGB to hex
   */
  private rgbToHex(r: number, g: number, b: number): string {
    return '#' + [r, g, b].map((x) => x.toString(16).padStart(2, '0')).join('');
  }
}

// Singleton instance
export const temporalVariationEngine = new TemporalVariationEngine();
