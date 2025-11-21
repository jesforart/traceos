/**
 * Week 5: Style DNA Encoding - Adaptive Behavior Manager
 *
 * Responds to fatigue, learning state, and style drift.
 * Provides UI warnings and automatic adjustments.
 */

import type { TemporalDNA, ArtistContext, DNASession } from './types';
import { StyleDNAConfig } from './config';

/**
 * Adaptive Behavior - System response to user state
 */
export interface AdaptiveBehavior {
  behavior_id: string;
  type: 'warning' | 'suggestion' | 'adjustment' | 'intervention';
  trigger: string;
  message: string;
  action?: () => void;
  priority: 'low' | 'medium' | 'high' | 'critical';
  timestamp: number;
}

/**
 * Fatigue Level Classification
 */
export type FatigueLevel = 'fresh' | 'focused' | 'tired' | 'exhausted';

/**
 * Adaptive Behavior Manager
 * Monitors user state and provides intelligent responses
 */
export class AdaptiveBehaviorManager {
  private behaviors: AdaptiveBehavior[] = [];
  private last_warning_time: number = 0;
  private warning_cooldown_ms: number = 60000; // 1 minute between warnings

  /**
   * Analyze temporal DNA and generate adaptive behaviors
   */
  analyzeBehaviors(
    temporal_dna: TemporalDNA,
    context: ArtistContext,
    session: DNASession
  ): AdaptiveBehavior[] {
    const behaviors: AdaptiveBehavior[] = [];

    // Check fatigue
    const fatigue_behaviors = this.checkFatigue(temporal_dna, context);
    behaviors.push(...fatigue_behaviors);

    // Check focus
    const focus_behaviors = this.checkFocus(temporal_dna);
    behaviors.push(...focus_behaviors);

    // Check learning state
    const learning_behaviors = this.checkLearningState(temporal_dna);
    behaviors.push(...learning_behaviors);

    // Check style drift
    const drift_behaviors = this.checkStyleDrift(temporal_dna, session);
    behaviors.push(...drift_behaviors);

    // Store behaviors
    this.behaviors = behaviors;

    return behaviors;
  }

