"""
ID generation utilities for enhanced logging.

This module provides functions for generating unique identifiers used in
structured logging to correlate and track operations across the system.
"""

import uuid
from typing import Optional


def generate_request_id() -> str:
    """
    Generate a unique request ID.
    
    Used to correlate LLM requests with their responses. Each request-response
    pair shares the same request_id.
    
    Returns:
        A unique UUID string (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    
    Example:
        >>> request_id = generate_request_id()
        >>> print(f"Request ID: {request_id}")
        Request ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    """
    return str(uuid.uuid4())


def generate_session_id(prefix: Optional[str] = None) -> str:
    """
    Generate a unique session ID for conversation tracking.
    
    Used to track all operations within a single conversation session.
    Multiple requests and responses within the same conversation share
    the same session_id.
    
    Args:
        prefix: Optional prefix for the session ID (e.g., "session", "conv")
    
    Returns:
        A unique session identifier string
    
    Example:
        >>> session_id = generate_session_id("session")
        >>> print(f"Session ID: {session_id}")
        Session ID: session-a1b2c3d4-e5f6-7890-abcd-ef1234567890
        
        >>> session_id = generate_session_id()
        >>> print(f"Session ID: {session_id}")
        Session ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    """
    session_uuid = str(uuid.uuid4())
    if prefix:
        return f"{prefix}-{session_uuid}"
    return session_uuid


def generate_correlation_id(prefix: Optional[str] = None) -> str:
    """
    Generate a unique correlation ID for linking related operations.
    
    Used to link related operations across different components. For example,
    a single user query might trigger multiple LLM calls, tool invocations,
    and reflections - all sharing the same correlation_id.
    
    Args:
        prefix: Optional prefix for the correlation ID (e.g., "query", "op")
    
    Returns:
        A unique correlation identifier string
    
    Example:
        >>> correlation_id = generate_correlation_id("query")
        >>> print(f"Correlation ID: {correlation_id}")
        Correlation ID: query-a1b2c3d4-e5f6-7890-abcd-ef1234567890
        
        >>> correlation_id = generate_correlation_id()
        >>> print(f"Correlation ID: {correlation_id}")
        Correlation ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
    """
    correlation_uuid = str(uuid.uuid4())
    if prefix:
        return f"{prefix}-{correlation_uuid}"
    return correlation_uuid
