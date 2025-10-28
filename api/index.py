"""
FastAPI Main Application with MongoDB Integration
"""
from fastapi import FastAPI, HTTPException
from .models import (
    ChatRequest, 
    EnhancedChatResponse, 
    IntentClassification, 
    RequirementFollowUpResponse, 
    CompleteRequirementsResponse
)
from .utils import generate_analysis_and_tips
from .retrieval import retrieval
from .requirement_extraction_system import CloudRequirementExtractor
from .database import connect_to_mongo, close_mongo_connection, get_database
from .session_manager import session_manager
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AWS Cloud Assistant - RAG & Requirement Extraction")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Global services
requirement_extractor: CloudRequirementExtractor = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global requirement_extractor
    
    logger.info("Initializing AWS Cloud Assistant...")
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        logger.info("MongoDB connected")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
        logger.warning("Continuing without MongoDB (stateless mode)")
    
    # Initialize requirement extractor
    requirement_extractor = CloudRequirementExtractor()
    
    logger.info("Enhanced chatbot system ready!")
    time.sleep(1)  # Give Ollama a moment to be ready

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_mongo_connection()
    logger.info("Shutdown complete")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        await db.command('ping')
        return {
            "status": "healthy", 
            "message": "AWS Cloud Assistant is running",
            "mongodb": "connected"
        }
    except Exception as e:
        return {
            "status": "healthy", 
            "message": "AWS Cloud Assistant is running",
            "mongodb": "disconnected",
            "warning": str(e)
        }

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session data including requirements and progress"""
    try:
        session = await session_manager.get_session(session_id)
        
        if not session:
            return {
                "found": False,
                "progress": {"completed": 0, "total": 9, "missingFields": []},
                "requirements": {}
            }
        
        # Calculate progress
        requirements = session.get("extracted_requirements", {})
        completed_count = len([v for v in requirements.values() if v and v != ""])
        missing_fields = [
            field for field in requirement_extractor.required_fields.keys()
            if not requirements.get(field) or requirements.get(field) == ""
        ]
        
        return {
            "found": True,
            "session_id": session_id,
            "mode": session.get("mode"),
            "is_complete": session.get("is_complete", False),
            "progress": {
                "completed": completed_count,
                "total": 9,
                "missingFields": missing_fields
            },
            "requirements": requirements,
            "chat_history": session.get("chat_history", [])
        }
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return {
            "found": False,
            "error": str(e),
            "progress": {"completed": 0, "total": 9, "missingFields": []}
        }

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete/Reset a session - clears all data"""
    try:
        collection = get_database()["sessions"]
        result = await collection.delete_one({"session_id": session_id})
        
        if result.deleted_count > 0:
            logger.info(f"Session deleted: {session_id}")
            return {"success": True, "message": "Session reset successfully"}
        else:
            return {"success": False, "message": "Session not found"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/chat")
async def chat(request: ChatRequest) -> EnhancedChatResponse:
    """
    Main chat endpoint with MongoDB session persistence
    """
    try:
        mode = request.mode or "aws_chat"
        
        # Create intent classification based on explicit mode
        intent_classification = IntentClassification(
            intent="aws_query" if mode == "aws_chat" else "project_requirements",
            confidence=1.0,
            reasoning=f"Explicit mode selection: {mode}"
        )
        
        # Get or create session from MongoDB
        session = await session_manager.get_or_create_session(
            session_id=request.session_id,
            user_id=request.user_id,
            mode=mode
        )
        session_id = session["session_id"]
        
        # Add user message to session
        await session_manager.add_message(
            session_id=session_id,
            sender="User",
            message=request.user_input,
            response_type=None
        )
        
        # Route based on mode
        if mode == "aws_chat":
            return await handle_aws_query(
                user_input=request.user_input,
                intent_classification=intent_classification,
                session_id=session_id
            )
        elif mode == "requirement_extraction":
            return await handle_project_requirements(
                user_input=request.user_input,
                intent_classification=intent_classification,
                session_id=session_id
            )
        else:
            # Fallback to AWS query
            return await handle_aws_query(
                user_input=request.user_input,
                intent_classification=intent_classification,
                session_id=session_id
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        # Fallback response
        fallback_intent = IntentClassification(
            intent="aws_query",
            confidence=0.5,
            reasoning=f"Error: {str(e)}"
        )
        
        return EnhancedChatResponse(
            intent_classification=fallback_intent,
            response_type="aws_query_response",
            question_analysis=f"Error processing request: {str(e)}",
            answer="I apologize, but I encountered an error. Please try again.",
            tips="Make sure to provide clear input."
        )

async def handle_aws_query(
    user_input: str,
    intent_classification: IntentClassification,
    session_id: str
) -> EnhancedChatResponse:
    """Handle AWS-related queries using RAG system"""
    try:
        # Use existing RAG system for AWS queries
        answer = retrieval(user_input)
        analysis, tips = generate_analysis_and_tips(user_input)
        
        # Format AI response
        ai_message = f"Analysis: {analysis.generations[0][0].text if hasattr(analysis, 'generations') else str(analysis)}\nAnswer: {answer}"
        
        # Save AI response to session
        await session_manager.add_message(
            session_id=session_id,
            sender="AI",
            message=ai_message,
            response_type="aws_query_response"
        )
        
        response = EnhancedChatResponse(
            intent_classification=intent_classification,
            response_type="aws_query_response",
            question_analysis=analysis.generations[0][0].text if hasattr(analysis, 'generations') else str(analysis),
            answer=answer,
            tips=tips.generations[0][0].text if hasattr(tips, 'generations') else str(tips),
            session_id=session_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in AWS query handler: {e}")
        return EnhancedChatResponse(
            intent_classification=intent_classification,
            response_type="aws_query_response",
            question_analysis=f"Error processing AWS query: {str(e)}",
            answer="I apologize, but I encountered an error while processing your AWS-related question. Please try rephrasing your question.",
            tips="Make sure to ask specific questions about AWS services, architecture patterns, or cloud concepts.",
            session_id=session_id
        )

async def handle_project_requirements(
    user_input: str,
    intent_classification: IntentClassification,
    session_id: str
) -> EnhancedChatResponse:
    """Handle project requirement extraction with MongoDB persistence"""
    try:
        # Get existing requirements and chat history from MongoDB
        existing_requirements = await session_manager.get_existing_requirements(session_id)
        conversation_history = await session_manager.get_chat_history(session_id, limit=5)
        
        # Extract requirements with context
        result = requirement_extractor.extract_requirements(
            user_input=user_input,
            existing_requirements=existing_requirements,
            conversation_history=conversation_history,
            rag_enabled=True
        )
        
        # Update requirements in MongoDB
        if result.get("current_requirements"):
            await session_manager.update_requirements(
                session_id=session_id,
                requirements=result["current_requirements"]
            )
        
        # Handle response types
        if result["type"] == "requirement_follow_up":
            follow_up_response = RequirementFollowUpResponse(**result)
            
            # Save AI response to session
            await session_manager.add_message(
                session_id=session_id,
                sender="AI",
                message=result.get("message", ""),
                response_type="requirement_follow_up"
            )
            
            return EnhancedChatResponse(
                intent_classification=intent_classification,
                response_type="requirement_follow_up",
                requirement_follow_up=follow_up_response,
                session_id=session_id
            )
            
        elif result["type"] == "complete_requirements":
            complete_response = CompleteRequirementsResponse(**result)
            
            # Mark session as complete
            await session_manager.mark_complete(session_id)
            
            # Save AI response to session
            await session_manager.add_message(
                session_id=session_id,
                sender="AI",
                message=result.get("message", ""),
                response_type="complete_requirements"
            )
            
            return EnhancedChatResponse(
                intent_classification=intent_classification,
                response_type="complete_requirements",
                complete_requirements=complete_response,
                session_id=session_id
            )
        else:
            # Fallback
            fallback_response = RequirementFollowUpResponse(
                current_requirements={},
                missing_fields=list(requirement_extractor.required_fields.keys()),
                follow_up_questions=[],
                progress="0/9 fields completed",
                message="I'll help you extract the cloud requirements for your project. Could you tell me more about what you're building?"
            )
            
            return EnhancedChatResponse(
                intent_classification=intent_classification,
                response_type="requirement_follow_up",
                requirement_follow_up=fallback_response,
                session_id=session_id
            )
            
    except Exception as e:
        logger.error(f"Error in requirement extraction handler: {e}")
        fallback_response = RequirementFollowUpResponse(
            current_requirements={},
            missing_fields=list(requirement_extractor.required_fields.keys()),
            follow_up_questions=[],
            progress="0/9 fields completed",
            message=f"I encountered an error while analyzing your project requirements: {str(e)}. Please provide more details about your project."
        )
        
        return EnhancedChatResponse(
            intent_classification=intent_classification,
            response_type="requirement_follow_up",
            requirement_follow_up=fallback_response,
            session_id=session_id
        )
