import { Stroke, Point } from '../types';

export function renderStroke(
  ctx: CanvasRenderingContext2D,
  stroke: Stroke,
  options?: {
    preview?: boolean;
    smoothing?: number;
  }
) {
  if (stroke.points.length === 0) return;

  const preview = options?.preview ?? false;
  const smoothing = options?.smoothing ?? 0.5;

  ctx.strokeStyle = preview ? `${stroke.color}80` : stroke.color;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  ctx.beginPath();

  if (stroke.points.length === 1) {
    const point = stroke.points[0];
    const radius = calculatePressureWidth(point.pressure, stroke.width);
    ctx.fillStyle = ctx.strokeStyle;
    ctx.arc(point.x, point.y, radius / 2, 0, Math.PI * 2);
    ctx.fill();
    return;
  }

  for (let i = 0; i < stroke.points.length; i++) {
    const point = stroke.points[i];
    const width = calculatePressureWidth(point.pressure, stroke.width);

    ctx.lineWidth = width;

    if (i === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      const prevPoint = stroke.points[i - 1];
      const midPoint = {
        x: (prevPoint.x + point.x) / 2,
        y: (prevPoint.y + point.y) / 2
      };

      if (smoothing > 0) {
        ctx.quadraticCurveTo(prevPoint.x, prevPoint.y, midPoint.x, midPoint.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    }
  }

  ctx.stroke();
}

function calculatePressureWidth(pressure: number, baseWidth: number): number {
  const normalizedPressure = Math.max(0, Math.min(1, pressure));
  const eased = normalizedPressure * normalizedPressure * (3 - 2 * normalizedPressure);

  const minMultiplier = 0.3;
  const maxMultiplier = 2.0;
  const multiplier = minMultiplier + (maxMultiplier - minMultiplier) * eased;

  return baseWidth * multiplier;
}

export function clearCanvas(ctx: CanvasRenderingContext2D) {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}

export function renderAllStrokes(
  ctx: CanvasRenderingContext2D,
  strokes: Stroke[]
) {
  clearCanvas(ctx);

  for (const stroke of strokes) {
    renderStroke(ctx, stroke);
  }
}
