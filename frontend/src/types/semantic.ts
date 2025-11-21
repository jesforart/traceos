import { Stroke } from './stroke';

/**
 * Semantic element - a labeled collection of strokes.
 */
export interface SemanticElement {
  /** Unique element identifier */
  id: string;

  /** Semantic label (e.g., "left_eyebrow", "nose") */
  label: string;

  /** IDs of strokes that make up this element */
  stroke_ids: string[];

  /** Bounding box of all strokes */
  bounding_box: {
    min_x: number;
    min_y: number;
    max_x: number;
    max_y: number;
  };

  /** Confidence if auto-detected (0.0-1.0) */
  confidence?: number;

  /** Whether this was auto-detected or manually tagged */
  auto_detected: boolean;

  /** Creation timestamp */
  created_at: number;
}

/**
 * Available semantic tags for face drawings.
 */
export const FACE_TAGS = [
  'left_eyebrow',
  'right_eyebrow',
  'left_eye',
  'right_eye',
  'nose',
  'mouth',
  'jaw',
  'left_ear',
  'right_ear',
  'hair',
  'outline',
  'other'
] as const;

export type FaceTag = typeof FACE_TAGS[number];

/**
 * Selection region for stroke selection.
 */
export interface SelectionRegion {
  type: 'lasso' | 'box' | 'individual';
  points: Array<{ x: number; y: number }>;
}
