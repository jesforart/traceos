/**
 * Week 3 v1.2: Cross-Schema Mutation - Mutator
 *
 * Implements genetic operators for design evolution.
 * Biological evolution metaphor for creative exploration.
 */

import type {
  MutationResult,
  MutationOperator,
  MutationPoint,
  CrossoverConfig,
  TransplantConfig,
  FusionConfig
} from './types';
import type { BaseSchema, SemanticNode } from '../schema/types';
import { ulid } from '../../utils/ulid';

/**
 * Schema Mutator - Genetic operators for design
 */
export class SchemaMutator {
  /**
   * Crossover - Combine two parent schemas
   */
  crossover(
    parent_a: BaseSchema,
    parent_b: BaseSchema,
    config: CrossoverConfig = { crossover_type: 'single_point', crossover_rate: 0.5 }
  ): MutationResult {
    const offspring = JSON.parse(JSON.stringify(parent_a)) as BaseSchema;
    offspring.schema_id = ulid();
    const mutation_points: MutationPoint[] = [];

    switch (config.crossover_type) {
      case 'single_point':
        // Split at midpoint
        const split_index = Math.floor(parent_a.semantic_nodes.length / 2);

        for (let i = split_index; i < offspring.semantic_nodes.length; i++) {
          if (parent_b.semantic_nodes[i]) {
            const original_id = offspring.semantic_nodes[i].node_id;
            offspring.semantic_nodes[i] = JSON.parse(
              JSON.stringify(parent_b.semantic_nodes[i])
            );

            mutation_points.push({
              point_id: ulid(),
              node_id: original_id,
              source_schema_id: parent_b.schema_id,
              description: `Inherited from parent B at crossover point ${split_index}`
            });
          }
        }
        break;

      case 'two_point':
        // Split at two points
        const point1 = Math.floor(parent_a.semantic_nodes.length / 3);
        const point2 = Math.floor((2 * parent_a.semantic_nodes.length) / 3);

        for (let i = point1; i < point2; i++) {
          if (parent_b.semantic_nodes[i]) {
            const original_id = offspring.semantic_nodes[i].node_id;
            offspring.semantic_nodes[i] = JSON.parse(
              JSON.stringify(parent_b.semantic_nodes[i])
            );

            mutation_points.push({
              point_id: ulid(),
              node_id: original_id,
              source_schema_id: parent_b.schema_id,
              description: `Inherited from parent B between crossover points ${point1}-${point2}`
            });
          }
        }
        break;

      case 'uniform':
        // Random selection for each node
        for (let i = 0; i < offspring.semantic_nodes.length; i++) {
          if (Math.random() < config.crossover_rate && parent_b.semantic_nodes[i]) {
            const original_id = offspring.semantic_nodes[i].node_id;
            offspring.semantic_nodes[i] = JSON.parse(
              JSON.stringify(parent_b.semantic_nodes[i])
            );

            mutation_points.push({
              point_id: ulid(),
              node_id: original_id,
              source_schema_id: parent_b.schema_id,
              description: `Uniform crossover from parent B`
            });
          }
        }
        break;
    }

    return {
      mutation_id: ulid(),
      operator: 'crossover',
      parent_schemas: [parent_a, parent_b],
      offspring_schema: offspring,
      mutation_points,
      created_at: Date.now()
    };
  }

