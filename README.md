# M-ARCH: Multi-Agent Retrieval-Augmented Generation Framework Using A2A and MCP

M-ARCH is a local-first, evidence-backed software project review platform. It dispatches specialized agents across your codebase and documentation, executing A2A communication, RAG hybrid retrieval, and strictly read-only MCP tools to produce verifiable, reproducible engineering reports.

## Key Features

- **Evidence-Backed Findings**: Every finding is linked to exact source files, lines, and chunks.
- **A2A Multi-Agent Collaboration**: Orchestrator, Code & Testing, Security, and Documentation specialists communicate via formal A2A protocols and structured artifacts.
- **Model Context Protocol (MCP)**: Agents access read-only tools and resources through standard MCP interfaces.
- **Resilient AI Routing**: Seamlessly switch between local Ollama (`qwen2.5-coder:7b`) and Groq cloud inference (`llama-3.3-70b-versatile`) with automatic fallback.
- **Privacy & Secret Redaction**: High-entropy strings and credentials are automatically stripped before optional cloud queries.
- **Apple HIG + Medusa Aesthetic**: Calm, high-density, precise dark/light interface built with Next.js App Router, Space Grotesk, and Space Mono.

## Quick Start

### 1. Configure Local Models
```powershell
ollama pull qwen2.5-coder:7b
```

### 2. Configure Backend
```powershell
cd backend
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```

### 3. Start Frontend
```powershell
cd frontend
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to start reviewing projects.
