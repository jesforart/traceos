"""
Modifier Engine - Core SVG transformation engine.

Handles SVG parsing, modifier application, and result generation.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from lxml import etree
import hashlib

from modifiers.base import ModifierRegistry

logger = logging.getLogger(__name__)


class ModifierEngine:
    """
    Core engine for applying modifiers to SVG assets.

    Uses lxml for SVG parsing and manipulation.
    Handles error recovery and metadata generation.
    """

    def __init__(self):
        """Initialize modifier engine."""
        self.registry = ModifierRegistry()
        logger.info(f"ModifierEngine initialized with {self.registry.count()} modifiers")

    def apply_modifier(
        self,
        svg_data: str,
        modifier_name: str,
        value: float
    ) -> Dict:
        """
        Apply single modifier to SVG data.

        Args:
            svg_data: SVG content as string
            modifier_name: Name of modifier to apply (e.g., "stroke_weight")
            value: Normalized value (0.0 to 1.0)

        Returns:
            Dictionary with:
                - success: bool
                - svg_data: modified SVG string (if successful)
                - error: error message (if failed)
                - metadata: dict with modifier info, timestamps, etc.

        Example:
            result = engine.apply_modifier(svg_data, "stroke_weight", 0.7)
            if result["success"]:
                new_svg = result["svg_data"]
        """
        start_time = datetime.utcnow()

        try:
            # Validate modifier exists
            modifier = self.registry.get(modifier_name)
            if not modifier:
                available = list(self.registry.list_all().keys())
                return {
                    "success": False,
                    "error": f"Modifier '{modifier_name}' not found. Available: {available}",
                    "metadata": {
                        "modifier": modifier_name,
                        "value": value,
                        "timestamp": start_time.isoformat()
                    }
                }

            # Validate value
            try:
                modifier.validate_value(value)
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "metadata": {
                        "modifier": modifier_name,
                        "value": value,
                        "timestamp": start_time.isoformat()
                    }
                }

            # Parse SVG
            svg_element = self._parse_svg(svg_data)
            if svg_element is None:
                return {
                    "success": False,
                    "error": "Failed to parse SVG data",
                    "metadata": {
                        "modifier": modifier_name,
                        "value": value,
                        "timestamp": start_time.isoformat()
                    }
                }

            # Apply modifier
            logger.info(f"Applying modifier '{modifier_name}' with value {value}")
            modified_element = modifier.apply(svg_element, value)

            # Serialize back to string
            modified_svg = self._serialize_svg(modified_element)

            # Compute metadata
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            metadata = {
                "modifier": modifier_name,
                "value": value,
                "timestamp": start_time.isoformat(),
                "duration_ms": round(duration_ms, 2),
                "original_size": len(svg_data),
                "modified_size": len(modified_svg),
                "checksum": self._compute_checksum(modified_svg)
            }

            logger.info(f"Modifier applied successfully in {duration_ms:.2f}ms")

            return {
                "success": True,
                "svg_data": modified_svg,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Error applying modifier '{modifier_name}': {e}", exc_info=True)
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            return {
                "success": False,
                "error": f"Modifier application failed: {str(e)}",
                "metadata": {
                    "modifier": modifier_name,
                    "value": value,
                    "timestamp": start_time.isoformat(),
                    "duration_ms": round(duration_ms, 2)
                }
            }

    def apply_multiple(
        self,
        svg_data: str,
        modifiers: Dict[str, float]
    ) -> Dict:
        """
        Apply multiple modifiers in sequence.

        Args:
            svg_data: SVG content as string
            modifiers: Dictionary of {modifier_name: value}

        Returns:
            Dictionary with success status, final SVG, and metadata

        Example:
            result = engine.apply_multiple(svg_data, {
                "stroke_weight": 0.5,
                "hue_shift": 0.3,
                "fill_opacity": 0.8
            })
        """
        start_time = datetime.utcnow()
        current_svg = svg_data
        applied = []
        errors = []

        for modifier_name, value in modifiers.items():
            result = self.apply_modifier(current_svg, modifier_name, value)

            if result["success"]:
                current_svg = result["svg_data"]
                applied.append({
                    "modifier": modifier_name,
                    "value": value,
                    "duration_ms": result["metadata"]["duration_ms"]
                })
            else:
                errors.append({
                    "modifier": modifier_name,
                    "value": value,
                    "error": result["error"]
                })
                logger.warning(f"Failed to apply {modifier_name}: {result['error']}")

        end_time = datetime.utcnow()
        total_duration_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "success": len(errors) == 0,
            "svg_data": current_svg if len(applied) > 0 else svg_data,
            "metadata": {
                "timestamp": start_time.isoformat(),
                "total_duration_ms": round(total_duration_ms, 2),
                "modifiers_applied": applied,
                "errors": errors,
                "original_size": len(svg_data),
                "final_size": len(current_svg)
            }
        }

    def _parse_svg(self, svg_data: str) -> Optional[etree._Element]:
        """
        Parse SVG string to lxml element.

        Args:
            svg_data: SVG content as string

        Returns:
            Parsed SVG element or None if parsing fails
        """
        try:
            # Clean up SVG data
            svg_bytes = svg_data.encode('utf-8')

            # Parse with lxml
            parser = etree.XMLParser(remove_blank_text=True, recover=True)
            svg_element = etree.fromstring(svg_bytes, parser=parser)

            return svg_element

        except Exception as e:
            logger.error(f"Failed to parse SVG: {e}")
            return None

    def _serialize_svg(self, svg_element: etree._Element) -> str:
        """
        Serialize lxml element back to SVG string.

        Args:
            svg_element: SVG element from lxml

        Returns:
            SVG content as string
        """
        try:
            svg_bytes = etree.tostring(
                svg_element,
                encoding='utf-8',
                xml_declaration=False,
                pretty_print=True
            )
            return svg_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"Failed to serialize SVG: {e}")
            raise

    def _compute_checksum(self, data: str) -> str:
        """
        Compute SHA256 checksum of data.

        Args:
            data: String data to hash

        Returns:
            Hex digest of SHA256 hash
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def list_modifiers(self) -> Dict[str, str]:
        """
        Get list of available modifiers with descriptions.

        Returns:
            Dictionary of {modifier_name: description}
        """
        modifiers = self.registry.list_all()
        return {
            name: mod.description
            for name, mod in modifiers.items()
        }

    def get_modifier_info(self, modifier_name: str) -> Optional[Dict]:
        """
        Get detailed info about a modifier.

        Args:
            modifier_name: Name of modifier

        Returns:
            Dictionary with modifier details or None if not found
        """
        modifier = self.registry.get(modifier_name)
        if not modifier:
            return None

        return {
            "name": modifier.name,
            "description": modifier.description,
            "class": modifier.__class__.__name__
        }
