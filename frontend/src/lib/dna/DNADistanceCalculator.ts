/**
 * Week 5: Style DNA Encoding - Distance Calculator
 *
 * Multi-space distance calculations across DNA tiers.
 * Supports Euclidean, cosine, and Manhattan metrics.
 */

import { StyleDNAConfig } from './config';
import type {
  StrokeDNA,
  ImageDNA,
  TemporalDNA,
  CompositeDNA,
  DNADistanceCalculator as IDNADistanceCalculator
} from './types';

/**
 * Distance Metric
 */
export type DistanceMetric = 'euclidean' | 'cosine' | 'manhattan';

/**
 * Multi-tier Distance Result
 */
export interface MultiTierDistance {
  overall_distance: number;
  stroke_distance: number;
  image_distance: number;
  temporal_distance: number;
  weights: {
    stroke: number;
    image: number;
    temporal: number;
    aesthetic: number;
  };
}

/**
 * DNA Distance Calculator
 * Calculates distances in multi-dimensional DNA spaces
 */
export class DNADistanceCalculator implements IDNADistanceCalculator {
  private metric: DistanceMetric;

  constructor(metric: DistanceMetric = 'cosine') {
    this.metric = metric;
  }

  /**
   * Calculate distance between two feature vectors
   */
  calculateDistance(dna_a: Float32Array, dna_b: Float32Array): number {
    if (dna_a.length !== dna_b.length) {
      throw new Error('DNA vectors must have same dimension');
    }

    switch (this.metric) {
      case 'euclidean':
        return this.euclideanDistance(dna_a, dna_b);
      case 'cosine':
        return this.cosineDistance(dna_a, dna_b);
      case 'manhattan':
        return this.manhattanDistance(dna_a, dna_b);
    }
  }

  /**
   * Calculate batch distances
   */
  calculateBatchDistances(query: Float32Array, targets: Float32Array[]): number[] {
    return targets.map((target) => this.calculateDistance(query, target));
  }

  /**
   * Calculate multi-tier distance between composite DNAs
   */
  calculateMultiTierDistance(
    composite_a: CompositeDNA,
    composite_b: CompositeDNA
  ): MultiTierDistance {
    const weights = StyleDNAConfig.distance_weights;

    // Stroke distance (average across all strokes)
    const stroke_distance = this.calculateStrokeDistance(
      composite_a.stroke_dna,
      composite_b.stroke_dna
    );

    // Image distance
    const image_distance =
      composite_a.image_dna && composite_b.image_dna
        ? this.calculateDistance(
            composite_a.image_dna.features,
            composite_b.image_dna.features
          )
        : 1.0; // Max distance if missing

    // Temporal distance
    const temporal_distance = this.calculateDistance(
      composite_a.temporal_dna.features,
      composite_b.temporal_dna.features
    );

    // Weighted combination
    const overall_distance =
      stroke_distance * weights.stroke +
      image_distance * weights.image +
      temporal_distance * weights.temporal;

    return {
      overall_distance,
      stroke_distance,
      image_distance,
      temporal_distance,
      weights
    };
  }

  /**
   * Calculate average stroke distance
   */
  private calculateStrokeDistance(
    strokes_a: StrokeDNA[],
    strokes_b: StrokeDNA[]
  ): number {
    if (strokes_a.length === 0 || strokes_b.length === 0) {
      return 1.0; // Max distance
    }

    // Use DTW (Dynamic Time Warping) for sequence alignment
    // Simplified: Compare corresponding indices
    const max_comparisons = Math.min(strokes_a.length, strokes_b.length);
    let total_distance = 0;

    for (let i = 0; i < max_comparisons; i++) {
      const distance = this.calculateDistance(
        strokes_a[i].features,
        strokes_b[i].features
      );
      total_distance += distance;
    }

    // Average distance
    return total_distance / max_comparisons;
  }

  /**
   * Find nearest neighbor
   */
  findNearestNeighbor(
    query: Float32Array,
    candidates: Float32Array[]
  ): { index: number; distance: number } {
    let min_distance = Infinity;
    let min_index = -1;

    for (let i = 0; i < candidates.length; i++) {
      const distance = this.calculateDistance(query, candidates[i]);
      if (distance < min_distance) {
        min_distance = distance;
        min_index = i;
      }
    }

    return { index: min_index, distance: min_distance };
  }

  /**
   * Find k nearest neighbors
   */
  findKNearestNeighbors(
    query: Float32Array,
    candidates: Float32Array[],
    k: number
  ): Array<{ index: number; distance: number }> {
    const distances = candidates.map((candidate, index) => ({
      index,
      distance: this.calculateDistance(query, candidate)
    }));

    // Sort by distance and take top k
    distances.sort((a, b) => a.distance - b.distance);
    return distances.slice(0, k);
  }

  /**
   * Euclidean distance
   */
  private euclideanDistance(a: Float32Array, b: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < a.length; i++) {
      const diff = a[i] - b[i];
      sum += diff * diff;
    }
    return Math.sqrt(sum);
  }

  /**
   * Cosine distance (1 - cosine similarity)
   */
  private cosineDistance(a: Float32Array, b: Float32Array): number {
    let dot = 0;
    let mag_a = 0;
    let mag_b = 0;

    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
      mag_a += a[i] * a[i];
      mag_b += b[i] * b[i];
    }

    const magnitude = Math.sqrt(mag_a) * Math.sqrt(mag_b);
    if (magnitude === 0) return 1.0; // Max distance

    const similarity = dot / magnitude;
    return 1 - similarity; // Convert to distance
  }

  /**
   * Manhattan distance (L1 norm)
   */
  private manhattanDistance(a: Float32Array, b: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < a.length; i++) {
      sum += Math.abs(a[i] - b[i]);
    }
    return sum;
  }

  /**
   * Set distance metric
   */
  setMetric(metric: DistanceMetric): void {
    this.metric = metric;
  }

  /**
   * Get current metric
   */
  getMetric(): DistanceMetric {
    return this.metric;
  }
}

/**
 * Global distance calculator instance
 */
export const globalDNADistanceCalculator = new DNADistanceCalculator();
