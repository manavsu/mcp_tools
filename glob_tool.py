import os
import glob
from typing import List, Optional, Tuple
from main import mcp


@mcp.tool
def glob_files(
    pattern: str, path: Optional[str] = None, limit: int = 100
) -> Tuple[List[str], bool]:
    """
    Fast file pattern matching tool for any codebase size.

    - Supports glob patterns like "**/*.js" or "src/**/*.ts"
    - Returns matching file paths sorted by modification time (newest first)
    - Use when you need to find files by name patterns
    - For open-ended multi-step searches across large repos, pair with a higher-level search/grep agent

    Parameters:
      pattern: Glob pattern (supports **, *, ?, []).
      path: Optional directory to search in. Defaults to current working directory.
      limit: Max number of results to return (default 100).

    Returns:
      (paths, truncated)
        paths: absolute file paths, newest first
        truncated: True if more results existed beyond 'limit'
    """
    d = os.getcwd() if path is None else path
    base = d if os.path.isabs(d) else os.path.abspath(os.path.join(os.getcwd(), d))
    patspec = os.path.join(base, pattern)

    hits = glob.glob(patspec, recursive=True)

    items: List[Tuple[str, float]] = []
    for p in hits:
        if not os.path.isfile(p):
            continue
        try:
            m = os.stat(p, follow_symlinks=True).st_mtime
        except OSError:
            m = 0.0
        items.append((os.path.abspath(p), m))

    items.sort(key=lambda x: x[1], reverse=True)

    trunc = len(items) > limit
    paths = [p for p, _ in items[:limit]]
    return paths, trunc
