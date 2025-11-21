/**
 * ProvenanceHooks - Synchronize replay data with provenance system
 *
 * Week 3 - Option D: Next-Gen Replay Engine
 * Phase 4: System Integration
 *
 * Bridges the replay engine with the provenance tracking system:
 * - Sync temporal features to provenance records
 * - Link replay sessions to artist profiles
 * - Track drawing progression for authenticity verification
 * - Enable temporal queries on provenance data
 */

import { TemporalFeatures, StrokeTemporalFeatures } from '../ai/AIProfileHooks';

/**
 * Provenance record with temporal data
 */
export interface ProvenanceRecord {
  /** Record ID */
  id: string;

  /** Artist profile ID */
  artistProfileId: string;

  /** Session ID (links to replay session) */
  sessionId: string;

  /** Timestamp of record creation */
  timestamp: number;

  /** Temporal features */
  temporal: TemporalFeatures;

  /** Per-stroke features (optional, for detailed analysis) */
  strokeFeatures?: StrokeTemporalFeatures[];

  /** Authenticity score (0-1) */
  authenticityScore?: number;

  /** Metadata */
  metadata: {
    deviceType: string;
    canvasSize: { width: number; height: number };
    traceOSVersion: string;
  };
}

/**
 * Temporal query parameters
 */
export interface TemporalQuery {
  /** Artist profile ID (optional) */
  artistProfileId?: string;

  /** Start timestamp (optional) */
  startTime?: number;

  /** End timestamp (optional) */
  endTime?: number;

  /** Minimum session duration (milliseconds) */
  minDuration?: number;

  /** Maximum session duration (milliseconds) */
  maxDuration?: number;

  /** Minimum stroke count */
  minStrokes?: number;

  /** Filter by stroke class distribution */
  strokeClassFilter?: {
    minGesture?: number;
    minDetail?: number;
    minShading?: number;
    minCorrective?: number;
  };
}

/**
 * Authenticity verification result
 */
export interface AuthenticityResult {
  /** Overall authenticity score (0-1) */
  score: number;

  /** Confidence in the score (0-1) */
  confidence: number;

  /** Individual component scores */
  components: {
    /** Temporal consistency (matches artist profile?) */
    temporalConsistency: number;

    /** Input device fingerprint (Apple Pencil, mouse, etc.) */
    deviceFingerprint: number;

    /** Drawing style consistency */
    styleConsistency: number;

    /** Pause pattern consistency */
    pausePattern: number;
  };

  /** Flags for suspicious patterns */
  flags: string[];
}

/**
 * ProvenanceHooks - Integrates replay engine with provenance system
 */
export class ProvenanceHooks {
  private apiBaseUrl: string;

  constructor(apiBaseUrl: string = 'http://localhost:8001/api') {
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Create a provenance record with temporal features
   *
   * @param temporal Temporal features from replay engine
   * @param artistProfileId Artist profile ID
   * @param sessionId Session ID
   * @param strokeFeatures Optional per-stroke features
   * @returns Created provenance record
   */
  async createProvenanceRecord(
    temporal: TemporalFeatures,
    artistProfileId: string,
    sessionId: string,
    strokeFeatures?: StrokeTemporalFeatures[]
  ): Promise<ProvenanceRecord> {
    const record: ProvenanceRecord = {
      id: this.generateRecordId(),
      artistProfileId,
      sessionId,
      timestamp: Date.now(),
      temporal,
      strokeFeatures,
      metadata: {
        deviceType: navigator.userAgent,
        canvasSize: { width: 800, height: 600 },
        traceOSVersion: '1.0.0-week3'
      }
    };

    // Send to backend
    const response = await fetch(`${this.apiBaseUrl}/provenance/records`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(record)
    });

    if (!response.ok) {
      throw new Error(`Failed to create provenance record: ${response.statusText}`);
    }

    const savedRecord = await response.json();

    console.log('[ProvenanceHooks] Created provenance record:', savedRecord.id);

    return savedRecord;
  }

