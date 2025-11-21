import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Stroke, Layer } from '../types';
import { useStrokeCapture } from '../hooks/useStrokeCapture';
import { renderStroke, renderAllStrokes } from '../utils/strokeRenderer';
import { ulid } from '../utils/ulid';

interface DrawingSurfaceProps {
  width?: number;
  height?: number;
  mode?: 'normal' | 'calibration' | 'markup';
  onStrokeCaptured?: (stroke: Stroke) => void;
}

export function DrawingSurface({
  width = 1920,
  height = 1080,
  mode = 'normal',
  onStrokeCaptured
}: DrawingSurfaceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ctx, setCtx] = useState<CanvasRenderingContext2D | null>(null);

  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [layers, setLayers] = useState<Layer[]>([
    {
      id: ulid(),
      name: 'Layer 1',
      visible: true,
      opacity: 1.0,
      blend_mode: 'normal',
      z_index: 0,
      stroke_ids: [],
      created_at: Date.now()
    }
  ]);
  const [currentLayerId, setCurrentLayerId] = useState(layers[0].id);

  const [currentTool, setCurrentTool] = useState<'pen' | 'brush' | 'eraser' | 'marker'>('pen');
  const [currentColor, setCurrentColor] = useState('#000000');
  const [currentWidth, setCurrentWidth] = useState(3);

  useEffect(() => {
    if (canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      if (context) {
        setCtx(context);
      }
    }
  }, []);

  const handleStrokeComplete = useCallback(
    async (stroke: Stroke) => {
      setStrokes(prev => [...prev, stroke]);

      setLayers(prev =>
        prev.map(layer =>
          layer.id === currentLayerId
            ? { ...layer, stroke_ids: [...layer.stroke_ids, stroke.id] }
            : layer
        )
      );

      try {
        await fetch('http://localhost:8000/api/drawing/strokes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(stroke)
        });
      } catch (error) {
        console.error('Failed to save stroke:', error);
      }

      if (mode === 'calibration' && onStrokeCaptured) {
        onStrokeCaptured(stroke);
      }
    },
    [currentLayerId, mode, onStrokeCaptured]
  );

  const strokeCapture = useStrokeCapture({
    tool: currentTool,
    color: currentColor,
    width: currentWidth,
    currentLayerId,
    onStrokeComplete: handleStrokeComplete
  });

  const handlePointerDown = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current) return;

      // Only accept pen input, ignore touch and mouse
      if (e.pointerType !== 'pen') return;

      e.currentTarget.setPointerCapture(e.pointerId);
      strokeCapture.startStroke(e.nativeEvent, canvasRef.current);
    },
    [strokeCapture]
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      if (!canvasRef.current || !strokeCapture.isDrawing) return;

      // Only accept pen input, ignore touch and mouse
      if (e.pointerType !== 'pen') return;

      strokeCapture.continueStroke(e.nativeEvent, canvasRef.current);
    },
    [strokeCapture]
  );

  const handlePointerUp = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      e.currentTarget.releasePointerCapture(e.pointerId);
      strokeCapture.endStroke();
    },
    [strokeCapture]
  );

  useEffect(() => {
    if (!ctx) return;

    renderAllStrokes(ctx, strokes);

    if (strokeCapture.currentStroke) {
      renderStroke(ctx, strokeCapture.currentStroke, { preview: true });
    }
  }, [ctx, strokes, strokeCapture.currentStroke]);

  return (
    <div className="drawing-surface">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        style={{
          touchAction: 'none',
          cursor: 'crosshair',
          border: '1px solid #ccc',
          userSelect: 'none',
          WebkitUserSelect: 'none',
          WebkitTouchCallout: 'none',
          WebkitTapHighlightColor: 'transparent'
        }}
      />

      <div className="tool-info">
        <p>Tool: {currentTool}</p>
        <p>Color: {currentColor}</p>
        <p>Width: {currentWidth}px</p>
        <p>Strokes: {strokes.length}</p>
      </div>
    </div>
  );
}
