/**
 * Week 5: Style DNA Encoding - Artist Context Manager
 *
 * Manages artist context injection into DNA encoding.
 * Provides temporal awareness and learning state.
 */

import { ulid } from '../../utils/ulid';

/**
 * Artist Context - State for DNA encoding
 */
export interface ArtistContext {
  context_id: string;
  session_id: string;
  artist_id?: string;

  // Temporal state
  session_start_time: number;
  last_stroke_time: number;
  total_strokes_in_session: number;

  // Learning state
  total_sessions: number;
  total_lifetime_strokes: number;
  skill_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';

  // Fatigue state
  current_fatigue_level: number; // 0-1
  consecutive_work_minutes: number;
  last_break_time: number;

  // Current tool state
  current_tool: string;
  current_color: string;
  current_brush_size: number;

  // Session goals
  session_intent?: string;
  target_outcome?: string;

  // Metadata
  created_at: number;
  updated_at: number;
}

/**
 * Artist Context Manager
 * Tracks and injects context into DNA encoding
 */
export class ArtistContextManager {
  private context: ArtistContext;
  private context_history: ArtistContext[] = [];

  constructor(
    session_id: string = ulid(),
    artist_id?: string
  ) {
    this.context = this.createDefaultContext(session_id, artist_id);
  }

  /**
   * Create default context
   */
  private createDefaultContext(session_id: string, artist_id?: string): ArtistContext {
    return {
      context_id: ulid(),
      session_id,
      artist_id,
      session_start_time: Date.now(),
      last_stroke_time: Date.now(),
      total_strokes_in_session: 0,
      total_sessions: 1,
      total_lifetime_strokes: 0,
      skill_level: 'beginner',
      current_fatigue_level: 0,
      consecutive_work_minutes: 0,
      last_break_time: Date.now(),
      current_tool: 'pen',
      current_color: '#000000',
      current_brush_size: 5,
      created_at: Date.now(),
      updated_at: Date.now()
    };
  }

  /**
   * Get current context
   */
  getContext(): Readonly<ArtistContext> {
    return this.context;
  }

  /**
   * Update context after stroke
   */
  onStrokeComplete(stroke_data: {
    tool?: string;
    color?: string;
    brush_size?: number;
  }): void {
    const now = Date.now();
    const time_since_last_stroke = now - this.context.last_stroke_time;

    this.context.last_stroke_time = now;
    this.context.total_strokes_in_session++;
    this.context.total_lifetime_strokes++;
    this.context.updated_at = now;

    // Update current tool state
    if (stroke_data.tool) this.context.current_tool = stroke_data.tool;
    if (stroke_data.color) this.context.current_color = stroke_data.color;
    if (stroke_data.brush_size) this.context.current_brush_size = stroke_data.brush_size;

    // Update fatigue (simple model)
    const work_minutes = (now - this.context.session_start_time) / 60000;
    this.context.consecutive_work_minutes = work_minutes;

    // Fatigue increases with time, resets on breaks
    const minutes_since_break = (now - this.context.last_break_time) / 60000;
    this.context.current_fatigue_level = Math.min(1, minutes_since_break / 60); // Fatigue over 1 hour

    // Update skill level based on total strokes
    this.context.skill_level = this.calculateSkillLevel(this.context.total_lifetime_strokes);
  }

  /**
   * Register a break (resets fatigue)
   */
  onBreak(): void {
    this.context.last_break_time = Date.now();
    this.context.current_fatigue_level = 0;
    this.context.updated_at = Date.now();
  }

  /**
   * Start new session
   */
  startNewSession(session_id: string = ulid()): void {
    // Save current context to history
    this.context_history.push({ ...this.context });

    // Create new context
    const previous_context = this.context;
    this.context = this.createDefaultContext(session_id, previous_context.artist_id);

    // Carry over cumulative state
    this.context.total_sessions = previous_context.total_sessions + 1;
    this.context.total_lifetime_strokes = previous_context.total_lifetime_strokes;
    this.context.skill_level = previous_context.skill_level;
  }

  /**
   * Set session intent
   */
  setSessionIntent(intent: string, target_outcome?: string): void {
    this.context.session_intent = intent;
    this.context.target_outcome = target_outcome;
    this.context.updated_at = Date.now();
  }

  /**
   * Calculate skill level from stroke count
   */
  private calculateSkillLevel(total_strokes: number): 'beginner' | 'intermediate' | 'advanced' | 'expert' {
    if (total_strokes < 500) return 'beginner';
    if (total_strokes < 2000) return 'intermediate';
    if (total_strokes < 10000) return 'advanced';
    return 'expert';
  }

  /**
   * Get context snapshot for DNA encoding
   */
  getSnapshot(): {
    fatigue_level: number;
    session_duration_minutes: number;
    strokes_in_session: number;
    skill_level: string;
    is_fatigued: boolean;
  } {
    const now = Date.now();
    const session_duration = (now - this.context.session_start_time) / 60000;

    return {
      fatigue_level: this.context.current_fatigue_level,
      session_duration_minutes: session_duration,
      strokes_in_session: this.context.total_strokes_in_session,
      skill_level: this.context.skill_level,
      is_fatigued: this.context.current_fatigue_level > 0.7
    };
  }

  /**
   * Serialize context
   */
  serialize(): string {
    return JSON.stringify({
      context: this.context,
      history: this.context_history
    });
  }

  /**
   * Deserialize context
   */
  static deserialize(json: string): ArtistContextManager {
    const data = JSON.parse(json);
    const manager = new ArtistContextManager();
    manager.context = data.context;
    manager.context_history = data.history;
    return manager;
  }

  /**
   * Get context history
   */
  getHistory(): readonly ArtistContext[] {
    return this.context_history;
  }

  /**
   * Clear history
   */
  clearHistory(): void {
    this.context_history = [];
  }
}

/**
 * Global context manager instance
 */
export const globalContextManager = new ArtistContextManager();
