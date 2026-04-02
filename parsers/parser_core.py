"""
parser_core.py — fire any parser at any file.
Detects extension, loads rules, dispatches.
Result always goes to patterns_log via demon catcher.
"""

import os
import re
import json
import sys

RULES_PATH = os.path.join(os.path.dirname(__file__), "parser_rules.json")

# Add server to path so we can hit demon catcher
_server_path = os.path.join(os.path.dirname(__file__), "..", "server")
if _server_path not in sys.path:
    sys.path.insert(0, _server_path)


def _load_rules() -> dict:
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def parse_file(file_path: str, send_to_catcher: bool = True) -> dict:
    """
    Parse any file.
    Returns {ext, lines, numbers, functions, headers, cleaned_text, char_count, word_count}
    """
    ext = os.path.splitext(file_path)[1].lower()
    rules = _load_rules().get(ext, {})

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except Exception as e:
        return {"error": str(e), "file": file_path}

    result = _apply_rules(raw, rules, ext)
    result["file"] = file_path
    result["ext"]  = ext

    if send_to_catcher:
        try:
            from modules import mod_patterns as pat
            pat.catch(result["cleaned_text"], source=f"parser:{file_path}", content_type=ext.lstrip("."))
        except Exception:
            pass

    return result


def _apply_rules(text: str, rules: dict, ext: str) -> dict:
    lines = text.splitlines()

    # strip comments
    if rules.get("strip_comments"):
        comment_char = "#" if ext in (".py", ".gd") else None
        if comment_char:
            lines = [l for l in lines if not l.strip().startswith(comment_char)]

    # strip blank lines
    if rules.get("strip_blank_lines"):
        lines = [l for l in lines if l.strip()]

    # normalize whitespace
    if rules.get("normalize_whitespace"):
        lines = [" ".join(l.split()) for l in lines]

    cleaned = "\n".join(lines)

    # extract numbers
    numbers = []
    if rules.get("extract_numbers"):
        numbers = [int(x) for x in re.findall(r'\d+', cleaned)]

    # extract function names
    functions = []
    if rules.get("extract_functions"):
        if ext == ".py":
            functions = re.findall(r'^def\s+(\w+)', cleaned, re.MULTILINE)
        elif ext == ".gd":
            functions = re.findall(r'^func\s+(\w+)', cleaned, re.MULTILINE)

    # extract markdown headers
    headers = []
    if rules.get("extract_headers"):
        headers = re.findall(r'^#{1,6}\s+(.+)', cleaned, re.MULTILINE)

    return {
        "cleaned_text": cleaned,
        "lines": lines,
        "line_count": len(lines),
        "char_count": len(cleaned),
        "word_count": len(cleaned.split()),
        "numbers": numbers,
        "functions": functions,
        "headers": headers
    }


if __name__ == "__main__":
    # CLI: python parser_core.py <file_path>
    if len(sys.argv) < 2:
        print("usage: parser_core.py <file_path>")
        sys.exit(1)
    r = parse_file(sys.argv[1])
    print(json.dumps({k: v for k, v in r.items() if k != "lines"}, indent=2))
