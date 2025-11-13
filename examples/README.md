# Log Analysis Examples

This directory contains example scripts for analyzing RAG5 enhanced logging output.

## Available Scripts

### Unified Flow Log Analysis

#### 1. analyze_flow_basic.py

Demonstrates basic flow log analysis including loading, parsing, filtering by session, and extracting timing statistics.

**Usage:**

```bash
python examples/analyze_flow_basic.py
```

**Features:**
- Load and parse unified flow log
- Display event type breakdown
- Extract timing statistics (tool execution, LLM calls, total query time)
- Filter entries by session ID
- Show session event timeline

**Requirements:** 10.1, 10.2

#### 2. analyze_flow_errors.py

Analyzes errors in flow logs, groups them by type, and extracts error context.

**Usage:**

```bash
python examples/analyze_flow_errors.py
```

**Features:**
- Find all errors in the log
- Group errors by type
- Extract error context (events before error)
- Identify error patterns
- Calculate error rates
- Provide recommendations

**Requirements:** 10.3

#### 3. analyze_flow_performance.py

Performs comprehensive performance analysis to identify bottlenecks and slow operations.

**Usage:**

```bash
python examples/analyze_flow_performance.py
```

**Features:**
- Overall performance statistics
- Find slow operations (queries, LLM calls, tool executions)
- Identify bottlenecks
- Analyze performance trends over time
- Generate performance reports with recommendations

**Requirements:** 10.2, 10.3

### Enhanced Logging Analysis

#### 4. analyze_llm_logs.py

Analyzes LLM interaction logs to extract insights about timing, token usage, errors, and performance.

**Usage:**

```bash
# Basic analysis
python examples/analyze_llm_logs.py

# Analyze specific log file
python examples/analyze_llm_logs.py --log-file logs/llm_interactions.log

# Find slow requests (> 10 seconds)
python examples/analyze_llm_logs.py --slow-threshold 10.0

# Analyze specific session
python examples/analyze_llm_logs.py --session-id session-xyz-789

# Get request/response pair
python examples/analyze_llm_logs.py --request-id a1b2c3d4-e5f6-7890

# Output as JSON
python examples/analyze_llm_logs.py --json
```

**Output includes:**
- Request/response counts
- Timing statistics (avg, median, p95, p99)
- Token usage statistics
- Model distribution
- Error summary
- Slow requests

#### 5. analyze_reflections.py

Analyzes agent reflection logs to understand reasoning processes and decision-making.

**Usage:**

```bash
# Basic analysis
python examples/analyze_reflections.py

# Analyze specific log file
python examples/analyze_reflections.py --log-file logs/agent_reflections.log

# Show reasoning flow for a session
python examples/analyze_reflections.py --session-id session-xyz-789

# Filter by reflection type
python examples/analyze_reflections.py --reflection-type query_analysis

# Output as JSON
python examples/analyze_reflections.py --json
```

**Output includes:**
- Reflection type distribution
- Intent detection patterns
- Tool usage statistics
- Retrieval quality metrics
- Confidence distribution
- Query reformulation examples

## Using jq for Log Analysis

