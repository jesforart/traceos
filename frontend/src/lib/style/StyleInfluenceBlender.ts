/**
 * Week 3 v1.2: Style Influence Vector Blending - Blender
 *
 * Multi-source style mixing engine.
 * Combines weighted aesthetic profiles into cohesive designs.
 */

import type {
  StyleInfluenceVector,
  BlendedStyleDNA,
  BlendConfiguration,
  StyleLibraryEntry
} from './types';
import type { AestheticProfile } from '../schema/types';
import { ulid } from '../../utils/ulid';

/**
 * Style Influence Blender - Multi-source style mixing
 */
export class StyleInfluenceBlender {
  private styleLibrary: Map<string, StyleLibraryEntry> = new Map();

  constructor() {
    this.initializeStyleLibrary();
  }

  /**
   * Blend multiple style influences
   */
  blend(
    sources: StyleInfluenceVector[],
    config: BlendConfiguration = { method: 'weighted_average' }
  ): BlendedStyleDNA {
    // Normalize weights if requested
    const normalized_sources = config.normalize_weights
      ? this.normalizeWeights(sources)
      : sources;

    // Apply blending method
    let resulting_profile: AestheticProfile;
    switch (config.method) {
      case 'weighted_average':
        resulting_profile = this.blendWeightedAverage(normalized_sources);
        break;
      case 'dominant':
        resulting_profile = this.blendDominant(normalized_sources);
        break;
      case 'layered':
        resulting_profile = this.blendLayered(normalized_sources);
        break;
      case 'harmonic':
        resulting_profile = this.blendHarmonic(normalized_sources);
        break;
      default:
        resulting_profile = this.blendWeightedAverage(normalized_sources);
    }

    return {
      blend_id: ulid(),
      blend_name: this.generateBlendName(normalized_sources),
      sources: normalized_sources,
      resulting_profile,
      blend_method: config.method,
      created_at: Date.now()
    };
  }

  /**
   * Weighted average blending
   */
  private blendWeightedAverage(sources: StyleInfluenceVector[]): AestheticProfile {
    if (sources.length === 0) {
      throw new Error('No sources provided for blending');
    }

    // Start with first source as base
    const base = JSON.parse(JSON.stringify(sources[0].aesthetic_profile));

    if (sources.length === 1) {
      return base;
    }

    // Blend numeric properties
    const dominant = sources.reduce((prev, curr) => (curr.weight > prev.weight ? curr : prev));

    const blended: AestheticProfile = {
      style_embedding_id: dominant.aesthetic_profile.style_embedding_id,
      design_language: dominant.aesthetic_profile.design_language,
      color_harmony: dominant.aesthetic_profile.color_harmony,
      texture_density: dominant.aesthetic_profile.texture_density,
      color_palette: this.blendColorPalettes(sources),
      typography: this.blendTypography(sources),
      spacing_system: this.blendSpacingSystem(sources),
      visual_language: this.blendVisualLanguage(sources)
    };

    return blended;
  }

  /**
   * Dominant source blending (highest weight wins)
   */
  private blendDominant(sources: StyleInfluenceVector[]): AestheticProfile {
    const dominant = sources.reduce((prev, current) =>
      current.weight > prev.weight ? current : prev
    );

    return JSON.parse(JSON.stringify(dominant.aesthetic_profile));
  }

  /**
   * Layered blending (apply sources in order)
   */
  private blendLayered(sources: StyleInfluenceVector[]): AestheticProfile {
    // Sort by weight (lowest to highest)
    const sorted = [...sources].sort((a, b) => a.weight - b.weight);

    // Start with base layer
    let result = JSON.parse(JSON.stringify(sorted[0].aesthetic_profile));

    // Apply each layer
    for (let i = 1; i < sorted.length; i++) {
      const layer = sorted[i];
      result = this.applyLayer(result, layer.aesthetic_profile, layer.weight);
    }

    return result;
  }

  /**
   * Harmonic blending (optimize for visual harmony)
   */
  private blendHarmonic(sources: StyleInfluenceVector[]): AestheticProfile {
    // Similar to weighted average but with harmony optimization
    const base = this.blendWeightedAverage(sources);

    // Apply harmony adjustments
    base.color_palette.harmony_rule = 'triadic';
    base.spacing_system.scale_factor = 1.618; // Golden ratio

    return base;
  }

  /**
   * Blend color palettes
   */
  private blendColorPalettes(sources: StyleInfluenceVector[]): AestheticProfile['color_palette'] {
    // Take primary from dominant source
    const dominant = sources.reduce((prev, curr) => (curr.weight > prev.weight ? curr : prev));

    // Blend accent colors
    const all_accents = sources.flatMap((s) => s.aesthetic_profile.color_palette.accents);

    return {
      primary: dominant.aesthetic_profile.color_palette.primary,
      secondary: dominant.aesthetic_profile.color_palette.secondary,
      accents: all_accents.slice(0, 3), // Take top 3
      neutrals: dominant.aesthetic_profile.color_palette.neutrals,
      harmony_rule: dominant.aesthetic_profile.color_palette.harmony_rule
    };
  }

