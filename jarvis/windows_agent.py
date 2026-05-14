"""
JARVIS Windows PC Agent — connects your Windows PC to the JARVIS cloud server.

Run this on your Windows machine. It connects to your cloud JARVIS server via
WebSocket and lets JARVIS control your PC remotely:
- Open apps, files, folders
- Run PowerShell commands
- System info (CPU, RAM, disk)
- File management
- Browser control

Usage:
  python windows_agent.py --server wss://your-server:8340 --token YOUR_AUTH_TOKEN

Install dependencies:
  pip install websockets psutil pyautogui
"""

import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Optional: pip install psutil  (for system monitoring)")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [windows-agent] %(message)s")
log = logging.getLogger("jarvis.windows")

AGENT_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# PC Control Functions
# ---------------------------------------------------------------------------

def get_system_info() -> dict:
    """Get current system stats."""
    info = {
        "platform": platform.system(),
        "hostname": platform.node(),
        "python": platform.python_version(),
        "agent_version": AGENT_VERSION,
    }
    if HAS_PSUTIL:
        info.update({
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_used_gb": round(psutil.virtual_memory().used / 1e9, 1),
            "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
            "disk_percent": psutil.disk_usage("/").percent if os.path.exists("/") else psutil.disk_usage("C:\\").percent,
        })
    return info


def open_app(app_name: str) -> dict:
    """Open an application by name."""
    try:
        if platform.system() == "Windows":
            # Try common apps by name
            app_map = {
                "chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "explorer": "explorer.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "task manager": "taskmgr.exe",
                "spotify": "spotify.exe",
                "discord": "discord.exe",
                "steam": "steam.exe",
                "obs": "obs64.exe",
                "vscode": "code.exe",
                "vs code": "code.exe",
            }
            exe = app_map.get(app_name.lower(), app_name)
            subprocess.Popen([exe], shell=True)
            return {"success": True, "message": f"Opened {app_name}."}
        else:
            subprocess.Popen(["xdg-open", app_name], shell=False)
            return {"success": True, "message": f"Opened {app_name}."}
    except Exception as e:
        return {"success": False, "message": f"Could not open {app_name}: {e}"}


def run_powershell(command: str, timeout: int = 30) -> dict:
    """Run a PowerShell command and return output."""
    try:
        if platform.system() != "Windows":
            return {"success": False, "output": "PowerShell only available on Windows."}
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip() or result.stderr.strip()
        return {
            "success": result.returncode == 0,
            "output": output[:2000],  # Limit output size
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"Command timed out after {timeout}s."}
    except Exception as e:
        return {"success": False, "output": str(e)}


