/**
 * Point captured from tablet/stylus input.
 */
export interface Point {
  x: number;
  y: number;
  pressure: number;
  tilt_x: number;
  tilt_y: number;
  timestamp: number;
  velocity?: number; // IMPROVEMENT #14: pixels per millisecond (for GPU)
}

export function pointFromEvent(event: PointerEvent, canvas: HTMLCanvasElement): Point {
  const rect = canvas.getBoundingClientRect();

  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
    pressure: event.pressure,
    tilt_x: event.tiltX,
    tilt_y: event.tiltY,
    timestamp: Date.now()
  };
}
