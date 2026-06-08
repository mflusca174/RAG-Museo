# Human AI Assistant

FastAPI backend that powers a voice-driven AI assistant. The service receives an audio file from the client, transcribes it via Azure Speech-to-Text, queries an Open WebUI RAG pipeline for an answer, and returns the response as synthesized speech via Azure Text-to-Speech.


## Pipeline

audio in → Azure STT → RAG (Open WebUI) → Azure TTS → audio out


## Stack

- **FastAPI** — API framework
- **Azure Cognitive Services** — Speech-to-Text and Text-to-Speech
- **Open WebUI** — RAG pipeline backend
- **Docker** — containerization

## Project Structure

human_ai_assistant/
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── README.md


## Configuration to review before deploying

Several values are **hardcoded** in `main.py` and must be updated to match your environment. Do not assume the defaults will work outside of the original setup.

### 1. RAG model and endpoint (`main.py`)

```python
OWUI_URL = "https://owui.apps.rhoai01.xeniaprogetti.it/api/chat/completions"
...
"model": "musei-rag"
```

- **`OWUI_URL`** — points to a specific Open WebUI instance. Change it if your RAG is hosted elsewhere.
- **`"model": "musei-rag"`** — the model name inside `ask_rag()`. This refers to a specific custom model in Open WebUI backed by a specific knowledge base. **If you want to use a different knowledge base or RAG configuration, you must change this model ID** to one that exists in your Open WebUI instance.

### 2. Azure endpoints (`main.py`)

```python
AZURE_ENDPOINT = "https://ai-xenia.cognitiveservices.azure.com"
AZURE_TTS_ENDPOINT = "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"
```

Update these if your Azure resource lives in a different region or under a different name.

### 3. Locale and voice (`main.py`)

```python
AZURE_LOCALE = "it-IT"
...
name='it-IT-ElsaNeural'
```

Both the STT locale and the TTS voice are set to Italian. Change them if you need a different language or voice.

### 4. API keys (`.env`)

API keys are read from environment variables. Create a `.env` file in the project root:

```
AZURE_SPEECH_KEY=your_azure_speech_key_here
OWUI_API_KEY=your_openwebui_api_key_here
```

**Never commit `.env` to version control.** Both keys must be regenerated and replaced if you're deploying to a new environment.

## Setup

### 1. Configure environment variables

Create the `.env` file as shown above.

### 2. Build and start the service

```bash
docker compose up -d --build
```

### 3. Check that the service is running

```bash
docker compose logs -f
```

The service will be available at `http://localhost:8000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check, returns `{"status": "ok"}` |
| `POST` | `/ask` | Accepts an audio file (multipart form, field `audio`), returns synthesized speech (`audio/mpeg`) |

### Example request

```bash
curl -X POST http://localhost:8000/ask \
  -F "audio=@question.ogg" \
  --output answer.mp3
```

## Useful Commands

```bash
# Restart the container
docker compose restart

# Stop the service
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Follow logs
docker compose logs -f
```

## Notes

- SSL verification is disabled (`verify=False`) on the RAG request because the Open WebUI instance may use a self-signed certificate. Remove this once a valid certificate is in place.
- Audio files are written to a temporary file on disk, processed, and cleaned up immediately. No audio data is persisted.