/**
 * Week 3: Design Variation Engine - Drift Detector
 *
 * Evolutionary design lineage protocol.
 * Detects semantic drift and triggers automatic branching.
 * "Future research technology" - biological evolution for designs.
 */

import type { BaseSchema } from '../schema/types';
import type { SemanticDrift, GeneratedVariation } from './types';
import { DRIFT_THRESHOLDS } from './types';

/**
 * Drift Detector - Measures semantic change over time
 */
export class DriftDetector {
  /**
   * Detect drift between parent and child schemas
   */
  detect(parent: BaseSchema, child: BaseSchema): SemanticDrift {
    const changed_nodes = this.findChangedNodes(parent, child);
    const drift_value = this.calculateDrift(changed_nodes);
    const category = this.categorizeDrift(drift_value);
    const should_branch = this.shouldBranch(drift_value, category);

    let branch_reason: string | undefined;
    if (should_branch) {
      branch_reason = this.getBranchReason(drift_value, category, changed_nodes);
    }

    return {
      drift_value,
      changed_nodes,
      category,
      should_branch,
      branch_reason
    };
  }

  /**
   * Find all nodes that changed
   */
  private findChangedNodes(
    parent: BaseSchema,
    child: BaseSchema
  ): SemanticDrift['changed_nodes'] {
    const changes: SemanticDrift['changed_nodes'] = [];

    for (const parent_node of parent.semantic_nodes) {
      const child_node = child.semantic_nodes.find(
        (n) => n.node_id === parent_node.node_id
      );

      if (!child_node) {
        // Node was removed
        continue;
      }

      // Compare each property
      for (const [property, parent_value] of Object.entries(
        parent_node.properties
      )) {
        const child_value = child_node.properties[property];

        if (parent_value === child_value) continue;

        // Calculate semantic impact of this change
        const semantic_impact = this.calculateSemanticImpact(
          parent_node.node_type,
          property,
          parent_value,
          child_value
        );

        changes.push({
          node_id: parent_node.node_id,
          property,
          original_value: parent_value,
          new_value: child_value,
          semantic_impact
        });
      }
    }

    return changes;
  }

  /**
   * Calculate overall drift value
   */
  private calculateDrift(changed_nodes: SemanticDrift['changed_nodes']): number {
    if (changed_nodes.length === 0) return 0;

    // Weighted average of semantic impacts
    const total_impact = changed_nodes.reduce(
      (sum, change) => sum + change.semantic_impact,
      0
    );

    return Math.min(total_impact / changed_nodes.length, 1.0);
  }

  /**
   * Calculate semantic impact of a single property change
   */
  private calculateSemanticImpact(
    node_type: string,
    property: string,
    original_value: any,
    new_value: any
  ): number {
    // High-impact properties (meaning changes significantly)
    const high_impact_properties = [
      'color',
      'backgroundColor',
      'fontSize',
      'fontFamily'
    ];

    // Medium-impact properties
    const medium_impact_properties = [
      'fontWeight',
      'padding',
      'margin',
      'borderRadius'
    ];

    // Low-impact properties
    const low_impact_properties = ['opacity', 'zIndex'];

    let base_impact = 0.1; // Default low impact

    if (high_impact_properties.includes(property)) {
      base_impact = 0.5;
    } else if (medium_impact_properties.includes(property)) {
      base_impact = 0.3;
    } else if (low_impact_properties.includes(property)) {
      base_impact = 0.1;
    }

    // Calculate magnitude of change
    let magnitude = 1.0;

    if (typeof original_value === 'number' && typeof new_value === 'number') {
      const diff = Math.abs(new_value - original_value);
      const avg = (Math.abs(original_value) + Math.abs(new_value)) / 2;
      magnitude = avg > 0 ? Math.min(diff / avg, 1.0) : 0;
    } else if (original_value !== new_value) {
      magnitude = 1.0; // Complete change for non-numeric
    }

    // Hero nodes have higher impact
    if (node_type === 'hero' || node_type === 'cta') {
      base_impact *= 1.5;
    }

    return Math.min(base_impact * magnitude, 1.0);
  }

  /**
   * Categorize drift level
   */
  private categorizeDrift(
    drift_value: number
  ): 'minor' | 'moderate' | 'significant' | 'severe' {
    if (drift_value < DRIFT_THRESHOLDS.minor) {
      return 'minor';
    } else if (drift_value < DRIFT_THRESHOLDS.moderate) {
      return 'moderate';
    } else if (drift_value < DRIFT_THRESHOLDS.significant) {
      return 'significant';
    } else {
      return 'severe';
    }
  }

  /**
   * Determine if branching should occur
   */
  private shouldBranch(
    drift_value: number,
    category: 'minor' | 'moderate' | 'significant' | 'severe'
  ): boolean {
    // Auto-branch on severe drift
    if (category === 'severe') {
      return true;
    }

    // Consider branching on significant drift
    if (category === 'significant' && drift_value > DRIFT_THRESHOLDS.significant) {
      return true;
    }

    return false;
  }

  /**
   * Generate branch reason
   */
  private getBranchReason(
    drift_value: number,
    category: string,
    changed_nodes: SemanticDrift['changed_nodes']
  ): string {
    const drift_percent = (drift_value * 100).toFixed(1);
    const node_count = changed_nodes.length;

    const high_impact_changes = changed_nodes.filter(
      (c) => c.semantic_impact > 0.4
    ).length;

    if (high_impact_changes > 0) {
      return `Severe semantic drift detected (${drift_percent}% drift, ${high_impact_changes} high-impact changes across ${node_count} nodes). Auto-branching to preserve design lineage.`;
    }

    return `Significant semantic drift detected (${drift_percent}% drift across ${node_count} nodes). Auto-branching to track divergent evolution.`;
  }

  /**
   * Track drift timeline across multiple variations
   */
  trackTimeline(variations: GeneratedVariation[]): {
    timestamps: number[];
    drift_values: number[];
    average_drift: number;
    max_drift: number;
    drift_velocity: number;
  } {
    const sorted = [...variations].sort((a, b) => a.created_at - b.created_at);

    const timestamps = sorted.map((v) => v.created_at);
    const drift_values = sorted.map((v) => v.semantic_drift);

    const average_drift =
      drift_values.reduce((sum, d) => sum + d, 0) / drift_values.length;
    const max_drift = Math.max(...drift_values);

    // Calculate drift velocity (rate of drift increase)
    let drift_velocity = 0;
    if (drift_values.length > 1) {
      const time_span = timestamps[timestamps.length - 1] - timestamps[0];
      const drift_span = drift_values[drift_values.length - 1] - drift_values[0];
      drift_velocity = time_span > 0 ? drift_span / (time_span / 1000) : 0; // drift per second
    }

    return {
      timestamps,
      drift_values,
      average_drift,
      max_drift,
      drift_velocity
    };
  }
}

// Singleton instance
export const driftDetector = new DriftDetector();
