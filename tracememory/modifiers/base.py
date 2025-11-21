"""
Base classes for modifier system.

Defines BaseModifier abstract class and ModifierRegistry for modifier registration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
from lxml import etree
import logging

logger = logging.getLogger(__name__)


class BaseModifier(ABC):
    """
    Abstract base class for SVG modifiers.

    All modifiers must:
    - Accept normalized values (0.0 to 1.0)
    - Return modified SVG element tree
    - Provide metadata about changes
    """

    def __init__(self, name: str, description: str):
        """
        Initialize modifier.

        Args:
            name: Modifier identifier (e.g., "stroke_weight")
            description: Human-readable description
        """
        self.name = name
        self.description = description

    @abstractmethod
    def apply(self, svg_element: etree._Element, value: float) -> etree._Element:
        """
        Apply modifier to SVG element.

        Args:
            svg_element: Root SVG element from lxml
            value: Normalized value (0.0 to 1.0)

        Returns:
            Modified SVG element

        Raises:
            ValueError: If value is out of range
        """
        pass

    def validate_value(self, value: float) -> None:
        """
        Validate modifier value is in range [0.0, 1.0].

        Args:
            value: Value to validate

        Raises:
            ValueError: If value is out of range
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"Modifier value must be numeric, got {type(value)}")

        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Modifier value must be in range [0.0, 1.0], got {value}")

    def denormalize(self, value: float, min_val: float, max_val: float) -> float:
        """
        Convert normalized value (0.0-1.0) to actual range.

        Args:
            value: Normalized value (0.0 to 1.0)
            min_val: Minimum value in target range
            max_val: Maximum value in target range

        Returns:
            Denormalized value in [min_val, max_val]

        Example:
            denormalize(0.5, 0, 100) -> 50.0
            denormalize(0.0, -10, 10) -> -10.0
        """
        return min_val + (value * (max_val - min_val))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class ModifierRegistry:
    """
    Registry for available modifiers.

    Allows registration and lookup of modifiers by name.
    Singleton pattern to ensure single source of truth.
    """

    _instance: Optional['ModifierRegistry'] = None
    _modifiers: Dict[str, BaseModifier] = {}

    def __new__(cls):
        """Singleton pattern - only one registry instance."""
        if cls._instance is None:
            cls._instance = super(ModifierRegistry, cls).__new__(cls)
            cls._modifiers = {}
        return cls._instance

    def register(self, modifier: BaseModifier) -> None:
        """
        Register a modifier.

        Args:
            modifier: Modifier instance to register

        Raises:
            ValueError: If modifier name already registered
        """
        if modifier.name in self._modifiers:
            logger.warning(f"Modifier '{modifier.name}' already registered, overwriting")

        self._modifiers[modifier.name] = modifier
        logger.info(f"Registered modifier: {modifier.name}")

    def get(self, name: str) -> Optional[BaseModifier]:
        """
        Get modifier by name.

        Args:
            name: Modifier name (e.g., "stroke_weight")

        Returns:
            Modifier instance or None if not found
        """
        return self._modifiers.get(name)

    def list_all(self) -> Dict[str, BaseModifier]:
        """
        Get all registered modifiers.

        Returns:
            Dictionary of {name: modifier_instance}
        """
        return self._modifiers.copy()

    def exists(self, name: str) -> bool:
        """
        Check if modifier exists.

        Args:
            name: Modifier name

        Returns:
            True if modifier is registered
        """
        return name in self._modifiers

    def count(self) -> int:
        """Get number of registered modifiers."""
        return len(self._modifiers)

    def clear(self) -> None:
        """Clear all registered modifiers (mainly for testing)."""
        self._modifiers.clear()
        logger.info("Cleared all modifiers from registry")

    def __repr__(self) -> str:
        return f"<ModifierRegistry(count={self.count()})>"


def register_modifier(name: str, description: str):
    """
    Decorator to auto-register modifiers.

    Usage:
        @register_modifier("stroke_weight", "Adjust stroke thickness")
        class StrokeWeightModifier(BaseModifier):
            ...
    """
    def decorator(cls: Type[BaseModifier]):
        # Create instance and register
        instance = cls(name=name, description=description)
        registry = ModifierRegistry()
        registry.register(instance)
        return cls
    return decorator
