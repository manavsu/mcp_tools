from typing import Union, Sequence, Optional, Tuple, Dict
import subprocess
from main import mcp


@mcp.tool
def run(
    cmd: Union[str, Sequence[str]],
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Tuple[int, str, str]:
    """
    Run a command and return (exit_code, stdout, stderr) with deterministic, non-interactive behavior.

    Summary
    - Synchronous execution with UTF-8 capture (no TTY, no prompts, no streaming)
    - Returns exactly: (code: int, out: str, err: str)
    - Prefer list form (exec without shell); shell form allowed when passing a string

    Preflight: directory verification
    - If the command creates files/dirs (e.g., mkdir, mv, cp, > redirects), first use the LS tool to verify the parent directory exists and is correct.
      Example: before mkdir "/abs/foo/bar", LS "/abs/foo" to confirm.

    Execution rules
    - Prefer list form to avoid shell interpretation/aliases:
      run(["ls", "-la"])  # recommended
    - If using shell form (string), you must quote paths with spaces:
      run('python "/path/with spaces/script.py"')
    - Use ';' or '&&' to chain multiple commands in shell form; do not use newlines inside the command.
    - Prefer absolute paths; avoid changing directories. Only use cd if explicitly requested.

    Search and file access policy
    - Do NOT use shell search/read utilities (find, grep, cat, head, tail, ls) via this runner.
    - Instead, use the dedicated tools: Grep, Glob, Task; for reading/listing, use Read and LS.
    - If you still need grep-like behavior, use ripgrep (rg or /usr/bin/rg) first.

    Security and behavior
    - Non-interactive: avoid commands that expect user input.
    - Avoid expanding untrusted input in shell form; pass a list to bypass the shell.
    - Outputs are decoded as UTF-8 with replacement for invalid bytes (recommended).

    Parameters
    - cmd: str | list[str]
      - str → runs via the shell (shell=True)
      - list[str] → executes directly (recommended)
    - cwd: optional working directory
    - env: optional environment mapping (replaces process env if provided)
    - timeout: optional float seconds; raises subprocess.TimeoutExpired if exceeded

    Returns
    - (code: int, out: str, err: str)

    Examples
    - List directory (no colors): run(["ls", "-la", "--color=never"])
    - Echo safely (no shell parsing): run(["echo", "hello world"])
    - Python with spaces in path (list): run(["python", "/path/with spaces/script.py"])
    - Shell chaining when needed: run('command ls -la --color=never && echo "done"')
    - Create directory after verifying parent with LS: run(["mkdir", "-p", "/abs/foo/bar"])
    """
    sh = isinstance(cmd, str)
    p = subprocess.run(
        cmd,
        shell=sh,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        errors="replace",
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr
