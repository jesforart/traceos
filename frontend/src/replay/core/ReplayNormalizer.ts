/**
 * ReplayNormalizer - Time domain normalization (0-1)
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 1: Core + Compression
 *
 * IMPROVEMENTS APPLIED:
 * - FIX #4: Binary search in sampleAt() for O(log n) performance
 *
 * Normalizes stroke timestamps to 0-1 range for:
 * - Uniform compression (independent of recording duration)
 * - Precise temporal queries via binary search
 * - GPU shader compatibility (normalized time inputs)
 */

import { Stroke, Point } from '../../types';

/**
 * NormalizedPoint - Point with time in [0, 1] range
 */
export interface NormalizedPoint extends Omit<Point, 'timestamp'> {
  /** Normalized time in [0, 1] range (0 = stroke start, 1 = stroke end) */
  normalizedTime: number;

  /** Original timestamp (milliseconds since epoch) */
  originalTimestamp: number;
}

/**
 * NormalizedStroke - Stroke with normalized time domain
 */
export interface NormalizedStroke extends Omit<Stroke, 'points'> {
  /** Normalized points (time in [0, 1]) */
  points: NormalizedPoint[];

  /** Original start time (milliseconds since epoch) */
  originalStartTime: number;

  /** Original end time (milliseconds since epoch) */
  originalEndTime: number;

  /** Original duration in milliseconds */
  durationMs: number;
}

/**
 * ReplayNormalizer - Converts strokes to/from normalized time domain
 */
export class ReplayNormalizer {
  /**
   * Normalize a stroke to [0, 1] time domain
   *
   * @param stroke Original stroke with absolute timestamps
   * @returns Normalized stroke with time in [0, 1]
   */
  normalize(stroke: Stroke): NormalizedStroke {
    if (stroke.points.length === 0) {
      throw new Error('[ReplayNormalizer] Cannot normalize empty stroke');
    }

    const startTime = stroke.points[0].timestamp;
    const endTime = stroke.points[stroke.points.length - 1].timestamp;
    const durationMs = endTime - startTime;

    // Edge case: single point or zero duration
    if (durationMs === 0) {
      return {
        ...stroke,
        points: stroke.points.map(point => ({
          ...point,
          normalizedTime: 0,
          originalTimestamp: point.timestamp
        })),
        originalStartTime: startTime,
        originalEndTime: endTime,
        durationMs: 0
      };
    }

    // Normalize each point
    const normalizedPoints: NormalizedPoint[] = stroke.points.map(point => ({
      x: point.x,
      y: point.y,
      pressure: point.pressure,
      tilt_x: point.tilt_x,
      tilt_y: point.tilt_y,
      velocity: point.velocity,
      normalizedTime: (point.timestamp - startTime) / durationMs,
      originalTimestamp: point.timestamp
    }));

    return {
      id: stroke.id,
      tool: stroke.tool,
      color: stroke.color,
      width: stroke.width,
      created_at: stroke.created_at,
      layer_id: stroke.layer_id,
      semantic_label: stroke.semantic_label,
      points: normalizedPoints,
      originalStartTime: startTime,
      originalEndTime: endTime,
      durationMs
    };
  }

  /**
   * Denormalize a stroke back to absolute time domain
   *
   * @param normalizedStroke Stroke with normalized time [0, 1]
   * @returns Original stroke with absolute timestamps
   */
  denormalize(normalizedStroke: NormalizedStroke): Stroke {
    const points: Point[] = normalizedStroke.points.map(point => ({
      x: point.x,
      y: point.y,
      pressure: point.pressure,
      tilt_x: point.tilt_x,
      tilt_y: point.tilt_y,
      velocity: point.velocity,
      timestamp: point.originalTimestamp
    }));

    return {
      id: normalizedStroke.id,
      tool: normalizedStroke.tool,
      color: normalizedStroke.color,
      width: normalizedStroke.width,
      created_at: normalizedStroke.created_at,
      layer_id: normalizedStroke.layer_id,
      semantic_label: normalizedStroke.semantic_label,
      points
    };
  }

