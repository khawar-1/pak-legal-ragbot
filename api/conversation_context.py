from typing import Dict, Any, Optional
import uuid
from datetime import datetime

class ConversationContext:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.requirements = {}
        self.conversation_history = []
        self.current_intent = None
        self.requirement_extraction_mode = False
    
    def set_intent(self, intent: str):
        """Set the current conversation intent"""
        self.current_intent = intent
        self.requirement_extraction_mode = (intent == "project_requirements")
    
    def add_message(self, sender: str, message: str, response_type: str = None):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "sender": sender,
            "message": message,
            "response_type": response_type
        })
    
    def update_requirements(self, new_requirements: Dict[str, Any]):
        """Update requirements with new information"""
        self.requirements.update(new_requirements)
    
    def get_requirements(self) -> Dict[str, Any]:
        """Get current requirements"""
        return self.requirements.copy()
    
    def is_requirement_extraction_complete(self) -> bool:
        """Check if requirement extraction is complete"""
        # Check if we have all required fields
        required_fields = [
            "project_overview", "application_type", "expected_users", 
            "data_types", "performance_requirements", "security_requirements",
            "budget_constraints", "deployment_region"
        ]
        
        return all(
            self.requirements.get(field) and 
            (not isinstance(self.requirements.get(field), list) or len(self.requirements.get(field)) > 0)
            for field in required_fields
        )
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        return {
            "session_id": self.session_id,
            "intent": self.current_intent,
            "requirement_extraction_mode": self.requirement_extraction_mode,
            "requirements_complete": self.is_requirement_extraction_complete(),
            "message_count": len(self.conversation_history),
            "created_at": self.created_at.isoformat()
        }

class ConversationManager:
    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}
    
    def get_or_create_context(self, session_id: Optional[str] = None) -> ConversationContext:
        """Get existing conversation context or create new one"""
        if session_id and session_id in self.active_conversations:
            return self.active_conversations[session_id]
        
        # Create new context
        context = ConversationContext()
        self.active_conversations[context.session_id] = context
        return context
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context by session ID"""
        return self.active_conversations.get(session_id)
    
    def update_context(self, session_id: str, context: ConversationContext):
        """Update conversation context"""
        self.active_conversations[session_id] = context
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up old conversation contexts"""
        current_time = datetime.now()
        to_remove = []
        
        for session_id, context in self.active_conversations.items():
            age_hours = (current_time - context.created_at).total_seconds() / 3600
            if age_hours > max_age_hours:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.active_conversations[session_id]

# Global conversation manager instance
conversation_manager = ConversationManager()
