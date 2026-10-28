# M-ARCH Privacy & Data Security

## Privacy Guarantees

1. **Local-First Processing**: In `Ollama` mode, 100% of code parsing, text extraction, embeddings, vector search, and model inference occurs strictly on your local machine. No code leaves localhost.
2. **Secret Redaction**: When `Groq`, `Auto`, or `Hybrid` cloud modes are enabled, M-ARCH runs an automated regex and entropy-based pre-flight redactor over retrieved code chunks before dispatching excerpts to Groq API.
3. **No Execution Guarantee**: M-ARCH conducts static parsing and structural inspection only. It will never run `npm install`, execute build scripts, run test suites, or execute code.
4. **Credential Isolation**: API keys reside exclusively in backend environment variables (`.env`). They are excluded from git, excluded from API responses, and never printed to console logs or stored in the database.
5. **Data Ownership & Deletion**: Projects, sources, chunks, embeddings, findings, and evaluation runs are saved in your local SQLite and vector store directories. Deleting a project permanently purges all associated files, vectors, and records.
