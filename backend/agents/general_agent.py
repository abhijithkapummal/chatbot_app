"""
General Agent - Handles casual conversation and non-contextual queries.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from .base_agent import BaseAgent, AgentResponse


class GeneralAgent(BaseAgent):
    """
    General Agent that handles greetings, small talk, and general questions
    that don't require database or document search.
    """

    def __init__(self):
        super().__init__("GeneralAgent")

    def get_prompt_template(self) -> ChatPromptTemplate:
        """Return the general conversation prompt template."""
        return ChatPromptTemplate.from_template("""
You are a helpful AI assistant for a chatbot application. You handle general conversation,
greetings, and questions that don't require specific data lookup.

Your personality:
- Friendly and professional
- Helpful and informative
- Concise but warm in responses
- Knowledgeable about general topics

Your capabilities:
- Answer general questions
- Provide helpful information
- Engage in casual conversation
- Explain what the chatbot system can do

Available specialized services (mention when relevant):
- Database queries for structured data analysis
- Document search for information from uploaded files
- File upload and processing capabilities

User Query: "{query}"

Context: {context}

Instructions:
- Provide helpful, natural responses
- If asked about your capabilities, mention the specialized agents
- For data or document questions, suggest using the appropriate features
- Keep responses conversational and engaging
- Don't make up specific data or facts

Respond naturally and helpfully:
""")

    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this is a general/casual query.
        Returns confidence score based on query analysis.
        """
        # Common greeting and casual conversation patterns
        general_patterns = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'how are you', 'what\'s up', 'greetings',
            'thank you', 'thanks', 'goodbye', 'bye', 'see you',
            'what can you do', 'help me', 'what are your capabilities',
            'who are you', 'what are you', 'tell me about yourself',
            'joke', 'story', 'weather', 'time', 'date'
        ]

        query_lower = query.lower().strip()

        # Exact matches for greetings
        if query_lower in ['hi', 'hello', 'hey', 'help', 'start']:
            return 0.95

        # Check for general conversation patterns
        for pattern in general_patterns:
            if pattern in query_lower:
                return 0.8

        # Questions about capabilities or general help
        if any(word in query_lower for word in ['what can', 'how to', 'help with', 'capabilities']):
            return 0.7

        # Very short queries are often general
        if len(query.split()) <= 2 and not any(char.isdigit() for char in query):
            return 0.6

        # Default for anything else
        return 0.3

    def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Process general conversation queries.
        """
        try:
            # Handle common greetings with predefined responses for better performance
            query_lower = query.lower().strip()

            predefined_responses = {
                'hi': "Hello! I'm your AI assistant. I can help you with data queries, document searches, and general questions. What would you like to know?",
                'hello': "Hi there! I'm here to help you with your questions. I can search through your data, uploaded documents, or just have a conversation. How can I assist you today?",
                'hey': "Hey! Nice to meet you. I'm an AI assistant that can help with database queries, document searches, and general assistance. What can I do for you?",
                'help': "I'm here to help! I can assist you with:\n• Database queries and data analysis\n• Searching through uploaded documents\n• General questions and conversation\n\nWhat would you like to explore?",
                'what can you do': "I have several capabilities:\n• **Database Agent**: Query and analyze structured data\n• **Document Search**: Find information in uploaded files\n• **General Assistant**: Help with various questions and conversations\n\nWhat type of assistance do you need?",
                'capabilities': "My main capabilities include:\n1. **Data Analysis**: I can query databases and provide insights\n2. **Document Search**: I can search through uploaded files and documents\n3. **General Help**: I can answer questions and have conversations\n\nHow would you like me to help you today?"
            }

            if query_lower in predefined_responses:
                return AgentResponse(
                    agent_name=self.agent_name,
                    content=predefined_responses[query_lower],
                    confidence=0.95
                )

            # For other queries, use LLM if available
            if self.llm_available:
                prompt_template = self.get_prompt_template()
                formatted_prompt = self._create_prompt(
                    prompt_template,
                    query=query,
                    context=context or {}
                )

                response_content = self._invoke_llm(formatted_prompt)
                confidence = 0.8
            else:
                # Fallback response when LLM is unavailable
                response_content = f"Thank you for your message: '{query}'. I'm here to help, though my AI capabilities are currently limited. I can still assist you with basic responses and information about the system's features."
                confidence = 0.5

            return AgentResponse(
                agent_name=self.agent_name,
                content=response_content,
                confidence=confidence
            )

        except Exception as e:
            return AgentResponse(
                agent_name=self.agent_name,
                content="I apologize, but I encountered an error while processing your request. Please try again or rephrase your question.",
                metadata={"error": str(e)},
                confidence=0.0
            )