  /**
   * Blend typography
   */
  private blendTypography(sources: StyleInfluenceVector[]): AestheticProfile['typography'] {
    // Weighted average for sizes
    const heading_size = this.weightedAverage(
      sources.map((s) => ({
        value: s.aesthetic_profile.typography.heading_size,
        weight: s.weight
      }))
    );

    const body_size = this.weightedAverage(
      sources.map((s) => ({
        value: s.aesthetic_profile.typography.body_size,
        weight: s.weight
      }))
    );

    // Take font family from dominant source
    const dominant = sources.reduce((prev, curr) => (curr.weight > prev.weight ? curr : prev));

    return {
      font_family_primary: dominant.aesthetic_profile.typography.font_family_primary,
      font_family_secondary: dominant.aesthetic_profile.typography.font_family_secondary,
      heading_size,
      body_size,
      line_height: this.weightedAverage(
        sources.map((s) => ({
          value: s.aesthetic_profile.typography.line_height,
          weight: s.weight
        }))
      ),
      letter_spacing: this.weightedAverage(
        sources.map((s) => ({
          value: s.aesthetic_profile.typography.letter_spacing,
          weight: s.weight
        }))
      )
    };
  }

  /**
   * Blend spacing system
   */
  private blendSpacingSystem(sources: StyleInfluenceVector[]): AestheticProfile['spacing_system'] {
    return {
      base_unit: Math.round(
        this.weightedAverage(
          sources.map((s) => ({
            value: s.aesthetic_profile.spacing_system.base_unit,
            weight: s.weight
          }))
        )
      ),
      scale_factor: this.weightedAverage(
        sources.map((s) => ({
          value: s.aesthetic_profile.spacing_system.scale_factor,
          weight: s.weight
        }))
      )
    };
  }

  /**
   * Blend visual language
   */
  private blendVisualLanguage(sources: StyleInfluenceVector[]): AestheticProfile['visual_language'] {
    return {
      border_radius: Math.round(
        this.weightedAverage(
          sources.map((s) => ({
            value: s.aesthetic_profile.visual_language.border_radius,
            weight: s.weight
          }))
        )
      ),
      border_width: Math.round(
        this.weightedAverage(
          sources.map((s) => ({
            value: s.aesthetic_profile.visual_language.border_width,
            weight: s.weight
          }))
        )
      ),
      shadow_intensity: this.weightedAverage(
        sources.map((s) => ({
          value: s.aesthetic_profile.visual_language.shadow_intensity,
          weight: s.weight
        }))
      )
    };
  }

  /**
   * Apply layer on top of base
   */
  private applyLayer(
    base: AestheticProfile,
    layer: AestheticProfile,
    alpha: number
  ): AestheticProfile {
    // Simple linear interpolation
    return {
      style_embedding_id: layer.style_embedding_id,
      design_language: layer.design_language,
      color_harmony: layer.color_harmony,
      texture_density: this.lerp(base.texture_density, layer.texture_density, alpha),
      color_palette: base.color_palette, // Colors from layer
      typography: {
        font_family_primary: layer.typography.font_family_primary,
        font_family_secondary: layer.typography.font_family_secondary,
        heading_size: this.lerp(base.typography.heading_size, layer.typography.heading_size, alpha),
        body_size: this.lerp(base.typography.body_size, layer.typography.body_size, alpha),
        line_height: this.lerp(base.typography.line_height, layer.typography.line_height, alpha),
        letter_spacing: this.lerp(base.typography.letter_spacing, layer.typography.letter_spacing, alpha)
      },
      spacing_system: {
        base_unit: Math.round(
          this.lerp(base.spacing_system.base_unit, layer.spacing_system.base_unit, alpha)
        ),
        scale_factor: this.lerp(
          base.spacing_system.scale_factor,
          layer.spacing_system.scale_factor,
          alpha
        )
      },
      visual_language: {
        border_radius: Math.round(
          this.lerp(
            base.visual_language.border_radius,
            layer.visual_language.border_radius,
            alpha
          )
        ),
        border_width: Math.round(
          this.lerp(base.visual_language.border_width, layer.visual_language.border_width, alpha)
        ),
        shadow_intensity: this.lerp(
          base.visual_language.shadow_intensity,
          layer.visual_language.shadow_intensity,
          alpha
        )
      }
    };
  }

