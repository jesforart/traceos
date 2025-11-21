/**
 * Week 5: Style DNA Encoding - Stroke DNA Encoder
 *
 * Extracts 30-dimensional feature vector from stroke data.
 * Hot path encoding - must complete in <16ms.
 */

import { StyleDNAConfig, STROKE_DNA_INDEX } from '../config';
import { globalBoundsNormalizer } from '../BoundsNormalizer';
import type { StrokeDNA, DNAEncoder, ArtistContext } from '../types';
import { ulid } from '../../../utils/ulid';

/**
 * Stroke Point - Input data
 */
export interface StrokePoint {
  x: number;
  y: number;
  pressure?: number;
  tilt_x?: number;
  tilt_y?: number;
  twist?: number;
  timestamp?: number;
}

/**
 * Stroke Data - Complete stroke input
 */
export interface StrokeData {
  stroke_id: string;
  points: StrokePoint[];
  tool: string;
  color: string;
  brush_size: number;
  canvas_width: number;
  canvas_height: number;
}

/**
 * Stroke DNA Encoder
 * Fast feature extraction for real-time encoding
 */
export class StrokeDNAEncoder implements DNAEncoder<StrokeDNA> {
  private readonly dimension = StyleDNAConfig.dimensions.stroke;

  /**
   * Synchronous encoding (hot path)
   */
  encodeSync(stroke_data: StrokeData, context?: ArtistContext): StrokeDNA {
    const start_time = performance.now();
    const features = new Float32Array(this.dimension);

    const points = stroke_data.points;
    if (points.length === 0) {
      throw new Error('Cannot encode empty stroke');
    }

    // Normalize bounds
    const { normalized_points, normalized_bounds } = globalBoundsNormalizer.normalizeStroke(
      points,
      stroke_data.canvas_width,
      stroke_data.canvas_height
    );

    // Extract features
    this.extractGeometricFeatures(normalized_points, features);
    this.extractStatisticalFeatures(normalized_points, features);
    this.extractDynamicFeatures(points, features);

    const encoding_time_ms = performance.now() - start_time;

    return {
      dna_id: ulid(),
      stroke_id: stroke_data.stroke_id,
      session_id: context?.session_id || 'unknown',
      features,
      normalized_bounds: normalized_bounds.normalized,
      tool: stroke_data.tool,
      color: stroke_data.color,
      timestamp: Date.now(),
      encoding_time_ms
    };
  }

  /**
   * Async encoding (delegates to sync)
   */
  async encode(stroke_data: StrokeData, context?: ArtistContext): Promise<StrokeDNA> {
    return this.encodeSync(stroke_data, context);
  }

  /**
   * Extract geometric features (indices 0-9)
   */
  private extractGeometricFeatures(points: StrokePoint[], features: Float32Array): void {
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);

    const min_x = Math.min(...xs);
    const max_x = Math.max(...xs);
    const min_y = Math.min(...ys);
    const max_y = Math.max(...ys);

    const width = max_x - min_x;
    const height = max_y - min_y;

    // MEAN_X, MEAN_Y
    features[STROKE_DNA_INDEX.MEAN_X] = this.mean(xs);
    features[STROKE_DNA_INDEX.MEAN_Y] = this.mean(ys);

    // WIDTH, HEIGHT
    features[STROKE_DNA_INDEX.WIDTH] = width;
    features[STROKE_DNA_INDEX.HEIGHT] = height;

    // ASPECT_RATIO
    features[STROKE_DNA_INDEX.ASPECT_RATIO] = height > 0 ? width / height : 0;

    // AREA (bounding box)
    features[STROKE_DNA_INDEX.AREA] = width * height;

    // PERIMETER (approximation)
    let perimeter = 0;
    for (let i = 1; i < points.length; i++) {
      const dx = points[i].x - points[i - 1].x;
      const dy = points[i].y - points[i - 1].y;
      perimeter += Math.sqrt(dx * dx + dy * dy);
    }
    features[STROKE_DNA_INDEX.PERIMETER] = perimeter;

    // COMPACTNESS (4π * area / perimeter²)
    const compactness =
      perimeter > 0 ? (4 * Math.PI * features[STROKE_DNA_INDEX.AREA]) / (perimeter * perimeter) : 0;
    features[STROKE_DNA_INDEX.COMPACTNESS] = compactness;

