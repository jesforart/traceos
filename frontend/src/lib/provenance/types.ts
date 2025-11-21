/**
 * Week 3: Design Variation Engine - Provenance Type System
 *
 * Types for tracking design lineage, branches, and evolution.
 * "Evolutionary design lineage protocol" - future research technology.
 * Based on WEEK3_DESIGN_VARIATION_ENGINE_v1.2_FINAL.md
 */

/**
 * Provenance Node - A point in design evolution
 */
export interface ProvenanceNode {
  node_id: string;
  schema_id: string;
  created_at: number;

  // Lineage
  parent_id?: string;
  children_ids: string[];

  // Branching
  is_branch_point: boolean;
  branch_reason?: string;

  // Changes
  changes: DesignChange[];

  // Context
  creator?: string;
  intent?: string;
  tags: string[];
}

/**
 * Design Change - What actually changed
 */
export interface DesignChange {
  change_id: string;
  change_type: 'add' | 'modify' | 'remove' | 'transform';

  // Target
  node_id: string;
  property?: string;

  // Values
  before_value?: any;
  after_value?: any;

  // Cause
  caused_by: 'modifier' | 'ai' | 'manual' | 'drift';
  modifier_id?: string;

  // Impact
  semantic_impact: number; // 0-1
}

/**
 * Design Lineage - Complete ancestry tree
 */
export interface DesignLineage {
  root_schema_id: string;
  created_at: number;

  // All nodes
  nodes: Record<string, ProvenanceNode>;

  // Branch points
  branches: DesignBranch[];

  // Statistics
  stats: {
    total_variations: number;
    total_branches: number;
    max_depth: number;
    total_changes: number;
  };
}

/**
 * Design Branch - Divergent evolution path
 */
export interface DesignBranch {
  branch_id: string;
  branch_point_id: string;
  created_at: number;

  // Why it branched
  reason: 'drift_threshold' | 'manual' | 'experiment' | 'mutation';
  drift_value?: number;

  // Lineage from branch point
  descendant_ids: string[];

  // Metadata
  name?: string;
  description?: string;
  tags: string[];
}

/**
 * Lineage Query - Search design history
 */
export interface LineageQuery {
  // Filters
  schema_ids?: string[];
  created_after?: number;
  created_before?: number;
  tags?: string[];
  min_drift?: number;
  max_drift?: number;

  // Traversal
  from_node?: string;
  max_depth?: number;
  direction?: 'ancestors' | 'descendants' | 'both';

  // Sorting
  sort_by?: 'created_at' | 'drift' | 'depth';
  sort_order?: 'asc' | 'desc';
}

/**
 * Lineage Query Result
 */
export interface LineageQueryResult {
  nodes: ProvenanceNode[];
  paths?: ProvenancePath[];
  total_count: number;
}

/**
 * Provenance Path - Route through lineage
 */
export interface ProvenancePath {
  path_id: string;
  nodes: ProvenanceNode[];
  total_drift: number;
  total_changes: number;
  branches_crossed: number;
}

/**
 * Automatic Branching Event
 */
export interface AutoBranchEvent {
  event_id: string;
  triggered_at: number;

  // Trigger
  parent_variation_id: string;
  child_variation_id: string;
  drift_value: number;
  threshold_exceeded: number;

  // Created branch
  branch_id: string;

  // Context
  auto_created: true;
  reason: string;
}

/**
 * Drift Timeline - Track drift over time
 */
export interface DriftTimeline {
  schema_id: string;
  timeline: {
    timestamp: number;
    drift_from_root: number;
    drift_from_parent: number;
    variation_id: string;
  }[];

  // Statistics
  average_drift: number;
  max_drift: number;
  drift_velocity: number; // Rate of drift increase
}
