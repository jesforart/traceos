/**
 * Week 3: Design Variation Engine - Modifier Applicator
 *
 * Applies typed transformations to semantic nodes.
 * Handles all 5 composition types with priority-based ordering.
 */

import type { SemanticNode, BaseSchema } from '../schema/types';
import type {
  ModifierDefinition,
  AppliedModifier,
  ModifierApplicationResult,
  ModifierCompositionChain,
  CompositionType
} from './types';

/**
 * Modifier Applicator - Core transformation engine
 */
export class ModifierApplicator {
  /**
   * Apply a single modifier to a node property
   */
  private applyComposition(
    original_value: any,
    modifier_value: any,
    composition_type: CompositionType,
    alpha: number = 0.5
  ): any {
    switch (composition_type) {
      case 'additive':
        // v_final = v_original + modifier
        if (typeof original_value === 'number' && typeof modifier_value === 'number') {
          return original_value + modifier_value;
        }
        return original_value;

      case 'multiplicative':
        // v_final = v_original * modifier
        if (typeof original_value === 'number' && typeof modifier_value === 'number') {
          return original_value * modifier_value;
        }
        return original_value;

      case 'override':
        // v_final = modifier
        return modifier_value;

      case 'blend':
        // v_final = lerp(v_original, modifier, alpha)
        if (typeof original_value === 'number' && typeof modifier_value === 'number') {
          return original_value * (1 - alpha) + modifier_value * alpha;
        }
        // Color blending
        if (typeof original_value === 'string' && typeof modifier_value === 'string') {
          return this.blendColors(original_value, modifier_value, alpha);
        }
        return original_value;

      case 'constraint':
        // v_final = clamp(v_original, min, max)
        if (typeof original_value === 'number' && typeof modifier_value === 'object') {
          const { min, max } = modifier_value as { min: number; max: number };
          return Math.max(min, Math.min(max, original_value));
        }
        return original_value;

      default:
        console.warn(`Unknown composition type: ${composition_type}`);
        return original_value;
    }
  }

  /**
   * Blend two colors (hex format)
   */
  private blendColors(color1: string, color2: string, alpha: number): string {
    const hex1 = color1.replace('#', '');
    const hex2 = color2.replace('#', '');

    const r1 = parseInt(hex1.substring(0, 2), 16);
    const g1 = parseInt(hex1.substring(2, 4), 16);
    const b1 = parseInt(hex1.substring(4, 6), 16);

    const r2 = parseInt(hex2.substring(0, 2), 16);
    const g2 = parseInt(hex2.substring(2, 4), 16);
    const b2 = parseInt(hex2.substring(4, 6), 16);

    const r = Math.round(r1 * (1 - alpha) + r2 * alpha);
    const g = Math.round(g1 * (1 - alpha) + g2 * alpha);
    const b = Math.round(b1 * (1 - alpha) + b2 * alpha);

    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }

  /**
   * Apply a single modifier to a schema
   */
  apply(
    schema: BaseSchema,
    modifier: ModifierDefinition,
    applied_modifier: AppliedModifier
  ): {
    schema: BaseSchema;
    results: ModifierApplicationResult[];
  } {
    const results: ModifierApplicationResult[] = [];
    const modified_schema = JSON.parse(JSON.stringify(schema)) as BaseSchema;

    // Apply to each target node
    for (const node_id of applied_modifier.target_node_ids) {
      const node = modified_schema.semantic_nodes.find((n) => n.node_id === node_id);

      if (!node) {
        results.push({
          success: false,
          original_value: null,
          modified_value: null,
          modifier_id: modifier.modifier_id,
          composition_used: modifier.composition_type,
          errors: [`Node not found: ${node_id}`]
        });
        continue;
      }

      // Apply to each target property
      for (const property of applied_modifier.target_properties) {
        const original_value = node.properties[property];
        const modifier_value = applied_modifier.parameter_values[property];

        if (modifier_value === undefined) {
          results.push({
            success: false,
            original_value,
            modified_value: null,
            modifier_id: modifier.modifier_id,
            composition_used: modifier.composition_type,
            warnings: [`No modifier value for property: ${property}`]
          });
          continue;
        }

        // Apply composition
        const modified_value = this.applyComposition(
          original_value,
          modifier_value,
          modifier.composition_type,
          applied_modifier.parameter_values['alpha'] || 0.5
        );

        // Update node
        node.properties[property] = modified_value;

        results.push({
          success: true,
          original_value,
          modified_value,
          modifier_id: modifier.modifier_id,
          composition_used: modifier.composition_type
        });
      }
    }

    return { schema: modified_schema, results };
  }

  /**
   * Apply multiple modifiers in priority order
   */
  applyChain(
    schema: BaseSchema,
    modifiers: Array<{
      definition: ModifierDefinition;
      applied: AppliedModifier;
    }>
  ): {
    schema: BaseSchema;
    chains: ModifierCompositionChain[];
  } {
    // Sort by priority (higher priority applies later)
    const sorted = modifiers.sort(
      (a, b) => a.definition.priority - b.definition.priority
    );

    const chains: Map<string, ModifierCompositionChain> = new Map();
    let current_schema = JSON.parse(JSON.stringify(schema)) as BaseSchema;

    // Apply each modifier in order
    for (const { definition, applied } of sorted) {
      const { schema: modified_schema } = this.apply(
        current_schema,
        definition,
        applied
      );

      // Track composition chain
      for (const node_id of applied.target_node_ids) {
        for (const property of applied.target_properties) {
          const chain_key = `${node_id}:${property}`;

          if (!chains.has(chain_key)) {
            const original_node = schema.semantic_nodes.find(
              (n) => n.node_id === node_id
            );
            chains.set(chain_key, {
              node_id,
              property,
              original_value: original_node?.properties[property],
              steps: [],
              final_value: null
            });
          }

          const chain = chains.get(chain_key)!;
          const current_node = current_schema.semantic_nodes.find(
            (n) => n.node_id === node_id
          );
          const modified_node = modified_schema.semantic_nodes.find(
            (n) => n.node_id === node_id
          );

          chain.steps.push({
            modifier_id: definition.modifier_id,
            composition_type: definition.composition_type,
            input_value: current_node?.properties[property],
            output_value: modified_node?.properties[property],
            priority: definition.priority
          });

          chain.final_value = modified_node?.properties[property];
        }
      }

      current_schema = modified_schema;
    }

    return {
      schema: current_schema,
      chains: Array.from(chains.values())
    };
  }

  /**
   * Check if a modifier can be applied to a node
   */
  canApply(
    node: SemanticNode,
    modifier: ModifierDefinition
  ): { can_apply: boolean; reason?: string } {
    // Check node type compatibility
    if (
      modifier.applicable_node_types.length > 0 &&
      !modifier.applicable_node_types.includes(node.node_type)
    ) {
      return {
        can_apply: false,
        reason: `Modifier not applicable to node type: ${node.node_type}`
      };
    }

    return { can_apply: true };
  }
}

// Singleton instance
export const modifierApplicator = new ModifierApplicator();
