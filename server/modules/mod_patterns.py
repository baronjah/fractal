"""
DEMON CATCHER — mod_patterns.py
Watches everything. Logs text submissions, file touches, script runs.
Finds numbers in everything. Calculates luck on everything.
"""

import re
from datetime import datetime
from . import mod_db as db
from . import mod_signal as sig
from . import mod_numbers as num


def catch(content: str, source: str, content_type: str = "text") -> dict:
    """
    Log any content passing through the server.
    content      — the raw text
    source       — who/what sent it (e.g. 'user_input', 'file:path', 'script:name')
    content_type — 'text', 'file', 'command', 'json', 'log'
    Returns the patterns_log row dict.
    """
    content = str(content) if content else ""
    chars   = len(content)
    words   = len(content.split())
    numbers = find_numbers(content)
    luck    = num.calculate(content)

    row_id = db.execute(
        """INSERT INTO patterns_log
           (source, content, content_type, char_count, word_count, numbers_found, luck_score)
           VALUES (?,?,?,?,?,?,?)""",
        (
            source, content[:4000], content_type,
            chars, words,
            ",".join(str(n) for n in numbers),
            luck["value"]
        )
    )

    sig.emit(
        sig.SIG_PATTERN, source="mod_patterns", target=source,
        payload={"id": row_id, "luck": luck["value"], "mode": luck["mode"], "chars": chars}
    )

    return {
        "id": row_id,
        "chars": chars,
        "words": words,
        "numbers": numbers,
        "luck": luck
    }


def find_numbers(text: str) -> list:
    """Extract every integer from a string. Returns list of ints."""
    return [int(x) for x in re.findall(r'\d+', text)]


def get_patterns(limit: int = 50, since: str = None, source: str = None) -> list:
    """Query patterns_log. since = ISO datetime string."""
    if since and source:
        return db.execute(
            "SELECT * FROM patterns_log WHERE timestamp>=? AND source=? ORDER BY id DESC LIMIT ?",
            (since, source, limit), fetch="all"
        )
    if since:
        return db.execute(
            "SELECT * FROM patterns_log WHERE timestamp>=? ORDER BY id DESC LIMIT ?",
            (since, limit), fetch="all"
        )
    if source:
        return db.execute(
            "SELECT * FROM patterns_log WHERE source=? ORDER BY id DESC LIMIT ?",
            (source, limit), fetch="all"
        )
    return db.execute(
        "SELECT * FROM patterns_log ORDER BY id DESC LIMIT ?",
        (limit,), fetch="all"
    )


def active_hours() -> list:
    """
    Return list of {hour, count} showing when user is most active.
    Based on patterns_log timestamps.
    """
    return db.execute(
        """SELECT strftime('%H', timestamp) AS hour, COUNT(*) AS count
           FROM patterns_log
           GROUP BY hour
           ORDER BY count DESC""",
        fetch="all"
    )


def lucky_hours() -> list:
    """
    Return {hour, avg_luck} — which hours have the highest average luck score.
    """
    return db.execute(
        """SELECT strftime('%H', timestamp) AS hour,
                  AVG(luck_score) AS avg_luck,
                  COUNT(*) AS count
           FROM patterns_log
           GROUP BY hour
           ORDER BY avg_luck DESC""",
        fetch="all"
    )
