/**
 * Week 5: Style DNA Encoding - Two-Pass Pipeline
 *
 * Hot path: <16ms real-time encoding (StrokeDNA)
 * Cold path: Async background encoding (ImageDNA, TemporalDNA)
 */

import type {
  StrokeDNA,
  ImageDNA,
  TemporalDNA,
  DNASession,
  DNATier,
  ArtistContext
} from './types';
import { StyleDNAConfig } from './config';
import { ulid } from '../../utils/ulid';

/**
 * Pipeline Result - Hot and Cold path results
 */
export interface PipelineResult {
  hot_path: {
    stroke_dna: StrokeDNA;
    encoding_time_ms: number;
    success: boolean;
  };
  cold_path: {
    image_dna?: ImageDNA;
    temporal_dna?: TemporalDNA;
    encoding_time_ms?: number;
    pending: boolean;
  };
}

/**
 * Pipeline Performance Metrics
 */
export interface PipelineMetrics {
  total_encodings: number;
  hot_path_violations: number; // Times we exceeded 16ms
  avg_hot_path_time_ms: number;
  avg_cold_path_time_ms: number;
  worker_utilization: number; // 0-1
}

/**
 * DNA Encoding Pipeline
 * Manages hot/cold path encoding with performance budgets
 */
export class DNAPipeline {
  private metrics: PipelineMetrics = {
    total_encodings: 0,
    hot_path_violations: 0,
    avg_hot_path_time_ms: 0,
    avg_cold_path_time_ms: 0,
    worker_utilization: 0
  };

  private hot_path_times: number[] = [];
  private cold_path_times: number[] = [];

  private worker_queue: Array<() => Promise<void>> = [];
  private workers_busy = 0;
  private max_workers = StyleDNAConfig.performance.worker_pool_size;

  /**
   * Encode stroke - Hot path (<16ms target)
   */
  async encodeStroke(
    stroke_data: any,
    context: ArtistContext,
    encoder: any
  ): Promise<PipelineResult> {
    const start_time = performance.now();

    // Hot path: StrokeDNA encoding
    let stroke_dna: StrokeDNA;
    try {
      stroke_dna = encoder.encodeSync(stroke_data, context);
    } catch (error) {
      console.error('Hot path encoding failed:', error);
      throw error;
    }

    const hot_time = performance.now() - start_time;

    // Track metrics
    this.hot_path_times.push(hot_time);
    this.metrics.total_encodings++;

    if (hot_time > StyleDNAConfig.performance.hot_path_budget_ms) {
      this.metrics.hot_path_violations++;
      console.warn(`⚠️  Hot path violation: ${hot_time.toFixed(2)}ms (budget: 16ms)`);
    }

    // Update average
    this.metrics.avg_hot_path_time_ms =
      this.hot_path_times.reduce((a, b) => a + b, 0) / this.hot_path_times.length;

    // Cold path: Schedule background encoding
    const cold_path_promise = this.scheduleColdPath(stroke_data, context);

    return {
      hot_path: {
        stroke_dna,
        encoding_time_ms: hot_time,
        success: true
      },
      cold_path: {
        pending: true
      }
    };
  }

  /**
   * Schedule cold path encoding (async)
   */
  private async scheduleColdPath(stroke_data: any, context: ArtistContext): Promise<void> {
    // Add to worker queue
    this.worker_queue.push(async () => {
      const start_time = performance.now();

      // Simulate cold path encoding
      // In real implementation, this would:
      // 1. Capture canvas snapshot
      // 2. Send to Web Worker for ImageDNA encoding
      // 3. Update TemporalDNA
      await this.simulateColdPathWork();

      const cold_time = performance.now() - start_time;
      this.cold_path_times.push(cold_time);

      this.metrics.avg_cold_path_time_ms =
        this.cold_path_times.reduce((a, b) => a + b, 0) / this.cold_path_times.length;
    });

    // Process queue
    this.processWorkerQueue();
  }

  /**
   * Process worker queue
   */
  private async processWorkerQueue(): Promise<void> {
    while (this.worker_queue.length > 0 && this.workers_busy < this.max_workers) {
      const task = this.worker_queue.shift();
      if (!task) break;

      this.workers_busy++;
      this.updateWorkerUtilization();

      task()
        .catch((error) => console.error('Cold path error:', error))
        .finally(() => {
          this.workers_busy--;
          this.updateWorkerUtilization();
          this.processWorkerQueue(); // Process next task
        });
    }
  }

  /**
   * Update worker utilization metric
   */
  private updateWorkerUtilization(): void {
    this.metrics.worker_utilization = this.workers_busy / this.max_workers;
  }

  /**
   * Simulate cold path work (placeholder)
   */
  private async simulateColdPathWork(): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, 100));
  }

  /**
   * Get pipeline metrics
   */
  getMetrics(): PipelineMetrics {
    return { ...this.metrics };
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary(): string {
    const violation_rate =
      this.metrics.total_encodings > 0
        ? (this.metrics.hot_path_violations / this.metrics.total_encodings) * 100
        : 0;

    return `
Pipeline Performance:
- Total encodings: ${this.metrics.total_encodings}
- Hot path avg: ${this.metrics.avg_hot_path_time_ms.toFixed(2)}ms
- Cold path avg: ${this.metrics.avg_cold_path_time_ms.toFixed(2)}ms
- Budget violations: ${this.metrics.hot_path_violations} (${violation_rate.toFixed(1)}%)
- Worker utilization: ${(this.metrics.worker_utilization * 100).toFixed(1)}%
    `.trim();
  }

  /**
   * Reset metrics
   */
  resetMetrics(): void {
    this.metrics = {
      total_encodings: 0,
      hot_path_violations: 0,
      avg_hot_path_time_ms: 0,
      avg_cold_path_time_ms: 0,
      worker_utilization: 0
    };
    this.hot_path_times = [];
    this.cold_path_times = [];
  }

  /**
   * Check if hot path is performing well
   */
  isHotPathHealthy(): boolean {
    return (
      this.metrics.avg_hot_path_time_ms < StyleDNAConfig.performance.hot_path_budget_ms &&
      this.metrics.hot_path_violations < this.metrics.total_encodings * 0.05
    ); // <5% violation rate
  }
}

/**
 * Global pipeline instance
 */
export const globalDNAPipeline = new DNAPipeline();
