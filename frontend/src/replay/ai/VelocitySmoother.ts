/**
 * VelocitySmoother - Savitzky-Golay filter for velocity smoothing
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 3: AI Integration
 *
 * Savitzky-Golay filtering:
 * - Smooths velocity data while preserving peaks and valleys
 * - Better than simple moving average for feature detection
 * - Commonly used in signal processing and scientific analysis
 *
 * Use cases:
 * - Remove input device noise (Apple Pencil jitter)
 * - Identify true acceleration/deceleration patterns
 * - Prepare data for AI training
 */

import { NormalizedPoint, NormalizedStroke } from '../core/ReplayNormalizer';

/**
 * Savitzky-Golay filter coefficients
 *
 * Precomputed for window size 5, polynomial order 2 (quadratic)
 */
const SG_COEFFICIENTS_5_2: number[] = [-3, 12, 17, 12, -3];
const SG_NORM_5_2 = 35;

/**
 * Savitzky-Golay filter coefficients (window size 7, order 2)
 */
const SG_COEFFICIENTS_7_2: number[] = [-2, 3, 6, 7, 6, 3, -2];
const SG_NORM_7_2 = 21;

/**
 * Smoothed velocity point
 */
export interface SmoothedPoint extends NormalizedPoint {
  /** Original raw velocity */
  rawVelocity: number;

  /** Smoothed velocity */
  smoothedVelocity: number;
}

/**
 * Smoothing parameters
 */
export interface SmoothingParams {
  /** Window size (5 or 7, default 5) */
  windowSize?: 5 | 7;

  /** Whether to preserve peak velocities (default true) */
  preservePeaks?: boolean;
}

/**
 * VelocitySmoother - Applies Savitzky-Golay filtering to velocity data
 */
export class VelocitySmoother {
  private params: Required<SmoothingParams>;

  constructor(params?: SmoothingParams) {
    this.params = {
      windowSize: params?.windowSize ?? 5,
      preservePeaks: params?.preservePeaks ?? true
    };
  }

  /**
   * Smooth velocity data for a stroke using Savitzky-Golay filter
   *
   * @param stroke Normalized stroke with velocity data
   * @returns Smoothed points
   */
  smoothStroke(stroke: NormalizedStroke): SmoothedPoint[] {
    const points = stroke.points;

    if (points.length < 3) {
      // Not enough points for smoothing
      return points.map(p => ({
        ...p,
        rawVelocity: p.velocity ?? 0,
        smoothedVelocity: p.velocity ?? 0
      }));
    }

    const velocities = points.map(p => p.velocity ?? 0);
    const smoothedVelocities = this.applySavitzkyGolay(velocities);

    // Preserve peaks if requested
    const finalVelocities = this.params.preservePeaks
      ? this.preservePeaks(velocities, smoothedVelocities)
      : smoothedVelocities;

    return points.map((p, i) => ({
      ...p,
      rawVelocity: velocities[i],
      smoothedVelocity: finalVelocities[i]
    }));
  }

  /**
   * Apply Savitzky-Golay filter to a 1D signal
   *
   * @param signal Input signal (velocity values)
   * @returns Smoothed signal
   */
  private applySavitzkyGolay(signal: number[]): number[] {
    const n = signal.length;
    const smoothed = new Array(n);

    const coeffs = this.params.windowSize === 5 ? SG_COEFFICIENTS_5_2 : SG_COEFFICIENTS_7_2;
    const norm = this.params.windowSize === 5 ? SG_NORM_5_2 : SG_NORM_7_2;
    const halfWindow = Math.floor(coeffs.length / 2);

    for (let i = 0; i < n; i++) {
      let sum = 0;

      for (let j = 0; j < coeffs.length; j++) {
        const index = i - halfWindow + j;

        // Handle boundaries by clamping indices
        const clampedIndex = Math.max(0, Math.min(n - 1, index));
        sum += coeffs[j] * signal[clampedIndex];
      }

      smoothed[i] = sum / norm;
    }

    return smoothed;
  }

  /**
   * Preserve peak velocities after smoothing
   *
   * If a peak was reduced by more than 10%, restore it
   *
   * @param original Original velocity signal
   * @param smoothed Smoothed velocity signal
   * @returns Final signal with peaks preserved
   */
  private preservePeaks(original: number[], smoothed: number[]): number[] {
    const final = [...smoothed];

    for (let i = 1; i < original.length - 1; i++) {
      const isPeak = original[i] > original[i - 1] && original[i] > original[i + 1];

      if (isPeak) {
        const reduction = (original[i] - smoothed[i]) / original[i];

        if (reduction > 0.1) {
          // Restore peak (blend 70% original, 30% smoothed)
          final[i] = 0.7 * original[i] + 0.3 * smoothed[i];
        }
      }
    }

    return final;
  }

  /**
   * Detect velocity peaks (local maxima)
   *
   * @param smoothedPoints Smoothed velocity points
   * @param threshold Minimum velocity to be considered a peak (default 100 px/ms)
   * @returns Indices of peak points
   */
  detectPeaks(smoothedPoints: SmoothedPoint[], threshold: number = 100): number[] {
    if (smoothedPoints.length < 3) {
      return [];
    }

    const peaks: number[] = [];

    for (let i = 1; i < smoothedPoints.length - 1; i++) {
      const prev = smoothedPoints[i - 1].smoothedVelocity;
      const current = smoothedPoints[i].smoothedVelocity;
      const next = smoothedPoints[i + 1].smoothedVelocity;

      if (current > prev && current > next && current >= threshold) {
        peaks.push(i);
      }
    }

    return peaks;
  }

