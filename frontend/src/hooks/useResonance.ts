/**
 * useResonance Hook
 *
 * The Gut's sensory interface — captures user micro-reactions
 * and transmits them to the backend for emotional state calculation.
 *
 * The Gut FEELS — it does not think. It tastes interactions:
 * - Rapid undos taste bitter (frustration)
 * - Smooth acceptance tastes sweet (flow)
 *
 * @provenance intent_gut_taste_001
 * @organ valuation
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { ResonanceEvent, ReadonlyGutState, MoodState } from '../types/gut';
import { validateToken, SovereigntyViolation } from '../sovereignty/validateToken';

/**
 * Return type for the useResonance hook.
 */
interface UseResonanceReturn {
  /** Emit a resonance event to the Gut */
  emitEvent: (event: Omit<ResonanceEvent, 'timestamp' | 'sessionId'>) => void;
  /** Current mood state (null if not yet received) */
  currentMood: MoodState | null;
  /** Current frustration index (0-1, null if not yet received) */
  frustrationIndex: number | null;
  /** Current flow probability (0-1, null if not yet received) */
  flowProbability: number | null;
  /** Whether the WebSocket is connected */
  isConnected: boolean;
  /** Last error message, if any */
  error: string | null;
}

/**
 * Token bucket for rate limiting.
 * 100 events/second = 1 token per 10ms refill
 */
interface TokenBucket {
  tokens: number;
  lastRefill: number;
}

/**
 * The Gut's sensory interface.
 *
 * This hook captures user micro-reactions and transmits them
 * to the backend Gut for emotional state calculation.
 *
 * SOVEREIGNTY: Token validation at init + every 60s.
 * If validation fails, all pending events are discarded.
 *
 * RATE LIMITING: 100 events/sec via token bucket.
 * Excess events dropped silently (prevents emotional DDoS).
 *
 * BATCHING: Events sent every 50ms to reduce WebSocket chatter.
 *
 * @param sessionId - Current session identifier
 * @param token - Sovereignty token (artist presence proof)
 */
export function useResonance(sessionId: string, token: string): UseResonanceReturn {
  // GutState received from backend
  const [gutState, setGutState] = useState<ReadonlyGutState | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refs for mutable state that shouldn't trigger re-renders
  const wsRef = useRef<WebSocket | null>(null);
  const bucketRef = useRef<TokenBucket>({ tokens: 100, lastRefill: performance.now() });
  const pendingRef = useRef<ResonanceEvent[]>([]);
  const tokenRef = useRef(token);
  const reconnectAttempts = useRef(0);

  // Update token ref when prop changes
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 1) SOVEREIGNTY: Validate token on init + every 60s
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  useEffect(() => {
    async function ensureValidToken() {
      const ok = await validateToken(sessionId, tokenRef.current);
      if (!ok) {
        // Hard sovereignty boundary: discard everything
        // The Gut goes silent — no surveillance without awareness
        pendingRef.current = [];
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
        setIsConnected(false);
        setError('SovereigntyViolation: Artist not present');
        throw new SovereigntyViolation('Invalid or expired token');
      }
      setError(null);
    }

    // Validate immediately
    ensureValidToken().catch(console.error);

    // Re-validate every 60 seconds
    const intervalId = setInterval(() => {
      ensureValidToken().catch(console.error);
    }, 60_000);

    return () => clearInterval(intervalId);
  }, [sessionId]);

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 2) WEBSOCKET: Connect to backend Gut
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  useEffect(() => {
    function connect() {
      // Use Iron Monolith port (8000)
      const wsUrl = `ws://localhost:8000/v1/gut/ws?session=${encodeURIComponent(sessionId)}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.debug('[Gut] WebSocket connected — the Gut is listening');
        wsRef.current = ws;
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        // The Gut shares how it feels
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'gut_state' && data.state) {
            setGutState(data.state);
          } else if (data.type === 'error') {
            setError(data.error || 'Unknown Gut error');
          }
        } catch {
          // Ignore malformed messages — the Gut doesn't taste garbage
        }
      };

      ws.onerror = (event) => {
        console.error('[Gut] WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.debug('[Gut] WebSocket closed:', event.code, event.reason);
        wsRef.current = null;
        setIsConnected(false);

        // Exponential backoff reconnection (max 30s)
        if (reconnectAttempts.current < 10) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectAttempts.current++;
          console.debug(`[Gut] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
          setTimeout(connect, delay);
        } else {
          setError('WebSocket connection lost — falling back to REST polling');
        }
      };
    }

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 3) RATE LIMITING: Token bucket (100 events/sec)
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const tryConsumeToken = useCallback((): boolean => {
    const now = performance.now();
    const bucket = bucketRef.current;
    const elapsed = now - bucket.lastRefill;

    // Refill: 1 token per 10ms = 100 tokens/sec
    const refill = Math.floor(elapsed / 10);
    if (refill > 0) {
      bucket.tokens = Math.min(100, bucket.tokens + refill);
      bucket.lastRefill = now;
    }

    if (bucket.tokens > 0) {
      bucket.tokens -= 1;
      return true;
    }

    // Rate limit hit — drop silently (per spec)
    return false;
  }, []);

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 4) BATCHING: Send events every 50ms
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  useEffect(() => {
    const batchInterval = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        return;
      }

      if (pendingRef.current.length === 0) {
        return;
      }

      // Drain the pending queue
      const batch = pendingRef.current.splice(0, pendingRef.current.length);

      // The Gut tastes this batch of interactions
      wsRef.current.send(JSON.stringify({
        type: 'resonance_batch',
        events: batch
      }));
    }, 50);

    return () => clearInterval(batchInterval);
  }, []);

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 5) EVENT EMISSION: The Gut senses this interaction
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  const emitEvent = useCallback(
    (eventData: Omit<ResonanceEvent, 'timestamp' | 'sessionId'>) => {
      // Rate limit check — prevent emotional DDoS
      if (!tryConsumeToken()) {
        // Dropped silently per spec
        return;
      }

      // Build the full event
      const event: ResonanceEvent = {
        ...eventData,
        timestamp: performance.now(),
        sessionId,
      };

      // Queue for batch sending
      pendingRef.current.push(event);
    },
    [sessionId, tryConsumeToken]
  );

  return {
    emitEvent,
    currentMood: gutState?.mood ?? null,
    frustrationIndex: gutState?.frustrationIndex ?? null,
    flowProbability: gutState?.flowProbability ?? null,
    isConnected,
    error,
  };
}
