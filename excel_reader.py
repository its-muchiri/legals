import json
import os
from typing import List

import pandas as pd

from config import EXCEL_FILE, KEYWORDS_COLUMN, PROCESSED_LOG
from logger import get_logger

TAGS_FILE = "tags.txt"

log = get_logger()

_EMPTY_LOG: dict = {
    "processed":   [],
    "failed":      [],
    "post_ids":    {},   # kept for backwards compat
    "posts":       {},   # rich per-keyword records (new)
    "token_usage": {},
}


# ── Log I/O ───────────────────────────────────────────────────────────────────

def load_processed_log() -> dict:
    if not os.path.exists(PROCESSED_LOG):
        return {k: v.copy() if isinstance(v, (list, dict)) else v
                for k, v in _EMPTY_LOG.items()}
    with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key, default in _EMPTY_LOG.items():
        data.setdefault(key, default.copy() if isinstance(default, (list, dict)) else default)
    return data


def save_processed_log(log_data: dict) -> None:
    with open(PROCESSED_LOG, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


# ── Per-keyword state ─────────────────────────────────────────────────────────

def mark_processed(keyword: str, post_id: int, log_data: dict) -> None:
    """Mark a keyword as successfully processed (maintains backwards compat)."""
    if keyword not in log_data["processed"]:
        log_data["processed"].append(keyword)
    log_data["post_ids"][keyword] = post_id
    if keyword in log_data["failed"]:
        log_data["failed"].remove(keyword)
    save_processed_log(log_data)


def mark_failed(keyword: str, log_data: dict) -> None:
    if keyword not in log_data["failed"]:
        log_data["failed"].append(keyword)
    save_processed_log(log_data)


def save_post_record(keyword: str, record: dict, log_data: dict) -> None:
    """Persist a full post record into log_data['posts'] and write to disk."""
    log_data.setdefault("posts", {})[keyword] = record
    save_processed_log(log_data)


# ── Keyword reading ───────────────────────────────────────────────────────────

def read_keywords() -> List[str]:
    """Return all keywords from the Excel file.

    Handles two layouts:
      - Standard: a column named KEYWORDS_COLUMN (e.g. 'Keywords')
      - Bare list: no header row, keywords in column 0, optionally prefixed
        with a number like '1. ', '2. ', with optional blank rows between.
    """
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(
            f"Excel file '{EXCEL_FILE}' not found. "
            "Place keywords.xlsx in the bot directory."
        )

    df_check = pd.read_excel(EXCEL_FILE, nrows=1)
    if KEYWORDS_COLUMN in df_check.columns:
        df = pd.read_excel(EXCEL_FILE)
        series = df[KEYWORDS_COLUMN]
    else:
        log.debug(f"Column '{KEYWORDS_COLUMN}' not found — reading first column as bare list.")
        df = pd.read_excel(EXCEL_FILE, header=None)
        series = df.iloc[:, 0]

    keywords = (
        series
        .dropna()
        .astype(str)
        .str.strip()
        .str.replace(r"^\d+\.\s*", "", regex=True)
        .str.strip()
        .tolist()
    )
    keywords = [kw for kw in keywords if kw]
    log.debug(f"Read {len(keywords)} keywords from {EXCEL_FILE}")
    return keywords


def get_pending_keywords() -> tuple[List[str], dict]:
    """Return (unprocessed_keywords, log_data)."""
    all_kw   = read_keywords()
    log_data = load_processed_log()
    done     = set(log_data["processed"])
    pending  = [kw for kw in all_kw if kw not in done]
    log.info(
        f"Keywords total={len(all_kw)}, already processed={len(done)}, "
        f"pending={len(pending)}"
    )
    return pending, log_data


# ── Tag file ──────────────────────────────────────────────────────────────────

def load_tags() -> List[str]:
    """Return all tags from tags.txt, one per line, stripping blank lines."""
    if not os.path.exists(TAGS_FILE):
        log.warning(f"{TAGS_FILE} not found — falling back to Claude-generated tags.")
        return []
    with open(TAGS_FILE, "r", encoding="utf-8") as f:
        tags = [line.strip() for line in f if line.strip()]
    log.debug(f"Loaded {len(tags)} tags from {TAGS_FILE}")
    return tags
