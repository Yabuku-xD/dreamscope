from __future__ import annotations

import io
import wave
import zipfile
import audioop
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm
from vosk import Model, KaldiRecognizer

from .settings import MODELS_DIR, VOSK_MODEL_URL, VOSK_MODEL_DIRNAME, VOSK_SAMPLE_RATE


_MODEL_CACHE: Optional[Model] = None


def _download_with_progress(url: str, dest: Path) -> None:
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    with dest.open("wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc="Downloading Vosk model") as pbar:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))


def ensure_vosk_model() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_dir = MODELS_DIR / VOSK_MODEL_DIRNAME
    if model_dir.exists() and any(model_dir.iterdir()):
        return model_dir

    zip_path = MODELS_DIR / f"{VOSK_MODEL_DIRNAME}.zip"
    if not zip_path.exists():
        _download_with_progress(VOSK_MODEL_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(MODELS_DIR)
    return model_dir


def get_model() -> Model:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    model_path = ensure_vosk_model()
    _MODEL_CACHE = Model(model_path.as_posix())
    return _MODEL_CACHE


def _read_wav_as_pcm16_mono_16k(path: Path) -> bytes:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    # Convert to 16-bit PCM mono 16k
    pcm = frames
    if channels == 2:
        pcm = audioop.tomono(pcm, sampwidth, 0.5, 0.5)
        channels = 1
    if sampwidth != 2:
        pcm = audioop.lin2lin(pcm, sampwidth, 2)
        sampwidth = 2
    if rate != VOSK_SAMPLE_RATE:
        pcm, _ = audioop.ratecv(pcm, 2, 1, rate, VOSK_SAMPLE_RATE, None)
        rate = VOSK_SAMPLE_RATE
    return pcm


def transcribe_wav(path: Path) -> str:
    model = get_model()
    pcm = _read_wav_as_pcm16_mono_16k(path)
    rec = KaldiRecognizer(model, VOSK_SAMPLE_RATE)
    rec.SetWords(True)
    # Feed in chunks
    buf = io.BytesIO(pcm)
    chunk = buf.read(4000)
    while chunk:
        rec.AcceptWaveform(chunk)
        chunk = buf.read(4000)
    final_result = rec.FinalResult()
    # final_result is a JSON string like {"text": "..."}
    try:
        import json
        return json.loads(final_result).get("text", "").strip()
    except Exception:
        return ""
