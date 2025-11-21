/**
 * Week 5: Style DNA Encoding - Temporal DNA Encoder
 *
 * Extracts 32-dimensional temporal features tracking learning and fatigue.
 * Updated periodically (not per-stroke).
 */

import { StyleDNAConfig, TEMPORAL_DNA_INDEX } from '../config';
import type { TemporalDNA, DNAEncoder, ArtistContext, DNASession, StrokeDNA } from '../types';
import { ulid } from '../../../utils/ulid';

/**
 * Session Statistics for temporal encoding
 */
export interface SessionStatistics {
  total_sessions: number;
  total_strokes: number;
  avg_stroke_length: number;
  preferred_velocity: number;
  preferred_pressure: number;
  tool_usage: Map<string, number>;
  color_usage: Map<string, number>;
  undo_count: number;
  error_count: number;
  break_count: number;
}

/**
 * Temporal DNA Encoder
 * Encodes learning, fatigue, and style evolution
 */
export class TemporalDNAEncoder implements DNAEncoder<TemporalDNA> {
  private readonly dimension = StyleDNAConfig.dimensions.temporal;

  /**
   * Encode from session data
   */
  async encode(
    session: DNASession,
    context: ArtistContext
  ): Promise<TemporalDNA> {
    const start_time = performance.now();
    const features = new Float32Array(this.dimension);

    // Calculate session statistics
    const stats = this.calculateSessionStatistics(session);

    // Extract learning metrics (indices 0-9)
    this.extractLearningMetrics(stats, context, features);

    // Extract fatigue indicators (indices 10-19)
    this.extractFatigueIndicators(stats, context, features);

    // Extract style evolution (indices 20-29)
    this.extractStyleEvolution(session, features);

    const encoding_time_ms = performance.now() - start_time;

    // Determine learning phase
    const learning_phase = this.determineLearningPhase(features);
    const skill_progression = this.calculateSkillProgression(stats);

    return {
      dna_id: ulid(),
      session_id: session.session_id,
      artist_id: context.artist_id,
      features,
      learning_phase,
      skill_progression,
      fatigue_level: features[TEMPORAL_DNA_INDEX.CURRENT_FATIGUE_LEVEL],
      focus_score: features[TEMPORAL_DNA_INDEX.FOCUS_SCORE],
      flow_state: features[TEMPORAL_DNA_INDEX.FLOW_STATE_DURATION] > 0.5,
      total_sessions: stats.total_sessions,
      total_strokes: stats.total_strokes,
      timestamp: Date.now(),
      encoding_time_ms
    };
  }

  /**
   * Sync encoding (delegates to async)
   */
  encodeSync(session: DNASession, context: ArtistContext): TemporalDNA {
    throw new Error('TemporalDNA encoding must be async (use encode() method)');
  }

  /**
   * Calculate session statistics
   */
  private calculateSessionStatistics(session: DNASession): SessionStatistics {
    const tool_usage = new Map<string, number>();
    const color_usage = new Map<string, number>();

    let total_velocity = 0;
    let total_pressure = 0;
    let total_length = 0;

    for (const stroke_dna of session.stroke_dnas) {
      // Tool usage
      const tool_count = tool_usage.get(stroke_dna.tool) || 0;
      tool_usage.set(stroke_dna.tool, tool_count + 1);

      // Color usage
      const color_count = color_usage.get(stroke_dna.color) || 0;
      color_usage.set(stroke_dna.color, color_count + 1);

      // Aggregate features
      total_velocity += stroke_dna.features[20]; // AVG_VELOCITY
      total_pressure += stroke_dna.features[24]; // PRESSURE_MEAN
      total_length += stroke_dna.features[6]; // PERIMETER
    }

    const stroke_count = session.stroke_dnas.length;

    return {
      total_sessions: 1, // Will be updated from context
      total_strokes: stroke_count,
      avg_stroke_length: stroke_count > 0 ? total_length / stroke_count : 0,
      preferred_velocity: stroke_count > 0 ? total_velocity / stroke_count : 0,
      preferred_pressure: stroke_count > 0 ? total_pressure / stroke_count : 0,
      tool_usage,
      color_usage,
      undo_count: 0, // Would track from UI events
      error_count: 0, // Would track from UI events
      break_count: 0 // Would track from context
    };
  }

