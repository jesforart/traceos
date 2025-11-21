/**
 * StrokeClassifier - Classify strokes by drawing intent
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 3: AI Integration
 *
 * IMPROVEMENTS APPLIED:
 * - FIX #5: Separate micro-pauses (<50ms) from real pauses
 *
 * Four stroke categories:
 * 1. Gesture: Fast, long, establishing lines (low curvature, high velocity)
 * 2. Detail: Slow, short, precise work (high curvature, low velocity)
 * 3. Shading: Medium speed, high pressure variation, repetitive
 * 4. Corrective: Short, follows previous stroke (overlapping trajectory)
 */

import { NormalizedStroke } from '../core/ReplayNormalizer';
import { MomentumCalculator } from './MomentumCalculator';
import { VelocitySmoother, SmoothedPoint } from './VelocitySmoother';

/**
 * Stroke classification result
 */
export type StrokeClass = 'gesture' | 'detail' | 'shading' | 'corrective';

/**
 * Stroke features for classification
 */
export interface StrokeFeatures {
  /** Stroke length (pixels) */
  length: number;

  /** Duration (milliseconds) */
  duration: number;

  /** Mean velocity (px/ms) */
  meanVelocity: number;

  /** Mean pressure (0-1) */
  meanPressure: number;

  /** Pressure variance */
  pressureVariance: number;

  /** Curvature (radians per pixel) */
  curvature: number;

  /** Mean momentum */
  meanMomentum: number;

  /** Number of direction changes */
  directionChanges: number;

  /** Straightness (0-1, 1 = perfectly straight) */
  straightness: number;
}

/**
 * Classification result with confidence
 */
export interface ClassificationResult {
  /** Predicted class */
  class: StrokeClass;

  /** Confidence score (0-1) */
  confidence: number;

  /** Features used for classification */
  features: StrokeFeatures;
}

/**
 * Pause detection result
 *
 * FIX #5: Distinguish micro-pauses from real pauses
 */
export interface PauseInfo {
  /** Index in stroke array after which pause occurred */
  afterStrokeIndex: number;

  /** Pause duration (milliseconds) */
  duration: number;

  /** Pause type */
  type: 'micro' | 'thinking' | 'deliberate';

  /** Whether this is an inter-stroke pause */
  isInterStroke: boolean;
}

/**
 * StrokeClassifier - Classifies strokes by drawing intent
 */
export class StrokeClassifier {
  private momentumCalculator: MomentumCalculator;
  private velocitySmoother: VelocitySmoother;

  constructor() {
    this.momentumCalculator = new MomentumCalculator();
    this.velocitySmoother = new VelocitySmoother();
  }

  /**
   * Classify a single stroke
   *
   * @param stroke Normalized stroke to classify
   * @param previousStroke Optional previous stroke (for corrective detection)
   * @returns Classification result with confidence
   */
  classify(stroke: NormalizedStroke, previousStroke?: NormalizedStroke): ClassificationResult {
    const features = this.extractFeatures(stroke);

    // Rule-based classification with confidence scoring
    let classification: StrokeClass;
    let confidence: number;

    if (previousStroke && this.isCorrectiveStroke(stroke, previousStroke, features)) {
      classification = 'corrective';
      confidence = 0.85;
    } else if (this.isGestureStroke(features)) {
      classification = 'gesture';
      confidence = 0.9;
    } else if (this.isShadingStroke(features)) {
      classification = 'shading';
      confidence = 0.8;
    } else {
      classification = 'detail';
      confidence = 0.75;
    }

    return {
      class: classification,
      confidence,
      features
    };
  }

