"""
Unit tests for SensitiveDataRedactor.

Tests prompt redaction, response redaction, custom pattern matching,
length preservation in redacted output, and verification that error
messages are never redacted.
"""

import pytest
from rag5.utils.redactor import SensitiveDataRedactor


class TestSensitiveDataRedactor:
    """Test suite for SensitiveDataRedactor"""
    
    def test_initialization_default(self):
        """Test default initialization"""
        redactor = SensitiveDataRedactor()
        
        assert redactor.redact_prompts is False
        assert redactor.redact_responses is False
        assert redactor.patterns == []
    
    def test_initialization_with_prompt_redaction(self):
        """Test initialization with prompt redaction enabled"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        assert redactor.redact_prompts is True
        assert redactor.redact_responses is False
    
    def test_initialization_with_response_redaction(self):
        """Test initialization with response redaction enabled"""
        redactor = SensitiveDataRedactor(redact_responses=True)
        
        assert redactor.redact_prompts is False
        assert redactor.redact_responses is True
    
    def test_initialization_with_both_redactions(self):
        """Test initialization with both prompt and response redaction"""
        redactor = SensitiveDataRedactor(
            redact_prompts=True,
            redact_responses=True
        )
        
        assert redactor.redact_prompts is True
        assert redactor.redact_responses is True
    
    def test_initialization_with_custom_patterns(self):
        """Test initialization with custom patterns"""
        patterns = [r'\b\d{3}-\d{2}-\d{4}\b', r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b']
        redactor = SensitiveDataRedactor(patterns=patterns)
        
        assert redactor.patterns == patterns
        assert len(redactor._compiled_patterns) == 2
    
    def test_redact_text_basic(self):
        """Test basic text redaction"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        text = "This is sensitive user data"
        redacted = redactor.redact_text(text)
        
        assert redacted == "[REDACTED: 27 characters]"
    
    def test_redact_text_preserves_length(self):
        """Test that redacted text preserves original length information"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        short_text = "Hi"
        long_text = "This is a much longer piece of text that contains sensitive information"
        
        short_redacted = redactor.redact_text(short_text)
        long_redacted = redactor.redact_text(long_text)
        
        assert "[REDACTED: 2 characters]" in short_redacted
        assert "[REDACTED: 71 characters]" in long_redacted
    
    def test_redact_text_empty_string(self):
        """Test redacting empty string"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        redacted = redactor.redact_text("")
        
        assert redacted == ""
    
    def test_redact_text_with_chinese_characters(self):
        """Test redacting text with Chinese characters"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        text = "李小勇和人合作入股了什么公司"
        redacted = redactor.redact_text(text)
        
        # Should preserve character count
        assert f"[REDACTED: {len(text)} characters]" in redacted
    
    def test_redact_text_with_custom_pattern_ssn(self):
        """Test redacting text with SSN pattern"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b\d{3}-\d{2}-\d{4}\b']
        )
        
        text = "My SSN is 123-45-6789 and I need help"
        redacted = redactor.redact_text(text)
        
        assert "123-45-6789" not in redacted
        assert "[REDACTED: 11 characters]" in redacted
        assert "and I need help" in redacted
    
    def test_redact_text_with_custom_pattern_email(self):
        """Test redacting text with email pattern"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b']
        )
        
        text = "Contact me at user@example.com for more info"
        redacted = redactor.redact_text(text)
        
        assert "user@example.com" not in redacted
        assert "[REDACTED:" in redacted
        assert "for more info" in redacted
    
    def test_redact_text_with_multiple_patterns(self):
        """Test redacting text with multiple patterns"""
        redactor = SensitiveDataRedactor(
            patterns=[
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
            ]
        )
        
        text = "My SSN is 123-45-6789 and email is user@example.com"
        redacted = redactor.redact_text(text)
        
        assert "123-45-6789" not in redacted
        assert "user@example.com" not in redacted
        assert "[REDACTED:" in redacted
    
    def test_redact_text_with_invalid_pattern(self):
        """Test that invalid regex patterns are handled gracefully"""
        # Invalid regex pattern (unmatched bracket)
        redactor = SensitiveDataRedactor(
            patterns=[r'[invalid(']
        )
        
        # Should not raise an exception
        text = "Some text"
        redacted = redactor.redact_text(text)
        
        # Should fall back to full redaction since pattern is invalid
        assert "[REDACTED:" in redacted
    
    def test_should_redact_llm_request_with_prompt_redaction(self):
        """Test should_redact for llm_request with prompt redaction enabled"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        assert redactor.should_redact("llm_request") is True
    
    def test_should_redact_llm_request_without_prompt_redaction(self):
        """Test should_redact for llm_request without prompt redaction"""
        redactor = SensitiveDataRedactor(redact_prompts=False)
        
        assert redactor.should_redact("llm_request") is False
    
    def test_should_redact_llm_response_with_response_redaction(self):
        """Test should_redact for llm_response with response redaction enabled"""
        redactor = SensitiveDataRedactor(redact_responses=True)
        
        assert redactor.should_redact("llm_response") is True
    
    def test_should_redact_llm_response_without_response_redaction(self):
        """Test should_redact for llm_response without response redaction"""
        redactor = SensitiveDataRedactor(redact_responses=False)
        
        assert redactor.should_redact("llm_response") is False
    
    def test_should_redact_llm_error_never_redacted(self):
        """Test that llm_error is never redacted"""
        redactor = SensitiveDataRedactor(
            redact_prompts=True,
            redact_responses=True
        )
        
        assert redactor.should_redact("llm_error") is False
    
    def test_should_redact_error_never_redacted(self):
        """Test that error log type is never redacted"""
        redactor = SensitiveDataRedactor(
            redact_prompts=True,
            redact_responses=True
        )
        
        assert redactor.should_redact("error") is False
    
    def test_should_redact_diagnostic_never_redacted(self):
        """Test that diagnostic log type is never redacted"""
        redactor = SensitiveDataRedactor(
            redact_prompts=True,
            redact_responses=True
        )
        
        assert redactor.should_redact("diagnostic") is False
    
    def test_should_redact_with_custom_patterns(self):
        """Test should_redact with custom patterns"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b\d{3}-\d{2}-\d{4}\b']
        )
        
        # Should redact non-error types when patterns are defined
        assert redactor.should_redact("llm_request") is True
        assert redactor.should_redact("llm_response") is True
        assert redactor.should_redact("agent_reflection") is True
        
        # But never error types
        assert redactor.should_redact("llm_error") is False
    
    def test_redact_if_needed_redacts_when_should(self):
        """Test redact_if_needed redacts when it should"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        text = "Sensitive prompt text"
        result = redactor.redact_if_needed(text, "llm_request")
        
        assert result == "[REDACTED: 21 characters]"
    
    def test_redact_if_needed_preserves_when_should_not(self):
        """Test redact_if_needed preserves text when it shouldn't redact"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        text = "Error message: Connection timeout"
        result = redactor.redact_if_needed(text, "llm_error")
        
        assert result == text
    
    def test_redact_if_needed_with_response_redaction(self):
        """Test redact_if_needed with response redaction"""
        redactor = SensitiveDataRedactor(redact_responses=True)
        
        response = "This is the LLM response"
        result = redactor.redact_if_needed(response, "llm_response")
        
        assert "[REDACTED:" in result
    
    def test_redact_if_needed_preserves_request_when_only_response_redacted(self):
        """Test that requests are preserved when only responses are redacted"""
        redactor = SensitiveDataRedactor(redact_responses=True)
        
        request = "This is the LLM request"
        result = redactor.redact_if_needed(request, "llm_request")
        
        assert result == request
    
    def test_redact_if_needed_with_custom_pattern(self):
        """Test redact_if_needed with custom pattern"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b\d{3}-\d{2}-\d{4}\b']
        )
        
        text = "My SSN is 123-45-6789"
        result = redactor.redact_if_needed(text, "llm_request")
        
        assert "123-45-6789" not in result
        assert "[REDACTED:" in result
    
    def test_error_messages_never_redacted_even_with_all_options(self):
        """Test that error messages are never redacted regardless of settings"""
        redactor = SensitiveDataRedactor(
            redact_prompts=True,
            redact_responses=True,
            patterns=[r'\b\d{3}-\d{2}-\d{4}\b']
        )
        
        error_text = "Error: Failed to connect to 123-45-6789"
        
        # Should not redact error type
        result = redactor.redact_if_needed(error_text, "llm_error")
        assert result == error_text
        
        result = redactor.redact_if_needed(error_text, "error")
        assert result == error_text
        
        result = redactor.redact_if_needed(error_text, "diagnostic")
        assert result == error_text
    
    def test_length_preservation_various_sizes(self):
        """Test that length is preserved for various text sizes"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        test_cases = [
            ("a", 1),
            ("Hello", 5),
            ("This is a test", 14),
            ("A" * 100, 100),
            ("A" * 1000, 1000),
        ]
        
        for text, expected_length in test_cases:
            redacted = redactor.redact_text(text)
            assert f"[REDACTED: {expected_length} characters]" in redacted
    
    def test_multiple_pattern_matches_in_same_text(self):
        """Test redacting multiple pattern matches in the same text"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b\d{3}-\d{2}-\d{4}\b']
        )
        
        text = "SSN1: 123-45-6789 and SSN2: 987-65-4321"
        redacted = redactor.redact_text(text)
        
        assert "123-45-6789" not in redacted
        assert "987-65-4321" not in redacted
        assert redacted.count("[REDACTED:") == 2
    
    def test_no_redaction_when_disabled(self):
        """Test that no redaction occurs when all options are disabled"""
        redactor = SensitiveDataRedactor(
            redact_prompts=False,
            redact_responses=False
        )
        
        text = "This should not be redacted"
        
        assert redactor.should_redact("llm_request") is False
        assert redactor.should_redact("llm_response") is False
        
        result = redactor.redact_if_needed(text, "llm_request")
        assert result == text
        
        result = redactor.redact_if_needed(text, "llm_response")
        assert result == text
    
    def test_redaction_with_unicode_characters(self):
        """Test redaction with various Unicode characters"""
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        test_cases = [
            "Hello 世界",
            "Привет мир",
            "مرحبا بالعالم",
            "🎉🎊🎈",
        ]
        
        for text in test_cases:
            redacted = redactor.redact_text(text)
            assert f"[REDACTED: {len(text)} characters]" in redacted
    
    def test_pattern_redaction_preserves_surrounding_text(self):
        """Test that pattern redaction preserves text around matches"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b\d{3}-\d{2}-\d{4}\b']
        )
        
        text = "Before 123-45-6789 after"
        redacted = redactor.redact_text(text)
        
        assert "Before" in redacted
        assert "after" in redacted
        assert "123-45-6789" not in redacted
    
    def test_case_insensitive_pattern(self):
        """Test case-insensitive pattern matching"""
        redactor = SensitiveDataRedactor(
            patterns=[r'(?i)\bsecret\b']
        )
        
        text1 = "This is a SECRET message"
        text2 = "This is a secret message"
        text3 = "This is a Secret message"
        
        for text in [text1, text2, text3]:
            redacted = redactor.redact_text(text)
            assert "SECRET" not in redacted.upper()
            assert "[REDACTED:" in redacted
    
    def test_phone_number_pattern(self):
        """Test redacting phone numbers"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b\d{3}-\d{3}-\d{4}\b']
        )
        
        text = "Call me at 555-123-4567"
        redacted = redactor.redact_text(text)
        
        assert "555-123-4567" not in redacted
        assert "Call me at" in redacted
    
    def test_credit_card_pattern(self):
        """Test redacting credit card numbers"""
        redactor = SensitiveDataRedactor(
            patterns=[r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b']
        )
        
        text = "Card: 1234-5678-9012-3456"
        redacted = redactor.redact_text(text)
        
        assert "1234-5678-9012-3456" not in redacted
        assert "Card:" in redacted