  /**
   * Extract learning metrics (indices 0-9)
   */
  private extractLearningMetrics(
    stats: SessionStatistics,
    context: ArtistContext,
    features: Float32Array
  ): void {
    // SESSION_COUNT
    features[TEMPORAL_DNA_INDEX.SESSION_COUNT] = context.total_sessions;

    // TOTAL_STROKES
    features[TEMPORAL_DNA_INDEX.TOTAL_STROKES] = context.total_lifetime_strokes;

    // AVG_STROKE_LENGTH (normalized)
    features[TEMPORAL_DNA_INDEX.AVG_STROKE_LENGTH] =
      Math.min(stats.avg_stroke_length / 1000, 1);

    // PREFERRED_VELOCITY (normalized)
    features[TEMPORAL_DNA_INDEX.PREFERRED_VELOCITY] =
      Math.min(stats.preferred_velocity / 100, 1);

    // PREFERRED_PRESSURE
    features[TEMPORAL_DNA_INDEX.PREFERRED_PRESSURE] = stats.preferred_pressure;

    // TOOL_DIVERSITY (number of unique tools used)
    features[TEMPORAL_DNA_INDEX.TOOL_DIVERSITY] =
      Math.min(stats.tool_usage.size / 10, 1);

    // COLOR_PALETTE_SIZE (number of unique colors)
    features[TEMPORAL_DNA_INDEX.COLOR_PALETTE_SIZE] =
      Math.min(stats.color_usage.size / 20, 1);

    // COMPOSITION_BIAS (placeholder - would analyze spatial patterns)
    features[TEMPORAL_DNA_INDEX.COMPOSITION_BIAS] = 0.5;

    // REVISION_RATE (undo frequency)
    const revision_rate =
      stats.total_strokes > 0 ? stats.undo_count / stats.total_strokes : 0;
    features[TEMPORAL_DNA_INDEX.REVISION_RATE] = Math.min(revision_rate, 1);

    // COMPLETION_RATE (placeholder)
    features[TEMPORAL_DNA_INDEX.COMPLETION_RATE] = 0.8;
  }

  /**
   * Extract fatigue indicators (indices 10-19)
   */
  private extractFatigueIndicators(
    stats: SessionStatistics,
    context: ArtistContext,
    features: Float32Array
  ): void {
    // CURRENT_FATIGUE_LEVEL (from context)
    features[TEMPORAL_DNA_INDEX.CURRENT_FATIGUE_LEVEL] = context.current_fatigue_level;

    // STROKE_CONSISTENCY (variance in stroke properties)
    const consistency = this.calculateStrokeConsistency(stats);
    features[TEMPORAL_DNA_INDEX.STROKE_CONSISTENCY] = consistency;

    // ERROR_FREQUENCY
    const error_frequency =
      stats.total_strokes > 0 ? stats.error_count / stats.total_strokes : 0;
    features[TEMPORAL_DNA_INDEX.ERROR_FREQUENCY] = Math.min(error_frequency, 1);

    // UNDO_RATE
    const undo_rate =
      stats.total_strokes > 0 ? stats.undo_count / stats.total_strokes : 0;
    features[TEMPORAL_DNA_INDEX.UNDO_RATE] = Math.min(undo_rate, 1);

    // PAUSE_FREQUENCY (placeholder)
    features[TEMPORAL_DNA_INDEX.PAUSE_FREQUENCY] = 0.1;

    // VELOCITY_VARIANCE (placeholder - would calculate from strokes)
    features[TEMPORAL_DNA_INDEX.VELOCITY_VARIANCE] = 0.3;

    // PRESSURE_STABILITY (inverse of pressure variance)
    features[TEMPORAL_DNA_INDEX.PRESSURE_STABILITY] = 0.7;

    // SESSION_DURATION (normalized)
    const session_duration_hours = context.consecutive_work_minutes / 60;
    features[TEMPORAL_DNA_INDEX.SESSION_DURATION] =
      Math.min(session_duration_hours / 4, 1); // Normalize to 4 hours

    // BREAK_COUNT
    features[TEMPORAL_DNA_INDEX.BREAK_COUNT] =
      Math.min(stats.break_count / 10, 1);

    // FOCUS_SCORE (inverse of fatigue and errors)
    const focus_score =
      1 - context.current_fatigue_level * 0.7 - error_frequency * 0.3;
    features[TEMPORAL_DNA_INDEX.FOCUS_SCORE] = Math.max(0, Math.min(1, focus_score));
  }

