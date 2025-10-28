# 🤖 Complete Chatbot System Architecture

## 🏗️ Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌──────────────────────┐  ┌──────────────────────────────┐   │
│  │  AWS Chat Mode       │  │  Requirement Extraction Mode  │   │
│  │  - Chat UI           │  │  - Chat UI                   │   │
│  │  - Message History   │  │  - Message History           │   │
│  │  - Separate Context  │  │  - Progress Tracker          │   │
│  └──────────────────────┘  └──────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP POST /api/chat
                                │ { user_input, mode, session_id }
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI - Python)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Main API Endpoint: /api/chat                   │  │
│  │  • Receives: user_input, mode, session_id                │  │
│  │  • Routes to appropriate handler based on mode           │  │
│  └───────────────────┬───────────────────┬───────────────────┘  │
│                      │                   │                      │
│        ┌─────────────▼──────────┐  ┌────▼──────────────────┐  │
│        │  AWS Chat Handler       │  │ Requirement Extractor  │  │
│        │  (handle_aws_query)     │  │ (handle_project_req)  │  │
│        └─────────────┬──────────┘  └────┬──────────────────┘  │
│                      │                   │                      │
│        ┌─────────────▼──────────┐  ┌────▼──────────────────┐  │
│        │   RAG Pipeline          │  │ LLM + RAG Extraction  │  │
│        │  • Vector DB (FAISS)    │  │ • Context from MongoDB│  │
│        │  • AWS Knowledge Base   │  │ • Last 5 messages     │  │
│        │  • Ollama Embeddings    │  │ • Extract JSON        │  │
│        │  • Llama 3B (LLM)       │  │ • Generate follow-ups │  │
│        └─────────────┬──────────┘  └────┬──────────────────┘  │
│                      │                   │                      │
└──────────────────────┼───────────────────┼──────────────────────┘
                       │                   │
           ┌───────────▼──────────┐  ┌────▼──────────────────┐
           │  Ollama LLM Service  │  │  MongoDB Database      │
           │  (llama3.1:8b)       │  │  • Session Storage     │
           │  • Text Generation   │  │  • Chat History        │
           │  • Embeddings        │  │  • Requirements JSON   │
           └──────────────────────┘  └───────────────────────┘
```

---

## 📋 Complete Flow Breakdown

### 🎯 **Mode 1: AWS Chat (RAG-Enhanced Q&A)**

#### **Step-by-Step Flow:**

```
1. USER ACTION
   └─> User selects "AWS Chat" mode
   └─> Types: "What is AWS Lambda?"

2. FRONTEND
   └─> Creates request: { user_input: "What is Lambda?", mode: "aws_chat", session_id: "abc123" }
   └─> POST to http://localhost:8000/api/chat

3. BACKEND (FastAPI)
   └─> Receives request at /api/chat endpoint
   └─> Routes to handle_aws_query()

4. RAG PIPELINE
   └─> Load AWS knowledge base (data_structure_q_&_a.txt)
   └─> Split into chunks
   └─> Create FAISS vector database with Ollama embeddings
   └─> Search: "What is Lambda?" → Retrieves top 5 relevant chunks
   └─> Build prompt with retrieved context
   └─> Send to Llama 3B model via Ollama API

5. LLM PROCESSING
   └─> Llama 3B receives: Context + User Question
   └─> Generates answer based on AWS knowledge base context
   └─> Returns: "Lambda is serverless compute that runs code..."

6. BACKEND RESPONSE
   └─> Formats response as EnhancedChatResponse
   └─> Returns: { answer, question_analysis, tips, intent_classification }

7. FRONTEND DISPLAY
   └─> Shows answer in chat UI
   └─> Updates AWS chat history
   └─> User can continue conversation
```

#### **Technical Details:**
- **Knowledge Base**: `api/data_structure_q_&_a.txt` (AWS Q&A)
- **Embeddings**: Nomic Embed Text (via Ollama)
- **Vector Store**: FAISS (in-memory, rebuilt each request)
- **Retrieval**: Top 5 most relevant chunks
- **LLM**: Llama 3.1:8b (via Ollama API)
- **Context**: Retrieved AWS docs + user question

---

### 🎯 **Mode 2: Requirement Extraction (Structured Extraction)**

#### **Step-by-Step Flow:**

```
1. USER ACTION
   └─> User selects "Requirement Extraction" mode
   └─> Types: "I'm building an e-commerce platform for 1000 users/day"

