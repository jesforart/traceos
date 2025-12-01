/**
 * Gut Organ Type Definitions
 *
 * The Gut tastes interaction events and derives emotional state.
 * These types define the language of valuation — how the system
 * feels about user interactions.
 *
 * @provenance intent_gut_taste_001
 * @organ valuation
 */

/**
 * The five emotional states the Gut can sense.
 * Named as feelings, not technical states.
 */
export type MoodState = 'Calm' | 'Flow' | 'Frustration' | 'Chaos' | 'Exploration';

/**
 * A single taste of user interaction.
 *
 * The Gut senses these micro-reactions and accumulates
 * them into frustration_index and flow_probability.
 */
export interface ResonanceEvent {
  /** What type of interaction occurred */
  type:
    | 'stroke_accept'   // User kept the stroke
    | 'stroke_reject'   // User immediately erased stroke
    | 'undo'            // User pressed undo
    | 'redo'            // User pressed redo
    | 'ghost_accept'    // User accepted AI suggestion
    | 'ghost_reject'    // User dismissed AI suggestion
    | 'pause_detected'; // User paused for >2s

  /** When this happened (performance.now()) */
  timestamp: number;

  /** Which session this belongs to */
  sessionId: string;

  /**
   * Time between action and user response.
   * Fast undo (<500ms) = bitter taste (frustration)
   * Fast accept (<200ms) = sweet taste (flow)
   */
  latencyMs?: number;

  /**
   * Flag for erratic input detection.
   * When true for >10s with high frustration → Chaos
   */
  erraticInput?: boolean;

  /** Additional context for this event */
  context?: Record<string, unknown>;
}

/**
 * The Gut's current emotional state.
 *
 * This is the output of the valuation organ — a synthesis
 * of all recent micro-reactions into actionable feeling.
 */
export interface GutState {
  /** Current dominant mood */
  mood: MoodState;

  /**
   * How frustrated is the user? (0-1)
   * > 0.7 = reduce AI creativity by 50%
   */
  frustrationIndex: number;

  /**
   * How likely is the user in flow? (0-1)
   * > 0.8 = increase AI exploration by 30%
   */
  flowProbability: number;

  /** When this state was last calculated */
  lastUpdated: string; // ISO timestamp
}

/**
 * Read-only view of GutState for cross-organ consumption.
 *
 * CONSTRAINT: Only the Valuation organ may mutate GutState.
 * Brain, Vision, and other organs receive this read-only view.
 */
export type ReadonlyGutState = Readonly<GutState>;

/**
 * Accumulated taste preferences that affect future sensing.
 *
 * Over time, the Gut develops preferences — certain patterns
 * of interaction that consistently lead to flow or frustration.
 */
export interface TasteProfile {
  /** User's typical undo latency (baseline) */
  baselineUndoLatencyMs: number;

  /** User's typical acceptance latency (baseline) */
  baselineAcceptLatencyMs: number;

  /** Techniques that correlate with flow states */
  flowAssociatedTechniques: string[];

  /** Patterns that correlate with frustration */
  frustrationTriggers: string[];

  /** Last calibration timestamp */
  calibratedAt: string;
}

/**
 * Message type for WebSocket communication with backend Gut.
 */
export interface GutWebSocketMessage {
  type: 'resonance_batch' | 'gut_state' | 'error';
  events?: ResonanceEvent[];
  state?: GutState;
  error?: string;
}
