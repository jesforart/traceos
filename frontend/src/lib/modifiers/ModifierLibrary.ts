/**
 * Week 3: Design Variation Engine - Modifier Library
 *
 * Built-in modifiers for common design transformations.
 */

import type { ModifierDefinition } from './types';

/**
 * Built-in Modifier Library
 */
export class ModifierLibrary {
  private modifiers: Map<string, ModifierDefinition> = new Map();

  constructor() {
    this.registerBuiltInModifiers();
  }

  /**
   * Register all built-in modifiers
   */
  private registerBuiltInModifiers() {
    // Color modifiers
    this.register({
      modifier_id: 'saturate',
      name: 'Saturate',
      description: 'Increase color saturation',
      category: 'color',
      applicable_node_types: [],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'multiplicative',
      priority: 5,
      parameters: [
        {
          param_id: 'factor',
          name: 'Saturation Factor',
          type: 'number',
          default_value: 1.2,
          min_value: 1.0,
          max_value: 2.0,
          ui_control: 'slider',
          step: 0.1
        }
      ]
    });

    // Typography modifiers
    this.register({
      modifier_id: 'scale_font',
      name: 'Scale Font Size',
      description: 'Multiply font size by a factor',
      category: 'typography',
      applicable_node_types: ['text', 'hero', 'cta'],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'multiplicative',
      priority: 5,
      parameters: [
        {
          param_id: 'fontSize',
          name: 'Scale Factor',
          type: 'number',
          default_value: 1.2,
          min_value: 0.8,
          max_value: 1.5,
          ui_control: 'slider',
          step: 0.1
        }
      ]
    });

    this.register({
      modifier_id: 'bold_text',
      name: 'Bold Text',
      description: 'Increase font weight',
      category: 'typography',
      applicable_node_types: ['text', 'hero', 'cta'],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'override',
      priority: 5,
      parameters: [
        {
          param_id: 'fontWeight',
          name: 'Font Weight',
          type: 'enum',
          default_value: 700,
          allowed_values: [400, 500, 600, 700, 800, 900],
          ui_control: 'select'
        }
      ]
    });

    // Spacing modifiers
    this.register({
      modifier_id: 'scale_padding',
      name: 'Scale Padding',
      description: 'Multiply padding by a factor',
      category: 'spacing',
      applicable_node_types: [],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'multiplicative',
      priority: 5,
      parameters: [
        {
          param_id: 'padding',
          name: 'Scale Factor',
          type: 'number',
          default_value: 1.4,
          min_value: 0.5,
          max_value: 2.0,
          ui_control: 'slider',
          step: 0.1
        }
      ]
    });

    this.register({
      modifier_id: 'add_margin',
      name: 'Add Margin',
      description: 'Add margin to element',
      category: 'spacing',
      applicable_node_types: [],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'additive',
      priority: 5,
      parameters: [
        {
          param_id: 'margin',
          name: 'Margin Amount (px)',
          type: 'number',
          default_value: 16,
          min_value: 0,
          max_value: 64,
          ui_control: 'slider',
          step: 4
        }
      ]
    });

    // Effects modifiers
    this.register({
      modifier_id: 'round_corners',
      name: 'Round Corners',
      description: 'Add border radius',
      category: 'effects',
      applicable_node_types: ['cta', 'shape'],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'override',
      priority: 5,
      parameters: [
        {
          param_id: 'borderRadius',
          name: 'Border Radius (px)',
          type: 'number',
          default_value: 8,
          min_value: 0,
          max_value: 32,
          ui_control: 'slider',
          step: 2
        }
      ]
    });

    this.register({
      modifier_id: 'adjust_opacity',
      name: 'Adjust Opacity',
      description: 'Change element opacity',
      category: 'effects',
      applicable_node_types: [],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'override',
      priority: 5,
      parameters: [
        {
          param_id: 'opacity',
          name: 'Opacity',
          type: 'number',
          default_value: 0.9,
          min_value: 0.1,
          max_value: 1.0,
          ui_control: 'slider',
          step: 0.1
        }
      ]
    });

    // Accessibility modifiers
    this.register({
      modifier_id: 'ensure_contrast',
      name: 'Ensure Contrast',
      description: 'Adjust colors to meet WCAG contrast requirements',
      category: 'accessibility',
      applicable_node_types: ['text', 'hero', 'cta'],
      applicable_zones: ['flexible', 'generative'],
      composition_type: 'constraint',
      priority: 10, // High priority
      parameters: [
        {
          param_id: 'min_contrast',
          name: 'Minimum Contrast Ratio',
          type: 'number',
          default_value: 4.5,
          min_value: 3.0,
          max_value: 7.0,
          ui_control: 'slider',
          step: 0.5
        }
      ]
    });

    console.log(`📚 Registered ${this.modifiers.size} built-in modifiers`);
  }

  /**
   * Register a modifier
   */
  register(modifier: ModifierDefinition) {
    this.modifiers.set(modifier.modifier_id, modifier);
  }

  /**
   * Get a modifier by ID
   */
  get(modifier_id: string): ModifierDefinition | undefined {
    return this.modifiers.get(modifier_id);
  }

  /**
   * Get all modifiers
   */
  getAll(): ModifierDefinition[] {
    return Array.from(this.modifiers.values());
  }

  /**
   * Get modifiers by category
   */
  getByCategory(category: string): ModifierDefinition[] {
    return this.getAll().filter((m) => m.category === category);
  }

  /**
   * Get modifiers applicable to a node type
   */
  getApplicableToNodeType(node_type: string): ModifierDefinition[] {
    return this.getAll().filter(
      (m) =>
        m.applicable_node_types.length === 0 ||
        m.applicable_node_types.includes(node_type)
    );
  }

  /**
   * Get modifiers applicable to a zone
   */
  getApplicableToZone(zone_type: 'rigid' | 'flexible' | 'generative'): ModifierDefinition[] {
    return this.getAll().filter((m) => m.applicable_zones.includes(zone_type));
  }
}

// Singleton instance
export const modifierLibrary = new ModifierLibrary();
