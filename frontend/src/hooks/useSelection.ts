import { useState, useCallback } from 'react';
import { Stroke } from '../types';
import { SelectionRegion } from '../types/semantic';
import { isStrokeInRegion } from '../utils/selectionUtils';

interface UseSelectionOptions {
  strokes: Stroke[];
  onSelectionComplete?: (strokeIds: string[]) => void;
}

export function useSelection({ strokes, onSelectionComplete }: UseSelectionOptions) {
  const [selectionMode, setSelectionMode] = useState<'lasso' | 'box' | 'individual' | null>(null);
  const [selectionRegion, setSelectionRegion] = useState<SelectionRegion | null>(null);
  const [selectedStrokeIds, setSelectedStrokeIds] = useState<string[]>([]);
  const [isSelecting, setIsSelecting] = useState(false);

  /**
   * Start selection
   */
  const startSelection = useCallback(
    (mode: 'lasso' | 'box' | 'individual', point: { x: number; y: number }) => {
      setSelectionMode(mode);
      setIsSelecting(true);
      setSelectionRegion({
        type: mode,
        points: [point]
      });
    },
    []
  );

  /**
   * Continue selection (mouse/pointer move)
   */
  const continueSelection = useCallback(
    (point: { x: number; y: number }) => {
      if (!selectionRegion || !isSelecting) return;

      setSelectionRegion({
        ...selectionRegion,
        points: [...selectionRegion.points, point]
      });
    },
    [selectionRegion, isSelecting]
  );

  /**
   * Complete selection
   */
  const completeSelection = useCallback(() => {
    if (!selectionRegion) return;

    // Find strokes within selection region
    const selected = strokes
      .filter(stroke => isStrokeInRegion(stroke, selectionRegion))
      .map(stroke => stroke.id);

    setSelectedStrokeIds(selected);
    setIsSelecting(false);

    if (onSelectionComplete) {
      onSelectionComplete(selected);
    }
  }, [selectionRegion, strokes, onSelectionComplete]);

  /**
   * Clear selection
   */
  const clearSelection = useCallback(() => {
    setSelectionMode(null);
    setSelectionRegion(null);
    setSelectedStrokeIds([]);
    setIsSelecting(false);
  }, []);

  /**
   * Toggle individual stroke selection
   */
  const toggleStroke = useCallback(
    (strokeId: string) => {
      setSelectedStrokeIds(prev =>
        prev.includes(strokeId)
          ? prev.filter(id => id !== strokeId)
          : [...prev, strokeId]
      );
    },
    []
  );

  return {
    selectionMode,
    selectionRegion,
    selectedStrokeIds,
    isSelecting,
    startSelection,
    continueSelection,
    completeSelection,
    clearSelection,
    toggleStroke,
    setSelectionMode
  };
}
