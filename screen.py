"""Windows screen awareness via PIL ImageGrab and win32gui."""
import os
import base64
from typing import Optional


ENABLED = os.getenv("SCREEN_AWARENESS", "true").lower() == "true"


def get_active_window_title() -> str:
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def capture_screenshot() -> Optional[bytes]:
    if not ENABLED:
        return None
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img = img.resize((1280, 720))
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        return buf.getvalue()
    except Exception:
        return None


def get_screen_context() -> str:
    title = get_active_window_title()
    if not title:
        return ""
    return f"Active window: {title}"


def screenshot_as_base64() -> Optional[str]:
    data = capture_screenshot()
    if data is None:
        return None
    return base64.b64encode(data).decode()
