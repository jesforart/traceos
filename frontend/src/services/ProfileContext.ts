/**
 * ProfileContext - Bridges semantic tagging (Day 2) with calibration (Day 3)
 *
 * This service manages the artist profile and provides:
 * - Semantic weighting for different facial features
 * - Shader constants for GPU rendering
 * - Pressure curve evaluation
 * - Nib and stabilizer parameters
 */

import { ArtistProfile, BezierCurve } from '../types/calibration';
import { FaceTag } from '../types/semantic';

export interface ShaderConstants {
  // Bezier control points (pressure -> radius)
  pressureToRadius: {
    p0: [number, number];
    p1: [number, number];
    p2: [number, number];
    p3: [number, number];
  };

  // Bezier control points (pressure -> density)
  pressureToDensity: {
    p0: [number, number];
    p1: [number, number];
    p2: [number, number];
    p3: [number, number];
  };

  // Nib parameters
  nib: {
    baseRadiusPx: number;
    minRadiusPx: number;
    maxRadiusPx: number;
    avgTiltDeg: number;
  };

  // Stabilizer parameters
  stabilizer: {
    microJitterRadiusPx: number;
    curveSmoothMin: number;
    curveSmoothMax: number;
    velocityMin: number;
    velocityMax: number;
  };
}

/**
 * Default semantic weights for different facial features.
 * Higher values = sharper/more defined strokes
 * Lower values = softer/smoother strokes
 */
const DEFAULT_SEMANTIC_WEIGHTS: Map<FaceTag, number> = new Map([
  ['left_eye', 1.2],      // Eyes sharper for definition
  ['right_eye', 1.2],
  ['left_eyebrow', 1.15], // Eyebrows fairly sharp
  ['right_eyebrow', 1.15],
  ['nose', 1.0],          // Nose neutral
  ['mouth', 1.05],        // Mouth slightly defined
  ['jaw', 0.8],           // Jaw softer
  ['outline', 0.75],      // Face outline very soft
  ['left_ear', 0.85],     // Ears somewhat soft
  ['right_ear', 0.85],
  ['hair', 0.9],          // Hair moderately soft
  ['other', 1.0]          // Default neutral
]);

export class ProfileContext {
  private profile: ArtistProfile | null = null;
  private semanticWeights: Map<FaceTag, number>;

  constructor() {
    this.semanticWeights = new Map(DEFAULT_SEMANTIC_WEIGHTS);
  }

  /**
   * Load artist profile from calibration data.
   */
  setProfile(profile: ArtistProfile): void {
    this.profile = profile;
  }

  /**
   * Get current profile.
   */
  getProfile(): ArtistProfile | null {
    return this.profile;
  }

  /**
   * Check if profile is loaded.
   */
  hasProfile(): boolean {
    return this.profile !== null;
  }

  /**
   * Get semantic weight for a specific face tag.
   * Returns 1.0 if no custom weight is set.
   */
  getSemanticWeight(tag: FaceTag): number {
    return this.semanticWeights.get(tag) ?? 1.0;
  }

  /**
   * Set custom semantic weight for a face tag.
   * @param tag - The facial feature tag
   * @param weight - Multiplier (0.5-2.0 recommended range)
   */
  setSemanticWeight(tag: FaceTag, weight: number): void {
    this.semanticWeights.set(tag, weight);
  }

  /**
   * Reset semantic weights to defaults.
   */
  resetSemanticWeights(): void {
    this.semanticWeights = new Map(DEFAULT_SEMANTIC_WEIGHTS);
  }

  /**
   * Export shader constants for GPU rendering.
   * This packages the profile data into a format ready for WGSL shaders.
   */
  getShaderConstants(): ShaderConstants | null {
    if (!this.profile) {
      return null;
    }

    const { curves, nib, stabilizer } = this.profile;

    // Convert Bezier curves to shader format
    const pressureToRadius = curves.pressureToRadius;
    const pressureToDensity = curves.pressureToDensity;

    return {
      pressureToRadius: {
        p0: pressureToRadius.controlPoints[0],
        p1: pressureToRadius.controlPoints[1],
        p2: pressureToRadius.controlPoints[2],
        p3: pressureToRadius.controlPoints[3]
      },
      pressureToDensity: {
        p0: pressureToDensity.controlPoints[0],
        p1: pressureToDensity.controlPoints[1],
        p2: pressureToDensity.controlPoints[2],
        p3: pressureToDensity.controlPoints[3]
      },
      nib: {
        baseRadiusPx: nib.baseRadiusPx,
        minRadiusPx: nib.minRadiusPx,
        maxRadiusPx: nib.maxRadiusPx,
        avgTiltDeg: nib.avgTiltDeg
      },
      stabilizer: {
        microJitterRadiusPx: stabilizer.microJitterRadiusPx,
        curveSmoothMin: stabilizer.curveSmooth.min,
        curveSmoothMax: stabilizer.curveSmooth.max,
        velocityMin: stabilizer.velocityAdapt.vMin,
        velocityMax: stabilizer.velocityAdapt.vMax
      }
    };
  }

