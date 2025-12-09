"""
Intent Handler - Creates design intents with provenance tracking.

@provenance traceos_protocol_v1
@organ kernel
"""

import logging
from datetime import datetime
from typing import List, Optional

from .schemas import Intent, IntentMetadata
from .persistence import ProtocolStorage

logger = logging.getLogger(__name__)


class IntentHandler:
    """
    Manages intent creation and storage with full persistence.

    Intents are the atomic units of design work in TraceOS.
    Every feature, fix, or experiment starts with an intent.
    """

    def __init__(self, storage: ProtocolStorage):
        """
        Initialize intent handler.

        Args:
            storage: Protocol storage instance
        """
        self.storage = storage

    def create_intent(
        self,
        title: str,
        goals: List[str],
        tags: Optional[List[str]] = None,
        spark: str = "Brain",
        requested_by: str = "Jessie"
    ) -> Intent:
        """
        Create a new intent with automatic provenance tracking.

        Args:
            title: Human-readable intent title
            goals: List of specific objectives
            tags: Optional searchable tags
            spark: Which organ initiated (default: Brain)
            requested_by: Human initiator (default: Jessie)

        Returns:
            Intent object with generated intent_id
        """
        # Generate intent ID with timestamp
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        intent_id = f"intent_{timestamp_str}"

        # Create intent
        intent = Intent(
            intent_id=intent_id,
            title=title,
            tags=tags or [],
            goals=goals,
            metadata=IntentMetadata(
                spark=spark,
                requested_by=requested_by,
                timestamp=datetime.utcnow()
            )
        )

        # Persist to disk
        self.storage.save_intent(intent)

        logger.info(f"Created intent: {intent_id} - {title}")
        logger.debug(f"Intent goals: {goals}")

        return intent

    def get_intent(self, intent_id: str) -> Optional[Intent]:
        """
        Retrieve intent by ID.

        Args:
            intent_id: Intent identifier

        Returns:
            Intent object or None if not found
        """
        return self.storage.load_intent(intent_id)

    def list_intents(self, tags: Optional[List[str]] = None) -> List[Intent]:
        """
        List all intents, optionally filtered by tags.

        Args:
            tags: Optional tag filter

        Returns:
            List of matching intents
        """
        return self.storage.list_intents(tags=tags)