  /**
   * Extract style evolution (indices 20-29)
   */
  private extractStyleEvolution(session: DNASession, features: Float32Array): void {
    // STYLE_DRIFT_RATE (placeholder - would compare to previous sessions)
    features[TEMPORAL_DNA_INDEX.STYLE_DRIFT_RATE] = 0.2;

    // EXPLORATION_SCORE (variety in tools/colors)
    const stroke_count = session.stroke_dnas.length;
    const unique_tools = new Set(session.stroke_dnas.map((s) => s.tool)).size;
    const unique_colors = new Set(session.stroke_dnas.map((s) => s.color)).size;
    const exploration = (unique_tools + unique_colors) / (stroke_count * 0.1);
    features[TEMPORAL_DNA_INDEX.EXPLORATION_SCORE] = Math.min(exploration, 1);

    // REFINEMENT_SCORE (consistency in approach)
    const refinement = 1 - exploration;
    features[TEMPORAL_DNA_INDEX.REFINEMENT_SCORE] = Math.max(0, refinement);

    // EXPERIMENTATION_RATE (new tools/colors per stroke)
    features[TEMPORAL_DNA_INDEX.EXPERIMENTATION_RATE] =
      Math.min(unique_tools / Math.max(stroke_count, 1), 1);

    // COMFORT_ZONE_RADIUS (variance in stroke features)
    features[TEMPORAL_DNA_INDEX.COMFORT_ZONE_RADIUS] = 0.5;

    // NOVELTY_SEEKING (based on exploration)
    features[TEMPORAL_DNA_INDEX.NOVELTY_SEEKING] = exploration;

    // PATTERN_REPETITION (inverse of exploration)
    features[TEMPORAL_DNA_INDEX.PATTERN_REPETITION] = 1 - exploration;

    // CREATIVE_BURST_COUNT (rapid changes in style - placeholder)
    features[TEMPORAL_DNA_INDEX.CREATIVE_BURST_COUNT] = 0;

    // DELIBERATE_PRACTICE_TIME (focused refinement - placeholder)
    features[TEMPORAL_DNA_INDEX.DELIBERATE_PRACTICE_TIME] = 0.6;

    // FLOW_STATE_DURATION (high focus + low fatigue)
    const flow_state =
      features[TEMPORAL_DNA_INDEX.FOCUS_SCORE] > 0.7 &&
      features[TEMPORAL_DNA_INDEX.CURRENT_FATIGUE_LEVEL] < 0.3
        ? 1
        : 0;
    features[TEMPORAL_DNA_INDEX.FLOW_STATE_DURATION] = flow_state;

    // Reserved indices (30-31) left at 0
    features[TEMPORAL_DNA_INDEX.RESERVED_1] = 0;
    features[TEMPORAL_DNA_INDEX.RESERVED_2] = 0;
  }

  /**
   * Calculate stroke consistency
   */
  private calculateStrokeConsistency(stats: SessionStatistics): number {
    // Simplified: High consistency = low variance in tool/color usage
    const tool_entropy = this.calculateEntropy(Array.from(stats.tool_usage.values()));
    const color_entropy = this.calculateEntropy(Array.from(stats.color_usage.values()));

    // High entropy = low consistency
    const max_entropy = Math.log2(10); // Assume max 10 tools/colors
    const consistency = 1 - (tool_entropy + color_entropy) / (2 * max_entropy);

    return Math.max(0, Math.min(1, consistency));
  }

  /**
   * Calculate entropy
   */
  private calculateEntropy(values: number[]): number {
    const total = values.reduce((a, b) => a + b, 0);
    if (total === 0) return 0;

    let entropy = 0;
    for (const value of values) {
      if (value > 0) {
        const p = value / total;
        entropy -= p * Math.log2(p);
      }
    }

    return entropy;
  }

  /**
   * Determine learning phase
   */
  private determineLearningPhase(
    features: Float32Array
  ): 'exploration' | 'refinement' | 'mastery' {
    const exploration_score = features[TEMPORAL_DNA_INDEX.EXPLORATION_SCORE];
    const refinement_score = features[TEMPORAL_DNA_INDEX.REFINEMENT_SCORE];
    const total_strokes = features[TEMPORAL_DNA_INDEX.TOTAL_STROKES];

    if (total_strokes < 1000) {
      return 'exploration';
    } else if (refinement_score > exploration_score) {
      return 'refinement';
    } else if (total_strokes > 5000 && refinement_score > 0.7) {
      return 'mastery';
    } else {
      return 'exploration';
    }
  }

  /**
   * Calculate skill progression
   */
  private calculateSkillProgression(stats: SessionStatistics): number {
    // Logarithmic progression based on total strokes
    const stroke_factor = Math.log10(stats.total_strokes + 1) / 5; // 0-1 at 100k strokes

    // Tool diversity factor
    const diversity_factor = Math.min(stats.tool_usage.size / 10, 1);

    // Combined progression
    return Math.min((stroke_factor + diversity_factor) / 2, 1);
  }

  getDimension(): number {
    return this.dimension;
  }

  getTier(): 'stroke' | 'image' | 'temporal' {
    return 'temporal';
  }
}

/**
 * Global encoder instance
 */
export const globalTemporalDNAEncoder = new TemporalDNAEncoder();
