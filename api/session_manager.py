"""
MongoDB-based Session Manager for Conversation Persistence
"""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from .database import get_database
from .db_models import SessionDocument, ChatMessage
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages conversation sessions with MongoDB persistence"""
    
    def __init__(self):
        self.collection_name = "sessions"
    
    def _get_collection(self):
        """Get sessions collection. Returns None if not connected."""
        db = get_database()
        if db is None:
            return None
        return db[self.collection_name]
    
    async def create_session(
        self, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        mode: str = "aws_chat"
    ) -> str:
        """Create a new session in MongoDB"""
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_doc = SessionDocument(
            session_id=session_id,
            user_id=user_id,
            mode=mode,
            chat_history=[],
            extracted_requirements={},
            is_complete=False
        )
        
        try:
            collection = self._get_collection()
            if collection is None:
                logger.warning(f"Stateless mode: cannot create session {session_id} in MongoDB")
                return session_id
            await collection.insert_one(session_doc.dict())
            logger.info(f"Created session: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return session_id # Return ID anyway for stateless support
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from MongoDB"""
        try:
            collection = self._get_collection()
            if collection is None:
                return None
            session = await collection.find_one({"session_id": session_id})
            
            if session:
                # Convert ObjectId to string for JSON serialization
                session["_id"] = str(session["_id"])
                return session
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        mode: str = "aws_chat"
    ) -> Dict[str, Any]:
        """Get existing session or create new one"""
        
        if session_id:
            session = await self.get_session(session_id)
            if session:
                return session
        
        # Create new session
        new_session_id = await self.create_session(session_id, user_id, mode)
        session = await self.get_session(new_session_id)
        if session:
            return session
            
        # Return a minimal session object for stateless mode
        return {
            "session_id": new_session_id,
            "user_id": user_id,
            "mode": mode,
            "chat_history": []
        }
    
    async def add_message(
        self,
        session_id: str,
        sender: str,
        message: str,
        response_type: Optional[str] = None
    ):
        """Add a message to session chat history"""
        try:
            collection = self._get_collection()
            if collection is None:
                logger.debug("Stateless mode: message not saved")
                return
            
            chat_message = ChatMessage(
                sender=sender,
                message=message,
                response_type=response_type
            )
            
            await collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"chat_history": chat_message.dict()},
                    "$set": {"last_updated": datetime.now().isoformat()}
                }
            )
            logger.debug(f"Added message to session: {session_id}")
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            # Don't raise, allow flow to continue
    
    async def update_requirements(
        self,
        session_id: str,
        requirements: Dict[str, Any],
        question_retries: Optional[Dict[str, int]] = None
    ):
        """Update extracted requirements for a session"""
        try:
            collection = self._get_collection()
            
            update_data = {
                "extracted_requirements": requirements,
                "last_updated": datetime.now().isoformat()
            }
            
            if question_retries is not None:
                update_data["question_retries"] = question_retries
            
            await collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            logger.debug(f"Updated requirements for session: {session_id}")
        except Exception as e:
            logger.error(f"Error updating requirements: {e}")
            raise
    
    async def get_question_retries(self, session_id: str) -> Dict[str, int]:
        """Get question retry counts for each field"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return {}
            return session.get("question_retries", {})
        except Exception as e:
            logger.error(f"Error getting question retries: {e}")
            return {}
    
    async def increment_field_retry(self, session_id: str, field: str):
        """Increment retry count for a specific field"""
        try:
            collection = self._get_collection()
            retries = await self.get_question_retries(session_id)
            retries[field] = retries.get(field, 0) + 1
            
            await collection.update_one(
                {"session_id": session_id},
                {"$set": {"question_retries": retries}}
            )
        except Exception as e:
            logger.error(f"Error incrementing retry: {e}")
    
    async def mark_complete(self, session_id: str):
        """Mark session as complete"""
        try:
            collection = self._get_collection()
            
            await collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "is_complete": True,
                        "last_updated": datetime.now().isoformat()
                    }
                }
            )
            logger.info(f"Marked session as complete: {session_id}")
        except Exception as e:
            logger.error(f"Error marking complete: {e}")
            raise
    
    async def get_chat_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get last N messages from chat history"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return []
            
            chat_history = session.get("chat_history", [])
            # Return last N messages
            return chat_history[-limit:] if len(chat_history) > limit else chat_history
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def get_existing_requirements(self, session_id: str) -> Dict[str, Any]:
        """Get existing extracted requirements"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return {}
            
            return session.get("extracted_requirements", {})
        except Exception as e:
            logger.error(f"Error getting requirements: {e}")
            return {}

    # ── Clarification state helpers ────────────────────────────────────────────

    async def set_pending_clarification(
        self,
        session_id: str,
        original_query: str,
        options: list,
        current_round: int = 1,
    ):
        """Store clarification state when the bot asks for clarification."""
        try:
            collection = self._get_collection()
            if collection is None:
                logger.debug("Stateless mode: clarification state not persisted")
                return
            await collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "pending_clarification": True,
                        "clarification_context": {
                            "original_query": original_query,
                            "options_offered": options,
                            "round": current_round,
                        },
                        "last_updated": datetime.now().isoformat(),
                    }
                },
            )
            logger.info(f"Set pending clarification for session {session_id} (round {current_round})")
        except Exception as e:
            logger.error(f"Error setting pending clarification: {e}")

    async def clear_pending_clarification(self, session_id: str):
        """Reset clarification state once the user gives a clear answer."""
        try:
            collection = self._get_collection()
            if collection is None:
                return
            await collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "pending_clarification": False,
                        "clarification_context": {},
                        "last_updated": datetime.now().isoformat(),
                    }
                },
            )
            logger.info(f"Cleared pending clarification for session {session_id}")
        except Exception as e:
            logger.error(f"Error clearing pending clarification: {e}")

    async def get_clarification_state(self, session_id: str) -> Dict[str, Any]:
        """
        Return the clarification state for a session.
        Shape: { "pending": bool, "original_query": str,
                 "options_offered": List[str], "round": int }
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return {"pending": False, "original_query": "", "options_offered": [], "round": 0}
            pending = session.get("pending_clarification", False)
            ctx = session.get("clarification_context") or {}
            return {
                "pending": pending,
                "original_query": ctx.get("original_query", ""),
                "options_offered": ctx.get("options_offered", []),
                "round": ctx.get("round", 0),
            }
        except Exception as e:
            logger.error(f"Error getting clarification state: {e}")
            return {"pending": False, "original_query": "", "options_offered": [], "round": 0}



# Global session manager instance
session_manager = SessionManager()
