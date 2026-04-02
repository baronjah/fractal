"""
MOD-L: L IS FOR LUCK — numerology engine
Every string, timestamp, name, or event has a number.
Every number has a mode: FLOW, BALANCE, BUILD, CHAOS, or AMPLIFIED.
"""

import json
import re
import os
from . import mod_db as db

_LUCK_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "numbers", "luck_tables.json")
_tables: dict = {}

MASTER_NUMBERS = {11, 22, 33}

MODE_MAP = {
    1: "FLOW",  2: "BALANCE", 3: "FLOW",  4: "BUILD",
    5: "CHAOS", 6: "BALANCE", 7: "CHAOS", 8: "BUILD",
    9: "FLOW",  11: "AMPLIFIED", 22: "AMPLIFIED", 33: "AMPLIFIED"
}


def _load_tables() -> dict:
    global _tables
    if not _tables:
        try:
            with open(_LUCK_PATH, "r", encoding="utf-8") as f:
                _tables = json.load(f)
        except FileNotFoundError:
            _tables = {}
    return _tables


def reduce(n: int) -> int:
    """
    Digit-sum reduce to single digit.
    Master numbers 11, 22, 33 stay as-is.
    """
    if n in MASTER_NUMBERS:
        return n
    s = sum(int(d) for d in str(abs(n)) if d.isdigit())
    if s in MASTER_NUMBERS:
        return s
    if s >= 10:
        return reduce(s)
    return s


def calculate(text: str) -> dict:
    """
    Input: any string (name, timestamp, sentence, number).
    Returns: {value, master, mode, table_entry, numbers_found}
    """
    _load_tables()
    # extract all digit groups from the text
    numbers_found = [int(x) for x in re.findall(r'\d+', text)]
    # sum all digit chars in entire string
    raw_sum = sum(int(c) for c in text if c.isdigit())
    if raw_sum == 0:
        # no digits — use char codes
        raw_sum = sum(ord(c) for c in text.lower() if c.isalpha())
    value = reduce(raw_sum) if raw_sum > 0 else 1
    master = value in MASTER_NUMBERS
    mode = MODE_MAP.get(value, "FLOW")
    entry = _tables.get(str(value), {})
    return {
        "value": value,
        "master": master,
        "mode": mode,
        "meaning": entry.get("meaning", ""),
        "color": entry.get("color", "#FFFFFF"),
        "vibe": entry.get("vibe", ""),
        "numbers_found": numbers_found,
        "raw_sum": raw_sum
    }


def luck_for_timestamp(ts: str) -> dict:
    """Calculate luck value for a datetime string."""
    return calculate(ts)


def log_calculation(input_text: str, notes: str = None) -> dict:
    """Calculate + persist to numbers_log. Returns result dict."""
    result = calculate(input_text)
    db.execute(
        "INSERT INTO numbers_log (input, calculated_value, luck_mode, notes) VALUES (?,?,?,?)",
        (input_text[:500], result["value"], result["mode"], notes)
    )
    return result


def get_log(limit: int = 50) -> list:
    return db.execute(
        "SELECT * FROM numbers_log ORDER BY id DESC LIMIT ?",
        (limit,), fetch="all"
    )


def current_mode() -> dict:
    """What is the luck mode RIGHT NOW (based on current timestamp)."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return calculate(ts)
