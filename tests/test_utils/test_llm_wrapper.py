"""
Unit tests for ChatOllamaWithLogging.

Tests logging on successful LLM calls, error handling, session_id tracking,
and timing measurement with mocked ChatOllama base class.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration, LLMResult
from rag5.utils.llm_logger import ChatOllamaWithLogging, LLMCallLogger


class TestChatOllamaWithLogging:
    """Test suite for ChatOllamaWithLogging"""
    
    @pytest.fixture
    def mock_llm_logger(self):
        """Create a mock LLMCallLogger"""
        logger = Mock(spec=LLMCallLogger)
        logger.log_request = Mock()
        logger.log_response = Mock()
        logger.log_error = Mock()
        return logger
    
    @pytest.fixture
    def chat_ollama_with_logging(self, mock_llm_logger, tmp_path):
        """Create ChatOllamaWithLogging instance with real logger"""
        # Create a real logger with temp file
        real_logger = LLMCallLogger(
            log_file=str(tmp_path / "test.log"),
            async_logging=False
        )
        # Replace its methods with mocks to track calls
        real_logger.log_request = mock_llm_logger.log_request
        real_logger.log_response = mock_llm_logger.log_response
        real_logger.log_error = mock_llm_logger.log_error
        
        return ChatOllamaWithLogging(
            llm_logger=real_logger,
            session_id="test-session-123",
            model="qwen2.5:7b",
            base_url="http://localhost:11434",
            temperature=0.1,
            timeout=120
        )
    
    def test_initialization(self, mock_llm_logger, tmp_path):
        """Test that ChatOllamaWithLogging initializes correctly"""
        real_logger = LLMCallLogger(
            log_file=str(tmp_path / "test.log"),
            async_logging=False
        )
        
        llm = ChatOllamaWithLogging(
            llm_logger=real_logger,
            session_id="test-session",
            model="qwen2.5:7b"
        )
        
        # Verify attributes are set (use object.__getattribute__ to access private attrs)
        assert object.__getattribute__(llm, '_llm_logger') == real_logger
        assert object.__getattribute__(llm, '_session_id') == "test-session"
        assert llm.model == "qwen2.5:7b"
    
    def test_format_messages_single_message(self, chat_ollama_with_logging):
        """Test formatting a single message"""
        messages = [HumanMessage(content="Hello, world!")]
        formatted = chat_ollama_with_logging._format_messages(messages)
        
        assert formatted == "[human]: Hello, world!"
    
    def test_format_messages_multiple_messages(self, chat_ollama_with_logging):
        """Test formatting multiple messages"""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is 2+2?"),
            AIMessage(content="4")
        ]
        formatted = chat_ollama_with_logging._format_messages(messages)
        
        expected = "[system]: You are a helpful assistant.\n[human]: What is 2+2?\n[ai]: 4"
        assert formatted == expected
    
    def test_generate_logs_request(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that _generate logs the request"""
        messages = [HumanMessage(content="Test message")]
        
        # Mock the parent _generate method
        mock_result = ChatResult(
            generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]
        )
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            chat_ollama_with_logging._generate(messages)
        
        # Verify log_request was called
        assert mock_llm_logger.log_request.called
        call_args = mock_llm_logger.log_request.call_args
        
        # Verify arguments
        assert call_args.kwargs['session_id'] == "test-session-123"
        assert call_args.kwargs['model'] == "qwen2.5:7b"
        assert "[human]: Test message" in call_args.kwargs['prompt']
        assert 'temperature' in call_args.kwargs['config']
        assert call_args.kwargs['config']['temperature'] == 0.1
    
    def test_generate_logs_response(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that _generate logs the response"""
        messages = [HumanMessage(content="Test message")]
        
        # Mock the parent _generate method
        mock_result = ChatResult(
            generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]
        )
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            result = chat_ollama_with_logging._generate(messages)
        
        # Verify log_response was called
        assert mock_llm_logger.log_response.called
        call_args = mock_llm_logger.log_response.call_args
        
        # Verify arguments
        assert call_args.kwargs['session_id'] == "test-session-123"
        assert call_args.kwargs['response'] == "Test response"
        assert 'duration_seconds' in call_args.kwargs
        assert call_args.kwargs['duration_seconds'] >= 0
    
    def test_generate_logs_token_usage(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that _generate logs token usage when available"""
        messages = [HumanMessage(content="Test message")]
        
        # Mock the parent _generate method with token usage
        mock_result = ChatResult(
            generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))],
            llm_output={
                "token_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                }
            }
        )
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            chat_ollama_with_logging._generate(messages)
        
        # Verify token usage was logged
        call_args = mock_llm_logger.log_response.call_args
        assert 'token_usage' in call_args.kwargs
        assert call_args.kwargs['token_usage']['prompt_tokens'] == 10
        assert call_args.kwargs['token_usage']['completion_tokens'] == 5
    
    def test_generate_logs_error(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that _generate logs errors"""
        messages = [HumanMessage(content="Test message")]
        
        # Mock the parent _generate method to raise an exception
        test_error = ValueError("Test error")
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', side_effect=test_error):
            with pytest.raises(ValueError):
                chat_ollama_with_logging._generate(messages)
        
        # Verify log_error was called
        assert mock_llm_logger.log_error.called
        call_args = mock_llm_logger.log_error.call_args
        
        # Verify arguments
        assert call_args.kwargs['session_id'] == "test-session-123"
        assert call_args.kwargs['error'] == test_error
        assert 'duration_seconds' in call_args.kwargs
    
    def test_generate_measures_timing(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that _generate measures request duration"""
        messages = [HumanMessage(content="Test message")]
        
        # Mock the parent _generate method with a delay
        def slow_generate(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return ChatResult(
                generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]
            )
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', side_effect=slow_generate):
            chat_ollama_with_logging._generate(messages)
        
        # Verify duration was measured
        call_args = mock_llm_logger.log_response.call_args
        duration = call_args.kwargs['duration_seconds']
        
        # Should be at least 0.1 seconds
        assert duration >= 0.1
    
    def test_generate_measures_timing_on_error(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that _generate measures duration even when error occurs"""
        messages = [HumanMessage(content="Test message")]
        
        # Mock the parent _generate method with a delay then error
        def slow_error(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            raise ValueError("Test error")
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', side_effect=slow_error):
            with pytest.raises(ValueError):
                chat_ollama_with_logging._generate(messages)
        
        # Verify duration was measured
        call_args = mock_llm_logger.log_error.call_args
        duration = call_args.kwargs['duration_seconds']
        
        # Should be at least 0.1 seconds
        assert duration >= 0.1
    
    def test_session_id_tracking(self, mock_llm_logger, tmp_path):
        """Test that session_id is tracked across multiple calls"""
        session_id = "persistent-session-456"
        real_logger = LLMCallLogger(
            log_file=str(tmp_path / "test.log"),
            async_logging=False
        )
        real_logger.log_request = mock_llm_logger.log_request
        real_logger.log_response = mock_llm_logger.log_response
        
        llm = ChatOllamaWithLogging(
            llm_logger=real_logger,
            session_id=session_id,
            model="qwen2.5:7b"
        )
        
        messages = [HumanMessage(content="Test message")]
        mock_result = ChatResult(
            generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]
        )
        
        # Make multiple calls
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            llm._generate(messages)
            llm._generate(messages)
        
        # Verify session_id is consistent
        assert mock_llm_logger.log_request.call_count == 2
        assert mock_llm_logger.log_response.call_count == 2
        
        for call in mock_llm_logger.log_request.call_args_list:
            assert call.kwargs['session_id'] == session_id
        
        for call in mock_llm_logger.log_response.call_args_list:
            assert call.kwargs['session_id'] == session_id
    
    def test_request_id_is_unique(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that each request gets a unique request_id"""
        messages = [HumanMessage(content="Test message")]
        mock_result = ChatResult(
            generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]
        )
        
        # Make multiple calls
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            chat_ollama_with_logging._generate(messages)
            chat_ollama_with_logging._generate(messages)
        
        # Get request_ids from both calls
        request_ids = [
            call.kwargs['request_id']
            for call in mock_llm_logger.log_request.call_args_list
        ]
        
        # Verify they are unique
        assert len(request_ids) == 2
        assert request_ids[0] != request_ids[1]
    
    def test_request_response_correlation(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that request and response share the same request_id"""
        messages = [HumanMessage(content="Test message")]
        mock_result = ChatResult(
            generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]
        )
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            chat_ollama_with_logging._generate(messages)
        
        # Get request_id from both calls
        request_id_from_request = mock_llm_logger.log_request.call_args.kwargs['request_id']
        request_id_from_response = mock_llm_logger.log_response.call_args.kwargs['request_id']
        
        # Verify they match
        assert request_id_from_request == request_id_from_response
    
    def test_config_includes_kwargs(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that additional kwargs are included in config"""
        messages = [HumanMessage(content="Test message")]
        mock_result = ChatResult(
            generations=[ChatGeneration(text="Test response", message=AIMessage(content="Test response"))]
        )
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            chat_ollama_with_logging._generate(messages, max_tokens=100, top_p=0.9)
        
        # Verify kwargs are in config
        call_args = mock_llm_logger.log_request.call_args
        config = call_args.kwargs['config']
        
        assert 'max_tokens' in config
        assert config['max_tokens'] == 100
        assert 'top_p' in config
        assert config['top_p'] == 0.9
    
    def test_empty_response_handling(self, chat_ollama_with_logging, mock_llm_logger):
        """Test handling of empty response"""
        messages = [HumanMessage(content="Test message")]
        
        # Mock result with no generations
        mock_result = ChatResult(generations=[])
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            chat_ollama_with_logging._generate(messages)
        
        # Verify empty string is logged
        call_args = mock_llm_logger.log_response.call_args
        assert call_args.kwargs['response'] == ""
    
    def test_chinese_characters_in_messages(self, chat_ollama_with_logging, mock_llm_logger):
        """Test that Chinese characters are handled correctly"""
        messages = [HumanMessage(content="李小勇是谁？")]
        mock_result = ChatResult(
            generations=[ChatGeneration(text="李小勇是一位企业家", message=AIMessage(content="李小勇是一位企业家"))]
        )
        
        with patch.object(ChatOllamaWithLogging.__bases__[0], '_generate', return_value=mock_result):
            chat_ollama_with_logging._generate(messages)
        
        # Verify Chinese characters in request
        request_call_args = mock_llm_logger.log_request.call_args
        assert "李小勇是谁？" in request_call_args.kwargs['prompt']
        
        # Verify Chinese characters in response
        response_call_args = mock_llm_logger.log_response.call_args
        assert response_call_args.kwargs['response'] == "李小勇是一位企业家"
