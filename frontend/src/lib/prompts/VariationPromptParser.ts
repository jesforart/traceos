/**
 * Week 3 v1.2: Variation Prompt DSL - Parser
 *
 * Parses natural language variation commands into executable instructions.
 */

import type {
  VariationInstructions,
  VariationAction,
  VariationConstraint,
  ValidationResult,
  ActionParser
} from './types';
import { DSL_KEYWORDS } from './types';
import type { BaseSchema } from '../schema/types';

/**
 * Variation Prompt Parser
 */
export class VariationPromptParser {
  /**
   * Parse a variation prompt into instructions
   */
  parse(prompt: string): VariationInstructions {
    const lines = prompt
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (lines.length === 0) {
      throw new Error('Empty prompt');
    }

    // First line should be "vary <node_id>:"
    const target = this.parseTarget(lines[0]);

    // Remaining lines are actions and constraints
    const actions: VariationAction[] = [];
    const constraints: VariationConstraint[] = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i];
      const tokens = this.tokenize(line);

      if (tokens.length === 0) continue;

      const verb = tokens[0].toLowerCase();

      // Check if it's a constraint
      if (DSL_KEYWORDS.constraints.includes(verb as any)) {
        const constraint = this.parseConstraint(tokens);
        if (constraint) {
          constraints.push(constraint);
        }
      } else if (DSL_KEYWORDS.actions.includes(verb as any)) {
        const action = this.parseAction(tokens);
        if (action) {
          actions.push(action);
        }
      } else {
        console.warn(`Unknown verb: ${verb}`);
      }
    }

    return {
      target,
      actions,
      constraints
    };
  }

  /**
   * Validate parsed instructions
   */
  validate(instructions: VariationInstructions): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check target exists
    if (!instructions.target || instructions.target.length === 0) {
      errors.push('No target node specified');
    }

    // Check at least one action
    if (instructions.actions.length === 0) {
      warnings.push('No actions specified');
    }

    // Validate each action
    for (const action of instructions.actions) {
      if (!action.property) {
        errors.push(`Action missing property: ${JSON.stringify(action)}`);
      }
      if (action.value === undefined) {
        errors.push(`Action missing value: ${JSON.stringify(action)}`);
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined,
      warnings: warnings.length > 0 ? warnings : undefined
    };
  }

  /**
   * Execute instructions on a schema
   */
  execute(instructions: VariationInstructions, schema: BaseSchema): BaseSchema {
    // Find target node
    const targetNode = schema.semantic_nodes.find(
      (n) => n.node_id === instructions.target
    );

    if (!targetNode) {
      throw new Error(`Target node not found: ${instructions.target}`);
    }

    // Clone schema
    const modified = JSON.parse(JSON.stringify(schema)) as BaseSchema;
    const modifiedNode = modified.semantic_nodes.find(
      (n) => n.node_id === instructions.target
    )!;

    // Apply each action
    for (const action of instructions.actions) {
      this.applyAction(modifiedNode, action);
    }

    // Validate constraints
    for (const constraint of instructions.constraints) {
      this.validateConstraint(modifiedNode, constraint);
    }

    return modified;
  }

  /**
   * Parse target from first line
   */
  private parseTarget(line: string): string {
    // Expected format: "vary <node_id>:"
    const match = line.match(/^vary\s+([a-zA-Z0-9_-]+):/);
    if (!match) {
      throw new Error(`Invalid target line: ${line}`);
    }
    return match[1];
  }

  /**
   * Tokenize a line
   */
  private tokenize(line: string): string[] {
    // Simple whitespace tokenization
    return line
      .split(/\s+/)
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
  }

  /**
   * Parse an action
   */
  private parseAction(tokens: string[]): VariationAction | null {
    const verb = tokens[0].toLowerCase();

    const actionParsers: Record<string, ActionParser> = {
      scale: this.parseScale.bind(this),
      shift: this.parseShift.bind(this),
      soften: this.parseSoften.bind(this),
      increase: this.parseIncrease.bind(this),
      decrease: this.parseDecrease.bind(this),
      enlarge: this.parseEnlarge.bind(this),
      round: this.parseRound.bind(this),
      add: this.parseAdd.bind(this),
      animate: this.parseAnimate.bind(this)
    };

    const parser = actionParsers[verb];
    if (!parser) {
      console.warn(`No parser for verb: ${verb}`);
      return null;
    }

    return parser(tokens.slice(1));
  }

  /**
   * Parse: scale <property> by <amount>
   */
  private parseScale(tokens: string[]): VariationAction {
    // ["width", "by", "1.2"]
    const property = tokens[0];
    const amount = parseFloat(tokens[2]);

    return {
      type: 'multiply',
      property,
      value: amount
    };
  }

  /**
   * Parse: shift <property> <value>
   * Examples:
   *   shift hue +10
   *   shift color toward #0066FF
   */
  private parseShift(tokens: string[]): VariationAction {
    const property = tokens[0];

    if (tokens.includes('toward')) {
      const targetIndex = tokens.indexOf('toward') + 1;
      const target = tokens[targetIndex];
      return {
        type: 'blend',
        property,
        value: 0.3,
        target,
        amount: 0.3
      };
    } else {
      const value = parseFloat(tokens[1]);
      return {
        type: 'add',
        property,
        value
      };
    }
  }

  /**
   * Parse: soften <property> <value>
   */
  private parseSoften(tokens: string[]): VariationAction {
    const property = tokens[0];
    const value = parseFloat(tokens[1]);

    return {
      type: 'multiply',
      property,
      value: 1 - value // Soften by reducing
    };
  }

  /**
   * Parse: increase <property> by <value>
   */
  private parseIncrease(tokens: string[]): VariationAction {
    const property = tokens[0];
    const value = parseFloat(tokens[2]); // Skip "by"

    return {
      type: 'add',
      property,
      value
    };
  }

  /**
   * Parse: decrease <property> by <value>
   */
  private parseDecrease(tokens: string[]): VariationAction {
    const property = tokens[0];
    const value = parseFloat(tokens[2]); // Skip "by"

    return {
      type: 'add',
      property,
      value: -value
    };
  }

  /**
   * Parse: enlarge by <percent>
   */
  private parseEnlarge(tokens: string[]): VariationAction {
    const value = parseFloat(tokens[1].replace('%', '')) / 100;

    return {
      type: 'multiply',
      property: 'scale',
      value: 1 + value
    };
  }

  /**
   * Parse: round corners to <value>
   */
  private parseRound(tokens: string[]): VariationAction {
    const value = parseFloat(tokens[2]); // Skip "corners to"

    return {
      type: 'set',
      property: 'borderRadius',
      value
    };
  }

  /**
   * Parse: add <property> <value>
   */
  private parseAdd(tokens: string[]): VariationAction {
    const property = tokens[0];
    const value = parseFloat(tokens[1]);

    return {
      type: 'add',
      property,
      value
    };
  }

  /**
   * Parse: animate on <event>
   */
  private parseAnimate(tokens: string[]): VariationAction {
    return {
      type: 'set',
      property: 'animation',
      value: tokens[1] // "hover", etc.
    };
  }

  /**
   * Parse a constraint
   */
  private parseConstraint(tokens: string[]): VariationConstraint | null {
    const verb = tokens[0].toLowerCase() as 'maintain' | 'preserve' | 'ensure';

    // Examples:
    //   maintain contrast > 4.5
    //   preserve readability
    //   ensure WCAG AAA

    if (tokens.length === 2) {
      // Simple constraint: "preserve readability"
      return {
        type: verb,
        property: tokens[1]
      };
    } else if (tokens.length === 3) {
      // Value constraint: "maintain contrast 4.5"
      return {
        type: verb,
        property: tokens[1],
        operator: '>=',
        value: parseFloat(tokens[2])
      };
    } else if (tokens.length === 4) {
      // Operator constraint: "maintain contrast > 4.5"
      return {
        type: verb,
        property: tokens[1],
        operator: tokens[2] as '>' | '<' | '>=' | '<=' | '==',
        value: parseFloat(tokens[3])
      };
    }

    return null;
  }

  /**
   * Apply an action to a node
   */
  private applyAction(
    node: any,
    action: VariationAction
  ): void {
    const currentValue = node.properties[action.property] ?? 0;

    switch (action.type) {
      case 'add':
        node.properties[action.property] =
          (currentValue as number) + (action.value as number);
        break;

      case 'multiply':
        node.properties[action.property] =
          (currentValue as number) * (action.value as number);
        break;

      case 'set':
        node.properties[action.property] = action.value;
        break;

      case 'blend':
        // Simple blend for now
        node.properties[action.property] = action.target;
        break;

      default:
        console.warn(`Unknown action type: ${action.type}`);
    }
  }

  /**
   * Validate a constraint
   */
  private validateConstraint(
    node: any,
    constraint: VariationConstraint
  ): void {
    // For now, just log - would implement actual validation
    console.log(`Validating constraint: ${constraint.type} ${constraint.property}`);
  }
}

// Singleton instance
export const variationPromptParser = new VariationPromptParser();
