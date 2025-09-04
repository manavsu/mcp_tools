import os
from typing import Tuple

from main import mcp


DEFAULT_READ_LIMIT = 2000
MAX_LINE_LENGTH = 2000

_IMAGE_TYPES = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".webp": "WebP",
}

# common binary-ish extensions to short-circuit
_BINARY_EXTS = {
    ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".class", ".jar", ".war", ".7z",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp",
    ".bin", ".dat", ".obj", ".o", ".a", ".lib", ".wasm", ".pyc", ".pyo",
}

@mcp.tool
def read_file(
    file_path: str,
    offset: int = 0,
    limit: int = DEFAULT_READ_LIMIT,
    max_line_len: int = MAX_LINE_LENGTH,
) -> Tuple[str, bool]:
    """
    Read a text file and return (output, has_more).

    Fast, agent-friendly reader:
    - filePath should be absolute; if not, it is resolved relative to CWD
    - Reads up to 'limit' lines starting from 'offset' (0-based), default 2000
    - Truncates any line longer than 2000 characters (configurable via max_line_len)
    - Returns content in cat -n style with line numbers starting at 1
    - Rejects binary files, including images

    Parameters:
      file_path: Absolute path to the file (relative paths are resolved to absolute).
      offset: Line number to start from (0-based).
      limit: Number of lines to read (default 2000).
      max_line_len: Max characters per line before truncating with "...".

    Returns:
      (output, has_more)
        output: String wrapped in <file> ... </file>, numbered like "00001| ..."
        has_more: True if the file has more lines beyond offset+limit

    Notes:
      - This function decodes as UTF-8 with replacement for invalid bytes.
      - It raises FileNotFoundError if the file does not exist.
      - Raises ValueError for binary or image files.
    """
    p = file_path if os.path.isabs(file_path) else os.path.abspath(file_path)

    ext = os.path.splitext(p)[1].lower()
    if ext in _IMAGE_TYPES:
        kind = _IMAGE_TYPES[ext]
        raise ValueError(f"This is an image file of type: {kind}\nUse a different tool to process images")

    if _is_binary(p):
        raise ValueError(f"Cannot read binary file: {p}")

    # Read entire file as text; simple and deterministic
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")

    start = max(0, int(offset))
    end = start + int(limit)
    raw = lines[start:end]

    shown = []
    for i, line in enumerate(raw, 0):
        s = line if len(line) <= max_line_len else (line[:max_line_len] + "...")
        num = str(start + i + 1).zfill(5)
        shown.append(f"{num}| {s}")

    has_more = len(lines) > start + len(raw)

    out = "<file>\n" + "\n".join(shown)
    if has_more:
        out += f"\n\n(File has more lines. Use 'offset' parameter to read beyond line {start + len(raw)})"
    out += "\n</file>"

    return out, has_more


def _is_binary(p: str) -> bool:
    ext = os.path.splitext(p)[1].lower()
    if ext in _BINARY_EXTS:
        return True

    try:
        size = os.stat(p).st_size
    except OSError:
        # Let the caller raise on open; treat as non-binary here
        return False
    if size == 0:
        return False

    n = min(4096, size)
    with open(p, "rb") as f:
        head = f.read(n)

    if b"\x00" in head:
        return True

    non_printable = 0
    for b in head:
        if b == 0:
            return True
        if b < 9 or (13 < b < 32):
            non_printable += 1
    return (non_printable / len(head)) > 0.3

