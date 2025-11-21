/**
 * Week 3 v1.2: Multi-Agent Variation Teams - Negotiator
 *
 * Coordinates specialist agents to reach design consensus.
 * Implements democratic negotiation protocols.
 */

import type {
  DesignAgent,
  NegotiationSession,
  ConsensusResult,
  AgentProposal,
  AgentEvaluation,
  NegotiationStrategy
} from './types';
import type { BaseSchema } from '../schema/types';
import { ulid } from '../../utils/ulid';

/**
 * Agent Negotiator - Multi-agent consensus building
 */
export class AgentNegotiator {
  /**
   * Start negotiation session
   */
  async negotiate(
    schema: BaseSchema,
    agents: DesignAgent[],
    strategy: NegotiationStrategy = 'weighted',
    max_rounds: number = 3
  ): Promise<NegotiationSession> {
    const session: NegotiationSession = {
      session_id: ulid(),
      schema,
      agents,
      proposals: [],
      evaluations: [],
      max_rounds,
      current_round: 0,
      started_at: Date.now()
    };

    // Run negotiation rounds
    for (let round = 0; round < max_rounds; round++) {
      session.current_round = round;

      // Phase 1: Collect proposals from all agents
      const round_proposals = agents.map((agent) => agent.propose(schema));
      session.proposals.push(...round_proposals);

      // Phase 2: Each agent evaluates other agents' proposals
      const round_evaluations: AgentEvaluation[] = [];
      for (const proposal of round_proposals) {
        for (const agent of agents) {
          if (agent.agent_id !== proposal.agent_id) {
            const evaluation = agent.evaluate(proposal, schema);
            round_evaluations.push(evaluation);
          }
        }
      }
      session.evaluations.push(...round_evaluations);

      // Phase 3: Check for consensus
      const consensus = this.checkConsensus(session, strategy);
      if (consensus) {
        session.consensus = consensus;
        session.ended_at = Date.now();
        break;
      }
    }

    // If no consensus reached, use fallback
    if (!session.consensus) {
      session.consensus = this.fallbackConsensus(session, strategy);
      session.ended_at = Date.now();
    }

    console.log(
      `🤝 Negotiation complete: ${session.consensus.approved_proposals.length} proposals approved (consensus: ${session.consensus.consensus_score.toFixed(1)}%)`
    );

    return session;
  }

  /**
   * Check if consensus has been reached
   */
  private checkConsensus(
    session: NegotiationSession,
    strategy: NegotiationStrategy
  ): ConsensusResult | null {
    const approved_proposals: AgentProposal[] = [];
    const modified_proposals: Array<{
      original: AgentProposal;
      adjustments: any[];
    }> = [];
    const rejected_proposals: AgentProposal[] = [];

    // Evaluate each proposal
    for (const proposal of session.proposals) {
      const evaluations = session.evaluations.filter(
        (e) => e.proposal_id === proposal.proposal_id
      );

      const decision = this.evaluateProposal(proposal, evaluations, strategy);

      if (decision.approved) {
        if (decision.adjustments.length > 0) {
          modified_proposals.push({
            original: proposal,
            adjustments: decision.adjustments
          });
        } else {
          approved_proposals.push(proposal);
        }
      } else {
        rejected_proposals.push(proposal);
      }
    }

    // Calculate consensus score
    const total_proposals = session.proposals.length;
    const approved_count = approved_proposals.length + modified_proposals.length;
    const consensus_score = total_proposals > 0 ? (approved_count / total_proposals) * 100 : 0;

    // Apply approved changes to schema
    // TODO: Implement actual modifier application
    // For now, return schema as-is since proper application requires ModifierDefinition lookup
    const final_schema = JSON.parse(JSON.stringify(session.schema)) as BaseSchema;

    return {
      consensus_id: ulid(),
      approved_proposals,
      modified_proposals,
      rejected_proposals,
      consensus_score,
      final_schema
    };
  }

  /**
   * Evaluate a single proposal based on strategy
   */
  private evaluateProposal(
    proposal: AgentProposal,
    evaluations: AgentEvaluation[],
    strategy: NegotiationStrategy
  ): { approved: boolean; adjustments: any[] } {
    if (evaluations.length === 0) {
      return { approved: true, adjustments: [] };
    }

    const adjustments: any[] = [];

    switch (strategy) {
      case 'unanimous':
        // All must approve
        const all_approve = evaluations.every((e) => e.verdict === 'approve');
        return { approved: all_approve, adjustments };

      case 'majority':
        // >50% must approve
        const approve_count = evaluations.filter((e) => e.verdict === 'approve').length;
        const majority = approve_count > evaluations.length / 2;
        return { approved: majority, adjustments };

      case 'weighted':
        // Weighted by agent priority
        const weighted_score = evaluations.reduce((sum, e) => {
          const weight = 1.0; // Could get from agent priority
          const vote = e.verdict === 'approve' ? 1 : e.verdict === 'reject' ? -1 : 0;
          return sum + vote * weight;
        }, 0);
        return { approved: weighted_score > 0, adjustments };

      case 'autocratic':
        // Highest priority agent wins
        const highest_priority_eval = evaluations.reduce((prev, curr) =>
          curr.score > prev.score ? curr : prev
        );
        return {
          approved: highest_priority_eval.verdict === 'approve',
          adjustments
        };

      default:
        return { approved: false, adjustments };
    }
  }

  /**
   * Fallback consensus when no agreement reached
   */
  private fallbackConsensus(
    session: NegotiationSession,
    strategy: NegotiationStrategy
  ): ConsensusResult {
    // Take only highest confidence proposals
    const sorted = [...session.proposals].sort((a, b) => b.confidence - a.confidence);
    const approved_proposals = sorted.slice(0, Math.ceil(sorted.length / 3));

    // TODO: Implement actual modifier application
    const final_schema = JSON.parse(JSON.stringify(session.schema)) as BaseSchema;

    return {
      consensus_id: ulid(),
      approved_proposals,
      modified_proposals: [],
      rejected_proposals: sorted.slice(Math.ceil(sorted.length / 3)),
      consensus_score: 50, // Partial consensus
      final_schema
    };
  }

  /**
   * Get negotiation summary
   */
  getSummary(session: NegotiationSession): string {
    if (!session.consensus) {
      return 'Negotiation in progress...';
    }

    const { approved_proposals, modified_proposals, rejected_proposals, consensus_score } =
      session.consensus;

    return `
Negotiation Summary:
- Rounds: ${session.current_round + 1}/${session.max_rounds}
- Approved: ${approved_proposals.length}
- Modified: ${modified_proposals.length}
- Rejected: ${rejected_proposals.length}
- Consensus: ${consensus_score.toFixed(1)}%
- Duration: ${session.ended_at ? session.ended_at - session.started_at : 0}ms
    `.trim();
  }
}

// Singleton instance
export const agentNegotiator = new AgentNegotiator();
