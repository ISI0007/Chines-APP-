"""
CC-CEDICT parser & loader.

CC-CEDICT is a free Chinese-English dictionary maintained at:
  https://www.mdbg.net/chinese/dictionary?page=cc-cedict

File format (one entry per line):
  Traditional Simplified [pin1 yin1] /def1/def2/

This service can:
1. Download the latest dictionary
2. Parse the raw file into structured records
3. Look up any character or word
"""

import re
import os
import gzip
import urllib.request
from typing import Optional
from functools import lru_cache

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
CEDICT_PATH = os.path.join(os.path.dirname(__file__), "../data/cedict_ts.u8")

_ENTRY_RE = re.compile(
    r"^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/$"
)


def download_cedict(dest: str = CEDICT_PATH) -> None:
    """Download and decompress CC-CEDICT into dest."""
    gz_path = dest + ".gz"
    print(f"Downloading CC-CEDICT from {CEDICT_URL} ...")
    urllib.request.urlretrieve(CEDICT_URL, gz_path)
    with gzip.open(gz_path, "rb") as f_in:
        data = f_in.read()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f_out:
        f_out.write(data)
    os.remove(gz_path)
    print(f"Saved {len(data):,} bytes → {dest}")


def parse_cedict_line(line: str) -> Optional[dict]:
    """Parse one CC-CEDICT line into a dict, or None if invalid."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = _ENTRY_RE.match(line)
    if not m:
        return None
    traditional, simplified, pinyin_raw, defs_raw = m.groups()
    definitions = [d.strip() for d in defs_raw.split("/") if d.strip()]
    # Convert numeric pinyin spaces: "ni3 hao3" already has spaces
    return {
        "traditional": traditional,
        "simplified": simplified,
        "pinyin": pinyin_raw,           # numeric (CC-CEDICT default)
        "definitions": definitions,
    }


@lru_cache(maxsize=1)
def load_cedict(path: str = CEDICT_PATH) -> dict[str, list[dict]]:
    """
    Load CC-CEDICT into an in-memory index keyed by simplified character.
    Returns { simplified: [entry, ...] } — multiple entries per key possible.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"CC-CEDICT not found at {path}. "
            "Run download_cedict() or provide the file manually."
        )
    index: dict[str, list[dict]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            entry = parse_cedict_line(line)
            if entry:
                key = entry["simplified"]
                index.setdefault(key, []).append(entry)
    return index


def lookup(simplified: str, path: str = CEDICT_PATH) -> list[dict]:
    """Look up a Chinese word. Returns list of matching CC-CEDICT entries."""
    try:
        index = load_cedict(path)
    except FileNotFoundError:
        return []
    return index.get(simplified, [])


def enrich_word(word_dict: dict, path: str = CEDICT_PATH) -> dict:
    """
    Given a word dict with at least 'simplified', add/override
    definitions and traditional form from CC-CEDICT if available.
    """
    entries = lookup(word_dict["simplified"], path)
    if entries:
        best = entries[0]
        word_dict.setdefault("traditional", best["traditional"])
        if not word_dict.get("definitions"):
            word_dict["definitions"] = best["definitions"]
    return word_dict
