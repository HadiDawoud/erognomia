"""Parse `window.<name> = [...]` assignments from IRL asset JS files."""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from typing import Any, List

logger = logging.getLogger(__name__)


def parse_js_window_array(js_source: str, var_name: str, *, relaxed: bool = False) -> List[Any]:
    """
    Extract and parse a top-level JS array assignment.

    `relaxed=False` suits JSON-like files (reference.js). `relaxed=True` applies
    extra normalisation for hand-written project.js (comments, bare keys, single quotes).
    Falls back to Node.js when relaxed parsing fails and `node` is available.
    """
    arr_text = _extract_array_text(js_source, var_name)
    arr_text = _strip_js_comments(arr_text)
    payload = arr_text
    if relaxed:
        payload = _normalize_js_string_literals(payload)
        payload = _quote_unquoted_keys(payload)
    payload = re.sub(r",(\s*[}\]])", r"\1", payload)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        if relaxed and shutil.which("node"):
            logger.warning(
                "Python parse failed for window.%s (%s); falling back to Node.js",
                var_name,
                exc,
            )
            data = _parse_with_node(js_source, var_name)
        else:
            raise ValueError(f"Failed to parse window.{var_name}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"window.{var_name} is not an array")
    return data


def _extract_array_text(js_source: str, var_name: str) -> str:
    pat = re.compile(rf"window\.{re.escape(var_name)}\s*=\s*\[", re.MULTILINE)
    match = pat.search(js_source)
    if not match:
        raise ValueError(f"No window.{var_name} assignment found")

    start = match.end() - 1
    depth = 0
    in_str: str | None = None
    escape = False

    for idx in range(start, len(js_source)):
        char = js_source[idx]
        if in_str:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == in_str:
                in_str = None
            continue
        if char in ('"', "'"):
            in_str = char
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return js_source[start : idx + 1]

    raise ValueError(f"Unclosed array for window.{var_name}")


def _strip_js_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    lines: List[str] = []
    for line in text.split("\n"):
        in_str = False
        quote: str | None = None
        out: List[str] = []
        idx = 0
        while idx < len(line):
            char = line[idx]
            if in_str:
                out.append(char)
                if char == "\\" and idx + 1 < len(line):
                    out.append(line[idx + 1])
                    idx += 2
                    continue
                if char == quote:
                    in_str = False
                idx += 1
                continue
            if char in ('"', "'"):
                in_str = True
                quote = char
                out.append(char)
                idx += 1
                continue
            if char == "/" and idx + 1 < len(line) and line[idx + 1] == "/":
                break
            out.append(char)
            idx += 1
        lines.append("".join(out))
    return "\n".join(lines)


def _normalize_js_string_literals(text: str) -> str:
    out: List[str] = []
    idx = 0
    n = len(text)
    in_double = False
    in_single = False
    escape = False

    while idx < n:
        char = text[idx]
        if in_single:
            if escape:
                out.append(char)
                escape = False
            elif char == "\\":
                if idx + 1 < n and text[idx + 1] == "'":
                    out.append("'")
                    idx += 2
                    continue
                out.append(char)
                escape = True
            elif char == "'":
                out.append('"')
                in_single = False
            elif char == '"':
                out.append('\\"')
            elif char == "\n":
                out.append("\\n")
            elif char == "\r":
                pass
            elif char == "\t":
                out.append("\\t")
            else:
                out.append(char)
            idx += 1
            continue

        if in_double:
            out.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_double = False
            idx += 1
            continue

        if char == '"':
            in_double = True
            out.append(char)
        elif char == "'":
            in_single = True
            out.append('"')
        else:
            out.append(char)
        idx += 1

    return "".join(out)


def _quote_unquoted_keys(text: str) -> str:
    return re.sub(r'([\{,\[]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', text)


def _parse_with_node(js_source: str, var_name: str) -> List[Any]:
    script = f"window = {{}};\n{js_source}\nprocess.stdout.write(JSON.stringify(window.{var_name}));"
    proc = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ValueError(f"Node.js parse failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return json.loads(proc.stdout)
