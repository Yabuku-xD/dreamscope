from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from meteostat import Hourly, Point
from astral.moon import phase


def get_moon_phase_info(dt: datetime) -> Dict:
    # Astral returns moon phase age (0..29.53)
    age = float(phase(dt))
    # Basic naming bins
    if age < 1.0:
        name = "New Moon"
    elif age < 7.4:
        name = "Waxing Crescent"
    elif age < 8.4:
        name = "First Quarter"
    elif age < 14.8:
        name = "Waxing Gibbous"
    elif age < 15.8:
        name = "Full Moon"
    elif age < 22.1:
        name = "Waning Gibbous"
    elif age < 23.1:
        name = "Last Quarter"
    else:
        name = "Waning Crescent"
    return {"age": age, "name": name}


def get_weather_snapshot(dt: datetime, latitude: Optional[float], longitude: Optional[float]) -> Optional[Dict]:
    if latitude is None or longitude is None:
        return None
    try:
        location = Point(latitude, longitude)
        data = Hourly(location, dt.replace(minute=0, second=0, microsecond=0), dt.replace(minute=0, second=0, microsecond=0))
        df = data.fetch()
        if df is None or df.empty:
            return None
        row = df.iloc[0]
        return {
            "temp_c": float(row.get("temp", None)) if row.get("temp", None) is not None else None,
            "humidity": float(row.get("rhum", None)) if row.get("rhum", None) is not None else None,
            "pressure_hpa": float(row.get("pres", None)) if row.get("pres", None) is not None else None,
            "wind_speed_kmh": float(row.get("wspd", None)) if row.get("wspd", None) is not None else None,
            "conditions_code": int(row.get("coco", None)) if row.get("coco", None) is not None else None,
        }
    except Exception:
        return None
