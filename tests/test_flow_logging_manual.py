#!/usr/bin/env python
"""
Manual test script for unified flow logging.

This script demonstrates the unified flow logging feature by running
a simple query and showing the generated log output.

Usage:
    python test_flow_logging_manual.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag5.core.agent.agent import SimpleRAGAgent
from rag5.config.settings import settings


def main():
    """Run a simple test query and display the flow log."""
    print("=" * 80)
    print("Unified Flow Logging Manual Test")
    print("=" * 80)
    print()
    
    # Display configuration
    print("Configuration:")
    print(f"  Flow Logging Enabled: {settings.enable_flow_logging}")
    print(f"  Flow Log File: {settings.flow_log_file}")
    print(f"  Flow Detail Level: {settings.flow_detail_level}")
    print(f"  Flow Max Content Length: {settings.flow_max_content_length}")
    print(f"  Flow Async Logging: {settings.flow_async_logging}")
    print()
    
    # Create agent
    print("Creating agent...")
    try:
        agent = SimpleRAGAgent()
        print(f"✓ Agent created successfully")
        print(f"  Session ID: {agent._initializer.session_id}")
        print(f"  Flow Logger: {'Enabled' if agent.flow_logger else 'Disabled'}")
        print()
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        print()
        print("Note: This test requires Ollama and Qdrant services to be running.")
        print("Please ensure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. Required models are available:")
        print(f"     - ollama pull {settings.llm_model}")
        print(f"     - ollama pull {settings.embed_model}")
        print("  3. Qdrant is running (if using vector search)")
        return 1
    
    # Run a simple query
    print("Running test query...")
    test_query = "你好，请介绍一下你自己"
    print(f"Query: {test_query}")
    print()
    
    try:
        answer = agent.chat(test_query)
        print("✓ Query completed successfully")
        print()
        print("Answer:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        print()
    except Exception as e:
        print(f"✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # Shutdown agent
    print("Shutting down agent...")
    agent.shutdown()
    print("✓ Agent shutdown complete")
    print()
    
    # Display flow log
    log_file = Path(settings.flow_log_file)
    if log_file.exists():
        print("=" * 80)
        print("Flow Log Output:")
        print("=" * 80)
        print()
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            # Show last 2000 characters to avoid overwhelming output
            if len(log_content) > 2000:
                print(f"[Showing last 2000 characters of {len(log_content)} total]")
                print()
                print(log_content[-2000:])
            else:
                print(log_content)
        print()
        print("=" * 80)
        print(f"Full log available at: {log_file}")
        print("=" * 80)
    else:
        print(f"Note: Flow log file not found at {log_file}")
        print("This may be because flow logging is disabled or the query failed.")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
