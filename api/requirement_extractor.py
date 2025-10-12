from langchain_ollama import OllamaLLM
from .config import OLLAMA_BASE_URL, LLAMA_MODEL
import json
from typing import Dict, List, Any, Optional

class CloudRequirementExtractor:
    def __init__(self):
        self.llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=LLAMA_MODEL,
            temperature=0.3
        )
    
    def extract_requirements(self, project_description: str) -> Dict[str, Any]:
        """
        Extract cloud infrastructure requirements from project description
        """
        
        extraction_prompt = f"""
        You are an expert AWS Cloud Solutions Architect. Extract cloud infrastructure requirements from the following project description.
        
        Project Description: "{project_description}"
        
        Analyze the project and extract the following information:
        
        1. **Application Type**: What kind of application is being built?
        2. **User Scale**: Expected number of users, concurrent users, or traffic volume
        3. **Data Requirements**: What kind of data needs to be stored? (user data, files, media, etc.)
        4. **Performance Needs**: Any specific performance requirements mentioned
        5. **Security Requirements**: Any security, compliance, or privacy requirements
        6. **Geographic Distribution**: Any mentions of global deployment or specific regions
        7. **Budget Considerations**: Any cost or budget constraints mentioned
        8. **Technical Stack**: Any specific technologies, frameworks, or programming languages mentioned
        9. **Real-time Features**: Any real-time functionality like messaging, notifications, live updates
        10. **Integration Needs**: Any third-party services or APIs that need to be integrated
        
        Respond with ONLY a JSON object in this exact format:
        {{
            "application_type": "web_app|mobile_app|api|data_platform|other",
            "user_scale": {{
                "expected_users": "number or range",
                "concurrent_users": "number or range",
                "traffic_volume": "low|medium|high|very_high"
            }},
            "data_requirements": {{
                "data_types": ["user_data", "files", "media", "analytics", "other"],
                "storage_size": "small|medium|large|very_large",
                "data_retention": "short_term|long_term|permanent"
            }},
            "performance_needs": {{
                "response_time": "fast|medium|flexible",
                "availability": "standard|high|critical",
                "scalability": "static|moderate|high"
            }},
            "security_requirements": {{
                "authentication": "basic|advanced|enterprise",
                "data_encryption": "required|preferred|not_specified",
                "compliance": ["none", "specific_standards_if_mentioned"]
            }},
            "geographic_distribution": {{
                "regions": ["single_region", "multiple_regions", "global"],
                "specific_regions": ["if_mentioned"]
            }},
            "budget_considerations": {{
                "cost_sensitivity": "low|medium|high",
                "budget_constraints": "none|moderate|strict"
            }},
            "technical_stack": {{
                "languages": ["if_mentioned"],
                "frameworks": ["if_mentioned"],
                "databases": ["if_mentioned"],
                "other_technologies": ["if_mentioned"]
            }},
            "real_time_features": {{
                "messaging": true|false,
                "notifications": true|false,
                "live_updates": true|false,
                "other_realtime": ["if_mentioned"]
            }},
            "integration_needs": {{
                "third_party_apis": ["if_mentioned"],
                "payment_systems": true|false,
                "social_media": true|false,
                "other_integrations": ["if_mentioned"]
            }},
            "aws_recommendations": {{
                "compute_services": ["suggested_based_on_requirements"],
                "storage_services": ["suggested_based_on_requirements"],
                "database_services": ["suggested_based_on_requirements"],
                "networking_services": ["suggested_based_on_requirements"],
                "security_services": ["suggested_based_on_requirements"],
                "monitoring_services": ["suggested_based_on_requirements"]
            }},
            "confidence_score": 0.0-1.0,
            "extraction_notes": "Any important details that don't fit in the above categories"
        }}
        
        Guidelines:
        - If information is not mentioned, use reasonable defaults or mark as "not_specified"
        - For numbers, use ranges when uncertain (e.g., "1000-5000")
        - Be conservative in recommendations - suggest proven, scalable solutions
        - Consider cost-effectiveness in recommendations
        - If multiple options are suitable, list them in order of preference
        """
        
        try:
            response = self.llm.invoke(extraction_prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate and clean the result
                result = self._validate_and_clean_result(result)
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback: structured text extraction
                return self._fallback_extraction(project_description, str(e))
                
        except Exception as e:
            return self._fallback_extraction(project_description, str(e))
    
    def _validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean the extracted requirements
        """
        # Ensure all required fields exist with defaults
        defaults = {
            "application_type": "web_app",
            "user_scale": {
                "expected_users": "not_specified",
                "concurrent_users": "not_specified", 
                "traffic_volume": "medium"
            },
            "data_requirements": {
                "data_types": ["user_data"],
                "storage_size": "medium",
                "data_retention": "long_term"
            },
            "performance_needs": {
                "response_time": "medium",
                "availability": "standard",
                "scalability": "moderate"
            },
            "security_requirements": {
                "authentication": "basic",
                "data_encryption": "preferred",
                "compliance": ["none"]
            },
            "geographic_distribution": {
                "regions": ["single_region"],
                "specific_regions": []
            },
            "budget_considerations": {
                "cost_sensitivity": "medium",
                "budget_constraints": "moderate"
            },
            "technical_stack": {
                "languages": [],
                "frameworks": [],
                "databases": [],
                "other_technologies": []
            },
            "real_time_features": {
                "messaging": False,
                "notifications": False,
                "live_updates": False,
                "other_realtime": []
            },
            "integration_needs": {
                "third_party_apis": [],
                "payment_systems": False,
                "social_media": False,
                "other_integrations": []
            },
            "aws_recommendations": {
                "compute_services": ["EC2"],
                "storage_services": ["S3"],
                "database_services": ["RDS"],
                "networking_services": ["VPC"],
                "security_services": ["IAM"],
                "monitoring_services": ["CloudWatch"]
            },
            "confidence_score": 0.7,
            "extraction_notes": "Extracted with standard defaults applied"
        }
        
        # Merge defaults with extracted data
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value
            elif isinstance(default_value, dict) and isinstance(result[key], dict):
                for sub_key, sub_default in default_value.items():
                    if sub_key not in result[key]:
                        result[key][sub_key] = sub_default
        
        # Ensure confidence score is valid
        if not isinstance(result.get('confidence_score'), (int, float)) or not 0 <= result['confidence_score'] <= 1:
            result['confidence_score'] = 0.7
        
        return result
    
    def _fallback_extraction(self, project_description: str, error_msg: str) -> Dict[str, Any]:
        """
        Fallback extraction using keyword analysis when LLM fails
        """
        description_lower = project_description.lower()
        
        # Basic keyword analysis
        app_type = "web_app"
        if any(word in description_lower for word in ['mobile', 'ios', 'android', 'app']):
            app_type = "mobile_app"
        elif any(word in description_lower for word in ['api', 'microservice', 'service']):
            app_type = "api"
        elif any(word in description_lower for word in ['data', 'analytics', 'ml', 'machine learning']):
            app_type = "data_platform"
        
        # Estimate scale based on keywords
        scale = "medium"
        if any(word in description_lower for word in ['thousand', 'k users', '10k', 'large']):
            scale = "high"
        elif any(word in description_lower for word in ['million', 'm users', 'global', 'worldwide']):
            scale = "very_high"
        elif any(word in description_lower for word in ['small', 'few', 'startup', 'prototype']):
            scale = "low"
        
        # Basic AWS recommendations based on app type and scale
        recommendations = {
            "compute_services": ["EC2"],
            "storage_services": ["S3"],
            "database_services": ["RDS"],
            "networking_services": ["VPC"],
            "security_services": ["IAM"],
            "monitoring_services": ["CloudWatch"]
        }
        
        if app_type == "mobile_app":
            recommendations["compute_services"] = ["Lambda", "API Gateway", "EC2"]
            recommendations["database_services"] = ["DynamoDB", "RDS"]
        elif scale in ["high", "very_high"]:
            recommendations["compute_services"] = ["ECS", "Lambda", "Auto Scaling"]
            recommendations["database_services"] = ["RDS", "ElastiCache", "DynamoDB"]
        
        return {
            "application_type": app_type,
            "user_scale": {
                "expected_users": "not_specified",
                "concurrent_users": "not_specified",
                "traffic_volume": scale
            },
            "data_requirements": {
                "data_types": ["user_data"],
                "storage_size": "medium",
                "data_retention": "long_term"
            },
            "performance_needs": {
                "response_time": "medium",
                "availability": "standard",
                "scalability": "moderate"
            },
            "security_requirements": {
                "authentication": "basic",
                "data_encryption": "preferred",
                "compliance": ["none"]
            },
            "geographic_distribution": {
                "regions": ["single_region"],
                "specific_regions": []
            },
            "budget_considerations": {
                "cost_sensitivity": "medium",
                "budget_constraints": "moderate"
            },
            "technical_stack": {
                "languages": [],
                "frameworks": [],
                "databases": [],
                "other_technologies": []
            },
            "real_time_features": {
                "messaging": False,
                "notifications": False,
                "live_updates": False,
                "other_realtime": []
            },
            "integration_needs": {
                "third_party_apis": [],
                "payment_systems": False,
                "social_media": False,
                "other_integrations": []
            },
            "aws_recommendations": recommendations,
            "confidence_score": 0.5,
            "extraction_notes": f"Fallback extraction due to LLM error: {error_msg}. Based on keyword analysis."
        }
    
    def generate_recommendation_summary(self, requirements: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of AWS recommendations
        """
        try:
            summary_prompt = f"""
            Based on the following extracted project requirements, generate a clear, actionable AWS architecture recommendation summary.
            
            Requirements: {json.dumps(requirements, indent=2)}
            
            Provide a summary that includes:
            1. **Project Overview**: Brief description of what's being built
            2. **Key AWS Services**: Main services recommended and why
            3. **Architecture Highlights**: Key architectural decisions
            4. **Cost Considerations**: Budget-friendly recommendations
            5. **Next Steps**: What to do first when starting the implementation
            
            Keep it concise but comprehensive, focusing on actionable advice for a developer or architect.
            """
            
            response = self.llm.invoke(summary_prompt)
            return response
            
        except Exception as e:
            # Fallback summary
            app_type = requirements.get('application_type', 'web_app')
            scale = requirements.get('user_scale', {}).get('traffic_volume', 'medium')
            
            recommendations = requirements.get('aws_recommendations', {})
            compute = ', '.join(recommendations.get('compute_services', ['EC2']))
            storage = ', '.join(recommendations.get('storage_services', ['S3']))
            database = ', '.join(recommendations.get('database_services', ['RDS']))
            
            return f"""
**AWS Architecture Recommendation Summary**

**Project Type**: {app_type.replace('_', ' ').title()}
**Expected Scale**: {scale.replace('_', ' ').title()}

**Recommended AWS Services**:
- **Compute**: {compute}
- **Storage**: {storage}  
- **Database**: {database}

**Next Steps**:
1. Set up VPC and networking infrastructure
2. Deploy compute resources based on scale requirements
3. Configure storage and database services
4. Implement security and monitoring

*Note: This is a fallback summary. For detailed recommendations, please ensure the LLM service is running properly.*
            """
