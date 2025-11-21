"""
Compression Engine - Compresses trace events using Claude API.

Takes a list of events from a design session and compresses them into
a compact memory summary with key decisions, modifiers, and preferences.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import json

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from config import settings

logger = logging.getLogger(__name__)


class CompressionResult:
    """Result of compression operation."""

    def __init__(
        self,
        summary: str,
        key_decisions: List[str],
        active_modifiers: Dict[str, float],
        user_preferences: List[str],
        design_intent: str,
        events_processed: int,
        tokens_in: int,
        tokens_out: int
    ):
        self.summary = summary
        self.key_decisions = key_decisions
        self.active_modifiers = active_modifiers
        self.user_preferences = user_preferences
        self.design_intent = design_intent
        self.events_processed = events_processed
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.compression_ratio = tokens_in / tokens_out if tokens_out > 0 else 1.0
        self.compressed_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "summary": self.summary,
            "key_decisions": self.key_decisions,
            "active_modifiers": self.active_modifiers,
            "user_preferences": self.user_preferences,
            "design_intent": self.design_intent,
            "events_processed": self.events_processed,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "compression_ratio": self.compression_ratio,
            "compressed_at": self.compressed_at.isoformat()
        }


class CompressionEngine:
    """
    Compresses trace events using Claude API.

    Features:
    - Event filtering by importance
    - Structured compression with Claude
    - Target output: 512 tokens
    - Extracts key decisions, modifiers, preferences

    Future:
    - HF model integration
    - Compression caching
    - Quality metrics
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize compression engine.

        Args:
            api_key: Anthropic API key (defaults to settings.ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

        if not self.api_key:
            logger.warning("No Anthropic API key configured - compression will fail")
            self.client = None
        elif Anthropic is None:
            logger.error("anthropic package not installed")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)
            logger.info("CompressionEngine initialized with Claude API")

    def compress_events(self, events: List[Dict]) -> CompressionResult:
        """
        Compress a list of trace events into a memory summary.

        Args:
            events: List of event dictionaries from Trace

        Returns:
            CompressionResult with compressed summary and metadata

        Raises:
            RuntimeError: If Claude API is not configured
            Exception: If compression fails
        """
        if not self.client:
            raise RuntimeError(
                "Compression engine not configured - missing Anthropic API key"
            )

        # Filter and format events
        filtered_events = self._filter_important_events(events)
        formatted_text = self._format_events(filtered_events)

        logger.info(
            f"Compressing {len(filtered_events)} events "
            f"(filtered from {len(events)})"
        )

        # Estimate input tokens (rough)
        tokens_in = len(formatted_text.split())

        # Compress using Claude
        compressed_data = self._compress_with_claude(formatted_text)

        # Parse response
        result = self._parse_compression_response(
            compressed_data,
            events_processed=len(filtered_events),
            tokens_in=tokens_in
        )

        logger.info(
            f"Compression complete: {result.events_processed} events → "
            f"{result.tokens_out} tokens (ratio: {result.compression_ratio:.2f}x)"
        )

        return result

    def _filter_important_events(self, events: List[Dict]) -> List[Dict]:
        """
        Keep only important events for compression.

        Priority tiers:
        - HIGH: user decisions, schema changes, provenance
        - MEDIUM: variation applies, notes
        - LOW: UI events, system logs (dropped)
        """
        high_priority = {
            "session.created",
            "session.updated",
            "provenance.stored",
            "schema.updated",
            "variation.accepted",
            "variation.rejected",
            "user_note.added",
        }

        medium_priority = {
            "variation.applied",
            "task.completed",
            "asset.created",
        }

        # Filter by priority
        high = [e for e in events if e.get("event_type") in high_priority]
        medium = [e for e in events if e.get("event_type") in medium_priority]

        # Limit total events
        max_events = settings.MAX_EVENTS_PER_COMPRESSION

        if len(high) + len(medium) > max_events:
            # Keep all high, sample medium
            medium_limit = max_events - len(high)
            medium = medium[-medium_limit:] if medium_limit > 0 else []

        filtered = high + medium

        # Sort by timestamp
        filtered.sort(key=lambda e: e.get("timestamp", ""))

        return filtered

    def _format_events(self, events: List[Dict]) -> str:
        """
        Format events for Claude compression.

        Output format:
        [TIME] EVENT_TYPE by ACTOR: details
        """
        lines = []

        for e in events:
            timestamp = e.get("timestamp", "")[:19]  # Truncate to seconds
            event_type = e.get("event_type", "unknown")
            actor = e.get("actor", "system")
            data = e.get("data", {})

            # Create readable line
            line = f"[{timestamp}] {event_type} by {actor}"

            # Add key data points
            if data:
                if "modifier" in data:
                    line += f" → {data['modifier']}={data.get('value', '?')}"
                elif "text" in data:
                    # Truncate long text
                    text = data['text'][:50] + "..." if len(data['text']) > 50 else data['text']
                    line += f" → \"{text}\""
                elif "schema_id" in data:
                    line += f" → schema {data['schema_id']}"
                elif "asset_type" in data:
                    line += f" → {data['asset_type']} asset"

            lines.append(line)

        return "\n".join(lines)

    def _compress_with_claude(self, formatted_events: str) -> str:
        """
        Use Claude API to compress events.

        Returns JSON with structured compression.
        """
        prompt = f"""You are compressing design session events into a memory summary for an AI system.

Events log:
```
{formatted_events}
```

Task:
Analyze these events and create a compressed memory summary.

Extract:
1. **Summary**: 2-3 sentence narrative of what happened in the session
2. **Key Decisions**: List of important decisions made (e.g., "chose organic style", "rejected harsh transitions")
3. **Active Modifiers**: Final modifier values that were applied (e.g., {{"stroke_weight": 0.7}})
4. **User Preferences**: Any preferences or constraints mentioned (e.g., "prefers muted palette", "WCAG AA required")
5. **Design Intent**: The overall goal or direction (1 sentence)

Format your response as JSON:
{{
  "summary": "narrative summary...",
  "key_decisions": ["decision 1", "decision 2"],
  "active_modifiers": {{"modifier_name": 0.7}},
  "user_preferences": ["preference 1", "preference 2"],
  "design_intent": "the overall goal..."
}}

Keep the summary concise - target ~400 tokens total.

Respond with ONLY the JSON object, no markdown formatting or extra text."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                temperature=0,  # Deterministic
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract text from response
            response_text = message.content[0].text

            logger.debug(f"Claude response: {response_text[:200]}...")

            return response_text

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def _parse_compression_response(
        self,
        response_text: str,
        events_processed: int,
        tokens_in: int
    ) -> CompressionResult:
        """
        Parse Claude's JSON response into CompressionResult.
        """
        try:
            # Clean up response (remove markdown if present)
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # Parse JSON
            data = json.loads(cleaned)

            # Extract fields
            summary = data.get("summary", "")
            key_decisions = data.get("key_decisions", [])
            active_modifiers = data.get("active_modifiers", {})
            user_preferences = data.get("user_preferences", [])
            design_intent = data.get("design_intent", "")

            # Estimate output tokens
            tokens_out = len(summary.split()) + len(str(data).split())

            return CompressionResult(
                summary=summary,
                key_decisions=key_decisions,
                active_modifiers=active_modifiers,
                user_preferences=user_preferences,
                design_intent=design_intent,
                events_processed=events_processed,
                tokens_in=tokens_in,
                tokens_out=tokens_out
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response_text}")

            # Fallback: create basic result
            return CompressionResult(
                summary=response_text[:500],  # Use first 500 chars
                key_decisions=[],
                active_modifiers={},
                user_preferences=[],
                design_intent="",
                events_processed=events_processed,
                tokens_in=tokens_in,
                tokens_out=len(response_text.split())
            )
