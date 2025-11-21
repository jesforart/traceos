/**
 * Week 5: Style DNA Encoding - Type Definitions
 *
 * Core types for the 3-tier DNA system.
 * Defines DNA vectors, sessions, and encoding interfaces.
 */

import type { ArtistContext } from './ArtistContextManager';

// Re-export for convenience
export type { ArtistContext } from './ArtistContextManager';

/**
 * DNA Tier - Three levels of encoding
 */
export type DNATier = 'stroke' | 'image' | 'temporal';

/**
 * Stroke DNA - 30-dimensional feature vector
 * Hot path encoding (<16ms)
 */
export interface StrokeDNA {
  dna_id: string;
  stroke_id: string;
  session_id: string;

  // Feature vector (30 dimensions)
  features: Float32Array; // Length 30

  // Normalized bounds (v1.2)
  normalized_bounds?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };

  // Metadata
  tool: string;
  color: string;
  timestamp: number;
  encoding_time_ms: number;
}

/**
 * Image DNA - 512-dimensional VGG19 embedding
 * Cold path encoding (background)
 */
export interface ImageDNA {
  dna_id: string;
  session_id: string;
  snapshot_id: string;

  // Feature vector (512 dimensions from VGG19)
  features: Float32Array; // Length 512

  // Visual analysis
  dominant_colors: string[];
  texture_features: {
    complexity: number;
    contrast: number;
    energy: number;
  };

  // Metadata
  width: number;
  height: number;
  timestamp: number;
  encoding_time_ms: number;
}

/**
 * Temporal DNA - 32-dimensional learning/fatigue vector
 * Updated periodically
 */
export interface TemporalDNA {
  dna_id: string;
  session_id: string;
  artist_id?: string;

  // Feature vector (32 dimensions)
  features: Float32Array; // Length 32

  // Learning metrics
  learning_phase: 'exploration' | 'refinement' | 'mastery';
  skill_progression: number; // 0-1

  // Fatigue indicators
  fatigue_level: number; // 0-1
  focus_score: number; // 0-1
  flow_state: boolean;

  // Metadata
  total_sessions: number;
  total_strokes: number;
  timestamp: number;
  encoding_time_ms: number;
}

/**
 * Composite DNA - All three tiers combined
 */
export interface CompositeDNA {
  composite_id: string;
  session_id: string;

  stroke_dna: StrokeDNA[];
  image_dna: ImageDNA | null;
  temporal_dna: TemporalDNA;

  // Confidence score (v1.2)
  confidence_score: number; // 0-1

  created_at: number;
  updated_at: number;
}

/**
 * DNA Session - Collection of all DNA for a work session
 */
export interface DNASession {
  session_id: string;
  artist_id?: string;

  // DNA collections
  stroke_dnas: StrokeDNA[];
  image_dnas: ImageDNA[];
  temporal_dnas: TemporalDNA[];

  // Session metadata
  session_name?: string;
  started_at: number;
  ended_at?: number;
  total_strokes: number;

  // Confidence score (v1.2)
  confidence_score: number;

  // Artist context
  context: ArtistContext;

  // Pretty score
  aesthetic_score?: number;
  aesthetic_mode?: 'strict' | 'balanced' | 'creative';
}

/**
 * DNA Encoder Interface
 * Defines contract for DNA encoding implementations
 */
export interface DNAEncoder<T> {
  encode(input: any, context?: ArtistContext): Promise<T>;
  encodeSync(input: any, context?: ArtistContext): T;
  getDimension(): number;
  getTier(): DNATier;
}

/**
 * DNA Distance Calculator Interface
 */
export interface DNADistanceCalculator {
  calculateDistance(dna_a: Float32Array, dna_b: Float32Array): number;
  calculateBatchDistances(query: Float32Array, targets: Float32Array[]): number[];
}

/**
 * DNA Blending Interface
 */
export interface DNABlender<T> {
  blend(dna_a: T, dna_b: T, alpha: number): T;
  blendMultiple(dnas: T[], weights: number[]): T;
}

/**
 * Pretty Score - Aesthetic regulation
 */
export interface PrettyScore {
  score_id: string;
  session_id: string;

  // Overall aesthetic score
  overall_score: number; // 0-1

  // Component scores
  color_harmony: number;
  composition_balance: number;
  visual_complexity: number;
  style_consistency: number;

  // Regulation
  mode: 'strict' | 'balanced' | 'creative';
  passes_threshold: boolean;
  recommendation?: string;

  timestamp: number;
}

/**
 * Confidence Score - Session representativeness (v1.2)
 */
export interface ConfidenceScore {
  confidence_id: string;
  session_id: string;

  // Overall confidence
  overall_confidence: number; // 0-1

  // Component confidence
  stroke_count_confidence: number; // Based on # of strokes
  session_age_confidence: number; // Decay over time
  completeness_confidence: number; // Has all DNA tiers

  // Metadata
  total_strokes: number;
  session_age_hours: number;
  computed_at: number;
}

/**
 * DNA Storage Record
 */
export interface DNAStorageRecord {
  record_id: string;
  session_id: string;
  tier: DNATier;

  // Serialized DNA data
  data: string; // JSON serialized

  // Storage metadata
  stored_at: number;
  size_bytes: number;
  archived: boolean;
}

/**
 * UMAP Projection - 3D visualization
 */
export interface UMAPProjection {
  projection_id: string;

  // Original high-dimensional points
  source_dnas: string[]; // DNA IDs

  // 3D projected coordinates
  coordinates: Array<{ x: number; y: number; z: number }>;

  // UMAP parameters
  n_neighbors: number;
  min_dist: number;
  metric: string;

  // Metadata
  computed_at: number;
  computation_time_ms: number;
}

/**
 * Bounds Normalization Result (v1.2)
 */
export interface NormalizedBounds {
  original: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  normalized: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  scale_factor: number;
  reference_dimensions: {
    width: number;
    height: number;
  };
}
