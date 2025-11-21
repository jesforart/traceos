/**
 * Week 5 v1.2: Bounds Normalization
 *
 * Scale-invariant stroke comparison.
 * Normalizes stroke bounds to reference dimensions for fair distance calculations.
 */

import { StyleDNAConfig } from './config';
import type { NormalizedBounds } from './types';

/**
 * Bounds Normalizer - Scale-invariant stroke encoding
 */
export class BoundsNormalizer {
  private readonly reference_width: number;
  private readonly reference_height: number;

  constructor(
    reference_width: number = StyleDNAConfig.normalization.reference_width,
    reference_height: number = StyleDNAConfig.normalization.reference_height
  ) {
    this.reference_width = reference_width;
    this.reference_height = reference_height;
  }

  /**
   * Normalize bounds to reference dimensions
   */
  normalize(
    bounds: { x: number; y: number; width: number; height: number },
    canvas_width: number,
    canvas_height: number
  ): NormalizedBounds {
    // Calculate scale factor
    const scale_x = this.reference_width / canvas_width;
    const scale_y = this.reference_height / canvas_height;
    const scale_factor = Math.min(scale_x, scale_y); // Uniform scaling

    // Apply scale
    const normalized = {
      x: bounds.x * scale_factor,
      y: bounds.y * scale_factor,
      width: bounds.width * scale_factor,
      height: bounds.height * scale_factor
    };

    return {
      original: { ...bounds },
      normalized,
      scale_factor,
      reference_dimensions: {
        width: this.reference_width,
        height: this.reference_height
      }
    };
  }

  /**
   * Denormalize bounds back to original canvas dimensions
   */
  denormalize(
    normalized_bounds: { x: number; y: number; width: number; height: number },
    canvas_width: number,
    canvas_height: number
  ): { x: number; y: number; width: number; height: number } {
    const scale_x = canvas_width / this.reference_width;
    const scale_y = canvas_height / this.reference_height;
    const scale_factor = Math.min(scale_x, scale_y);

    return {
      x: normalized_bounds.x * scale_factor,
      y: normalized_bounds.y * scale_factor,
      width: normalized_bounds.width * scale_factor,
      height: normalized_bounds.height * scale_factor
    };
  }

  /**
   * Normalize a point coordinate
   */
  normalizePoint(
    point: { x: number; y: number },
    canvas_width: number,
    canvas_height: number
  ): { x: number; y: number } {
    const scale_x = this.reference_width / canvas_width;
    const scale_y = this.reference_height / canvas_height;
    const scale_factor = Math.min(scale_x, scale_y);

    return {
      x: point.x * scale_factor,
      y: point.y * scale_factor
    };
  }

  /**
   * Normalize an array of points
   */
  normalizePoints(
    points: Array<{ x: number; y: number }>,
    canvas_width: number,
    canvas_height: number
  ): Array<{ x: number; y: number }> {
    return points.map((p) => this.normalizePoint(p, canvas_width, canvas_height));
  }

  /**
   * Calculate bounding box from points
   */
  calculateBounds(points: Array<{ x: number; y: number }>): {
    x: number;
    y: number;
    width: number;
    height: number;
  } {
    if (points.length === 0) {
      return { x: 0, y: 0, width: 0, height: 0 };
    }

    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);

    const min_x = Math.min(...xs);
    const max_x = Math.max(...xs);
    const min_y = Math.min(...ys);
    const max_y = Math.max(...ys);

    return {
      x: min_x,
      y: min_y,
      width: max_x - min_x,
      height: max_y - min_y
    };
  }

  /**
   * Normalize stroke points and calculate normalized bounds
   */
  normalizeStroke(
    points: Array<{ x: number; y: number }>,
    canvas_width: number,
    canvas_height: number
  ): {
    normalized_points: Array<{ x: number; y: number }>;
    normalized_bounds: NormalizedBounds;
  } {
    const original_bounds = this.calculateBounds(points);
    const normalized_points = this.normalizePoints(points, canvas_width, canvas_height);
    const normalized_bounds = this.normalize(original_bounds, canvas_width, canvas_height);

    return {
      normalized_points,
      normalized_bounds
    };
  }

  /**
   * Get reference dimensions
   */
  getReferenceDimensions(): { width: number; height: number } {
    return {
      width: this.reference_width,
      height: this.reference_height
    };
  }
}

/**
 * Global bounds normalizer instance
 */
export const globalBoundsNormalizer = new BoundsNormalizer();
