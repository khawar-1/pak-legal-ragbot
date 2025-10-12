from langchain_ollama import OllamaLLM
from .config import OLLAMA_BASE_URL, LLAMA_MODEL
import json
from typing import Dict, Any, List, Optional

class CloudRequirementExtractor:
    def __init__(self):
        self.llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=LLAMA_MODEL,
            temperature=0.3
        )
        
        # Required fields for complete requirement extraction
        self.required_fields = {
            "project_overview": "Brief description of the project",
            "application_type": "Type of application (web app, mobile app, API, etc.)",
            "expected_users": "Number of expected users",
            "concurrent_users": "Peak concurrent users",
            "data_types": "Types of data to be stored",
            "data_volume": "Expected data volume",
            "performance_requirements": "Response time, availability needs",
            "security_requirements": "Authentication, compliance needs",
            "budget_constraints": "Budget limitations",
            "deployment_region": "Geographic deployment requirements",
            "integration_needs": "Third-party integrations required",
            "scalability_requirements": "Growth expectations"
        }
        
        # Follow-up questions for missing fields
        self.follow_up_questions = {
            "project_overview": "Could you provide a brief description of your project?",
            "application_type": "What type of application are you building? (web app, mobile app, API, data platform, etc.)",
            "expected_users": "How many users do you expect to handle? (e.g., 1,000, 10,000, 100,000)",
            "concurrent_users": "How many users will be using the system simultaneously at peak times?",
            "data_types": "What kind of data will you store? (user profiles, transactions, media files, logs, etc.)",
            "data_volume": "What's the expected data volume? (small, medium, large, very large)",
            "performance_requirements": "Any specific performance needs? (response time, uptime requirements)",
            "security_requirements": "Any security or compliance requirements? (authentication, data encryption, GDPR, etc.)",
            "budget_constraints": "Any budget considerations? (low-cost, enterprise, etc.)",
            "deployment_region": "Where do you need to deploy? (single region, multiple regions, global)",
            "integration_needs": "Any third-party integrations required? (payment systems, APIs, etc.)",
            "scalability_requirements": "How do you expect the system to grow over time?"
        }
    
    def extract_requirements(self, user_input: str, existing_requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract requirements from user input and determine if follow-up questions are needed
        """
        
        if existing_requirements is None:
            existing_requirements = {}
        
        # Extract information from current input
        extracted = self._extract_from_input(user_input)
        
        # Merge with existing requirements
        merged_requirements = {**existing_requirements, **extracted}
        
        # Check what fields are still missing
        missing_fields = self._identify_missing_fields(merged_requirements)
        
        if missing_fields:
            return self._generate_follow_up_response(missing_fields, merged_requirements)
        else:
            return self._generate_complete_requirements_response(merged_requirements)
    
    def _extract_from_input(self, user_input: str) -> Dict[str, Any]:
        """Extract requirement information from user input using LLM"""
        
        extraction_prompt = f"""
        Extract cloud infrastructure requirements from this project description:
        
        "{user_input}"
        
        Analyze and extract the following information if mentioned:
        
        1. Project Overview: Brief description of what's being built
        2. Application Type: Type of application (web app, mobile app, API, data platform, etc.)
        3. User Scale: Expected users, concurrent users, traffic volume
        4. Data Requirements: Types of data, storage needs, volume
        5. Performance Needs: Response time, availability, scalability requirements
        6. Security Requirements: Authentication, compliance, encryption needs
        7. Budget Considerations: Cost constraints, pricing preferences
        8. Deployment: Geographic requirements, regions
        9. Integrations: Third-party services, APIs needed
        10. Scalability: Growth expectations, future needs
        
        Respond with ONLY a JSON object:
        {{
            "project_overview": "description if mentioned, else empty string",
            "application_type": "type if mentioned, else empty string",
            "expected_users": "number or range if mentioned, else empty string",
            "concurrent_users": "number if mentioned, else empty string",
            "data_types": ["list of data types if mentioned"],
            "data_volume": "size if mentioned, else empty string",
            "performance_requirements": "requirements if mentioned, else empty string",
            "security_requirements": "requirements if mentioned, else empty string",
            "budget_constraints": "constraints if mentioned, else empty string",
            "deployment_region": "regions if mentioned, else empty string",
            "integration_needs": ["list of integrations if mentioned"],
            "scalability_requirements": "requirements if mentioned, else empty string"
        }}
        """
        
        try:
            response = self.llm.invoke(extraction_prompt)
            
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                return {}
                
        except Exception as e:
            print(f"Error in requirement extraction: {e}")
            return {}
    
    def _identify_missing_fields(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify which required fields are missing or empty"""
        
        missing_fields = []
        
        for field in self.required_fields.keys():
            value = requirements.get(field, "")
            
            # Check if field is missing or empty
            if not value or (isinstance(value, list) and len(value) == 0):
                missing_fields.append(field)
        
        return missing_fields
    
    def _generate_follow_up_response(self, missing_fields: List[str], current_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate follow-up questions for missing fields"""
        
        # Prioritize the most important missing fields (ask for 1-3 at a time)
        priority_fields = self._prioritize_fields(missing_fields)
        
        # Generate questions for top priority fields
        questions = []
        for field in priority_fields[:3]:  # Ask max 3 questions at once
            questions.append({
                "field": field,
                "question": self.follow_up_questions[field],
                "context": self._get_field_context(field)
            })
        
        return {
            "type": "requirement_follow_up",
            "status": "incomplete",
            "current_requirements": self._format_current_requirements(current_requirements),
            "missing_fields": missing_fields,
            "follow_up_questions": questions,
            "progress": f"{len(current_requirements)}/{len(self.required_fields)} fields completed",
            "message": "I need more details to extract complete cloud requirements for your project."
        }
    
    def _generate_complete_requirements_response(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response when all requirements are collected"""
        
        return {
            "type": "complete_requirements",
            "status": "complete",
            "requirements": self._format_final_requirements(requirements),
            "message": "✅ All requirements extracted successfully! This data is ready for cloud architecture planning."
        }
    
    def _prioritize_fields(self, missing_fields: List[str]) -> List[str]:
        """Prioritize which fields to ask for first"""
        
        # Priority order for asking questions
        priority_order = [
            "project_overview",
            "application_type", 
            "expected_users",
            "data_types",
            "performance_requirements",
            "security_requirements",
            "budget_constraints",
            "deployment_region",
            "concurrent_users",
            "data_volume",
            "integration_needs",
            "scalability_requirements"
        ]
        
        # Sort missing fields by priority
        prioritized = []
        for field in priority_order:
            if field in missing_fields:
                prioritized.append(field)
        
        return prioritized
    
    def _get_field_context(self, field: str) -> str:
        """Get context information for a field"""
        
        context_map = {
            "expected_users": "This helps determine the right infrastructure scale",
            "application_type": "Different application types require different architectures",
            "data_types": "Understanding your data helps recommend appropriate storage solutions",
            "performance_requirements": "Performance needs affect service selection and configuration",
            "security_requirements": "Security needs determine authentication and encryption requirements",
            "budget_constraints": "Budget helps optimize cost-effective solutions"
        }
        
        return context_map.get(field, "This information helps provide better recommendations")
    
    def _format_current_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Format current requirements for display"""
        
        formatted = {}
        for field, value in requirements.items():
            if value:  # Only include non-empty values
                formatted[field] = value
        
        return formatted
    
    def _format_final_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Format final requirements in a structured way"""
        
        return {
            "project_overview": requirements.get("project_overview", ""),
            "application_type": requirements.get("application_type", ""),
            "user_scale": {
                "expected_users": requirements.get("expected_users", ""),
                "concurrent_users": requirements.get("concurrent_users", ""),
                "scalability_requirements": requirements.get("scalability_requirements", "")
            },
            "data_requirements": {
                "data_types": requirements.get("data_types", []),
                "data_volume": requirements.get("data_volume", "")
            },
            "performance_needs": {
                "performance_requirements": requirements.get("performance_requirements", "")
            },
            "security_requirements": {
                "security_requirements": requirements.get("security_requirements", "")
            },
            "deployment_requirements": {
                "deployment_region": requirements.get("deployment_region", ""),
                "budget_constraints": requirements.get("budget_constraints", ""),
                "integration_needs": requirements.get("integration_needs", [])
            }
        }
