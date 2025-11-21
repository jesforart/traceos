/**
 * Week 3: Design Variation Engine - Schema Type System
 *
 * Foundation types for semantic design schemas, nodes, zones, and variations.
 * Based on WEEK3_DESIGN_VARIATION_ENGINE_v1.2_FINAL.md
 */

/**
 * Semantic Node - Concrete design element with meaning
 * Like Pixar's USD but for 2D creative intelligence
 */
export interface SemanticNode {
  node_id: string;
  node_type: 'hero' | 'nav' | 'cta' | 'content' | 'background' | 'text' | 'image' | 'shape';
  semantic_label: string;

  // Concrete geometry
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };

  // Visual properties
  properties: {
    color?: string;
    fontSize?: number;
    fontFamily?: string;
    fontWeight?: number;
    backgroundColor?: string;
    borderRadius?: number;
    padding?: number;
    margin?: number;
    opacity?: number;
    zIndex?: number;
    [key: string]: any; // Extensible
  };

  // Relationships
  parent_id?: string;
  children_ids: string[];

  // Zone assignment
  zone_id: string;
}

/**
 * Variation Zone - Control theory for transformations
 * Defines how much a node can change
 */
export type ZoneType = 'rigid' | 'flexible' | 'generative';

export interface VariationZone {
  zone_id: string;
  zone_type: ZoneType;
  description: string;

  // Rigid: No changes allowed
  // Flexible: Bounded changes
  // Generative: Unbounded exploration

  constraints: ZoneConstraint[];
}

export interface ZoneConstraint {
  property: string;

  // For rigid zones
  locked?: true;

  // For flexible zones
  min_value?: number;
  max_value?: number;
  allowed_values?: any[];

  // Distance bands (from spec)
  distance_band?: {
    min_distance: number;
    max_distance: number;
  };
}

/**
 * Aesthetic Profile - Style DNA
 */
export interface AestheticProfile {
  style_embedding_id: string;
  design_language: 'minimal' | 'editorial' | 'playful' | 'corporate' | 'artistic';
  color_harmony: 'monochromatic' | 'analogous' | 'complementary' | 'triadic' | 'custom';
  texture_density: number; // 0-1

  // v1.2: Extended aesthetic properties for advanced features
  color_palette: {
    primary: string;
    secondary: string;
    accents: string[];
    neutrals: string[];
    harmony_rule: string;
  };
  typography: {
    font_family_primary: string;
    font_family_secondary: string;
    heading_size: number;
    body_size: number;
    line_height: number;
    letter_spacing: number;
  };
  spacing_system: {
    base_unit: number;
    scale_factor: number;
  };
  visual_language: {
    border_radius: number;
    border_width: number;
    shadow_intensity: number;
  };
}

/**
 * Design Context - Brand and technical constraints
 */
export interface DesignContext {
  brand_id?: string;
  target_audience?: string[];
  accessibility_level: 'AA' | 'AAA';
  device_targets: ('desktop' | 'tablet' | 'mobile')[];
  color_mode: 'light' | 'dark' | 'auto';
}

/**
 * Evaluation Criteria - How to judge quality
 */
export interface EvaluationCriteria {
  metrics: {
    accessibility_score?: number;
    brand_alignment?: number;
    visual_hierarchy?: number;
    readability?: number;
  };

  required_validations: ('wcag' | 'brand' | 'structure')[];
}

/**
 * Base Schema - Complete design definition
 * The core creative object
 */
export interface BaseSchema {
  // Identity
  schema_id: string;
  version: string;
  created_at: number;
  updated_at: number;

  // Intent
  intent: string;

  // Structure
  semantic_nodes: SemanticNode[];
  variation_zones: VariationZone[];

  // Style
  aesthetic_profile: AestheticProfile;

  // Context
  context: DesignContext;

  // Validation
  evaluation: EvaluationCriteria;

  // Constraints
  constraints: GlobalConstraint[];

  // Variation rules
  variation_rules: VariationRule[];

  // Lineage (for v1.1)
  parent_schemas?: string[];
  mutation_type?: string;
  blend_ratio?: number;
}

/**
 * Global Constraint - Schema-wide rules
 */
export interface GlobalConstraint {
  constraint_id: string;
  type: 'accessibility' | 'brand' | 'performance' | 'layout' | 'custom';
  rule: string;
  priority: number; // 1-10
  required: boolean;
}

/**
 * Variation Rule - How to generate variations
 */
export interface VariationRule {
  rule_id: string;
  target_zone: string;
  target_properties: string[];

  // Generation strategy
  strategy: 'random' | 'guided' | 'ai' | 'template';

  // Bounds
  variation_distance: {
    min: number;
    max: number;
  };

  // Conditions
  conditions?: {
    property: string;
    operator: '==' | '!=' | '>' | '<' | '>=' | '<=';
    value: any;
  }[];
}

/**
 * Schema Metadata - For storage and retrieval
 */
export interface SchemaMetadata {
  schema_id: string;
  name: string;
  description: string;
  tags: string[];
  author?: string;
  thumbnail?: string;
  stats: {
    variation_count: number;
    last_variation: number;
  };
}
