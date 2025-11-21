/**
 * Week 3 v1.2: Variation Prompt DSL - AI Prompt Generator
 *
 * Converts natural language to DSL commands.
 * Future: Could integrate with LLM for more sophisticated parsing.
 */

import type { VariationInstructions } from './types';
import { variationPromptParser } from './VariationPromptParser';

/**
 * AI Prompt Generator - Natural language to DSL
 */
export class AIPromptGenerator {
  /**
   * Generate DSL from natural language prompt
   *
   * This is a basic pattern-matching implementation.
   * Future: Could integrate with LLM API for more sophisticated understanding.
   */
  generateDSL(naturalLanguage: string, targetNodeId: string): string {
    const dslLines: string[] = [`vary ${targetNodeId}:`];

    // Normalize input
    const input = naturalLanguage.toLowerCase();

    // Pattern matching for common intents
    if (input.includes('bigger') || input.includes('larger') || input.includes('enlarge')) {
      const match = input.match(/(\d+)%/);
      const percent = match ? match[1] : '20';
      dslLines.push(`  enlarge by ${percent}%`);
    }

    if (input.includes('scale') && input.includes('width')) {
      const match = input.match(/(\d+\.?\d*)/);
      const factor = match ? match[1] : '1.2';
      dslLines.push(`  scale width by ${factor}`);
    }

    if (input.includes('scale') && input.includes('height')) {
      const match = input.match(/(\d+\.?\d*)/);
      const factor = match ? match[1] : '1.2';
      dslLines.push(`  scale height by ${factor}`);
    }

    if (input.includes('bold') || input.includes('bolder')) {
      dslLines.push(`  increase fontWeight by 200`);
    }

    if (input.includes('round') && input.includes('corner')) {
      const match = input.match(/(\d+)/);
      const radius = match ? match[1] : '8';
      dslLines.push(`  round corners to ${radius}`);
    }

    if (input.includes('shift') && input.includes('hue')) {
      const match = input.match(/([+-]?\d+)/);
      const amount = match ? match[1] : '+10';
      dslLines.push(`  shift hue ${amount}`);
    }

    if (input.includes('more padding')) {
      const match = input.match(/(\d+\.?\d*)/);
      const factor = match ? match[1] : '1.4';
      dslLines.push(`  scale padding by ${factor}`);
    }

    if (input.includes('opacity')) {
      const match = input.match(/(\d+\.?\d*)/);
      const value = match ? match[1] : '0.9';
      dslLines.push(`  add opacity ${value}`);
    }

    // Accessibility constraints
    if (input.includes('accessible') || input.includes('wcag')) {
      dslLines.push(`  maintain contrast > 4.5`);
    }

    if (input.includes('readable') || input.includes('readability')) {
      dslLines.push(`  preserve readability`);
    }

    // If no patterns matched, return a helpful default
    if (dslLines.length === 1) {
      dslLines.push(`  # No recognized patterns. Try: "make it 20% bigger and bold"`);
    }

    return dslLines.join('\n');
  }

  /**
   * Generate and parse DSL in one step
   */
  generateInstructions(
    naturalLanguage: string,
    targetNodeId: string
  ): VariationInstructions {
    const dsl = this.generateDSL(naturalLanguage, targetNodeId);
    return variationPromptParser.parse(dsl);
  }

  /**
   * Get example prompts for UI
   */
  getExamples(): Array<{ natural: string; dsl: string }> {
    return [
      {
        natural: 'Make it 20% bigger and bold',
        dsl: 'vary hero_title:\n  enlarge by 20%\n  increase fontWeight by 200'
      },
      {
        natural: 'Round the corners to 12px',
        dsl: 'vary hero_cta:\n  round corners to 12'
      },
      {
        natural: 'Shift hue +15 degrees',
        dsl: 'vary hero_background:\n  shift hue +15'
      },
      {
        natural: 'Scale width by 1.5',
        dsl: 'vary content_section:\n  scale width by 1.5'
      },
      {
        natural: 'Make it accessible with WCAG AA',
        dsl: 'vary text_content:\n  maintain contrast > 4.5\n  preserve readability'
      }
    ];
  }
}

// Singleton instance
export const aiPromptGenerator = new AIPromptGenerator();
