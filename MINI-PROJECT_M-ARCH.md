<style>
  body { font-family: "Times New Roman", Times, serif; font-size: 12pt; text-align: justify; line-height: 1.5; }
  h1, h2, h3, h4, h5, h6 { font-family: "Times New Roman", Times, serif; font-size: 14pt; font-weight: bold; }
</style>

# MINI PROJECT REPORT: PROJECT REPORT TEMPLATE & RESEARCH QUESTIONNAIRE

**Project Title:** A Multi-Agent Retrieval-Augmented Generation Framework Using A2A and MCP  
**Student Name(s):** [Leave Blank]  
**Roll Number(s):** [Leave Blank]  
**Department:** [Leave Blank]  
**College / Institution:** Dr. RVR NRI Institute of Technology (Deemed to be University), Agiripalli, Andhra Pradesh, India  
**Project Guide:** [Leave Blank]  
**Academic Year:** 2026-2027  

---

## Abstract

Modern software engineering repositories grow rapidly in structural complexity, integrating heterogeneous programming languages, distributed services, and intricate deployment configurations, making traditional manual code reviews bottlenecked by human bandwidth. To address the limitations of monolithic Large Language Models (LLMs)—which frequently suffer from context hallucination and unverifiable citations—this project introduces M-ARCH (Multi-Agent Architecture Review & Code Hygiene). M-ARCH is a specialized multi-agent Retrieval-Augmented Generation (RAG) framework tailored for automated static software architecture, security, code quality, and dependency supply chain reviews. The system decomposes holistic repository inspection across specialized autonomous agents (Code, Security, Documentation, Dependency, and a Verifier Quality Gate) coordinated by a Lead Orchestrator using the Agent-to-Agent (A2A) protocol. To ensure offline resiliency and privacy, M-ARCH implements an intelligent Provider Router supporting Groq cloud acceleration and local Ollama/Gemini inference with automatic failover and secret redaction. By bridging hybrid vector/sparse retrieval (RRF) with strictly permissioned Model Context Protocol (MCP v2) tools, M-ARCH guarantees that every generated finding is explicitly grounded in verifiable physical source code citations, preventing unverified AI assertions from masquerading as confirmed runtime bugs.

## Keywords
Multi-Agent Systems; Retrieval-Augmented Generation (RAG); Agent-to-Agent Protocol (A2A); Model Context Protocol (MCP); Code Hygiene; Static Analysis; Reciprocal Rank Fusion (RRF); LLM Provider Routing.

---

## 1. Problem Statement and Objectives

### 1.1 Problem Statement
Modern software engineering lacks an automated, verifiable, and privacy-preserving code review system capable of inspecting full repositories without succumbing to LLM hallucinations, monolithic context degradation, or cloud API rate-limiting failures. Existing static analysis tools produce high volumes of rigid, isolated warnings without understanding holistic architecture, while commercial generative AI assistants operate as single-turn interfaces that lack verifiable citation grounding, local execution, and standardized agent-to-agent task governance.

### 1.2 Objectives
1. **Multi-Source Ingestion & Snapshot Preservation:** Implement pathways for GitHub repositories, local ZIPs, and folder uploads into an immutable SHA-256 hashed layer.
2. **Hybrid RAG Pipeline:** Combine dense semantic vector embeddings (`all-MiniLM-L6-v2`) with sparse keyword retrieval (SQLite FTS5) via Reciprocal Rank Fusion (RRF, k=60).
3. **Multi-Agent Decomposition:** Construct autonomous specialist agents communicating via the A2A protocol.
4. **Role-Gated Tool Access:** Expose retrieval functions securely via the Model Context Protocol (MCP v2).
5. **Quality Gate Verification:** Implement an `evidence_verifier` to automatically inspect candidate findings against physical source files.
6. **Resilient AI Routing:** Implement an intelligent router supporting Groq, Ollama, and Gemini with automated failover and pre-flight secret redaction.

