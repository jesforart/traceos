/**
 * useStrokeCapture - Enhanced stroke capture with smoothing and velocity
 *
 * IMPROVEMENT #11: 120Hz throttling (RAF-based)
 * IMPROVEMENT #14: Velocity calculation for GPU
 * IMPROVEMENT #3: Zero-pressure fix for first frame
 * IMPROVEMENT #5: iPad-specific smoothing
 */

import { useState, useCallback, useRef } from 'react';
import { Stroke, Point } from '../types';
import { ulid } from '../utils/ulid';

interface UseStrokeCaptureOptions {
  tool: 'pen' | 'brush' | 'eraser' | 'marker';
  color: string;
  width: number;
  currentLayerId: string;
  onStrokeComplete?: (stroke: Stroke) => void;
}

export function useStrokeCapture(options: UseStrokeCaptureOptions) {
  const [currentStroke, setCurrentStroke] = useState<Stroke | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);

  // IMPROVEMENT #3: Track last pressure to avoid zero-pressure dips
  const lastPressureRef = useRef(0.5);

  // IMPROVEMENT #5: Position smoothing for iPad
  const lastPositionRef = useRef<{ x: number; y: number } | null>(null);

  // IMPROVEMENT #11: 120Hz throttling with RAF
  const rafPendingRef = useRef(false);
  const pendingEventRef = useRef<{ event: PointerEvent; canvas: HTMLCanvasElement } | null>(null);

  // IMPROVEMENT #14: Track time for velocity calculation
  const lastTimestampRef = useRef(0);

  // IMPROVEMENT #3: Smooth pressure to avoid zero-pressure dips
  const smoothPressure = (pressure: number, pointerType: string): number => {
    // Fix first-frame zero-pressure bug
    if (pressure === 0 && pointerType === 'pen') {
      return lastPressureRef.current;
    }

    if (pressure === 0 || pressure === 0.5) {
      return 0.5;
    }

    // Exponential moving average
    const smoothed = 0.7 * pressure + 0.3 * lastPressureRef.current;
    lastPressureRef.current = smoothed;
    return smoothed;
  };

  // IMPROVEMENT #5: Smooth position for iPad
  const smoothPosition = (x: number, y: number): { x: number; y: number } => {
    if (!lastPositionRef.current) {
      lastPositionRef.current = { x, y };
      return { x, y };
    }

    const smoothX = 0.8 * x + 0.2 * lastPositionRef.current.x;
    const smoothY = 0.8 * y + 0.2 * lastPositionRef.current.y;

    lastPositionRef.current = { x: smoothX, y: smoothY };
    return { x: smoothX, y: smoothY };
  };

  // IMPROVEMENT #14: Calculate velocity
  const calculateVelocity = (x: number, y: number, timestamp: number): number => {
    if (!lastPositionRef.current || lastTimestampRef.current === 0) {
      return 0;
    }

    const dx = x - lastPositionRef.current.x;
    const dy = y - lastPositionRef.current.y;
    const dt = timestamp - lastTimestampRef.current;

    if (dt === 0) return 0;

    const distance = Math.sqrt(dx * dx + dy * dy);
    const velocity = distance / dt; // pixels per millisecond

    return velocity;
  };

  const startStroke = useCallback(
    (event: PointerEvent, canvas: HTMLCanvasElement) => {
      const rect = canvas.getBoundingClientRect();
      const rawX = event.clientX - rect.left;
      const rawY = event.clientY - rect.top;

      lastPositionRef.current = { x: rawX, y: rawY };
      lastTimestampRef.current = event.timeStamp;

      const point: Point = {
        x: rawX,
        y: rawY,
        pressure: smoothPressure(event.pressure, event.pointerType),
        tilt_x: event.tiltX || 0,
        tilt_y: event.tiltY || 0,
        timestamp: event.timeStamp,
        velocity: 0 // First point has no velocity
      };

      const newStroke: Stroke = {
        id: ulid(),
        points: [point],
        tool: options.tool,
        color: options.color,
        width: options.width,
        layer_id: options.currentLayerId,
        created_at: Date.now()
      };

      setCurrentStroke(newStroke);
      setIsDrawing(true);
    },
    [options.tool, options.color, options.width, options.currentLayerId]
  );

  const continueStrokeInternal = useCallback(
    (event: PointerEvent, canvas: HTMLCanvasElement) => {
      if (!currentStroke || !isDrawing) return;

      const rect = canvas.getBoundingClientRect();
      const rawX = event.clientX - rect.left;
      const rawY = event.clientY - rect.top;

      const smoothed = smoothPosition(rawX, rawY);
      const velocity = calculateVelocity(smoothed.x, smoothed.y, event.timeStamp);

      lastTimestampRef.current = event.timeStamp;

      const point: Point = {
        x: smoothed.x,
        y: smoothed.y,
        pressure: smoothPressure(event.pressure, event.pointerType),
        tilt_x: event.tiltX || 0,
        tilt_y: event.tiltY || 0,
        timestamp: event.timeStamp,
        velocity // IMPROVEMENT #14: Store velocity for GPU
      };

      setCurrentStroke(prev => {
        if (!prev) return null;
        return {
          ...prev,
          points: [...prev.points, point]
        };
      });
    },
    [currentStroke, isDrawing]
  );

  // IMPROVEMENT #11: Throttled continueStroke (120Hz max via RAF)
  const continueStroke = useCallback(
    (event: PointerEvent, canvas: HTMLCanvasElement) => {
      // Store latest event
      pendingEventRef.current = { event, canvas };

      // If RAF already scheduled, skip
      if (rafPendingRef.current) return;

      rafPendingRef.current = true;
      requestAnimationFrame(() => {
        rafPendingRef.current = false;

        if (pendingEventRef.current) {
          continueStrokeInternal(pendingEventRef.current.event, pendingEventRef.current.canvas);
          pendingEventRef.current = null;
        }
      });
    },
    [continueStrokeInternal]
  );

  const endStroke = useCallback(() => {
    if (!currentStroke || !isDrawing) return;

    if (options.onStrokeComplete) {
      options.onStrokeComplete(currentStroke);
    }

    setCurrentStroke(null);
    setIsDrawing(false);

    // Reset state
    lastPressureRef.current = 0.5;
    lastPositionRef.current = null;
    lastTimestampRef.current = 0;
    rafPendingRef.current = false;
    pendingEventRef.current = null;
  }, [currentStroke, isDrawing, options]);

  return {
    currentStroke,
    isDrawing,
    startStroke,
    continueStroke,
    endStroke
  };
}