  /**
   * Check fatigue level and suggest breaks
   */
  private checkFatigue(
    temporal_dna: TemporalDNA,
    context: ArtistContext
  ): AdaptiveBehavior[] {
    const behaviors: AdaptiveBehavior[] = [];
    const fatigue_level = this.classifyFatigueLevel(temporal_dna.fatigue_level);

    // Critical fatigue - intervention
    if (fatigue_level === 'exhausted') {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'intervention',
        trigger: 'critical_fatigue',
        message:
          '🚨 High fatigue detected. Taking a 15-minute break is strongly recommended.',
        priority: 'critical',
        action: () => this.suggestBreak(15),
        timestamp: Date.now()
      });
    }
    // High fatigue - warning
    else if (fatigue_level === 'tired') {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'warning',
        trigger: 'high_fatigue',
        message:
          '⚠️  Fatigue increasing. Consider taking a short break to maintain quality.',
        priority: 'high',
        action: () => this.suggestBreak(5),
        timestamp: Date.now()
      });
    }

    // Long session warning
    const session_hours = context.consecutive_work_minutes / 60;
    if (session_hours > 2) {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'suggestion',
        trigger: 'long_session',
        message: `💡 You've been working for ${session_hours.toFixed(1)} hours. A break might help refresh your creativity.`,
        priority: 'medium',
        timestamp: Date.now()
      });
    }

    return behaviors;
  }

  /**
   * Check focus score and provide alerts
   */
  private checkFocus(temporal_dna: TemporalDNA): AdaptiveBehavior[] {
    const behaviors: AdaptiveBehavior[] = [];

    // Low focus
    if (temporal_dna.focus_score < 0.4) {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'warning',
        trigger: 'low_focus',
        message:
          '🎯 Focus level is low. Consider reducing distractions or taking a short break.',
        priority: 'medium',
        timestamp: Date.now()
      });
    }

    // Flow state achieved!
    if (temporal_dna.flow_state) {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'suggestion',
        trigger: 'flow_state',
        message:
          '✨ Flow state detected! You\'re in the zone - keep this momentum going.',
        priority: 'low',
        timestamp: Date.now()
      });
    }

    return behaviors;
  }

  /**
   * Check learning state and provide guidance
   */
  private checkLearningState(temporal_dna: TemporalDNA): AdaptiveBehavior[] {
    const behaviors: AdaptiveBehavior[] = [];

    switch (temporal_dna.learning_phase) {
      case 'exploration':
        behaviors.push({
          behavior_id: this.generateId(),
          type: 'suggestion',
          trigger: 'exploration_phase',
          message:
            '🔍 Exploration phase: Try experimenting with different tools and techniques.',
          priority: 'low',
          timestamp: Date.now()
        });
        break;

      case 'refinement':
        behaviors.push({
          behavior_id: this.generateId(),
          type: 'suggestion',
          trigger: 'refinement_phase',
          message:
            '🎨 Refinement phase: Focus on consistency and polishing your technique.',
          priority: 'low',
          timestamp: Date.now()
        });
        break;

      case 'mastery':
        behaviors.push({
          behavior_id: this.generateId(),
          type: 'suggestion',
          trigger: 'mastery_phase',
          message:
            '🏆 Mastery phase: Your skills are advanced. Consider tackling complex challenges.',
          priority: 'low',
          timestamp: Date.now()
        });
        break;
    }

    // Skill progression milestone
    if (temporal_dna.skill_progression > 0.8) {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'suggestion',
        trigger: 'high_skill',
        message:
          '🌟 Your skill level is high! Consider exploring advanced techniques or sharing your work.',
        priority: 'low',
        timestamp: Date.now()
      });
    }

    return behaviors;
  }

  /**
   * Check style drift and warn if deviating
   */
  private checkStyleDrift(
    temporal_dna: TemporalDNA,
    session: DNASession
  ): AdaptiveBehavior[] {
    const behaviors: AdaptiveBehavior[] = [];

    // High style drift (features[20])
    const drift_rate = temporal_dna.features[20]; // STYLE_DRIFT_RATE

    if (drift_rate > 0.5) {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'warning',
        trigger: 'high_style_drift',
        message:
          '⚡ Style drift detected. Your current strokes differ significantly from your session style.',
        priority: 'medium',
        timestamp: Date.now()
      });
    }

    // High experimentation rate
    const experimentation = temporal_dna.features[23]; // EXPERIMENTATION_RATE
    if (experimentation > 0.7) {
      behaviors.push({
        behavior_id: this.generateId(),
        type: 'suggestion',
        trigger: 'high_experimentation',
        message:
          '🧪 High experimentation detected. Great for exploration, but may affect consistency.',
        priority: 'low',
        timestamp: Date.now()
      });
    }

    return behaviors;
  }

  /**
   * Classify fatigue level
   */
  private classifyFatigueLevel(fatigue_score: number): FatigueLevel {
    if (fatigue_score < 0.25) return 'fresh';
    if (fatigue_score < 0.5) return 'focused';
    if (fatigue_score < 0.75) return 'tired';
    return 'exhausted';
  }

  /**
   * Suggest break duration
   */
  private suggestBreak(minutes: number): void {
    console.log(`💤 Break suggested: ${minutes} minutes`);
    // In production, would trigger UI modal or notification
  }

  /**
   * Get priority behaviors (high + critical only)
   */
  getPriorityBehaviors(): AdaptiveBehavior[] {
    return this.behaviors.filter(
      (b) => b.priority === 'high' || b.priority === 'critical'
    );
  }

  /**
   * Get behaviors by type
   */
  getBehaviorsByType(
    type: 'warning' | 'suggestion' | 'adjustment' | 'intervention'
  ): AdaptiveBehavior[] {
    return this.behaviors.filter((b) => b.type === type);
  }

  /**
   * Should show warning (respects cooldown)
   */
  shouldShowWarning(): boolean {
    const now = Date.now();
    if (now - this.last_warning_time > this.warning_cooldown_ms) {
      this.last_warning_time = now;
      return true;
    }
    return false;
  }

  /**
   * Clear behaviors
   */
  clearBehaviors(): void {
    this.behaviors = [];
  }

  /**
   * Get behavior summary
   */
  getSummary(): string {
    const by_type = {
      warning: this.behaviors.filter((b) => b.type === 'warning').length,
      suggestion: this.behaviors.filter((b) => b.type === 'suggestion').length,
      adjustment: this.behaviors.filter((b) => b.type === 'adjustment').length,
      intervention: this.behaviors.filter((b) => b.type === 'intervention').length
    };

    return `
Adaptive Behaviors:
- Warnings: ${by_type.warning}
- Suggestions: ${by_type.suggestion}
- Adjustments: ${by_type.adjustment}
- Interventions: ${by_type.intervention}
    `.trim();
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `behavior_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

/**
 * Automatic Brush Adjuster
 * Modifies brush parameters based on fatigue and focus
 */
export class BrushAdjuster {
  /**
   * Adjust brush size based on fatigue
   * Higher fatigue = larger brush (easier to control)
   */
  adjustBrushSize(base_size: number, fatigue_level: number): number {
    const fatigue_multiplier = 1 + fatigue_level * 0.3; // Up to 30% increase
    return Math.round(base_size * fatigue_multiplier);
  }

  /**
   * Adjust opacity based on focus
   * Lower focus = lower opacity (gentler, more forgiving)
   */
  adjustOpacity(base_opacity: number, focus_score: number): number {
    const focus_multiplier = 0.7 + focus_score * 0.3; // 0.7-1.0 range
    return Math.max(0, Math.min(1, base_opacity * focus_multiplier));
  }

  /**
   * Adjust smoothing based on fatigue
   * Higher fatigue = more smoothing (compensates for shaky hands)
   */
  adjustSmoothing(base_smoothing: number, fatigue_level: number): number {
    const fatigue_multiplier = 1 + fatigue_level * 0.5; // Up to 50% increase
    return Math.max(0, Math.min(1, base_smoothing * fatigue_multiplier));
  }

  /**
   * Get recommended brush settings
   */
  getRecommendedSettings(
    temporal_dna: TemporalDNA,
    current_settings: {
      size: number;
      opacity: number;
      smoothing: number;
    }
  ): {
    size: number;
    opacity: number;
    smoothing: number;
    adjusted: boolean;
  } {
    const fatigue = temporal_dna.fatigue_level;
    const focus = temporal_dna.focus_score;

    // Only adjust if fatigue is significant
    if (fatigue < 0.3 && focus > 0.7) {
      return { ...current_settings, adjusted: false };
    }

    const adjusted_size = this.adjustBrushSize(current_settings.size, fatigue);
    const adjusted_opacity = this.adjustOpacity(current_settings.opacity, focus);
    const adjusted_smoothing = this.adjustSmoothing(current_settings.smoothing, fatigue);

    return {
      size: adjusted_size,
      opacity: adjusted_opacity,
      smoothing: adjusted_smoothing,
      adjusted: true
    };
  }
}

/**
 * Global instances
 */
export const globalAdaptiveBehaviorManager = new AdaptiveBehaviorManager();
export const globalBrushAdjuster = new BrushAdjuster();
