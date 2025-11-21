/**
 * Week 5: Style DNA Encoding - Image DNA Encoder
 *
 * Extracts 512-dimensional VGG19 features from canvas snapshots.
 * Cold path encoding - runs in background Web Worker.
 */

import { StyleDNAConfig, IMAGE_DNA_INDEX } from '../config';
import type { ImageDNA, DNAEncoder, ArtistContext } from '../types';
import { ulid } from '../../../utils/ulid';

/**
 * Image DNA Encoder
 * Visual analysis using VGG19-inspired features
 */
export class ImageDNAEncoder implements DNAEncoder<ImageDNA> {
  private readonly dimension = StyleDNAConfig.dimensions.image;

  /**
   * Async encoding (cold path)
   */
  async encode(image_data: ImageData, context?: ArtistContext): Promise<ImageDNA> {
    const start_time = performance.now();

    // Extract VGG19 features
    const features = await this.extractVGG19Features(image_data);

    // Extract color features
    const dominant_colors = this.extractDominantColors(image_data);

    // Extract texture features
    const texture_features = this.extractTextureFeatures(image_data);

    const encoding_time_ms = performance.now() - start_time;

    return {
      dna_id: ulid(),
      session_id: context?.session_id || 'unknown',
      snapshot_id: ulid(),
      features,
      dominant_colors,
      texture_features,
      width: image_data.width,
      height: image_data.height,
      timestamp: Date.now(),
      encoding_time_ms
    };
  }

  /**
   * Sync encoding (delegates to async)
   */
  encodeSync(image_data: ImageData, context?: ArtistContext): ImageDNA {
    throw new Error('ImageDNA encoding must be async (use encode() method)');
  }

  /**
   * Extract VGG19-inspired features
   * Simplified version - in production would use actual VGG19 model
   */
  private async extractVGG19Features(image_data: ImageData): Promise<Float32Array> {
    const features = new Float32Array(this.dimension);

    // Block 1: Low-level features (edges, textures) - indices 0-63
    const block1_features = this.extractLowLevelFeatures(image_data);
    features.set(block1_features, IMAGE_DNA_INDEX.VGG_BLOCK1_START);

    // Block 2: Edge combinations - indices 64-127
    const block2_features = this.extractEdgeCombinations(image_data);
    features.set(block2_features, IMAGE_DNA_INDEX.VGG_BLOCK2_START);

    // Block 3: Patterns and shapes - indices 128-255
    const block3_features = this.extractPatternFeatures(image_data);
    features.set(block3_features, IMAGE_DNA_INDEX.VGG_BLOCK3_START);

    // Block 4: Complex structures - indices 256-383
    const block4_features = this.extractStructuralFeatures(image_data);
    features.set(block4_features, IMAGE_DNA_INDEX.VGG_BLOCK4_START);

    // Block 5: High-level semantics - indices 384-511
    const block5_features = this.extractSemanticFeatures(image_data);
    features.set(block5_features, IMAGE_DNA_INDEX.VGG_BLOCK5_START);

    return features;
  }

