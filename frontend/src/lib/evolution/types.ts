/**
 * Week 3 v1.2: Cross-Schema Mutation - Types
 *
 * Genetic operators for design evolution and speciation.
 */

import type { BaseSchema, SemanticNode } from '../schema/types';

/**
 * Mutation Operator Types
 */
export type MutationOperator = 'crossover' | 'transplant' | 'fusion' | 'point_mutation';

/**
 * Mutation Result
 */
export interface MutationResult {
  mutation_id: string;
  operator: MutationOperator;
  parent_schemas: BaseSchema[];
  offspring_schema: BaseSchema;
  mutation_points: MutationPoint[];
  fitness_score?: number;
  created_at: number;
}

/**
 * Mutation Point - Where genetic material was swapped
 */
export interface MutationPoint {
  point_id: string;
  node_id: string;
  property?: string;
  source_schema_id: string;
  description: string;
}

/**
 * Crossover Configuration
 */
export interface CrossoverConfig {
  crossover_type: 'single_point' | 'two_point' | 'uniform';
  crossover_rate: number; // 0.0 to 1.0
  preserve_hierarchy?: boolean;
}

/**
 * Transplant Configuration
 */
export interface TransplantConfig {
  source_node_ids: string[];
  target_zone_id?: string;
  preserve_style?: boolean;
}

/**
 * Fusion Configuration
 */
export interface FusionConfig {
  blend_ratio: number; // 0.0 to 1.0
  fusion_method: 'average' | 'dominant' | 'alternate';
}

/**
 * Fitness Function - Evaluates design quality
 */
export interface FitnessFunction {
  evaluate(schema: BaseSchema): number; // 0-100
}

/**
 * Evolutionary Population
 */
export interface DesignPopulation {
  population_id: string;
  generation: number;
  schemas: BaseSchema[];
  fitness_scores: Map<string, number>;
  best_schema?: BaseSchema;
  average_fitness: number;
}

/**
 * Evolution Strategy
 */
export interface EvolutionStrategy {
  population_size: number;
  mutation_rate: number;
  crossover_rate: number;
  selection_method: 'tournament' | 'roulette' | 'elite';
  elitism_count?: number; // Top N to preserve
  max_generations: number;
}

/**
 * Gene - Designates inheritable trait
 */
export interface DesignGene {
  gene_id: string;
  node_id: string;
  property: string;
  value: any;
  dominance: number; // 0-1, how strongly this gene expresses
}
