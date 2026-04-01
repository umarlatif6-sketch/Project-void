import os
import logging
import base64
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

_cached_settings = None
_cache_expires_at = 0


def _get_access_token() -> str:
    global _cached_settings, _cache_expires_at

    now = time.time()
    if _cached_settings and _cache_expires_at > now + 60:
        return _cached_settings["access_token"]

    hostname = os.environ.get("REPLIT_CONNECTORS_HOSTNAME")
    repl_identity = os.environ.get("REPL_IDENTITY")
    web_repl_renewal = os.environ.get("WEB_REPL_RENEWAL")

    if repl_identity:
        token = "repl " + repl_identity
    elif web_repl_renewal:
        token = "depl " + web_repl_renewal
    else:
        raise RuntimeError("No Replit identity token found (REPL_IDENTITY / WEB_REPL_RENEWAL)")

    if not hostname:
        raise RuntimeError("REPLIT_CONNECTORS_HOSTNAME not set")

    import urllib.request
    url = f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-mail"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "X-Replit-Token": token})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    items = data.get("items", [])
    if not items:
        raise RuntimeError("Gmail not connected — no items returned from connectors API")

    settings = items[0].get("settings", {})
    access_token = settings.get("access_token") or (
        settings.get("oauth", {}).get("credentials", {}).get("access_token")
    )
    if not access_token:
        raise RuntimeError("Gmail access token not found in connection settings")

    expires_at_str = settings.get("expires_at")
    if expires_at_str:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            _cache_expires_at = dt.timestamp()
        except Exception:
            _cache_expires_at = now + 3500
    else:
        _cache_expires_at = now + 3500

    _cached_settings = {"access_token": access_token}
    return access_token


def send_email(to: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Send an email via Gmail API using the connected Replit Gmail integration."""
    try:
        import urllib.request

        access_token = _get_access_token()

        msg = MIMEMultipart("alternative")
        msg["To"] = to
        msg["Subject"] = subject
        msg["From"] = "me"

        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        payload = json.dumps({"raw": raw}).encode("utf-8")

        req = urllib.request.Request(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            logger.info("[Gmail] Email sent to %s, message id: %s", to, result.get("id"))
            return True

    except Exception as e:
        logger.error("[Gmail] Failed to send email to %s: %s", to, e)
        return False