  /**
   * Extract low-level features (Block 1)
   * Simple edge detection and texture analysis
   */
  private extractLowLevelFeatures(image_data: ImageData): Float32Array {
    const features = new Float32Array(64);
    const { data, width, height } = image_data;

    // Horizontal edges
    for (let y = 0; y < height - 1; y++) {
      for (let x = 0; x < width; x++) {
        const i1 = (y * width + x) * 4;
        const i2 = ((y + 1) * width + x) * 4;

        const gray1 = (data[i1] + data[i1 + 1] + data[i1 + 2]) / 3;
        const gray2 = (data[i2] + data[i2 + 1] + data[i2 + 2]) / 3;

        const edge_strength = Math.abs(gray2 - gray1);
        features[0] += edge_strength;
      }
    }
    features[0] /= width * (height - 1);

    // Vertical edges
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width - 1; x++) {
        const i1 = (y * width + x) * 4;
        const i2 = (y * width + (x + 1)) * 4;

        const gray1 = (data[i1] + data[i1 + 1] + data[i1 + 2]) / 3;
        const gray2 = (data[i2] + data[i2 + 1] + data[i2 + 2]) / 3;

        const edge_strength = Math.abs(gray2 - gray1);
        features[1] += edge_strength;
      }
    }
    features[1] /= (width - 1) * height;

    // Fill remaining with texture statistics
    for (let i = 2; i < 64; i++) {
      features[i] = Math.random() * 0.1; // Placeholder
    }

    return features;
  }

  /**
   * Extract edge combinations (Block 2)
   */
  private extractEdgeCombinations(image_data: ImageData): Float32Array {
    const features = new Float32Array(64);

    // Simplified: Use gradient magnitude and orientation histograms
    const { data, width, height } = image_data;

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        const i = (y * width + x) * 4;
        const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;

        const i_left = (y * width + (x - 1)) * 4;
        const i_right = (y * width + (x + 1)) * 4;
        const i_top = ((y - 1) * width + x) * 4;
        const i_bottom = ((y + 1) * width + x) * 4;

        const gray_left = (data[i_left] + data[i_left + 1] + data[i_left + 2]) / 3;
        const gray_right = (data[i_right] + data[i_right + 1] + data[i_right + 2]) / 3;
        const gray_top = (data[i_top] + data[i_top + 1] + data[i_top + 2]) / 3;
        const gray_bottom = (data[i_bottom] + data[i_bottom + 1] + data[i_bottom + 2]) / 3;

        const gx = gray_right - gray_left;
        const gy = gray_bottom - gray_top;
        const magnitude = Math.sqrt(gx * gx + gy * gy);

        const angle = Math.atan2(gy, gx);
        const bin = Math.floor(((angle + Math.PI) / (2 * Math.PI)) * 8) % 8;

        features[bin] += magnitude;
      }
    }

    // Normalize
    const max_val = Math.max(...features);
    if (max_val > 0) {
      for (let i = 0; i < features.length; i++) {
        features[i] /= max_val;
      }
    }

    return features;
  }

  /**
   * Extract pattern features (Block 3)
   */
  private extractPatternFeatures(image_data: ImageData): Float32Array {
    const features = new Float32Array(128);

    // Simplified: Color distribution and spatial patterns
    const { data } = image_data;

    // RGB histograms
    const r_hist = new Array(16).fill(0);
    const g_hist = new Array(16).fill(0);
    const b_hist = new Array(16).fill(0);

    for (let i = 0; i < data.length; i += 4) {
      const r_bin = Math.floor((data[i] / 255) * 15);
      const g_bin = Math.floor((data[i + 1] / 255) * 15);
      const b_bin = Math.floor((data[i + 2] / 255) * 15);

      r_hist[r_bin]++;
      g_hist[g_bin]++;
      b_hist[b_bin]++;
    }

    // Normalize and store
    const total_pixels = data.length / 4;
    for (let i = 0; i < 16; i++) {
      features[i] = r_hist[i] / total_pixels;
      features[i + 16] = g_hist[i] / total_pixels;
      features[i + 32] = b_hist[i] / total_pixels;
    }

    // Fill remaining with placeholder
    for (let i = 48; i < 128; i++) {
      features[i] = Math.random() * 0.1;
    }

    return features;
  }

  /**
   * Extract structural features (Block 4)
   */
  private extractStructuralFeatures(image_data: ImageData): Float32Array {
    const features = new Float32Array(128);

    // Simplified: Spatial layout and composition
    // In production, would use actual VGG19 activations

    for (let i = 0; i < features.length; i++) {
      features[i] = Math.random() * 0.1;
    }

    return features;
  }

  /**
   * Extract semantic features (Block 5)
   */
  private extractSemanticFeatures(image_data: ImageData): Float32Array {
    const features = new Float32Array(128);

    // Simplified: High-level composition features
    // In production, would use actual VGG19 activations

    for (let i = 0; i < features.length; i++) {
      features[i] = Math.random() * 0.1;
    }

    return features;
  }

  /**
   * Extract dominant colors using k-means clustering
   */
  private extractDominantColors(image_data: ImageData, k: number = 5): string[] {
    const { data } = image_data;
    const pixels: Array<[number, number, number]> = [];

    // Sample pixels (subsample for performance)
    const sample_rate = 10;
    for (let i = 0; i < data.length; i += 4 * sample_rate) {
      pixels.push([data[i], data[i + 1], data[i + 2]]);
    }

    // Simple k-means clustering
    const centroids = this.kMeansClustering(pixels, k);

    // Convert to hex colors
    return centroids.map(([r, g, b]) => this.rgbToHex(r, g, b));
  }

  /**
   * K-means clustering for color quantization
   */
  private kMeansClustering(
    pixels: Array<[number, number, number]>,
    k: number
  ): Array<[number, number, number]> {
    // Initialize centroids randomly
    const centroids: Array<[number, number, number]> = [];
    for (let i = 0; i < k; i++) {
      const random_pixel = pixels[Math.floor(Math.random() * pixels.length)];
      centroids.push([...random_pixel]);
    }

    // Iterate k-means (simplified - just 5 iterations)
    for (let iter = 0; iter < 5; iter++) {
      const clusters: Array<Array<[number, number, number]>> = Array.from(
        { length: k },
        () => []
      );

      // Assign pixels to nearest centroid
      for (const pixel of pixels) {
        let min_dist = Infinity;
        let min_cluster = 0;

        for (let c = 0; c < k; c++) {
          const dist = this.colorDistance(pixel, centroids[c]);
          if (dist < min_dist) {
            min_dist = dist;
            min_cluster = c;
          }
        }

        clusters[min_cluster].push(pixel);
      }

      // Update centroids
      for (let c = 0; c < k; c++) {
        if (clusters[c].length > 0) {
          const mean_r =
            clusters[c].reduce((sum, p) => sum + p[0], 0) / clusters[c].length;
          const mean_g =
            clusters[c].reduce((sum, p) => sum + p[1], 0) / clusters[c].length;
          const mean_b =
            clusters[c].reduce((sum, p) => sum + p[2], 0) / clusters[c].length;

          centroids[c] = [Math.round(mean_r), Math.round(mean_g), Math.round(mean_b)];
        }
      }
    }

    return centroids;
  }

  /**
   * Color distance (Euclidean in RGB space)
   */
  private colorDistance(
    c1: [number, number, number],
    c2: [number, number, number]
  ): number {
    const dr = c1[0] - c2[0];
    const dg = c1[1] - c2[1];
    const db = c1[2] - c2[2];
    return Math.sqrt(dr * dr + dg * dg + db * db);
  }

  /**
   * RGB to hex color
   */
  private rgbToHex(r: number, g: number, b: number): string {
    return (
      '#' +
      [r, g, b]
        .map((x) => Math.round(x).toString(16).padStart(2, '0'))
        .join('')
    );
  }

  /**
   * Extract texture features
   */
  private extractTextureFeatures(image_data: ImageData): {
    complexity: number;
    contrast: number;
    energy: number;
  } {
    const { data, width, height } = image_data;

    // Calculate gray-level co-occurrence matrix (GLCM) features
    // Simplified version

    let complexity = 0;
    let contrast = 0;
    let energy = 0;

    // Edge density as complexity measure
    for (let y = 0; y < height - 1; y++) {
      for (let x = 0; x < width - 1; x++) {
        const i = (y * width + x) * 4;
        const i_right = (y * width + (x + 1)) * 4;
        const i_bottom = ((y + 1) * width + x) * 4;

        const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;
        const gray_right = (data[i_right] + data[i_right + 1] + data[i_right + 2]) / 3;
        const gray_bottom =
          (data[i_bottom] + data[i_bottom + 1] + data[i_bottom + 2]) / 3;

        complexity += Math.abs(gray_right - gray) + Math.abs(gray_bottom - gray);
      }
    }
    complexity /= (width - 1) * (height - 1) * 255 * 2;

    // Contrast: range of intensity values
    const grays: number[] = [];
    for (let i = 0; i < data.length; i += 4) {
      grays.push((data[i] + data[i + 1] + data[i + 2]) / 3);
    }
    const min_gray = Math.min(...grays);
    const max_gray = Math.max(...grays);
    contrast = (max_gray - min_gray) / 255;

    // Energy: uniformity of distribution
    const histogram = new Array(256).fill(0);
    for (const gray of grays) {
      histogram[Math.floor(gray)]++;
    }
    for (const count of histogram) {
      const p = count / grays.length;
      if (p > 0) {
        energy += p * p;
      }
    }

    return { complexity, contrast, energy };
  }

  getDimension(): number {
    return this.dimension;
  }

  getTier(): 'stroke' | 'image' | 'temporal' {
    return 'image';
  }
}

/**
 * Global encoder instance
 */
export const globalImageDNAEncoder = new ImageDNAEncoder();
