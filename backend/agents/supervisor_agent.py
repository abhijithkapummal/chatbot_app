"""
Supervisor Agent - Routes queries to appropriate specialized agents.
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseAgent, AgentResponse


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent that analyzes queries and routes them to appropriate agents.
    Acts as the central decision-maker in the agentic workflow.
    """

    def __init__(self):
        super().__init__("SupervisorAgent")
        self.available_agents = ["database", "vector_db", "general"]

    def get_prompt_template(self) -> ChatPromptTemplate:
        """Return the routing prompt template."""
        return ChatPromptTemplate.from_template("""
You are a Supervisor Agent responsible for routing user queries to the most appropriate specialized agent.

Available agents and their capabilities:

1. **database** - Handles queries that can be answered using structured data from PostgreSQL tables:
   - Questions about data, statistics, reports, counts, aggregations
   - Queries that might require SQL operations (SELECT, JOIN, WHERE, GROUP BY, etc.)
   - Examples: "How many users?", "Show sales data", "What's the average age?"

2. **vector_db** - Handles queries about information stored in uploaded files/documents:
   - Questions about content from uploaded files (PDFs, text files, documents)
   - Information retrieval from embedded document chunks
   - Examples: "What does the document say about X?", "Find information about Y"

3. **general** - Handles casual conversation and non-contextual queries:
   - Greetings, small talk, general questions
   - Queries not related to specific data or documents
   - Examples: "Hello", "How are you?", "Tell me a joke", "What can you do?"

Context about available data sources:
- Database tables: {db_tables}
- Vector database status: {vector_db_status}

Vector Database Search Results:
- Found {search_results_count} relevant documents (similarity ≥ 0.7)
- Relevant content preview: {relevant_content_preview}

User Query: "{query}"

Analyze the query and determine which agent should handle it. Consider:
1. Does it require structured data analysis? → database
2. Does it ask about uploaded document content or does the vector search show relevant results? → vector_db
3. Is it general conversation or non-specific? → general

IMPORTANT: If the vector database search found relevant content (search_results_count > 0), strongly consider routing to vector_db unless the query clearly requires database operations.

Respond with ONLY the agent name: database, vector_db, or general
""")

    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """Supervisor always handles routing, so always returns 1.0."""
        return 1.0

    def route_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Route the query to the appropriate agent.
        Returns the name of the agent that should handle the query.
        """
        if not context:
            context = {}

        # Get database table information
        db_tables = context.get('db_tables', 'No database connection')
        vector_db_status = context.get('vector_db_status', 'No vector database available')

        # Get vector search results
        vector_search_results = context.get('vector_search_results', {})

        search_results_count = vector_search_results.get('search_results_count', 0)
        relevant_content = vector_search_results.get('relevant_content', [])

        # Create relevant content preview for the prompt
        relevant_content_preview = "None"
        if relevant_content:
            content_previews = []
            for i, result in enumerate(relevant_content[:2], 1):  # Show first 2 results
                content_preview = result.get('content', '')[:150] + '...' if len(result.get('content', '')) > 150 else result.get('content', '')
                similarity_score = result.get('similarity_score', 0)
                content_previews.append(f"{i}. (Score: {similarity_score:.2f}) {content_preview}")
            relevant_content_preview = "\n".join(content_previews)

        prompt_template = self.get_prompt_template()
        prompt = self._create_prompt(
            prompt_template,
            query=query,
            db_tables=db_tables,
            vector_db_status=vector_db_status,
            search_results_count=search_results_count,
            relevant_content_preview=relevant_content_preview
        )

        response = self._invoke_llm(prompt)

        # Extract agent name from response
        agent_name = response.strip().lower()

        # Validate and default to general if invalid
        if agent_name not in self.available_agents:
            print(f"Supervisor - Invalid agent routing: {agent_name}, defaulting to general")
            agent_name = "general"

        print(f"Supervisor - Routing query to: {agent_name} (Vector results: {search_results_count})")
        return agent_name

    def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Process query by routing to appropriate agent.
        This method is called by the workflow to get routing decision.
        """
        routed_agent = self.route_query(query, context)

        return AgentResponse(
            agent_name=self.agent_name,
            content=routed_agent,
            metadata={
                "routed_to": routed_agent,
                "routing_confidence": 0.9
            },
            confidence=0.9,
            requires_followup=True
        )
