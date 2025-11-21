/**
 * Week 3: Design Variation Engine - Variation Generator
 *
 * Generates design variations using modifiers and variation rules.
 * Respects zones, constraints, and distance bounds.
 */

import type { BaseSchema, SemanticNode, VariationZone } from '../schema/types';
import type { ModifierDefinition, AppliedModifier } from '../modifiers/types';
import type {
  VariationRequest,
  VariationGenerationResult,
  GeneratedVariation
} from './types';
import { modifierApplicator } from '../modifiers/ModifierApplicator';
import { styleDistanceCalculator } from './StyleDistanceCalculator';
import { styleSafetyLens } from './StyleSafetyLens';
import { ulid } from '../../utils/ulid';

/**
 * Variation Generator - Core generation engine
 */
export class VariationGenerator {
  /**
   * Generate variations from a base schema
   */
  async generate(
    base_schema: BaseSchema,
    available_modifiers: ModifierDefinition[],
    request: VariationRequest
  ): Promise<VariationGenerationResult> {
    const start_time = performance.now();
    const variations: GeneratedVariation[] = [];
    const errors: string[] = [];

    let total_generated = 0;
    let total_rejected = 0;

    for (let i = 0; i < request.count; i++) {
      try {
        const variation = await this.generateSingle(
          base_schema,
          available_modifiers,
          request
        );

        if (variation) {
          // Check safety if required
          if (request.min_safety_score !== undefined) {
            if (variation.safety_score.overall_score < request.min_safety_score) {
              total_rejected++;
              continue;
            }
          }

          variations.push(variation);
          total_generated++;
        } else {
          total_rejected++;
        }
      } catch (error) {
        errors.push(`Generation ${i} failed: ${error}`);
        total_rejected++;
      }
    }

    const generation_time_ms = performance.now() - start_time;

    return {
      success: variations.length > 0,
      variations,
      total_generated,
      total_safe: variations.filter(
        (v) => v.safety_score.recommendation === 'safe'
      ).length,
      total_rejected,
      generation_time_ms,
      errors: errors.length > 0 ? errors : undefined
    };
  }

  /**
   * Generate a single variation
   */
  private async generateSingle(
    base_schema: BaseSchema,
    available_modifiers: ModifierDefinition[],
    request: VariationRequest
  ): Promise<GeneratedVariation | null> {
    // 1. Select modifiers to apply
    const selected_modifiers = this.selectModifiers(
      base_schema,
      available_modifiers,
      request
    );

    if (selected_modifiers.length === 0) {
      return null;
    }

    // 2. Create applied modifier instances
    const applied_modifiers = this.createAppliedModifiers(
      base_schema,
      selected_modifiers,
      request
    );

    // 3. Apply modifiers to schema
    const { schema: modified_schema } = modifierApplicator.applyChain(
      base_schema,
      selected_modifiers.map((m, i) => ({
        definition: m,
        applied: applied_modifiers[i]
      }))
    );

    // 4. Calculate style distance
    const style_distance = styleDistanceCalculator.calculate(
      base_schema,
      modified_schema
    );

    // Check if within requested distance range
    if (
      style_distance.overall_distance < request.distance_range.min ||
      style_distance.overall_distance > request.distance_range.max
    ) {
      return null;
    }

    // 5. Validate with Safety Lens
    const safety_score = await styleSafetyLens.validate(
      modified_schema,
      base_schema.context
    );

    // 6. Calculate semantic drift
    const semantic_drift = this.calculateSemanticDrift(base_schema, modified_schema);

    // 7. Create variation
    const variation: GeneratedVariation = {
      variation_id: ulid(),
      parent_schema_id: base_schema.schema_id,
      created_at: Date.now(),
      schema: modified_schema,
      applied_modifiers,
      style_distance: style_distance.overall_distance,
      safety_score,
      semantic_drift: semantic_drift.drift_value,
      drift_category: semantic_drift.category,
      generation_method: request.method,
      tags: []
    };

    return variation;
  }

