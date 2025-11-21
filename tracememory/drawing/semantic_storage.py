from typing import List, Dict, Optional
from .semantic_models import SemanticElement

class SemanticStorage:
    """Store semantic elements in memory."""

    def __init__(self):
        self.elements: Dict[str, SemanticElement] = {}

    def store_element(self, element: SemanticElement):
        """Store semantic element."""
        self.elements[element.id] = element

    def get_element(self, element_id: str) -> Optional[SemanticElement]:
        """Get element by ID."""
        return self.elements.get(element_id)

    def get_all_elements(self) -> List[SemanticElement]:
        """Get all elements."""
        return list(self.elements.values())

    def delete_element(self, element_id: str):
        """Delete element."""
        if element_id in self.elements:
            del self.elements[element_id]

    def clear_all(self):
        """Clear all elements."""
        self.elements = {}

    def get_by_label(self, label: str) -> List[SemanticElement]:
        """Get elements by label."""
        return [e for e in self.elements.values() if e.label == label]