  /**
   * Evaluate cubic Bezier curve at parameter t.
   * @param curve - Bezier curve with 4 control points
   * @param t - Parameter value (0.0 to 1.0)
   * @returns Interpolated [x, y] value
   */
  private evaluateBezier(curve: BezierCurve, t: number): [number, number] {
    // Clamp t to [0, 1]
    t = Math.max(0.0, Math.min(1.0, t));

    const [p0, p1, p2, p3] = curve.controlPoints;
    const u = 1 - t;

    // Cubic Bezier formula: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
    const x = u * u * u * p0[0] +
              3 * u * u * t * p1[0] +
              3 * u * t * t * p2[0] +
              t * t * t * p3[0];

    const y = u * u * u * p0[1] +
              3 * u * u * t * p1[1] +
              3 * u * t * t * p2[1] +
              t * t * t * p3[1];

    return [x, y];
  }

  /**
   * Evaluate pressure -> radius curve.
   * @param pressure - Input pressure (0.0 to 1.0)
   * @param semanticWeight - Optional semantic weight multiplier
   * @returns Radius value (0.0 to 1.0)
   */
  evaluatePressureToRadius(pressure: number, semanticWeight: number = 1.0): number {
    if (!this.profile) {
      // Fallback: linear mapping
      return pressure * semanticWeight;
    }

    const curve = this.profile.curves.pressureToRadius;

    // Find the Y value by evaluating at pressure (used as t)
    const [, radius] = this.evaluateBezier(curve, pressure);

    // Apply semantic weighting
    return radius * semanticWeight;
  }

  /**
   * Evaluate pressure -> density curve.
   * @param pressure - Input pressure (0.0 to 1.0)
   * @param semanticWeight - Optional semantic weight multiplier
   * @returns Density value (0.0 to 1.0)
   */
  evaluatePressureToDensity(pressure: number, semanticWeight: number = 1.0): number {
    if (!this.profile) {
      // Fallback: linear mapping
      return pressure * semanticWeight;
    }

    const curve = this.profile.curves.pressureToDensity;

    // Find the Y value by evaluating at pressure (used as t)
    const [, density] = this.evaluateBezier(curve, pressure);

    // Apply semantic weighting
    return density * semanticWeight;
  }

  /**
   * Get nib parameters (for rendering initialization).
   */
  getNibParameters() {
    if (!this.profile) {
      return {
        baseRadiusPx: 2.0,
        minRadiusPx: 0.4,
        maxRadiusPx: 12.0,
        avgTiltDeg: 35.0
      };
    }

    return this.profile.nib;
  }

  /**
   * Get stabilizer parameters (for stroke smoothing).
   */
  getStabilizerParameters() {
    if (!this.profile) {
      return {
        microJitterRadiusPx: 2.0,
        curveSmooth: { min: 0.05, max: 0.20 },
        velocityAdapt: { vMin: 0.0, vMax: 1500.0 }
      };
    }

    return this.profile.stabilizer;
  }

  /**
   * Get all semantic weights as a plain object.
   * Useful for debugging or serialization.
   */
  getAllSemanticWeights(): Record<FaceTag, number> {
    const result = {} as Record<FaceTag, number>;
    this.semanticWeights.forEach((weight, tag) => {
      result[tag] = weight;
    });
    return result;
  }

  /**
   * Get profile metadata for display.
   */
  getProfileMetadata() {
    if (!this.profile) {
      return null;
    }

    return {
      id: this.profile.id,
      artistName: this.profile.artistName,
      createdAt: this.profile.createdAt,
      version: this.profile.version,
      traceProfileVersion: this.profile.traceProfileVersion,
      brushEngineVersion: this.profile.brushEngineVersion,
      fingerprint: this.profile.device.calibrationFingerprint
    };
  }
}

// Global singleton instance
export const profileContext = new ProfileContext();
