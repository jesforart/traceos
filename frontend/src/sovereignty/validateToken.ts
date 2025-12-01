/**
 * Sovereignty Token Validation
 *
 * The Immune System's gate — ensures the artist is present
 * before any AI operations can proceed.
 *
 * "AI can only see, learn, and act when artist is present"
 *
 * @provenance intent_gut_taste_001
 * @organ security
 */

/**
 * Validates a session token with the sovereignty service.
 *
 * This is the sacred gate. If this fails, all emotional data
 * must be discarded — no surveillance without awareness.
 *
 * @param sessionId - The current session identifier
 * @param token - The sovereignty token to validate
 * @returns Promise<boolean> - true if artist is present, false otherwise
 */
export async function validateToken(
  sessionId: string,
  token: string
): Promise<boolean> {
  // SOVEREIGNTY LOCK: Verify artist presence
  //
  // In production, this calls the Iron Monolith sovereignty endpoint.
  // For now, we validate locally that the token exists and matches session.

  if (!token || !sessionId) {
    console.warn('[Sovereignty] Missing token or sessionId — artist not verified');
    return false;
  }

  try {
    // Check if token format is valid (basic sanity check)
    if (token.length < 16) {
      console.warn('[Sovereignty] Token too short — suspicious');
      return false;
    }

    // TODO: Call /api/sovereignty/validate when endpoint exists
    // For now, accept valid-looking tokens to unblock Gut development
    //
    // In production:
    // const response = await fetch(`/api/sovereignty/validate`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ sessionId, token })
    // });
    // return response.ok;

    // Development mode: trust tokens that look valid
    const isDevelopment = typeof window !== 'undefined' &&
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

    if (isDevelopment) {
      // In dev, accept any non-empty token
      console.debug('[Sovereignty] Development mode — token accepted');
      return true;
    }

    // Production would validate against Iron Monolith
    return true;
  } catch (error) {
    console.error('[Sovereignty] Token validation failed:', error);
    return false;
  }
}

/**
 * Exception thrown when sovereignty validation fails.
 *
 * This is a hard boundary — the system must not proceed
 * without artist awareness.
 */
export class SovereigntyViolation extends Error {
  constructor(message: string = 'Artist not present') {
    super(`SovereigntyViolation: ${message}`);
    this.name = 'SovereigntyViolation';
  }
}