    // ELONGATION (ratio of principal axes)
    const elongation = this.calculateElongation(points);
    features[STROKE_DNA_INDEX.ELONGATION] = elongation;

    // ORIENTATION (angle of principal axis)
    const orientation = this.calculateOrientation(points);
    features[STROKE_DNA_INDEX.ORIENTATION] = orientation;
  }

  /**
   * Extract statistical features (indices 10-19)
   */
  private extractStatisticalFeatures(points: StrokePoint[], features: Float32Array): void {
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);

    // X_VARIANCE, Y_VARIANCE
    features[STROKE_DNA_INDEX.X_VARIANCE] = this.variance(xs);
    features[STROKE_DNA_INDEX.Y_VARIANCE] = this.variance(ys);

    // X_SKEWNESS, Y_SKEWNESS
    features[STROKE_DNA_INDEX.X_SKEWNESS] = this.skewness(xs);
    features[STROKE_DNA_INDEX.Y_SKEWNESS] = this.skewness(ys);

    // X_KURTOSIS, Y_KURTOSIS
    features[STROKE_DNA_INDEX.X_KURTOSIS] = this.kurtosis(xs);
    features[STROKE_DNA_INDEX.Y_KURTOSIS] = this.kurtosis(ys);

    // POINT_DENSITY (points per unit length)
    const perimeter = features[STROKE_DNA_INDEX.PERIMETER];
    features[STROKE_DNA_INDEX.POINT_DENSITY] = perimeter > 0 ? points.length / perimeter : 0;

    // CURVATURE_MEAN
    const curvatures = this.calculateCurvatures(points);
    features[STROKE_DNA_INDEX.CURVATURE_MEAN] = this.mean(curvatures);

    // CURVATURE_STD
    features[STROKE_DNA_INDEX.CURVATURE_STD] = Math.sqrt(this.variance(curvatures));

    // CORNER_COUNT (high curvature points)
    const corner_threshold = 0.5; // Radians
    const corner_count = curvatures.filter((c) => Math.abs(c) > corner_threshold).length;
    features[STROKE_DNA_INDEX.CORNER_COUNT] = corner_count;
  }

  /**
   * Extract dynamic features (indices 20-29)
   */
  private extractDynamicFeatures(points: StrokePoint[], features: Float32Array): void {
    // Calculate velocities
    const velocities: number[] = [];
    for (let i = 1; i < points.length; i++) {
      const dx = points[i].x - points[i - 1].x;
      const dy = points[i].y - points[i - 1].y;
      const dt =
        points[i].timestamp && points[i - 1].timestamp
          ? (points[i].timestamp! - points[i - 1].timestamp!) / 1000
          : 0.016; // Default 60fps

      const velocity = dt > 0 ? Math.sqrt(dx * dx + dy * dy) / dt : 0;
      velocities.push(velocity);
    }

    // AVG_VELOCITY, MAX_VELOCITY
    features[STROKE_DNA_INDEX.AVG_VELOCITY] = this.mean(velocities);
    features[STROKE_DNA_INDEX.MAX_VELOCITY] = Math.max(...velocities, 0);

    // Calculate accelerations
    const accelerations: number[] = [];
    for (let i = 1; i < velocities.length; i++) {
      const dv = velocities[i] - velocities[i - 1];
      const dt = 0.016; // Assume consistent timestep
      accelerations.push(dt > 0 ? dv / dt : 0);
    }

    // AVG_ACCELERATION, MAX_ACCELERATION
    features[STROKE_DNA_INDEX.AVG_ACCELERATION] = this.mean(accelerations);
    features[STROKE_DNA_INDEX.MAX_ACCELERATION] = Math.max(...accelerations.map(Math.abs), 0);

    // Pressure features
    const pressures = points.map((p) => p.pressure || 0.5);
    features[STROKE_DNA_INDEX.PRESSURE_MEAN] = this.mean(pressures);
    features[STROKE_DNA_INDEX.PRESSURE_STD] = Math.sqrt(this.variance(pressures));

    // Tilt features (if available)
    const tilts = points.map((p) => (p.tilt_x || 0) + (p.tilt_y || 0));
    features[STROKE_DNA_INDEX.TILT_MEAN] = this.mean(tilts);

    // Twist features (if available)
    const twists = points.map((p) => p.twist || 0);
    features[STROKE_DNA_INDEX.TWIST_MEAN] = this.mean(twists);

    // DURATION (first to last timestamp)
    const first_time = points[0].timestamp || 0;
    const last_time = points[points.length - 1].timestamp || 0;
    features[STROKE_DNA_INDEX.DURATION] = (last_time - first_time) / 1000; // Seconds

    // PAUSE_COUNT (detect pauses in drawing)
    const pause_threshold = 0.1; // 100ms
    let pause_count = 0;
    for (let i = 1; i < points.length; i++) {
      if (points[i].timestamp && points[i - 1].timestamp) {
        const dt = (points[i].timestamp! - points[i - 1].timestamp!) / 1000;
        if (dt > pause_threshold) {
          pause_count++;
        }
      }
    }
    features[STROKE_DNA_INDEX.PAUSE_COUNT] = pause_count;
  }

  /**
   * Calculate elongation using PCA
   */
  private calculateElongation(points: StrokePoint[]): number {
    const mean_x = this.mean(points.map((p) => p.x));
    const mean_y = this.mean(points.map((p) => p.y));

    // Covariance matrix
    let cov_xx = 0;
    let cov_yy = 0;
    let cov_xy = 0;

    for (const p of points) {
      const dx = p.x - mean_x;
      const dy = p.y - mean_y;
      cov_xx += dx * dx;
      cov_yy += dy * dy;
      cov_xy += dx * dy;
    }

    cov_xx /= points.length;
    cov_yy /= points.length;
    cov_xy /= points.length;

    // Eigenvalues (simplified)
    const trace = cov_xx + cov_yy;
    const det = cov_xx * cov_yy - cov_xy * cov_xy;
    const lambda1 = trace / 2 + Math.sqrt((trace * trace) / 4 - det);
    const lambda2 = trace / 2 - Math.sqrt((trace * trace) / 4 - det);

    return lambda2 > 0 ? lambda1 / lambda2 : 1;
  }

  /**
   * Calculate orientation angle
   */
  private calculateOrientation(points: StrokePoint[]): number {
    const mean_x = this.mean(points.map((p) => p.x));
    const mean_y = this.mean(points.map((p) => p.y));

    let cov_xy = 0;
    let cov_xx = 0;

    for (const p of points) {
      const dx = p.x - mean_x;
      const dy = p.y - mean_y;
      cov_xy += dx * dy;
      cov_xx += dx * dx;
    }

    return Math.atan2(2 * cov_xy, cov_xx);
  }

  /**
   * Calculate curvatures at each point
   */
  private calculateCurvatures(points: StrokePoint[]): number[] {
    const curvatures: number[] = [];

    for (let i = 1; i < points.length - 1; i++) {
      const p1 = points[i - 1];
      const p2 = points[i];
      const p3 = points[i + 1];

      const v1x = p2.x - p1.x;
      const v1y = p2.y - p1.y;
      const v2x = p3.x - p2.x;
      const v2y = p3.y - p2.y;

      const cross = v1x * v2y - v1y * v2x;
      const dot = v1x * v2x + v1y * v2y;

      const curvature = Math.atan2(cross, dot);
      curvatures.push(curvature);
    }

    return curvatures;
  }

  /**
   * Statistical utilities
   */
  private mean(values: number[]): number {
    return values.reduce((a, b) => a + b, 0) / values.length;
  }

  private variance(values: number[]): number {
    const m = this.mean(values);
    return values.reduce((sum, v) => sum + (v - m) ** 2, 0) / values.length;
  }

  private skewness(values: number[]): number {
    const m = this.mean(values);
    const std = Math.sqrt(this.variance(values));
    if (std === 0) return 0;
    return values.reduce((sum, v) => sum + ((v - m) / std) ** 3, 0) / values.length;
  }

  private kurtosis(values: number[]): number {
    const m = this.mean(values);
    const std = Math.sqrt(this.variance(values));
    if (std === 0) return 0;
    return values.reduce((sum, v) => sum + ((v - m) / std) ** 4, 0) / values.length - 3;
  }

  getDimension(): number {
    return this.dimension;
  }

  getTier(): 'stroke' | 'image' | 'temporal' {
    return 'stroke';
  }
}

/**
 * Global encoder instance
 */
export const globalStrokeDNAEncoder = new StrokeDNAEncoder();
