# LangGraph + LangChain Agentic Workflow System

This document explains the implementation of a sophisticated agentic workflow system that uses LangGraph and LangChain to intelligently route user queries to specialized agents.

## System Architecture

The system consists of four main components:

### 1. **Supervisor Agent (Router)**

- **Role**: Central decision-maker that analyzes incoming queries and routes them to appropriate agents
- **Technology**: Uses Groq LLM for intelligent routing decisions
- **Capabilities**:
  - Analyzes query intent and context
  - Inspects available data sources (database tables, vector DB status)
  - Routes to Database, Vector DB, or General agents

### 2. **Database Agent**

- **Role**: Handles queries requiring structured data analysis
- **Technology**: Dynamic SQL generation and execution with PostgreSQL
- **Capabilities**:
  - Dynamically inspects database schema (tables and columns)
  - Generates safe, optimized SQL queries
  - Executes queries and formats results
  - Provides natural language responses with data insights

### 3. **Vector DB Agent**

- **Role**: Handles queries about uploaded document content
- **Technology**: Semantic search with FAISS and sentence transformers
- **Capabilities**:
  - Reformulates queries for better semantic search
  - Retrieves relevant document chunks
  - Implements Retrieval-Augmented Generation (RAG)
  - Cites sources and provides confidence scores

### 4. **General Agent**

- **Role**: Handles casual conversation and non-contextual queries
- **Technology**: LLM-based conversation with predefined responses for common patterns
- **Capabilities**:
  - Greetings and small talk
  - System capability explanations
  - General assistance and guidance

## LangGraph Workflow

The workflow is implemented using LangGraph's state-based execution model:

```
User Query → Supervisor → Route Decision → Specialized Agent → Final Response
```

### Workflow State

```python
class WorkflowState(TypedDict):
    query: str                              # Original user query
    context: Dict[str, Any]                 # System context (DB info, vector status)
    supervisor_response: AgentResponse      # Supervisor routing decision
    routed_agent: str                       # Selected agent name
    final_response: AgentResponse           # Final agent response
    messages: List[Dict[str, Any]]          # Workflow execution log
    error: Optional[str]                    # Error information if any
```

### Execution Flow

1. **Context Preparation**: System gathers metadata about available data sources
2. **Supervisor Analysis**: LLM analyzes query and determines appropriate agent
3. **Agent Processing**: Specialized agent processes the query using its tools
4. **Response Finalization**: Workflow packages the response with metadata

## Prompt Templates

### Supervisor Agent Prompt

The supervisor uses a comprehensive prompt that includes:

- Available agent descriptions and capabilities
- Current database table information
- Vector database status
- Query analysis guidelines

### Database Agent Prompt

Features a multi-step process:

- Database schema inspection
- SQL query generation rules
- Safety constraints (SELECT only)
- Error handling guidelines

### Vector DB Agent Prompt

Implements RAG methodology:

- Query reformulation for semantic search
- Document chunk retrieval and ranking
- Source citation requirements
- Confidence assessment

### General Agent Prompt

Focuses on conversation:

- Personality guidelines (friendly, professional)
- Capability explanations
- Routing suggestions for specialized queries

## Tools and Capabilities

### Database Agent Tools

- `inspect_database_schema`: Get table and column information
- `validate_sql_query`: Check query safety and syntax
- `execute_sql_query`: Run queries and format results

### Vector DB Agent Tools

- `get_vector_db_info`: Check database status and document count
- `reformulate_query`: Optimize queries for semantic search
- `semantic_search`: Find relevant document chunks

## Dynamic Query Processing

### Database Queries

1. **Schema Inspection**: Automatically discovers available tables and columns
2. **Query Generation**: LLM generates SQL based on schema and user intent
3. **Safety Validation**: Ensures only SELECT operations are performed
4. **Result Formatting**: Converts SQL results to natural language

### Vector Queries

1. **Status Check**: Verifies vector database and model availability
2. **Query Reformulation**: Optimizes search terms for better retrieval
3. **Semantic Search**: Uses FAISS for similarity matching
4. **RAG Response**: Combines retrieved context with LLM generation

## Usage Examples

### Database Query

```
User: "How many users are in the system?"
→ Supervisor routes to Database Agent
→ Database Agent inspects schema, finds 'users' table
→ Generates: SELECT COUNT(*) FROM users;
→ Executes query and returns natural language result
```

### Document Query

```
User: "What does the uploaded document say about sales?"
→ Supervisor routes to Vector DB Agent
→ Vector Agent reformulates to "sales revenue performance metrics"
→ Performs semantic search in embedded documents
→ Returns RAG response with source citations
```

### General Query

```
User: "Hello, what can you do?"
→ Supervisor routes to General Agent
→ General Agent provides capability overview
→ Suggests how to use database and document features
```

## Configuration

### Environment Variables

```
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### Dependencies

- LangChain >= 0.1.20
- LangGraph >= 0.0.51
- LangChain-Groq >= 0.1.5
- PostgreSQL with psycopg2
- FAISS for vector search
- Sentence Transformers

## Error Handling

The system implements comprehensive error handling:

1. **Agent Fallbacks**: If primary agent fails, system defaults to General Agent
2. **LLM Unavailability**: Graceful degradation with predefined responses
3. **Database Errors**: Clear error messages and retry logic
4. **Vector Search Issues**: Fallback to general responses when embeddings unavailable

## Performance Considerations

- **Lazy Loading**: Agents initialize only when needed
- **Connection Pooling**: Database connections are reused
- **Caching**: Vector models loaded once and shared
- **Timeout Handling**: Requests have appropriate timeouts

## Security Features

- **SQL Injection Prevention**: Parameterized queries only
- **Query Restrictions**: Only SELECT operations allowed
- **Input Validation**: All user inputs are sanitized
- **Authentication**: JWT-based user authentication required

## Extensibility

The system is designed for easy extension:

1. **New Agents**: Inherit from `BaseAgent` class
2. **Additional Tools**: Add to agent tool registries
3. **Custom Routing**: Modify supervisor routing logic
4. **New Data Sources**: Extend context preparation

## Monitoring and Debugging

- **Workflow Logging**: Each step logs execution details
- **Confidence Scores**: All responses include confidence metrics
- **Metadata Tracking**: Rich metadata for debugging and analysis
- **Error Propagation**: Clear error messages throughout the stack