  /**
   * Transplant - Move nodes from one schema to another
   */
  transplant(
    donor: BaseSchema,
    recipient: BaseSchema,
    config: TransplantConfig
  ): MutationResult {
    const offspring = JSON.parse(JSON.stringify(recipient)) as BaseSchema;
    offspring.schema_id = ulid();
    const mutation_points: MutationPoint[] = [];

    // Extract nodes from donor
    const transplanted_nodes = config.source_node_ids
      .map((id) => donor.semantic_nodes.find((n) => n.node_id === id))
      .filter((n): n is SemanticNode => n !== undefined);

    // Add to recipient
    for (const node of transplanted_nodes) {
      const cloned_node = JSON.parse(JSON.stringify(node)) as SemanticNode;
      cloned_node.node_id = ulid(); // New ID

      // Apply zone if specified
      if (config.target_zone_id) {
        cloned_node.zone_id = config.target_zone_id;
      }

      offspring.semantic_nodes.push(cloned_node);

      mutation_points.push({
        point_id: ulid(),
        node_id: cloned_node.node_id,
        source_schema_id: donor.schema_id,
        description: `Transplanted from donor schema`
      });
    }

    return {
      mutation_id: ulid(),
      operator: 'transplant',
      parent_schemas: [donor, recipient],
      offspring_schema: offspring,
      mutation_points,
      created_at: Date.now()
    };
  }

  /**
   * Fusion - Blend two schemas completely
   */
  fusion(
    schema_a: BaseSchema,
    schema_b: BaseSchema,
    config: FusionConfig = { blend_ratio: 0.5, fusion_method: 'average' }
  ): MutationResult {
    const offspring = JSON.parse(JSON.stringify(schema_a)) as BaseSchema;
    offspring.schema_id = ulid();
    const mutation_points: MutationPoint[] = [];

    // Fuse each node
    for (let i = 0; i < offspring.semantic_nodes.length; i++) {
      const node_a = schema_a.semantic_nodes[i];
      const node_b = schema_b.semantic_nodes[i];

      if (!node_b) continue;

      const fused_node = this.fuseNodes(node_a, node_b, config);
      offspring.semantic_nodes[i] = fused_node;

      mutation_points.push({
        point_id: ulid(),
        node_id: fused_node.node_id,
        source_schema_id: schema_b.schema_id,
        description: `Fused with schema B (ratio: ${config.blend_ratio})`
      });
    }

    // Fuse aesthetic profile
    offspring.aesthetic_profile = this.fuseAestheticProfiles(
      schema_a.aesthetic_profile,
      schema_b.aesthetic_profile,
      config.blend_ratio
    );

    return {
      mutation_id: ulid(),
      operator: 'fusion',
      parent_schemas: [schema_a, schema_b],
      offspring_schema: offspring,
      mutation_points,
      created_at: Date.now()
    };
  }

  /**
   * Point Mutation - Random small changes
   */
  pointMutation(schema: BaseSchema, mutation_rate: number = 0.1): MutationResult {
    const offspring = JSON.parse(JSON.stringify(schema)) as BaseSchema;
    offspring.schema_id = ulid();
    const mutation_points: MutationPoint[] = [];

    // Mutate each node with probability
    for (const node of offspring.semantic_nodes) {
      if (Math.random() < mutation_rate) {
        // Mutate random property
        const properties = Object.keys(node.properties);
        const random_property = properties[Math.floor(Math.random() * properties.length)];
        const current_value = node.properties[random_property];

        if (typeof current_value === 'number') {
          // Numeric mutation: +/- 20%
          const delta = current_value * 0.2 * (Math.random() * 2 - 1);
          node.properties[random_property] = current_value + delta;

          mutation_points.push({
            point_id: ulid(),
            node_id: node.node_id,
            property: random_property,
            source_schema_id: schema.schema_id,
            description: `Point mutation: ${random_property} ${current_value.toFixed(2)} → ${(current_value + delta).toFixed(2)}`
          });
        }
      }
    }

    return {
      mutation_id: ulid(),
      operator: 'point_mutation',
      parent_schemas: [schema],
      offspring_schema: offspring,
      mutation_points,
      created_at: Date.now()
    };
  }

