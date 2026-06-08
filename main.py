import os
import tempfile
import json
import urllib3
import io
import requests
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv() 
urllib3.disable_warnings()

AZURE_ENDPOINT = "https://ai-xenia.cognitiveservices.azure.com"
AZURE_TTS_ENDPOINT = "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"
AZURE_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_LOCALE = "it-IT"
API_VERSION = "2024-11-15"

OWUI_URL = "https://owui.apps.rhoai01.xeniaprogetti.it/api/chat/completions"
OWUI_API_KEY = "Bearer " + os.getenv("OWUI_API_KEY", "")

app = FastAPI()

class TextRequest(BaseModel):
    text: str

def stt_azure(audio_path: str) -> str:
    url = f"{AZURE_ENDPOINT}/speechtotext/transcriptions:transcribe?api-version={API_VERSION}"
    with open(audio_path, "rb") as f:
        files = {
            "audio": (os.path.basename(audio_path), f, "application/octet-stream"),
            "definition": (None, json.dumps({"locales": [AZURE_LOCALE]}), "application/json"),
        }
        resp = requests.post(url, headers={"Ocp-Apim-Subscription-Key": AZURE_KEY}, files=files, timeout=120)
    resp.raise_for_status()
    combined = resp.json().get("combinedPhrases", [])
    if not combined:
        raise ValueError("No transcription received from Azure")
    return combined[0]["text"]


def ask_rag(text: str) -> str:
    resp = requests.post(
        OWUI_URL,
        headers={"Authorization": OWUI_API_KEY},
        json={
            "model": "musei-rag",
            "messages": [
                {"role": "user", "content": text}
            ]
        },
        verify=False
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def tts_azure(text: str) -> bytes:
    ssml = f"""<speak version='1.0' xml:lang='it-IT'>
        <voice xml:lang='it-IT' name='it-IT-ElsaNeural'>{text}</voice>
    </speak>"""
    resp = requests.post(
        AZURE_TTS_ENDPOINT,
        headers={
            "Ocp-Apim-Subscription-Key": AZURE_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
        },
        data=ssml.encode("utf-8"),
        timeout=30
    )
    resp.raise_for_status()
    return resp.content


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/ask-text")
async def ask_text(req: TextRequest):
    response = ask_rag(req.text)
    audio_response = tts_azure(response)
    return StreamingResponse(io.BytesIO(audio_response), media_type="audio/mpeg")

@app.post("/ask")
async def ask(audio: UploadFile = File(...)):
    suffix = os.path.splitext(audio.filename)[1] or ".ogg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(await audio.read())
        tmp_path = f.name
    try:
        text = stt_azure(tmp_path)
        response = ask_rag(text)
        audio_response = tts_azure(response)
    finally:
        os.unlink(tmp_path)
    return StreamingResponse(io.BytesIO(audio_response), media_type="audio/mpeg")
