/**
 * Week 5: Style DNA Encoding - Web Worker
 *
 * Background processing for ImageDNA and TemporalDNA encoding.
 * Runs off main thread to avoid blocking UI.
 */

/**
 * Worker Message Types
 */
export type WorkerMessage =
  | {
      type: 'encode_image';
      payload: {
        image_data: ImageData;
        session_id: string;
        snapshot_id: string;
      };
    }
  | {
      type: 'encode_temporal';
      payload: {
        session_data: any;
        context: any;
      };
    }
  | {
      type: 'calculate_distance';
      payload: {
        dna_a: Float32Array;
        dna_b: Float32Array;
        metric: 'euclidean' | 'cosine' | 'manhattan';
      };
    }
  | {
      type: 'batch_distance';
      payload: {
        query: Float32Array;
        targets: Float32Array[];
        metric: 'euclidean' | 'cosine' | 'manhattan';
      };
    };

/**
 * Worker Response Types
 */
export type WorkerResponse =
  | {
      type: 'encode_image_result';
      payload: {
        image_dna: any;
        encoding_time_ms: number;
      };
    }
  | {
      type: 'encode_temporal_result';
      payload: {
        temporal_dna: any;
        encoding_time_ms: number;
      };
    }
  | {
      type: 'distance_result';
      payload: {
        distance: number;
      };
    }
  | {
      type: 'batch_distance_result';
      payload: {
        distances: number[];
      };
    }
  | {
      type: 'error';
      payload: {
        error: string;
      };
    };

/**
 * Worker message handler
 */
self.onmessage = async (event: MessageEvent<WorkerMessage>) => {
  const start_time = performance.now();

  try {
    switch (event.data.type) {
      case 'encode_image':
        await handleEncodeImage(event.data.payload, start_time);
        break;

      case 'encode_temporal':
        await handleEncodeTemporal(event.data.payload, start_time);
        break;

      case 'calculate_distance':
        handleCalculateDistance(event.data.payload);
        break;

      case 'batch_distance':
        handleBatchDistance(event.data.payload);
        break;

      default:
        throw new Error('Unknown message type');
    }
  } catch (error) {
    const response: WorkerResponse = {
      type: 'error',
      payload: {
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    };
    self.postMessage(response);
  }
};

/**
 * Handle ImageDNA encoding
 */
async function handleEncodeImage(
  payload: { image_data: ImageData; session_id: string; snapshot_id: string },
  start_time: number
): Promise<void> {
  // Simulate VGG19 encoding
  // In real implementation, this would use a pre-trained VGG19 model
  const features = new Float32Array(512);
  for (let i = 0; i < 512; i++) {
    features[i] = Math.random(); // Placeholder
  }

  const encoding_time_ms = performance.now() - start_time;

  const response: WorkerResponse = {
    type: 'encode_image_result',
    payload: {
      image_dna: {
        dna_id: generateId(),
        session_id: payload.session_id,
        snapshot_id: payload.snapshot_id,
        features,
        dominant_colors: ['#FF0000', '#00FF00', '#0000FF'],
        texture_features: {
          complexity: 0.5,
          contrast: 0.7,
          energy: 0.6
        },
        width: payload.image_data.width,
        height: payload.image_data.height,
        timestamp: Date.now(),
        encoding_time_ms
      },
      encoding_time_ms
    }
  };

  self.postMessage(response);
}

/**
 * Handle TemporalDNA encoding
 */
async function handleEncodeTemporal(
  payload: { session_data: any; context: any },
  start_time: number
): Promise<void> {
  // Simulate temporal encoding
  const features = new Float32Array(32);
  for (let i = 0; i < 32; i++) {
    features[i] = Math.random(); // Placeholder
  }

  const encoding_time_ms = performance.now() - start_time;

  const response: WorkerResponse = {
    type: 'encode_temporal_result',
    payload: {
      temporal_dna: {
        dna_id: generateId(),
        session_id: payload.session_data.session_id,
        features,
        learning_phase: 'exploration',
        skill_progression: 0.5,
        fatigue_level: 0.3,
        focus_score: 0.8,
        flow_state: false,
        total_sessions: 1,
        total_strokes: 100,
        timestamp: Date.now(),
        encoding_time_ms
      },
      encoding_time_ms
    }
  };

  self.postMessage(response);
}

/**
 * Handle distance calculation
 */
function handleCalculateDistance(payload: {
  dna_a: Float32Array;
  dna_b: Float32Array;
  metric: 'euclidean' | 'cosine' | 'manhattan';
}): void {
  const distance = calculateDistance(payload.dna_a, payload.dna_b, payload.metric);

  const response: WorkerResponse = {
    type: 'distance_result',
    payload: { distance }
  };

  self.postMessage(response);
}

/**
 * Handle batch distance calculation
 */
function handleBatchDistance(payload: {
  query: Float32Array;
  targets: Float32Array[];
  metric: 'euclidean' | 'cosine' | 'manhattan';
}): void {
  const distances = payload.targets.map((target) =>
    calculateDistance(payload.query, target, payload.metric)
  );

  const response: WorkerResponse = {
    type: 'batch_distance_result',
    payload: { distances }
  };

  self.postMessage(response);
}

/**
 * Calculate distance between two DNA vectors
 */
function calculateDistance(
  a: Float32Array,
  b: Float32Array,
  metric: 'euclidean' | 'cosine' | 'manhattan'
): number {
  if (a.length !== b.length) {
    throw new Error('DNA vectors must have same dimension');
  }

  switch (metric) {
    case 'euclidean':
      return euclideanDistance(a, b);
    case 'cosine':
      return cosineDistance(a, b);
    case 'manhattan':
      return manhattanDistance(a, b);
  }
}

/**
 * Euclidean distance
 */
function euclideanDistance(a: Float32Array, b: Float32Array): number {
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    const diff = a[i] - b[i];
    sum += diff * diff;
  }
  return Math.sqrt(sum);
}

/**
 * Cosine distance (1 - cosine similarity)
 */
function cosineDistance(a: Float32Array, b: Float32Array): number {
  let dot = 0;
  let mag_a = 0;
  let mag_b = 0;

  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    mag_a += a[i] * a[i];
    mag_b += b[i] * b[i];
  }

  const similarity = dot / (Math.sqrt(mag_a) * Math.sqrt(mag_b));
  return 1 - similarity;
}

/**
 * Manhattan distance
 */
function manhattanDistance(a: Float32Array, b: Float32Array): number {
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    sum += Math.abs(a[i] - b[i]);
  }
  return sum;
}

/**
 * Generate unique ID (simple version for worker)
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
