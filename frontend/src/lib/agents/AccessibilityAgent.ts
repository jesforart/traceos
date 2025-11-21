/**
 * Week 3 v1.2: Multi-Agent Variation Teams - Accessibility Agent
 *
 * Specialist agent for WCAG compliance and inclusive design.
 */

import type {
  DesignAgent,
  AgentProposal,
  AgentEvaluation,
  AgentType
} from './types';
import type { BaseSchema, SemanticNode } from '../schema/types';
import type { AppliedModifier } from '../modifiers/types';
import { ulid } from '../../utils/ulid';

/**
 * Accessibility Agent - WCAG compliance specialist
 */
export class AccessibilityAgent implements DesignAgent {
  agent_id: string;
  agent_type: AgentType = 'accessibility';
  name: string = 'Accessibility Specialist';
  description: string = 'Ensures WCAG AA/AAA compliance and inclusive design';
  priority: number = 10; // Highest priority

  constructor() {
    this.agent_id = ulid();
  }

  /**
   * Propose accessibility improvements
   */
  propose(schema: BaseSchema): AgentProposal {
    const modifiers: AppliedModifier[] = [];
    const target_node_ids: string[] = [];

    for (const node of schema.semantic_nodes) {
      if (!this.canModify(node)) continue;

      // Check contrast ratios
      if (node.properties.color && node.properties.backgroundColor) {
        const contrast = this.calculateContrastRatio(
          node.properties.color,
          node.properties.backgroundColor
        );

        const target_contrast = schema.context.accessibility_level === 'AAA' ? 7.0 : 4.5;

        if (contrast < target_contrast) {
          modifiers.push({
            application_id: ulid(),
            modifier_id: 'ensure_contrast',
            target_node_ids: [node.node_id],
            target_properties: ['color', 'backgroundColor'],
            parameter_values: { min_contrast: target_contrast },
            applied_at: Date.now()
          });
          target_node_ids.push(node.node_id);
        }
      }

      // Check font sizes
      if (node.properties.fontSize && node.properties.fontSize < 14) {
        modifiers.push({
          application_id: ulid(),
          modifier_id: 'scale_font',
          target_node_ids: [node.node_id],
          target_properties: ['fontSize'],
          parameter_values: { fontSize: 14 / node.properties.fontSize },
          applied_at: Date.now()
        });
        target_node_ids.push(node.node_id);
      }

      // Check touch targets (mobile)
      if (schema.context.device_targets.includes('mobile')) {
        if (
          node.node_type === 'cta' &&
          (node.bounds.width < 44 || node.bounds.height < 44)
        ) {
          // Suggest enlarging
          const scale_factor = 44 / Math.min(node.bounds.width, node.bounds.height);
          modifiers.push({
            application_id: ulid(),
            modifier_id: 'enlarge',
            target_node_ids: [node.node_id],
            target_properties: ['width', 'height'],
            parameter_values: { scale: scale_factor },
            applied_at: Date.now()
          });
          target_node_ids.push(node.node_id);
        }
      }
    }

    return {
      proposal_id: ulid(),
      agent_id: this.agent_id,
      agent_type: this.agent_type,
      target_node_ids,
      modifiers,
      rationale: `Ensuring WCAG ${schema.context.accessibility_level} compliance`,
      confidence: 0.95,
      priority: this.priority
    };
  }

  /**
   * Evaluate proposal from another agent
   */
  evaluate(proposal: AgentProposal, schema: BaseSchema): AgentEvaluation {
    const concerns: string[] = [];
    let score = 100;

    // Check if proposal violates accessibility
    for (const modifier of proposal.modifiers) {
      const node = schema.semantic_nodes.find((n) => modifier.target_node_ids.includes(n.node_id));
      if (!node) continue;

      // Font size reduction
      if (modifier.modifier_id === 'scale_font' && modifier.parameter_values.fontSize < 1.0) {
        const final_size = (node.properties.fontSize || 16) * modifier.parameter_values.fontSize;
        if (final_size < 14) {
          concerns.push(`Font size ${final_size.toFixed(1)}px is below recommended 14px`);
          score -= 40;
        }
      }

      // Opacity reduction
      if (modifier.modifier_id === 'adjust_opacity' && modifier.parameter_values.opacity < 0.7) {
        concerns.push('Low opacity may reduce readability');
        score -= 20;
      }

      // Color changes (may affect contrast)
      if (
        modifier.modifier_id === 'saturate' ||
        modifier.modifier_id.includes('color')
      ) {
        concerns.push('Color changes may affect contrast ratios - needs verification');
        score -= 10;
      }
    }

    // Accessibility agent has veto power on serious violations
    const verdict = score >= 70 ? 'approve' : score >= 50 ? 'approve_with_conditions' : 'reject';

    return {
      evaluation_id: ulid(),
      evaluator_agent_id: this.agent_id,
      proposal_id: proposal.proposal_id,
      verdict,
      score,
      concerns
    };
  }

  /**
   * Can modify this node?
   */
  canModify(node: SemanticNode): boolean {
    // Accessibility concerns apply to all visible nodes
    return node.node_type !== 'background';
  }

  /**
   * Calculate WCAG contrast ratio
   */
  private calculateContrastRatio(fg: string, bg: string): number {
    const fg_luminance = this.relativeLuminance(fg);
    const bg_luminance = this.relativeLuminance(bg);

    const lighter = Math.max(fg_luminance, bg_luminance);
    const darker = Math.min(fg_luminance, bg_luminance);

    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Calculate relative luminance
   */
  private relativeLuminance(color: string): number {
    const rgb = this.hexToRgb(color);
    if (!rgb) return 0;

    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((c) => {
      const sRGB = c / 255;
      return sRGB <= 0.03928 ? sRGB / 12.92 : Math.pow((sRGB + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /**
   * Convert hex to RGB
   */
  private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        }
      : null;
  }
}
