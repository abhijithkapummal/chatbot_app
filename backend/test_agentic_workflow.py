#!/usr/bin/env python3
"""
Test script for the Agentic Workflow System.
Demonstrates how different types of queries are routed to appropriate agents.
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from agents.workflow import get_workflow
from models.database import init_db


def test_query(query: str, expected_agent: str = None):
    """Test a single query and display results."""
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    try:
        workflow = get_workflow()
        result = workflow.process_query(query)

        print(f"Success: {result.get('success')}")
        print(f"Agent: {result.get('agent')}")
        print(f"Routed to: {result.get('routed_to')}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"\nResponse:")
        print(result.get('response', 'No response'))

        if result.get('metadata'):
            print(f"\nMetadata:")
            metadata = result.get('metadata', {})
            for key, value in metadata.items():
                if key == 'sources' and isinstance(value, list):
                    print(f"  {key}: {', '.join(value) if value else 'None'}")
                elif key in ['sql_query', 'reformulated_query']:
                    print(f"  {key}: {value}")
                elif key == 'raw_results':
                    print(f"  {key}: [Results truncated for display]")
                else:
                    print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")

        if expected_agent and result.get('routed_to') != expected_agent:
            print(f"\n⚠️  ROUTING MISMATCH: Expected {expected_agent}, got {result.get('routed_to')}")
        elif expected_agent:
            print(f"\n✅ ROUTING CORRECT: {expected_agent}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


def main():
    """Run comprehensive tests of the agentic workflow."""

    print("🚀 Starting Agentic Workflow Tests")
    print("=" * 60)

    # Initialize database
    print("Initializing database...")
    init_db()

    # Test cases grouped by expected agent
    test_cases = [
        # General Agent Tests
        ("Hello", "general"),
        ("Hi there!", "general"),
        ("What can you do?", "general"),
        ("Tell me about yourself", "general"),
        ("Help me", "general"),

        # Database Agent Tests
        ("How many users are in the system?", "database"),
        ("Show me all users", "database"),
        ("What's the total count of file uploads?", "database"),
        ("List all tables in the database", "database"),
        ("Give me statistics about user registrations", "database"),
        ("How many files were uploaded recently?", "database"),

        # Vector DB Agent Tests
        ("What does the uploaded document say about sales?", "vector_db"),
        ("Find information about TCS in the documents", "vector_db"),
        ("Tell me about the content in the uploaded files", "vector_db"),
        ("Search for information about business data", "vector_db"),
        ("What information is available in the documents?", "vector_db"),

        # Edge Cases / Ambiguous Queries
        ("data analysis", None),  # Could go to either database or vector_db
        ("show me information", None),  # Could go to either agent
        ("help with files", None),  # Could be vector_db or general
    ]

    # Run all test cases
    for i, (query, expected_agent) in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}/{len(test_cases)}")
        test_query(query, expected_agent)

    # Summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total test cases: {len(test_cases)}")
    print("Tests completed. Review the routing decisions above.")
    print("\nKey things to verify:")
    print("1. ✅ General queries route to GeneralAgent")
    print("2. ✅ Data/count queries route to DatabaseAgent")
    print("3. ✅ Document/file queries route to VectorDBAgent")
    print("4. ✅ Responses are appropriate for each agent type")
    print("5. ✅ Error handling works gracefully")


if __name__ == "__main__":
    main()
