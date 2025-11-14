# Knowledge Base Management Examples

This directory contains example scripts demonstrating various knowledge base management features.

## 🎯 Examples Overview

| Example | Description | Lines | Difficulty | Time |
|---------|-------------|-------|------------|------|
| `basic_usage.py` | Basic KB operations (create, upload, query) | ~250 | Beginner | 5 min |
| `multi_domain.py` | Multiple KBs for different domains | ~400 | Intermediate | 10 min |
| `multi_language.py` | Multi-language knowledge bases | ~350 | Intermediate | 10 min |
| `advanced_config.py` | Advanced configuration options | ~450 | Advanced | 15 min |
| `batch_operations.py` | Batch file processing | ~400 | Intermediate | 10 min |
| `monitoring.py` | Performance monitoring and statistics | ~500 | Advanced | 15 min |

**Total:** 6 examples, ~2,350 lines of code

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start required services:
   ```bash
   # Start Qdrant
   docker run -p 6333:6333 qdrant/qdrant
   
   # Start Ollama
   ollama serve
   ```

3. Pull embedding models:
   ```bash
   ollama pull nomic-embed-text
   ollama pull bge-m3
   ```

4. Initialize the database:
   ```bash
   python -m scripts.migrate_kb --create-default
   ```

## Running Examples

Each example can be run independently:

```bash
# Basic usage
python examples/kb_management/basic_usage.py

# Multi-domain
python examples/kb_management/multi_domain.py

# Multi-language
python examples/kb_management/multi_language.py

# Advanced configuration
python examples/kb_management/advanced_config.py

# Batch operations
python examples/kb_management/batch_operations.py

# Monitoring
python examples/kb_management/monitoring.py
```

## Example Data

Some examples require sample documents. You can:

1. Use your own documents
2. Create sample files:
   ```bash
   mkdir -p test_data
   echo "Sample document content" > test_data/sample.txt
   ```

## Customization

All examples can be customized by modifying:
- File paths
- Knowledge base names
- Configuration parameters
- Embedding models

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Make sure you're in the project root
cd /path/to/rag5-simplified
python examples/kb_management/basic_usage.py
```

**Connection errors:**
```bash
# Check Qdrant is running
curl http://localhost:6333/health

# Check Ollama is running
curl http://localhost:11434/api/tags
```

**Database errors:**
```bash
# Reinitialize database
python -m scripts.migrate_kb --create-default
```

## Learning Path

Recommended order for learning:

1. **Start with `basic_usage.py`**
   - Learn fundamental operations
   - Understand the workflow

2. **Try `multi_domain.py`**
   - Learn about KB isolation
   - Understand use cases

3. **Explore `advanced_config.py`**
   - Learn configuration options
   - Understand trade-offs

4. **Practice with `batch_operations.py`**
   - Learn efficient processing
   - Handle multiple files

5. **Monitor with `monitoring.py`**
   - Learn performance tracking
   - Understand metrics

## Additional Resources

- [Main Documentation](../../docs/KNOWLEDGE_BASE_MANAGEMENT.md)
- [CLI Guide](../../scripts/KB_CLI_README.md)
- [API Guide](../../docs/KB_API_USAGE.md)
- [Configuration Guide](../../docs/KB_CONFIGURATION.md)

## Contributing

Have a useful example? Contributions are welcome!

1. Create your example script
2. Add documentation
3. Test thoroughly
4. Submit a pull request
