"""
Base Agent class for the agentic workflow system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from config import Config
import os


class AgentResponse(BaseModel):
    """Standard response format for all agents."""
    agent_name: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    requires_followup: bool = False


class BaseAgent(ABC):
    """Base class for all agents in the workflow."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

        # Initialize Groq LLM
        try:
            # Clear proxy settings that might interfere
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]

            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=Config.GROQ_API_KEY,
                temperature=0.1,
                max_tokens=2048
            )
            self.llm_available = True
            print(f"{agent_name} - Groq LLM initialized successfully")
        except Exception as e:
            print(f"{agent_name} - Warning: Could not initialize Groq LLM: {e}")
            self.llm = None
            self.llm_available = False

    @abstractmethod
    def get_prompt_template(self) -> ChatPromptTemplate:
        """Return the prompt template for this agent."""
        pass

    @abstractmethod
    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this agent can handle the given query.
        Returns confidence score (0.0 to 1.0).
        """
        pass

    @abstractmethod
    def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Process the query and return a response.
        """
        pass

    def _invoke_llm(self, prompt: str, **kwargs) -> str:
        """Helper method to invoke the LLM with error handling."""
        if not self.llm_available or not self.llm:
            return f"I apologize, but the AI service is currently unavailable for {self.agent_name}."

        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"{self.agent_name} - LLM invocation error: {e}")
            return f"I encountered an error while processing your request with {self.agent_name}. Please try again."

    def _create_prompt(self, template: ChatPromptTemplate, **variables) -> str:
        """Helper method to create formatted prompt from template."""
        try:
            formatted_prompt = template.format(**variables)
            return formatted_prompt
        except Exception as e:
            print(f"{self.agent_name} - Prompt formatting error: {e}")
            return f"Error formatting prompt for {self.agent_name}"
