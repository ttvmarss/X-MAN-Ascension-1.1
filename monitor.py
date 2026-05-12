"""Background monitoring: check build task status, system resources, etc."""
import asyncio
import os
import time
from typing import Callable, Optional

import tracking


async def poll_builds(callback: Callable[[str, dict], None], interval: int = 10):
    """Periodically check for completed builds and call callback(task_id, build_info)."""
    notified: set[str] = set()
    while True:
        await asyncio.sleep(interval)
        try:
            conn = tracking._get_conn()
            rows = conn.execute(
                "SELECT * FROM build_tasks WHERE status IN ('done','failed') AND id NOT IN ({})".format(
                    ",".join("?" * len(notified)) if notified else "'_'"
                ),
                list(notified) if notified else [],
            ).fetchall()
            conn.close()
            for row in rows:
                build = dict(row)
                notified.add(build["id"])
                await callback(build["id"], build)
        except Exception:
            pass


def get_system_info() -> dict:
    try:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_used_gb": round(psutil.virtual_memory().used / 1e9, 1),
            "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
        }
    except ImportError:
        return {}
