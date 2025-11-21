"""
TraceOS SVG CRUD Operations
Element-level manipulation for Penpot MCP integration.

Built on top of the lxml parsing foundation.
"""

from lxml import etree
from typing import Dict, List, Optional, Union
import copy


class SVGCRUDError(Exception):
    """Base exception for CRUD operations."""
    pass


class ElementNotFoundError(SVGCRUDError):
    """Raised when element cannot be found."""
    pass


class InvalidElementError(SVGCRUDError):
    """Raised when element data is invalid."""
    pass


class SVGCRUD:
    """CRUD operations for SVG elements."""

    def __init__(self, svg_string: str):
        """Initialize with SVG string."""
        self.svg_string = svg_string
        self.tree = self._parse_svg(svg_string)
        self.namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    def _parse_svg(self, svg_string: str) -> etree.Element:
        """Parse SVG string to lxml tree."""
        try:
            if isinstance(svg_string, str):
                svg_string = svg_string.encode('utf-8')
            return etree.fromstring(svg_string)
        except Exception as e:
            raise InvalidElementError(f"Invalid SVG: {e}")

    def to_string(self) -> str:
        """Convert tree back to SVG string."""
        return etree.tostring(self.tree, encoding='unicode')

    # ==========================================
    # READ OPERATIONS
    # ==========================================

    def get_element_by_id(self, element_id: str) -> Optional[etree.Element]:
        """
        Get element by ID.

        Args:
            element_id: Element ID to find

        Returns:
            Element if found, None otherwise
        """
        elements = self.tree.xpath(f'//*[@id="{element_id}"]')
        return elements[0] if elements else None

    def query_elements(self, selector: str) -> List[etree.Element]:
        """
        Query elements using CSS selector or XPath.

        Args:
            selector: CSS selector (e.g., 'rect.highlighted') or XPath

        Returns:
            List of matching elements
        """
        # Try CSS selector first
        try:
            from lxml.cssselect import CSSSelector
            sel = CSSSelector(selector)
            return sel(self.tree)
        except:
            pass

        # Try XPath
        try:
            return self.tree.xpath(selector)
        except:
            return []

    def get_element_attributes(self, element_id: str) -> Dict[str, str]:
        """
        Get all attributes of an element.

        Args:
            element_id: Element ID

        Returns:
            Dictionary of attribute name -> value

        Raises:
            ElementNotFoundError: If element not found
        """
        element = self.get_element_by_id(element_id)

        if element is None:
            raise ElementNotFoundError(f"Element '{element_id}' not found")

        return dict(element.attrib)

    # ==========================================
    # UPDATE OPERATIONS
    # ==========================================

    def update_element(self, element_id: str, attributes: Dict[str, str]) -> str:
        """
        Update element attributes (Penpot MCP compatible).

        Args:
            element_id: Element ID to update
            attributes: Dictionary of attributes to set
                       e.g., {'fill': '#FF0000', 'rx': '8'}

        Returns:
            Updated SVG string

        Raises:
            ElementNotFoundError: If element not found

        Example:
            >>> crud.update_element('rect1', {'fill': 'blue', 'rx': '5'})
        """
        element = self.get_element_by_id(element_id)

        if element is None:
            raise ElementNotFoundError(f"Element '{element_id}' not found")

        # Update attributes
        for key, value in attributes.items():
            element.set(key, str(value))

        return self.to_string()

    def update_element_style(self, element_id: str, style_props: Dict[str, str]) -> str:
        """
        Update element style properties.

        Args:
            element_id: Element ID
            style_props: Style properties dict
                        e.g., {'fill': '#FF0000', 'stroke-width': '2'}

        Returns:
            Updated SVG string
        """
        element = self.get_element_by_id(element_id)

        if element is None:
            raise ElementNotFoundError(f"Element '{element_id}' not found")

        # Get existing style
        existing_style = element.get('style', '')
        style_dict = self._parse_style(existing_style)

        # Update with new props
        style_dict.update(style_props)

        # Convert back to style string
        new_style = '; '.join([f'{k}: {v}' for k, v in style_dict.items()])
        element.set('style', new_style)

        return self.to_string()

    def set_transform(self, element_id: str, transform: str) -> str:
        """
        Set transform attribute on element.

        Args:
            element_id: Element ID
            transform: Transform string (e.g., 'translate(10, 20) rotate(45)')

        Returns:
            Updated SVG string
        """
        return self.update_element(element_id, {'transform': transform})

    # ==========================================
    # CREATE OPERATIONS
    # ==========================================

    def create_element(
        self,
        element_type: str,
        attributes: Dict[str, str],
        parent_id: Optional[str] = None
    ) -> str:
        """
        Create new element (Penpot MCP compatible).

        Args:
            element_type: Element type ('rect', 'circle', 'text', etc.)
            attributes: Element attributes including 'id'
            parent_id: Optional parent element ID (defaults to root <svg>)

        Returns:
            Updated SVG string with new element

        Example:
            >>> crud.create_element('circle', {
            ...     'id': 'circle1',
            ...     'cx': '100',
            ...     'cy': '100',
            ...     'r': '50',
            ...     'fill': 'red'
            ... })
        """
        # Get parent element
        if parent_id:
            parent = self.get_element_by_id(parent_id)
            if parent is None:
                raise ElementNotFoundError(f"Parent '{parent_id}' not found")
        else:
            parent = self.tree

        # Create new element with namespace
        ns = self.namespaces['svg']
        new_element = etree.Element(f'{{{ns}}}{element_type}')

        # Set attributes
        for key, value in attributes.items():
            new_element.set(key, str(value))

        # Append to parent
        parent.append(new_element)

        return self.to_string()

    def clone_element(
        self,
        element_id: str,
        new_id: str,
        transform: Optional[str] = None
    ) -> str:
        """
        Clone an existing element.

        Args:
            element_id: ID of element to clone
            new_id: ID for the cloned element
            transform: Optional transform for cloned element

        Returns:
            Updated SVG string
        """
        element = self.get_element_by_id(element_id)

        if element is None:
            raise ElementNotFoundError(f"Element '{element_id}' not found")

        # Deep copy element
        cloned = copy.deepcopy(element)
        cloned.set('id', new_id)

        if transform:
            cloned.set('transform', transform)

        # Insert after original
        parent = element.getparent()
        index = list(parent).index(element)
        parent.insert(index + 1, cloned)

        return self.to_string()

    # ==========================================
    # DELETE OPERATIONS
    # ==========================================

    def delete_element(self, element_id: str) -> str:
        """
        Delete element by ID (Penpot MCP compatible).

        Args:
            element_id: Element ID to delete

        Returns:
            Updated SVG string

        Raises:
            ElementNotFoundError: If element not found
        """
        element = self.get_element_by_id(element_id)

        if element is None:
            raise ElementNotFoundError(f"Element '{element_id}' not found")

        # Remove from parent
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

        return self.to_string()

    def delete_elements_by_query(self, selector: str) -> str:
        """
        Delete all elements matching selector.

        Args:
            selector: CSS selector or XPath

        Returns:
            Updated SVG string
        """
        elements = self.query_elements(selector)

        for element in elements:
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

        return self.to_string()

    # ==========================================
    # UTILITY FUNCTIONS
    # ==========================================

    def _parse_style(self, style_string: str) -> Dict[str, str]:
        """Parse CSS style string to dictionary."""
        if not style_string:
            return {}

        style_dict = {}
        for item in style_string.split(';'):
            if ':' in item:
                key, value = item.split(':', 1)
                style_dict[key.strip()] = value.strip()

        return style_dict

    def element_exists(self, element_id: str) -> bool:
        """Check if element exists."""
        return self.get_element_by_id(element_id) is not None

    def count_elements(self) -> int:
        """Count total elements in SVG."""
        return len(self.tree.xpath('//*'))


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def get_element_by_id(svg_string: str, element_id: str) -> Optional[Dict]:
    """Get element by ID. Returns None if not found."""
    crud = SVGCRUD(svg_string)
    try:
        attrs = crud.get_element_attributes(element_id)
        return attrs
    except ElementNotFoundError:
        return None


def update_element(svg_string: str, element_id: str, attributes: Dict[str, str]) -> str:
    """Update element attributes."""
    crud = SVGCRUD(svg_string)
    return crud.update_element(element_id, attributes)


def create_element(svg_string: str, element_type: str, attributes: Dict[str, str]) -> str:
    """Create new element."""
    crud = SVGCRUD(svg_string)
    return crud.create_element(element_type, attributes)


def delete_element(svg_string: str, element_id: str) -> str:
    """Delete element by ID."""
    crud = SVGCRUD(svg_string)
    return crud.delete_element(element_id)
