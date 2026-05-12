"""Windows Mail integration via Outlook COM or stub fallback."""
import os
from typing import Optional


BACKEND = os.getenv("MAIL_BACKEND", "auto")


def _try_outlook() -> bool:
    try:
        import win32com.client  # noqa: F401
        return True
    except ImportError:
        return False


def _get_outlook_emails(max_count: int = 10) -> list[dict]:
    import win32com.client
    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    inbox = ns.GetDefaultFolder(6)  # 6 = olFolderInbox
    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)

    emails = []
    count = 0
    for msg in messages:
        if count >= max_count:
            break
        try:
            if msg.UnRead:
                emails.append({
                    "subject": msg.Subject,
                    "sender": msg.SenderName,
                    "sender_email": msg.SenderEmailAddress,
                    "received": str(msg.ReceivedTime),
                    "preview": msg.Body[:300] if msg.Body else "",
                    "unread": True,
                })
                count += 1
        except Exception:
            continue
    return emails


def get_unread_emails(max_count: int = 10) -> list[dict]:
    if BACKEND == "outlook" or (BACKEND == "auto" and _try_outlook()):
        try:
            return _get_outlook_emails(max_count)
        except Exception:
            pass
    return []


def format_emails_for_speech(emails: list[dict]) -> str:
    if not emails:
        return "No unread messages, sir."
    count = len(emails)
    if count == 1:
        e = emails[0]
        return (
            f"You have one unread message from {e['sender']}: "
            f"\"{e['subject']}\". Received {e.get('received', 'recently')}."
        )
    senders = ", ".join(e["sender"] for e in emails[:3])
    suffix = f" and {count - 3} others" if count > 3 else ""
    return (
        f"You have {count} unread messages from {senders}{suffix}. "
        f"Shall I read any of them, sir?"
    )
