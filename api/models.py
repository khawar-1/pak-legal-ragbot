from pydantic import BaseModel
from typing import Dict, List, Any, Optional

class ChatRequest(BaseModel):
    user_input: str

class SimpleChatResponse(BaseModel):
    question_analysis: str
    answer: str
    tips: str

class IntentClassification(BaseModel):
    intent: str  # "aws_query" or "project_requirements"
    confidence: float
    reasoning: str

class FollowUpQuestion(BaseModel):
    field: str
    question: str
    context: str

class RequirementFollowUpResponse(BaseModel):
    type: str = "requirement_follow_up"
    status: str = "incomplete"
    current_requirements: Dict[str, Any]
    missing_fields: List[str]
    follow_up_questions: List[FollowUpQuestion]
    progress: str
    message: str

class CompleteRequirementsResponse(BaseModel):
    type: str = "complete_requirements"
    status: str = "complete"
    requirements: Dict[str, Any]
    message: str

class EnhancedChatResponse(BaseModel):
    intent_classification: IntentClassification
    response_type: str  # "aws_query_response" or "requirement_follow_up" or "complete_requirements"
    
    # For AWS query responses (existing)
    question_analysis: Optional[str] = None
    answer: Optional[str] = None
    tips: Optional[str] = None
    
    # For requirement extraction responses
    requirement_follow_up: Optional[RequirementFollowUpResponse] = None
    complete_requirements: Optional[CompleteRequirementsResponse] = None
    
    # Session management
    session_id: Optional[str] = None


class UserScale(BaseModel):
    expected_users: str
    concurrent_users: str
    traffic_volume: str

class DataRequirements(BaseModel):
    data_types: List[str]
    storage_size: str
    data_retention: str

class PerformanceNeeds(BaseModel):
    response_time: str
    availability: str
    scalability: str

class SecurityRequirements(BaseModel):
    authentication: str
    data_encryption: str
    compliance: List[str]

class GeographicDistribution(BaseModel):
    regions: List[str]
    specific_regions: List[str]

class BudgetConsiderations(BaseModel):
    cost_sensitivity: str
    budget_constraints: str

class TechnicalStack(BaseModel):
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    other_technologies: List[str]

class RealTimeFeatures(BaseModel):
    messaging: bool
    notifications: bool
    live_updates: bool
    other_realtime: List[str]

class IntegrationNeeds(BaseModel):
    third_party_apis: List[str]
    payment_systems: bool
    social_media: bool
    other_integrations: List[str]

class AWSRecommendations(BaseModel):
    compute_services: List[str]
    storage_services: List[str]
    database_services: List[str]
    networking_services: List[str]
    security_services: List[str]
    monitoring_services: List[str]

class ExtractedRequirements(BaseModel):
    application_type: str
    user_scale: UserScale
    data_requirements: DataRequirements
    performance_needs: PerformanceNeeds
    security_requirements: SecurityRequirements
    geographic_distribution: GeographicDistribution
    budget_considerations: BudgetConsiderations
    technical_stack: TechnicalStack
    real_time_features: RealTimeFeatures
    integration_needs: IntegrationNeeds
    aws_recommendations: AWSRecommendations
    confidence_score: float
    extraction_notes: str

class ChatResponse(BaseModel):
    intent_classification: IntentClassification
    response_type: str  # "aws_query_response", "requirement_extraction_response", "general_chat_response"
    
    # For AWS query responses
    question_analysis: Optional[str] = None
    answer: Optional[str] = None
    tips: Optional[str] = None
    
    # For requirement extraction responses
    extracted_requirements: Optional[ExtractedRequirements] = None
    recommendation_summary: Optional[str] = None
    
    # For general chat responses
    general_response: Optional[str] = None