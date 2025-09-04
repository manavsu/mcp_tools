import os
import re
import subprocess
from typing import List, Optional, Tuple
from main import mcp

@mcp.tool
def grep_search_rg(
    pattern: str,
    path: Optional[str] = None,
    include: Optional[str] = None,
    limit: int = 100,
) -> Tuple[List[Tuple[str, int, str]], bool]:
    """
    Fast content search tool powered by ripgrep.

    - Uses ripgrep (rg) for full regex search
    - Optional include filter passed as --glob (e.g., '*.js', '*.{ts,tsx}')
    - Returns matches sorted by file mtime (newest first)
    - For counting/advanced flags, call rg directly

    Returns: (matches, truncated)
      matches: list of (file_path, line_number, line_text)
      truncated: True if more than 'limit' matches existed
    """
    if not pattern:
        raise ValueError("pattern is required")

    d = os.getcwd() if path is None else path
    base = d if os.path.isabs(d) else os.path.abspath(os.path.join(os.getcwd(), d))

    args = ["rg", "-n", pattern]
    if include:
        args += ["--glob", include]
    args.append(base)

    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if p.returncode == 1:
        return [], False
    if p.returncode != 0:
        raise RuntimeError(
            p.stderr.strip() or f"ripgrep failed with code {p.returncode}"
        )

    rx = re.compile(r"^(.*?):(\d+):(.*)$")
    rows = []
    for line in p.stdout.splitlines():
        m = rx.match(line)
        if not m:
            continue
        fp, ln, txt = m.group(1), int(m.group(2)), m.group(3)
        try:
            mt = os.stat(fp, follow_symlinks=True).st_mtime
        except OSError:
            mt = 0.0
        rows.append((os.path.abspath(fp), ln, txt.rstrip("\n"), mt))

    if not rows:
        return [], False

    rows.sort(key=lambda r: r[3], reverse=True)
    truncated = len(rows) > limit
    cut = rows[:limit]
    return [(p, n, t) for p, n, t, _ in cut], truncated



