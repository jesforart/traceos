import { Stroke, Point } from '../types';
import { SelectionRegion } from '../types/semantic';

/**
 * Check if stroke is within selection region.
 */
export function isStrokeInRegion(stroke: Stroke, region: SelectionRegion): boolean {
  if (region.type === 'individual') {
    // Individual mode - exact click on stroke
    return false; // Handled differently
  }

  if (region.type === 'box') {
    return isStrokeInBox(stroke, region.points);
  }

  if (region.type === 'lasso') {
    return isStrokeInLasso(stroke, region.points);
  }

  return false;
}

/**
 * Box selection - axis-aligned bounding box.
 */
function isStrokeInBox(
  stroke: Stroke,
  points: Array<{ x: number; y: number }>
): boolean {
  if (points.length < 2) return false;

  const start = points[0];
  const end = points[points.length - 1];

  const minX = Math.min(start.x, end.x);
  const maxX = Math.max(start.x, end.x);
  const minY = Math.min(start.y, end.y);
  const maxY = Math.max(start.y, end.y);

  // Check if any stroke point is within box
  return stroke.points.some(p =>
    p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY
  );
}

/**
 * Lasso selection - point-in-polygon test.
 * Uses ray casting algorithm.
 */
function isStrokeInLasso(
  stroke: Stroke,
  lassoPoints: Array<{ x: number; y: number }>
): boolean {
  if (lassoPoints.length < 3) return false;

  // Check if any stroke point is inside lasso
  return stroke.points.some(p => isPointInPolygon(p, lassoPoints));
}

/**
 * Point-in-polygon test using ray casting.
 */
function isPointInPolygon(
  point: { x: number; y: number },
  polygon: Array<{ x: number; y: number }>
): boolean {
  let inside = false;

  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x;
    const yi = polygon[i].y;
    const xj = polygon[j].x;
    const yj = polygon[j].y;

    const intersect =
      yi > point.y !== yj > point.y &&
      point.x < ((xj - xi) * (point.y - yi)) / (yj - yi) + xi;

    if (intersect) inside = !inside;
  }

  return inside;
}

/**
 * Render selection region to canvas.
 */
export function renderSelectionRegion(
  ctx: CanvasRenderingContext2D,
  region: SelectionRegion
) {
  if (region.points.length === 0) return;

  ctx.save();
  ctx.strokeStyle = '#0066FF';
  ctx.lineWidth = 2;
  ctx.setLineDash([5, 5]);

  ctx.beginPath();

  if (region.type === 'box') {
    // Draw rectangle
    const start = region.points[0];
    const end = region.points[region.points.length - 1];
    const width = end.x - start.x;
    const height = end.y - start.y;
    ctx.rect(start.x, start.y, width, height);
  } else if (region.type === 'lasso') {
    // Draw freeform path
    ctx.moveTo(region.points[0].x, region.points[0].y);
    for (let i = 1; i < region.points.length; i++) {
      ctx.lineTo(region.points[i].x, region.points[i].y);
    }
    ctx.closePath();
  }

  ctx.stroke();
  ctx.restore();
}
