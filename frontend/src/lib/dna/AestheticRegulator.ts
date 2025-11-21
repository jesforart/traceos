/**
 * Week 5: Style DNA Encoding - Aesthetic Regulator
 *
 * Pretty Score calculation and aesthetic regulation.
 * Three modes: strict, balanced, creative.
 */

import { StyleDNAConfig } from './config';
import type { PrettyScore, DNASession, ImageDNA } from './types';
import { ulid } from '../../utils/ulid';

/**
 * Aesthetic Regulation Mode
 */
export type AestheticMode = 'strict' | 'balanced' | 'creative';

/**
 * Aesthetic Regulator
 * Calculates Pretty Score and enforces aesthetic standards
 */
export class AestheticRegulator {
  private mode: AestheticMode;

  constructor(mode: AestheticMode = 'balanced') {
    this.mode = mode;
  }

  /**
   * Calculate Pretty Score for a session
   */
  calculatePrettyScore(session: DNASession): PrettyScore {
    // Get latest image DNA
    const image_dna = session.image_dnas[session.image_dnas.length - 1];

    if (!image_dna) {
      // No image data, return default score
      return this.createDefaultScore(session);
    }

    // Calculate component scores
    const color_harmony = this.calculateColorHarmony(image_dna);
    const composition_balance = this.calculateCompositionBalance(session);
    const visual_complexity = this.calculateVisualComplexity(image_dna);
    const style_consistency = this.calculateStyleConsistency(session);

    // Overall score (weighted average)
    const overall_score =
      color_harmony * 0.3 +
      composition_balance * 0.3 +
      visual_complexity * 0.2 +
      style_consistency * 0.2;

    // Check threshold based on mode
    const threshold = this.getThresholdForMode();
    const passes_threshold = overall_score >= threshold;

    // Generate recommendation
    const recommendation = this.generateRecommendation(
      overall_score,
      { color_harmony, composition_balance, visual_complexity, style_consistency },
      passes_threshold
    );

    return {
      score_id: ulid(),
      session_id: session.session_id,
      overall_score,
      color_harmony,
      composition_balance,
      visual_complexity,
      style_consistency,
      mode: this.mode,
      passes_threshold,
      recommendation,
      timestamp: Date.now()
    };
  }

  /**
   * Calculate color harmony score
   */
  private calculateColorHarmony(image_dna: ImageDNA): number {
    const colors = image_dna.dominant_colors;

    if (colors.length === 0) return 0.5;

    // Analyze color relationships
    const harmony_scores: number[] = [];

    for (let i = 0; i < colors.length - 1; i++) {
      for (let j = i + 1; j < colors.length; j++) {
        const harmony = this.calculateColorPairHarmony(colors[i], colors[j]);
        harmony_scores.push(harmony);
      }
    }

    // Average harmony across all pairs
    const avg_harmony =
      harmony_scores.length > 0
        ? harmony_scores.reduce((a, b) => a + b, 0) / harmony_scores.length
        : 0.5;

    return avg_harmony;
  }

  /**
   * Calculate harmony between two colors
   */
  private calculateColorPairHarmony(color1: string, color2: string): number {
    const rgb1 = this.hexToRgb(color1);
    const rgb2 = this.hexToRgb(color2);

    if (!rgb1 || !rgb2) return 0.5;

    // Calculate hue difference
    const hue1 = this.rgbToHue(rgb1);
    const hue2 = this.rgbToHue(rgb2);
    const hue_diff = Math.abs(hue1 - hue2);

    // Harmonious relationships (complementary, analogous, triadic)
    const is_complementary = Math.abs(hue_diff - 180) < 30;
    const is_analogous = hue_diff < 60;
    const is_triadic = Math.abs(hue_diff - 120) < 30 || Math.abs(hue_diff - 240) < 30;

    if (is_complementary) return 0.9;
    if (is_triadic) return 0.85;
    if (is_analogous) return 0.8;

    // Calculate saturation and value compatibility
    const sat_diff = Math.abs(this.getSaturation(rgb1) - this.getSaturation(rgb2));
    const val_diff = Math.abs(this.getValue(rgb1) - this.getValue(rgb2));

    const compatibility = 1 - (sat_diff + val_diff) / 2;
    return compatibility * 0.7; // Lower score for non-standard relationships
  }