  /**
   * Extract features from a stroke for classification
   */
  private extractFeatures(stroke: NormalizedStroke): StrokeFeatures {
    const points = stroke.points;

    if (points.length < 2) {
      return {
        length: 0,
        duration: 0,
        meanVelocity: 0,
        meanPressure: 0,
        pressureVariance: 0,
        curvature: 0,
        meanMomentum: 0,
        directionChanges: 0,
        straightness: 0
      };
    }

    // Length
    let length = 0;
    for (let i = 1; i < points.length; i++) {
      const dx = points[i].x - points[i - 1].x;
      const dy = points[i].y - points[i - 1].y;
      length += Math.sqrt(dx * dx + dy * dy);
    }

    // Duration
    const duration = stroke.durationMs;

    // Velocity
    const velocities = points.map(p => p.velocity ?? 0);
    const meanVelocity = velocities.reduce((a, b) => a + b, 0) / velocities.length;

    // Pressure
    const pressures = points.map(p => p.pressure);
    const meanPressure = pressures.reduce((a, b) => a + b, 0) / pressures.length;
    const pressureVariance = pressures.reduce((acc, p) => acc + (p - meanPressure) ** 2, 0) / pressures.length;

    // Curvature (total angular change / length)
    let totalAngleChange = 0;
    for (let i = 1; i < points.length - 1; i++) {
      const angle1 = Math.atan2(points[i].y - points[i - 1].y, points[i].x - points[i - 1].x);
      const angle2 = Math.atan2(points[i + 1].y - points[i].y, points[i + 1].x - points[i].x);
      const angleDiff = Math.abs(angle2 - angle1);
      totalAngleChange += Math.min(angleDiff, 2 * Math.PI - angleDiff);
    }
    const curvature = length === 0 ? 0 : totalAngleChange / length;

    // Momentum
    const momentumPoints = this.momentumCalculator.calculateStrokeMomentum(stroke);
    const meanMomentum = momentumPoints.reduce((sum, p) => sum + p.momentum, 0) / momentumPoints.length;

    // Direction changes (inflection points)
    let directionChanges = 0;
    for (let i = 1; i < points.length - 1; i++) {
      const dx1 = points[i].x - points[i - 1].x;
      const dy1 = points[i].y - points[i - 1].y;
      const dx2 = points[i + 1].x - points[i].x;
      const dy2 = points[i + 1].y - points[i].y;

      // Cross product sign change indicates direction change
      const cross1 = dx1 * dy2 - dy1 * dx2;
      if (i > 1) {
        const dx0 = points[i - 1].x - points[i - 2].x;
        const dy0 = points[i - 1].y - points[i - 2].y;
        const cross0 = dx0 * dy1 - dy0 * dx1;

        if (cross0 * cross1 < 0) {
          directionChanges++;
        }
      }
    }

    // Straightness (ratio of direct distance to path length)
    const directDistance = Math.sqrt(
      (points[points.length - 1].x - points[0].x) ** 2 +
      (points[points.length - 1].y - points[0].y) ** 2
    );
    const straightness = length === 0 ? 0 : directDistance / length;

    return {
      length,
      duration,
      meanVelocity,
      meanPressure,
      pressureVariance,
      curvature,
      meanMomentum,
      directionChanges,
      straightness
    };
  }

  /**
   * Check if stroke is a gesture (fast, long, straight)
   */
  private isGestureStroke(features: StrokeFeatures): boolean {
    return (
      features.length > 100 &&           // Long stroke
      features.meanVelocity > 150 &&     // Fast
      features.straightness > 0.7 &&     // Relatively straight
      features.curvature < 0.01          // Low curvature
    );
  }

  /**
   * Check if stroke is shading (repetitive, pressure variation)
   */
  private isShadingStroke(features: StrokeFeatures): boolean {
    return (
      features.pressureVariance > 0.05 &&  // High pressure variation
      features.directionChanges > 3 &&     // Repetitive motion
      features.meanVelocity > 50 &&        // Not too slow
      features.meanVelocity < 200          // Not too fast
    );
  }

  /**
   * Check if stroke is corrective (follows previous stroke path)
   */
  private isCorrectiveStroke(
    stroke: NormalizedStroke,
    previousStroke: NormalizedStroke,
    features: StrokeFeatures
  ): boolean {
    // Corrective strokes are typically:
    // - Short (< 50px)
    // - Quick (< 200ms after previous)
    // - Overlapping with previous stroke

    if (features.length > 50) {
      return false;
    }

    const timeSincePrevious = stroke.originalStartTime - previousStroke.originalEndTime;

    if (timeSincePrevious > 200) {
      return false; // Too long after previous stroke
    }

    // Check spatial overlap
    const overlap = this.calculateSpatialOverlap(stroke, previousStroke);

    return overlap > 0.5; // At least 50% overlap
  }

