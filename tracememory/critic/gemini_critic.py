"""
Gemini Critic - Aesthetic evaluation using Gemini 2.0 Flash API

RED TEAM FIX #5: Structured JSON output mode for reliable parsing.

This module provides aesthetic critique using Google's Gemini API with
response_mime_type="application/json" for guaranteed JSON output.
"""

import json
import os
import base64
from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class CritiqueScore(BaseModel):
    """Individual critique dimension score"""
    score: float = Field(..., ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    rationale: str = Field(..., description="Brief explanation of score")


class AestheticCritique(BaseModel):
    """
    Structured aesthetic critique output.

    RED TEAM FIX #5: Validated schema for JSON output.
    """
    # Overall assessment
    overall_score: float = Field(..., ge=0.0, le=1.0)
    overall_feedback: str

    # Dimension scores
    composition: CritiqueScore
    color_harmony: CritiqueScore
    balance: CritiqueScore
    visual_interest: CritiqueScore
    technical_execution: CritiqueScore

    # Additional insights
    strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)

    # Metadata
    critic_version: str = "gemini-2.0-flash"
    evaluated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class GeminiCritic:
    """
    Aesthetic critic using Gemini 2.0 Flash API with structured JSON output.

    RED TEAM FIX #5: Uses response_mime_type="application/json" for reliable parsing.

    Features:
    - Structured JSON output (no hallucinated formats)
    - Mock mode for testing without API calls
    - Support for both raster images and SVG
    - Pydantic validation of responses
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        mock_mode: bool = False,
        model: str = "gemini-2.0-flash-exp"
    ):
        """
        Initialize GeminiCritic.

        Args:
            api_key: Google AI API key (or set GOOGLE_API_KEY env var)
            mock_mode: If True, return mock responses without API calls
            model: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.mock_mode = mock_mode
        self.model = model

        if not self.mock_mode and not self.api_key:
            raise ValueError(
                "API key required. Set GOOGLE_API_KEY env var or pass api_key parameter. "
                "Use mock_mode=True for testing without API."
            )

        # Initialize Gemini client (lazy import)
        if not self.mock_mode:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai package required. Install with: "
                    "pip install google-generativeai"
                )
        else:
            self.client = None

    def critique_image(
        self,
        image_data: bytes,
        mime_type: str = "image/png",
        context: Optional[Dict[str, Any]] = None
    ) -> AestheticCritique:
        """
        Critique a raster image using Gemini API.

        RED TEAM FIX #5: Structured JSON output guaranteed by response_mime_type.

        Args:
            image_data: Raw image bytes (PNG, JPEG, etc.)
            mime_type: Image MIME type
            context: Optional context dict {intent, style_keywords, target_audience}

        Returns:
            AestheticCritique with validated JSON structure
        """
        if self.mock_mode:
            return self._mock_critique(context)

        # Build prompt with context
        prompt = self._build_critique_prompt(context)

        # Encode image for API
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Call Gemini API with structured output
        try:
            model = self.client.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "response_mime_type": "application/json",  # RED TEAM FIX #5
                    "response_schema": self._get_json_schema()
                }
            )

            # Create image part
            image_part = {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": image_b64
                }
            }

            response = model.generate_content([prompt, image_part])
            response_json = json.loads(response.text)

            # Validate with Pydantic
            return AestheticCritique(**response_json)

        except Exception as e:
            raise RuntimeError(f"Gemini API critique failed: {str(e)}")

    def critique_svg(
        self,
        svg_data: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AestheticCritique:
        """
        Critique an SVG using Gemini API.

        RED TEAM FIX #5: Structured JSON output guaranteed by response_mime_type.

        Args:
            svg_data: SVG XML string
            context: Optional context dict {intent, style_keywords, target_audience}

        Returns:
            AestheticCritique with validated JSON structure
        """
        if self.mock_mode:
            return self._mock_critique(context)

        # Build prompt with SVG context
        prompt = self._build_critique_prompt(context, is_svg=True)
        prompt += f"\n\nSVG Content:\n```xml\n{svg_data}\n```"

        # Call Gemini API with structured output (text-only, no image)
        try:
            model = self.client.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "response_mime_type": "application/json",  # RED TEAM FIX #5
                    "response_schema": self._get_json_schema()
                }
            )

            response = model.generate_content(prompt)
            response_json = json.loads(response.text)

            # Validate with Pydantic
            return AestheticCritique(**response_json)

        except Exception as e:
            raise RuntimeError(f"Gemini API critique failed: {str(e)}")

    def _build_critique_prompt(
        self,
        context: Optional[Dict[str, Any]] = None,
        is_svg: bool = False
    ) -> str:
        """Build critique prompt with optional context"""
        media_type = "SVG vector graphic" if is_svg else "image"

        prompt = f"""You are an expert aesthetic critic evaluating a {media_type}.

Provide a detailed aesthetic critique covering:
1. **Composition**: Layout, structure, visual flow
2. **Color Harmony**: Color relationships, palette cohesion
3. **Balance**: Visual weight distribution, symmetry/asymmetry
4. **Visual Interest**: Engagement, uniqueness, focal points
5. **Technical Execution**: Craftsmanship, precision, polish

For each dimension, provide:
- A score from 0.0 (poor) to 1.0 (excellent)
- A brief rationale (1-2 sentences)

Also provide:
- Overall score (0.0 to 1.0)
- Overall feedback (2-3 sentences)
- List of strengths (2-4 items)
- List of areas for improvement (2-4 items)
- Style tags (3-5 descriptive keywords like "organic", "minimalist", "vibrant")
"""

        # Add context if provided
        if context:
            prompt += "\n\n**Context:**\n"
            if "intent" in context:
                intent = context["intent"]
                if "emotional_register" in intent:
                    prompt += f"- Emotional register: {intent['emotional_register']}\n"
                if "target_audience" in intent:
                    prompt += f"- Target audience: {intent['target_audience']}\n"
                if "style_keywords" in intent:
                    prompt += f"- Style keywords: {', '.join(intent['style_keywords'])}\n"

        prompt += "\n\nProvide your critique in the specified JSON format."

        return prompt

    def _get_json_schema(self) -> Dict:
        """
        Get JSON schema for structured output.

        RED TEAM FIX #5: Explicit schema ensures reliable JSON parsing.
        """
        return {
            "type": "object",
            "properties": {
                "overall_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "overall_feedback": {"type": "string"},
                "composition": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "rationale": {"type": "string"}
                    },
                    "required": ["score", "rationale"]
                },
                "color_harmony": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "rationale": {"type": "string"}
                    },
                    "required": ["score", "rationale"]
                },
                "balance": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "rationale": {"type": "string"}
                    },
                    "required": ["score", "rationale"]
                },
                "visual_interest": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "rationale": {"type": "string"}
                    },
                    "required": ["score", "rationale"]
                },
                "technical_execution": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "rationale": {"type": "string"}
                    },
                    "required": ["score", "rationale"]
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "areas_for_improvement": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "style_tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": [
                "overall_score",
                "overall_feedback",
                "composition",
                "color_harmony",
                "balance",
                "visual_interest",
                "technical_execution",
                "strengths",
                "areas_for_improvement",
                "style_tags"
            ]
        }

    def _mock_critique(self, context: Optional[Dict[str, Any]] = None) -> AestheticCritique:
        """
        Return mock critique for testing without API calls.

        Useful for CI/CD and development without consuming API quota.
        """
        return AestheticCritique(
            overall_score=0.75,
            overall_feedback="This is a mock critique generated without API calls. "
                           "The artwork shows promise with good composition and color choices.",
            composition=CritiqueScore(
                score=0.8,
                rationale="Layout is well-structured with clear visual hierarchy."
            ),
            color_harmony=CritiqueScore(
                score=0.7,
                rationale="Color palette is cohesive but could use more contrast."
            ),
            balance=CritiqueScore(
                score=0.75,
                rationale="Visual weight is distributed evenly across the composition."
            ),
            visual_interest=CritiqueScore(
                score=0.7,
                rationale="Engaging focal points with room for more dynamic elements."
            ),
            technical_execution=CritiqueScore(
                score=0.8,
                rationale="Clean execution with attention to detail."
            ),
            strengths=[
                "Strong compositional structure",
                "Cohesive color palette",
                "Good technical execution"
            ],
            areas_for_improvement=[
                "Add more visual contrast",
                "Enhance dynamic elements",
                "Experiment with asymmetry"
            ],
            style_tags=["organic", "balanced", "harmonious", "polished"]
        )
