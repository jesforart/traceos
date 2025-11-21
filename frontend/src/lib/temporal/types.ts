/**
 * Week 3 v1.2: Temporal Design Variations - Types
 *
 * Keyframe-based design evolution over time.
 */

import type { BaseSchema } from '../schema/types';

/**
 * Design Keyframe - Snapshot at specific time
 */
export interface DesignKeyframe {
  keyframe_id: string;
  time: number; // Milliseconds from start
  schema: BaseSchema;
  easing?: EasingFunction;
  metadata?: {
    label?: string;
    description?: string;
  };
}

/**
 * Easing functions for interpolation
 */
export type EasingFunction =
  | 'linear'
  | 'ease_in'
  | 'ease_out'
  | 'ease_in_out'
  | 'cubic_bezier'
  | 'spring'
  | 'bounce';

/**
 * Temporal Schema - Design that evolves over time
 */
export interface TemporalSchema {
  temporal_id: string;
  name: string;
  base_schema: BaseSchema;
  keyframes: DesignKeyframe[];
  duration: number; // Total duration in milliseconds
  loop?: boolean;
  created_at: number;
}

/**
 * Interpolated Frame - Generated frame at specific time
 */
export interface InterpolatedFrame {
  frame_id: string;
  time: number;
  schema: BaseSchema;
  source_keyframes: {
    before: DesignKeyframe;
    after: DesignKeyframe;
  };
  interpolation_factor: number; // 0.0 to 1.0
}

/**
 * Animation Timeline - Complete sequence
 */
export interface AnimationTimeline {
  timeline_id: string;
  temporal_schema: TemporalSchema;
  frame_rate: number; // FPS
  total_frames: number;
  frames: InterpolatedFrame[];
  export_format?: 'video' | 'gif' | 'frames';
}

/**
 * Temporal Event - Triggered at specific time
 */
export interface TemporalEvent {
  event_id: string;
  time: number;
  type: 'style_change' | 'modifier_apply' | 'branch' | 'custom';
  data: any;
}

/**
 * Temporal Variation Config
 */
export interface TemporalVariationConfig {
  start_schema: BaseSchema;
  end_schema: BaseSchema;
  duration: number;
  easing?: EasingFunction;
  fps?: number;
  intermediate_keyframes?: number; // Auto-generate N keyframes
}
