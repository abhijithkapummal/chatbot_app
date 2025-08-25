# Agentic Workflow Usage Examples

This document provides practical examples of how to use the LangGraph + LangChain agentic workflow system.

## 🚀 Quick Start

### 1. API Integration (Recommended)

The agentic workflow is now integrated into your existing Flask API. Simply make requests to the `/user/chat` endpoint:

```python
# POST to /user/chat
{
    "message": "How many users are in the system?"
}

# Response
{
    "success": true,
    "response": "Based on the database query, there are currently 5 users in the system.",
    "agent": "DatabaseAgent",
    "confidence": 0.8,
    "routed_to": "database",
    "metadata": {
        "sql_query": "SELECT COUNT(*) FROM users;",
        "raw_results": "{\"query\": \"SELECT COUNT(*) FROM users;\", \"row_count\": 1, \"data\": [{\"count\": 5}]}"
    }
}
```

### 2. Direct Python Usage

```python
from agents.workflow import get_workflow

# Initialize workflow
workflow = get_workflow()

# Process query
result = workflow.process_query("Hello, what can you do?")

print(f"Agent: {result['agent']}")
print(f"Response: {result['response']}")
```

## 📊 Query Examples by Agent Type

### Database Agent Queries

These queries will be routed to the **Database Agent** for SQL-based analysis:

```python
queries = [
    "How many users are registered?",
    "Show me the latest file uploads",
    "What's the total count of files in the system?",
    "List all users created in the last month",
    "Give me statistics about user registrations",
    "How many files were uploaded today?",
    "Show me all tables in the database",
    "What's the average file size uploaded?"
]

# Example API call
curl -X POST http://localhost:5000/user/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"message": "How many users are registered?"}'
```

**Expected Response:**

```json
{
  "success": true,
  "response": "According to the database, there are currently 3 registered users in the system.",
  "agent": "DatabaseAgent",
  "confidence": 0.8,
  "routed_to": "database",
  "metadata": {
    "sql_query": "SELECT COUNT(*) FROM users;",
    "schema_used": "users table with columns: id, username, email, password_hash, user_type, created_at"
  }
}
```

### Vector DB Agent Queries

These queries will be routed to the **Vector DB Agent** for document search:

```python
queries = [
    "What does the uploaded document say about sales?",
    "Find information about TCS in the documents",
    "Tell me about the business data mentioned in files",
    "Search for financial information in uploaded documents",
    "What content is available about quarterly reports?",
    "Explain the data trends mentioned in the files"
]

# Example API call
curl -X POST http://localhost:5000/user/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"message": "What does the document say about TCS?"}'
```

**Expected Response:**

```json
{
  "success": true,
  "response": "Based on the uploaded documents, TCS (Tata Consultancy Services) is mentioned in the context of technology services and consulting. The document indicates that TCS has been involved in digital transformation projects and has shown consistent growth in the IT sector.",
  "agent": "VectorDBAgent",
  "confidence": 0.75,
  "routed_to": "vector_db",
  "metadata": {
    "sources": ["tcs.txt", "business-financial-data.csv"],
    "reformulated_query": "TCS Tata Consultancy Services technology consulting digital transformation",
    "search_results": "3 relevant chunks found"
  }
}
```

### General Agent Queries

These queries will be routed to the **General Agent** for conversation:

```python
queries = [
    "Hello",
    "Hi there!",
    "What can you do?",
    "Help me understand your capabilities",
    "Tell me about yourself",
    "Good morning",
    "Thank you",
    "What features do you have?"
]

# Example API call
curl -X POST http://localhost:5000/user/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"message": "Hello, what can you do?"}'
```

**Expected Response:**

```json
{
  "success": true,
  "response": "Hello! I'm your AI assistant with specialized capabilities:\n\n• **Database Analysis**: I can query and analyze your structured data\n• **Document Search**: I can search through uploaded files and documents\n• **General Help**: I can answer questions and have conversations\n\nWhat would you like me to help you with today?",
  "agent": "GeneralAgent",
  "confidence": 0.95,
  "routed_to": "general"
}
```

