/**
 * AIProfileHooks - Temporal feature extraction for AI
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 3: AI Integration
 *
 * Integrates all AI components to extract comprehensive temporal features:
 * - Momentum analysis (pressure × velocity)
 * - Velocity smoothing (Savitzky-Golay)
 * - Stroke classification (gesture/detail/shading/corrective)
 * - Pause detection (micro/thinking/deliberate)
 *
 * Features are exported for:
 * - AI training datasets
 * - Artist style fingerprinting
 * - Drawing pattern analysis
 * - Provenance tracking
 */

import { NormalizedStroke } from '../core/ReplayNormalizer';
import { MomentumCalculator, MomentumStats } from './MomentumCalculator';
import { VelocitySmoother } from './VelocitySmoother';
import { StrokeClassifier, ClassificationResult, PauseInfo, StrokeClass } from './StrokeClassifier';

/**
 * Comprehensive temporal feature set for AI
 */
export interface TemporalFeatures {
  /** Session identifier */
  sessionId: string;

  /** Artist profile ID (if available) */
  artistProfileId?: string;

  /** Total session duration (milliseconds) */
  sessionDuration: number;

  /** Total number of strokes */
  totalStrokes: number;

  /** Stroke classifications */
  strokeClasses: {
    gesture: number;
    detail: number;
    shading: number;
    corrective: number;
  };

  /** Momentum statistics */
  momentum: {
    overall: MomentumStats;
    byClass: Record<StrokeClass, MomentumStats>;
  };

  /** Velocity statistics */
  velocity: {
    meanRaw: number;
    meanSmoothed: number;
    maxRaw: number;
    maxSmoothed: number;
    noiseReduction: number;
  };

  /** Pause statistics */
  pauses: {
    total: number;
    micro: number;
    thinking: number;
    deliberate: number;
    meanDuration: number;
    maxDuration: number;
  };

  /** Drawing rhythm metrics */
  rhythm: {
    strokesPerMinute: number;
    averageStrokeDuration: number;
    burstiness: number; // Coefficient of variation of inter-stroke intervals
  };

  /** Pressure statistics */
  pressure: {
    mean: number;
    stdDev: number;
    min: number;
    max: number;
  };

  /** Spatial statistics */
  spatial: {
    canvasUtilization: number; // Percentage of canvas used
    meanStrokeLength: number;
    totalPathLength: number;
  };
}

/**
 * Per-stroke temporal features
 */
export interface StrokeTemporalFeatures {
  /** Stroke ID */
  strokeId: string;

  /** Stroke classification */
  class: StrokeClass;

  /** Classification confidence */
  confidence: number;

  /** Momentum statistics for this stroke */
  momentum: MomentumStats;

  /** Velocity statistics */
  velocity: {
    mean: number;
    max: number;
    peaks: number[]; // Indices of velocity peaks
    valleys: number[]; // Indices of velocity valleys
  };

  /** Duration (milliseconds) */
  duration: number;

  /** Length (pixels) */
  length: number;

  /** Straightness (0-1) */
  straightness: number;

  /** Pressure variation */
  pressureVariation: number;

  /** Pause before this stroke (if any) */
  pauseBefore?: PauseInfo;
}

/**
 * AIProfileHooks - Extracts temporal features for AI
 */
export class AIProfileHooks {
  private momentumCalculator: MomentumCalculator;
  private velocitySmoother: VelocitySmoother;
  private strokeClassifier: StrokeClassifier;

  constructor() {
    this.momentumCalculator = new MomentumCalculator();
    this.velocitySmoother = new VelocitySmoother();
    this.strokeClassifier = new StrokeClassifier();
  }