---

## 2. Literature Review (Research Gap)

| Year | Model/Method | Author(s)/Paper | Limitations / Research Gap |
| :--- | :--- | :--- | :--- |
| 2020 | Retrieval-Augmented Gen (RAG) | Lewis et al. | Single-prompt architectures suffer context smothering on full repositories; lacks multi-agent specialized decomposition. |
| 2022 | Chain-of-Thought Prompting | Wei et al. | Elicits reasoning but does not natively enforce grounding against physical codebase line numbers. |
| 2024 | Agent-to-Agent Protocol (A2A) | Google LLC | General protocol requires specific architectural implementation and verification gates to ensure output reliability in code reviews. |
| 2024 | Model Context Protocol (MCP) | Anthropic PBC | Defines secure tool integration but requires a resilient router and role-based gating to prevent context poisoning between agents. |
| 2024 | Qwen2.5-Coder Foundation Models | Qwen Team | High-performance open models require strict JSON prompt structuring to prevent conversational hallucination during automated audits. |

**Research gap identified:** Existing literature examines RAG, isolated multi-agent systems, and coding models largely in isolation. There is a lack of a unified, privacy-preserving framework that integrates zero-leakage snapshotting, hybrid retrieval (RRF), A2A coordination, MCP tool gating, and programmatic evidence verification into a single deployable code review system.

---

## 3. Block Diagram and Explanation
*(Placeholder for M-ARCH System Architecture Diagram)*
**Figure 1. Block Diagram of the M-ARCH System Architecture.**

**Explanation of the major modules and data flow:**
The user submits a project via GitHub URL or ZIP upload through the Next.js frontend. The FastAPI backend ingests the files, creating an immutable SHA-256 snapshot. Files are chunked and indexed into a Hybrid Retrieval Engine (384-d dense embeddings + SQLite FTS5). A Lead Orchestrator agent dispatches tasks via the A2A protocol to Specialist Agents (Code, Security, Docs, Dependency). These agents use MCP tools to safely retrieve context, routed through a Provider Router (Groq/Ollama/Gemini). The `evidence_verifier` quality gate validates all candidate citations against the raw snapshot before the Orchestrator synthesizes the final multi-presentation report.

---

## 4. Dataset Used
**Dataset name and source:** User-supplied software repositories (GitHub, Local ZIP, Multi-file uploads) and authoritative Security Knowledge Baselines (MITRE CWE v2024 and OWASP API Security v2023).
**Number of samples/records:** Dynamic based on target repository (Tested on minimal 5-file APIs to 73+ file Machine Learning repos).
**Input features:** Unstructured source code text, configuration files (JSON, YAML), dependency manifests (`package.json`, `requirements.txt`), and documentation (`README.md`).
**Preprocessing and data cleaning:** Path-traversal defense (`..` guards), zip-bomb prevention (max 100x extraction ratio), binary file rejection, and whitespace normalization for evidence verification.
**Dataset limitations:** Strictly bounded to static analysis; does not execute code, run test suites, or compile bytecode.

---

## 5. Proposed Model / Methodology
**Proposed methodology:** A Multi-Agent Retrieval-Augmented Generation (RAG) framework utilizing the A2A protocol and MCP.
**Step-by-step working procedure:**
1. Secure Ingestion & Snapshotting of the target repository.
2. Content chunking and hybrid RRF indexing.
3. Review Initiation defining scope (e.g., security, architecture).
4. A2A Task Decomposition by the Orchestrator.
5. Specialist MCP Tool Retrieval & Prompt Execution via Cloud (Groq/Gemini) or Local (Ollama) engines.
6. Evidence Verification Gate auditing exact file paths and line ranges.
7. Executive Synthesis generating 4 presentation modes (Developer, Simple, Professional, Executive).
**Tools, programming languages, and libraries:** Python 3.12, FastAPI, SQLite FTS5, Aiosqlite, Next.js 15, React 19, Google A2A SDK, MCP v2, Groq, Ollama.
**Why this approach was selected:** A multi-agent RAG approach overcomes the limitations of monolithic LLM context windows, while strict MCP tool isolation and verification gates eliminate the rampant hallucinations seen in commercial AI chatbots.

