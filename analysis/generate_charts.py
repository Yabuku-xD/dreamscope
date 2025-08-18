from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlmodel import Session, select

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / 'server'))

from models import Dream, engine  # type: ignore


def load_dataframe() -> pd.DataFrame:
    with Session(engine) as session:
        rows = list(session.exec(select(Dream)))
    records = []
    for d in rows:
        records.append({
            'id': d.id,
            'created_at': d.created_at,
            'sentiment_compound': d.sentiment_compound,
            'moon_phase': d.moon_phase,
            'moon_phase_name': d.moon_phase_name,
            'stress_level': d.stress_level,
        })
    return pd.DataFrame.from_records(records)


def main() -> None:
    out_dir = Path(__file__).resolve().parent / 'out'
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataframe()
    if df.empty:
        print('No data yet. Add some dreams first.')
        return

    # Sentiment distribution
    plt.figure(figsize=(6,4))
    sns.histplot(df['sentiment_compound'].dropna(), bins=20, kde=True)
    plt.title('Sentiment Compound Distribution')
    plt.tight_layout()
    plt.savefig(out_dir / 'sentiment_distribution.png', dpi=160)

    # Sentiment by moon phase name
    if 'moon_phase_name' in df.columns and df['moon_phase_name'].notna().any():
        plt.figure(figsize=(8,4))
        sns.boxplot(data=df.dropna(subset=['sentiment_compound', 'moon_phase_name']), x='moon_phase_name', y='sentiment_compound')
        plt.title('Sentiment by Moon Phase')
        plt.xticks(rotation=30, ha='right')
        plt.tight_layout()
        plt.savefig(out_dir / 'sentiment_by_moon_phase.png', dpi=160)

    # Sentiment vs stress level
    if 'stress_level' in df.columns and df['stress_level'].notna().any():
        plt.figure(figsize=(6,4))
        sns.scatterplot(data=df.dropna(subset=['sentiment_compound', 'stress_level']), x='stress_level', y='sentiment_compound')
        plt.title('Sentiment vs Stress Level')
        plt.tight_layout()
        plt.savefig(out_dir / 'sentiment_vs_stress.png', dpi=160)

    print('Charts saved to', out_dir)


if __name__ == '__main__':
    main()
