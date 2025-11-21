/**
 * Week 3: Design Variation Engine - Style Distance Calculator
 *
 * Calculates semantic distance between design schemas.
 * Uses multiple metrics (color, typography, spacing, layout).
 */

import type { BaseSchema } from '../schema/types';
import type { StyleDistance } from './types';

/**
 * Style Distance Calculator
 */
export class StyleDistanceCalculator {
  /**
   * Calculate overall style distance between two schemas
   */
  calculate(schema_a: BaseSchema, schema_b: BaseSchema): StyleDistance {
    const color_distance = this.calculateColorDistance(schema_a, schema_b);
    const typography_distance = this.calculateTypographyDistance(schema_a, schema_b);
    const spacing_distance = this.calculateSpacingDistance(schema_a, schema_b);
    const layout_distance = this.calculateLayoutDistance(schema_a, schema_b);

    // Weighted average
    const overall_distance =
      color_distance * 0.3 +
      typography_distance * 0.25 +
      spacing_distance * 0.25 +
      layout_distance * 0.2;

    // Classify into distance band
    let band: 'micro' | 'minor' | 'moderate' | 'major' | 'extreme';
    if (overall_distance < 0.1) {
      band = 'micro';
    } else if (overall_distance < 0.25) {
      band = 'minor';
    } else if (overall_distance < 0.5) {
      band = 'moderate';
    } else if (overall_distance < 0.75) {
      band = 'major';
    } else {
      band = 'extreme';
    }

    return {
      overall_distance,
      color_distance,
      typography_distance,
      spacing_distance,
      layout_distance,
      band
    };
  }

  /**
   * Calculate color distance
   */
  private calculateColorDistance(schema_a: BaseSchema, schema_b: BaseSchema): number {
    let total_distance = 0;
    let count = 0;

    for (const node_a of schema_a.semantic_nodes) {
      const node_b = schema_b.semantic_nodes.find((n) => n.node_id === node_a.node_id);
      if (!node_b) continue;

      // Compare color properties
      const color_a = node_a.properties.color;
      const color_b = node_b.properties.color;
      if (color_a && color_b) {
        total_distance += this.colorDifference(color_a, color_b);
        count++;
      }

      const bg_a = node_a.properties.backgroundColor;
      const bg_b = node_b.properties.backgroundColor;
      if (bg_a && bg_b) {
        total_distance += this.colorDifference(bg_a, bg_b);
        count++;
      }
    }

    return count > 0 ? total_distance / count : 0;
  }

  /**
   * Calculate typography distance
   */
  private calculateTypographyDistance(schema_a: BaseSchema, schema_b: BaseSchema): number {
    let total_distance = 0;
    let count = 0;

    for (const node_a of schema_a.semantic_nodes) {
      const node_b = schema_b.semantic_nodes.find((n) => n.node_id === node_a.node_id);
      if (!node_b) continue;

      // Font size
      const size_a = node_a.properties.fontSize;
      const size_b = node_b.properties.fontSize;
      if (size_a && size_b) {
        total_distance += Math.abs(size_b - size_a) / Math.max(size_a, size_b);
        count++;
      }

      // Font weight
      const weight_a = node_a.properties.fontWeight;
      const weight_b = node_b.properties.fontWeight;
      if (weight_a && weight_b) {
        total_distance += Math.abs(weight_b - weight_a) / 900; // Max weight is 900
        count++;
      }

      // Font family (binary: same or different)
      const family_a = node_a.properties.fontFamily;
      const family_b = node_b.properties.fontFamily;
      if (family_a && family_b) {
        total_distance += family_a === family_b ? 0 : 1;
        count++;
      }
    }

    return count > 0 ? total_distance / count : 0;
  }

  /**
   * Calculate spacing distance
   */
  private calculateSpacingDistance(schema_a: BaseSchema, schema_b: BaseSchema): number {
    let total_distance = 0;
    let count = 0;

    for (const node_a of schema_a.semantic_nodes) {
      const node_b = schema_b.semantic_nodes.find((n) => n.node_id === node_a.node_id);
      if (!node_b) continue;

      // Padding
      const padding_a = node_a.properties.padding;
      const padding_b = node_b.properties.padding;
      if (padding_a !== undefined && padding_b !== undefined) {
        total_distance += Math.abs(padding_b - padding_a) / Math.max(padding_a, padding_b, 1);
        count++;
      }

      // Margin
      const margin_a = node_a.properties.margin;
      const margin_b = node_b.properties.margin;
      if (margin_a !== undefined && margin_b !== undefined) {
        total_distance += Math.abs(margin_b - margin_a) / Math.max(margin_a, margin_b, 1);
        count++;
      }
    }

    return count > 0 ? total_distance / count : 0;
  }

  /**
   * Calculate layout distance
   */
  private calculateLayoutDistance(schema_a: BaseSchema, schema_b: BaseSchema): number {
    let total_distance = 0;
    let count = 0;

    for (const node_a of schema_a.semantic_nodes) {
      const node_b = schema_b.semantic_nodes.find((n) => n.node_id === node_a.node_id);
      if (!node_b) continue;

      // Position
      const x_diff = Math.abs(node_b.bounds.x - node_a.bounds.x);
      const y_diff = Math.abs(node_b.bounds.y - node_a.bounds.y);
      const pos_distance = Math.sqrt(x_diff * x_diff + y_diff * y_diff) / 1000; // Normalize
      total_distance += Math.min(pos_distance, 1);
      count++;

      // Size
      const w_diff = Math.abs(node_b.bounds.width - node_a.bounds.width);
      const h_diff = Math.abs(node_b.bounds.height - node_a.bounds.height);
      const size_distance =
        (w_diff / Math.max(node_a.bounds.width, 1) + h_diff / Math.max(node_a.bounds.height, 1)) /
        2;
      total_distance += Math.min(size_distance, 1);
      count++;
    }

    return count > 0 ? total_distance / count : 0;
  }

  /**
   * Calculate color difference (Delta E)
   * Simplified version using RGB distance
   */
  private colorDifference(color1: string, color2: string): number {
    const rgb1 = this.hexToRgb(color1);
    const rgb2 = this.hexToRgb(color2);

    if (!rgb1 || !rgb2) return 0;

    const r_diff = rgb2.r - rgb1.r;
    const g_diff = rgb2.g - rgb1.g;
    const b_diff = rgb2.b - rgb1.b;

    // Euclidean distance in RGB space, normalized to 0-1
    const distance = Math.sqrt(r_diff * r_diff + g_diff * g_diff + b_diff * b_diff);
    return distance / 441.67; // Max RGB distance is ~441.67
  }

  /**
   * Convert hex color to RGB
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
}

// Singleton instance
export const styleDistanceCalculator = new StyleDistanceCalculator();
