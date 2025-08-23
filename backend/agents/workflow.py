"""
LangGraph Workflow for Agentic System.
Orchestrates the flow between Supervisor and specialized agents.
"""

import json
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import operator

from .supervisor_agent import SupervisorAgent
from .database_agent import DatabaseAgent
from .vector_db_agent import VectorDBAgent
from .general_agent import GeneralAgent
from .base_agent import AgentResponse
from models.database import db
from services.vector_service import VectorService


class WorkflowState(TypedDict):
    """State definition for the workflow."""
    query: str
    context: Dict[str, Any]
    supervisor_response: Optional[AgentResponse]
    routed_agent: Optional[str]
    final_response: Optional[AgentResponse]
    messages: Annotated[List[Dict[str, Any]], operator.add]
    error: Optional[str]


class AgenticWorkflow:
    """
    LangGraph-based workflow that orchestrates the agentic system.
    Routes queries through supervisor to appropriate specialized agents.
    """

    def __init__(self):
        """Initialize the workflow with all agents."""
        print("Initializing Agentic Workflow...")

        # Initialize all agents
        self.supervisor = SupervisorAgent()
        self.database_agent = DatabaseAgent()
        self.vector_db_agent = VectorDBAgent()
        self.general_agent = GeneralAgent()

        # Agent registry
        self.agents = {
            "database": self.database_agent,
            "vector_db": self.vector_db_agent,
            "general": self.general_agent
        }

        # Build the workflow graph
        self.workflow = self._build_workflow()
        print("Agentic Workflow initialized successfully!")

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""

        # Create the state graph
        workflow = StateGraph(WorkflowState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("database_agent", self._database_agent_node)
        workflow.add_node("vector_db_agent", self._vector_db_agent_node)
        workflow.add_node("general_agent", self._general_agent_node)
        workflow.add_node("finalize", self._finalize_node)

        # Define the routing logic
        def route_after_supervisor(state: WorkflowState) -> str:
            """Route to appropriate agent based on supervisor decision."""
            routed_agent = state.get("routed_agent")
            if routed_agent == "database":
                return "database_agent"
            elif routed_agent == "vector_db":
                return "vector_db_agent"
            elif routed_agent == "general":
                return "general_agent"
            else:
                # Fallback to general agent
                return "general_agent"

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            route_after_supervisor,
            {
                "database_agent": "database_agent",
                "vector_db_agent": "vector_db_agent",
                "general_agent": "general_agent"
            }
        )

        # All agents route to finalize
        workflow.add_edge("database_agent", "finalize")
        workflow.add_edge("vector_db_agent", "finalize")
        workflow.add_edge("general_agent", "finalize")

        # Finalize node ends the workflow
        workflow.add_edge("finalize", END)

        # Compile the workflow
        return workflow.compile()

    def _prepare_context(self, query: str) -> Dict[str, Any]:
        """Prepare context information for agents."""
        context = {
            "timestamp": "current",
            "user_query": query
        }

        # Get database information
        try:
            if db.is_connected():
               # Get table names and columns
               tables_query = """
               SELECT
                   t.table_name,
                   c.column_name,
                   c.data_type
               FROM
                   information_schema.tables t
               JOIN
                   information_schema.columns c
                   ON c.table_name = t.table_name
                   AND c.table_schema = t.table_schema
               WHERE
                   t.table_schema = 'public'
               ORDER BY
                   t.table_name, c.ordinal_position;
               """
               tables = db.execute_query(tables_query, fetch=True)
               if tables:
                   db_tables = {}
                   for row in tables:
                       table = row['table_name']
                       column = row['column_name']
                       dtype = row['data_type']
                       if table not in db_tables:
                           db_tables[table] = []
                       db_tables[table].append({'column_name': column, 'data_type': dtype})
                   context["db_tables"] = db_tables
               else:
                   context["db_tables"] = "No tables found"
            else:
               context["db_tables"] = "Database not connected"

        except Exception as e:
            context["db_tables"] = f"Database error: {str(e)}"

        # Get vector database information
        try:
            vector_service = VectorService()
            vector_info = vector_service.get_info()
            context["vector_db_status"] = f"{vector_info.get('total_documents', 0)} documents available" if vector_info.get('model_available', False) else "Vector DB not available"
        except Exception as e:
            context["vector_db_status"] = f"Vector DB error: {str(e)}"

        return context

    def _supervisor_node(self, state: WorkflowState) -> WorkflowState:
        """Supervisor node that routes the query."""
        try:
            query = state["query"]
            context = state["context"]
            print(f"Supervisor node context: {context}")

            print(f"Supervisor processing query: {query}")

            # Get routing decision from supervisor
            supervisor_response = self.supervisor.process_query(query, context)
            routed_agent = supervisor_response.metadata.get("routed_to", "general")

            print(f"Supervisor routed to: {routed_agent}")

            return {
                **state,
                "supervisor_response": supervisor_response,
                "routed_agent": routed_agent,
                "messages": [{"role": "supervisor", "content": f"Routing to {routed_agent} agent"}]
            }

        except Exception as e:
            print(f"Supervisor node error: {e}")
            return {
                **state,
                "routed_agent": "general",
                "error": f"Supervisor error: {str(e)}",
                "messages": [{"role": "supervisor", "content": f"Error in routing, defaulting to general agent: {str(e)}"}]
            }

    def _database_agent_node(self, state: WorkflowState) -> WorkflowState:
        """Database agent node."""
        try:
            query = state["query"]
            context = state["context"]

            print("Database agent processing query")

            response = self.database_agent.process_query(query, context)

            return {
                **state,
                "final_response": response,
                "messages": state["messages"] + [{"role": "database_agent", "content": "Database query processed"}]
            }

        except Exception as e:
            print(f"Database agent error: {e}")
            error_response = AgentResponse(
                agent_name="DatabaseAgent",
                content=f"I encountered an error while processing your database query: {str(e)}",
                confidence=0.0
            )
            return {
                **state,
                "final_response": error_response,
                "error": str(e),
                "messages": state["messages"] + [{"role": "database_agent", "content": f"Error: {str(e)}"}]
            }

    def _vector_db_agent_node(self, state: WorkflowState) -> WorkflowState:
        """Vector DB agent node."""
        try:
            query = state["query"]
            context = state["context"]

            print("Vector DB agent processing query")

            response = self.vector_db_agent.process_query(query, context)

            return {
                **state,
                "final_response": response,
                "messages": state["messages"] + [{"role": "vector_db_agent", "content": "Vector search completed"}]
            }

        except Exception as e:
            print(f"Vector DB agent error: {e}")
            error_response = AgentResponse(
                agent_name="VectorDBAgent",
                content=f"I encountered an error while searching documents: {str(e)}",
                confidence=0.0
            )
            return {
                **state,
                "final_response": error_response,
                "error": str(e),
                "messages": state["messages"] + [{"role": "vector_db_agent", "content": f"Error: {str(e)}"}]
            }

    def _general_agent_node(self, state: WorkflowState) -> WorkflowState:
        """General agent node."""
        try:
            query = state["query"]
            context = state["context"]

            print("General agent processing query")

            response = self.general_agent.process_query(query, context)

            return {
                **state,
                "final_response": response,
                "messages": state["messages"] + [{"role": "general_agent", "content": "General response generated"}]
            }

        except Exception as e:
            print(f"General agent error: {e}")
            error_response = AgentResponse(
                agent_name="GeneralAgent",
                content=f"I apologize, but I encountered an error: {str(e)}",
                confidence=0.0
            )
            return {
                **state,
                "final_response": error_response,
                "error": str(e),
                "messages": state["messages"] + [{"role": "general_agent", "content": f"Error: {str(e)}"}]
            }

    def _finalize_node(self, state: WorkflowState) -> WorkflowState:
        """Finalize the response."""
        print("Finalizing workflow response")

        final_response = state.get("final_response")
        if not final_response:
            # Fallback response
            final_response = AgentResponse(
                agent_name="WorkflowError",
                content="I apologize, but I couldn't process your request properly. Please try again.",
                confidence=0.0
            )

        return {
            **state,
            "final_response": final_response,
            "messages": state["messages"] + [{"role": "workflow", "content": "Workflow completed"}]
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query through the complete agentic workflow.

        Args:
            query: User query string

        Returns:
            Dictionary containing the response and metadata
        """
        try:
            print(f"Starting workflow for query: {query}")

            # Prepare context
            context = self._prepare_context(query)

            # Initial state
            initial_state = WorkflowState(
                query=query,
                context=context,
                supervisor_response=None,
                routed_agent=None,
                final_response=None,
                messages=[],
                error=None
            )

            # Run the workflow
            final_state = self.workflow.invoke(initial_state)

            # Extract results
            final_response = final_state.get("final_response")

            if final_response:
                result = {
                    "success": True,
                    "response": final_response.content,
                    "agent": final_response.agent_name,
                    "confidence": final_response.confidence,
                    "metadata": final_response.metadata,
                    "routed_to": final_state.get("routed_agent"),
                    "workflow_messages": final_state.get("messages", [])
                }
            else:
                result = {
                    "success": False,
                    "response": "I apologize, but I couldn't process your request.",
                    "agent": "WorkflowError",
                    "confidence": 0.0,
                    "error": final_state.get("error"),
                    "workflow_messages": final_state.get("messages", [])
                }

            print(f"Workflow completed. Agent: {result.get('agent')}, Success: {result.get('success')}")
            return result

        except Exception as e:
            print(f"Workflow error: {e}")
            return {
                "success": False,
                "response": f"I encountered an error while processing your request: {str(e)}",
                "agent": "WorkflowError",
                "confidence": 0.0,
                "error": str(e)
            }


# Global workflow instance
_workflow_instance = None


def get_workflow() -> AgenticWorkflow:
    """Get the global workflow instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = AgenticWorkflow()
    return _workflow_instance
