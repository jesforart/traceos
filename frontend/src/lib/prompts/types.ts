/**
 * Week 3 v1.2: Variation Prompt DSL - Type Definitions
 *
 * Natural language design commands for variation generation.
 * Example:
 *   vary hero_background:
 *       scale width by 1.2
 *       shift hue +10
 *       soften edges 0.3
 */

import type { BaseSchema } from '../schema/types';

/**
 * Variation Action - Single design operation
 */
export interface VariationAction {
  type: 'scale' | 'shift' | 'add' | 'multiply' | 'blend' | 'set' | 'constraint';
  property: string;
  value: number | string;
  target?: string; // For blend operations
  amount?: number; // For blend operations
}

/**
 * Variation Constraint - Design rule
 */
export interface VariationConstraint {
  type: 'maintain' | 'preserve' | 'ensure';
  property: string;
  operator?: '>' | '<' | '>=' | '<=' | '==';
  value?: number | string;
}

/**
 * Variation Instructions - Parsed DSL
 */
export interface VariationInstructions {
  target: string; // Node ID
  actions: VariationAction[];
  constraints: VariationConstraint[];
}

/**
 * Validation Result
 */
export interface ValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

/**
 * DSL Action Parsers
 */
export type ActionParser = (tokens: string[]) => VariationAction | null;

/**
 * DSL Keywords
 */
export const DSL_KEYWORDS = {
  // Action verbs
  actions: [
    'scale',
    'shift',
    'soften',
    'increase',
    'decrease',
    'enlarge',
    'shrink',
    'round',
    'animate',
    'add',
    'remove'
  ],

  // Constraint verbs
  constraints: ['maintain', 'preserve', 'ensure'],

  // Operators
  operators: ['by', 'to', 'toward', '+', '-', '*', '/'],

  // Properties
  properties: [
    'width',
    'height',
    'hue',
    'saturation',
    'brightness',
    'edges',
    'font-size',
    'color',
    'padding',
    'margin',
    'opacity',
    'contrast',
    'corners'
  ]
} as const;
