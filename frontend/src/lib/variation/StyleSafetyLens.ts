/**
 * Week 3: Design Variation Engine - Style Safety Lens
 *
 * "Lighthouse for Creative AI"
 * Post-generation validation for design variations.
 * World-first style safety checking system.
 */

import type { BaseSchema, DesignContext } from '../schema/types';
import type {
  SafetyScore,
  AccessibilityViolation,
  BrandViolation,
  StructuralIssue,
  QualityWarning
} from './types';

/**
 * Style Safety Lens - Multi-level validation
 */
export class StyleSafetyLens {
  /**
   * Validate a schema across all dimensions
   */
  async validate(schema: BaseSchema, context: DesignContext): Promise<SafetyScore> {
    // Run all validations in parallel
    const [brand_safety, accessibility_safety, structural_safety, quality_safety] =
      await Promise.all([
        this.validateBrandSafety(schema),
        this.validateAccessibility(schema, context),
        this.validateStructure(schema),
        this.validateQuality(schema)
      ]);

    // Calculate overall score (weighted average)
    const overall_score =
      brand_safety.score * 0.25 +
      accessibility_safety.score * 0.35 +
      structural_safety.score * 0.25 +
      quality_safety.score * 0.15;

    // Determine recommendation
    let recommendation: 'safe' | 'review' | 'unsafe';
    if (overall_score >= 80) {
      recommendation = 'safe';
    } else if (overall_score >= 60) {
      recommendation = 'review';
    } else {
      recommendation = 'unsafe';
    }

    return {
      overall_score,
      brand_safety,
      accessibility_safety,
      structural_safety,
      quality_safety,
      recommendation
    };
  }

  /**
   * Validate brand safety
   */
  private async validateBrandSafety(
    schema: BaseSchema
  ): Promise<{ score: number; violations: BrandViolation[] }> {
    const violations: BrandViolation[] = [];

    // TODO: Implement brand guideline checks
    // - Color palette compliance
    // - Typography usage
    // - Logo placement
    // - Tone/style consistency

    // For now, return perfect score
    return {
      score: 100,
      violations
    };
  }

  /**
   * Validate accessibility (WCAG compliance)
   */
  private async validateAccessibility(
    schema: BaseSchema,
    context: DesignContext
  ): Promise<{
    score: number;
    wcag_level: 'AA' | 'AAA' | 'fail';
    violations: AccessibilityViolation[];
  }> {
    const violations: AccessibilityViolation[] = [];

    // Check contrast ratios
    for (const node of schema.semantic_nodes) {
      if (node.properties.color && node.properties.backgroundColor) {
        const contrast = this.calculateContrastRatio(
          node.properties.color,
          node.properties.backgroundColor
        );

        const min_contrast = context.accessibility_level === 'AAA' ? 7.0 : 4.5;

        if (contrast < min_contrast) {
          violations.push({
            severity: 'error',
            wcag_criterion: '1.4.3',
            level: context.accessibility_level,
            message: `Insufficient contrast ratio: ${contrast.toFixed(2)}:1 (need ${min_contrast}:1)`,
            node_id: node.node_id,
            contrast_ratio: contrast,
            min_contrast_required: min_contrast
          });
        }
      }

      // Check touch target size (mobile)
      if (context.device_targets.includes('mobile')) {
        if (
          node.node_type === 'cta' &&
          (node.bounds.width < 44 || node.bounds.height < 44)
        ) {
          violations.push({
            severity: 'error',
            wcag_criterion: '2.5.5',
            level: 'AAA',
            message: 'Touch target too small (minimum 44x44px)',
            node_id: node.node_id,
            touch_target_size: {
              width: node.bounds.width,
              height: node.bounds.height
            },
            min_touch_target: { width: 44, height: 44 }
          });
        }
      }

      // Check font size
      if (node.properties.fontSize && node.properties.fontSize < 12) {
        violations.push({
          severity: 'warning',
          wcag_criterion: '1.4.4',
          level: 'AA',
          message: `Font size too small: ${node.properties.fontSize}px (minimum 12px recommended)`,
          node_id: node.node_id
        });
      }
    }

    // Calculate score
    const max_violations = schema.semantic_nodes.length * 2; // Rough estimate
    const score = Math.max(
      0,
      100 - (violations.length / max_violations) * 100
    );

    // Determine WCAG level
    const has_errors = violations.some((v) => v.severity === 'error');
    const wcag_level: 'AA' | 'AAA' | 'fail' = has_errors
      ? 'fail'
      : context.accessibility_level;

    return {
      score,
      wcag_level,
      violations
    };
  }

  /**
   * Validate structural integrity
   */
  private async validateStructure(
    schema: BaseSchema
  ): Promise<{ score: number; issues: StructuralIssue[] }> {
    const issues: StructuralIssue[] = [];

    // Check for overlapping nodes
    for (let i = 0; i < schema.semantic_nodes.length; i++) {
      for (let j = i + 1; j < schema.semantic_nodes.length; j++) {
        const node_a = schema.semantic_nodes[i];
        const node_b = schema.semantic_nodes[j];

        if (this.boundsOverlap(node_a.bounds, node_b.bounds)) {
          issues.push({
            severity: 'warning',
            type: 'overlap',
            message: 'Nodes overlap',
            node_ids: [node_a.node_id, node_b.node_id]
          });
        }
      }
    }

    // Check for orphan nodes (no parent, no children)
    for (const node of schema.semantic_nodes) {
      if (!node.parent_id && node.children_ids.length === 0) {
        issues.push({
          severity: 'warning',
          type: 'orphan',
          message: 'Orphan node (no parent or children)',
          node_ids: [node.node_id]
        });
      }
    }

    const score = Math.max(0, 100 - issues.length * 10);

    return { score, issues };
  }

  /**
   * Validate quality
   */
  private async validateQuality(
    schema: BaseSchema
  ): Promise<{ score: number; warnings: QualityWarning[] }> {
    const warnings: QualityWarning[] = [];

    // Check alignment
    // Check spacing consistency
    // Check readability

    // For now, return good score
    const score = 90;

    return { score, warnings };
  }

  /**
   * Calculate WCAG contrast ratio
   */
  private calculateContrastRatio(fg: string, bg: string): number {
    const fg_luminance = this.relativeLuminance(fg);
    const bg_luminance = this.relativeLuminance(bg);

    const lighter = Math.max(fg_luminance, bg_luminance);
    const darker = Math.min(fg_luminance, bg_luminance);

    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Calculate relative luminance
   */
  private relativeLuminance(color: string): number {
    const rgb = this.hexToRgb(color);
    if (!rgb) return 0;

    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((c) => {
      const sRGB = c / 255;
      return sRGB <= 0.03928
        ? sRGB / 12.92
        : Math.pow((sRGB + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /**
   * Convert hex to RGB
   */
  private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        }
      : null;
  }

  /**
   * Check if two bounds overlap
   */
  private boundsOverlap(
    a: { x: number; y: number; width: number; height: number },
    b: { x: number; y: number; width: number; height: number }
  ): boolean {
    return !(
      a.x + a.width < b.x ||
      b.x + b.width < a.x ||
      a.y + a.height < b.y ||
      b.y + b.height < a.y
    );
  }
}

// Singleton instance
export const styleSafetyLens = new StyleSafetyLens();
