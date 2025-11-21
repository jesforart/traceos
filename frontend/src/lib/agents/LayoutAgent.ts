/**
 * Week 3 v1.2: Multi-Agent Variation Teams - Layout Agent
 *
 * Specialist agent for spatial arrangement and hierarchy.
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
 * Layout Agent - Spatial arrangement specialist
 */
export class LayoutAgent implements DesignAgent {
  agent_id: string;
  agent_type: AgentType = 'layout';
  name: string = 'Layout Specialist';
  description: string = 'Optimizes spatial arrangement and visual hierarchy';
  priority: number = 7;

  constructor() {
    this.agent_id = ulid();
  }

  /**
   * Propose layout improvements
   */
  propose(schema: BaseSchema): AgentProposal {
    const modifiers: AppliedModifier[] = [];
    const target_node_ids: string[] = [];

    // Analyze spacing
    for (const node of schema.semantic_nodes) {
      if (!this.canModify(node)) continue;

      // Suggest padding adjustments for better breathing room
      if (node.properties.padding && node.properties.padding < 16) {
        modifiers.push({
          application_id: ulid(),
          modifier_id: 'scale_padding',
          target_node_ids: [node.node_id],
          target_properties: ['padding'],
          parameter_values: { padding: 1.5 },
          applied_at: Date.now()
        });
        target_node_ids.push(node.node_id);
      }

      // Suggest margin for proper spacing
      if (node.node_type === 'hero' || node.node_type === 'cta') {
        modifiers.push({
          application_id: ulid(),
          modifier_id: 'add_margin',
          target_node_ids: [node.node_id],
          target_properties: ['margin'],
          parameter_values: { margin: 24 },
          applied_at: Date.now()
        });
        target_node_ids.push(node.node_id);
      }
    }

    return {
      proposal_id: ulid(),
      agent_id: this.agent_id,
      agent_type: this.agent_type,
      target_node_ids,
      modifiers,
      rationale: 'Improving spacing and visual hierarchy for better readability',
      confidence: 0.8,
      priority: this.priority
    };
  }

  /**
   * Evaluate proposal from another agent
   */
  evaluate(proposal: AgentProposal, schema: BaseSchema): AgentEvaluation {
    const concerns: string[] = [];
    let score = 100;

    // Check if proposal affects layout
    for (const modifier of proposal.modifiers) {
      const node = schema.semantic_nodes.find((n) => modifier.target_node_ids.includes(n.node_id));
      if (!node) continue;

      // Check for overlapping concerns
      if (
        modifier.modifier_id === 'scale_padding' ||
        modifier.modifier_id === 'add_margin'
      ) {
        // This is our domain, evaluate carefully
        if (modifier.parameter_values.padding && modifier.parameter_values.padding < 1.0) {
          concerns.push('Reducing padding may harm readability');
          score -= 20;
        }
      }

      // Check for layout breaking changes
      if (modifier.modifier_id === 'scale_font' && modifier.parameter_values.fontSize > 2.0) {
        concerns.push('Large font scaling may break layout');
        score -= 30;
      }
    }

    const verdict =
      score >= 80 ? 'approve' : score >= 60 ? 'approve_with_conditions' : 'reject';

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
    // Layout agent works on all nodes
    return true;
  }
}