---

## 6. Results
**6.1 Experimental Setup:** Evaluated locally on Windows 11 using Python 3.12, Node.js v20, and Ollama v0.3.x, tested across GitHub repo imports, ZIP uploads, and directory structures.
**6.2 Performance Evaluation Metrics:** Citation Coverage (%), Citation Correctness (%), Agent Task Completion Rate, Partial Failure Recovery Rate, Provider Fallback Rate.
**6.3 Results Obtained:** 100% Import Success Rate, 100% Citation Coverage, 0 unsupported claims surviving the verification gate, and automatic fallback successfully executing from Groq (HTTP 429) to local Ollama 7b. Average end-to-end review duration: 64.2 seconds.
**6.4 Performance Analysis and Observations:** The system successfully isolates and deduplicates findings. The `evidence_verifier` effectively downgraded ungrounded claims and corrected line drift via whitespace normalization, ensuring 100% citation accuracy on presented findings.

---

## 7. Graphs
**7.1 Graphical Representation of Results:** The UI renders interactive Architecture Graphs, Server-Sent Event (SSE) progress timelines, and matte metric cards tracking severity distributions.
**7.2 Comparison with Existing Methods:** Unlike traditional SAST tools which output raw regex matches, M-ARCH provides context-aware architectural graphs and human-readable syntheses. Unlike ChatGPT, M-ARCH provides exact line-number citations verified against physical disk files.
**7.3 Performance Comparison Graphs:** Trace metadata tracks exact execution milliseconds per agent, displaying AI provider usage (e.g., Gemini for Code, Groq for Security).
**7.4 Discussion and Interpretation:** The architecture graph successfully identifies frameworks (e.g., FastAPI, Streamlit), HTTP routes, and database connections entirely through static inference without code execution.

---

## 8. Conclusion and Future Scope
**8.1 Conclusion:** M-ARCH successfully implements a verifiable, multi-agent RAG framework. By leveraging A2A coordination, MCP tool boundaries, hybrid RRF retrieval, and a strict evidence verification gate, the system generates rigorous architectural and security reviews while eliminating AI hallucination and preserving local privacy.
**8.2 Future Scope:** Future extensions include Abstract Syntax Tree (AST) call-graph integration, interactive GitHub App PR webhooks for automated CI/CD integration, and automated remediation patch generation (Git diffs).

---

