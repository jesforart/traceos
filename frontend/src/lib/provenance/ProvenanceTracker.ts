/**
 * Week 3: Design Variation Engine - Provenance Tracker
 *
 * Tracks complete design lineage with automatic branching.
 * Biological evolution metaphor for design history.
 */

import type { BaseSchema } from '../schema/types';
import type { GeneratedVariation, SemanticDrift } from '../variation/types';
import type {
  ProvenanceNode,
  DesignLineage,
  DesignBranch,
  DesignChange,
  AutoBranchEvent
} from './types';
import { driftDetector } from '../variation/DriftDetector';
import { ulid } from '../../utils/ulid';

const DB_NAME = 'TraceOS_ProvenanceStore';
const DB_VERSION = 1;
const LINEAGE_STORE = 'lineages';
const NODES_STORE = 'nodes';
const BRANCHES_STORE = 'branches';

/**
 * Initialize IndexedDB database
 */
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      if (!db.objectStoreNames.contains(LINEAGE_STORE)) {
        db.createObjectStore(LINEAGE_STORE, { keyPath: 'root_schema_id' });
      }

      if (!db.objectStoreNames.contains(NODES_STORE)) {
        const nodeStore = db.createObjectStore(NODES_STORE, { keyPath: 'node_id' });
        nodeStore.createIndex('schema_id', 'schema_id', { unique: false });
        nodeStore.createIndex('parent_id', 'parent_id', { unique: false });
      }

      if (!db.objectStoreNames.contains(BRANCHES_STORE)) {
        const branchStore = db.createObjectStore(BRANCHES_STORE, {
          keyPath: 'branch_id'
        });
        branchStore.createIndex('branch_point_id', 'branch_point_id', {
          unique: false
        });
      }
    };
  });
}

/**
 * Provenance Tracker - Design lineage management
 */
export class ProvenanceTracker {
  /**
   * Create a new lineage
   */
  async createLineage(root_schema: BaseSchema): Promise<DesignLineage> {
    const lineage: DesignLineage = {
      root_schema_id: root_schema.schema_id,
      created_at: Date.now(),
      nodes: {},
      branches: [],
      stats: {
        total_variations: 0,
        total_branches: 0,
        max_depth: 0,
        total_changes: 0
      }
    };

    // Create root node
    const root_node: ProvenanceNode = {
      node_id: ulid(),
      schema_id: root_schema.schema_id,
      created_at: Date.now(),
      children_ids: [],
      is_branch_point: false,
      changes: [],
      tags: ['root']
    };

    lineage.nodes[root_node.node_id] = root_node;

    // Save to IndexedDB
    await this.saveLineage(lineage);
    await this.saveNode(root_node);

    console.log(`🌳 Created lineage for schema: ${root_schema.schema_id}`);

    return lineage;
  }

  /**
   * Record a variation in the lineage
   */
  async recordVariation(
    parent_schema: BaseSchema,
    variation: GeneratedVariation
  ): Promise<{
    node: ProvenanceNode;
    auto_branched: boolean;
    branch?: DesignBranch;
  }> {
    // Detect drift
    const drift = driftDetector.detect(parent_schema, variation.schema);

    // Find parent node
    const parent_node = await this.findNodeBySchemaId(parent_schema.schema_id);
    if (!parent_node) {
      throw new Error(`Parent node not found for schema: ${parent_schema.schema_id}`);
    }

    // Extract changes
    const changes: DesignChange[] = drift.changed_nodes.map((change) => ({
      change_id: ulid(),
      change_type: 'modify',
      node_id: change.node_id,
      property: change.property,
      before_value: change.original_value,
      after_value: change.new_value,
      caused_by: 'modifier',
      semantic_impact: change.semantic_impact
    }));

    // Create variation node
    const variation_node: ProvenanceNode = {
      node_id: ulid(),
      schema_id: variation.variation_id,
      created_at: variation.created_at,
      parent_id: parent_node.node_id,
      children_ids: [],
      is_branch_point: false,
      changes,
      tags: []
    };

    // Update parent
    parent_node.children_ids.push(variation_node.node_id);

    let auto_branched = false;
    let branch: DesignBranch | undefined;

    // Check if we should auto-branch
    if (drift.should_branch) {
      branch = await this.createBranch(
        parent_node,
        variation_node,
        'drift_threshold',
        drift
      );
      auto_branched = true;

      console.log(`🌿 Auto-branched at node ${parent_node.node_id}: ${drift.branch_reason}`);
    }

    // Save everything
    await this.saveNode(parent_node);
    await this.saveNode(variation_node);
    if (branch) {
      await this.saveBranch(branch);
    }

    // Update lineage stats
    await this.updateLineageStats(parent_schema.schema_id, variation_node);

    return {
      node: variation_node,
      auto_branched,
      branch
    };
  }

  /**
   * Create a branch
   */
  private async createBranch(
    branch_point: ProvenanceNode,
    first_descendant: ProvenanceNode,
    reason: 'drift_threshold' | 'manual' | 'experiment' | 'mutation',
    drift?: SemanticDrift
  ): Promise<DesignBranch> {
    // Mark branch point
    branch_point.is_branch_point = true;
    branch_point.branch_reason = drift?.branch_reason;

    const branch: DesignBranch = {
      branch_id: ulid(),
      branch_point_id: branch_point.node_id,
      created_at: Date.now(),
      reason,
      drift_value: drift?.drift_value,
      descendant_ids: [first_descendant.node_id],
      tags: []
    };

    return branch;
  }

  /**
   * Find a node by schema ID
   */
  private async findNodeBySchemaId(schema_id: string): Promise<ProvenanceNode | null> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([NODES_STORE], 'readonly');
      const store = tx.objectStore(NODES_STORE);
      const index = store.index('schema_id');
      const request = index.get(schema_id);

      request.onsuccess = () => {
        resolve(request.result || null);
      };
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Save lineage
   */
  private async saveLineage(lineage: DesignLineage): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([LINEAGE_STORE], 'readwrite');
      const store = tx.objectStore(LINEAGE_STORE);
      const request = store.put(lineage);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Save node
   */
  private async saveNode(node: ProvenanceNode): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([NODES_STORE], 'readwrite');
      const store = tx.objectStore(NODES_STORE);
      const request = store.put(node);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Save branch
   */
  private async saveBranch(branch: DesignBranch): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([BRANCHES_STORE], 'readwrite');
      const store = tx.objectStore(BRANCHES_STORE);
      const request = store.put(branch);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Update lineage statistics
   */
  private async updateLineageStats(
    root_schema_id: string,
    new_node: ProvenanceNode
  ): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([LINEAGE_STORE], 'readwrite');
      const store = tx.objectStore(LINEAGE_STORE);
      const request = store.get(root_schema_id);

      request.onsuccess = () => {
        const lineage = request.result as DesignLineage;
        if (lineage) {
          lineage.stats.total_variations++;
          lineage.stats.total_changes += new_node.changes.length;

          // Calculate depth
          const depth = this.calculateDepth(lineage, new_node.node_id);
          lineage.stats.max_depth = Math.max(lineage.stats.max_depth, depth);

          store.put(lineage);
        }
      };

      request.onerror = () => reject(request.error);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
    });
  }

  /**
   * Calculate node depth
   */
  private calculateDepth(lineage: DesignLineage, node_id: string): number {
    let depth = 0;
    let current_id: string | undefined = node_id;

    while (current_id) {
      const node: ProvenanceNode | undefined = lineage.nodes[current_id];
      if (!node || !node.parent_id) break;
      depth++;
      current_id = node.parent_id;
    }

    return depth;
  }

  /**
   * Get lineage for a schema
   */
  async getLineage(root_schema_id: string): Promise<DesignLineage | null> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([LINEAGE_STORE], 'readonly');
      const store = tx.objectStore(LINEAGE_STORE);
      const request = store.get(root_schema_id);

      request.onsuccess = () => {
        resolve(request.result || null);
      };
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }
}

// Singleton instance
export const provenanceTracker = new ProvenanceTracker();
