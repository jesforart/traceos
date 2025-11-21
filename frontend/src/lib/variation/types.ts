/**
 * Week 3: Design Variation Engine - Variation Type System
 *
 * Types for generating, tracking, and validating design variations.
 * Based on WEEK3_DESIGN_VARIATION_ENGINE_v1.2_FINAL.md
 */

import type { BaseSchema } from '../schema/types';
import type { AppliedModifier } from '../modifiers/types';

/**
 * Generated Variation - A specific design variant
 */
export interface GeneratedVariation {
  variation_id: string;
  parent_schema_id: string;
  created_at: number;

  // The actual variant schema
  schema: BaseSchema;

  // What changed
  applied_modifiers: AppliedModifier[];

  // Distance from parent
  style_distance: number;

  // Validation results
  safety_score: SafetyScore;

  // Drift tracking
  semantic_drift: number;
  drift_category: 'minor' | 'moderate' | 'significant' | 'severe';

  // Metadata
  generation_method: 'random' | 'guided' | 'ai' | 'manual';
  tags: string[];
}

/**
 * Safety Score - Multi-level validation
 * "Lighthouse for Creative AI"
 */
export interface SafetyScore {
  overall_score: number; // 0-100

  // Component scores
  brand_safety: {
    score: number;
    violations: BrandViolation[];
  };

  accessibility_safety: {
    score: number;
    wcag_level: 'AA' | 'AAA' | 'fail';
    violations: AccessibilityViolation[];
  };

  structural_safety: {
    score: number;
    issues: StructuralIssue[];
  };

  quality_safety: {
    score: number;
    warnings: QualityWarning[];
  };

  // Recommendation
  recommendation: 'safe' | 'review' | 'unsafe';
}

/**
 * Brand Violation - Brand guideline breaches
 */
export interface BrandViolation {
  severity: 'error' | 'warning';
  type: 'color' | 'typography' | 'spacing' | 'logo' | 'tone';
  message: string;
  node_id: string;
  expected?: any;
  actual?: any;
}

/**
 * Accessibility Violation - WCAG failures
 */
export interface AccessibilityViolation {
  severity: 'error' | 'warning';
  wcag_criterion: string;
  level: 'A' | 'AA' | 'AAA';
  message: string;
  node_id: string;

  // Specific checks
  contrast_ratio?: number;
  min_contrast_required?: number;
  touch_target_size?: { width: number; height: number };
  min_touch_target?: { width: number; height: number };
}

/**
 * Structural Issue - Design integrity problems
 */
export interface StructuralIssue {
  severity: 'error' | 'warning';
  type: 'overlap' | 'overflow' | 'missing' | 'orphan' | 'hierarchy';
  message: string;
  node_ids: string[];
}

/**
 * Quality Warning - Non-critical issues
 */
export interface QualityWarning {
  type: 'alignment' | 'spacing' | 'consistency' | 'readability';
  message: string;
  node_id: string;
  suggestion?: string;
}

/**
 * Style Distance - Measure of variation magnitude
 */
export interface StyleDistance {
  overall_distance: number; // 0-1

  // Component distances
  color_distance: number;
  typography_distance: number;
  spacing_distance: number;
  layout_distance: number;

  // Distance band classification
  band: 'micro' | 'minor' | 'moderate' | 'major' | 'extreme';
}

/**
 * Distance Band Definitions
 * From the spec's "distance bands" concept
 */
export const DISTANCE_BANDS = {
  micro: { min: 0, max: 0.1, label: 'Micro variation' },
  minor: { min: 0.1, max: 0.25, label: 'Minor variation' },
  moderate: { min: 0.25, max: 0.5, label: 'Moderate variation' },
  major: { min: 0.5, max: 0.75, label: 'Major variation' },
  extreme: { min: 0.75, max: 1.0, label: 'Extreme variation' }
} as const;

/**
 * Semantic Drift - Measure of meaning change
 * "Evolutionary design lineage protocol"
 */
export interface SemanticDrift {
  drift_value: number; // 0-1

  // What drifted
  changed_nodes: {
    node_id: string;
    property: string;
    original_value: any;
    new_value: any;
    semantic_impact: number;
  }[];

  // Drift categorization
  category: 'minor' | 'moderate' | 'significant' | 'severe';

  // Should branch?
  should_branch: boolean;
  branch_reason?: string;
}

/**
 * Drift Threshold Configuration
 */
export const DRIFT_THRESHOLDS = {
  minor: 0.15,        // < 15% drift - safe
  moderate: 0.30,     // 15-30% drift - monitor
  significant: 0.50,  // 30-50% drift - consider branching
  severe: 0.50        // > 50% drift - auto-branch
} as const;

/**
 * Variation Generation Request
 */
export interface VariationRequest {
  base_schema_id: string;

  // Generation parameters
  count: number;
  distance_range: {
    min: number;
    max: number;
  };

  // Targeting
  target_zones?: string[];
  target_properties?: string[];

  // Constraints
  maintain_brand_safety?: boolean;
  maintain_accessibility?: boolean;
  min_safety_score?: number;

  // Method
  method: 'random' | 'guided' | 'ai';

  // AI guidance (if method === 'ai')
  ai_intent?: string;
}

/**
 * Variation Generation Result
 */
export interface VariationGenerationResult {
  success: boolean;
  variations: GeneratedVariation[];

  // Statistics
  total_generated: number;
  total_safe: number;
  total_rejected: number;

  // Performance
  generation_time_ms: number;

  // Errors
  errors?: string[];
}