  /**
   * Query provenance records by temporal criteria
   *
   * @param query Temporal query parameters
   * @returns Matching provenance records
   */
  async queryByTemporal(query: TemporalQuery): Promise<ProvenanceRecord[]> {
    const queryParams = new URLSearchParams();

    if (query.artistProfileId) {
      queryParams.append('artistProfileId', query.artistProfileId);
    }

    if (query.startTime !== undefined) {
      queryParams.append('startTime', query.startTime.toString());
    }

    if (query.endTime !== undefined) {
      queryParams.append('endTime', query.endTime.toString());
    }

    if (query.minDuration !== undefined) {
      queryParams.append('minDuration', query.minDuration.toString());
    }

    if (query.maxDuration !== undefined) {
      queryParams.append('maxDuration', query.maxDuration.toString());
    }

    if (query.minStrokes !== undefined) {
      queryParams.append('minStrokes', query.minStrokes.toString());
    }

    const response = await fetch(`${this.apiBaseUrl}/provenance/records?${queryParams.toString()}`);

    if (!response.ok) {
      throw new Error(`Failed to query provenance records: ${response.statusText}`);
    }

    const records: ProvenanceRecord[] = await response.json();

    console.log('[ProvenanceHooks] Queried', records.length, 'records');

    return records;
  }

