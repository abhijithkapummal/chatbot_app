"""
Vector DB Agent - Handles queries requiring semantic search in vector database.
"""

import json
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from .base_agent import BaseAgent, AgentResponse
from services.vector_service import VectorService


class VectorDBAgent(BaseAgent):
    """
    Vector DB Agent that performs semantic search on uploaded documents
    and provides RAG-based responses.
    """

    def __init__(self):
        super().__init__("VectorDBAgent")
        self.vector_service = VectorService()
        self._setup_tools()

    def _setup_tools(self):
        """Setup LangChain tools for vector database operations."""
        self.tools = [
            Tool(
                name="semantic_search",
                description="Perform semantic search in the vector database to find relevant document chunks",
                func=self._semantic_search
            ),
            Tool(
                name="get_vector_db_info",
                description="Get information about the vector database (number of documents, status)",
                func=self._get_vector_db_info
            ),
            Tool(
                name="reformulate_query",
                description="Reformulate user query for better semantic search results",
                func=self._reformulate_query
            )
        ]

    def get_prompt_template(self) -> ChatPromptTemplate:
        """Return the vector search prompt template."""
        return ChatPromptTemplate.from_template("""
You are a Vector DB Agent specialized in finding and presenting information from uploaded documents.

Your process:
1. First, check the vector database status and available documents
2. Reformulate the user query for optimal semantic search if needed
3. Perform semantic search to find relevant document chunks
4. Analyze the retrieved context and generate a comprehensive response
5. Cite sources and explain the confidence in your answer

Available tools:
- get_vector_db_info: Check vector database status and document count
- reformulate_query: Improve query for better semantic search
- semantic_search: Find relevant document chunks

User Query: "{query}"

Context: {context}

Instructions:
- Always check vector database status first
- Use semantic search to find the most relevant information
- Provide detailed answers based on the retrieved context
- If no relevant information is found, clearly state this
- Always cite the source documents when providing information
- Explain your confidence level in the answer

Begin by checking the vector database status.
""")

    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this query requires vector database search.
        Returns confidence score based on query analysis.
        """
        # Keywords that suggest document/content queries
        doc_keywords = [
            'document', 'file', 'uploaded', 'content', 'text',
            'what does', 'according to', 'in the document',
            'find information', 'tell me about', 'explain',
            'describe', 'details about', 'information on'
        ]

        query_lower = query.lower()

        # Check for document-related keywords
        keyword_matches = sum(1 for keyword in doc_keywords if keyword in query_lower)

        # Check if vector database has content
        vector_info = self.vector_service.get_info()
        has_documents = vector_info.get('total_documents', 0) > 0

        if keyword_matches >= 1 and has_documents:
            return 0.9
        elif has_documents and any(word in query_lower for word in ['what', 'how', 'why', 'when', 'where']):
            return 0.7
        elif keyword_matches >= 1:
            return 0.5
        else:
            return 0.2

    def _get_vector_db_info(self) -> str:
        """Get vector database status and information."""
        try:
            info = self.vector_service.get_info()
            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Error getting vector database info: {str(e)}"

    def _reformulate_query(self, query: str) -> str:
        """Reformulate query for better semantic search results."""
        try:
            if not self.llm_available:
                return query  # Return original query if LLM unavailable

            reformulation_prompt = f"""
Reformulate the following user query to make it more effective for semantic search in a document database.

Original query: "{query}"

Rules for reformulation:
1. Extract key concepts and terms
2. Make the query more specific and searchable
3. Add relevant synonyms or alternative phrasings
4. Keep it concise but comprehensive
5. Focus on the main information need

Reformulated query:
"""

            reformulated = self._invoke_llm(reformulation_prompt).strip()
            return reformulated if reformulated else query

        except Exception as e:
            print(f"Error reformulating query: {e}")
            return query

    def _semantic_search(self, query: str, top_k: int = 5) -> str:
        """Perform semantic search and return formatted results."""
        try:
            # Get vector database info first
            info = self.vector_service.get_info()
            if not info.get('model_available', False):
                return "Vector search model is not available"

            if info.get('total_documents', 0) == 0:
                return "No documents found in vector database"

            # Perform search
            results = self.vector_service.search(query, top_k=top_k)

            if not results:
                return "No relevant documents found for the query"

            # Format results
            formatted_results = {
                "query": query,
                "results_count": len(results),
                "results": []
            }

            for i, result in enumerate(results):
                formatted_result = {
                    "rank": i + 1,
                    "content": result.get('content', 'No content'),
                    "score": result.get('score', 0.0),
                    "metadata": {
                        "filename": result.get('filename', 'Unknown'),
                        "chunk_id": result.get('chunk_id', 'Unknown')
                    }
                }
                formatted_results["results"].append(formatted_result)

            return json.dumps(formatted_results, indent=2)

        except Exception as e:
            return f"Error performing semantic search: {str(e)}"

    def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Process vector database query using semantic search and RAG.
        """
        try:
            if not self.llm_available:
                return AgentResponse(
                    agent_name=self.agent_name,
                    content="Vector DB Agent is currently unavailable due to LLM service issues.",
                    confidence=0.0
                )

            # Step 1: Check vector database status
            vector_info = self._get_vector_db_info()
            vector_data = json.loads(vector_info)

            if not vector_data.get('model_available', False):
                return AgentResponse(
                    agent_name=self.agent_name,
                    content="The vector search model is not available. Please ensure the sentence transformer model is properly initialized.",
                    confidence=0.0
                )

            if vector_data.get('total_documents', 0) == 0:
                return AgentResponse(
                    agent_name=self.agent_name,
                    content="No documents have been uploaded to the vector database yet. Please upload some documents first.",
                    confidence=0.0
                )

            # Step 2: Reformulate query for better search
            reformulated_query = self._reformulate_query(query)

            # Step 3: Perform semantic search
            search_results = self._semantic_search(reformulated_query, top_k=5)

            # Step 4: Generate RAG response
            rag_prompt = f"""
The user asked: "{query}"

The reformulated search query was: "{reformulated_query}"

Here are the relevant document chunks found:
{search_results}

Vector Database Info:
{vector_info}

Please provide a comprehensive answer to the user's question based on the retrieved document chunks.

Instructions:
1. Use the information from the document chunks to answer the question
2. If the chunks don't contain enough information, state this clearly
3. Cite the source documents (filenames) when providing information
4. Be specific about which parts of your answer come from which documents
5. If there are conflicting information in different chunks, mention this
6. Provide a confidence assessment of your answer

Format your response naturally and helpfully.
"""

            rag_response = self._invoke_llm(rag_prompt)

            # Parse search results for metadata
            try:
                search_data = json.loads(search_results)
                sources = [result['metadata']['filename'] for result in search_data.get('results', [])]
                confidence = max([result['score'] for result in search_data.get('results', [])], default=0.0)
            except:
                sources = []
                confidence = 0.5

            return AgentResponse(
                agent_name=self.agent_name,
                content=rag_response,
                metadata={
                    "original_query": query,
                    "reformulated_query": reformulated_query,
                    "sources": sources,
                    "search_results": search_results,
                    "vector_db_status": vector_info
                },
                confidence=min(confidence, 0.9)
            )

        except Exception as e:
            return AgentResponse(
                agent_name=self.agent_name,
                content=f"I encountered an error while searching the document database: {str(e)}",
                metadata={"error": str(e)},
                confidence=0.0
            )
