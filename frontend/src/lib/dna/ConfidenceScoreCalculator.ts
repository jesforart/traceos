/**
 * Week 5 v1.2: Confidence Score Calculator
 *
 * Calculates how representative a session is for style encoding.
 * Based on stroke count, session age, and completeness.
 */

import { StyleDNAConfig } from './config';
import type { ConfidenceScore, DNASession } from './types';
import { ulid } from '../../utils/ulid';

/**
 * Confidence Score Calculator
 * Determines session representativeness
 */
export class ConfidenceScoreCalculator {
  /**
   * Calculate confidence score for a session
   */
  calculate(session: DNASession): ConfidenceScore {
    const stroke_count_confidence = this.calculateStrokeCountConfidence(session.total_strokes);
    const session_age_confidence = this.calculateSessionAgeConfidence(session.started_at);
    const completeness_confidence = this.calculateCompletenessConfidence(session);

    // Weighted combination
    const overall_confidence =
      stroke_count_confidence * 0.5 +
      session_age_confidence * 0.3 +
      completeness_confidence * 0.2;

    const session_age_hours = (Date.now() - session.started_at) / (1000 * 60 * 60);

    return {
      confidence_id: ulid(),
      session_id: session.session_id,
      overall_confidence,
      stroke_count_confidence,
      session_age_confidence,
      completeness_confidence,
      total_strokes: session.total_strokes,
      session_age_hours,
      computed_at: Date.now()
    };
  }

  /**
   * Calculate confidence based on stroke count
   * More strokes = higher confidence
   */
  private calculateStrokeCountConfidence(stroke_count: number): number {
    const min_strokes = StyleDNAConfig.confidence.min_strokes_for_high_confidence;
    const max_strokes = StyleDNAConfig.confidence.max_strokes_for_full_confidence;

    if (stroke_count < min_strokes) {
      // Low confidence below minimum
      return stroke_count / min_strokes;
    } else if (stroke_count >= max_strokes) {
      // Full confidence at maximum
      return 1.0;
    } else {
      // Linear interpolation between min and max
      const range = max_strokes - min_strokes;
      const position = stroke_count - min_strokes;
      return position / range;
    }
  }

  /**
   * Calculate confidence based on session age
   * Newer sessions = higher confidence (decays over time)
   */
  private calculateSessionAgeConfidence(started_at: number): number {
    const age_hours = (Date.now() - started_at) / (1000 * 60 * 60);
    const decay_hours = StyleDNAConfig.confidence.session_age_decay_hours;

    // Exponential decay
    const decay_rate = 0.1; // Adjustable decay rate
    const confidence = Math.exp(-decay_rate * (age_hours / decay_hours));

    return Math.max(0, Math.min(1, confidence));
  }

  /**
   * Calculate confidence based on completeness
   * Has all DNA tiers = higher confidence
   */
  private calculateCompletenessConfidence(session: DNASession): number {
    let score = 0;
    const tier_weight = 1 / 3;

    // Check stroke DNA
    if (session.stroke_dnas && session.stroke_dnas.length > 0) {
      score += tier_weight;
    }

    // Check image DNA
    if (session.image_dnas && session.image_dnas.length > 0) {
      score += tier_weight;
    }

    // Check temporal DNA
    if (session.temporal_dnas && session.temporal_dnas.length > 0) {
      score += tier_weight;
    }

    return score;
  }

  /**
   * Get confidence category
   */
  getCategoryForScore(score: number): 'low' | 'medium' | 'high' {
    if (score < 0.4) return 'low';
    if (score < 0.7) return 'medium';
    return 'high';
  }

  /**
   * Get recommendation based on confidence
   */
  getRecommendation(confidence: ConfidenceScore): string {
    const category = this.getCategoryForScore(confidence.overall_confidence);

    switch (category) {
      case 'low':
        if (confidence.stroke_count_confidence < 0.5) {
          return 'Add more strokes to improve confidence. Current: ' + confidence.total_strokes;
        } else if (confidence.completeness_confidence < 0.5) {
          return 'Session is incomplete. Ensure all DNA tiers are encoded.';
        } else {
          return 'Session is too old. Consider creating a new session.';
        }
      case 'medium':
        return 'Session confidence is moderate. Additional strokes will improve accuracy.';
      case 'high':
        return 'Session is highly representative. Safe to use for style matching.';
    }
  }

  /**
   * Check if session meets minimum confidence threshold
   */
  meetsMinimumThreshold(confidence: ConfidenceScore, threshold: number = 0.5): boolean {
    return confidence.overall_confidence >= threshold;
  }

  /**
   * Calculate confidence for multiple sessions
   */
  calculateBatch(sessions: DNASession[]): ConfidenceScore[] {
    return sessions.map((session) => this.calculate(session));
  }

  /**
   * Get highest confidence session
   */
  selectHighestConfidence(sessions: DNASession[]): DNASession | null {
    if (sessions.length === 0) return null;

    const confidences = this.calculateBatch(sessions);
    const max_confidence = Math.max(...confidences.map((c) => c.overall_confidence));
    const max_index = confidences.findIndex((c) => c.overall_confidence === max_confidence);

    return sessions[max_index];
  }
}

/**
 * Global confidence score calculator instance
 */
export const confidenceScoreCalculator = new ConfidenceScoreCalculator();
