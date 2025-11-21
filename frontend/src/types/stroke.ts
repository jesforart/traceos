import { Point } from './point';

export interface Stroke {
  id: string;
  points: Point[];
  tool: 'pen' | 'brush' | 'eraser' | 'marker';
  color: string;
  width: number;
  semantic_label?: string;
  layer_id: string;
  created_at: number;
}

export interface StrokeMetrics {
  avg_pressure: number;
  pressure_variance: number;
  avg_speed: number;
  length: number;
  smoothness: number;
  bounding_box: {
    min_x: number;
    min_y: number;
    max_x: number;
    max_y: number;
  };
}
