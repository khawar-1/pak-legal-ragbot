"""
FastAPI Main Application - Legal Case Assistant with MongoDB Integration
"""
from fastapi import FastAPI, HTTPException
from .models import ChatRequest, ChatResponse, IntentClassification
from .retrieval import retrieval
from .database import connect_to_mongo, close_mongo_connection, get_database
from .session_manager import session_manager
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal Case Assistant - Pakistan Law RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Initializing Legal Case Assistant...")
    
    try:
        await connect_to_mongo()
        logger.info("MongoDB connected")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
        logger.warning("Continuing without MongoDB (stateless mode)")
    
    logger.info("Legal Case Assistant ready!")


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
            "message": "Legal Case Assistant is running",
            "mongodb": "connected"
        }
    except Exception as e:
        return {
            "status": "healthy", 
            "message": "Legal Case Assistant is running",
            "mongodb": "disconnected",
            "warning": str(e)
        }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session data including chat history"""
    try:
        session = await session_manager.get_session(session_id)
        
        if not session:
            return {
                "found": False,
                "chat_history": []
            }
        
        return {
            "found": True,
            "session_id": session_id,
            "chat_history": session.get("chat_history", [])
        }
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return {
            "found": False,
            "error": str(e),
            "chat_history": []
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
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for legal queries with MongoDB session persistence
    """
    session_id = request.session_id or "stateless-session"  # Always initialize
    try:
        # Create intent classification
        intent_classification = IntentClassification(
            intent="legal_query",
            confidence=1.0,
            reasoning="Legal case query"
        )
        
        try:
            # Get or create session from MongoDB
            session = await session_manager.get_or_create_session(
                session_id=request.session_id,
                user_id=request.user_id,
                mode="legal_chat"
            )
            session_id = session["session_id"]
            
            # Fetch history BEFORE adding the current message.
            # This ensures last_user_msgs[-1] is the PREVIOUS question,
            # not the current one — critical for correct FAISS query enrichment.
            chat_history = []
            try:
                chat_history = await session_manager.get_chat_history(session_id, limit=4)
            except Exception as hist_err:
                logger.warning(f"Could not fetch chat history: {hist_err}")

            # Fetch clarification state BEFORE adding the current user message
            clarification_state = {}
            try:
                clarification_state = await session_manager.get_clarification_state(session_id)
            except Exception as cs_err:
                logger.warning(f"Could not fetch clarification state: {cs_err}")

            # Add current user message to session (after history is captured)
            await session_manager.add_message(
                session_id=session_id,
                sender="User",
                message=request.user_input,
                response_type=None
            )
        except Exception as db_err:
            logger.warning(f"MongoDB unavailable, running in stateless mode: {db_err}")
            chat_history = []
            clarification_state = {}
            # Continue without session persistence

        # Handle legal query using RAG system
        return await handle_legal_query(
            user_input=request.user_input,
            intent_classification=intent_classification,
            session_id=session_id,
            chat_history=chat_history,
            clarification_state=clarification_state,
        )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        fallback_intent = IntentClassification(
            intent="legal_query",
            confidence=0.5,
            reasoning=f"Error: {str(e)}"
        )
        
        return ChatResponse(
            intent_classification=fallback_intent,
            response_type="legal_query_response",
            question_analysis=f"Error processing request: {str(e)}",
            answer="I apologize, but I encountered an error. Please try again.",
            tips="Make sure to provide clear input about legal cases or statutes.",
            session_id=session_id
        )


async def handle_legal_query(
    user_input: str,
    intent_classification: IntentClassification,
    session_id: str,
    chat_history: list = [],
    clarification_state: dict = {},
) -> ChatResponse:
    """Handle legal-related queries using RAG system"""
    try:
        # Use RAG system — returns 4-tuple now
        answer, context, options, is_vague = retrieval(
            user_input,
            chat_history=chat_history,
            clarification_state=clarification_state,
        )

        # Update clarification state in session
        try:
            if is_vague:
                current_round = clarification_state.get("round", 0) + 1
                await session_manager.set_pending_clarification(
                    session_id=session_id,
                    original_query=user_input,
                    options=options,
                    current_round=current_round,
                )
            else:
                await session_manager.clear_pending_clarification(session_id)
        except Exception as cs_err:
            logger.warning(f"Could not update clarification state: {cs_err}")

        # Save AI response to session
        await session_manager.add_message(
            session_id=session_id,
            sender="AI",
            message=answer,
            response_type="clarification_needed" if is_vague else "legal_query_response",
        )

        return ChatResponse(
            intent_classification=intent_classification,
            response_type="clarification_needed" if is_vague else "legal_query_response",
            question_analysis="",
            answer=answer,
            tips="",
            session_id=session_id,
            follow_up_options=options,
            is_clarification_needed=is_vague,
        )

    except Exception as e:
        logger.error(f"Error in legal query handler: {e}")
        return ChatResponse(
            intent_classification=intent_classification,
            response_type="legal_query_response",
            question_analysis=f"Error processing legal query: {str(e)}",
            answer="I apologize, but I encountered an error while processing your legal question. Please try rephrasing your question.",
            tips="Make sure to ask specific questions about legal cases, statutes, or legal principles.",
            session_id=session_id,
            follow_up_options=[],
            is_clarification_needed=False,
        )
