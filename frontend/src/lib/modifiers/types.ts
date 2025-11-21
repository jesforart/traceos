/**
 * Week 3: Design Variation Engine - Modifier Type System
 *
 * Typed transformations for design variations.
 * Based on WEEK3_DESIGN_VARIATION_ENGINE_v1.2_FINAL.md
 */

/**
 * Modifier Composition Types
 * How modifiers combine when applied together
 */
export type CompositionType =
  | 'additive'        // v_final = v_original + modifier
  | 'multiplicative'  // v_final = v_original * modifier
  | 'override'        // v_final = modifier
  | 'blend'           // v_final = lerp(v_original, modifier, alpha)
  | 'constraint';     // v_final = clamp(v_original, min, max)

/**
 * Modifier Category - Organizational grouping
 */
export type ModifierCategory =
  | 'color'
  | 'typography'
  | 'spacing'
  | 'layout'
  | 'effects'
  | 'animation'
  | 'accessibility';

/**
 * Base Modifier Definition
 */
export interface ModifierDefinition {
  modifier_id: string;
  name: string;
  description: string;
  category: ModifierCategory;

  // Application rules
  applicable_node_types: string[];
  applicable_zones: ('rigid' | 'flexible' | 'generative')[];

  // Composition
  composition_type: CompositionType;
  priority: number; // Higher priority applies later

  // Parameters
  parameters: ModifierParameter[];

  // Examples
  examples?: {
    input: any;
    output: any;
    description: string;
  }[];
}

/**
 * Modifier Parameter - Configurable values
 */
export interface ModifierParameter {
  param_id: string;
  name: string;
  type: 'number' | 'string' | 'boolean' | 'color' | 'enum';

  // Validation
  default_value: any;
  min_value?: number;
  max_value?: number;
  allowed_values?: any[];

  // UI hints
  ui_control: 'slider' | 'input' | 'select' | 'color-picker' | 'toggle';
  step?: number;
}

/**
 * Applied Modifier - Instance with concrete values
 */
export interface AppliedModifier {
  application_id: string;
  modifier_id: string;

  // Targeting
  target_node_ids: string[];
  target_properties: string[];

  // Parameter values
  parameter_values: Record<string, any>;

  // Metadata
  applied_at: number;
  applied_by?: string;
}

/**
 * Modifier Application Result
 */
export interface ModifierApplicationResult {
  success: boolean;
  original_value: any;
  modified_value: any;
  modifier_id: string;
  composition_used: CompositionType;
  warnings?: string[];
  errors?: string[];
}

/**
 * Modifier Composition Chain
 * Tracks how multiple modifiers combine
 */
export interface ModifierCompositionChain {
  node_id: string;
  property: string;
  original_value: any;

  steps: {
    modifier_id: string;
    composition_type: CompositionType;
    input_value: any;
    output_value: any;
    priority: number;
  }[];

  final_value: any;
}

/**
 * Built-in Modifier Library
 */
export const MODIFIER_CATEGORIES = {
  color: {
    saturate: 'Increase color saturation',
    desaturate: 'Decrease color saturation',
    shift_hue: 'Rotate hue value',
    lighten: 'Increase lightness',
    darken: 'Decrease lightness',
    increase_contrast: 'Boost contrast ratio'
  },
  typography: {
    scale_font: 'Scale font size',
    adjust_weight: 'Adjust font weight',
    adjust_leading: 'Adjust line height',
    adjust_tracking: 'Adjust letter spacing'
  },
  spacing: {
    scale_padding: 'Scale padding',
    scale_margin: 'Scale margin',
    adjust_gap: 'Adjust grid/flex gap'
  },
  layout: {
    align: 'Change alignment',
    distribute: 'Distribute spacing',
    resize: 'Resize element',
    reposition: 'Change position'
  },
  effects: {
    blur: 'Apply blur effect',
    shadow: 'Apply shadow',
    opacity: 'Adjust opacity',
    border_radius: 'Adjust corner radius'
  },
  animation: {
    fade_in: 'Fade in animation',
    slide_in: 'Slide in animation',
    scale_in: 'Scale in animation'
  },
  accessibility: {
    ensure_contrast: 'Ensure WCAG contrast',
    ensure_touch_target: 'Ensure minimum touch size',
    add_aria: 'Add ARIA attributes'
  }
} as const;
