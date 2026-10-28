# M-ARCH Architecture Specification

## Overview

M-ARCH is a local-first, evidence-backed software project review platform designed to systematically inspect, evaluate, and verify software repositories using multi-agent reasoning, Retrieval-Augmented Generation (RAG), the Agent-to-Agent (A2A) protocol, and the Model Context Protocol (MCP).

## System Architecture

```mermaid
graph TD
    UI["Next.js Frontend (App Router, Space Grotesk / Mono)"] --> |HTTP / SSE| API["FastAPI Backend (v1 REST)"]
    
    subgraph "Backend Application"
        API --> DB[(SQLite / FTS5 + Async SQLAlchemy)]
        API --> VEC[(Persistent Local Vector Store)]
        API --> ORCH["Orchestrator Agent"]
        
        subgraph "A2A Protocol Layer"
            ORCH --> |A2A Task Request| C_AGENT["Code & Testing Agent"]
            ORCH --> |A2A Task Request| S_AGENT["Security Agent"]
            ORCH --> |A2A Task Request| D_AGENT["Documentation Agent"]
            
            C_AGENT --> |Structured Artifact| ORCH
            S_AGENT --> |Structured Artifact| ORCH
            D_AGENT --> |Structured Artifact| ORCH
        end
        
        subgraph "Model Context Protocol (MCP) Server"
            TOOLS["Read-Only Project Tools & Resources"]
            C_AGENT --> |MCP Tool Call| TOOLS
            S_AGENT --> |MCP Tool Call| TOOLS
            D_AGENT --> |MCP Tool Call| TOOLS
        end
        
        subgraph "RAG Engine"
            INGEST["Ingestion & Safe Extractor"] --> CHUNK["Semantic & Code Chunker"]
            CHUNK --> EMBED["Local Embedding Pipeline"]
            EMBED --> VEC
            CHUNK --> FTS["SQLite FTS5 Full-Text Index"]
            RETRIEVE["Hybrid Retriever (Dense + FTS5 + RRF Fusion)"] --> TOOLS
        end
        
        subgraph "Model Inference Routing"
            ROUTER["Provider Router (Auto / Groq / Ollama / Hybrid)"]
            ROUTER --> REDACT["Secret Redactor"]
            REDACT --> GROQ["Groq Cloud Inference"]
            ROUTER --> OLLAMA["Local Ollama Inference"]
        end
        
        C_AGENT --> ROUTER
        S_AGENT --> ROUTER
        D_AGENT --> ROUTER
        ORCH --> ROUTER
    end
```

## Core Tenets

1. **Evidence-First Verification**: Every finding references specific chunk IDs, source line numbers, and exact supporting code excerpts.
2. **A2A & MCP Compliance**: Genuine Agent-to-Agent task distribution and Model Context Protocol tool execution.
3. **Safe Execution**: Never executes uploaded project code, scripts, or tests.
4. **Resilient Provider Modes**: Local Ollama support, Groq cloud acceleration, Auto fallback with exponential backoff, and Hybrid task routing.
5. **Data Protection**: Secrets are detected and redacted before any cloud LLM invocation.
