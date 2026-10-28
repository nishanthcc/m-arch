# M-ARCH API Reference

All API routes are prefixed under `/api/v1`.

### Health & Provider
- `GET /api/v1/health` - Backend and database health
- `GET /api/v1/settings/providers` - Status of Groq and Ollama connections (without exposing secrets)

### Projects & Sources
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects/{id}` - Get project details
- `DELETE /api/v1/projects/{id}` - Delete project and all associated vectors/records
- `POST /api/v1/projects/{id}/sources` - Upload files or repository zip
- `GET /api/v1/projects/{id}/sources/{source_id}` - Get source details
- `DELETE /api/v1/projects/{id}/sources/{source_id}` - Delete a source
- `POST /api/v1/projects/{id}/index` - Index ingested sources into FTS5 and vector store
- `GET /api/v1/projects/{id}/index/status` - Current indexing progress

### Reviews & Streaming Events
- `POST /api/v1/reviews` - Start a new multi-agent review
- `GET /api/v1/reviews` - List reviews
- `GET /api/v1/reviews/{id}` - Review status, orchestrator summary, agent findings
- `GET /api/v1/reviews/{id}/events` - Server-Sent Events (SSE) live progress stream
- `GET /api/v1/reviews/{id}/findings` - Filterable findings list
- `GET /api/v1/reviews/{id}/report` - Exportable Markdown / HTML review report

### Agents & MCP
- `GET /api/v1/agents` - List registered A2A agents, Agent Cards, and allowed MCP tools
- `GET /api/v1/agents/{id}/health` - Individual agent status

### Settings & Evaluations
- `GET /api/v1/settings` - Current application settings
- `PATCH /api/v1/settings` - Update model provider, weights, or thresholds
- `GET /api/v1/evaluations` - List evaluation runs
- `POST /api/v1/evaluations/datasets` - Upload custom evaluation dataset
- `POST /api/v1/evaluations/runs` - Execute evaluation benchmark run
- `GET /api/v1/evaluations/runs/{id}` - Evaluation run results and metrics
