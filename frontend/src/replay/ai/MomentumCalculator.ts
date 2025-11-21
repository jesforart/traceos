/**
 * MomentumCalculator - Calculate stroke momentum for AI features
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 3: AI Integration
 *
 * IMPROVEMENTS APPLIED:
 * - FIX #6: Momentum entropy epsilon check (avoid log(0) errors)
 *
 * Momentum = pressure × velocity
 * - High momentum: Fast, hard strokes (gesture lines, bold shading)
 * - Low momentum: Slow, light strokes (detail work, feathering)
 * - Momentum entropy: Variability in drawing style
 */

import { NormalizedPoint, NormalizedStroke } from '../core/ReplayNormalizer';

/**
 * Momentum data for a single point
 */
export interface MomentumPoint extends NormalizedPoint {
  /** Momentum value (pressure × velocity) */
  momentum: number;
}

/**
 * Momentum statistics for a stroke
 */
export interface MomentumStats {
  /** Mean momentum across stroke */
  mean: number;

  /** Median momentum */
  median: number;

  /** Standard deviation of momentum */
  stdDev: number;

  /** Minimum momentum */
  min: number;

  /** Maximum momentum */
  max: number;

  /** Momentum range (max - min) */
  range: number;

  /** Momentum entropy (measure of variability) */
  entropy: number;

  /** Coefficient of variation (stdDev / mean) */
  coefficientOfVariation: number;
}

/**
 * MomentumCalculator - Computes momentum for strokes
 */
export class MomentumCalculator {
  /**
   * Calculate momentum for all points in a stroke
   *
   * @param stroke Normalized stroke with velocity data
   * @returns Stroke with momentum points
   */
  calculateStrokeMomentum(stroke: NormalizedStroke): MomentumPoint[] {
    const momentumPoints: MomentumPoint[] = [];

    for (const point of stroke.points) {
      const velocity = point.velocity ?? 0;
      const pressure = point.pressure;

      // Momentum = pressure × velocity
      const momentum = pressure * velocity;

      momentumPoints.push({
        ...point,
        momentum
      });
    }

    return momentumPoints;
  }

  /**
   * Calculate momentum statistics for a stroke
   *
   * FIX #6: Epsilon check in entropy calculation to avoid log(0)
   *
   * @param momentumPoints Points with momentum data
   * @returns Momentum statistics
   */
  calculateStats(momentumPoints: MomentumPoint[]): MomentumStats {
    if (momentumPoints.length === 0) {
      return {
        mean: 0,
        median: 0,
        stdDev: 0,
        min: 0,
        max: 0,
        range: 0,
        entropy: 0,
        coefficientOfVariation: 0
      };
    }

    const momentumValues = momentumPoints.map(p => p.momentum);

    // Mean
    const sum = momentumValues.reduce((acc, val) => acc + val, 0);
    const mean = sum / momentumValues.length;

    // Median
    const sortedValues = [...momentumValues].sort((a, b) => a - b);
    const median = sortedValues[Math.floor(sortedValues.length / 2)];

    // Standard deviation
    const variance = momentumValues.reduce((acc, val) => acc + (val - mean) ** 2, 0) / momentumValues.length;
    const stdDev = Math.sqrt(variance);

    // Min/Max/Range
    const min = Math.min(...momentumValues);
    const max = Math.max(...momentumValues);
    const range = max - min;

    // FIX #6: Entropy calculation with epsilon check
    const entropy = this.calculateEntropy(momentumValues);

    // Coefficient of variation
    const coefficientOfVariation = mean === 0 ? 0 : stdDev / mean;

    return {
      mean,
      median,
      stdDev,
      min,
      max,
      range,
      entropy,
      coefficientOfVariation
    };
  }

  /**
   * Calculate Shannon entropy of momentum distribution
   *
   * FIX #6: Epsilon check to avoid log(0) errors
   *
   * High entropy = variable momentum (diverse drawing style)
   * Low entropy = consistent momentum (uniform drawing style)
   *
   * @param values Momentum values
   * @returns Entropy (bits)
   */
  private calculateEntropy(values: number[]): number {
    if (values.length === 0) {
      return 0;
    }

    // Create histogram with 10 bins
    const numBins = 10;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min;

    if (range === 0) {
      return 0; // All values are the same
    }

    const bins = new Array(numBins).fill(0);

    for (const value of values) {
      const binIndex = Math.min(numBins - 1, Math.floor(((value - min) / range) * numBins));
      bins[binIndex]++;
    }

    // Calculate entropy
    let entropy = 0;
    const total = values.length;

    for (const count of bins) {
      if (count > 0) {
        const probability = count / total;

        // FIX #6: Epsilon check (avoid log(0))
        if (probability > 1e-10) {
          entropy -= probability * Math.log2(probability);
        }
      }
    }

    return entropy;
  }

