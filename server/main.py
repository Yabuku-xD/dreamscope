from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .settings import BASE_DIR
from .utils import ensure_directories, save_uploaded_audio, parse_dt, to_json_str
from .models import Dream, create_db_and_tables, get_session, get_all_dreams
from .stt import transcribe_wav
from .nlp import analyze_text
from .external import get_moon_phase_info, get_weather_snapshot


app = FastAPI(title="DreamScope")

templates = Jinja2Templates(directory=(BASE_DIR / "templates").as_posix())
app.mount("/static", StaticFiles(directory=(BASE_DIR / "static").as_posix()), name="static")


@app.on_event("startup")
def startup_event() -> None:
    ensure_directories()
    create_db_and_tables()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload(
    request: Request,
    audio: UploadFile,
    sleep_start: Optional[str] = Form(None),
    sleep_end: Optional[str] = Form(None),
    stress_level: Optional[int] = Form(None),
    diet_tags: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
) -> Response:
    audio_path = save_uploaded_audio(audio)

    dream = Dream(
        audio_path=str(audio_path),
        sleep_start=parse_dt(sleep_start),
        sleep_end=parse_dt(sleep_end),
        stress_level=stress_level,
        diet_tags=diet_tags,
        latitude=latitude,
        longitude=longitude,
    )

    with get_session() as session:
        session.add(dream)
        session.commit()

    return RedirectResponse(url="/dreams", status_code=303)


@app.get("/dreams", response_class=HTMLResponse)
async def dreams(request: Request) -> HTMLResponse:
    items = get_all_dreams(limit=200)
    return templates.TemplateResponse("dreams.html", {"request": request, "dreams": items})


@app.get("/dreams/{dream_id}", response_class=HTMLResponse)
async def dream_detail(request: Request, dream_id: int) -> HTMLResponse:
    with get_session() as session:
        dream = session.get(Dream, dream_id)
    if not dream:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse("dream_detail.html", {"request": request, "dream": dream})


@app.get("/media/{dream_id}")
async def media(dream_id: int) -> Response:
    with get_session() as session:
        dream = session.get(Dream, dream_id)
    if not dream:
        return Response(status_code=404)
    path = Path(dream.audio_path)
    if not path.exists():
        return Response(status_code=404)
    return FileResponse(path, media_type="audio/wav")


@app.post("/analyze/{dream_id}")
async def analyze(dream_id: int) -> Response:
    with get_session() as session:
        dream = session.get(Dream, dream_id)
        if not dream:
            return Response(status_code=404)
        # Transcribe
        transcript = transcribe_wav(Path(dream.audio_path))
        dream.transcript = transcript
        # NLP
        results = analyze_text(transcript)
        dream.sentiment_compound = float(results["sentiment"].get("compound", 0.0))
        dream.emotions_json = to_json_str(results.get("emotions", {}))
        dream.keywords_json = to_json_str(results.get("keywords", []))
        dream.themes_json = to_json_str(results.get("themes", []))
        # External
        created_at = dream.created_at or datetime.utcnow()
        moon = get_moon_phase_info(created_at)
        dream.moon_phase = float(moon.get("age", 0.0))
        dream.moon_phase_name = moon.get("name")
        weather = get_weather_snapshot(created_at, dream.latitude, dream.longitude)
        dream.weather_json = to_json_str(weather or {})

        session.add(dream)
        session.commit()

    return RedirectResponse(url=f"/dreams/{dream_id}", status_code=303)


@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request) -> HTMLResponse:
    items = get_all_dreams(limit=500)
    return templates.TemplateResponse("analytics.html", {"request": request, "dreams": items})


@app.get("/export.csv")
async def export_csv() -> Response:
    # Simple CSV export in-memory
    import io
    import csv

    headers = [
        "id",
        "created_at",
        "audio_path",
        "transcript",
        "latitude",
        "longitude",
        "sleep_start",
        "sleep_end",
        "stress_level",
        "diet_tags",
        "sentiment_compound",
        "emotions_json",
        "keywords_json",
        "themes_json",
        "weather_json",
        "moon_phase",
        "moon_phase_name",
    ]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for d in get_all_dreams(limit=100000):
        writer.writerow({
            "id": d.id,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "audio_path": d.audio_path,
            "transcript": d.transcript,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "sleep_start": d.sleep_start.isoformat() if d.sleep_start else None,
            "sleep_end": d.sleep_end.isoformat() if d.sleep_end else None,
            "stress_level": d.stress_level,
            "diet_tags": d.diet_tags,
            "sentiment_compound": d.sentiment_compound,
            "emotions_json": d.emotions_json,
            "keywords_json": d.keywords_json,
            "themes_json": d.themes_json,
            "weather_json": d.weather_json,
            "moon_phase": d.moon_phase,
            "moon_phase_name": d.moon_phase_name,
        })

    content = buf.getvalue().encode("utf-8")
    return Response(content, media_type="text/csv")
