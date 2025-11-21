"""
Session management and lifecycle control.

The SessionManager handles all session operations:
- Session creation and initialization
- Session retrieval and listing
- Session updates (notes, state changes)
- Session deletion
- Integration with storage layer
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime

from models.memory import MemoryBlock, DesignDNA
from storage.memory_storage import MemoryStorage
from api.errors import SessionNotFoundException, MemAgentException, ErrorCode
from config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session lifecycle and operations.

    Features:
    - Session CRUD operations
    - Integration with MemoryStorage
    - Session validation and state management
    - Automatic cleanup and maintenance
    """

    def __init__(self, storage: Optional[MemoryStorage] = None):
        """
        Initialize session manager.

        Args:
            storage: MemoryStorage instance (creates new if None)
        """
        self.storage = storage or MemoryStorage()
        logger.info("SessionManager initialized")

    def create_session(
        self,
        session_id: str,
        intent: str,
        created_by: str = "user"
    ) -> MemoryBlock:
        """
        Create a new session with initial memory block.

        Args:
            session_id: Unique session identifier
            intent: Design intent/goal for the session
            created_by: User or system creating the session

        Returns:
            Created MemoryBlock

        Raises:
            MemAgentException: If session already exists
        """
        # Check if session already exists
        if self.storage.session_exists(session_id):
            raise MemAgentException(
                error_code=ErrorCode.SESSION_ALREADY_EXISTS,
                message=f"Session already exists: {session_id}",
                status_code=409,
                hint="Use a different session_id or load the existing session"
            )

        # Create initial memory block
        now = datetime.utcnow()
        memory_block = MemoryBlock(
            session_id=session_id,
            created_at=now,
            last_updated=now,
            summary=f"Session initialized by {created_by}",
            design_intent=intent
        )

        # Save to storage
        self.storage.save_memory_block(memory_block)

        logger.info(
            f"Session created: {session_id} "
            f"(memory_block_id: {memory_block.memory_block_id})"
        )

        return memory_block

    def get_session(self, session_id: str) -> MemoryBlock:
        """
        Get session memory block.

        Args:
            session_id: Session identifier

        Returns:
            MemoryBlock for the session

        Raises:
            SessionNotFoundException: If session doesn't exist
        """
        memory_block = self.storage.load_memory_block(session_id)

        if memory_block is None:
            raise SessionNotFoundException(session_id)

        logger.debug(f"Session retrieved: {session_id}")
        return memory_block

    def update_session(
        self,
        session_id: str,
        summary: Optional[str] = None,
        active_modifiers: Optional[Dict[str, float]] = None,
        design_dna: Optional[DesignDNA] = None,
        provenance_chain: Optional[List[str]] = None
    ) -> MemoryBlock:
        """
        Update session with new data.

        Args:
            session_id: Session identifier
            summary: New summary text
            active_modifiers: Updated modifier values
            design_dna: Updated design DNA
            provenance_chain: Updated provenance chain

        Returns:
            Updated MemoryBlock

        Raises:
            SessionNotFoundException: If session doesn't exist
        """
        # Load existing block
        memory_block = self.get_session(session_id)

        # Update fields
        if summary is not None:
            memory_block.summary = summary

        if active_modifiers is not None:
            memory_block.active_modifiers.update(active_modifiers)

        if design_dna is not None:
            memory_block.design_dna = design_dna

        if provenance_chain is not None:
            memory_block.provenance_chain = provenance_chain

        # Update timestamp
        memory_block.last_updated = datetime.utcnow()

        # Save
        self.storage.save_memory_block(memory_block)

        logger.info(f"Session updated: {session_id}")
        return memory_block

    def add_note(self, session_id: str, note: str) -> MemoryBlock:
        """
        Add a user note to session.

        Args:
            session_id: Session identifier
            note: Note text

        Returns:
            Updated MemoryBlock

        Raises:
            SessionNotFoundException: If session doesn't exist
        """
        memory_block = self.get_session(session_id)

        # Add note to user preferences
        memory_block.user_preferences.append(note)
        memory_block.last_updated = datetime.utcnow()

        # Save
        self.storage.save_memory_block(memory_block)

        logger.info(f"Note added to session {session_id}: {note[:50]}...")
        return memory_block

    def add_key_decision(self, session_id: str, decision: str) -> MemoryBlock:
        """
        Add a key decision to session.

        Args:
            session_id: Session identifier
            decision: Decision description

        Returns:
            Updated MemoryBlock

        Raises:
            SessionNotFoundException: If session doesn't exist
        """
        memory_block = self.get_session(session_id)

        # Add decision
        memory_block.key_decisions.append(decision)
        memory_block.last_updated = datetime.utcnow()

        # Save
        self.storage.save_memory_block(memory_block)

        logger.info(f"Key decision added to session {session_id}")
        return memory_block

    def delete_session(self, session_id: str):
        """
        Delete a session and all associated data.

        Args:
            session_id: Session identifier

        Raises:
            SessionNotFoundException: If session doesn't exist
        """
        # Verify session exists
        if not self.storage.session_exists(session_id):
            raise SessionNotFoundException(session_id)

        # Delete from storage
        self.storage.delete_session(session_id)

        logger.info(f"Session deleted: {session_id}")

    def list_sessions(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List all sessions with metadata.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session metadata dicts
        """
        all_sessions = self.storage.list_sessions(limit=limit + offset)

        # Apply offset
        sessions = all_sessions[offset:offset + limit]

        logger.debug(f"Listed {len(sessions)} sessions")
        return sessions

    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics.

        Returns:
            Dict with storage metrics
        """
        return self.storage.get_storage_stats()

    def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists
        """
        return self.storage.session_exists(session_id)

    def repair_storage(self):
        """
        Repair storage index by scanning disk.

        Useful for maintenance after manual operations.
        """
        logger.info("Repairing storage index...")
        self.storage.repair_index()
        logger.info("Storage repair complete")