[jq](https://stedolan.github.io/jq/) is a powerful command-line JSON processor. Here are useful examples:

### Basic Queries

```bash
# Pretty-print all log entries
cat logs/llm_interactions.log | jq '.'

# Count total entries
cat logs/llm_interactions.log | wc -l

# Get first 5 entries
cat logs/llm_interactions.log | head -5 | jq '.'
```

### Filtering by Log Type

```bash
# Get all LLM requests
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_request")'

# Get all LLM responses
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_response")'

# Get all errors
cat logs/llm_interactions.log | jq 'select(.data.status=="error")'
```

### Extracting Specific Fields

```bash
# Extract all prompts
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_request") | .data.prompt'

# Extract all response durations
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_response") | .data.duration_seconds'

# Extract model names
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_request") | .data.model'

# Extract token usage
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_response") | .data.token_usage'
```

### Filtering by Conditions

```bash
# Find slow requests (> 5 seconds)
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_response" and .data.duration_seconds > 5)'

# Find requests with high token usage (> 1000 tokens)
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_response" and .data.token_usage.total_tokens > 1000)'

# Find requests to specific model
cat logs/llm_interactions.log | jq 'select(.log_type=="llm_request" and .data.model=="qwen2.5:7b")'

# Find entries for specific session
cat logs/llm_interactions.log | jq 'select(.session_id=="session-xyz-789")'
```

### Correlating Requests and Responses

```bash
# Get request and response for specific request_id
REQUEST_ID="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
cat logs/llm_interactions.log | jq "select(.request_id==\"$REQUEST_ID\")"

# Get all entries for a correlation_id
CORR_ID="query-456"
cat logs/*.log | jq "select(.correlation_id==\"$CORR_ID\")"
```

### Aggregations and Statistics

```bash
# Count requests by model
cat logs/llm_interactions.log | \
  jq 'select(.log_type=="llm_request") | .data.model' | \
  sort | uniq -c

# Calculate average response time
cat logs/llm_interactions.log | \
  jq 'select(.log_type=="llm_response") | .data.duration_seconds' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'

# Calculate total token usage
cat logs/llm_interactions.log | \
  jq 'select(.log_type=="llm_response") | .data.token_usage.total_tokens' | \
  awk '{sum+=$1} END {print "Total tokens:", sum}'

# Count errors by type
cat logs/llm_interactions.log | \
  jq 'select(.data.status=="error") | .data.error' | \
  sort | uniq -c
```

### Agent Reflection Analysis

```bash
# Get all query analyses
cat logs/agent_reflections.log | jq 'select(.data.reflection_type=="query_analysis")'

# Extract detected intents
cat logs/agent_reflections.log | \
  jq 'select(.data.reflection_type=="query_analysis") | .data.detected_intent' | \
  sort | uniq -c

# Get tool decisions
cat logs/agent_reflections.log | jq 'select(.data.reflection_type=="tool_decision")'

# Extract tool names and confidence
cat logs/agent_reflections.log | \
  jq 'select(.data.reflection_type=="tool_decision") | {tool: .data.tool_name, confidence: .data.confidence}'

# Get retrieval evaluations
cat logs/agent_reflections.log | jq 'select(.data.reflection_type=="retrieval_evaluation")'

# Extract retrieval scores
cat logs/agent_reflections.log | \
  jq 'select(.data.reflection_type=="retrieval_evaluation") | .data.top_scores[]'
```

### Time-Based Analysis

```bash
# Get entries from specific date
cat logs/llm_interactions.log | jq 'select(.timestamp | startswith("2025-11-10"))'

# Get entries from last hour (requires date manipulation)
# This is more complex and better done with Python scripts

# Sort by timestamp
cat logs/llm_interactions.log | jq -s 'sort_by(.timestamp)'
```

### Complex Queries

```bash
# Get slow requests with their prompts
cat logs/llm_interactions.log | \
  jq 'select(.log_type=="llm_response" and .data.duration_seconds > 5) | 
      {request_id, duration: .data.duration_seconds, timestamp}'

# Calculate percentiles (requires sorting)
cat logs/llm_interactions.log | \
  jq -s 'map(select(.log_type=="llm_response") | .data.duration_seconds) | sort | 
         {p50: .[length/2|floor], p95: .[length*0.95|floor], p99: .[length*0.99|floor]}'

# Get session summary
SESSION_ID="session-xyz-789"
cat logs/llm_interactions.log | \
  jq -s "map(select(.session_id==\"$SESSION_ID\")) | 
         {count: length, 
          total_duration: map(select(.log_type==\"llm_response\") | .data.duration_seconds) | add,
          total_tokens: map(select(.log_type==\"llm_response\") | .data.token_usage.total_tokens) | add}"
```

### Combining Multiple Log Files

```bash
# Analyze all logs for a session
SESSION_ID="session-xyz-789"
cat logs/*.log | jq "select(.session_id==\"$SESSION_ID\")" | jq -s 'sort_by(.timestamp)'

# Get complete picture of a query
CORR_ID="query-456"
echo "=== LLM Interactions ==="
cat logs/llm_interactions.log | jq "select(.correlation_id==\"$CORR_ID\")"
echo "=== Agent Reflections ==="
cat logs/agent_reflections.log | jq "select(.correlation_id==\"$CORR_ID\")"
echo "=== Context Changes ==="
cat logs/conversation_context.log | jq "select(.session_id==\"$SESSION_ID\")"
```

### Exporting to CSV

```bash
# Export timing data to CSV
echo "request_id,duration,tokens" > timing.csv
cat logs/llm_interactions.log | \
  jq -r 'select(.log_type=="llm_response") | 
         [.request_id, .data.duration_seconds, .data.token_usage.total_tokens] | 
         @csv' >> timing.csv

# Export tool decisions to CSV
echo "timestamp,tool,confidence" > tools.csv
cat logs/agent_reflections.log | \
  jq -r 'select(.data.reflection_type=="tool_decision") | 
         [.timestamp, .data.tool_name, .data.confidence] | 
         @csv' >> tools.csv
```

## Python Analysis Examples

For more complex analysis, use the Python scripts:

### Timing Analysis

```python
from examples.analyze_llm_logs import LLMLogAnalyzer

analyzer = LLMLogAnalyzer("logs/llm_interactions.log")

# Get timing statistics
stats = analyzer.get_timing_stats()
print(f"Average: {stats['avg_duration']:.2f}s")
print(f"P95: {stats['p95_duration']:.2f}s")

# Find slow requests
slow = analyzer.find_slow_requests(threshold=5.0)
for req in slow:
    print(f"{req['request_id']}: {req['duration']:.2f}s")
```

### Token Usage Analysis

```python
from examples.analyze_llm_logs import LLMLogAnalyzer

analyzer = LLMLogAnalyzer("logs/llm_interactions.log")

# Get token statistics
tokens = analyzer.get_token_stats()
print(f"Total tokens: {tokens['total_tokens']:,}")
print(f"Average per request: {tokens['avg_total_tokens']:.0f}")
```

### Reflection Analysis

```python
from examples.analyze_reflections import ReflectionLogAnalyzer

analyzer = ReflectionLogAnalyzer("logs/agent_reflections.log")

# Get intent distribution
intents = analyzer.get_intent_distribution()
for intent, count in intents.items():
    print(f"{intent}: {count}")

# Get tool usage
tools = analyzer.get_tool_usage_stats()
for tool, count in tools['tool_counts'].items():
    conf = tools['avg_confidence'][tool]
    print(f"{tool}: {count} times (confidence: {conf:.2f})")
```

### Session Flow Analysis

```python
from examples.analyze_reflections import ReflectionLogAnalyzer

analyzer = ReflectionLogAnalyzer("logs/agent_reflections.log")

# Print reasoning flow for a session
analyzer.print_session_flow("session-xyz-789")
```

## Tips and Best Practices

1. **Use jq for quick queries**: Great for one-off analysis and exploration
2. **Use Python scripts for complex analysis**: Better for statistics, aggregations, and reports
3. **Combine tools**: Use jq to filter, then pipe to Python for processing
4. **Save useful queries**: Create shell scripts for frequently-used queries
5. **Use correlation IDs**: Track related operations across multiple log files
6. **Monitor in real-time**: Use `tail -f` with jq for live monitoring

## Real-Time Monitoring

```bash
# Watch LLM interactions
tail -f logs/llm_interactions.log | jq '.'

# Watch only responses
tail -f logs/llm_interactions.log | jq 'select(.log_type=="llm_response")'

# Watch slow requests
tail -f logs/llm_interactions.log | \
  jq 'select(.log_type=="llm_response" and .data.duration_seconds > 5)'

# Watch errors
tail -f logs/llm_interactions.log | jq 'select(.data.status=="error")'

# Watch agent reasoning
tail -f logs/agent_reflections.log | jq '.'
```

## Troubleshooting

### Invalid JSON errors

If you get JSON parsing errors:

```bash
# Find invalid JSON lines
cat logs/llm_interactions.log | while read line; do
    echo "$line" | jq . > /dev/null 2>&1 || echo "Invalid: $line"
done

# Skip invalid lines
cat logs/llm_interactions.log | jq -R 'fromjson? | select(. != null)'
```

### Large log files

For very large log files:

```bash
# Process in chunks
split -l 10000 logs/llm_interactions.log chunk_
for file in chunk_*; do
    cat $file | jq '...' >> results.json
done

# Use grep to pre-filter
grep "session-xyz" logs/llm_interactions.log | jq '.'

# Sample random entries
shuf -n 100 logs/llm_interactions.log | jq '.'
```

## Further Reading

- [jq Manual](https://stedolan.github.io/jq/manual/)
- [Enhanced Logging Guide](../docs/enhanced_logging.md)
- [RAG5 Documentation](../README.md)