  /**
   * Select which modifiers to apply
   */
  private selectModifiers(
    base_schema: BaseSchema,
    available_modifiers: ModifierDefinition[],
    request: VariationRequest
  ): ModifierDefinition[] {
    // Filter modifiers based on target zones
    let candidates = available_modifiers;

    if (request.target_zones) {
      candidates = candidates.filter((m) =>
        request.target_zones!.some((zone) => m.applicable_zones.includes(zone as any))
      );
    }

    if (candidates.length === 0) {
      return [];
    }

    // Random selection
    const count = Math.floor(Math.random() * 3) + 1; // 1-3 modifiers
    const selected: ModifierDefinition[] = [];

    for (let i = 0; i < count && candidates.length > 0; i++) {
      const index = Math.floor(Math.random() * candidates.length);
      selected.push(candidates[index]);
      candidates.splice(index, 1);
    }

    return selected;
  }

  /**
   * Create applied modifier instances with random parameter values
   */
  private createAppliedModifiers(
    base_schema: BaseSchema,
    modifiers: ModifierDefinition[],
    request: VariationRequest
  ): AppliedModifier[] {
    return modifiers.map((modifier) => {
      // Select random nodes to apply to
      let target_nodes = base_schema.semantic_nodes;

      // Filter by target zones if specified
      if (request.target_zones) {
        target_nodes = target_nodes.filter((n) =>
          request.target_zones!.includes(n.zone_id)
        );
      }

      // Filter by modifier applicability
      target_nodes = target_nodes.filter(
        (n) =>
          modifier.applicable_node_types.length === 0 ||
          modifier.applicable_node_types.includes(n.node_type)
      );

      if (target_nodes.length === 0) {
        target_nodes = base_schema.semantic_nodes.slice(0, 1);
      }

      // Random selection of 1-2 nodes
      const node_count = Math.min(
        Math.floor(Math.random() * 2) + 1,
        target_nodes.length
      );
      const target_node_ids: string[] = [];
      for (let i = 0; i < node_count; i++) {
        const index = Math.floor(Math.random() * target_nodes.length);
        target_node_ids.push(target_nodes[index].node_id);
      }

      // Generate random parameter values
      const parameter_values: Record<string, any> = {};
      for (const param of modifier.parameters) {
        if (param.type === 'number') {
          const min = param.min_value ?? 0;
          const max = param.max_value ?? 1;
          parameter_values[param.param_id] =
            Math.random() * (max - min) + min;
        } else if (param.type === 'boolean') {
          parameter_values[param.param_id] = Math.random() > 0.5;
        } else if (param.type === 'enum' && param.allowed_values) {
          const index = Math.floor(
            Math.random() * param.allowed_values.length
          );
          parameter_values[param.param_id] =
            param.allowed_values[index];
        } else {
          parameter_values[param.param_id] = param.default_value;
        }
      }

      // Select target properties based on request
      let target_properties = request.target_properties || [
        'color',
        'fontSize',
        'padding'
      ];

      return {
        application_id: ulid(),
        modifier_id: modifier.modifier_id,
        target_node_ids,
        target_properties,
        parameter_values,
        applied_at: Date.now()
      };
    });
  }

  /**
   * Calculate semantic drift between schemas
   */
  private calculateSemanticDrift(
    original: BaseSchema,
    modified: BaseSchema
  ): { drift_value: number; category: 'minor' | 'moderate' | 'significant' | 'severe' } {
    let total_drift = 0;
    let property_count = 0;

    for (const orig_node of original.semantic_nodes) {
      const mod_node = modified.semantic_nodes.find(
        (n) => n.node_id === orig_node.node_id
      );

      if (!mod_node) continue;

      // Compare each property
      for (const [key, orig_value] of Object.entries(orig_node.properties)) {
        const mod_value = mod_node.properties[key];

        if (orig_value === mod_value) continue;

        // Calculate property-level drift
        if (typeof orig_value === 'number' && typeof mod_value === 'number') {
          const diff = Math.abs(mod_value - orig_value);
          const avg = (Math.abs(orig_value) + Math.abs(mod_value)) / 2;
          const relative_diff = avg > 0 ? diff / avg : 0;
          total_drift += Math.min(relative_diff, 1);
        } else {
          // Non-numeric properties count as full drift if changed
          total_drift += 1;
        }

        property_count++;
      }
    }

    const drift_value =
      property_count > 0 ? total_drift / property_count : 0;

    // Categorize
    let category: 'minor' | 'moderate' | 'significant' | 'severe';
    if (drift_value < 0.15) {
      category = 'minor';
    } else if (drift_value < 0.30) {
      category = 'moderate';
    } else if (drift_value < 0.50) {
      category = 'significant';
    } else {
      category = 'severe';
    }

    return { drift_value, category };
  }
}

// Singleton instance
export const variationGenerator = new VariationGenerator();