  /**
   * Classify momentum level
   *
   * @param momentum Momentum value
   * @returns Classification (low/medium/high)
   */
  classifyMomentum(momentum: number): 'low' | 'medium' | 'high' {
    if (momentum < 50) {
      return 'low'; // Slow, light strokes (detail work)
    } else if (momentum < 200) {
      return 'medium'; // Normal drawing
    } else {
      return 'high'; // Fast, hard strokes (gestures)
    }
  }

  /**
   * Detect momentum transitions (changes in drawing intensity)
   *
   * @param momentumPoints Points with momentum data
   * @param threshold Momentum change threshold (default 100)
   * @returns Indices of transition points
   */
  detectTransitions(momentumPoints: MomentumPoint[], threshold: number = 100): number[] {
    if (momentumPoints.length < 2) {
      return [];
    }

    const transitions: number[] = [];

    for (let i = 1; i < momentumPoints.length; i++) {
      const prevMomentum = momentumPoints[i - 1].momentum;
      const currentMomentum = momentumPoints[i].momentum;

      const change = Math.abs(currentMomentum - prevMomentum);

      if (change > threshold) {
        transitions.push(i);
      }
    }

    return transitions;
  }

  /**
   * Calculate momentum for multiple strokes
   *
   * @param strokes Array of normalized strokes
   * @returns Array of momentum point arrays
   */
  calculateMultipleStrokes(strokes: NormalizedStroke[]): MomentumPoint[][] {
    return strokes.map(stroke => this.calculateStrokeMomentum(stroke));
  }

  /**
   * Calculate aggregate momentum statistics across multiple strokes
   *
   * @param strokes Array of normalized strokes
   * @returns Aggregate momentum statistics
   */
  calculateAggregateStats(strokes: NormalizedStroke[]): MomentumStats {
    const allMomentumPoints: MomentumPoint[] = [];

    for (const stroke of strokes) {
      const momentumPoints = this.calculateStrokeMomentum(stroke);
      allMomentumPoints.push(...momentumPoints);
    }

    return this.calculateStats(allMomentumPoints);
  }

  /**
   * Identify high-momentum segments (fast, hard drawing)
   *
   * @param momentumPoints Points with momentum data
   * @param percentileThreshold Percentile threshold (0-1, default 0.75 = top 25%)
   * @returns Indices of high-momentum points
   */
  identifyHighMomentumSegments(momentumPoints: MomentumPoint[], percentileThreshold: number = 0.75): number[] {
    if (momentumPoints.length === 0) {
      return [];
    }

    const momentumValues = momentumPoints.map(p => p.momentum);
    const sortedValues = [...momentumValues].sort((a, b) => a - b);
    const thresholdIndex = Math.floor(sortedValues.length * percentileThreshold);
    const threshold = sortedValues[thresholdIndex];

    const highMomentumIndices: number[] = [];

    for (let i = 0; i < momentumPoints.length; i++) {
      if (momentumPoints[i].momentum >= threshold) {
        highMomentumIndices.push(i);
      }
    }

    return highMomentumIndices;
  }

  /**
   * Calculate momentum gradient (rate of change)
   *
   * Useful for detecting sudden accelerations/decelerations
   *
   * @param momentumPoints Points with momentum data
   * @returns Momentum gradient for each point
   */
  calculateMomentumGradient(momentumPoints: MomentumPoint[]): number[] {
    if (momentumPoints.length < 2) {
      return [];
    }

    const gradients: number[] = [];

    for (let i = 1; i < momentumPoints.length; i++) {
      const dt = momentumPoints[i].normalizedTime - momentumPoints[i - 1].normalizedTime;
      const dm = momentumPoints[i].momentum - momentumPoints[i - 1].momentum;

      if (dt === 0) {
        gradients.push(0);
      } else {
        gradients.push(dm / dt);
      }
    }

    return gradients;
  }
}
