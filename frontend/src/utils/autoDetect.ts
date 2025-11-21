import { SemanticElement } from '../types/semantic';

/**
 * Trigger auto-detection on backend.
 */
export async function autoDetectElements(
  strokeIds?: string[]
): Promise<SemanticElement[]> {
  try {
    const response = await fetch('http://localhost:8000/api/semantic/auto-detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stroke_ids: strokeIds
      })
    });

    const elements = await response.json();
    return elements;
  } catch (error) {
    console.error('Auto-detection failed:', error);
    return [];
  }
}