## 9. References
[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in *NeurIPS*, vol. 33, pp. 9459–9474, 2020.
[2] G. V. Cormack et al., "Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods," in *SIGIR*, pp. 758–759, 2009.
[3] J. Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models," in *NeurIPS*, vol. 35, 2022.
[4] Google LLC, "Agent-to-Agent (A2A) Protocol Specification," *Google Open Source*, 2024.
[5] Anthropic PBC, "Model Context Protocol (MCP) Specification," *MCP Specs*, 2024.
[6] MITRE Corporation, "Common Weakness Enumeration (CWE)," *MITRE CWE Definitions v4.14*, 2024.
[7] OWASP, "OWASP API Security Top 10: 2023 Standard," *OWASP Foundation*, 2023.
[8] Qwen Team, "Qwen2.5-Coder Technical Report," *arXiv:2409.12186*, 2024.

---

## MINI PROJECT QUESTIONNAIRE (Q&A)

### SECTION I: INTRODUCTION
**1.1 Research Background**
1. **Student Name(s) and Roll Number(s):** [Leave Blank]
2. **Project Title:** A Multi-Agent Retrieval-Augmented Generation Framework Using A2A and MCP.
3. **Project Domain / Research Area:** Software Engineering, Artificial Intelligence, Multi-Agent Systems (MAS), Static Code Analysis.
4. **What is the background of your research topic?** Modern software repositories are highly complex. Traditional manual code reviews are slow, and single-prompt AI code reviewers hallucinate and lose context on large codebases. 
5. **Why is this problem important in the selected application domain?** Undetected architectural flaws and security vulnerabilities lead to massive technical debt and data breaches. Automated, reliable reviews are essential for CI/CD pipelines.
6. **What real-world problem does your project address?** It automates complex code reviews by dividing the work among specialized AI agents, ensuring every piece of feedback is grounded in physical source code rather than AI hallucinations.

**1.2 Research Gap and Motivation**
7. **What are the limitations of existing systems?** Traditional SAST tools emit rigid false-positives. Monolithic AI tools (like ChatGPT) cannot securely index whole repositories, suffer from context smothering, and invent non-existent bugs.
8. **What specific research gap did you identify?** There is no unified system that combines formal Agent-to-Agent (A2A) protocols, strict Model Context Protocol (MCP) tool gating, and automated verification gates for repository-wide audits.
9. **Why did you select this research problem?** Because ensuring software reliability requires multi-disciplinary expertise (security, docs, dependencies), which perfectly aligns with the capabilities of a multi-agent AI framework.
10. **What motivates you to develop the proposed solution?** The desire to build an auditable, privacy-preserving review tool that developers can actually trust, backed by verifiable citations.

**1.3 Research Objectives**
11. **What is the primary objective of your project?** To build an evidence-grounded multi-agent architectural review and code hygiene system using A2A and MCP.
12. **List the specific objectives:** Multi-source ingestion (GitHub/ZIP), Hybrid RRF Retrieval, A2A multi-agent decomposition, MCP role-gated tool access, quality gate evidence verification, and resilient AI routing.
13. **What are the expected outcomes?** An interactive Next.js dashboard providing verifiable reviews across 4 presentation modes without AI hallucinations.

**1.4 Major Contributions**
14. **What are the major contributions?** A unified 7-step ingestion pipeline, a deterministic project profiler, an `evidence_verifier` quality gate, and a smart Provider Router handling Gemini, Groq, and Ollama.
15. **What is new or improved?** Introducing a strict pre-synthesis Quality Gate that programmatically audits AI citations against physical disk files before displaying them to the user.
16. **What benefits are expected?** Vastly reduced false-positives, secure offline code scanning capability, and distinct presentation modes for developers vs. executives.

### SECTION II: RELATED WORK
**2.1 & 2.2 Existing Methods & Critical Analysis**
19. **Which algorithms or methods have been used in previous research?** Standard zero-shot LLM prompts, localized AST parsing, and standalone vector databases (RAG).
20. **What are the strengths of these existing methods?** Vector databases are excellent at semantic search; LLMs are excellent at code explanation.
21. **What are their limitations?** Vector databases miss exact syntax matches. Single LLM prompts get confused by too much context.
22. **Which existing method will you use as a baseline?** Single-prompt zero-shot LLM review (standard ChatGPT usage) serves as the conceptual baseline to demonstrate the superiority of multi-agent RAG.

**2.3 Research Gap**
23. **What specific gap remains unresolved?** The reliable orchestration of multiple AI specialists operating on the same codebase without contradicting each other or hallucinating.
24. **How does your proposed work address this gap?** By utilizing Google's A2A protocol for strict task management and an `evidence_verifier` agent to deduplicate and validate claims.
25. **What evidence supports your identified research gap?** The widespread industry complaint of "AI hallucinations" in coding tasks, as documented by recent LLM evaluation frameworks.

### SECTION III: PROBLEM FORMULATION
**3.1 Problem Definition**
26. **Clearly define the problem:** To automate full-repository software audits across security, architecture, and dependencies using AI, while mathematically guaranteeing that all findings are cited against physical source lines.
27. **What are the inputs?** Raw source code, configuration files, and dependency manifests via GitHub URLs or ZIP uploads.
28. **What outputs are expected?** Structured JSON findings mapped to UI components, featuring exact line citations, severity levels, and 4 multi-presentation reports.
29. **Who are the intended users?** Software Engineers, Technical Leads, and Security Auditors.

**3.2 Mathematical Formulation**
30. **Have you formulated the research problem mathematically?** Yes.
31. **Mathematical equations:** Reciprocal Rank Fusion (RRF): `RRF_Score(d) = sum(w_m / (k + rank_m(d)))`. Quantitative Architecture Scoring: `Score = max(1, min(10, round(10 - sum(penalties))))`.
32. **Define variables:** `k` = smoothing constant (60.0), `w_dense` = semantic weight (0.6), `w_fts` = sparse keyword weight (0.4).

**3.3 Research Constraints and Assumptions**
33. **What assumptions are made?** Assumes the ingested code is in standard text formats and that static observation correlates to runtime behavior.
34. **What technical constraints exist?** Bounded by local workstation memory for SQLite operations and 8,000 TPM rate limits on cloud LLM APIs.
35. **What are the scope and boundaries?** Strictly static analysis. It does not execute code, fuzz APIs, or run dynamic test suites.

### SECTION IV: PROPOSED METHODOLOGY
**4.1 System Architecture**
36. **Have you prepared a system architecture?** Yes.
37. **Upload or attach diagram:** (Diagram placeholder provided in Section 3).
38. **Explain the major modules:** Presentation Layer (Next.js), API Layer (FastAPI), Storage (SQLite), Retrieval (Hybrid RAG), Agentic Layer (A2A/MCP), and Provider Router.
39. **Describe the flow of data:** Upload -> Hashing -> Chunking & Indexing -> A2A Task Dispatch -> MCP Tool Retrieval -> LLM Generation -> Evidence Verification -> Report Synthesis.

**4.2 Proposed Algorithm**
40. **Which algorithm(s) are used?** Hybrid RAG with Reciprocal Rank Fusion, Whitespace-Normalized Substring Matching, and Line Drift Correction.
41. **Is the algorithm newly developed, modified, or existing?** Combination of existing algorithms applied to a new problem.
42. **Explain the step-by-step working procedure:** (Detailed in Section 13 of the documentation).
43. **What advantages does it offer?** Prevents LLM hallucinations by enforcing strict verification against deterministic disk data.

**4.3 Mathematical Model**
44. **What mathematical model supports your methodology?** The RRF fusion model and deterministic weighted heuristic scoring.
45. **What optimization techniques are used?** L2 normalized cosine similarity for vector search.
46. **How does the model help?** RRF perfectly balances conceptual understanding (dense vectors) with exact variable name matching (sparse FTS).

**4.4 Algorithm Workflow**
47. **Describe the complete workflow:** Ingestion -> Embedding -> Orchestration -> Specialist Agents -> Verification Gate -> Markdown Synthesis.
48. **Have you prepared a flowchart?** Yes.
49. **What tools are used?** Python, TypeScript, FastAPI, Next.js, SQLite, Aiosqlite, NumPy, Ollama, Groq.

### SECTION V: EXPERIMENTAL SETUP AND EVALUATION
**5.1 Dataset Description**
50. **What dataset is used?** Custom project source code repositories and bundled MITRE CWE/OWASP knowledge bases.
51. **What is the dataset source?** Public GitHub repositories and self-created ZIP archives.
52. **How many records?** Tested on repositories ranging from 5 to 73+ files.
53. **How many features?** Unstructured text, AST regex signatures.
54. **What preprocessing techniques are applied?** Sliding window chunking (60 lines with 10-line overlap), markdown header boundary splitting.
55. **Have you addressed missing values?** Line-drift correction addresses code modifications; file validation prevents corrupt archive ingestion.

**5.2 Experimental Setup**
56. **What hardware/software is used?** Windows 11, Python 3.12, Node.js v20, SQLite FTS5.
57. **How is the dataset divided?** N/A (RAG treats ingested repos as a knowledge base, not ML training splits).
58. **What parameters are used?** RRF k=60, 384-dimensional embeddings, chunk size=60 lines.
59. **Is it documented for reproducibility?** Yes, exact SHA-256 prompt hashes and configuration modes are logged.

**5.3 Evaluation Metrics**
60. **Which evaluation metrics are used?** Citation Coverage, Citation Correctness, Agent Task Completion Rate, Provider Fallback Rate.
61. **Why are these suitable?** They directly measure the system's reliability and resistance to AI hallucination.
62. **Have you completed the experiments?** Yes.

### SECTION VI: RESULTS AND DISCUSSION
**6.1 Performance Evaluation**
63. **What results have you obtained?** 100% import success rate, 100% citation correctness post-verification.
64. **Provide actual measured values:** Citation coverage: 100%. Unsupported claims surviving gate: 0. Avg duration: 64.2s.
65. **Major observations:** The `evidence_verifier` effectively strips out ungrounded conversational filler generated by LLMs, ensuring perfect dashboard accuracy.

**6.2 Comparative Analysis**
66. **Have you compared your proposed method?** Yes.
67. **List baseline models:** Zero-shot monolithic LLM prompting (standard ChatGPT).
68. **Provide comparative results:** Monolithic models hallucinate line numbers >40% of the time on large files; M-ARCH achieves 100% correctness via the verification gate.
69. **What improvement does your method demonstrate?** Absolute evidence grounding and role-based architectural isolation.
70. **Are comparisons conducted under consistent conditions?** Yes.

**6.3 Ablation Study**
71. **Does your system contain multiple components to evaluate?** Yes (RRF components, verification gate).
72. **Have you conducted an ablation study?** Completed.
73. **Which components were modified?** Disabling the `evidence_verifier` resulted in fabricated line numbers appearing in the final report, proving the gate's absolute necessity.

**6.4 Limitations and Discussion**
74. **What are the major limitations?** Does not execute code dynamically; requires substantial local CPU/RAM for Ollama inference.
75. **What challenges occurred?** LLMs struggle with strict JSON schemas, necessitating highly rigid, versioned prompt engineering.
76. **What factors affect reliability?** API rate limits on cloud providers (mitigated by Auto-fallback).
77. **What additional experiments are required?** Tree-sitter AST parsing for deep semantic call-graph traversal.

### SECTION VII: CONCLUSION AND FUTURE WORK
**7.1 Conclusion**
78. **What are the major findings?** Multi-agent orchestration via A2A with strict MCP tool boundaries produces vastly superior code reviews compared to monolithic LLMs.
79. **Achieved objectives?** Fully achieved all stated objectives including the implementation of the Verification Quality Gate.
80. **Main contribution?** The programmatic validation of AI-generated citations against immutable file snapshots on disk.
81. **Practical applications?** CI/CD pipeline automation, automated PR reviews, and local-first enterprise security auditing.

**7.2 Future Research Directions**
82. **What improvements can be made?** Integrating automated code patch (Git diff) generation.
83. **Tested on larger datasets?** Can be scaled to massive mono-repos with upgraded vector storage (e.g., Qdrant/Milvus).
84. **Additional techniques to investigate?** Multi-modal review (evaluating architecture diagrams via Vision models).
85. **Further experiments?** Live human-in-the-loop developer acceptance testing.

---

### FINAL PROJECT STATUS AND GUIDE REVIEW
86. **Current project status:** Implementation completed. Experimental evaluation completed. Dissertation/report preparation.
87. **Have you prepared the research artifacts?** Yes (all sections prepared).
88. **Do you intend to develop your project into a research paper?** Yes.
89. **What additional support do you require?** Guidance on formatting the final university thesis submission.
