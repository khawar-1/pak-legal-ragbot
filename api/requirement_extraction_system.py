"""
Enhanced Cloud Requirement Extractor with RAG and Conversation History
"""
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores.faiss import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from .config import OLLAMA_BASE_URL, LLAMA_MODEL, EMBEDDING_MODEL, KNOWLEDGE_BASE_PATH
import json
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class CloudRequirementExtractor:
    """Extracts structured cloud requirements from project descriptions"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=LLAMA_MODEL,
            temperature=0.3
        )
        
        # Required fields - 9 core fields as specified
        self.required_fields = {
            "project_type": "Type of project (e.g., e-commerce, social media, video platform)",
            "scalability": "Scalability needs (users, growth expectations)",
            "storage": "Storage requirements (types and volumes)",
            "security": "Security requirements (authentication, encryption, compliance)",
            "compute": "Compute needs (serverless, containers, VMs)",
            "region": "Deployment region preferences",
            "database": "Database requirements (relational, NoSQL, types)",
            "networking": "Networking needs (CDN, VPC, load balancing)",
            "deployment_preferences": "Deployment preferences (serverless, containers, etc.)"
        }
        
        # Follow-up questions for missing fields - Simple, user-friendly language
        self.follow_up_questions = {
            "project_type": "What kind of project are you building? (e.g., online store, social media app, video platform, mobile app, blog)",
            "scalability": "How many users do you expect? (e.g., small team, thousands per day, growing quickly)",
            "storage": "What kind of files or data will you store? (e.g., images, videos, user profiles, documents, product catalogs)",
            "security": "Who will use your app? Do you need user login, payment protection, or special privacy requirements?",
            "compute": "How should your app handle traffic? (e.g., scale automatically, always running, handle video processing)",
            "region": "Where are most of your users located? (e.g., United States, Europe, Asia, worldwide)",
            "database": "What kind of information will you store? (e.g., user accounts, products for sale, posts/comments, transactions)",
            "networking": "Do you need fast content delivery worldwide? (e.g., for images/videos to load quickly everywhere)",
            "deployment_preferences": "How do you want to run your app? (e.g., automatically scale with traffic, run on fixed servers, simple setup)"
        }
        
        # Initialize RAG components (lazy loading)
        self._vector_store = None
        self._embeddings = None
    
    def _get_rag_context(self, user_input: str) -> str:
        """Get relevant AWS patterns from knowledge base using RAG"""
        try:
            if not self._vector_store:
                # Load and create vector store
                loader = TextLoader(KNOWLEDGE_BASE_PATH)
                documents = loader.load()
                
                text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                texts = text_splitter.split_documents(documents)
                
                self._embeddings = OllamaEmbeddings(
                    base_url=OLLAMA_BASE_URL,
                    model=EMBEDDING_MODEL
                )
                
                self._vector_store = FAISS.from_documents(texts, self._embeddings)
            
            # Retrieve relevant chunks
            retriever = self._vector_store.as_retriever(search_kwargs={"k": 3})
            relevant_docs = retriever.invoke(user_input)
            
            # Format context
            context = "\n".join([doc.page_content for doc in relevant_docs])
            return context[:1000]  # Limit context length
            
        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {e}")
            return ""
    
    def extract_requirements(
        self, 
        user_input: str,
        existing_requirements: Dict[str, Any] = None,
        conversation_history: List[Dict[str, Any]] = None,
        rag_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Extract requirements from user input with conversation context
        
        Args:
            user_input: Current user message
            existing_requirements: Previously extracted requirements
            conversation_history: Last N messages from conversation
            rag_enabled: Whether to use RAG for AWS patterns
        """
        
        if existing_requirements is None:
            existing_requirements = {}
        
        if conversation_history is None:
            conversation_history = []
        
        # Get RAG context if enabled
        rag_context = ""
        if rag_enabled:
            rag_context = self._get_rag_context(user_input)
        
        # Extract information from current input with context
        extracted = self._extract_from_input(
            user_input, 
            existing_requirements, 
            conversation_history,
            rag_context
        )
        
        # Merge with existing requirements (new values override old ones)
        merged_requirements = {**existing_requirements, **extracted}
        
        # Clean up merged requirements (remove None/empty values from new extraction)
        merged_requirements = {
            k: v for k, v in merged_requirements.items() 
            if v and v != "" and v != "null" and v != "None"
        }
        
        # Check what fields are still missing
        missing_fields = self._identify_missing_fields(merged_requirements)
        
        if missing_fields:
            return self._generate_follow_up_response(missing_fields, merged_requirements)
        else:
            return self._generate_complete_requirements_response(merged_requirements)
    
    def _extract_from_input(
        self,
        user_input: str,
        existing_requirements: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        rag_context: str
    ) -> Dict[str, Any]:
        """Extract requirement information using LLM with context"""
        
        # Format conversation history
        history_text = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-5:]:  # Last 5 messages
                sender = msg.get("sender", "User")
                message = msg.get("message", "")
                history_lines.append(f"{sender}: {message}")
            history_text = "\n".join(history_lines)
        
        # Format existing requirements
        existing_text = ""
        if existing_requirements:
            existing_items = [
                f"{k}: {v}" for k, v in existing_requirements.items() 
                if v and v != "" and v != "null"
            ]
            existing_text = "\n".join(existing_items) if existing_items else ""
        
        # Build strict extraction prompt - ONLY extract explicitly stated information
        extraction_prompt = f"""You are a strict requirements extractor. Extract ONLY information that is EXPLICITLY stated in the user input.

{rag_context and f"Relevant AWS Context:\n{rag_context}\n" or ""}

Conversation History (last messages):
{history_text or "No previous conversation"}

Previously Extracted Requirements:
{existing_text or "None"}

Current User Input:
"{user_input}"

CRITICAL RULES:
1. Extract information from user's simple, everyday language and map it to technical requirements
2. DO NOT infer or assume requirements not mentioned
3. DO NOT fill fields based on "typical" patterns - only extract what user describes
4. If a field is not mentioned, you MUST return null for that field
5. Keep previously extracted values unless explicitly updated by the current input
6. MAP simple language to technical terms when extracting (see examples below)

EXTRACTION & MAPPING EXAMPLES:
- "online store" → project_type: "e-commerce platform" (map simple to technical)
- "hundreds of users" → scalability: "low-medium scale, hundreds of users" (extract from simple description)
- "store product images" → storage: "product images storage" (extract what user describes)
- "need user login" → security: "authentication required" (map simple need to technical requirement)
- "US customers" → region: "US region" (map location to region requirement)
- "automatically scale with traffic" → deployment_preferences: "auto-scaling/serverless" (map user description to technical term)

DO NOT infer:
- "ecommerce app" does NOT imply storage, security, database automatically
- Only extract what the user EXPLICITLY describes in their own words
- Then map their simple language to appropriate technical requirement terms

Required fields (9 fields - extract from user's simple language and map to requirements):
- project_type: Extract if user describes what they're building (e.g., "online store" → "e-commerce platform", "social media app" → "social networking platform", "blog" → "content management system")
- scalability: Extract if user mentions users, traffic, or growth in simple terms (e.g., "hundreds of users" → "low-medium scale", "thousands per day" → "high scale", "small team" → "small scale")
- storage: Extract if user mentions files or data in simple terms (e.g., "store images" → "image storage", "user profiles" → "user data storage", "videos" → "video storage")
- security: Extract if user mentions authentication or privacy needs (e.g., "user login" → "authentication required", "payment security" → "secure payment processing", "private data" → "data privacy/encryption")
- compute: Extract if user describes how app should handle load (e.g., "scale automatically" → "auto-scaling/serverless", "handle high traffic" → "high-performance compute", "always running" → "always-on compute")
- region: Extract if user mentions location in simple terms (e.g., "US users" → "US region", "Europe" → "EU region", "worldwide" → "global deployment")
- database: Extract if user mentions what information they'll store (e.g., "user accounts" → "user management database", "products" → "product catalog database", "posts and comments" → "content/social database")
- networking: Extract if user mentions content delivery needs (e.g., "fast image loading" → "CDN for static content", "videos load quickly" → "content delivery optimization")
- deployment_preferences: Extract if user mentions how they want to deploy (e.g., "automatically scale" → "serverless/auto-scaling", "simple setup" → "managed services", "fixed servers" → "traditional VMs")

Respond with ONLY a JSON object (no markdown, no explanation):
{{
    "project_type": "ONLY if explicitly mentioned, else null",
    "scalability": "ONLY if explicitly mentioned, else null",
    "storage": "ONLY if explicitly mentioned, else null",
    "security": "ONLY if explicitly mentioned, else null",
    "compute": "ONLY if explicitly mentioned, else null",
    "region": "ONLY if explicitly mentioned, else null",
    "database": "ONLY if explicitly mentioned, else null",
    "networking": "ONLY if explicitly mentioned, else null",
    "deployment_preferences": "ONLY if explicitly mentioned, else null"
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
                
                # Strict filtering: Only keep explicitly stated values
                filtered_result = {}
                for k, v in result.items():
                    # Reject null, empty, or None values
                    if not v or v == "null" or v == "None" or v == "" or v is None:
                        continue
                    
                    # Reject common inferred patterns
                    if isinstance(v, str):
                        v_lower = v.lower().strip()
                        
                        # Reject very generic/inferred phrases
                        generic_phrases = [
                            "typical", "usually", "generally", "normally", "standard",
                            "expected", "common", "typical for", "standard for",
                            "would need", "should have", "might need", "typically requires"
                        ]
                        
                        is_inferred = any(phrase in v_lower for phrase in generic_phrases)
                        
                        # Reject if value is too generic or looks inferred
                        if is_inferred:
                            logger.debug(f"Rejected inferred value for {k}: {v}")
                            continue
                        
                        # Only keep if value is meaningful (not just filler)
                        if len(v_lower) > 2 and v_lower not in ["yes", "no", "maybe"]:
                            filtered_result[k] = v
                
                # Log extraction results
                if filtered_result:
                    logger.info(f"Extracted {len(filtered_result)} fields from input: {list(filtered_result.keys())}")
                
                return filtered_result
            else:
                logger.warning("No JSON found in LLM response")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error in requirement extraction: {e}")
            return {}
    
    def _identify_missing_fields(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify which required fields are missing or empty"""
        
        missing_fields = []
        
        for field in self.required_fields.keys():
            value = requirements.get(field)
            
            # Check if field is missing or empty
            if not value or value == "" or value == "null" or value == "None":
                missing_fields.append(field)
        
        return missing_fields
    
    def _generate_contextual_question(self, field: str, current_requirements: Dict[str, Any]) -> str:
        """Generate contextual question based on what user already told us"""
        scalability = current_requirements.get("scalability", "").lower() if current_requirements.get("scalability") else ""
        
        if field == "compute" and scalability:
            # Check if low traffic mentioned
            if any(term in scalability for term in ["50", "few", "small", "limited", "low", "not much"]):
                return "Since you have low traffic (50 users), would you prefer simple/always-on setup or auto-scaling? (Simple setup is fine for 50 users)"
        
        if field == "networking" and scalability:
            if any(term in scalability for term in ["50", "few", "small", "local", "single region"]):
                return "Do you need fast content delivery worldwide, or is basic networking sufficient for your 50 users?"
        
        # Default question
        return self.follow_up_questions[field]
    
    def _generate_follow_up_response(
        self, 
        missing_fields: List[str], 
        current_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate follow-up questions for missing fields"""
        
        # Prioritize the most important missing fields
        priority_fields = self._prioritize_fields(missing_fields)
        
        # Generate contextual questions for top priority fields (max 3 at a time)
        questions = []
        for field in priority_fields[:3]:
            question_text = self._generate_contextual_question(field, current_requirements)
            questions.append({
                "field": field,
                "question": question_text,
                "context": self._get_field_context(field)
            })
        
        # Count completed fields
        completed_count = len([v for v in current_requirements.values() if v and v != ""])
        total_count = len(self.required_fields)
        
        return {
            "type": "requirement_follow_up",
            "status": "incomplete",
            "current_requirements": self._format_current_requirements(current_requirements),
            "missing_fields": missing_fields,
            "follow_up_questions": questions,
            "progress": f"{completed_count}/{total_count} fields completed",
            "message": "I need more details to extract complete cloud requirements for your project."
        }
    
    def _generate_complete_requirements_response(
        self, 
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response when all requirements are collected"""
        
        return {
            "type": "complete_requirements",
            "status": "complete",
            "requirements": requirements,
            "message": "All requirements extracted successfully! This data is ready for cloud architecture planning."
        }
    
    def _prioritize_fields(self, missing_fields: List[str]) -> List[str]:
        """Prioritize which fields to ask for first"""
        
        # Priority order for asking questions
        priority_order = [
            "project_type",      # Most important - know what we're building
            "scalability",       # User scale determines architecture
            "region",            # Geographic constraints
            "storage",           # Data requirements
            "security",          # Security needs
            "compute",           # Compute resources
            "database",          # Database needs
            "networking",        # Networking requirements
            "deployment_preferences"  # Deployment approach
        ]
        
        # Sort missing fields by priority
        prioritized = []
        for field in priority_order:
            if field in missing_fields:
                prioritized.append(field)
        
        # Add any remaining fields not in priority order
        for field in missing_fields:
            if field not in prioritized:
                prioritized.append(field)
        
        return prioritized
    
    def _get_field_context(self, field: str) -> str:
        """Get user-friendly context explanation for a field"""
        
        context_map = {
            "project_type": "This helps me understand what you're building and recommend the right cloud services",
            "scalability": "This helps me size your infrastructure correctly - more users need more resources",
            "storage": "This helps me recommend the right storage solution for your files and data",
            "security": "This helps me ensure your app is secure and meets compliance requirements",
            "compute": "This helps me recommend how to run your application efficiently",
            "region": "This helps me deploy your app close to your users for faster performance",
            "database": "This helps me recommend the right database solution for your data",
            "networking": "This helps me ensure fast content delivery to your users worldwide",
            "deployment_preferences": "This helps me recommend the best way to deploy and scale your application"
        }
        
        return context_map.get(field, "This information helps me provide better recommendations for your project")
    
    def _format_current_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Format current requirements for display (remove empty values)"""
        
        formatted = {}
        for field, value in requirements.items():
            if value and value != "" and value != "null" and value != "None":
                formatted[field] = value
        
        return formatted