  /**
   * Verify authenticity of a drawing session
   *
   * Compares temporal features with artist profile baseline
   *
   * @param temporal Temporal features to verify
   * @param artistProfileId Artist profile ID
   * @returns Authenticity verification result
   */
  async verifyAuthenticity(
    temporal: TemporalFeatures,
    artistProfileId: string
  ): Promise<AuthenticityResult> {
    const response = await fetch(`${this.apiBaseUrl}/provenance/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ temporal, artistProfileId })
    });

    if (!response.ok) {
      throw new Error(`Failed to verify authenticity: ${response.statusText}`);
    }

    const result: AuthenticityResult = await response.json();

    console.log('[ProvenanceHooks] Authenticity score:', result.score);

    return result;
  }

  /**
   * Get temporal baseline for an artist
   *
   * Computes aggregate statistics across all sessions
   *
   * @param artistProfileId Artist profile ID
   * @returns Baseline temporal features
   */
  async getArtistBaseline(artistProfileId: string): Promise<TemporalFeatures> {
    const response = await fetch(`${this.apiBaseUrl}/provenance/baseline/${artistProfileId}`);

    if (!response.ok) {
      throw new Error(`Failed to get artist baseline: ${response.statusText}`);
    }

    const baseline: TemporalFeatures = await response.json();

    console.log('[ProvenanceHooks] Retrieved baseline for artist:', artistProfileId);

    return baseline;
  }

  /**
   * Update provenance record with authenticity score
   *
   * @param recordId Provenance record ID
   * @param authenticityScore Authenticity score (0-1)
   */
  async updateAuthenticityScore(recordId: string, authenticityScore: number): Promise<void> {
    const response = await fetch(`${this.apiBaseUrl}/provenance/records/${recordId}/authenticity`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ authenticityScore })
    });

    if (!response.ok) {
      throw new Error(`Failed to update authenticity score: ${response.statusText}`);
    }

    console.log('[ProvenanceHooks] Updated authenticity score for record:', recordId);
  }

  /**
   * Link temporal features to artist profile
   *
   * Updates the artist profile with temporal statistics
   *
   * @param artistProfileId Artist profile ID
   * @param temporal Temporal features
   */
  async linkToProfile(artistProfileId: string, temporal: TemporalFeatures): Promise<void> {
    const response = await fetch(`${this.apiBaseUrl}/calibration/profiles/${artistProfileId}/temporal`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ temporal })
    });

    if (!response.ok) {
      throw new Error(`Failed to link temporal features to profile: ${response.statusText}`);
    }

    console.log('[ProvenanceHooks] Linked temporal features to profile:', artistProfileId);
  }

  /**
   * Export provenance records for analysis
   *
   * @param query Temporal query parameters
   * @param format Export format (json or csv)
   * @returns Exported data
   */
  async exportRecords(query: TemporalQuery, format: 'json' | 'csv' = 'json'): Promise<string> {
    const records = await this.queryByTemporal(query);

    if (format === 'json') {
      return JSON.stringify(records, null, 2);
    } else {
      // CSV export
      return this.recordsToCSV(records);
    }
  }

  /**
   * Convert provenance records to CSV format
   */
  private recordsToCSV(records: ProvenanceRecord[]): string {
    if (records.length === 0) {
      return '';
    }

    const headers = [
      'id',
      'artistProfileId',
      'sessionId',
      'timestamp',
      'sessionDuration',
      'totalStrokes',
      'gestureStrokes',
      'detailStrokes',
      'shadingStrokes',
      'correctiveStrokes',
      'momentumMean',
      'velocityMean',
      'authenticityScore'
    ];

    const rows = records.map(r => [
      r.id,
      r.artistProfileId,
      r.sessionId,
      r.timestamp,
      r.temporal.sessionDuration,
      r.temporal.totalStrokes,
      r.temporal.strokeClasses.gesture,
      r.temporal.strokeClasses.detail,
      r.temporal.strokeClasses.shading,
      r.temporal.strokeClasses.corrective,
      r.temporal.momentum.overall.mean,
      r.temporal.velocity.meanSmoothed,
      r.authenticityScore ?? ''
    ]);

    return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  }

  /**
   * Generate a unique record ID
   */
  private generateRecordId(): string {
    return `prov_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }

  /**
   * Compare two temporal feature sets for similarity
   *
   * Returns a similarity score (0-1)
   *
   * @param features1 First temporal features
   * @param features2 Second temporal features
   * @returns Similarity score (0-1)
   */
  calculateSimilarity(features1: TemporalFeatures, features2: TemporalFeatures): number {
    // Weighted similarity across multiple dimensions
    const weights = {
      momentum: 0.3,
      velocity: 0.2,
      strokeClasses: 0.2,
      rhythm: 0.15,
      pressure: 0.15
    };

    // Momentum similarity (normalized difference)
    const momentumSim = 1 - Math.min(1, Math.abs(features1.momentum.overall.mean - features2.momentum.overall.mean) / 200);

    // Velocity similarity
    const velocitySim = 1 - Math.min(1, Math.abs(features1.velocity.meanSmoothed - features2.velocity.meanSmoothed) / 200);

    // Stroke class distribution similarity (cosine similarity)
    const classVector1 = [
      features1.strokeClasses.gesture,
      features1.strokeClasses.detail,
      features1.strokeClasses.shading,
      features1.strokeClasses.corrective
    ];
    const classVector2 = [
      features2.strokeClasses.gesture,
      features2.strokeClasses.detail,
      features2.strokeClasses.shading,
      features2.strokeClasses.corrective
    ];
    const classCosineSim = this.cosineSimilarity(classVector1, classVector2);

    // Rhythm similarity
    const rhythmSim = 1 - Math.min(1, Math.abs(features1.rhythm.strokesPerMinute - features2.rhythm.strokesPerMinute) / 100);

    // Pressure similarity
    const pressureSim = 1 - Math.min(1, Math.abs(features1.pressure.mean - features2.pressure.mean));

    // Weighted average
    const similarity =
      weights.momentum * momentumSim +
      weights.velocity * velocitySim +
      weights.strokeClasses * classCosineSim +
      weights.rhythm * rhythmSim +
      weights.pressure * pressureSim;

    return similarity;
  }

  /**
   * Calculate cosine similarity between two vectors
   */
  private cosineSimilarity(vec1: number[], vec2: number[]): number {
    if (vec1.length !== vec2.length) {
      throw new Error('Vectors must have the same length');
    }

    const dotProduct = vec1.reduce((sum, val, i) => sum + val * vec2[i], 0);
    const mag1 = Math.sqrt(vec1.reduce((sum, val) => sum + val * val, 0));
    const mag2 = Math.sqrt(vec2.reduce((sum, val) => sum + val * val, 0));

    if (mag1 === 0 || mag2 === 0) {
      return 0;
    }

    return dotProduct / (mag1 * mag2);
  }
}
