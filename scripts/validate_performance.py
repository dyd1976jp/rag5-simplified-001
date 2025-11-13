#!/usr/bin/env python3
"""
Performance validation script for enhanced LLM logging.

Validates that logging overhead meets the following targets:
- < 5ms per log operation
- < 1% total overhead on request time
- Handles concurrent requests efficiently
"""

import time
import statistics
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from rag5.utils.llm_logger import LLMCallLogger
from rag5.utils.reflection_logger import AgentReflectionLogger
from rag5.utils.context_logger import ConversationContextLogger


class PerformanceValidator:
    """Validates logging performance against targets."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.results: Dict[str, Any] = {}
        
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def measure_llm_logger_overhead(self, num_operations: int = 1000) -> Dict[str, float]:
        """Measure LLM logger performance."""
        print(f"\n📊 Testing LLM Logger ({num_operations} operations)...")
        
        log_file = self.temp_dir / "llm_test.log"
        logger = LLMCallLogger(
            log_file=str(log_file),
            enable_prompt_logging=True,
            enable_response_logging=True
        )
        
        # Measure request logging
        request_times = []
        for i in range(num_operations):
            start = time.perf_counter()
            logger.log_request(
                request_id=f"req-{i}",
                session_id="test-session",
                model="qwen2.5:7b",
                prompt="This is a test prompt " * 50,  # ~1KB
                config={"temperature": 0.1, "timeout": 120}
            )
            duration = (time.perf_counter() - start) * 1000  # Convert to ms
            request_times.append(duration)
        
        # Measure response logging
        response_times = []
        for i in range(num_operations):
            start = time.perf_counter()
            logger.log_response(
                request_id=f"req-{i}",
                session_id="test-session",
                response="This is a test response " * 50,  # ~1KB
                duration_seconds=2.5,
                token_usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
            )
            duration = (time.perf_counter() - start) * 1000
            response_times.append(duration)
        
        # Flush and shutdown
        logger.flush()
        logger.shutdown()
        
        return {
            "request_mean": statistics.mean(request_times),
            "request_median": statistics.median(request_times),
            "request_p95": statistics.quantiles(request_times, n=20)[18],  # 95th percentile
            "request_max": max(request_times),
            "response_mean": statistics.mean(response_times),
            "response_median": statistics.median(response_times),
            "response_p95": statistics.quantiles(response_times, n=20)[18],
            "response_max": max(response_times),
        }
    
    def measure_reflection_logger_overhead(self, num_operations: int = 1000) -> Dict[str, float]:
        """Measure reflection logger performance."""
        print(f"\n📊 Testing Reflection Logger ({num_operations} operations)...")
        
        log_file = self.temp_dir / "reflection_test.log"
        logger = AgentReflectionLogger(log_file=str(log_file))
        
        times = []
        for i in range(num_operations):
            start = time.perf_counter()
            logger.log_query_analysis(
                original_query="测试查询",
                detected_intent="factual_lookup",
                requires_tools=True,
                reasoning="This is test reasoning " * 20
            )
            duration = (time.perf_counter() - start) * 1000
            times.append(duration)
        
        logger.flush()
        logger.shutdown()
        
        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "p95": statistics.quantiles(times, n=20)[18],
            "max": max(times),
        }
    
    def measure_context_logger_overhead(self, num_operations: int = 1000) -> Dict[str, float]:
        """Measure context logger performance."""
        print(f"\n📊 Testing Context Logger ({num_operations} operations)...")
        
        log_file = self.temp_dir / "context_test.log"
        logger = ConversationContextLogger(log_file=str(log_file))
        
        times = []
        for i in range(num_operations):
            start = time.perf_counter()
            logger.log_message_added(
                role="user",
                content_length=500,
                total_messages=i + 1,
                total_tokens=1000 + i * 100
            )
            duration = (time.perf_counter() - start) * 1000
            times.append(duration)
        
        logger.flush()
        logger.shutdown()
        
        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "p95": statistics.quantiles(times, n=20)[18],
            "max": max(times),
        }
    
    def measure_concurrent_performance(self, num_threads: int = 10, ops_per_thread: int = 100) -> Dict[str, float]:
        """Measure performance under concurrent load."""
        print(f"\n📊 Testing Concurrent Performance ({num_threads} threads, {ops_per_thread} ops each)...")
        
        log_file = self.temp_dir / "concurrent_test.log"
        logger = LLMCallLogger(log_file=str(log_file))
        
        def worker(thread_id: int) -> List[float]:
            times = []
            for i in range(ops_per_thread):
                start = time.perf_counter()
                logger.log_request(
                    request_id=f"thread-{thread_id}-req-{i}",
                    session_id=f"session-{thread_id}",
                    model="qwen2.5:7b",
                    prompt="Concurrent test prompt " * 30,
                    config={"temperature": 0.1}
                )
                duration = (time.perf_counter() - start) * 1000
                times.append(duration)
            return times
        
        all_times = []
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in as_completed(futures):
                all_times.extend(future.result())
        
        logger.flush()
        logger.shutdown()
        
        return {
            "mean": statistics.mean(all_times),
            "median": statistics.median(all_times),
            "p95": statistics.quantiles(all_times, n=20)[18],
            "max": max(all_times),
            "total_ops": len(all_times),
        }
    
    def measure_total_overhead(self, num_requests: int = 100) -> Dict[str, float]:
        """Measure total logging overhead as percentage of request time."""
        print(f"\n📊 Testing Total Overhead ({num_requests} simulated requests)...")
        
        log_file = self.temp_dir / "overhead_test.log"
        logger = LLMCallLogger(log_file=str(log_file))
        
        # Simulate requests with and without logging
        simulated_request_time = 2.0  # 2 seconds per request
        
        overhead_percentages = []
        for i in range(num_requests):
            # Measure logging time
            logging_start = time.perf_counter()
            
            logger.log_request(
                request_id=f"req-{i}",
                session_id="test-session",
                model="qwen2.5:7b",
                prompt="Test prompt " * 100,
                config={"temperature": 0.1}
            )
            
            # Simulate LLM request
            time.sleep(simulated_request_time)
            
            logger.log_response(
                request_id=f"req-{i}",
                session_id="test-session",
                response="Test response " * 100,
                duration_seconds=simulated_request_time,
                token_usage={"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300}
            )
            
            logging_time = time.perf_counter() - logging_start - simulated_request_time
            overhead_pct = (logging_time / simulated_request_time) * 100
            overhead_percentages.append(overhead_pct)
        
        logger.flush()
        logger.shutdown()
        
        return {
            "mean_overhead_pct": statistics.mean(overhead_percentages),
            "median_overhead_pct": statistics.median(overhead_percentages),
            "max_overhead_pct": max(overhead_percentages),
        }
    
    def run_all_tests(self):
        """Run all performance tests."""
        print("=" * 70)
        print("🚀 Enhanced LLM Logging Performance Validation")
        print("=" * 70)
        
        # Test 1: LLM Logger
        self.results["llm_logger"] = self.measure_llm_logger_overhead()
        
        # Test 2: Reflection Logger
        self.results["reflection_logger"] = self.measure_reflection_logger_overhead()
        
        # Test 3: Context Logger
        self.results["context_logger"] = self.measure_context_logger_overhead()
        
        # Test 4: Concurrent Performance
        self.results["concurrent"] = self.measure_concurrent_performance()
        
        # Test 5: Total Overhead
        self.results["total_overhead"] = self.measure_total_overhead()
        
        self.print_results()
        self.validate_targets()
    
    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 70)
        print("📈 PERFORMANCE RESULTS")
        print("=" * 70)
        
        print("\n1️⃣  LLM Logger Performance:")
        llm = self.results["llm_logger"]
        print(f"   Request Logging:")
        print(f"     Mean:   {llm['request_mean']:.3f} ms")
        print(f"     Median: {llm['request_median']:.3f} ms")
        print(f"     P95:    {llm['request_p95']:.3f} ms")
        print(f"     Max:    {llm['request_max']:.3f} ms")
        print(f"   Response Logging:")
        print(f"     Mean:   {llm['response_mean']:.3f} ms")
        print(f"     Median: {llm['response_median']:.3f} ms")
        print(f"     P95:    {llm['response_p95']:.3f} ms")
        print(f"     Max:    {llm['response_max']:.3f} ms")
        
        print("\n2️⃣  Reflection Logger Performance:")
        refl = self.results["reflection_logger"]
        print(f"     Mean:   {refl['mean']:.3f} ms")
        print(f"     Median: {refl['median']:.3f} ms")
        print(f"     P95:    {refl['p95']:.3f} ms")
        print(f"     Max:    {refl['max']:.3f} ms")
        
        print("\n3️⃣  Context Logger Performance:")
        ctx = self.results["context_logger"]
        print(f"     Mean:   {ctx['mean']:.3f} ms")
        print(f"     Median: {ctx['median']:.3f} ms")
        print(f"     P95:    {ctx['p95']:.3f} ms")
        print(f"     Max:    {ctx['max']:.3f} ms")
        
        print("\n4️⃣  Concurrent Performance:")
        conc = self.results["concurrent"]
        print(f"     Mean:   {conc['mean']:.3f} ms")
        print(f"     Median: {conc['median']:.3f} ms")
        print(f"     P95:    {conc['p95']:.3f} ms")
        print(f"     Max:    {conc['max']:.3f} ms")
        print(f"     Total Operations: {conc['total_ops']}")
        
        print("\n5️⃣  Total Overhead:")
        ovh = self.results["total_overhead"]
        print(f"     Mean:   {ovh['mean_overhead_pct']:.3f}%")
        print(f"     Median: {ovh['median_overhead_pct']:.3f}%")
        print(f"     Max:    {ovh['max_overhead_pct']:.3f}%")
    
    def validate_targets(self):
        """Validate against performance targets."""
        print("\n" + "=" * 70)
        print("✅ TARGET VALIDATION")
        print("=" * 70)
        
        passed = True
        
        # Target 1: < 5ms per log operation
        print("\n🎯 Target 1: < 5ms per log operation")
        llm = self.results["llm_logger"]
        refl = self.results["reflection_logger"]
        ctx = self.results["context_logger"]
        
        checks = [
            ("LLM Request (mean)", llm['request_mean'], 5.0),
            ("LLM Response (mean)", llm['response_mean'], 5.0),
            ("Reflection (mean)", refl['mean'], 5.0),
            ("Context (mean)", ctx['mean'], 5.0),
        ]
        
        for name, value, target in checks:
            status = "✅ PASS" if value < target else "❌ FAIL"
            print(f"   {name}: {value:.3f} ms {status}")
            if value >= target:
                passed = False
        
        # Target 2: < 1% total overhead
        print("\n🎯 Target 2: < 1% total overhead")
        ovh = self.results["total_overhead"]
        overhead_pass = ovh['mean_overhead_pct'] < 1.0
        status = "✅ PASS" if overhead_pass else "❌ FAIL"
        print(f"   Mean overhead: {ovh['mean_overhead_pct']:.3f}% {status}")
        if not overhead_pass:
            passed = False
        
        # Target 3: Concurrent performance
        print("\n🎯 Target 3: Concurrent request handling")
        conc = self.results["concurrent"]
        concurrent_pass = conc['p95'] < 10.0  # Allow 10ms for concurrent
        status = "✅ PASS" if concurrent_pass else "❌ FAIL"
        print(f"   P95 latency: {conc['p95']:.3f} ms {status}")
        if not concurrent_pass:
            passed = False
        
        print("\n" + "=" * 70)
        if passed:
            print("🎉 ALL PERFORMANCE TARGETS MET!")
        else:
            print("⚠️  SOME PERFORMANCE TARGETS NOT MET")
        print("=" * 70)
        
        return passed


def main():
    """Run performance validation."""
    validator = PerformanceValidator()
    try:
        validator.run_all_tests()
    finally:
        validator.cleanup()


if __name__ == "__main__":
    main()