2. FRONTEND
   └─> Creates request: { user_input: "...", mode: "requirement_extraction", session_id: "xyz789" }
   └─> POST to http://localhost:8000/api/chat

3. BACKEND (FastAPI)
   └─> Receives request at /api/chat endpoint
   └─> Routes to handle_project_requirements()

4. SESSION MANAGEMENT
   └─> Load session from MongoDB using session_id
   └─> If no session → Create new session
   └─> Get existing requirements and chat history

5. RAG ENHANCEMENT (Optional but Recommended)
   └─> Retrieve relevant AWS patterns from knowledge base
   └─> Get similar project examples (e.g., "e-commerce platform patterns")
   └─> Extract AWS service recommendations context

6. CONTEXT BUILDING
   └─> Get last 5 messages from conversation history
   └─> Merge with existing requirements JSON
   └─> Build comprehensive prompt with:
       • Current user input
       • Conversation history
       • Existing requirements
       • RAG-retrieved patterns

7. LLM EXTRACTION
   └─> Send to Llama 3B with extraction prompt
   └─> LLM extracts/updates requirements JSON:
       {
         "project_type": "e-commerce platform",
         "scalability": "high - 1000 users/day",
         "storage": "product images, user data",
         "security": "authentication, payment encryption",
         "compute": "web application servers",
         "region": null,  // Missing!
         "database": "user data, products, orders",
         "networking": "CDN for images",
         "deployment_preferences": null  // Missing!
       }

8. MISSING FIELD CHECK
   └─> Compare extracted JSON with required fields
   └─> Identify missing: ["region", "deployment_preferences"]
   └─> If missing → Generate follow-up questions
   └─> If complete → Mark as complete

9. DATABASE UPDATE
   └─> Save updated requirements to MongoDB
   └─> Save new chat messages
   └─> Update session last_updated timestamp

10. BACKEND RESPONSE
    └─> If incomplete:
        {
          response_type: "requirement_follow_up",
          current_requirements: {...},
          missing_fields: ["region", "deployment_preferences"],
          follow_up_questions: [
            {
              field: "region",
              question: "Which region do you want to deploy?",
              context: "Helps determine latency and compliance"
            }
          ],
          progress: "7/9 fields completed"
        }
    └─> If complete:
        {
          response_type: "complete_requirements",
          requirements: {...complete JSON...},
          message: "✅ All requirements extracted!"
        }

11. FRONTEND DISPLAY
    └─> Shows follow-up questions or completion message
    └─> Updates progress bar (7/9 fields)
    └─> Displays current requirements JSON
    └─> User answers follow-up questions
    └─> Process repeats until all fields filled
```

#### **Technical Details:**
- **Extraction Schema**: 9 core fields (project_type, scalability, storage, security, compute, region, database, networking, deployment_preferences)
- **Context Sources**: 
  - MongoDB chat history (last 5 messages)
  - Existing requirements JSON
  - RAG-retrieved AWS patterns (optional)
- **Database**: MongoDB for persistence
- **LLM**: Llama 3.1:8b for structured extraction
- **Follow-up Logic**: Prioritizes most important missing fields

---

## 🗄️ Database Schema (MongoDB)

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "abc123",
  "user_id": "kashan",  // Optional
  "mode": "requirement_extraction",  // or "aws_chat"
  
  // Chat History
  "chat_history": [
    {
      "timestamp": "2025-01-27T10:00:00Z",
      "sender": "User",
      "message": "I'm building an e-commerce platform",
      "response_type": null
    },
    {
      "timestamp": "2025-01-27T10:00:05Z",
      "sender": "AI",
      "message": "Could you specify the deployment region?",
      "response_type": "requirement_follow_up"
    }
  ],
  
  // Requirements (only for requirement_extraction mode)
  "extracted_requirements": {
    "project_type": "e-commerce platform",
    "scalability": "high - 1000 users/day",
    "storage": "product images, user data",
    "security": "authentication, payment encryption",
    "compute": "web application servers",
    "region": null,
    "database": "user data, products, orders",
    "networking": "CDN for images",
    "deployment_preferences": null
  },
  
  // Status
  "is_complete": false,
  "created_at": "2025-01-27T10:00:00Z",
  "last_updated": "2025-01-27T10:05:00Z"
}
```

---

## 🔄 Complete User Journey Examples

### **Example 1: AWS Query**

```
User: "What is AWS Lambda?"
     ↓
[RAG] Retrieves: "Lambda is serverless compute..."
     ↓
[LLM] Generates answer with context
     ↓
Response: "Lambda is serverless compute that runs code in response 
          to events with automatic scaling..."
     ↓
[No DB] AWS chat doesn't need persistence (stateless)
```