  /**
   * Sample a normalized stroke at a specific normalized time
   *
   * FIX #4: Binary search for O(log n) performance
   *
   * @param normalizedStroke Stroke to sample
   * @param normalizedTime Time in [0, 1] to sample at
   * @returns Interpolated point at the specified time, or null if out of range
   */
  sampleAt(normalizedStroke: NormalizedStroke, normalizedTime: number): NormalizedPoint | null {
    if (normalizedStroke.points.length === 0) {
      return null;
    }

    // Clamp to [0, 1]
    normalizedTime = Math.max(0, Math.min(1, normalizedTime));

    const points = normalizedStroke.points;

    // Edge cases
    if (normalizedTime <= 0) {
      return points[0];
    }

    if (normalizedTime >= 1) {
      return points[points.length - 1];
    }

    // FIX #4: Binary search to find surrounding points
    let left = 0;
    let right = points.length - 1;

    while (left < right - 1) {
      const mid = Math.floor((left + right) / 2);

      if (points[mid].normalizedTime === normalizedTime) {
        return points[mid];
      } else if (points[mid].normalizedTime < normalizedTime) {
        left = mid;
      } else {
        right = mid;
      }
    }

    // Interpolate between points[left] and points[right]
    const p0 = points[left];
    const p1 = points[right];

    const t0 = p0.normalizedTime;
    const t1 = p1.normalizedTime;

    // Avoid division by zero
    if (t1 - t0 === 0) {
      return p0;
    }

    // Linear interpolation parameter
    const alpha = (normalizedTime - t0) / (t1 - t0);

    return {
      x: p0.x + alpha * (p1.x - p0.x),
      y: p0.y + alpha * (p1.y - p0.y),
      pressure: p0.pressure + alpha * (p1.pressure - p0.pressure),
      tilt_x: p0.tilt_x + alpha * (p1.tilt_x - p0.tilt_x),
      tilt_y: p0.tilt_y + alpha * (p1.tilt_y - p0.tilt_y),
      velocity: p0.velocity && p1.velocity ? p0.velocity + alpha * (p1.velocity - p0.velocity) : undefined,
      normalizedTime,
      originalTimestamp: p0.originalTimestamp + alpha * (p1.originalTimestamp - p0.originalTimestamp)
    };
  }

  /**
   * Normalize multiple strokes to [0, 1] time domain
   *
   * @param strokes Array of strokes to normalize
   * @returns Array of normalized strokes
   */
  normalizeAll(strokes: Stroke[]): NormalizedStroke[] {
    return strokes.map(stroke => this.normalize(stroke));
  }

  /**
   * Denormalize multiple strokes back to absolute time domain
   *
   * @param normalizedStrokes Array of normalized strokes
   * @returns Array of original strokes
   */
  denormalizeAll(normalizedStrokes: NormalizedStroke[]): Stroke[] {
    return normalizedStrokes.map(stroke => this.denormalize(stroke));
  }

  /**
   * Get the duration of a normalized stroke in milliseconds
   *
   * @param normalizedStroke Normalized stroke
   * @returns Duration in milliseconds
   */
  getDuration(normalizedStroke: NormalizedStroke): number {
    return normalizedStroke.durationMs;
  }

  /**
   * Convert normalized time to absolute timestamp
   *
   * @param normalizedStroke Normalized stroke
   * @param normalizedTime Time in [0, 1]
   * @returns Absolute timestamp in milliseconds
   */
  toAbsoluteTime(normalizedStroke: NormalizedStroke, normalizedTime: number): number {
    return normalizedStroke.originalStartTime + normalizedTime * normalizedStroke.durationMs;
  }

  /**
   * Convert absolute timestamp to normalized time
   *
   * @param normalizedStroke Normalized stroke
   * @param timestamp Absolute timestamp in milliseconds
   * @returns Normalized time in [0, 1]
   */
  toNormalizedTime(normalizedStroke: NormalizedStroke, timestamp: number): number {
    if (normalizedStroke.durationMs === 0) {
      return 0;
    }

    return (timestamp - normalizedStroke.originalStartTime) / normalizedStroke.durationMs;
  }
}
