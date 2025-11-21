from typing import List, Dict, Optional
from .models import Stroke, ProcessedStroke

class StrokeStorage:
    """Store strokes in memory."""

    def __init__(self):
        self.strokes: Dict[str, ProcessedStroke] = {}
        self.session_strokes: List[str] = []

    def store_stroke(self, processed_stroke: ProcessedStroke):
        """Store processed stroke."""
        self.strokes[processed_stroke.stroke.id] = processed_stroke
        self.session_strokes.append(processed_stroke.stroke.id)

    def get_stroke(self, stroke_id: str) -> Optional[ProcessedStroke]:
        """Retrieve stroke by ID."""
        return self.strokes.get(stroke_id)

    def get_session_strokes(self) -> List[ProcessedStroke]:
        """Get all strokes from current session."""
        return [
            self.strokes[sid]
            for sid in self.session_strokes
            if sid in self.strokes
        ]

    def clear_session(self):
        """Clear current session."""
        self.session_strokes = []
