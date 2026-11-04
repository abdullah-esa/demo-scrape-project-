"""
Pandas-based cleaning & normalization pipeline.
"""

import logging
import re
from typing import Dict

import pandas as pd

from config import SiteConfig

logger = logging.getLogger(__name__)


def _cast_value(value, dtype: str, strip_pattern: str = None):
    """Cast a single value safely."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()

    if strip_pattern:
        s = re.sub(strip_pattern, "", s).strip()

    if dtype == "int":
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return None
    if dtype == "float":
        try:
            return float(s)
        except (ValueError, TypeError):
            return None
    if dtype == "datetime":
        try:
            return pd.to_datetime(s, errors="coerce")
        except Exception:
            return pd.NaT
    # str
    return s if s else None


def clean_dataframe(raw_records: list, config: SiteConfig) -> pd.DataFrame:
    """Apply dtype casting, strip patterns, dedupe, and missing-value handling."""
    if not raw_records:
        logger.warning("No records to clean.")
        return pd.DataFrame()

    df = pd.DataFrame(raw_records)
    logger.info(f"Raw DataFrame shape: {df.shape}")

    # 1. Apply per-field dtype + strip patterns
    for col in df.columns:
        dtype = config.dtypes.get(col, "str")
        pattern = config.strip_patterns.get(col)
        df[col] = df[col].apply(lambda v: _cast_value(v, dtype, pattern))

    # 2. Drop fully-empty rows
    df = df.dropna(how="all")

    # 3. Deduplicate on primary keys
    if config.primary_keys:
        existing_keys = [k for k in config.primary_keys if k in df.columns]
        if existing_keys:
            before = len(df)
            df = df.drop_duplicates(subset=existing_keys, keep="first")
            logger.info(
                f"Deduped on {existing_keys}: {before} -> {len(df)} rows"
            )

    # 4. Reset index
    df = df.reset_index(drop=True)

    # 5. Null report
    null_counts: Dict[str, int] = df.isna().sum().to_dict()
    logger.info(f"Null counts: {null_counts}")

    return df