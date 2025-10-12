from langchain_ollama import OllamaLLM
from .config import OLLAMA_BASE_URL, LLAMA_MODEL
import json
from typing import Dict, Any

class IntentClassifier:
    def __init__(self):
        self.llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=LLAMA_MODEL,
            temperature=0.1  # Lower temperature for more consistent classification
        )
    
    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user intent into one of the following categories:
        1. aws_query: Questions about AWS services, architecture, or cloud concepts
        2. project_requirements: Descriptions of projects needing cloud infrastructure recommendations
        3. general_chat: General conversation not related to AWS or project requirements
        """
        
        classification_prompt = f"""
        You are an expert intent classifier for a cloud architecture assistant.
        
        Analyze the following user input and classify it into ONE of these categories:
        
        1. "aws_query" - Questions about AWS services, architecture patterns, cloud concepts, technical how-tos
        2. "project_requirements" - Descriptions of projects, applications, or systems that need cloud infrastructure recommendations
        3. "general_chat" - General conversation, greetings, or topics unrelated to AWS/projects
        
        User Input: "{user_input}"
        
        Respond with ONLY a JSON object in this exact format:
        {{
            "intent": "aws_query|project_requirements|general_chat",
            "confidence": 0.0-1.0,
            "reasoning": "Brief explanation of why this classification was chosen"
        }}
        
        Examples:
        - "How does AWS Lambda work?" → aws_query
        - "I'm building an e-commerce platform that needs to handle 10k users" → project_requirements  
        - "Hello, how are you?" → general_chat
        - "What's the best way to store user data in AWS?" → aws_query
        - "We have a mobile app with real-time messaging features" → project_requirements
        """
        
        try:
            response = self.llm.invoke(classification_prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (in case LLM adds extra text)
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate the response structure
                if not all(key in result for key in ['intent', 'confidence', 'reasoning']):
                    raise ValueError("Invalid response structure")
                
                # Validate intent value
                valid_intents = ['aws_query', 'project_requirements', 'general_chat']
                if result['intent'] not in valid_intents:
                    raise ValueError(f"Invalid intent: {result['intent']}")
                
                # Validate confidence
                confidence = float(result['confidence'])
                if not 0.0 <= confidence <= 1.0:
                    raise ValueError(f"Invalid confidence: {confidence}")
                
                return result
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Fallback: simple keyword-based classification
                return self._fallback_classification(user_input, str(e))
                
        except Exception as e:
            # Ultimate fallback
            return self._fallback_classification(user_input, str(e))
    
    def _fallback_classification(self, user_input: str, error_msg: str) -> Dict[str, Any]:
        """
        Fallback classification using keyword matching when LLM fails
        """
        user_input_lower = user_input.lower()
        
        # AWS-related keywords
        aws_keywords = [
            'aws', 'amazon web services', 'ec2', 's3', 'lambda', 'rds', 'dynamodb',
            'cloudformation', 'iam', 'vpc', 'load balancer', 'autoscaling', 'elastic',
            'cloudfront', 'api gateway', 'sqs', 'sns', 'cloudwatch', 'route 53'
        ]
        
        # Project-related keywords
        project_keywords = [
            'building', 'developing', 'creating', 'project', 'application', 'app',
            'website', 'platform', 'system', 'service', 'users', 'traffic',
            'database', 'storage', 'deployment', 'infrastructure', 'architecture'
        ]
        
        # Count keyword matches
        aws_score = sum(1 for keyword in aws_keywords if keyword in user_input_lower)
        project_score = sum(1 for keyword in project_keywords if keyword in user_input_lower)
        
        # Determine intent based on scores
        if aws_score > project_score and aws_score > 0:
            intent = "aws_query"
            confidence = min(0.8, 0.5 + (aws_score * 0.1))
        elif project_score > aws_score and project_score > 0:
            intent = "project_requirements"
            confidence = min(0.8, 0.5 + (project_score * 0.1))
        else:
            intent = "general_chat"
            confidence = 0.6
        
        return {
            "intent": intent,
            "confidence": confidence,
            "reasoning": f"Fallback classification due to LLM error: {error_msg}. Based on keyword analysis."
        }
