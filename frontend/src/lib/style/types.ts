/**
 * Week 3 v1.2: Style Influence Vector Blending - Types
 *
 * Multi-source style mixing with weighted vectors.
 */

import type { AestheticProfile } from '../schema/types';

/**
 * Style Influence Vector - Represents a style contribution
 */
export interface StyleInfluenceVector {
  source_id: string;
  source_name: string;
  source_type: 'brand' | 'artist' | 'era' | 'genre' | 'custom';
  weight: number; // 0.0 to 1.0
  aesthetic_profile: AestheticProfile;
  metadata?: {
    description?: string;
    tags?: string[];
    created_at?: number;
  };
}

/**
 * Blended Style DNA - Result of multi-source blending
 */
export interface BlendedStyleDNA {
  blend_id: string;
  blend_name: string;
  sources: StyleInfluenceVector[];
  resulting_profile: AestheticProfile;
  blend_method: 'weighted_average' | 'dominant' | 'layered' | 'harmonic';
  created_at: number;
  metadata?: {
    formula?: string;
    use_case?: string;
  };
}

/**
 * Style Library Entry - Predefined style templates
 */
export interface StyleLibraryEntry {
  entry_id: string;
  name: string;
  category: 'brand' | 'artist' | 'era' | 'genre';
  aesthetic_profile: AestheticProfile;
  description: string;
  tags: string[];
  preview_image?: string;
}

/**
 * Blend Configuration - How to combine sources
 */
export interface BlendConfiguration {
  method: 'weighted_average' | 'dominant' | 'layered' | 'harmonic';
  normalize_weights?: boolean; // Auto-normalize to sum to 1.0
  preserve_constraints?: boolean; // Keep original constraints
  interpolation?: 'linear' | 'cubic' | 'ease_in' | 'ease_out';
}
