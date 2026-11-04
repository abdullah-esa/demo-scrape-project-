"""
Universal export: CSV + JSON, with directory creation and logging.
"""

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def export_dataframe(df: pd.DataFrame, output_dir: str, basename: str) -> None:
    """Export DataFrame to <output_dir>/<basename>.csv and .json."""
    if df.empty:
        logger.warning("DataFrame is empty; skipping export.")
        return

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / f"{basename}.csv"
    json_path = out_dir / f"{basename}.json"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    # Convert timestamps to ISO strings for JSON compatibility
    df_json = df.copy()
    for col in df_json.select_dtypes(include=["datetime", "datetimetz"]).columns:
        df_json[col] = df_json[col].astype(str)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(df_json.to_dict(orient="records"), f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Exported {len(df)} rows -> {csv_path}")
    logger.info(f"✓ Exported {len(df)} rows -> {json_path}")
    logger.info("Summary stats (numeric):\n%s", df.describe(include="number").to_string())