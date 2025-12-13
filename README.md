# LLM Council Sentinel

An advanced AI deliberation system featuring multi-model council meetings, anonymized peer review, and robust health checking.

## 🚀 Key Features

- **3-Stage Deliberation**:
  1.  **Proposal**: Multiple models generate independent answers.
  2.  **Peer Review**: Models anonymize and rank each other's answers.
  3.  **Consensus**: A Chairman model synthesizes the final result based on rankings.
- **Robust Health System**:
  -   **Smart Caching**: Health status cached for 1 hour to reduce API load.
  -   **Circuit Breaker**: Exponential backoff for failing models.
  -   **Strict Filtering**: Unhealthy models are prevented from answering.
  -   **UI Transparency**: "Show unavailable" toggle reveals down/slow models.
- **Modern UI**:
  -   Streaming responses.
  -   Visual voting/ranking display.
  -   Dark/Light mode ready (optimized for Light).
  -   **Conversation Management**:
      -   Single delete enabled.
      -   Bulk delete with selection mode.

## 🛠️ Quick Start (Development)

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenRouter API Key

### 1. Backend Setup
```bash
cd backend
# Create .env file
echo "OPENROUTER_API_KEY=sk-or-..." > .env
echo "ADMIN_TOKEN=secret-token" >> .env

# Install dependencies (using uv or pip)
uv pip install -r requirements.txt

# Run Backend (Port 8010)
cd ..
uv run python -m backend.main
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Access the app at **http://localhost:5173**.

## 📚 Documentation

- **[Technical Architecture (AGENTS.md)](docs/AGENTS.md)**: Deep dive into the codebase, logic, and design decisions.
- **[Debugging Guide](DEBUG_GUIDE.md)**: How to troubleshoot issues.

## ⚠️ Troubleshooting

**Models show as "Unavailable"?**
- This usually means the OpenRouter API check failed (timeout or error).
- Click "Show unavailable" to see the specific error.
- Check your network and API key.
- You can force a refresh via API: `GET /api/councilors?refresh=true`.
- The system automatically filters them out to prevent crashes.