### **Example 2: Requirement Extraction (Multi-turn)**

```
Turn 1:
User: "I'm building a video sharing platform"
     ↓
[Extract] project_type: "video sharing platform"
[Missing] 8 fields
     ↓
Response: "I need more details. What's your expected user count?"

Turn 2:
User: "Around 10,000 users initially, growing to 100k"
     ↓
[Load from DB] Previous requirements
[Extract] scalability: "10k → 100k growth"
[Still Missing] 7 fields
     ↓
Response: "What region do you plan to deploy?"

Turn 3:
User: "US East, maybe global later"
     ↓
[Extract] region: "US East, global expansion"
[Still Missing] 6 fields
     ↓
Response: "Tell me about your storage needs..."

... (continues until all 9 fields filled)

Turn 7:
User: "Serverless preferred"
     ↓
[Extract] deployment_preferences: "serverless"
[Check] All 9 fields complete!
     ↓
Response: "✅ All requirements extracted!"
[Save] Complete JSON to MongoDB
```

---

## 🔧 Technical Stack

### **Frontend**
- **Framework**: Next.js 13 (React)
- **UI Library**: Material-UI (MUI)
- **State Management**: React useState (local state)
- **API Calls**: Fetch API

### **Backend**
- **Framework**: FastAPI (Python)
- **LLM**: Ollama (Llama 3.1:8b)
- **Embeddings**: Nomic Embed Text (via Ollama)
- **Vector Store**: FAISS (LangChain)
- **Database**: MongoDB (with pymongo/motor)
- **RAG**: LangChain retrieval chains

### **Infrastructure**
- **LLM Service**: Ollama (localhost:11434)
- **Backend API**: FastAPI (localhost:8000)
- **Frontend**: Next.js (localhost:3000)
- **Database**: MongoDB (localhost:27017)

---

## 🎯 Key Features

### ✅ **Separation of Concerns**
- Two completely separate modes
- Different chat histories
- Different UI components
- Different backend handlers

### ✅ **RAG Enhancement**
- AWS Chat: Full RAG with knowledge base
- Requirement Extraction: Optional RAG for patterns

### ✅ **Persistent Context**
- MongoDB stores all conversations
- Resume sessions after refresh
- Track extraction progress
- Maintain conversation history

### ✅ **Intelligent Extraction**
- Uses conversation history
- Merges with existing requirements
- Prioritizes missing fields
- Generates contextual follow-ups

### ✅ **Production-Ready**
- Error handling
- Fallback mechanisms
- Session management
- Progress tracking
- Structured JSON output

---

## 🚀 How Sessions Work

### **Session Creation**
```
User visits → Frontend generates session_id (UUID)
First message → Backend creates MongoDB document
Each message → Updates MongoDB document
```

### **Session Resumption**
```
User refreshes → Frontend sends session_id
Backend loads → MongoDB retrieves session
Continue chat → Seamless continuation
```

### **Session Separation**
```
AWS Chat Mode → session_id: "aws_chat_abc123"
Requirement Mode → session_id: "req_extract_xyz789"
Separate histories → No mixing between modes
```

---

## 📊 Data Flow Summary

```
┌──────────┐
│  User    │ ── Types message ──> ┌─────────┐
└──────────┘                       │Frontend │
                                   └────┬────┘
                                        │ POST /api/chat
                                        ↓
                                   ┌─────────┐
                                   │ FastAPI │
                                   └────┬────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ↓                   ↓                   ↓
              ┌──────────┐        ┌──────────┐       ┌──────────┐
              │   RAG    │        │   LLM    │       │ MongoDB  │
              │ Pipeline │        │ Ollama   │       │ Database │
              └────┬─────┘        └────┬─────┘       └────┬─────┘
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       │
                                       ↓
                                   ┌─────────┐
                                   │Response │
                                   └────┬────┘
                                        │ JSON
                                        ↓
                                   ┌─────────┐
                                   │Frontend │
                                   └────┬────┘
                                        │
                                        ↓
                                   ┌──────────┐
                                   │Display UI│
                                   └──────────┘
```

---

This architecture provides:
- ✅ Two distinct modes with clear separation
- ✅ RAG for AWS knowledge retrieval
- ✅ MongoDB persistence for sessions
- ✅ Intelligent requirement extraction
- ✅ Multi-turn conversations
- ✅ Production-grade error handling

Would you like me to proceed with implementing this complete system?

