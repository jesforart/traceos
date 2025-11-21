/**
 * GPUDrawingSurface - WebGPU-accelerated drawing canvas.
 *
 * Features:
 * - GPU-accelerated stamp rendering at 60 FPS
 * - Artist profile-driven rendering
 * - Semantic weighting for facial features
 * - Touch/pointer input handling
 * - Responsive canvas sizing
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useWebGPU } from '../hooks/useWebGPU';
import { useGPURenderer, createStampFromPoint } from '../hooks/useGPURenderer';
import { configureCanvas, resizeCanvas } from '../gpu/device';
import { CanvasContext } from '../gpu/types';
import { ArtistProfile } from '../types/calibration';
import { FaceTag } from '../types/semantic';

export interface GPUDrawingSurfaceProps {
  /** Canvas width (CSS pixels) */
  width?: number;

  /** Canvas height (CSS pixels) */
  height?: number;

  /** Artist profile for rendering */
  profile?: ArtistProfile | null;

  /** Current drawing color */
  color?: string;

  /** Current semantic tag (for semantic weighting) */
  semanticTag?: FaceTag;

  /** Callback when drawing starts */
  onDrawStart?: () => void;

  /** Callback when drawing ends */
  onDrawEnd?: () => void;

  /** Callback for errors */
  onError?: (error: Error) => void;
}

export function GPUDrawingSurface(props: GPUDrawingSurfaceProps) {
  const {
    width = 800,
    height = 600,
    profile,
    color = '#000000',
    semanticTag,
    onDrawStart,
    onDrawEnd,
    onError
  } = props;

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [canvasContext, setCanvasContext] = useState<CanvasContext | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const animationFrameRef = useRef<number | null>(null);

  // Initialize WebGPU
  const { deviceContext, isInitializing, error: gpuError, isSupported } = useWebGPU();

  // Initialize renderer
  const {
    renderer,
    isReady,
    error: rendererError,
    addStamp,
    clearCanvas,
    render,
    resize
  } = useGPURenderer({
    deviceContext,
    canvasWidth: width,
    canvasHeight: height,
    profile
  });

  // Handle errors
  useEffect(() => {
    const error = gpuError || rendererError;
    if (error && onError) {
      onError(error);
    }
  }, [gpuError, rendererError, onError]);

  // Configure canvas
  useEffect(() => {
    if (!canvasRef.current || !deviceContext) return;

    const canvas = canvasRef.current;

    // Resize canvas to physical pixels
    resizeCanvas(canvas, deviceContext.devicePixelRatio);

    // Configure canvas for WebGPU
    const ctx = configureCanvas(canvas, deviceContext);
    setCanvasContext(ctx);
  }, [deviceContext]);

  // Handle canvas resize
  useEffect(() => {
    if (!canvasRef.current || !deviceContext) return;

    const canvas = canvasRef.current;
    resizeCanvas(canvas, deviceContext.devicePixelRatio);

    // Notify renderer
    resize(canvas.width, canvas.height);
  }, [width, height, deviceContext, resize]);

  // Render loop
  useEffect(() => {
    if (!isReady || !canvasContext) return;

    const renderLoop = () => {
      render(canvasContext);
      animationFrameRef.current = requestAnimationFrame(renderLoop);
    };

    animationFrameRef.current = requestAnimationFrame(renderLoop);

    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isReady, canvasContext, render]);

  // Parse hex color to RGBA
  const parseColor = useCallback((hexColor: string): [number, number, number, number] => {
    const hex = hexColor.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;
    return [r, g, b, 1.0];
  }, []);

  // Handle pointer down
  const handlePointerDown = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isReady || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const dpr = deviceContext?.devicePixelRatio || 1;

    const x = (event.clientX - rect.left) * dpr;
    const y = (event.clientY - rect.top) * dpr;
    const pressure = event.pressure || 0.5;

    const rgba = parseColor(color);
    const stamp = createStampFromPoint(x, y, pressure, rgba, semanticTag);

    addStamp(stamp);

    setIsDrawing(true);
    if (onDrawStart) {
      onDrawStart();
    }

    // Capture pointer
    canvas.setPointerCapture(event.pointerId);
  }, [isReady, deviceContext, color, semanticTag, addStamp, parseColor, onDrawStart]);

  // Handle pointer move
  const handlePointerMove = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !isReady || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const dpr = deviceContext?.devicePixelRatio || 1;

    const x = (event.clientX - rect.left) * dpr;
    const y = (event.clientY - rect.top) * dpr;
    const pressure = event.pressure || 0.5;

    const rgba = parseColor(color);
    const stamp = createStampFromPoint(x, y, pressure, rgba, semanticTag);

    addStamp(stamp);
  }, [isDrawing, isReady, deviceContext, color, semanticTag, addStamp, parseColor]);

  // Handle pointer up
  const handlePointerUp = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !canvasRef.current) return;

    setIsDrawing(false);
    if (onDrawEnd) {
      onDrawEnd();
    }

    // Release pointer
    canvasRef.current.releasePointerCapture(event.pointerId);
  }, [isDrawing, onDrawEnd]);

  // Render loading/error states
  if (!isSupported) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f0f0' }}>
        <p>WebGPU is not supported in this browser. Please use Chrome 113+, Edge 113+, or Safari 18+.</p>
      </div>
    );
  }

  if (isInitializing) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f0f0' }}>
        <p>Initializing GPU...</p>
      </div>
    );
  }

  if (gpuError) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#ffe0e0' }}>
        <p>GPU Error: {gpuError.message}</p>
      </div>
    );
  }

  if (rendererError) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#ffe0e0' }}>
        <p>Renderer Error: {rendererError.message}</p>
      </div>
    );
  }

  if (!isReady) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f0f0' }}>
        <p>Loading renderer...</p>
      </div>
    );
  }

  return (
    <div style={{ width, height, position: 'relative' }}>
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          touchAction: 'none',
          cursor: 'crosshair'
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      />
      {!isReady && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.8)'
        }}>
          <p>Initializing renderer...</p>
        </div>
      )}
    </div>
  );
}
