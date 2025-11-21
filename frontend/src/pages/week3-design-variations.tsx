/**
 * Week 3: Design Variation Engine - Demo Page
 *
 * Showcases the Design Variation Engine capabilities:
 * - Schema creation
 * - Modifier application
 * - Variation generation
 * - Safety validation
 * - Drift detection
 * - Provenance tracking
 */

import React, { useState, useEffect } from 'react';
import type { BaseSchema } from '../lib/schema/types';
import type { GeneratedVariation } from '../lib/variation/types';
import { schemaStore } from '../lib/schema/SchemaStore';
import { modifierLibrary } from '../lib/modifiers/ModifierLibrary';
import { variationGenerator } from '../lib/variation/VariationGenerator';
import { provenanceTracker } from '../lib/provenance/ProvenanceTracker';
import { variationPromptParser } from '../lib/prompts/VariationPromptParser';
import { aiPromptGenerator } from '../lib/prompts/AIPromptGenerator';
import { styleInfluenceBlender } from '../lib/style/StyleInfluenceBlender';
import { temporalVariationEngine } from '../lib/temporal/TemporalVariationEngine';
import { agentNegotiator } from '../lib/agents/AgentNegotiator';
import { LayoutAgent } from '../lib/agents/LayoutAgent';
import { AccessibilityAgent } from '../lib/agents/AccessibilityAgent';
import { schemaMutator } from '../lib/evolution/SchemaMutator';
import { ulid } from '../utils/ulid';