  /**
   * Extract comprehensive temporal features from a drawing session
   *
   * @param strokes Array of normalized strokes
   * @param sessionId Session identifier
   * @param artistProfileId Optional artist profile ID
   * @returns Complete temporal feature set
   */
  extractSessionFeatures(
    strokes: NormalizedStroke[],
    sessionId: string,
    artistProfileId?: string
  ): TemporalFeatures {
    if (strokes.length === 0) {
      return this.emptyFeatures(sessionId, artistProfileId);
    }

    // Classify strokes
    const classifications = this.strokeClassifier.classifyAll(strokes);
    const classStats = this.strokeClassifier.getClassificationStats(classifications);

    // Detect pauses
    const pauses = this.strokeClassifier.detectPauses(strokes);
    const pauseStatsRaw = this.strokeClassifier.getPauseStats(pauses);
    const pauseStats = {
      total: pauseStatsRaw.totalPauses,
      micro: pauseStatsRaw.microPauses,
      thinking: pauseStatsRaw.thinkingPauses,
      deliberate: pauseStatsRaw.deliberatePauses,
      meanDuration: pauseStatsRaw.meanDuration,
      maxDuration: pauseStatsRaw.maxDuration
    };

    // Calculate momentum
    const overallMomentum = this.momentumCalculator.calculateAggregateStats(strokes);
    const momentumByClass = this.calculateMomentumByClass(strokes, classifications);

    // Calculate velocity statistics
    const velocityStats = this.calculateVelocityStats(strokes);

    // Calculate rhythm metrics
    const rhythmMetrics = this.calculateRhythmMetrics(strokes, pauses);

    // Calculate pressure statistics
    const pressureStats = this.calculatePressureStats(strokes);

    // Calculate spatial statistics
    const spatialStats = this.calculateSpatialStats(strokes);

    // Session duration
    const sessionStartTime = Math.min(...strokes.map(s => s.originalStartTime));
    const sessionEndTime = Math.max(...strokes.map(s => s.originalEndTime));
    const sessionDuration = sessionEndTime - sessionStartTime;

    return {
      sessionId,
      artistProfileId,
      sessionDuration,
      totalStrokes: strokes.length,
      strokeClasses: classStats,
      momentum: {
        overall: overallMomentum,
        byClass: momentumByClass
      },
      velocity: velocityStats,
      pauses: pauseStats,
      rhythm: rhythmMetrics,
      pressure: pressureStats,
      spatial: spatialStats
    };
  }

  /**
   * Extract per-stroke temporal features
   *
   * @param strokes Array of normalized strokes
   * @returns Array of per-stroke features
   */
  extractStrokeFeatures(strokes: NormalizedStroke[]): StrokeTemporalFeatures[] {
    const classifications = this.strokeClassifier.classifyAll(strokes);
    const pauses = this.strokeClassifier.detectPauses(strokes);

    return strokes.map((stroke, i) => {
      const classification = classifications[i];
      const momentumPoints = this.momentumCalculator.calculateStrokeMomentum(stroke);
      const momentumStats = this.momentumCalculator.calculateStats(momentumPoints);

      const smoothedPoints = this.velocitySmoother.smoothStroke(stroke);
      const velocityPeaks = this.velocitySmoother.detectPeaks(smoothedPoints);
      const velocityValleys = this.velocitySmoother.detectValleys(smoothedPoints);

      const velocities = smoothedPoints.map(p => p.smoothedVelocity);
      const meanVelocity = velocities.reduce((a, b) => a + b, 0) / velocities.length;
      const maxVelocity = Math.max(...velocities);

      // Calculate length
      let length = 0;
      for (let j = 1; j < stroke.points.length; j++) {
        const dx = stroke.points[j].x - stroke.points[j - 1].x;
        const dy = stroke.points[j].y - stroke.points[j - 1].y;
        length += Math.sqrt(dx * dx + dy * dy);
      }

      // Straightness
      const directDistance = Math.sqrt(
        (stroke.points[stroke.points.length - 1].x - stroke.points[0].x) ** 2 +
        (stroke.points[stroke.points.length - 1].y - stroke.points[0].y) ** 2
      );
      const straightness = length === 0 ? 0 : directDistance / length;

      // Pressure variation
      const pressures = stroke.points.map(p => p.pressure);
      const meanPressure = pressures.reduce((a, b) => a + b, 0) / pressures.length;
      const pressureVariation = Math.sqrt(
        pressures.reduce((acc, p) => acc + (p - meanPressure) ** 2, 0) / pressures.length
      );

      // Find pause before this stroke
      const pauseBefore = pauses.find(p => p.afterStrokeIndex === i - 1);

      return {
        strokeId: stroke.id,
        class: classification.class,
        confidence: classification.confidence,
        momentum: momentumStats,
        velocity: {
          mean: meanVelocity,
          max: maxVelocity,
          peaks: velocityPeaks,
          valleys: velocityValleys
        },
        duration: stroke.durationMs,
        length,
        straightness,
        pressureVariation,
        pauseBefore
      };
    });
  }

