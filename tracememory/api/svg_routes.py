"""
FastAPI routes for SVG feature extraction and CRUD operations.

Week 1 Implementation - Adds missing feature extraction and element manipulation.
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from svg_analyzer import SVGAnalyzer, extract_all_features
from svg_crud import SVGCRUD, ElementNotFoundError

logger = logging.getLogger(__name__)

# Router for SVG operations
router = APIRouter(prefix="/v1/svg", tags=["svg"])


# ==========================================
# FEATURE EXTRACTION ENDPOINTS
# ==========================================

@router.post("/analyze")
async def analyze_svg(request: Request):
    """
    Analyze SVG and extract design features.

    Request body:
    {
        "svg": "<svg>...</svg>",
        "extract": ["colors", "typography", "spacing", "shapes"] // optional
    }

    Response:
    {
        "status": "ok",
        "features": {
            "colors": {...},
            "typography": {...},
            "spacing": {...},
            "shapes": {...}
        }
    }
    """
    try:
        data = await request.json()
        svg_string = data.get('svg')
        extract_types = data.get('extract', ['colors', 'typography', 'spacing', 'shapes'])

        if not svg_string:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing 'svg' in request"}
            )

        analyzer = SVGAnalyzer(svg_string)
        features = {}

        if 'colors' in extract_types:
            features['colors'] = analyzer.extract_colors()
            features['color_harmony'] = analyzer.analyze_color_harmony()

        if 'typography' in extract_types:
            features['typography'] = analyzer.extract_typography()
            features['type_scale'] = analyzer.calculate_type_scale()

        if 'spacing' in extract_types:
            features['spacing'] = analyzer.extract_spacing()

        if 'shapes' in extract_types:
            features['shapes'] = analyzer.analyze_shapes()

        logger.info(f"Analyzed SVG: extracted {len(features)} feature types")

        return {
            "status": "ok",
            "features": features
        }

    except ValueError as e:
        logger.error(f"Invalid SVG: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Invalid SVG: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/extract-all")
async def extract_all_svg_features(request: Request):
    """
    Extract all features from SVG (for Style DNA).

    Request body:
    {
        "svg": "<svg>...</svg>"
    }

    Response:
    {
        "status": "ok",
        "features": { complete feature set }
    }
    """
    try:
        data = await request.json()
        svg_string = data.get('svg')

        if not svg_string:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing 'svg' in request"}
            )

        features = extract_all_features(svg_string)

        logger.info("Extracted complete feature set for Style DNA")

        return {
            "status": "ok",
            "features": features
        }

    except ValueError as e:
        logger.error(f"Invalid SVG: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Invalid SVG: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Feature extraction error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


# ==========================================
# CRUD ENDPOINTS
# ==========================================

@router.post("/element/get")
async def get_svg_element(request: Request):
    """
    Get element by ID.

    Request body:
    {
        "svg": "<svg>...</svg>",
        "element_id": "rect1"
    }

    Response:
    {
        "status": "ok",
        "element": {
            "id": "rect1",
            "attributes": {"fill": "#FF0000", "width": "100", ...}
        }
    }
    """
    try:
        data = await request.json()
        svg_string = data.get('svg')
        element_id = data.get('element_id')

        if not svg_string or not element_id:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing 'svg' or 'element_id'"}
            )

        crud = SVGCRUD(svg_string)
        attributes = crud.get_element_attributes(element_id)

        logger.debug(f"Retrieved element: {element_id}")

        return {
            "status": "ok",
            "element": {
                "id": element_id,
                "attributes": attributes
            }
        }

    except ElementNotFoundError as e:
        logger.warning(f"Element not found: {e}")
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Get element error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/element/update")
async def update_svg_element(request: Request):
    """
    Update element attributes.

    Request body:
    {
        "svg": "<svg>...</svg>",
        "element_id": "rect1",
        "attributes": {"fill": "#00FF00", "rx": "8"}
    }

    Response:
    {
        "status": "ok",
        "svg": "<svg>... updated ...</svg>"
    }
    """
    try:
        data = await request.json()
        svg_string = data.get('svg')
        element_id = data.get('element_id')
        attributes = data.get('attributes', {})

        if not svg_string or not element_id:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"}
            )

        crud = SVGCRUD(svg_string)
        updated_svg = crud.update_element(element_id, attributes)

        logger.info(f"Updated element: {element_id} with {len(attributes)} attributes")

        return {
            "status": "ok",
            "svg": updated_svg
        }

    except ElementNotFoundError as e:
        logger.warning(f"Element not found: {e}")
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Update element error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/element/create")
async def create_svg_element(request: Request):
    """
    Create new element.

    Request body:
    {
        "svg": "<svg>...</svg>",
        "element_type": "circle",
        "attributes": {"id": "circle1", "cx": "100", "cy": "100", "r": "50", "fill": "red"}
    }

    Response:
    {
        "status": "ok",
        "svg": "<svg>... with new element ...</svg>"
    }
    """
    try:
        data = await request.json()
        svg_string = data.get('svg')
        element_type = data.get('element_type')
        attributes = data.get('attributes', {})
        parent_id = data.get('parent_id')

        if not svg_string or not element_type:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"}
            )

        crud = SVGCRUD(svg_string)
        updated_svg = crud.create_element(element_type, attributes, parent_id)

        logger.info(f"Created element: {element_type} with id {attributes.get('id', 'none')}")

        return {
            "status": "ok",
            "svg": updated_svg
        }

    except ElementNotFoundError as e:
        logger.warning(f"Parent element not found: {e}")
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Create element error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/element/delete")
async def delete_svg_element(request: Request):
    """
    Delete element by ID.

    Request body:
    {
        "svg": "<svg>...</svg>",
        "element_id": "rect1"
    }

    Response:
    {
        "status": "ok",
        "svg": "<svg>... without deleted element ...</svg>"
    }
    """
    try:
        data = await request.json()
        svg_string = data.get('svg')
        element_id = data.get('element_id')

        if not svg_string or not element_id:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"}
            )

        crud = SVGCRUD(svg_string)
        updated_svg = crud.delete_element(element_id)

        logger.info(f"Deleted element: {element_id}")

        return {
            "status": "ok",
            "svg": updated_svg
        }

    except ElementNotFoundError as e:
        logger.warning(f"Element not found: {e}")
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Delete element error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/element/clone")
async def clone_svg_element(request: Request):
    """
    Clone an existing element.

    Request body:
    {
        "svg": "<svg>...</svg>",
        "element_id": "circle1",
        "new_id": "circle2",
        "transform": "translate(100, 100)" // optional
    }

    Response:
    {
        "status": "ok",
        "svg": "<svg>... with cloned element ...</svg>"
    }
    """
    try:
        data = await request.json()
        svg_string = data.get('svg')
        element_id = data.get('element_id')
        new_id = data.get('new_id')
        transform = data.get('transform')

        if not svg_string or not element_id or not new_id:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"}
            )

        crud = SVGCRUD(svg_string)
        updated_svg = crud.clone_element(element_id, new_id, transform)

        logger.info(f"Cloned element: {element_id} -> {new_id}")

        return {
            "status": "ok",
            "svg": updated_svg
        }

    except ElementNotFoundError as e:
        logger.warning(f"Element not found: {e}")
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Clone element error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
