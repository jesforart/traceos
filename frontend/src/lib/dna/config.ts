/**
 * Week 5: Style DNA Encoding - Configuration
 *
 * Central configuration for the 3-tier DNA system.
 * Defines feature dimensions, thresholds, and performance settings.
 */

/**
 * Style DNA Configuration Object
 * Single source of truth for all DNA encoding parameters
 */
export const StyleDNAConfig = {
  // Feature dimensions for each DNA tier
  dimensions: {
    stroke: 30,
    image: 512,
    temporal: 32
  },

  // Performance settings
  performance: {
    hot_path_budget_ms: 16, // Real-time budget (60 FPS)
    cold_path_timeout_ms: 5000, // Background analysis timeout
    worker_pool_size: 2 // Number of Web Workers
  },

  // Bounds normalization (v1.2)
  normalization: {
    reference_width: 1920,
    reference_height: 1080,
    enabled: true
  },

  // Confidence score settings (v1.2)
  confidence: {
    min_strokes_for_high_confidence: 50,
    max_strokes_for_full_confidence: 200,
    session_age_decay_hours: 24
  },

  // Aesthetic regulation
  aesthetic: {
    pretty_score_threshold: 0.7,
    modes: {
      strict: { min_score: 0.8, reject_below: true },
      balanced: { min_score: 0.7, reject_below: false },
      creative: { min_score: 0.5, reject_below: false }
    }
  },

  // Temporal DNA settings
  temporal: {
    fatigue_window_minutes: 15,
    learning_decay_rate: 0.95,
    session_cooldown_minutes: 30
  },

  // UMAP visualization
  umap: {
    n_neighbors: 15,
    min_dist: 0.1,
    n_components: 3,
    metric: 'cosine' as const
  },

  // Storage settings
  storage: {
    mode: 'indexeddb' as 'indexeddb' | 'memory' | 'localstorage',
    archive_after_days: 30,
    max_sessions_in_memory: 100
  },

  // Distance calculation weights
  distance_weights: {
    stroke: 0.4,
    image: 0.3,
    temporal: 0.2,
    aesthetic: 0.1
  }
} as const;

/**
 * Feature Index Constants
 * Human-readable names for DNA feature dimensions
 */

export const STROKE_DNA_INDEX = {
  // Geometric features (0-9)
  MEAN_X: 0,
  MEAN_Y: 1,
  WIDTH: 2,
  HEIGHT: 3,
  ASPECT_RATIO: 4,
  AREA: 5,
  PERIMETER: 6,
  COMPACTNESS: 7,
  ELONGATION: 8,
  ORIENTATION: 9,

  // Statistical features (10-19)
  X_VARIANCE: 10,
  Y_VARIANCE: 11,
  X_SKEWNESS: 12,
  Y_SKEWNESS: 13,
  X_KURTOSIS: 14,
  Y_KURTOSIS: 15,
  POINT_DENSITY: 16,
  CURVATURE_MEAN: 17,
  CURVATURE_STD: 18,
  CORNER_COUNT: 19,

  // Dynamic features (20-29)
  AVG_VELOCITY: 20,
  MAX_VELOCITY: 21,
  AVG_ACCELERATION: 22,
  MAX_ACCELERATION: 23,
  PRESSURE_MEAN: 24,
  PRESSURE_STD: 25,
  TILT_MEAN: 26,
  TWIST_MEAN: 27,
  DURATION: 28,
  PAUSE_COUNT: 29
} as const;

export const IMAGE_DNA_INDEX = {
  // VGG19 Block 1 (0-63)
  VGG_BLOCK1_START: 0,
  VGG_BLOCK1_END: 63,

  // VGG19 Block 2 (64-127)
  VGG_BLOCK2_START: 64,
  VGG_BLOCK2_END: 127,

  // VGG19 Block 3 (128-255)
  VGG_BLOCK3_START: 128,
  VGG_BLOCK3_END: 255,

  // VGG19 Block 4 (256-383)
  VGG_BLOCK4_START: 256,
  VGG_BLOCK4_END: 383,

  // VGG19 Block 5 (384-511)
  VGG_BLOCK5_START: 384,
  VGG_BLOCK5_END: 511,

  // Semantic groupings
  LOW_LEVEL_FEATURES: { start: 0, end: 127 }, // Edges, textures
  MID_LEVEL_FEATURES: { start: 128, end: 255 }, // Patterns, shapes
  HIGH_LEVEL_FEATURES: { start: 256, end: 511 } // Complex structures
} as const;

export const TEMPORAL_DNA_INDEX = {
  // Learning metrics (0-9)
  SESSION_COUNT: 0,
  TOTAL_STROKES: 1,
  AVG_STROKE_LENGTH: 2,
  PREFERRED_VELOCITY: 3,
  PREFERRED_PRESSURE: 4,
  TOOL_DIVERSITY: 5,
  COLOR_PALETTE_SIZE: 6,
  COMPOSITION_BIAS: 7,
  REVISION_RATE: 8,
  COMPLETION_RATE: 9,

  // Fatigue indicators (10-19)
  CURRENT_FATIGUE_LEVEL: 10,
  STROKE_CONSISTENCY: 11,
  ERROR_FREQUENCY: 12,
  UNDO_RATE: 13,
  PAUSE_FREQUENCY: 14,
  VELOCITY_VARIANCE: 15,
  PRESSURE_STABILITY: 16,
  SESSION_DURATION: 17,
  BREAK_COUNT: 18,
  FOCUS_SCORE: 19,

  // Style evolution (20-29)
  STYLE_DRIFT_RATE: 20,
  EXPLORATION_SCORE: 21,
  REFINEMENT_SCORE: 22,
  EXPERIMENTATION_RATE: 23,
  COMFORT_ZONE_RADIUS: 24,
  NOVELTY_SEEKING: 25,
  PATTERN_REPETITION: 26,
  CREATIVE_BURST_COUNT: 27,
  DELIBERATE_PRACTICE_TIME: 28,
  FLOW_STATE_DURATION: 29,

  // Reserved for future (30-31)
  RESERVED_1: 30,
  RESERVED_2: 31
} as const;

/**
 * Type guards for configuration validation
 */
export function isValidDNADimension(tier: 'stroke' | 'image' | 'temporal', value: number): boolean {
  return value >= 0 && value < StyleDNAConfig.dimensions[tier];
}

export function isValidConfidenceScore(score: number): boolean {
  return score >= 0 && score <= 1;
}

export function isValidPrettyScore(score: number): boolean {
  return score >= 0 && score <= 1;
}