  /**
   * Detect velocity valleys (local minima)
   *
   * @param smoothedPoints Smoothed velocity points
   * @param threshold Maximum velocity to be considered a valley (default 20 px/ms)
   * @returns Indices of valley points
   */
  detectValleys(smoothedPoints: SmoothedPoint[], threshold: number = 20): number[] {
    if (smoothedPoints.length < 3) {
      return [];
    }

    const valleys: number[] = [];

    for (let i = 1; i < smoothedPoints.length - 1; i++) {
      const prev = smoothedPoints[i - 1].smoothedVelocity;
      const current = smoothedPoints[i].smoothedVelocity;
      const next = smoothedPoints[i + 1].smoothedVelocity;

      if (current < prev && current < next && current <= threshold) {
        valleys.push(i);
      }
    }

    return valleys;
  }

  /**
   * Calculate velocity statistics
   *
   * @param smoothedPoints Smoothed velocity points
   * @returns Velocity statistics
   */
  calculateStats(smoothedPoints: SmoothedPoint[]): {
    meanRaw: number;
    meanSmoothed: number;
    maxRaw: number;
    maxSmoothed: number;
    noiseReduction: number;
  } {
    if (smoothedPoints.length === 0) {
      return {
        meanRaw: 0,
        meanSmoothed: 0,
        maxRaw: 0,
        maxSmoothed: 0,
        noiseReduction: 0
      };
    }

    const rawVelocities = smoothedPoints.map(p => p.rawVelocity);
    const smoothedVelocities = smoothedPoints.map(p => p.smoothedVelocity);

    const meanRaw = rawVelocities.reduce((a, b) => a + b, 0) / rawVelocities.length;
    const meanSmoothed = smoothedVelocities.reduce((a, b) => a + b, 0) / smoothedVelocities.length;

    const maxRaw = Math.max(...rawVelocities);
    const maxSmoothed = Math.max(...smoothedVelocities);

    // Noise reduction: variance reduction
    const varianceRaw = rawVelocities.reduce((acc, v) => acc + (v - meanRaw) ** 2, 0) / rawVelocities.length;
    const varianceSmoothed = smoothedVelocities.reduce((acc, v) => acc + (v - meanSmoothed) ** 2, 0) / smoothedVelocities.length;

    const noiseReduction = varianceRaw === 0 ? 0 : (1 - varianceSmoothed / varianceRaw) * 100;

    return {
      meanRaw,
      meanSmoothed,
      maxRaw,
      maxSmoothed,
      noiseReduction
    };
  }

  /**
   * Smooth multiple strokes
   *
   * @param strokes Array of normalized strokes
   * @returns Array of smoothed point arrays
   */
  smoothMultipleStrokes(strokes: NormalizedStroke[]): SmoothedPoint[][] {
    return strokes.map(stroke => this.smoothStroke(stroke));
  }

  /**
   * Detect acceleration/deceleration events
   *
   * @param smoothedPoints Smoothed velocity points
   * @param threshold Acceleration threshold (px/ms²)
   * @returns Indices and types of events
   */
  detectAccelerationEvents(smoothedPoints: SmoothedPoint[], threshold: number = 500): Array<{
    index: number;
    type: 'acceleration' | 'deceleration';
    magnitude: number;
  }> {
    if (smoothedPoints.length < 2) {
      return [];
    }

    const events: Array<{ index: number; type: 'acceleration' | 'deceleration'; magnitude: number }> = [];

    for (let i = 1; i < smoothedPoints.length; i++) {
      const dt = smoothedPoints[i].normalizedTime - smoothedPoints[i - 1].normalizedTime;

      if (dt === 0) continue;

      const dv = smoothedPoints[i].smoothedVelocity - smoothedPoints[i - 1].smoothedVelocity;
      const acceleration = dv / dt;

      if (Math.abs(acceleration) >= threshold) {
        events.push({
          index: i,
          type: acceleration > 0 ? 'acceleration' : 'deceleration',
          magnitude: Math.abs(acceleration)
        });
      }
    }

    return events;
  }

  /**
   * Calculate smoothness metric (lower = smoother)
   *
   * Based on sum of squared jerk (third derivative of position)
   *
   * @param smoothedPoints Smoothed velocity points
   * @returns Smoothness score
   */
  calculateSmoothness(smoothedPoints: SmoothedPoint[]): number {
    if (smoothedPoints.length < 3) {
      return 0;
    }

    let jerkSum = 0;

    for (let i = 2; i < smoothedPoints.length; i++) {
      const v0 = smoothedPoints[i - 2].smoothedVelocity;
      const v1 = smoothedPoints[i - 1].smoothedVelocity;
      const v2 = smoothedPoints[i].smoothedVelocity;

      // Approximate jerk (third derivative)
      const jerk = v2 - 2 * v1 + v0;
      jerkSum += jerk * jerk;
    }

    return jerkSum / smoothedPoints.length;
  }
}
