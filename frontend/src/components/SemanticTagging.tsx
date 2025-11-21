import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Stroke } from '../types';
import { SelectionTool } from './SelectionTool';
import { TagPanel } from './TagPanel';
import { useSelection } from '../hooks/useSelection';
import { useSemanticElements } from '../hooks/useSemanticElements';
import { FaceTag } from '../types/semantic';
import { autoDetectElements } from '../utils/autoDetect';
import { renderAllStrokes } from '../utils/strokeRenderer';
import { renderSelectionRegion } from '../utils/selectionUtils';

interface SemanticTaggingProps {
  strokes: Stroke[];
  onModeChange?: (mode: 'drawing' | 'tagging') => void;
}

export function SemanticTagging({ strokes, onModeChange }: SemanticTaggingProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ctx, setCtx] = useState<CanvasRenderingContext2D | null>(null);
  const [isAutoDetecting, setIsAutoDetecting] = useState(false);

  const selection = useSelection({
    strokes,
    onSelectionComplete: (strokeIds) => {
      console.log('Selected strokes:', strokeIds);
    }
  });

  const semanticElements = useSemanticElements();

  // Initialize canvas context
  useEffect(() => {
    if (canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      if (context) {
        setCtx(context);
      }
    }
  }, []);

  // Render strokes and selection region
  useEffect(() => {
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

    // Render all strokes
    renderAllStrokes(ctx, strokes);

    // Render selection region
    if (selection.selectionRegion && selection.isSelecting) {
      renderSelectionRegion(ctx, selection.selectionRegion);
    }

    // Highlight selected strokes
    if (selection.selectedStrokeIds.length > 0) {
      const selectedStrokes = strokes.filter(s =>
        selection.selectedStrokeIds.includes(s.id)
      );
      ctx.save();
      ctx.strokeStyle = '#0066FF';
      ctx.lineWidth = 3;
      selectedStrokes.forEach(stroke => {
        ctx.beginPath();
        stroke.points.forEach((p, i) => {
          if (i === 0) ctx.moveTo(p.x, p.y);
          else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();
      });
      ctx.restore();
    }
  }, [ctx, strokes, selection.selectionRegion, selection.isSelecting, selection.selectedStrokeIds]);

  const handleTagSelected = async (tag: FaceTag) => {
    if (selection.selectedStrokeIds.length === 0) return;

    await semanticElements.createElement(
      tag,
      selection.selectedStrokeIds,
      strokes
    );

    selection.clearSelection();
  };

  const handleAutoDetect = async () => {
    setIsAutoDetecting(true);

    try {
      const detected = await autoDetectElements();

      // Update elements list
      semanticElements.setElements(detected);

      console.log('Auto-detected:', detected.length, 'elements');
    } catch (error) {
      console.error('Auto-detection failed:', error);
    } finally {
      setIsAutoDetecting(false);
    }
  };

  // Canvas pointer handlers
  const handlePointerDown = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current || !selection.selectionMode) return;

      const rect = canvasRef.current.getBoundingClientRect();
      const point = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };

      e.currentTarget.setPointerCapture(e.pointerId);
      selection.startSelection(selection.selectionMode, point);
    },
    [selection]
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current || !selection.isSelecting) return;

      const rect = canvasRef.current.getBoundingClientRect();
      const point = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      };

      selection.continueSelection(point);
    },
    [selection]
  );

  const handlePointerUp = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      e.currentTarget.releasePointerCapture(e.pointerId);
      selection.completeSelection();
    },
    [selection]
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem',
        borderBottom: '1px solid #ccc',
        background: '#f5f5f5'
      }}>
        <h2 style={{ margin: 0 }}>Semantic Tagging</h2>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleAutoDetect}
            disabled={isAutoDetecting || strokes.length === 0}
            style={{
              padding: '0.5rem 1rem',
              background: isAutoDetecting ? '#ccc' : '#0066FF',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isAutoDetecting ? 'not-allowed' : 'pointer'
            }}
          >
            {isAutoDetecting ? 'Detecting...' : 'Auto-Detect'}
          </button>

          {onModeChange && (
            <button
              onClick={() => onModeChange('drawing')}
              style={{
                padding: '0.5rem 1rem',
                background: '#666',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Back to Drawing
            </button>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{
          flex: '0 0 300px',
          padding: '1rem',
          borderRight: '1px solid #ccc',
          overflowY: 'auto',
          background: 'white'
        }}>
          <SelectionTool
            currentMode={selection.selectionMode}
            onModeChange={(mode) => selection.setSelectionMode(mode)}
          />

          <div style={{ marginTop: '1rem' }}>
            {selection.selectedStrokeIds.length > 0 && (
              <p style={{
                padding: '0.5rem',
                background: '#e3f2fd',
                borderRadius: '4px',
                color: '#1976d2'
              }}>
                {selection.selectedStrokeIds.length} strokes selected
              </p>
            )}
          </div>
        </div>

        <div style={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '1rem',
          background: '#f5f5f5'
        }}>
          <canvas
            ref={canvasRef}
            width={1600}
            height={800}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
            style={{
              border: '1px solid #ccc',
              background: 'white',
              cursor: selection.selectionMode ? 'crosshair' : 'default',
              touchAction: 'none'
            }}
          />
        </div>

        <div style={{
          flex: '0 0 300px',
          padding: '1rem',
          borderLeft: '1px solid #ccc',
          overflowY: 'auto',
          background: 'white'
        }}>
          <TagPanel
            elements={semanticElements.elements}
            selectedStrokeIds={selection.selectedStrokeIds}
            onTagSelected={handleTagSelected}
            onElementDelete={semanticElements.deleteElement}
            onElementUpdate={semanticElements.updateLabel}
          />
        </div>
      </div>
    </div>
  );
}