  /**
   * Calculate momentum statistics grouped by stroke class
   */
  private calculateMomentumByClass(
    strokes: NormalizedStroke[],
    classifications: ClassificationResult[]
  ): Record<StrokeClass, MomentumStats> {
    const byClass: Record<StrokeClass, NormalizedStroke[]> = {
      gesture: [],
      detail: [],
      shading: [],
      corrective: []
    };

    strokes.forEach((stroke, i) => {
      byClass[classifications[i].class].push(stroke);
    });

    return {
      gesture: this.momentumCalculator.calculateAggregateStats(byClass.gesture),
      detail: this.momentumCalculator.calculateAggregateStats(byClass.detail),
      shading: this.momentumCalculator.calculateAggregateStats(byClass.shading),
      corrective: this.momentumCalculator.calculateAggregateStats(byClass.corrective)
    };
  }

  /**
   * Calculate aggregate velocity statistics
   */
  private calculateVelocityStats(strokes: NormalizedStroke[]): {
    meanRaw: number;
    meanSmoothed: number;
    maxRaw: number;
    maxSmoothed: number;
    noiseReduction: number;
  } {
    const allSmoothedPoints = strokes.flatMap(stroke => this.velocitySmoother.smoothStroke(stroke));

    if (allSmoothedPoints.length === 0) {
      return {
        meanRaw: 0,
        meanSmoothed: 0,
        maxRaw: 0,
        maxSmoothed: 0,
        noiseReduction: 0
      };
    }

    return this.velocitySmoother.calculateStats(allSmoothedPoints);
  }

  /**
   * Calculate drawing rhythm metrics
   */
  private calculateRhythmMetrics(strokes: NormalizedStroke[], pauses: PauseInfo[]): {
    strokesPerMinute: number;
    averageStrokeDuration: number;
    burstiness: number;
  } {
    if (strokes.length === 0) {
      return {
        strokesPerMinute: 0,
        averageStrokeDuration: 0,
        burstiness: 0
      };
    }

    // Session duration
    const sessionStart = Math.min(...strokes.map(s => s.originalStartTime));
    const sessionEnd = Math.max(...strokes.map(s => s.originalEndTime));
    const sessionDuration = sessionEnd - sessionStart;

    // Strokes per minute
    const strokesPerMinute = sessionDuration === 0 ? 0 : (strokes.length / sessionDuration) * 60000;

    // Average stroke duration
    const averageStrokeDuration = strokes.reduce((sum, s) => sum + s.durationMs, 0) / strokes.length;

    // Burstiness (coefficient of variation of inter-stroke intervals)
    if (pauses.length === 0) {
      return {
        strokesPerMinute,
        averageStrokeDuration,
        burstiness: 0
      };
    }

    const intervals = pauses.map(p => p.duration);
    const meanInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
    const stdDevInterval = Math.sqrt(
      intervals.reduce((acc, interval) => acc + (interval - meanInterval) ** 2, 0) / intervals.length
    );

    const burstiness = meanInterval === 0 ? 0 : stdDevInterval / meanInterval;

    return {
      strokesPerMinute,
      averageStrokeDuration,
      burstiness
    };
  }

  /**
   * Calculate pressure statistics
   */
  private calculatePressureStats(strokes: NormalizedStroke[]): {
    mean: number;
    stdDev: number;
    min: number;
    max: number;
  } {
    const allPressures = strokes.flatMap(s => s.points.map(p => p.pressure));

    if (allPressures.length === 0) {
      return { mean: 0, stdDev: 0, min: 0, max: 0 };
    }

    const mean = allPressures.reduce((a, b) => a + b, 0) / allPressures.length;
    const stdDev = Math.sqrt(
      allPressures.reduce((acc, p) => acc + (p - mean) ** 2, 0) / allPressures.length
    );
    const min = Math.min(...allPressures);
    const max = Math.max(...allPressures);

    return { mean, stdDev, min, max };
  }

