#!/usr/bin/env python3
"""
Security validation script for enhanced LLM logging.

Validates:
- Sensitive data redaction works correctly
- File permissions on log files
- No data leaks in error scenarios
- Security best practices
"""

import os
import stat
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from rag5.utils.llm_logger import LLMCallLogger
from rag5.utils.redactor import SensitiveDataRedactor


class SecurityValidator:
    """Validates security aspects of logging system."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results: Dict[str, bool] = {}
        self.issues: List[str] = []
        
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_prompt_redaction(self) -> bool:
        """Test that prompts are properly redacted."""
        print("\n🔒 Testing prompt redaction...")
        
        log_file = self.temp_dir / "redaction_test.log"
        logger = LLMCallLogger(
            log_file=str(log_file),
            redact_prompts=True,
            redact_responses=False
        )
        
        sensitive_prompt = "My SSN is 123-45-6789 and my email is user@example.com"
        
        logger.log_request(
            request_id="test-1",
            session_id="test-session",
            model="qwen2.5:7b",
            prompt=sensitive_prompt,
            config={}
        )
        
        logger.flush()
        logger.shutdown()
        
        # Read log file and check for redaction
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Should not contain sensitive data
        if "123-45-6789" in content or "user@example.com" in content:
            self.issues.append("Prompt redaction failed: sensitive data found in logs")
            return False
        
        # Should contain redaction marker
        if "[REDACTED:" not in content:
            self.issues.append("Prompt redaction failed: no redaction marker found")
            return False
        
        print("   ✅ Prompts properly redacted")
        return True
    
    def test_response_redaction(self) -> bool:
        """Test that responses are properly redacted."""
        print("\n🔒 Testing response redaction...")
        
        log_file = self.temp_dir / "response_redaction_test.log"
        logger = LLMCallLogger(
            log_file=str(log_file),
            redact_prompts=False,
            redact_responses=True
        )
        
        sensitive_response = "The password is SuperSecret123!"
        
        logger.log_response(
            request_id="test-1",
            session_id="test-session",
            response=sensitive_response,
            duration_seconds=1.5,
            token_usage=None
        )
        
        logger.flush()
        logger.shutdown()
        
        # Read log file and check for redaction
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Should not contain sensitive data
        if "SuperSecret123" in content:
            self.issues.append("Response redaction failed: sensitive data found in logs")
            return False
        
        # Should contain redaction marker
        if "[REDACTED:" not in content:
            self.issues.append("Response redaction failed: no redaction marker found")
            return False
        
        print("   ✅ Responses properly redacted")
        return True
    
    def test_error_messages_not_redacted(self) -> bool:
        """Test that error messages are never redacted."""
        print("\n🔒 Testing error messages are not redacted...")
        
        log_file = self.temp_dir / "error_test.log"
        logger = LLMCallLogger(
            log_file=str(log_file),
            redact_prompts=True,
            redact_responses=True
        )
        
        error_message = "Connection failed: timeout after 30 seconds"
        
        logger.log_error(
            request_id="test-1",
            session_id="test-session",
            error=Exception(error_message),
            duration_seconds=30.0
        )
        
        logger.flush()
        logger.shutdown()
        
        # Read log file and check error is not redacted
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Error message should be present
        if "timeout" not in content.lower():
            self.issues.append("Error messages incorrectly redacted")
            return False
        
        print("   ✅ Error messages preserved (not redacted)")
        return True
    
    def test_custom_pattern_redaction(self) -> bool:
        """Test custom pattern redaction."""
        print("\n🔒 Testing custom pattern redaction...")
        
        redactor = SensitiveDataRedactor(
            redact_prompts=True,
            patterns=[r'\b\d{3}-\d{2}-\d{4}\b']  # SSN pattern
        )
        
        text = "My SSN is 123-45-6789 and I live in California"
        redacted = redactor.redact_text(text)
        
        # Should not contain SSN
        if "123-45-6789" in redacted:
            self.issues.append("Custom pattern redaction failed: SSN found")
            return False
        
        # Should preserve non-sensitive parts
        if "California" not in redacted:
            self.issues.append("Custom pattern redaction removed non-sensitive data")
            return False
        
        print("   ✅ Custom patterns properly redacted")
        return True
    
    def test_file_permissions(self) -> bool:
        """Test that log files have appropriate permissions."""
        print("\n🔒 Testing file permissions...")
        
        log_file = self.temp_dir / "permissions_test.log"
        logger = LLMCallLogger(log_file=str(log_file))
        
        logger.log_request(
            request_id="test-1",
            session_id="test-session",
            model="qwen2.5:7b",
            prompt="test",
            config={}
        )
        
        logger.flush()
        logger.shutdown()
        
        # Check file permissions
        file_stat = os.stat(log_file)
        file_mode = stat.filemode(file_stat.st_mode)
        
        # On Unix systems, check if file is readable by others
        if file_stat.st_mode & stat.S_IROTH:
            self.issues.append(f"Log file is world-readable: {file_mode}")
            print(f"   ⚠️  Warning: Log file is world-readable ({file_mode})")
            print(f"   💡 Recommendation: Set permissions to 600 (owner read/write only)")
            return False
        
        print(f"   ✅ File permissions appropriate ({file_mode})")
        return True
    
    def test_no_data_leak_on_exception(self) -> bool:
        """Test that exceptions don't leak sensitive data."""
        print("\n🔒 Testing exception handling...")
        
        log_file = self.temp_dir / "exception_test.log"
        logger = LLMCallLogger(
            log_file=str(log_file),
            redact_prompts=True
        )
        
        # Try to cause an exception during logging
        try:
            # This should not raise an exception
            logger.log_request(
                request_id="test-1",
                session_id="test-session",
                model="qwen2.5:7b",
                prompt="Sensitive data: password123",
                config={}
            )
            
            # Force an error by trying to write to closed file
            logger.shutdown()
            logger.log_request(
                request_id="test-2",
                session_id="test-session",
                model="qwen2.5:7b",
                prompt="More sensitive data",
                config={}
            )
            
            print("   ✅ Exceptions handled gracefully")
            return True
            
        except Exception as e:
            # Check if exception message contains sensitive data
            error_msg = str(e)
            if "password123" in error_msg or "sensitive" in error_msg.lower():
                self.issues.append("Exception leaked sensitive data")
                return False
            
            print("   ✅ No data leak in exceptions")
            return True
    
    def test_redaction_length_preservation(self) -> bool:
        """Test that redaction preserves content length information."""
        print("\n🔒 Testing redaction length preservation...")
        
        redactor = SensitiveDataRedactor(redact_prompts=True)
        
        test_cases = [
            ("Short text", 10),
            ("Medium length text " * 10, 200),
            ("Very long text " * 100, 1500),
        ]
        
        for text, expected_min_length in test_cases:
            redacted = redactor.redact_text(text)
            
            # Should contain length information
            if "characters]" not in redacted:
                self.issues.append("Redaction doesn't preserve length information")
                return False
            
            # Extract length from redaction marker
            import re
            match = re.search(r'\[REDACTED: (\d+) characters\]', redacted)
            if not match:
                self.issues.append("Redaction marker format incorrect")
                return False
            
            reported_length = int(match.group(1))
            if reported_length < expected_min_length:
                self.issues.append(f"Reported length {reported_length} less than expected {expected_min_length}")
                return False
        
        print("   ✅ Redaction preserves length information")
        return True
    
    def run_all_tests(self) -> Tuple[int, int]:
        """Run all security tests."""
        print("=" * 70)
        print("🔐 Enhanced LLM Logging Security Validation")
        print("=" * 70)
        
        tests = [
            ("Prompt Redaction", self.test_prompt_redaction),
            ("Response Redaction", self.test_response_redaction),
            ("Error Messages Not Redacted", self.test_error_messages_not_redacted),
            ("Custom Pattern Redaction", self.test_custom_pattern_redaction),
            ("File Permissions", self.test_file_permissions),
            ("Exception Handling", self.test_no_data_leak_on_exception),
            ("Length Preservation", self.test_redaction_length_preservation),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                if test_func():
                    self.results[name] = True
                    passed += 1
                else:
                    self.results[name] = False
                    failed += 1
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
                self.results[name] = False
                self.issues.append(f"{name}: {str(e)}")
                failed += 1
        
        return passed, failed
    
    def print_summary(self, passed: int, failed: int):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("📊 SECURITY VALIDATION SUMMARY")
        print("=" * 70)
        
        total = passed + failed
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if self.issues:
            print("\n⚠️  Issues Found:")
            for issue in self.issues:
                print(f"   - {issue}")
        
        print("\n" + "=" * 70)
        if failed == 0:
            print("🎉 ALL SECURITY CHECKS PASSED!")
        else:
            print("⚠️  SOME SECURITY CHECKS FAILED - REVIEW REQUIRED")
        print("=" * 70)
        
        # Print security best practices
        print("\n📋 Security Best Practices:")
        print("   1. Enable redaction in production: set redact_prompts=True, redact_responses=True")
        print("   2. Set log file permissions to 600 (owner read/write only)")
        print("   3. Implement log rotation to prevent unbounded growth")
        print("   4. Regularly review logs for accidental sensitive data exposure")
        print("   5. Use custom patterns to redact domain-specific sensitive data")
        print("   6. Never log authentication tokens or API keys")
        print("   7. Consider encrypting logs at rest for highly sensitive environments")
        print("   8. Implement log retention policies compliant with regulations")


def main():
    """Run security validation."""
    validator = SecurityValidator()
    try:
        passed, failed = validator.run_all_tests()
        validator.print_summary(passed, failed)
        return 0 if failed == 0 else 1
    finally:
        validator.cleanup()


if __name__ == "__main__":
    exit(main())