  /**
   * Calculate spatial overlap between two strokes (0-1)
   */
  private calculateSpatialOverlap(stroke1: NormalizedStroke, stroke2: NormalizedStroke): number {
    // Simple bounding box overlap check
    const bbox1 = this.getBoundingBox(stroke1);
    const bbox2 = this.getBoundingBox(stroke2);

    const overlapX = Math.max(0, Math.min(bbox1.maxX, bbox2.maxX) - Math.max(bbox1.minX, bbox2.minX));
    const overlapY = Math.max(0, Math.min(bbox1.maxY, bbox2.maxY) - Math.max(bbox1.minY, bbox2.minY));

    const overlapArea = overlapX * overlapY;
    const area1 = (bbox1.maxX - bbox1.minX) * (bbox1.maxY - bbox1.minY);

    return area1 === 0 ? 0 : overlapArea / area1;
  }

  /**
   * Get bounding box of a stroke
   */
  private getBoundingBox(stroke: NormalizedStroke): {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
  } {
    const xs = stroke.points.map(p => p.x);
    const ys = stroke.points.map(p => p.y);

    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys)
    };
  }

  /**
   * Classify multiple strokes
   *
   * @param strokes Array of normalized strokes
   * @returns Array of classification results
   */
  classifyAll(strokes: NormalizedStroke[]): ClassificationResult[] {
    const results: ClassificationResult[] = [];

    for (let i = 0; i < strokes.length; i++) {
      const previousStroke = i > 0 ? strokes[i - 1] : undefined;
      results.push(this.classify(strokes[i], previousStroke));
    }

    return results;
  }

  /**
   * Detect pauses between strokes
   *
   * FIX #5: Distinguish micro-pauses (<50ms) from thinking (50-500ms) and deliberate (>500ms) pauses
   *
   * @param strokes Array of normalized strokes (must be sorted by startTime)
   * @returns Array of pause information
   */
  detectPauses(strokes: NormalizedStroke[]): PauseInfo[] {
    if (strokes.length < 2) {
      return [];
    }

    const pauses: PauseInfo[] = [];

    for (let i = 0; i < strokes.length - 1; i++) {
      const currentStroke = strokes[i];
      const nextStroke = strokes[i + 1];

      const pauseDuration = nextStroke.originalStartTime - currentStroke.originalEndTime;

      if (pauseDuration < 0) {
        // Overlapping strokes (multi-touch or error)
        continue;
      }

      // FIX #5: Classify pause type
      let type: 'micro' | 'thinking' | 'deliberate';

      if (pauseDuration < 50) {
        type = 'micro'; // Hand repositioning, continuous drawing
      } else if (pauseDuration < 500) {
        type = 'thinking'; // Brief consideration
      } else {
        type = 'deliberate'; // Intentional pause, planning, or distraction
      }

      pauses.push({
        afterStrokeIndex: i,
        duration: pauseDuration,
        type,
        isInterStroke: true
      });
    }

    return pauses;
  }

  /**
   * Get classification statistics
   *
   * @param results Array of classification results
   * @returns Statistics by class
   */
  getClassificationStats(results: ClassificationResult[]): {
    gesture: number;
    detail: number;
    shading: number;
    corrective: number;
    total: number;
  } {
    const stats = {
      gesture: 0,
      detail: 0,
      shading: 0,
      corrective: 0,
      total: results.length
    };

    for (const result of results) {
      stats[result.class]++;
    }

    return stats;
  }

  /**
   * Calculate pause statistics
   *
   * @param pauses Array of pause information
   * @returns Pause statistics
   */
  getPauseStats(pauses: PauseInfo[]): {
    totalPauses: number;
    microPauses: number;
    thinkingPauses: number;
    deliberatePauses: number;
    meanDuration: number;
    maxDuration: number;
  } {
    if (pauses.length === 0) {
      return {
        totalPauses: 0,
        microPauses: 0,
        thinkingPauses: 0,
        deliberatePauses: 0,
        meanDuration: 0,
        maxDuration: 0
      };
    }

    const microPauses = pauses.filter(p => p.type === 'micro').length;
    const thinkingPauses = pauses.filter(p => p.type === 'thinking').length;
    const deliberatePauses = pauses.filter(p => p.type === 'deliberate').length;

    const durations = pauses.map(p => p.duration);
    const meanDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
    const maxDuration = Math.max(...durations);

    return {
      totalPauses: pauses.length,
      microPauses,
      thinkingPauses,
      deliberatePauses,
      meanDuration,
      maxDuration
    };
  }
}
