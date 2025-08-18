from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fastapi import UploadFile

from .settings import DATA_DIR, UPLOADS_DIR


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def generate_audio_filename(extension: str = "wav") -> str:
    unique_id = uuid.uuid4().hex
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    return f"dream_{timestamp}_{unique_id}.{extension}"


def save_uploaded_audio(file: UploadFile, destination_dir: Path = UPLOADS_DIR) -> Path:
    """Save uploaded audio to disk as WAV and return the absolute path."""
    extension = (file.filename or "").split(".")[-1].lower() or "wav"
    if extension not in {"wav", "wave"}:
        extension = "wav"
    filename = generate_audio_filename(extension=extension)
    path = destination_dir / filename
    with path.open("wb") as f:
        f.write(file.file.read())
    return path


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Expect ISO 8601 from <input type="datetime-local"> (YYYY-MM-DDTHH:MM)
        return datetime.fromisoformat(value)
    except Exception:
        return None


def to_json_str(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        return "{}"


def dicts_to_csv(rows: Iterable[Dict[str, Any]], fieldnames: List[str], dest: Path) -> None:
    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