  /**
   * Calculate spatial statistics
   */
  private calculateSpatialStats(strokes: NormalizedStroke[]): {
    canvasUtilization: number;
    meanStrokeLength: number;
    totalPathLength: number;
  } {
    if (strokes.length === 0) {
      return {
        canvasUtilization: 0,
        meanStrokeLength: 0,
        totalPathLength: 0
      };
    }

    // Calculate bounding box
    const allPoints = strokes.flatMap(s => s.points);
    const xs = allPoints.map(p => p.x);
    const ys = allPoints.map(p => p.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    const usedArea = (maxX - minX) * (maxY - minY);
    const canvasUtilization = usedArea / (800 * 600); // Assuming 800x600 canvas

    // Calculate total path length
    let totalPathLength = 0;

    for (const stroke of strokes) {
      for (let i = 1; i < stroke.points.length; i++) {
        const dx = stroke.points[i].x - stroke.points[i - 1].x;
        const dy = stroke.points[i].y - stroke.points[i - 1].y;
        totalPathLength += Math.sqrt(dx * dx + dy * dy);
      }
    }

    const meanStrokeLength = totalPathLength / strokes.length;

    return {
      canvasUtilization,
      meanStrokeLength,
      totalPathLength
    };
  }

  /**
   * Return empty features for empty sessions
   */
  private emptyFeatures(sessionId: string, artistProfileId?: string): TemporalFeatures {
    const emptyMomentumStats: MomentumStats = {
      mean: 0,
      median: 0,
      stdDev: 0,
      min: 0,
      max: 0,
      range: 0,
      entropy: 0,
      coefficientOfVariation: 0
    };

    return {
      sessionId,
      artistProfileId,
      sessionDuration: 0,
      totalStrokes: 0,
      strokeClasses: { gesture: 0, detail: 0, shading: 0, corrective: 0 },
      momentum: {
        overall: emptyMomentumStats,
        byClass: {
          gesture: emptyMomentumStats,
          detail: emptyMomentumStats,
          shading: emptyMomentumStats,
          corrective: emptyMomentumStats
        }
      },
      velocity: {
        meanRaw: 0,
        meanSmoothed: 0,
        maxRaw: 0,
        maxSmoothed: 0,
        noiseReduction: 0
      },
      pauses: {
        total: 0,
        micro: 0,
        thinking: 0,
        deliberate: 0,
        meanDuration: 0,
        maxDuration: 0
      },
      rhythm: {
        strokesPerMinute: 0,
        averageStrokeDuration: 0,
        burstiness: 0
      },
      pressure: {
        mean: 0,
        stdDev: 0,
        min: 0,
        max: 0
      },
      spatial: {
        canvasUtilization: 0,
        meanStrokeLength: 0,
        totalPathLength: 0
      }
    };
  }

  /**
   * Export features as JSON for AI training
   *
   * @param features Temporal features
   * @returns JSON string
   */
  exportJSON(features: TemporalFeatures): string {
    return JSON.stringify(features, null, 2);
  }

  /**
   * Export features as CSV for data analysis
   *
   * @param features Array of temporal features
   * @returns CSV string
   */
  exportCSV(features: TemporalFeatures[]): string {
    if (features.length === 0) {
      return '';
    }

    const headers = [
      'sessionId',
      'artistProfileId',
      'sessionDuration',
      'totalStrokes',
      'gestureStrokes',
      'detailStrokes',
      'shadingStrokes',
      'correctiveStrokes',
      'momentumMean',
      'velocityMean',
      'strokesPerMinute',
      'burstiness'
    ];

    const rows = features.map(f => [
      f.sessionId,
      f.artistProfileId ?? '',
      f.sessionDuration,
      f.totalStrokes,
      f.strokeClasses.gesture,
      f.strokeClasses.detail,
      f.strokeClasses.shading,
      f.strokeClasses.corrective,
      f.momentum.overall.mean,
      f.velocity.meanSmoothed,
      f.rhythm.strokesPerMinute,
      f.rhythm.burstiness
    ]);

    return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  }
}