  /**
   * Fuse two nodes
   */
  private fuseNodes(
    node_a: SemanticNode,
    node_b: SemanticNode,
    config: FusionConfig
  ): SemanticNode {
    const result = JSON.parse(JSON.stringify(node_a)) as SemanticNode;
    const alpha = config.blend_ratio;

    // Fuse bounds
    result.bounds = {
      x: this.lerp(node_a.bounds.x, node_b.bounds.x, alpha),
      y: this.lerp(node_a.bounds.y, node_b.bounds.y, alpha),
      width: this.lerp(node_a.bounds.width, node_b.bounds.width, alpha),
      height: this.lerp(node_a.bounds.height, node_b.bounds.height, alpha)
    };

    // Fuse properties
    for (const [key, value_a] of Object.entries(node_a.properties)) {
      const value_b = node_b.properties[key];

      if (typeof value_a === 'number' && typeof value_b === 'number') {
        result.properties[key] = this.lerp(value_a, value_b, alpha);
      } else {
        // Non-numeric: choose based on ratio
        result.properties[key] = Math.random() < alpha ? value_b : value_a;
      }
    }

    return result;
  }

  /**
   * Fuse aesthetic profiles
   */
  private fuseAestheticProfiles(
    profile_a: BaseSchema['aesthetic_profile'],
    profile_b: BaseSchema['aesthetic_profile'],
    alpha: number
  ): BaseSchema['aesthetic_profile'] {
    return {
      style_embedding_id: Math.random() < alpha ? profile_b.style_embedding_id : profile_a.style_embedding_id,
      design_language: Math.random() < alpha ? profile_b.design_language : profile_a.design_language,
      color_harmony: Math.random() < alpha ? profile_b.color_harmony : profile_a.color_harmony,
      texture_density: this.lerp(profile_a.texture_density, profile_b.texture_density, alpha),
      color_palette: {
        primary: Math.random() < alpha ? profile_b.color_palette.primary : profile_a.color_palette.primary,
        secondary: Math.random() < alpha ? profile_b.color_palette.secondary : profile_a.color_palette.secondary,
        accents: [...profile_a.color_palette.accents, ...profile_b.color_palette.accents].slice(0, 3),
        neutrals: profile_a.color_palette.neutrals,
        harmony_rule: Math.random() < alpha ? profile_b.color_palette.harmony_rule : profile_a.color_palette.harmony_rule
      },
      typography: {
        font_family_primary: profile_a.typography.font_family_primary,
        font_family_secondary: profile_a.typography.font_family_secondary,
        heading_size: this.lerp(
          profile_a.typography.heading_size,
          profile_b.typography.heading_size,
          alpha
        ),
        body_size: this.lerp(
          profile_a.typography.body_size,
          profile_b.typography.body_size,
          alpha
        ),
        line_height: this.lerp(
          profile_a.typography.line_height,
          profile_b.typography.line_height,
          alpha
        ),
        letter_spacing: this.lerp(
          profile_a.typography.letter_spacing,
          profile_b.typography.letter_spacing,
          alpha
        )
      },
      spacing_system: {
        base_unit: Math.round(
          this.lerp(profile_a.spacing_system.base_unit, profile_b.spacing_system.base_unit, alpha)
        ),
        scale_factor: this.lerp(
          profile_a.spacing_system.scale_factor,
          profile_b.spacing_system.scale_factor,
          alpha
        )
      },
      visual_language: {
        border_radius: Math.round(
          this.lerp(
            profile_a.visual_language.border_radius,
            profile_b.visual_language.border_radius,
            alpha
          )
        ),
        border_width: Math.round(
          this.lerp(
            profile_a.visual_language.border_width,
            profile_b.visual_language.border_width,
            alpha
          )
        ),
        shadow_intensity: this.lerp(
          profile_a.visual_language.shadow_intensity,
          profile_b.visual_language.shadow_intensity,
          alpha
        )
      }
    };
  }

  /**
   * Linear interpolation
   */
  private lerp(a: number, b: number, t: number): number {
    return a * (1 - t) + b * t;
  }
}

// Singleton instance
export const schemaMutator = new SchemaMutator();
