/**
 * Week 5: Style DNA Encoding - Seeded Random Number Generator
 *
 * Deterministic RNG for perfect undo/redo and provenance.
 * Based on Mulberry32 algorithm for speed and quality.
 */

/**
 * Seeded Random Number Generator
 * Provides deterministic pseudo-random numbers for reproducibility
 */
export class SeededRNG {
  private state: number;
  private readonly initial_seed: number;

  constructor(seed: number = Date.now()) {
    this.initial_seed = seed;
    this.state = seed;
  }

  /**
   * Generate next random number in [0, 1)
   * Uses Mulberry32 algorithm - fast and high quality
   */
  next(): number {
    this.state |= 0;
    this.state = (this.state + 0x6d2b79f5) | 0;
    let t = Math.imul(this.state ^ (this.state >>> 15), 1 | this.state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /**
   * Generate random integer in [min, max]
   */
  nextInt(min: number, max: number): number {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  /**
   * Generate random float in [min, max)
   */
  nextFloat(min: number, max: number): number {
    return this.next() * (max - min) + min;
  }

  /**
   * Generate random boolean with given probability
   */
  nextBoolean(probability: number = 0.5): boolean {
    return this.next() < probability;
  }

  /**
   * Generate random element from array
   */
  choice<T>(array: T[]): T {
    return array[this.nextInt(0, array.length - 1)];
  }

  /**
   * Shuffle array in-place (Fisher-Yates)
   */
  shuffle<T>(array: T[]): T[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = this.nextInt(0, i);
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  /**
   * Generate Gaussian (normal) random number
   * Uses Box-Muller transform
   */
  nextGaussian(mean: number = 0, stdDev: number = 1): number {
    const u1 = this.next();
    const u2 = this.next();
    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return z0 * stdDev + mean;
  }

  /**
   * Reset to initial seed
   */
  reset(): void {
    this.state = this.initial_seed;
  }

  /**
   * Get current state for serialization
   */
  getState(): number {
    return this.state;
  }

  /**
   * Restore state from serialization
   */
  setState(state: number): void {
    this.state = state;
  }

  /**
   * Create a new RNG with a derived seed
   * Useful for creating independent streams
   */
  derive(offset: number): SeededRNG {
    return new SeededRNG(this.initial_seed + offset);
  }

  /**
   * Clone current RNG state
   */
  clone(): SeededRNG {
    const cloned = new SeededRNG(this.initial_seed);
    cloned.setState(this.state);
    return cloned;
  }
}

/**
 * Global RNG instance for convenience
 * Can be seeded for deterministic behavior
 */
export const globalRNG = new SeededRNG();

/**
 * Seed the global RNG
 */
export function seedGlobalRNG(seed: number): void {
  globalRNG.setState(seed);
}
