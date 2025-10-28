# 🗄️ MongoDB Setup Guide

## Step 1: Get MongoDB Atlas Connection String

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up or log in
3. Create a new cluster (Free tier is fine)
4. Click "Connect" → "Connect your application"
5. Copy the connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)

## Step 2: Set Environment Variable

Create or update `.env.local` file in the project root:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=aws_chatbot

# Ollama Configuration (existing)
OLLAMA_BASE_URL=http://localhost:11434
LLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
```

**Important:** Replace `username`, `password`, and `cluster` with your actual MongoDB Atlas credentials.

## Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r api/requirements.txt

# Frontend dependencies are already installed
```

## Step 4: Run the Application

```bash
# Terminal 1: Start FastAPI backend
cd api
python -m uvicorn index:app --reload --port 8000

# Terminal 2: Start Next.js frontend
npm run dev
```

## Step 5: Verify MongoDB Connection

Visit: `http://localhost:8000/api/health`

You should see:
```json
{
  "status": "healthy",
  "message": "AWS Cloud Assistant is running",
  "mongodb": "connected"
}
```

## Troubleshooting

### MongoDB Connection Failed
- Check your connection string in `.env.local`
- Make sure MongoDB Atlas allows connections from your IP (0.0.0.0/0 for testing)
- Verify network access in MongoDB Atlas dashboard

### Application Works Without MongoDB
- The app will work in "stateless mode" if MongoDB is unavailable
- Session persistence won't work, but basic functionality remains
- Check backend logs for MongoDB connection warnings

## Testing

### Test Requirement Extraction with Persistence:
1. Open the app
2. Switch to "Requirement Extraction" mode
3. Start describing your project
4. Refresh the page - your session should persist!
5. Check MongoDB Atlas → Collections → `sessions` to see stored data

### Test AWS Chat Mode:
1. Switch to "AWS Chat" mode
2. Ask: "What is AWS Lambda?"
3. Verify RAG response with AWS knowledge base

## Database Schema

Sessions are stored in MongoDB with this structure:

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "unique-session-id",
  "mode": "requirement_extraction" | "aws_chat",
  "chat_history": [
    {
      "timestamp": "2025-01-27T10:00:00Z",
      "sender": "User" | "AI",
      "message": "...",
      "response_type": "..."
    }
  ],
  "extracted_requirements": {
    "project_type": "...",
    "scalability": "...",
    // ... 9 fields total
  },
  "is_complete": false,
  "created_at": "2025-01-27T10:00:00Z",
  "last_updated": "2025-01-27T10:05:00Z"
}
```

## Next Steps

Once MongoDB is connected:
- ✅ Sessions persist across page refreshes
- ✅ Requirement extraction progress is saved
- ✅ Chat history is stored in database
- ✅ Multiple users can have separate sessions

Ready to test! 🚀

