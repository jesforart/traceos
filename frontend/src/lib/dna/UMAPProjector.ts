/**
 * Week 5: Style DNA Encoding - UMAP Projector
 *
 * Dimensionality reduction for DNA visualization.
 * Projects high-dimensional DNA into 3D space.
 */

import { StyleDNAConfig } from './config';
import type { UMAPProjection, StrokeDNA, ImageDNA, TemporalDNA } from './types';
import { ulid } from '../../utils/ulid';
import { globalDNADistanceCalculator } from './DNADistanceCalculator';

/**
 * UMAP Projector
 * Reduces high-dimensional DNA to 3D for visualization
 */
export class UMAPProjector {
  private n_neighbors: number;
  private min_dist: number;
  private n_components: number;
  private metric: 'euclidean' | 'cosine' | 'manhattan';

  constructor(
    n_neighbors: number = StyleDNAConfig.umap.n_neighbors,
    min_dist: number = StyleDNAConfig.umap.min_dist,
    n_components: number = StyleDNAConfig.umap.n_components,
    metric: 'euclidean' | 'cosine' | 'manhattan' = StyleDNAConfig.umap.metric
  ) {
    this.n_neighbors = n_neighbors;
    this.min_dist = min_dist;
    this.n_components = n_components;
    this.metric = metric;
  }

  /**
   * Project stroke DNAs to 3D space
   */
  async projectStrokeDNAs(stroke_dnas: StrokeDNA[]): Promise<UMAPProjection> {
    const start_time = performance.now();

    const features_matrix = stroke_dnas.map((dna) => dna.features);
    const coordinates = await this.project(features_matrix);

    const computation_time_ms = performance.now() - start_time;

    return {
      projection_id: ulid(),
      source_dnas: stroke_dnas.map((dna) => dna.dna_id),
      coordinates,
      n_neighbors: this.n_neighbors,
      min_dist: this.min_dist,
      metric: this.metric,
      computed_at: Date.now(),
      computation_time_ms
    };
  }

  /**
   * Project image DNAs to 3D space
   */
  async projectImageDNAs(image_dnas: ImageDNA[]): Promise<UMAPProjection> {
    const start_time = performance.now();

    const features_matrix = image_dnas.map((dna) => dna.features);
    const coordinates = await this.project(features_matrix);

    const computation_time_ms = performance.now() - start_time;

    return {
      projection_id: ulid(),
      source_dnas: image_dnas.map((dna) => dna.dna_id),
      coordinates,
      n_neighbors: this.n_neighbors,
      min_dist: this.min_dist,
      metric: this.metric,
      computed_at: Date.now(),
      computation_time_ms
    };
  }

  /**
   * Project temporal DNAs to 3D space
   */
  async projectTemporalDNAs(temporal_dnas: TemporalDNA[]): Promise<UMAPProjection> {
    const start_time = performance.now();

    const features_matrix = temporal_dnas.map((dna) => dna.features);
    const coordinates = await this.project(features_matrix);

    const computation_time_ms = performance.now() - start_time;

    return {
      projection_id: ulid(),
      source_dnas: temporal_dnas.map((dna) => dna.dna_id),
      coordinates,
      n_neighbors: this.n_neighbors,
      min_dist: this.min_dist,
      metric: this.metric,
      computed_at: Date.now(),
      computation_time_ms
    };
  }

  /**
   * Core UMAP projection algorithm (simplified)
   * In production, would use umap-js or similar library
   */
  private async project(
    features_matrix: Float32Array[]
  ): Promise<Array<{ x: number; y: number; z: number }>> {
    if (features_matrix.length === 0) {
      return [];
    }

    // Step 1: Compute distance matrix
    const distance_matrix = this.computeDistanceMatrix(features_matrix);

    // Step 2: Build k-NN graph
    const knn_graph = this.buildKNNGraph(distance_matrix);

    // Step 3: Initialize embedding (random)
    let embedding = this.initializeEmbedding(features_matrix.length);

    // Step 4: Optimize embedding (simplified gradient descent)
    embedding = this.optimizeEmbedding(embedding, knn_graph, 100); // 100 iterations

    return embedding;
  }

  /**
   * Compute pairwise distance matrix
   */
  private computeDistanceMatrix(features_matrix: Float32Array[]): number[][] {
    const n = features_matrix.length;
    const distance_matrix: number[][] = [];

    for (let i = 0; i < n; i++) {
      distance_matrix[i] = [];
      for (let j = 0; j < n; j++) {
        if (i === j) {
          distance_matrix[i][j] = 0;
        } else {
          const distance = globalDNADistanceCalculator.calculateDistance(
            features_matrix[i],
            features_matrix[j]
          );
          distance_matrix[i][j] = distance;
        }
      }
    }

    return distance_matrix;
  }

