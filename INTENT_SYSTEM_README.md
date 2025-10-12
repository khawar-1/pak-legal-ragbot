# AWS Cloud Assistant - Intent-Based Chatbot System

## Overview

This enhanced chatbot system now supports **intent classification** and **cloud requirement extraction** in addition to the existing AWS RAG (Retrieval-Augmented Generation) functionality. The system automatically detects what type of query the user is making and routes it to the appropriate handler.

## Features

### 1. Intent Classification
The system automatically classifies user input into three categories:
- **`aws_query`**: Questions about AWS services, architecture patterns, or cloud concepts
- **`project_requirements`**: Descriptions of projects needing cloud infrastructure recommendations  
- **`general_chat`**: General conversation, greetings, or unrelated topics

### 2. Cloud Requirement Extraction
When users describe their projects, the system extracts:
- Application type and scale
- Data storage requirements
- Performance and security needs
- Technical stack preferences
- Real-time feature requirements
- Integration needs
- AWS service recommendations

### 3. Smart Routing
Based on intent classification, the system routes requests to:
- **RAG System**: For AWS knowledge queries
- **Requirement Extractor**: For project analysis
- **General Handler**: For casual conversation

## API Response Structure

The new API returns structured responses with the following format:

```json
{
  "intent_classification": {
    "intent": "aws_query|project_requirements|general_chat",
    "confidence": 0.85,
    "reasoning": "User is asking about AWS Lambda service"
  },
  "response_type": "aws_query_response|requirement_extraction_response|general_chat_response",
  
  // For AWS queries
  "question_analysis": "Analysis of the AWS question",
  "answer": "RAG-generated answer from knowledge base",
  "tips": "Additional AWS tips and best practices",
  
  // For project requirements
  "extracted_requirements": {
    "application_type": "web_app|mobile_app|api|data_platform",
    "user_scale": {
      "expected_users": "1000-5000",
      "concurrent_users": "100-500", 
      "traffic_volume": "medium"
    },
    "aws_recommendations": {
      "compute_services": ["EC2", "Lambda"],
      "storage_services": ["S3"],
      "database_services": ["RDS"]
    }
    // ... more detailed requirements
  },
  "recommendation_summary": "Human-readable AWS architecture recommendations",
  
  // For general chat
  "general_response": "Helpful guidance on how to use the assistant"
}
```

## Usage Examples

### AWS Query Example
```
User: "How does AWS Lambda work?"
Response: Routes to RAG system, returns detailed AWS Lambda information from knowledge base
```

### Project Requirements Example
```
User: "I'm building an e-commerce platform that needs to handle 10,000 users, store product images, and process payments"
Response: Extracts requirements and provides AWS architecture recommendations including:
- EC2/ECS for compute
- RDS for database
- S3 for image storage
- API Gateway for payment processing
- CloudFront for CDN
```

### General Chat Example
```
User: "Hello, how are you?"
Response: Provides helpful guidance on how to use the assistant for AWS queries and project requirements
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r api/requirements.txt
```

### 2. Configure Ollama
Make sure Ollama is running with the required models:
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 3. Update Environment Variables
Create/update `.env.local`:
```
OLLAMA_BASE_URL=http://localhost:11434
LLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
KNOWLEDGE_BASE_PATH=api/data_structure_q_&_a.txt
```

### 4. Start the System
```bash
npm run dev
```

## Testing

Run the test script to verify functionality:
```bash
python api/test_intent_system.py
```

## Architecture

### Components

1. **IntentClassifier** (`api/intent_classifier.py`)
   - Uses LLM to classify user intent
   - Fallback keyword-based classification
   - Returns structured intent data

2. **CloudRequirementExtractor** (`api/requirement_extractor.py`)
   - Extracts detailed project requirements
   - Generates AWS service recommendations
   - Provides human-readable summaries

3. **Enhanced API** (`api/index.py`)
   - Routes requests based on intent
   - Maintains backward compatibility
   - Provides structured responses

4. **Updated Models** (`api/models.py`)
   - Pydantic models for all data structures
   - Type validation and serialization
   - Comprehensive requirement schemas

### Flow Diagram

```
User Input
    ↓
Intent Classification
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   AWS Query     │ Project Req.    │ General Chat    │
│       ↓         │       ↓         │       ↓         │
│ RAG System      │ Req. Extractor  │ Simple Response │
│ (Existing)      │ (New)           │ (New)           │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
Structured Response
```

## Configuration

### Intent Classification Settings
- **Temperature**: 0.1 (for consistent classification)
- **Fallback**: Keyword-based matching
- **Confidence Threshold**: Configurable per use case

### Requirement Extraction Settings  
- **Temperature**: 0.3 (balanced creativity/consistency)
- **Validation**: Automatic data validation and defaults
- **Fallback**: Keyword-based analysis

## Error Handling

The system includes comprehensive error handling:
- **LLM Failures**: Automatic fallback to keyword-based classification/extraction
- **JSON Parsing Errors**: Graceful degradation with default responses
- **Service Unavailable**: Helpful error messages with troubleshooting tips

## Future Enhancements

Potential improvements:
1. **Learning from User Feedback**: Improve classification accuracy over time
2. **Custom Requirement Templates**: Industry-specific requirement extraction
3. **Cost Estimation**: Integrate AWS pricing data for budget recommendations
4. **Architecture Diagrams**: Generate visual architecture recommendations
5. **Multi-cloud Support**: Extend beyond AWS to other cloud providers

## Troubleshooting

### Common Issues

1. **Ollama Connection Errors**
   - Ensure Ollama is running: `ollama serve`
   - Check model availability: `ollama list`
   - Verify base URL in configuration

2. **Classification Accuracy Issues**
   - Provide more context in queries
   - Use specific AWS terminology for AWS queries
   - Include project details for requirement extraction

3. **Performance Issues**
   - Reduce temperature for faster responses
   - Use smaller models for classification
   - Implement caching for frequent queries

### Debug Mode

Enable detailed logging by setting environment variable:
```
DEBUG=true
```

This will provide detailed information about intent classification, requirement extraction, and routing decisions.
