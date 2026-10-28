# M-ARCH Setup & Installation Guide

## Hardware Prerequisites
- Operating System: Windows 11 / Linux / macOS
- Recommended RAM: 16 GB+
- GPU: Dedicated GPU (e.g. RTX 3050 6GB) or modern multi-core CPU
- Storage: 10 GB+ free disk space

## 1. Local Model Setup (Ollama)
Install Ollama from [ollama.com](https://ollama.com).

Recommended model: `qwen2.5-coder:7b`
```powershell
ollama pull qwen2.5-coder:7b
```
Verify the model is running:
```powershell
ollama run qwen2.5-coder:7b "Hello"
```

## 2. Groq Cloud Setup (Optional)
If using Groq for accelerated inference:
1. Obtain an API key from [console.groq.com](https://console.groq.com).
2. Open `backend/.env`.
3. Add your key: `GROQ_API_KEY=gsk_...`
4. Never commit or share your `.env` file.

## 3. Backend Setup
Navigate to `backend/` and install dependencies:
```powershell
cd backend
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```
Start the backend server:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

## 4. Frontend Setup
Navigate to `frontend/` and install dependencies:
```powershell
cd frontend
npm install
npm run dev
```
Access the M-ARCH UI at: `http://localhost:3000`
