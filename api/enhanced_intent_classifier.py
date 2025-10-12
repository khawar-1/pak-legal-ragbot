from langchain_ollama import OllamaLLM
from .config import OLLAMA_BASE_URL, LLAMA_MODEL
import json
from typing import Dict, Any, List

class BinaryIntentClassifier:
    def __init__(self):
        self.llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=LLAMA_MODEL,
            temperature=0.1
        )
        self.confidence_threshold = 0.7
        
        # Keywords for fallback classification
        self.aws_keywords = [
            "aws", "lambda", "s3", "ec2", "rds", "dynamodb", "vpc", "iam",
            "how", "what", "explain", "difference", "compare", "best way",
            "tutorial", "guide", "setup", "configure", "deploy", "cloudformation",
            "api gateway", "cloudfront", "elastic", "autoscaling", "cloudwatch"
        ]
        
        self.project_keywords = [
            "building", "developing", "creating", "project", "application", "app",
            "website", "platform", "system", "users", "traffic", "scale",
            "startup", "company", "business", "need", "require", "want",
            "e-commerce", "social media", "mobile app", "web app", "api"
        ]
    
    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user intent into one of two categories:
        1. aws_query: Technical questions about AWS services
        2. project_requirements: Project descriptions needing requirement extraction
        """
        
        # Try LLM classification first
        llm_result = self._llm_classify(user_input)
        
        if llm_result["confidence"] >= self.confidence_threshold:
            return llm_result
        else:
            # Fall back to keyword-based classification
            return self._keyword_classify(user_input)
    
    def _llm_classify(self, user_input: str) -> Dict[str, Any]:
        """LLM-based intent classification"""
        
        classification_prompt = f"""
        Analyze this user input and classify it into ONE of these categories:
        
        1. "aws_query" - Technical questions about AWS services, how things work, best practices
           Examples: "How does Lambda work?", "What's the best way to store data?", "Explain S3", "Compare Lambda vs EC2"
        
        2. "project_requirements" - Descriptions of projects, applications, or systems that need cloud infrastructure
           Examples: "Building an e-commerce platform", "Need to handle 10k users", "Creating a social media app"
        
        User Input: "{user_input}"
        
        Respond with ONLY this JSON format:
        {{"intent": "aws_query|project_requirements", "confidence": 0.0-1.0, "reasoning": "Brief explanation"}}
        """
        
        try:
            response = self.llm.invoke(classification_prompt)
            
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate result
                if self._validate_intent_result(result):
                    return result
                else:
                    raise ValueError("Invalid LLM response structure")
            else:
                raise ValueError("No JSON found in LLM response")
                
        except Exception as e:
            # Return low confidence result to trigger fallback
            return {
                "intent": "aws_query",
                "confidence": 0.3,
                "reasoning": f"LLM classification failed: {str(e)}"
            }
    
    def _keyword_classify(self, user_input: str) -> Dict[str, Any]:
        """Keyword-based fallback classification"""
        
        user_input_lower = user_input.lower()
        
        # Count keyword matches
        aws_score = sum(1 for keyword in self.aws_keywords if keyword in user_input_lower)
        project_score = sum(1 for keyword in self.project_keywords if keyword in user_input_lower)
        
        # Determine intent based on scores
        if aws_score > project_score and aws_score > 0:
            intent = "aws_query"
            confidence = min(0.8, 0.5 + (aws_score * 0.1))
            reasoning = f"Based on AWS-related keywords: {aws_score} matches"
        elif project_score > aws_score and project_score > 0:
            intent = "project_requirements"
            confidence = min(0.8, 0.5 + (project_score * 0.1))
            reasoning = f"Based on project-related keywords: {project_score} matches"
        else:
            # Default to aws_query for unclear cases
            intent = "aws_query"
            confidence = 0.5
            reasoning = "No clear indicators, defaulting to AWS query"
        
        return {
            "intent": intent,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def _validate_intent_result(self, result: Dict[str, Any]) -> bool:
        """Validate the intent classification result"""
        
        # Check required fields
        if not all(key in result for key in ['intent', 'confidence', 'reasoning']):
            return False
        
        # Check intent is valid
        if result['intent'] not in ['aws_query', 'project_requirements']:
            return False
        
        # Check confidence is valid
        if not isinstance(result['confidence'], (int, float)) or not 0.0 <= result['confidence'] <= 1.0:
            return False
        
        return True
