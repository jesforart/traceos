export interface Layer {
  id: string;
  name: string;
  visible: boolean;
  opacity: number;
  blend_mode: 'normal' | 'multiply' | 'screen' | 'overlay';
  z_index: number;
  stroke_ids: string[];
  created_at: number;
}