  /**
   * Calculate composition balance score
   */
  private calculateCompositionBalance(session: DNASession): number {
    const strokes = session.stroke_dnas;

    if (strokes.length === 0) return 0.5;

    // Analyze spatial distribution
    const centroids = strokes.map((s) => ({
      x: s.features[0], // MEAN_X
      y: s.features[1] // MEAN_Y
    }));

    // Calculate center of mass
    const center_x = centroids.reduce((sum, c) => sum + c.x, 0) / centroids.length;
    const center_y = centroids.reduce((sum, c) => sum + c.y, 0) / centroids.length;

    // Reference dimensions (normalized space)
    const ref_center_x = StyleDNAConfig.normalization.reference_width / 2;
    const ref_center_y = StyleDNAConfig.normalization.reference_height / 2;

    // Balance score: closer to center = higher balance
    const center_offset = Math.sqrt(
      Math.pow(center_x - ref_center_x, 2) + Math.pow(center_y - ref_center_y, 2)
    );
    const max_offset = Math.sqrt(ref_center_x ** 2 + ref_center_y ** 2);
    const balance = 1 - center_offset / max_offset;

    // Quadrant distribution (good balance = even distribution)
    const quadrants = [0, 0, 0, 0]; // TL, TR, BL, BR
    for (const c of centroids) {
      const is_left = c.x < ref_center_x;
      const is_top = c.y < ref_center_y;

      if (is_top && is_left) quadrants[0]++;
      else if (is_top && !is_left) quadrants[1]++;
      else if (!is_top && is_left) quadrants[2]++;
      else quadrants[3]++;
    }

    const total = quadrants.reduce((a, b) => a + b, 0);
    const distribution = quadrants.map((q) => q / total);
    const ideal_distribution = 0.25;
    const distribution_variance =
      distribution.reduce((sum, d) => sum + (d - ideal_distribution) ** 2, 0) / 4;
    const distribution_score = 1 - Math.min(distribution_variance * 4, 1);

    // Combined balance (60% center, 40% distribution)
    return balance * 0.6 + distribution_score * 0.4;
  }

  /**
   * Calculate visual complexity score
   */
  private calculateVisualComplexity(image_dna: ImageDNA): number {
    const texture = image_dna.texture_features;

    // Ideal complexity: not too simple, not too busy
    const ideal_complexity = 0.5;

    // Penalize extremes
    const complexity_penalty = Math.abs(texture.complexity - ideal_complexity);
    const complexity_score = 1 - complexity_penalty * 2;

    // Contrast and energy also affect complexity perception
    const contrast_score = texture.contrast; // Good contrast = good
    const energy_score = 1 - Math.abs(texture.energy - 0.5) * 2; // Moderate energy = good

    // Combined complexity score
    return complexity_score * 0.5 + contrast_score * 0.3 + energy_score * 0.2;
  }

  /**
   * Calculate style consistency score
   */
  private calculateStyleConsistency(session: DNASession): number {
    const strokes = session.stroke_dnas;

    if (strokes.length < 2) return 1.0; // Single stroke is perfectly consistent

    // Analyze stroke feature variance
    const feature_indices = [2, 3, 4, 20, 24]; // WIDTH, HEIGHT, ASPECT_RATIO, AVG_VELOCITY, PRESSURE_MEAN

    let consistency = 0;
    for (const idx of feature_indices) {
      const values = strokes.map((s) => s.features[idx]);
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const variance =
        values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length;
      const std_dev = Math.sqrt(variance);
      const coefficient_of_variation = mean !== 0 ? std_dev / Math.abs(mean) : 0;

      // Low CV = high consistency
      const feature_consistency = 1 - Math.min(coefficient_of_variation, 1);
      consistency += feature_consistency;
    }

    consistency /= feature_indices.length;

    // Tool and color consistency
    const unique_tools = new Set(strokes.map((s) => s.tool)).size;
    const unique_colors = new Set(strokes.map((s) => s.color)).size;

    const tool_consistency = 1 - Math.min(unique_tools / 10, 1);
    const color_consistency = 1 - Math.min(unique_colors / 20, 1);

    // Combined consistency (50% feature, 25% tool, 25% color)
    return consistency * 0.5 + tool_consistency * 0.25 + color_consistency * 0.25;
  }

