/**
 * Calibration system types - Personal feel calibration
 */

import { Stroke } from './stroke';

export interface CalibrationPhase {
  /** Phase identifier */
  id: 'feather' | 'normal' | 'heavy';

  /** Display name */
  name: string;

  /** Instructions for user */
  instruction: string;

  /** Duration in seconds */
  durationSeconds: number;

  /** Example image/animation (optional) */
  exampleUrl?: string;
}

export interface CalibrationStroke {
  /** Stroke data from drawing surface */
  stroke: Stroke;

  /** Which phase this was captured in */
  phase: 'feather' | 'normal' | 'heavy';

  /** Timestamp of capture */
  timestamp: number;
}

export interface CalibrationSession {
  /** Unique session ID */
  id: string;

  /** User identifier */
  userId?: string;

  /** All strokes captured during calibration */
  strokes: CalibrationStroke[];

  /** Start time */
  startedAt: number;

  /** End time */
  completedAt?: number;

  /** Current phase */
  currentPhase: 'feather' | 'normal' | 'heavy' | 'complete';

  /** Generated profile (after analysis) */
  profile?: ArtistProfile;
}

export interface PressureDistribution {
  /** Minimum pressure observed */
  min: number;

  /** Maximum pressure observed */
  max: number;

  /** Mean pressure */
  mean: number;

  /** Median pressure */
  median: number;

  /** Standard deviation */
  stdDev: number;

  /** Histogram bins (10 bins from 0-1) */
  histogram: number[];
}

export interface TiltDistribution {
  /** Average tilt angle in degrees */
  avgTiltDeg: number;

  /** Average azimuth angle in degrees */
  avgAzimuthDeg: number;

  /** Tilt range (min, max) */
  tiltRange: [number, number];

  /** Most common tilt angle */
  modeTiltDeg: number;
}

export interface VelocityDistribution {
  /** Average velocity in px/s */
  avgVelocity: number;

  /** Max velocity observed */
  maxVelocity: number;

  /** Velocity at 25th percentile */
  p25Velocity: number;

  /** Velocity at 75th percentile */
  p75Velocity: number;
}

export interface BezierCurve {
  /** 4 control points for cubic Bezier */
  controlPoints: [
    [number, number], // P0
    [number, number], // P1
    [number, number], // P2
    [number, number]  // P3
  ];
}

export interface ArtistProfile {
  /** Profile identifier */
  id: string;

  /** Artist name */
  artistName: string;

  /** Creation timestamp */
  createdAt: number;

  /** Version (for schema changes) */
  version: number;

  /** Trace profile version */
  traceProfileVersion: string;

  /** Brush engine version */
  brushEngineVersion: string;

  /** Device info */
  device: {
    type: string;
    model?: string;
    stylus?: string;
    calibrationFingerprint?: string;
    capturedAt?: number;
  };

  /** Statistical distributions */
  distributions: {
    feather: {
      pressure: PressureDistribution;
      tilt: TiltDistribution;
      velocity: VelocityDistribution;
    };
    normal: {
      pressure: PressureDistribution;
      tilt: TiltDistribution;
      velocity: VelocityDistribution;
    };
    heavy: {
      pressure: PressureDistribution;
      tilt: TiltDistribution;
      velocity: VelocityDistribution;
    };
  };

  /** Fitted curves (ready for GPU renderer) */
  curves: {
    pressureToRadius: BezierCurve;
    pressureToDensity: BezierCurve;
    velocityToOpacity: Array<[number, number]>;
    velocityToSoftness: Array<[number, number]>;
  };

  /** Nib parameters */
  nib: {
    baseRadiusPx: number;
    minRadiusPx: number;
    maxRadiusPx: number;
    avgTiltDeg: number;
  };

  /** Stabilizer settings */
  stabilizer: {
    microJitterRadiusPx: number;
    curveSmooth: {
      min: number;
      max: number;
    };
    velocityAdapt: {
      vMin: number;
      vMax: number;
    };
  };

  /** Temporal features (Week 3: Replay engine integration) */
  temporal?: {
    /** Baseline momentum mean (pressure × velocity) */
    momentumMean: number;

    /** Baseline velocity mean (px/ms) */
    velocityMean: number;

    /** Stroke class distribution */
    strokeClassDistribution: {
      gesture: number;
      detail: number;
      shading: number;
      corrective: number;
    };

    /** Average strokes per minute */
    strokesPerMinute: number;

    /** Burstiness (coefficient of variation of inter-stroke intervals) */
    burstiness: number;

    /** Last updated timestamp */
    lastUpdated: number;

    /** Number of sessions used to compute baseline */
    sessionCount: number;
  };
}

export const CALIBRATION_PHASES: CalibrationPhase[] = [
  {
    id: 'feather',
    name: 'Feather Touch',
    instruction: 'Draw the lightest lines you can - barely touching the screen',
    durationSeconds: 3
  },
  {
    id: 'normal',
    name: 'Natural Writing',
    instruction: 'Draw normally, like you would write or sketch naturally',
    durationSeconds: 3
  },
  {
    id: 'heavy',
    name: 'Heavy Shading',
    instruction: 'Make broad, bold strokes with heavy pressure and tilt',
    durationSeconds: 4
  }
];
