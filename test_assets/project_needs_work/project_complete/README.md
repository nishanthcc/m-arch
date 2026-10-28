# User Management Gateway (Complete Candidate)

Production-ready microservice providing secure user profile lookups and arithmetic operations.

## Architecture & Security Highlights
- **Zero Hardcoded Credentials:** All credentials and environment configs are read via `os.getenv`.
- **Injection Resilient:** Parameterized endpoints and strict Pydantic schemas eliminate SQL and Code Injection (CWE-89, CWE-94).
- **Restricted CORS:** Bound to explicit domain allowlists rather than wildcards.
- **Automated Test Coverage:** Includes unit and integration test suites in `tests/`.

## Prerequisites
- Python 3.10+
- Virtual environment (`venv`)

## Installation & Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Service
```bash
uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
```

## Running the Automated Test Suite
```bash
pytest tests/
```

## License
MIT License. See LICENSE file for full terms.