  /**
   * Get threshold for current mode
   */
  private getThresholdForMode(): number {
    return StyleDNAConfig.aesthetic.modes[this.mode].min_score;
  }

  /**
   * Generate recommendation based on score
   */
  private generateRecommendation(
    overall_score: number,
    components: {
      color_harmony: number;
      composition_balance: number;
      visual_complexity: number;
      style_consistency: number;
    },
    passes: boolean
  ): string {
    if (passes) {
      if (overall_score >= 0.9) {
        return '✨ Excellent aesthetic quality! Your work shows strong harmony and balance.';
      } else if (overall_score >= 0.8) {
        return '👍 Good aesthetic quality. Minor refinements could elevate it further.';
      } else {
        return '✓ Meets aesthetic standards. Consider exploring variations.';
      }
    }

    // Failed threshold - provide specific guidance
    const entries = Object.entries(components);
    const weakest = entries.reduce<{key: string; value: number}>((min, [key, value]) =>
      value < min.value ? { key, value } : min
    , { key: entries[0][0], value: entries[0][1] });

    switch (weakest.key) {
      case 'color_harmony':
        return '🎨 Color harmony could be improved. Try complementary or analogous color schemes.';
      case 'composition_balance':
        return '⚖️  Composition balance needs attention. Consider distributing elements more evenly.';
      case 'visual_complexity':
        return '🔍 Visual complexity is off. Aim for moderate detail - not too simple, not too busy.';
      case 'style_consistency':
        return '🎯 Style consistency needs work. Try maintaining similar stroke characteristics.';
      default:
        return 'Consider refining your work to meet aesthetic standards.';
    }
  }

  /**
   * Create default score when no image data available
   */
  private createDefaultScore(session: DNASession): PrettyScore {
    return {
      score_id: ulid(),
      session_id: session.session_id,
      overall_score: 0.5,
      color_harmony: 0.5,
      composition_balance: 0.5,
      visual_complexity: 0.5,
      style_consistency: 0.5,
      mode: this.mode,
      passes_threshold: false,
      recommendation: 'Add strokes to generate aesthetic analysis.',
      timestamp: Date.now()
    };
  }

  /**
   * Set regulation mode
   */
  setMode(mode: AestheticMode): void {
    this.mode = mode;
  }

  /**
   * Get current mode
   */
  getMode(): AestheticMode {
    return this.mode;
  }

  /**
   * Check if score passes threshold
   */
  passesThreshold(score: number): boolean {
    const threshold = this.getThresholdForMode();
    return score >= threshold;
  }

  /**
   * Color utilities
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

  private rgbToHue(rgb: { r: number; g: number; b: number }): number {
    const r = rgb.r / 255;
    const g = rgb.g / 255;
    const b = rgb.b / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const delta = max - min;

    if (delta === 0) return 0;

    let hue = 0;
    if (max === r) {
      hue = ((g - b) / delta) % 6;
    } else if (max === g) {
      hue = (b - r) / delta + 2;
    } else {
      hue = (r - g) / delta + 4;
    }

    return (hue * 60 + 360) % 360;
  }

  private getSaturation(rgb: { r: number; g: number; b: number }): number {
    const r = rgb.r / 255;
    const g = rgb.g / 255;
    const b = rgb.b / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);

    return max === 0 ? 0 : (max - min) / max;
  }

  private getValue(rgb: { r: number; g: number; b: number }): number {
    return Math.max(rgb.r, rgb.g, rgb.b) / 255;
  }
}

/**
 * Global aesthetic regulator instance
 */
export const globalAestheticRegulator = new AestheticRegulator();
