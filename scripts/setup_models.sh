#!/bin/bash

# Setup script for RAG5 Simplified System
# This script pulls the required Ollama models

set -e  # Exit on error

echo "================================================================================"
echo "RAG5 Simplified System - Model Setup"
echo "================================================================================"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Error: Ollama is not installed"
    echo ""
    echo "Please install Ollama first:"
    echo "  - macOS/Linux: https://ollama.ai/download"
    echo "  - Or use: curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    exit 1
fi

echo "✅ Ollama is installed"
echo ""

# Check if Ollama service is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama service is not running"
    echo ""
    echo "Please start Ollama in another terminal:"
    echo "  ollama serve"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Ollama service is running"
echo ""

# Pull LLM model
echo "📥 Pulling LLM model: qwen2.5:7b"
echo "   (This may take several minutes depending on your internet connection)"
echo ""
ollama pull qwen2.5:7b

echo ""
echo "✅ LLM model downloaded"
echo ""

# Pull embedding model
echo "📥 Pulling embedding model: bge-m3"
echo "   (This may take a few minutes)"
echo ""
ollama pull bge-m3

echo ""
echo "✅ Embedding model downloaded"
echo ""

# List installed models
echo "================================================================================"
echo "Installed Models:"
echo "================================================================================"
ollama list

echo ""
echo "================================================================================"
echo "✅ Setup Complete!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant"
echo "  2. Configure environment: cp .env.example .env"
echo "  3. Ingest documents: python ingest.py data/"
echo "  4. Run the UI: streamlit run ui.py"
echo ""
