from __future__ import annotations

from pathlib import Path


BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
UPLOADS_DIR: Path = DATA_DIR / "uploads"
MODELS_DIR: Path = DATA_DIR / "models"
DB_PATH: Path = DATA_DIR / "dreams.db"

# Vosk English small model (about 50–60 MB zipped)
VOSK_MODEL_URL: str = (
    "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
)
VOSK_MODEL_DIRNAME: str = "vosk-model-small-en-us-0.15"
VOSK_SAMPLE_RATE: int = 16000

# Application metadata
APP_NAME: str = "DreamScope"