// Example hero schema
const createExampleSchema = (): BaseSchema => {
  return {
    schema_id: ulid(),
    version: '1.0',
    created_at: Date.now(),
    updated_at: Date.now(),
    intent: 'Hero section for landing page',

    semantic_nodes: [
      {
        node_id: 'hero_background',
        node_type: 'background',
        semantic_label: 'Hero Background',
        bounds: { x: 0, y: 0, width: 800, height: 400 },
        properties: {
          backgroundColor: '#0066FF',
          opacity: 1.0
        },
        children_ids: ['hero_title', 'hero_cta'],
        zone_id: 'flexible_zone'
      },
      {
        node_id: 'hero_title',
        node_type: 'hero',
        semantic_label: 'Hero Title',
        bounds: { x: 50, y: 100, width: 700, height: 80 },
        properties: {
          color: '#FFFFFF',
          fontSize: 48,
          fontWeight: 700,
          fontFamily: 'system-ui'
        },
        parent_id: 'hero_background',
        children_ids: [],
        zone_id: 'flexible_zone'
      },
      {
        node_id: 'hero_cta',
        node_type: 'cta',
        semantic_label: 'Call to Action Button',
        bounds: { x: 50, y: 220, width: 200, height: 50 },
        properties: {
          backgroundColor: '#FF6600',
          color: '#FFFFFF',
          fontSize: 18,
          fontWeight: 600,
          borderRadius: 8,
          padding: 16
        },
        parent_id: 'hero_background',
        children_ids: [],
        zone_id: 'flexible_zone'
      }
    ],

    variation_zones: [
      {
        zone_id: 'flexible_zone',
        zone_type: 'flexible',
        description: 'Flexible design elements that can vary within bounds',
        constraints: [
          {
            property: 'fontSize',
            min_value: 12,
            max_value: 72
          },
          {
            property: 'padding',
            min_value: 8,
            max_value: 32
          }
        ]
      }
    ],

    aesthetic_profile: {
      style_embedding_id: 'modern_minimal_001',
      design_language: 'minimal',
      color_harmony: 'complementary',
      texture_density: 0.3,
      color_palette: {
        primary: '#0066FF',
        secondary: '#00FF88',
        accents: ['#FF6600', '#FFAA00'],
        neutrals: ['#FFFFFF', '#F5F5F5', '#333333'],
        harmony_rule: 'complementary'
      },
      typography: {
        font_family_primary: 'system-ui',
        font_family_secondary: 'monospace',
        heading_size: 48,
        body_size: 16,
        line_height: 1.5,
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
    },

    context: {
      accessibility_level: 'AA',
      device_targets: ['desktop', 'tablet', 'mobile'],
      color_mode: 'light'
    },

    evaluation: {
      metrics: {},
      required_validations: ['wcag', 'structure']
    },

    constraints: [],
    variation_rules: []
  };
};

export default function Week3DesignVariations() {
  const [baseSchema, setBaseSchema] = useState<BaseSchema | null>(null);
  const [variations, setVariations] = useState<GeneratedVariation[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    safe: 0,
    review: 0,
    unsafe: 0
  });

  // Initialize with example schema
  useEffect(() => {
    const schema = createExampleSchema();
    setBaseSchema(schema);
    schemaStore.save(schema);
    provenanceTracker.createLineage(schema);
  }, []);

  // Generate variations
  const handleGenerate = async () => {
    if (!baseSchema) return;

    setIsGenerating(true);

    try {
      const modifiers = modifierLibrary.getAll();

      const result = await variationGenerator.generate(baseSchema, modifiers, {
        base_schema_id: baseSchema.schema_id,
        count: 5,
        distance_range: { min: 0.1, max: 0.5 },
        target_zones: ['flexible_zone'],
        method: 'random',
        min_safety_score: 50
      });

      setVariations(result.variations);

      // Calculate stats
      const safe = result.variations.filter(
        (v) => v.safety_score.recommendation === 'safe'
      ).length;
      const review = result.variations.filter(
        (v) => v.safety_score.recommendation === 'review'
      ).length;
      const unsafe = result.variations.filter(
        (v) => v.safety_score.recommendation === 'unsafe'
      ).length;

      setStats({
        total: result.variations.length,
        safe,
        review,
        unsafe
      });

      // Record in provenance
      for (const variation of result.variations) {
        await provenanceTracker.recordVariation(baseSchema, variation);
      }

      console.log('✅ Generated variations:', result);
    } catch (error) {
      console.error('❌ Generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '8px' }}>
          Week 3: Design Variation Engine
        </h1>
        <p style={{ fontSize: '16px', color: '#666' }}>
          Foundation v1.0 + Visionary v1.2 - Schema-based design generation with advanced variation features
        </p>
      </header>

      {/* Base Schema */}
      {baseSchema && (
        <section style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '16px' }}>
            Base Schema
          </h2>
          <div
            style={{
              padding: '24px',
              backgroundColor: '#f5f5f5',
              borderRadius: '8px'
            }}
          >
            <div style={{ marginBottom: '12px' }}>
              <strong>ID:</strong> {baseSchema.schema_id}
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong>Intent:</strong> {baseSchema.intent}
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong>Nodes:</strong> {baseSchema.semantic_nodes.length}
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong>Zones:</strong> {baseSchema.variation_zones.length}
            </div>
            <div>
              <strong>Design Language:</strong>{' '}
              {baseSchema.aesthetic_profile.design_language}
            </div>
          </div>
        </section>
      )}

      {/* Generation Controls */}
      <section style={{ marginBottom: '40px' }}>
        <button
          onClick={handleGenerate}
          disabled={!baseSchema || isGenerating}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            fontWeight: 600,
            backgroundColor: isGenerating ? '#ccc' : '#0066FF',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: isGenerating ? 'not-allowed' : 'pointer'
          }}
        >
          {isGenerating ? 'Generating...' : 'Generate Variations'}
        </button>
      </section>

      {/* v1.2 Feature Demos */}
      {baseSchema && (
        <section style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '16px' }}>
            v1.2 Visionary Features
          </h2>

          <div style={{ display: 'grid', gap: '24px' }}>
            {/* Variation Prompt DSL */}
            <div style={{ padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>
                1. Variation Prompt DSL
              </h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                Natural language variation commands
              </p>
              <button
                onClick={() => {
                  const dsl = aiPromptGenerator.generateDSL('Make it 20% bigger and bold', 'hero_title');
                  const instructions = variationPromptParser.parse(dsl);
                  const result = variationPromptParser.execute(instructions, baseSchema);
                  console.log('🎯 DSL Result:', { dsl, instructions, result });
                  alert('DSL executed! Check console for results.');
                }}
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  backgroundColor: '#4CAF50',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Try: "Make it 20% bigger and bold"
              </button>
            </div>

            {/* Style Influence Blending */}
            <div style={{ padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>
                2. Style Influence Blending
              </h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                Multi-source style mixing with weighted vectors
              </p>
              <button
                onClick={() => {
                  const modernTech = styleInfluenceBlender.createInfluenceVector('modern_tech', 0.7);
                  const brutalist = styleInfluenceBlender.createInfluenceVector('brutalist', 0.3);
                  if (modernTech && brutalist) {
                    const blend = styleInfluenceBlender.blend([modernTech, brutalist], {
                      method: 'weighted_average',
                      normalize_weights: true
                    });
                    console.log('🎨 Style Blend:', blend);
                    alert(`Blended: ${blend.blend_name} (method: ${blend.blend_method})`);
                  }
                }}
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  backgroundColor: '#9C27B0',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Blend: Modern Tech (70%) + Brutalist (30%)
              </button>
            </div>

            {/* Temporal Variations */}
            <div style={{ padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>
                3. Temporal Design Variations
              </h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                Keyframe-based design evolution over time
              </p>
              <button
                onClick={() => {
                  const endSchema = JSON.parse(JSON.stringify(baseSchema)) as BaseSchema;
                  endSchema.semantic_nodes[1].properties.fontSize = 72; // Enlarge title
                  endSchema.semantic_nodes[1].properties.color = '#00FF88'; // Change color

                  const temporal = temporalVariationEngine.createTemporalSchema({
                    start_schema: baseSchema,
                    end_schema: endSchema,
                    duration: 3000,
                    easing: 'ease_in_out',
                    intermediate_keyframes: 2
                  });

                  console.log('⏱️ Temporal Schema:', temporal);
                  alert(`Created ${temporal.keyframes.length} keyframes over 3 seconds`);
                }}
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  backgroundColor: '#FF9800',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Animate: Title grows & changes color
              </button>
            </div>

            {/* Multi-Agent Teams */}
            <div style={{ padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>
                4. Multi-Agent Variation Teams
              </h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                Specialist agents negotiate design consensus
              </p>
              <button
                onClick={async () => {
                  const agents = [new LayoutAgent(), new AccessibilityAgent()];
                  const session = await agentNegotiator.negotiate(baseSchema, agents, 'weighted', 2);
                  const summary = agentNegotiator.getSummary(session);
                  console.log('🤝 Negotiation Session:', session);
                  alert(summary);
                }}
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  backgroundColor: '#2196F3',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Negotiate: Layout + Accessibility Agents
              </button>
            </div>

            {/* Cross-Schema Mutation */}
            <div style={{ padding: '20px', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>
                5. Cross-Schema Mutation
              </h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                Genetic operators for design evolution
              </p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => {
                    const parent_b = JSON.parse(JSON.stringify(baseSchema)) as BaseSchema;
                    parent_b.schema_id = ulid();
                    parent_b.semantic_nodes[1].properties.fontSize = 64;

                    const result = schemaMutator.crossover(baseSchema, parent_b, {
                      crossover_type: 'uniform',
                      crossover_rate: 0.5
                    });

                    console.log('🧬 Crossover:', result);
                    alert(`Crossover complete: ${result.mutation_points.length} mutation points`);
                  }}
                  style={{
                    padding: '8px 16px',
                    fontSize: '14px',
                    backgroundColor: '#E91E63',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Crossover
                </button>
                <button
                  onClick={() => {
                    const result = schemaMutator.pointMutation(baseSchema, 0.3);
                    console.log('🔬 Point Mutation:', result);
                    alert(`Mutation: ${result.mutation_points.length} properties mutated`);
                  }}
                  style={{
                    padding: '8px 16px',
                    fontSize: '14px',
                    backgroundColor: '#F44336',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Point Mutation
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Statistics */}
      {variations.length > 0 && (
        <section style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '16px' }}>
            Generation Statistics
          </h2>
          <div style={{ display: 'flex', gap: '16px' }}>
            <div
              style={{
                flex: 1,
                padding: '16px',
                backgroundColor: '#e8f5e9',
                borderRadius: '8px'
              }}
            >
              <div style={{ fontSize: '32px', fontWeight: 700, color: '#2e7d32' }}>
                {stats.safe}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Safe</div>
            </div>
            <div
              style={{
                flex: 1,
                padding: '16px',
                backgroundColor: '#fff3e0',
                borderRadius: '8px'
              }}
            >
              <div style={{ fontSize: '32px', fontWeight: 700, color: '#f57c00' }}>
                {stats.review}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Review</div>
            </div>
            <div
              style={{
                flex: 1,
                padding: '16px',
                backgroundColor: '#ffebee',
                borderRadius: '8px'
              }}
            >
              <div style={{ fontSize: '32px', fontWeight: 700, color: '#c62828' }}>
                {stats.unsafe}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>Unsafe</div>
            </div>
          </div>
        </section>
      )}

      {/* Variations List */}
      {variations.length > 0 && (
        <section>
          <h2 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '16px' }}>
            Generated Variations ({variations.length})
          </h2>
          <div style={{ display: 'grid', gap: '16px' }}>
            {variations.map((variation, index) => (
              <div
                key={variation.variation_id}
                style={{
                  padding: '20px',
                  backgroundColor: '#fff',
                  border: '1px solid #ddd',
                  borderRadius: '8px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ fontSize: '18px', fontWeight: 600 }}>
                    Variation #{index + 1}
                  </div>
                  <div>
                    <span
                      style={{
                        padding: '4px 12px',
                        backgroundColor:
                          variation.safety_score.recommendation === 'safe'
                            ? '#e8f5e9'
                            : variation.safety_score.recommendation === 'review'
                            ? '#fff3e0'
                            : '#ffebee',
                        color:
                          variation.safety_score.recommendation === 'safe'
                            ? '#2e7d32'
                            : variation.safety_score.recommendation === 'review'
                            ? '#f57c00'
                            : '#c62828',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 600
                      }}
                    >
                      {variation.safety_score.recommendation.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '14px' }}>
                  <div>
                    <strong>Style Distance:</strong>{' '}
                    {(variation.style_distance * 100).toFixed(1)}%
                  </div>
                  <div>
                    <strong>Semantic Drift:</strong> {variation.drift_category}
                  </div>
                  <div>
                    <strong>Safety Score:</strong>{' '}
                    {variation.safety_score.overall_score.toFixed(0)}
                  </div>
                  <div>
                    <strong>WCAG Level:</strong>{' '}
                    {variation.safety_score.accessibility_safety.wcag_level}
                  </div>
                  <div>
                    <strong>Modifiers Applied:</strong>{' '}
                    {variation.applied_modifiers.length}
                  </div>
                  <div>
                    <strong>Distance Band:</strong> {variation.safety_score.overall_score >= 80 ? 'safe' : variation.safety_score.overall_score >= 60 ? 'moderate' : 'high'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
