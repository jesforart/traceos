import { useState, useCallback } from 'react';
import { SemanticElement, FaceTag } from '../types/semantic';
import { ulid } from '../utils/ulid';
import { Stroke } from '../types';

export function useSemanticElements() {
  const [elements, setElements] = useState<SemanticElement[]>([]);

  /**
   * Create semantic element from selected strokes
   */
  const createElement = useCallback(
    async (label: FaceTag, strokeIds: string[], strokes: Stroke[]) => {
      // Calculate bounding box
      const selectedStrokes = strokes.filter(s => strokeIds.includes(s.id));
      const allPoints = selectedStrokes.flatMap(s => s.points);

      const boundingBox = {
        min_x: Math.min(...allPoints.map(p => p.x)),
        min_y: Math.min(...allPoints.map(p => p.y)),
        max_x: Math.max(...allPoints.map(p => p.x)),
        max_y: Math.max(...allPoints.map(p => p.y))
      };

      const element: SemanticElement = {
        id: ulid(),
        label,
        stroke_ids: strokeIds,
        bounding_box: boundingBox,
        auto_detected: false,
        created_at: Date.now()
      };

      // Send to backend
      try {
        const response = await fetch('http://localhost:8000/api/semantic/elements', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            label,
            stroke_ids: strokeIds
          })
        });

        const savedElement = await response.json();
        setElements(prev => [...prev, savedElement]);

        return savedElement;
      } catch (error) {
        console.error('Failed to create semantic element:', error);
        // Still add locally even if backend fails
        setElements(prev => [...prev, element]);
        return element;
      }
    },
    []
  );

  /**
   * Delete semantic element
   */
  const deleteElement = useCallback(
    async (elementId: string) => {
      try {
        await fetch(`http://localhost:8000/api/semantic/elements/${elementId}`, {
          method: 'DELETE'
        });
      } catch (error) {
        console.error('Failed to delete element:', error);
      }

      setElements(prev => prev.filter(e => e.id !== elementId));
    },
    []
  );

  /**
   * Update element label
   */
  const updateLabel = useCallback(
    async (elementId: string, newLabel: FaceTag) => {
      try {
        await fetch(`http://localhost:8000/api/semantic/elements/${elementId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ label: newLabel })
        });
      } catch (error) {
        console.error('Failed to update element:', error);
      }

      setElements(prev =>
        prev.map(e => (e.id === elementId ? { ...e, label: newLabel } : e))
      );
    },
    []
  );

  /**
   * Clear all elements
   */
  const clearAll = useCallback(async () => {
    try {
      await fetch('http://localhost:8000/api/semantic/session', {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Failed to clear elements:', error);
    }

    setElements([]);
  }, []);

  /**
   * Load elements from backend
   */
  const loadElements = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/semantic/elements');
      const loadedElements = await response.json();
      setElements(loadedElements);
    } catch (error) {
      console.error('Failed to load elements:', error);
    }
  }, []);

  return {
    elements,
    createElement,
    deleteElement,
    updateLabel,
    clearAll,
    loadElements,
    setElements
  };
}
