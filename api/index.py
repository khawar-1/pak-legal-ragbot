from fastapi import FastAPI, HTTPException
from .models import ChatRequest, SimpleChatResponse, EnhancedChatResponse, IntentClassification, RequirementFollowUpResponse, CompleteRequirementsResponse
from .qa_chain import get_qa_chain, run_qa_chain
from .utils import generate_analysis_and_tips
from .retrieval import retrieval
from .enhanced_intent_classifier import BinaryIntentClassifier
from .requirement_extraction_system import CloudRequirementExtractor
from .conversation_context import conversation_manager
from fastapi.middleware.cors import CORSMiddleware
import time
import json

app = FastAPI(title="RAG Interview Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize services after CORS middleware is added
@app.on_event("startup")
async def startup_event():
    print("Initializing enhanced chatbot system...")
    global qa_chain, intent_classifier, requirement_extractor
    qa_chain = get_qa_chain()
    intent_classifier = BinaryIntentClassifier()
    requirement_extractor = CloudRequirementExtractor()
    print("Enhanced chatbot system ready!")
    time.sleep(1)  # Give Ollama a moment to be ready

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "RAG Interview Assistant is running"}

@app.post("/api/chat")
async def chat(request: ChatRequest) -> EnhancedChatResponse:
    try:
        # Step 1: Classify user intent
        intent_result = intent_classifier.classify_intent(request.user_input)
        intent_classification = IntentClassification(**intent_result)
        
        # Step 2: Route based on intent
        if intent_classification.intent == "aws_query":
            return await handle_aws_query(request.user_input, intent_classification)
        elif intent_classification.intent == "project_requirements":
            return await handle_project_requirements(request.user_input, intent_classification)
        else:
            # Fallback to AWS query
            return await handle_aws_query(request.user_input, intent_classification)
            
    except Exception as e:
        # Fallback response
        fallback_intent = IntentClassification(
            intent="aws_query",
            confidence=0.5,
            reasoning=f"Error in intent classification: {str(e)}"
        )
        return await handle_aws_query(request.user_input, fallback_intent)

async def handle_aws_query(user_input: str, intent_classification: IntentClassification) -> EnhancedChatResponse:
    """Handle AWS-related queries using RAG system"""
    try:
        # Use existing RAG system for AWS queries
        answer = retrieval(user_input)
        analysis, tips = generate_analysis_and_tips(user_input)
        
        return EnhancedChatResponse(
            intent_classification=intent_classification,
            response_type="aws_query_response",
            question_analysis=analysis.generations[0][0].text if hasattr(analysis, 'generations') else str(analysis),
            answer=answer,
            tips=tips.generations[0][0].text if hasattr(tips, 'generations') else str(tips)
        )
    except Exception as e:
        # Fallback response for AWS queries
        return EnhancedChatResponse(
            intent_classification=intent_classification,
            response_type="aws_query_response",
            question_analysis=f"Error processing AWS query: {str(e)}",
            answer="I apologize, but I encountered an error while processing your AWS-related question. Please try rephrasing your question or ensure the RAG system is properly configured.",
            tips="Make sure to ask specific questions about AWS services, architecture patterns, or cloud concepts."
        )

async def handle_project_requirements(user_input: str, intent_classification: IntentClassification) -> EnhancedChatResponse:
    """Handle project requirement extraction"""
    try:
        # Extract requirements from project description
        result = requirement_extractor.extract_requirements(user_input)
        
        if result["type"] == "requirement_follow_up":
            return EnhancedChatResponse(
                intent_classification=intent_classification,
                response_type="requirement_follow_up",
                requirement_follow_up=RequirementFollowUpResponse(**result)
            )
        elif result["type"] == "complete_requirements":
            return EnhancedChatResponse(
                intent_classification=intent_classification,
                response_type="complete_requirements",
                complete_requirements=CompleteRequirementsResponse(**result)
            )
        else:
            # Fallback
            return EnhancedChatResponse(
                intent_classification=intent_classification,
                response_type="requirement_follow_up",
                requirement_follow_up=RequirementFollowUpResponse(
                    current_requirements={},
                    missing_fields=["project_overview", "application_type", "expected_users"],
                    follow_up_questions=[],
                    progress="0/12 fields completed",
                    message="I'll help you extract the cloud requirements for your project. Could you tell me more about what you're building?"
                )
            )
            
    except Exception as e:
        # Fallback response for requirement extraction
        return EnhancedChatResponse(
            intent_classification=intent_classification,
            response_type="requirement_follow_up",
            requirement_follow_up=RequirementFollowUpResponse(
                current_requirements={},
                missing_fields=["project_overview"],
                follow_up_questions=[],
                progress="0/12 fields completed",
                message=f"I encountered an error while analyzing your project requirements: {str(e)}. Please provide more details about your project."
            )
        )

# chat(ChatRequest(user_input="What is a linked list?"))