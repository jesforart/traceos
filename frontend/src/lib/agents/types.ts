/**
 * Week 3 v1.2: Multi-Agent Variation Teams - Types
 *
 * Specialist design agents that negotiate consensus.
 */

import type { BaseSchema, SemanticNode } from '../schema/types';
import type { AppliedModifier } from '../modifiers/types';

/**
 * Design Agent - Specialist agent interface
 */
export interface DesignAgent {
  agent_id: string;
  agent_type: AgentType;
  name: string;
  description: string;
  priority: number; // 1-10, higher = more influence

  /**
   * Propose changes to schema
   */
  propose(schema: BaseSchema): AgentProposal;

  /**
   * Evaluate another agent's proposal
   */
  evaluate(proposal: AgentProposal, schema: BaseSchema): AgentEvaluation;

  /**
   * Can this agent apply changes to this node?
   */
  canModify(node: SemanticNode): boolean;
}

/**
 * Agent Types
 */
export type AgentType =
  | 'layout'
  | 'typography'
  | 'color'
  | 'accessibility'
  | 'brand'
  | 'animation';

/**
 * Agent Proposal - Suggested changes
 */
export interface AgentProposal {
  proposal_id: string;
  agent_id: string;
  agent_type: AgentType;
  target_node_ids: string[];
  modifiers: AppliedModifier[];
  rationale: string;
  confidence: number; // 0.0 to 1.0
  priority: number;
}

/**
 * Agent Evaluation - Response to proposal
 */
export interface AgentEvaluation {
  evaluation_id: string;
  evaluator_agent_id: string;
  proposal_id: string;
  verdict: 'approve' | 'approve_with_conditions' | 'reject' | 'abstain';
  score: number; // 0-100
  concerns: string[];
  suggested_adjustments?: Partial<AppliedModifier>[];
}

/**
 * Negotiation Session - Multi-agent consensus building
 */
export interface NegotiationSession {
  session_id: string;
  schema: BaseSchema;
  agents: DesignAgent[];
  proposals: AgentProposal[];
  evaluations: AgentEvaluation[];
  consensus?: ConsensusResult;
  max_rounds: number;
  current_round: number;
  started_at: number;
  ended_at?: number;
}

/**
 * Consensus Result - Final agreed changes
 */
export interface ConsensusResult {
  consensus_id: string;
  approved_proposals: AgentProposal[];
  modified_proposals: Array<{
    original: AgentProposal;
    adjustments: Partial<AppliedModifier>[];
  }>;
  rejected_proposals: AgentProposal[];
  consensus_score: number; // 0-100, how much agents agreed
  final_schema: BaseSchema;
}

/**
 * Agent Configuration
 */
export interface AgentConfig {
  agent_type: AgentType;
  priority?: number;
  enabled?: boolean;
  custom_rules?: Record<string, any>;
}

/**
 * Negotiation Strategy
 */
export type NegotiationStrategy =
  | 'unanimous' // All agents must approve
  | 'majority' // >50% approval
  | 'weighted' // Weighted by priority
  | 'autocratic'; // Highest priority agent wins
