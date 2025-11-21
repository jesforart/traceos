/**
 * useStrokeCapture - Enhanced stroke capture with smoothing and velocity
 *
 * IMPROVEMENT #11: 120Hz throttling (RAF-based)
 * IMPROVEMENT #14: Velocity calculation for GPU
 * IMPROVEMENT #3: Zero-pressure fix for first frame
 * IMPROVEMENT #5: iPad-specific smoothing
 * FIX #3: Float32Array ring buffer (zero-allocation rendering)
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

// FIX #3: Ring buffer configuration
const FIELDS_PER_POINT = 7; // x, y, pressure, tilt_x, tilt_y, timestamp, velocity
const MAX_POINTS = 10000;
const BUFFER_SIZE = MAX_POINTS * FIELDS_PER_POINT;

export function useStrokeCapture(options: UseStrokeCaptureOptions) {
  // FIX #3: Replace currentStroke with separate metadata and buffer
  const [strokeMetadata, setStrokeMetadata] = useState<Omit<Stroke, 'points'> | null>(null);
  const [pointCount, setPointCount] = useState(0); // Cheap state update for re-renders
  const [isDrawing, setIsDrawing] = useState(false);

  // FIX #3: Pre-allocated ring buffer (zero allocation during drawing)
  const pointsBufferRef = useRef<Float32Array>(new Float32Array(BUFFER_SIZE));
  const bufferHeadRef = useRef(0);

  // IMPROVEMENT #3: Track last pressure to avoid zero-pressure dips
  const lastPressureRef = useRef(0.5);

  // IMPROVEMENT #5: Position smoothing for iPad
  const lastPositionRef = useRef<{ x: number; y: number } | null>(null);

  // IMPROVEMENT #11: 120Hz throttling with RAF
  const rafPendingRef = useRef(false);
  const pendingEventRef = useRef<{ event: PointerEvent; canvas: HTMLCanvasElement } | null>(null);

  // IMPROVEMENT #14: Track time for velocity calculation
  const lastTimestampRef = useRef(0);

  // FIX #3: Write point to ring buffer (zero allocation)
  const writePointToBuffer = useCallback(
    (
      buffer: Float32Array,
      index: number,
      point: {
        x: number;
        y: number;
        pressure: number;
        tilt_x: number;
        tilt_y: number;
        timestamp: number;
        velocity: number;
      }
    ) => {
      if (index >= MAX_POINTS) {
        console.warn('[useStrokeCapture] Buffer overflow, max points reached');
        return;
      }

      const offset = index * FIELDS_PER_POINT;
      buffer[offset + 0] = point.x;
      buffer[offset + 1] = point.y;
      buffer[offset + 2] = point.pressure;
      buffer[offset + 3] = point.tilt_x;
      buffer[offset + 4] = point.tilt_y;
      buffer[offset + 5] = point.timestamp;
      buffer[offset + 6] = point.velocity;
    },
    []
  );

  // FIX #3: Get raw buffer for rendering (zero allocation)
  const getRawBuffer = useCallback((): {
    buffer: Float32Array;
    pointCount: number;
    fieldsPerPoint: number;
  } => {
    return {
      buffer: pointsBufferRef.current,
      pointCount: bufferHeadRef.current,
      fieldsPerPoint: FIELDS_PER_POINT
    };
  }, []);

  // FIX #3: Get points array for React UI (allocates only when needed)
  const getPointsArray = useCallback((): Point[] => {
    const points: Point[] = [];
    const buffer = pointsBufferRef.current;
    const count = bufferHeadRef.current;

    for (let i = 0; i < count; i++) {
      const offset = i * FIELDS_PER_POINT;
      points.push({
        x: buffer[offset + 0],
        y: buffer[offset + 1],
        pressure: buffer[offset + 2],
        tilt_x: buffer[offset + 3],
        tilt_y: buffer[offset + 4],
        timestamp: buffer[offset + 5],
        velocity: buffer[offset + 6]
      });
    }

    return points;
  }, []);

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

      // FIX #3: Reset ring buffer
      bufferHeadRef.current = 0;

      const point = {
        x: rawX,
        y: rawY,
        pressure: smoothPressure(event.pressure, event.pointerType),
        tilt_x: event.tiltX || 0,
        tilt_y: event.tiltY || 0,
        timestamp: event.timeStamp,
        velocity: 0 // First point has no velocity
      };

      // FIX #3: Write first point to ring buffer
      writePointToBuffer(pointsBufferRef.current, bufferHeadRef.current, point);
      bufferHeadRef.current++;

      // FIX #3: Store stroke metadata (without points array)
      const metadata: Omit<Stroke, 'points'> = {
        id: ulid(),
        tool: options.tool,
        color: options.color,
        width: options.width,
        layer_id: options.currentLayerId,
        created_at: Date.now()
      };

      setStrokeMetadata(metadata);
      setPointCount(1);
      setIsDrawing(true);
    },
    [options.tool, options.color, options.width, options.currentLayerId, writePointToBuffer]
  );

  const continueStrokeInternal = useCallback(
    (event: PointerEvent, canvas: HTMLCanvasElement) => {
      if (!strokeMetadata || !isDrawing) return;

      const rect = canvas.getBoundingClientRect();
      const rawX = event.clientX - rect.left;
      const rawY = event.clientY - rect.top;

      const smoothed = smoothPosition(rawX, rawY);
      const velocity = calculateVelocity(smoothed.x, smoothed.y, event.timeStamp);

      lastTimestampRef.current = event.timeStamp;

      const point = {
        x: smoothed.x,
        y: smoothed.y,
        pressure: smoothPressure(event.pressure, event.pointerType),
        tilt_x: event.tiltX || 0,
        tilt_y: event.tiltY || 0,
        timestamp: event.timeStamp,
        velocity // IMPROVEMENT #14: Store velocity for GPU
      };

      // FIX #3: Write to ring buffer (zero allocation)
      writePointToBuffer(pointsBufferRef.current, bufferHeadRef.current, point);
      bufferHeadRef.current++;

      // Trigger re-render with cheap state update
      setPointCount(bufferHeadRef.current);
    },
    [strokeMetadata, isDrawing, writePointToBuffer]
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
    if (!strokeMetadata || !isDrawing) return;

    // FIX #3: Convert ring buffer to points array only when saving
    if (options.onStrokeComplete) {
      const stroke: Stroke = {
        ...strokeMetadata,
        points: getPointsArray()
      };
      options.onStrokeComplete(stroke);
    }

    // Reset state
    setStrokeMetadata(null);
    setPointCount(0);
    setIsDrawing(false);
    bufferHeadRef.current = 0;

    lastPressureRef.current = 0.5;
    lastPositionRef.current = null;
    lastTimestampRef.current = 0;
    rafPendingRef.current = false;
    pendingEventRef.current = null;
  }, [strokeMetadata, isDrawing, options, getPointsArray]);

  // FIX #3: Compute currentStroke for UI compatibility (allocates only when accessed)
  const currentStroke: Stroke | null = strokeMetadata
    ? {
        ...strokeMetadata,
        points: getPointsArray()
      }
    : null;

  return {
    currentStroke, // For UI (allocates array)
    isDrawing,
    startStroke,
    continueStroke,
    endStroke,
    // FIX #3: Ring buffer access methods
    getRawBuffer, // For rendering (zero allocation)
    getPointsArray, // For UI only (allocates array)
    pointCount // Current number of points
  };
}