## 🔄 Workflow Execution Flow

Here's what happens when you send a query:

1. **Query Received**: Your message hits the `/user/chat` endpoint
2. **Context Preparation**: System gathers database and vector DB status
3. **Supervisor Analysis**: LLM analyzes the query and decides routing
4. **Agent Processing**: Specialized agent uses its tools to process the query
5. **Response Generation**: Agent formulates a natural language response
6. **Metadata Packaging**: System packages response with confidence and metadata

## 🛠️ Testing the System

### Run the Test Suite

```bash
cd backend
python test_agentic_workflow.py
```

This will run comprehensive tests covering all agent types and routing scenarios.

### Manual Testing via API

1. **Start the Flask server**:

```bash
cd backend
python app.py
```

2. **Authenticate** (get JWT token from `/auth/login`)

3. **Test different query types**:

```bash
# Database query
curl -X POST http://localhost:5000/user/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "How many files are uploaded?"}'

# Document query
curl -X POST http://localhost:5000/user/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "What information is in the uploaded documents?"}'

# General query
curl -X POST http://localhost:5000/user/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Hello, how are you?"}'
```

## 🎯 Expected Routing Behavior

| Query Type   | Example                       | Expected Agent | Confidence |
| ------------ | ----------------------------- | -------------- | ---------- |
| Data/Stats   | "How many users?"             | DatabaseAgent  | 0.8-0.9    |
| Documents    | "What does file say about X?" | VectorDBAgent  | 0.7-0.9    |
| Greetings    | "Hello", "Hi"                 | GeneralAgent   | 0.9-0.95   |
| Capabilities | "What can you do?"            | GeneralAgent   | 0.8-0.9    |
| Ambiguous    | "Show me information"         | Any agent      | 0.5-0.7    |

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Failed**

   - Check `DATABASE_URL` in environment variables
   - Ensure PostgreSQL is running
   - Verify credentials

2. **Vector DB Not Available**

   - Check if documents have been uploaded
   - Verify sentence-transformers model is downloaded
   - Check FAISS index files exist

3. **LLM Service Unavailable**

   - Verify `GROQ_API_KEY` is set
   - Check internet connection
   - System will fallback to basic responses

4. **Routing Issues**
   - Queries might be ambiguous
   - Check supervisor routing logic
   - Review agent confidence scores

### Debug Information

The system provides extensive metadata for debugging:

```json
{
  "metadata": {
    "sql_query": "Generated SQL",
    "sources": ["document1.txt"],
    "reformulated_query": "Optimized search query",
    "raw_results": "Detailed results",
    "workflow_messages": ["Step-by-step execution log"]
  }
}
```

## 🔮 Future Enhancements

The system is designed to be easily extensible:

1. **New Agents**: Add specialized agents for specific domains
2. **Additional Tools**: Extend agent capabilities with new tools
3. **Custom Routing**: Implement domain-specific routing logic
4. **Multi-step Workflows**: Chain multiple agents for complex queries
5. **Memory Integration**: Add conversation history and context memory

## 📝 API Documentation

### Main Chat Endpoint

**POST** `/user/chat`

**Headers:**

- `Authorization: Bearer <jwt_token>`
- `Content-Type: application/json`

**Request Body:**

```json
{
  "message": "Your query here"
}
```

**Response:**

```json
{
    "success": boolean,
    "response": "Natural language response",
    "agent": "Agent that processed the query",
    "confidence": float (0.0-1.0),
    "routed_to": "Agent routing decision",
    "metadata": {
        "agent_specific_data": "varies by agent"
    }
}
```

### Legacy Endpoint

**POST** `/user/chat/legacy`

Maintains backward compatibility with the original simple chat system.

---

🎉 **Congratulations!** You now have a fully functional LangGraph + LangChain agentic workflow system that intelligently routes queries to specialized agents based on their capabilities and the available data sources.