  /**
   * Normalize weights to sum to 1.0
   */
  private normalizeWeights(sources: StyleInfluenceVector[]): StyleInfluenceVector[] {
    const total = sources.reduce((sum, s) => sum + s.weight, 0);
    if (total === 0) return sources;

    return sources.map((s) => ({
      ...s,
      weight: s.weight / total
    }));
  }

  /**
   * Calculate weighted average
   */
  private weightedAverage(values: Array<{ value: number; weight: number }>): number {
    const total_weight = values.reduce((sum, v) => sum + v.weight, 0);
    if (total_weight === 0) return values[0]?.value || 0;

    const weighted_sum = values.reduce((sum, v) => sum + v.value * v.weight, 0);
    return weighted_sum / total_weight;
  }

  /**
   * Linear interpolation
   */
  private lerp(a: number, b: number, t: number): number {
    return a * (1 - t) + b * t;
  }

  /**
   * Generate blend name from sources
   */
  private generateBlendName(sources: StyleInfluenceVector[]): string {
    if (sources.length === 0) return 'Empty Blend';
    if (sources.length === 1) return sources[0].source_name;
    if (sources.length === 2) {
      return `${sources[0].source_name} × ${sources[1].source_name}`;
    }
    return `${sources[0].source_name} + ${sources.length - 1} more`;
  }

  /**
   * Initialize predefined style library
   */
  private initializeStyleLibrary() {
    // Brand styles
    this.addStyleEntry({
      entry_id: 'modern_tech',
      name: 'Modern Tech',
      category: 'brand',
      description: 'Clean, minimal, high-contrast tech aesthetic',
      tags: ['minimal', 'tech', 'modern'],
      aesthetic_profile: {
        style_embedding_id: 'modern_tech_001',
        design_language: 'minimal',
        color_harmony: 'complementary',
        texture_density: 0.2,
        color_palette: {
          primary: '#0066FF',
          secondary: '#00FF88',
          accents: ['#FF0066', '#FFAA00'],
          neutrals: ['#FFFFFF', '#F5F5F5', '#333333'],
          harmony_rule: 'complementary'
        },
        typography: {
          font_family_primary: 'Inter',
          font_family_secondary: 'SF Mono',
          heading_size: 48,
          body_size: 16,
          line_height: 1.6,
          letter_spacing: 0
        },
        spacing_system: {
          base_unit: 8,
          scale_factor: 1.5
        },
        visual_language: {
          border_radius: 8,
          border_width: 1,
          shadow_intensity: 0.2
        }
      }
    });

    // Artist styles
    this.addStyleEntry({
      entry_id: 'brutalist',
      name: 'Brutalist',
      category: 'artist',
      description: 'Bold, geometric, raw concrete aesthetic',
      tags: ['bold', 'geometric', 'brutal'],
      aesthetic_profile: {
        style_embedding_id: 'brutalist_001',
        design_language: 'artistic',
        color_harmony: 'monochromatic',
        texture_density: 0.9,
        color_palette: {
          primary: '#000000',
          secondary: '#CCCCCC',
          accents: ['#FF3300', '#0033FF'],
          neutrals: ['#FFFFFF', '#999999', '#333333'],
          harmony_rule: 'monochromatic'
        },
        typography: {
          font_family_primary: 'Arial',
          font_family_secondary: 'Courier',
          heading_size: 72,
          body_size: 14,
          line_height: 1.2,
          letter_spacing: -0.5
        },
        spacing_system: {
          base_unit: 16,
          scale_factor: 2.0
        },
        visual_language: {
          border_radius: 0,
          border_width: 4,
          shadow_intensity: 0
        }
      }
    });

    console.log(`🎨 Initialized style library with ${this.styleLibrary.size} entries`);
  }

  /**
   * Add entry to style library
   */
  addStyleEntry(entry: StyleLibraryEntry) {
    this.styleLibrary.set(entry.entry_id, entry);
  }

  /**
   * Get style entry
   */
  getStyleEntry(entry_id: string): StyleLibraryEntry | undefined {
    return this.styleLibrary.get(entry_id);
  }

  /**
   * Get all style entries
   */
  getAllStyleEntries(): StyleLibraryEntry[] {
    return Array.from(this.styleLibrary.values());
  }

  /**
   * Create style influence vector from library entry
   */
  createInfluenceVector(
    entry_id: string,
    weight: number = 1.0
  ): StyleInfluenceVector | null {
    const entry = this.styleLibrary.get(entry_id);
    if (!entry) return null;

    return {
      source_id: entry.entry_id,
      source_name: entry.name,
      source_type: entry.category,
      weight,
      aesthetic_profile: entry.aesthetic_profile,
      metadata: {
        description: entry.description,
        tags: entry.tags
      }
    };
  }
}

// Singleton instance
export const styleInfluenceBlender = new StyleInfluenceBlender();
