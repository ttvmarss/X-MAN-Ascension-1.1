"""Windows-compatible system actions: open URLs, launch apps, run terminal commands."""
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import tracking


PROJECTS_DIR = Path(
    os.getenv("PROJECTS_DIR", "") or os.path.expanduser("~/Documents/JARVIS Projects")
)
CLAUDE_CODE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")


def open_url(url: str) -> bool:
    """Open a URL in the default browser."""
    try:
        os.startfile(url)
        return True
    except Exception:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
            return True
        except Exception:
            return False


def open_app(app_name: str) -> bool:
    """Launch a Windows application by name or path."""
    try:
        if os.path.isabs(app_name) and os.path.exists(app_name):
            subprocess.Popen([app_name])
            return True
        subprocess.Popen(["cmd", "/c", "start", app_name], shell=False)
        return True
    except Exception:
        return False


def open_browser(query_or_url: str) -> bool:
    """Open Chrome with a search query or URL."""
    if query_or_url.startswith("http://") or query_or_url.startswith("https://"):
        url = query_or_url
    else:
        import urllib.parse
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query_or_url)
    return open_url(url)


def run_terminal_command(command: str, cwd: Optional[str] = None) -> tuple[bool, str]:
    """Run a command in Windows Terminal or cmd and return (success, output)."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out."
    except Exception as e:
        return False, str(e)


def open_windows_terminal(cwd: Optional[str] = None) -> bool:
    """Open Windows Terminal (or cmd as fallback) in the given directory."""
    try:
        if cwd:
            subprocess.Popen(["wt", "-d", cwd])
        else:
            subprocess.Popen(["wt"])
        return True
    except FileNotFoundError:
        try:
            cmd = f'start cmd /K "cd /d {cwd}"' if cwd else "start cmd"
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception:
            return False


def spawn_claude_code_build(prompt: str, project_name: Optional[str] = None) -> str:
    """Spawn a Claude Code subprocess to build a project. Returns task_id."""
    task_id = str(uuid.uuid4())[:8]
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    if not project_name:
        words = prompt.lower().split()[:3]
        project_name = "-".join(w for w in words if w.isalpha()) or "jarvis-project"

    project_dir = PROJECTS_DIR / f"{project_name}-{task_id}"
    project_dir.mkdir(parents=True, exist_ok=True)

    tracking.register_build(task_id, prompt, str(project_dir))

    script = project_dir / "_jarvis_build.ps1"
    script.write_text(
        f'Set-Location "{project_dir}"\n'
        f'echo "{prompt}" | {CLAUDE_CODE_PATH} --print\n',
        encoding="utf-8",
    )

    try:
        proc = subprocess.Popen(
            ["powershell", "-File", str(script)],
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        _monitor_build_async(task_id, proc)
    except Exception as e:
        tracking.update_build(task_id, "failed", str(e))

    return task_id


def _monitor_build_async(task_id: str, proc: subprocess.Popen):
    import threading

    def _run():
        try:
            out, _ = proc.communicate(timeout=300)
            status = "done" if proc.returncode == 0 else "failed"
            tracking.update_build(task_id, status, out or "")
        except subprocess.TimeoutExpired:
            proc.kill()
            tracking.update_build(task_id, "failed", "Timed out after 5 minutes.")
        except Exception as e:
            tracking.update_build(task_id, "failed", str(e))

    threading.Thread(target=_run, daemon=True).start()


def connect_to_project(project_path: str) -> str:
    """Open Claude Code in an existing project directory. Returns task_id."""
    task_id = str(uuid.uuid4())[:8]
    path = Path(project_path).expanduser()
    tracking.register_build(task_id, f"Connect to {path}", str(path))
    try:
        subprocess.Popen(
            [CLAUDE_CODE_PATH],
            cwd=str(path),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        tracking.update_build(task_id, "done", "Claude Code opened.")
    except Exception as e:
        tracking.update_build(task_id, "failed", str(e))
    return task_id


def do_research(topic: str, output_dir: Optional[str] = None) -> str:
    """Spawn a Claude Opus research task. Returns task_id."""
    task_id = str(uuid.uuid4())[:8]
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = Path(output_dir) if output_dir else PROJECTS_DIR / f"research-{task_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    tracking.register_build(task_id, f"Research: {topic}", str(out_dir))

    script = out_dir / "_research.ps1"
    safe_topic = topic.replace('"', "'")
    script.write_text(
        f'$topic = "{safe_topic}"\n'
        f'$prompt = "Research this topic thoroughly and produce an HTML report: $topic"\n'
        f'echo $prompt | {CLAUDE_CODE_PATH} --print > "{out_dir / "report.html"}"\n',
        encoding="utf-8",
    )
    try:
        proc = subprocess.Popen(
            ["powershell", "-File", str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        _monitor_build_async(task_id, proc)
    except Exception as e:
        tracking.update_build(task_id, "failed", str(e))

    return task_id