  /**
   * Build k-NN graph
   */
  private buildKNNGraph(
    distance_matrix: number[][]
  ): Array<Array<{ index: number; weight: number }>> {
    const n = distance_matrix.length;
    const knn_graph: Array<Array<{ index: number; weight: number }>> = [];

    for (let i = 0; i < n; i++) {
      // Find k nearest neighbors
      const distances = distance_matrix[i]
        .map((dist, idx) => ({ index: idx, distance: dist }))
        .filter((item) => item.index !== i);

      distances.sort((a, b) => a.distance - b.distance);
      const neighbors = distances.slice(0, this.n_neighbors);

      // Convert to weights (closer = higher weight)
      const weights = neighbors.map(({ index, distance }) => ({
        index,
        weight: Math.exp(-distance) // Exponential decay
      }));

      knn_graph[i] = weights;
    }

    return knn_graph;
  }

  /**
   * Initialize embedding randomly
   */
  private initializeEmbedding(
    n_points: number
  ): Array<{ x: number; y: number; z: number }> {
    const embedding: Array<{ x: number; y: number; z: number }> = [];

    for (let i = 0; i < n_points; i++) {
      embedding.push({
        x: (Math.random() - 0.5) * 10,
        y: (Math.random() - 0.5) * 10,
        z: (Math.random() - 0.5) * 10
      });
    }

    return embedding;
  }

  /**
   * Optimize embedding (simplified)
   */
  private optimizeEmbedding(
    embedding: Array<{ x: number; y: number; z: number }>,
    knn_graph: Array<Array<{ index: number; weight: number }>>,
    iterations: number
  ): Array<{ x: number; y: number; z: number }> {
    const learning_rate = 0.1;

    for (let iter = 0; iter < iterations; iter++) {
      // Gradient descent step
      const gradients = embedding.map(() => ({ x: 0, y: 0, z: 0 }));

      // Attractive forces (pull neighbors together)
      for (let i = 0; i < embedding.length; i++) {
        for (const { index: j, weight } of knn_graph[i]) {
          const dx = embedding[j].x - embedding[i].x;
          const dy = embedding[j].y - embedding[i].y;
          const dz = embedding[j].z - embedding[i].z;

          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
          const force = weight * (dist - this.min_dist);

          if (dist > 0) {
            gradients[i].x += (force * dx) / dist;
            gradients[i].y += (force * dy) / dist;
            gradients[i].z += (force * dz) / dist;
          }
        }
      }

      // Repulsive forces (push non-neighbors apart)
      for (let i = 0; i < embedding.length; i++) {
        for (let j = i + 1; j < embedding.length; j++) {
          // Check if j is a neighbor of i
          const is_neighbor = knn_graph[i].some((n) => n.index === j);
          if (is_neighbor) continue;

          const dx = embedding[j].x - embedding[i].x;
          const dy = embedding[j].y - embedding[i].y;
          const dz = embedding[j].z - embedding[i].z;

          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (dist < this.min_dist * 5) {
            // Repel if too close
            const force = -0.1 / (dist + 0.1);

            gradients[i].x += (force * dx) / dist;
            gradients[i].y += (force * dy) / dist;
            gradients[i].z += (force * dz) / dist;

            gradients[j].x -= (force * dx) / dist;
            gradients[j].y -= (force * dy) / dist;
            gradients[j].z -= (force * dz) / dist;
          }
        }
      }

      // Apply gradients
      for (let i = 0; i < embedding.length; i++) {
        embedding[i].x += gradients[i].x * learning_rate;
        embedding[i].y += gradients[i].y * learning_rate;
        embedding[i].z += gradients[i].z * learning_rate;
      }
    }

    return embedding;
  }

  /**
   * Get recommended parameters for dataset size
   */
  static getRecommendedParams(dataset_size: number): {
    n_neighbors: number;
    min_dist: number;
  } {
    if (dataset_size < 50) {
      return { n_neighbors: 5, min_dist: 0.1 };
    } else if (dataset_size < 200) {
      return { n_neighbors: 15, min_dist: 0.1 };
    } else if (dataset_size < 1000) {
      return { n_neighbors: 30, min_dist: 0.05 };
    } else {
      return { n_neighbors: 50, min_dist: 0.01 };
    }
  }
}

/**
 * Global UMAP projector instance
 */
export const globalUMAPProjector = new UMAPProjector();