def open_url(url: str) -> dict:
    """Open a URL in the default browser."""
    try:
        import webbrowser
        webbrowser.open(url)
        return {"success": True, "message": f"Opened {url} in browser."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def list_files(path: str = None) -> dict:
    """List files in a directory."""
    try:
        target = Path(path) if path else Path.home() / "Desktop"
        if not target.exists():
            target = Path.home()
        files = []
        for item in sorted(target.iterdir()):
            files.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
            })
        return {"success": True, "path": str(target), "files": files[:50]}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_running_processes() -> dict:
    """Get list of running processes."""
    if not HAS_PSUTIL:
        return {"success": False, "message": "psutil not installed"}
    try:
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                procs.append({
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "cpu": round(proc.info["cpu_percent"] or 0, 1),
                    "mem": round(proc.info["memory_percent"] or 0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        # Sort by CPU usage descending
        procs.sort(key=lambda x: x["cpu"], reverse=True)
        return {"success": True, "processes": procs[:20]}
    except Exception as e:
        return {"success": False, "message": str(e)}


def kill_process(name_or_pid: str) -> dict:
    """Kill a process by name or PID."""
    if not HAS_PSUTIL:
        return {"success": False, "message": "psutil not installed"}
    try:
        killed = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"].lower() == name_or_pid.lower() or str(proc.info["pid"]) == name_or_pid:
                    proc.kill()
                    killed.append(proc.info["name"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if killed:
            return {"success": True, "message": f"Killed: {', '.join(killed)}"}
        return {"success": False, "message": f"No process found matching '{name_or_pid}'"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def shutdown_pc(action: str = "shutdown") -> dict:
    """Shutdown, restart, or sleep the PC."""
    try:
        if platform.system() == "Windows":
            cmds = {
                "shutdown": ["shutdown", "/s", "/t", "10"],
                "restart": ["shutdown", "/r", "/t", "10"],
                "sleep": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                "cancel": ["shutdown", "/a"],
            }
        else:
            cmds = {
                "shutdown": ["shutdown", "-h", "now"],
                "restart": ["reboot"],
                "sleep": ["systemctl", "suspend"],
                "cancel": [],
            }
        cmd = cmds.get(action.lower())
        if not cmd:
            return {"success": False, "message": f"Unknown action: {action}"}
        subprocess.Popen(cmd)
        return {"success": True, "message": f"PC {action} initiated."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# Command Dispatcher
# ---------------------------------------------------------------------------

def handle_command(cmd: dict) -> dict:
    """Dispatch an incoming command from JARVIS server."""
    action = cmd.get("action", "")
    params = cmd.get("params", {})

    handlers = {
        "system_info": lambda: get_system_info(),
        "open_app": lambda: open_app(params.get("app", "")),
        "run_powershell": lambda: run_powershell(params.get("command", ""), params.get("timeout", 30)),
        "open_url": lambda: open_url(params.get("url", "")),
        "list_files": lambda: list_files(params.get("path")),
        "running_processes": lambda: get_running_processes(),
        "kill_process": lambda: kill_process(params.get("target", "")),
        "shutdown": lambda: shutdown_pc(params.get("action", "shutdown")),
        "ping": lambda: {"success": True, "message": "pong", "info": get_system_info()},
    }

    handler = handlers.get(action)
    if not handler:
        return {"success": False, "message": f"Unknown command: {action}"}

    try:
        return handler()
    except Exception as e:
        log.error(f"Command '{action}' failed: {e}")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# WebSocket Connection to JARVIS Cloud Server
# ---------------------------------------------------------------------------

class WindowsAgent:
    def __init__(self, server_url: str, auth_token: str = ""):
        self.server_url = server_url
        self.auth_token = auth_token
        self._reconnect_delay = 3
        self._running = True

    async def connect(self):
        """Main connection loop with auto-reconnect."""
        while self._running:
            try:
                log.info(f"Connecting to JARVIS server: {self.server_url}")
                headers = {}
                if self.auth_token:
                    headers["Authorization"] = f"Bearer {self.auth_token}"

                async with websockets.connect(
                    self.server_url,
                    extra_headers=headers,
                    ping_interval=30,
                    ping_timeout=10,
                ) as ws:
                    self._reconnect_delay = 3  # Reset on successful connect
                    log.info("Connected to JARVIS server!")

                    # Announce ourselves
                    await ws.send(json.dumps({
                        "type": "agent_hello",
                        "agent": "windows",
                        "version": AGENT_VERSION,
                        "system": get_system_info(),
                    }))

                    async for message in ws:
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type", "")

                            if msg_type == "pc_command":
                                log.info(f"Command received: {data.get('action')}")
                                result = handle_command(data)
                                await ws.send(json.dumps({
                                    "type": "pc_result",
                                    "command_id": data.get("command_id"),
                                    "result": result,
                                }))
                            elif msg_type == "ping":
                                await ws.send(json.dumps({"type": "pong"}))
                        except json.JSONDecodeError:
                            log.warning(f"Bad message: {message[:100]}")
                        except Exception as e:
                            log.error(f"Message error: {e}")

            except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                log.warning(f"Disconnected: {e}. Reconnecting in {self._reconnect_delay}s...")
            except Exception as e:
                log.error(f"Unexpected error: {e}")

            if self._running:
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, 60)

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# WebSocket endpoint on JARVIS server side (added to server.py)
# This section documents the /ws/pc endpoint the agent connects to.
# ---------------------------------------------------------------------------

# The server expects the agent to connect to: /ws/pc
# Messages from server to agent: {"type": "pc_command", "action": "...", "params": {...}, "command_id": "..."}
# Messages from agent to server: {"type": "pc_result", "command_id": "...", "result": {...}}
#                                 {"type": "agent_hello", "agent": "windows", "version": "...", "system": {...}}


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="JARVIS Windows PC Agent")
    parser.add_argument("--server", default=os.getenv("JARVIS_SERVER", ""),
                        help="JARVIS server WebSocket URL (e.g. wss://your-server:8340/ws/pc)")
    parser.add_argument("--token", default=os.getenv("AUTH_TOKEN", ""),
                        help="Auth token (set AUTH_TOKEN env var or pass here)")
    args = parser.parse_args()

    if not args.server:
        print("\nJARVIS Windows Agent")
        print("=" * 40)
        print("Usage: python windows_agent.py --server wss://YOUR_SERVER:8340/ws/pc")
        print("\nOr set environment variables:")
        print("  JARVIS_SERVER=wss://your-server:8340/ws/pc")
        print("  AUTH_TOKEN=your_auth_token  (if server requires auth)")
        print("\nInstall dependencies:")
        print("  pip install websockets psutil")
        sys.exit(1)

    # Ensure URL ends with /ws/pc
    url = args.server
    if not url.endswith("/ws/pc"):
        url = url.rstrip("/") + "/ws/pc"

    print(f"\nJARVIS Windows Agent v{AGENT_VERSION}")
    print(f"Server: {url}")
    print(f"Auth: {'yes' if args.token else 'none'}")
    print(f"System: {platform.node()} ({platform.system()})")
    print("-" * 40)
    print("Connecting... (Ctrl+C to stop)")

    agent = WindowsAgent(url, args.token)
    try:
        await agent.connect()
    except KeyboardInterrupt:
        agent.stop()
        print("\nAgent stopped.")


if __name__ == "__main__":
    asyncio.run(main())
