/**
 * Week 5: Style DNA Encoding - Worker Pool Manager
 *
 * Manages pool of Web Workers for parallel DNA encoding.
 * Distributes work and handles responses.
 */

import { StyleDNAConfig } from './config';
import type { WorkerMessage, WorkerResponse } from './workers/dna-worker';

/**
 * Worker Task - Queued work item
 */
interface WorkerTask {
  task_id: string;
  message: WorkerMessage;
  resolve: (response: WorkerResponse) => void;
  reject: (error: Error) => void;
  created_at: number;
}

/**
 * Worker Pool Manager
 * Manages multiple Web Workers for parallel processing
 */
export class WorkerPool {
  private workers: Worker[] = [];
  private available_workers: Worker[] = [];
  private task_queue: WorkerTask[] = [];
  private pending_tasks: Map<Worker, WorkerTask> = new Map();

  private pool_size: number;
  private worker_url: string;

  constructor(pool_size: number = StyleDNAConfig.performance.worker_pool_size) {
    this.pool_size = pool_size;
    this.worker_url = new URL('./workers/dna-worker.ts', import.meta.url).href;
  }

  /**
   * Initialize worker pool
   */
  async initialize(): Promise<void> {
    for (let i = 0; i < this.pool_size; i++) {
      const worker = new Worker(this.worker_url, { type: 'module' });
      worker.onmessage = (event) => this.handleWorkerMessage(worker, event);
      worker.onerror = (error) => this.handleWorkerError(worker, error);

      this.workers.push(worker);
      this.available_workers.push(worker);
    }

    console.log(`✅ Worker pool initialized: ${this.pool_size} workers`);
  }

  /**
   * Submit task to worker pool
   */
  async submit<T extends WorkerResponse>(message: WorkerMessage): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const task: WorkerTask = {
        task_id: this.generateTaskId(),
        message,
        resolve: resolve as (response: WorkerResponse) => void,
        reject,
        created_at: Date.now()
      };

      this.task_queue.push(task);
      this.processQueue();
    });
  }

  /**
   * Process task queue
   */
  private processQueue(): void {
    while (this.task_queue.length > 0 && this.available_workers.length > 0) {
      const task = this.task_queue.shift();
      const worker = this.available_workers.shift();

      if (!task || !worker) break;

      this.pending_tasks.set(worker, task);
      worker.postMessage(task.message);
    }
  }

  /**
   * Handle worker message
   */
  private handleWorkerMessage(worker: Worker, event: MessageEvent<WorkerResponse>): void {
    const task = this.pending_tasks.get(worker);

    if (!task) {
      console.warn('Received message from worker with no pending task');
      return;
    }

    // Remove from pending
    this.pending_tasks.delete(worker);
    this.available_workers.push(worker);

    // Handle response
    if (event.data.type === 'error') {
      task.reject(new Error(event.data.payload.error));
    } else {
      task.resolve(event.data);
    }

    // Process next task
    this.processQueue();
  }

  /**
   * Handle worker error
   */
  private handleWorkerError(worker: Worker, error: ErrorEvent): void {
    const task = this.pending_tasks.get(worker);

    if (task) {
      task.reject(new Error(error.message));
      this.pending_tasks.delete(worker);
    }

    // Worker may be corrupted, restart it
    this.restartWorker(worker);
  }

  /**
   * Restart a worker
   */
  private restartWorker(old_worker: Worker): void {
    // Terminate old worker
    old_worker.terminate();

    // Remove from available workers
    const index = this.available_workers.indexOf(old_worker);
    if (index > -1) {
      this.available_workers.splice(index, 1);
    }

    // Create new worker
    const new_worker = new Worker(this.worker_url, { type: 'module' });
    new_worker.onmessage = (event) => this.handleWorkerMessage(new_worker, event);
    new_worker.onerror = (error) => this.handleWorkerError(new_worker, error);

    // Replace in workers array
    const worker_index = this.workers.indexOf(old_worker);
    if (worker_index > -1) {
      this.workers[worker_index] = new_worker;
    }

    this.available_workers.push(new_worker);

    console.warn('Worker restarted after error');
  }

  /**
   * Terminate all workers
   */
  terminate(): void {
    for (const worker of this.workers) {
      worker.terminate();
    }

    this.workers = [];
    this.available_workers = [];
    this.task_queue = [];
    this.pending_tasks.clear();

    console.log('Worker pool terminated');
  }

  /**
   * Get pool statistics
   */
  getStats(): {
    total_workers: number;
    available_workers: number;
    queued_tasks: number;
    pending_tasks: number;
  } {
    return {
      total_workers: this.workers.length,
      available_workers: this.available_workers.length,
      queued_tasks: this.task_queue.length,
      pending_tasks: this.pending_tasks.size
    };
  }

  /**
   * Generate task ID
   */
  private generateTaskId(): string {
    return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Wait for all pending tasks to complete
   */
  async waitForCompletion(): Promise<void> {
    while (this.pending_tasks.size > 0 || this.task_queue.length > 0) {
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  }
}

/**
 * Global worker pool instance
 */
export const globalWorkerPool = new WorkerPool();
