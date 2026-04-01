import os
import logging
import base64
import json
import time
import urllib.error
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


def _gmail_get(path: str, params=None) -> dict:
    """
    Make a GET request to the Gmail API. Raises on scope/auth errors.
    params may be a dict or a list of (key, value) tuples to support repeated keys.
    """
    import urllib.request
    import urllib.parse
    access_token = _get_access_token()
    url = f"https://gmail.googleapis.com/gmail/v1/{path}"
    if params:
        if isinstance(params, dict):
            params = list(params.items())
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        if e.code in (401, 403):
            raise PermissionError(f"Gmail read access denied (HTTP {e.code}). Re-authorise Gmail with gmail.readonly scope. Detail: {body}") from e
        raise RuntimeError(f"Gmail API error {e.code}: {body}") from e


def _get_message_headers(msg_id: str) -> dict:
    """Fetch subject, from, to, date headers for a single message."""
    try:
        params = [
            ("format", "metadata"),
            ("metadataHeaders", "Subject"),
            ("metadataHeaders", "From"),
            ("metadataHeaders", "To"),
            ("metadataHeaders", "Date"),
        ]
        data = _gmail_get(f"users/me/messages/{msg_id}", params)
        headers = {h["name"].lower(): h["value"] for h in data.get("payload", {}).get("headers", [])}
        return {
            "id": msg_id,
            "subject": headers.get("subject", ""),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "date": headers.get("date", ""),
        }
    except Exception as e:
        logger.warning("[Gmail] Could not fetch headers for message %s: %s", msg_id, e)
        return {"id": msg_id, "subject": "", "from": "", "to": "", "date": ""}


def list_sent_to_addresses(email_addresses: list, max_results: int = 200) -> dict:
    """
    Check the SENT folder for emails sent to any of the given addresses.
    Returns a dict: {email_address: [{"subject": ..., "date": ...}, ...]}
    Raises PermissionError if read scopes are missing.
    """
    sent_map = {addr.lower(): [] for addr in email_addresses}

    try:
        data = _gmail_get("users/me/messages", {
            "labelIds": "SENT",
            "maxResults": max_results,
        })
    except PermissionError:
        raise
    except Exception as e:
        logger.error("[Gmail] list_sent_to_addresses failed: %s", e)
        return sent_map

    message_stubs = data.get("messages", [])
    for stub in message_stubs:
        try:
            info = _get_message_headers(stub["id"])
            to_raw = info.get("to", "").lower()
            for addr in sent_map:
                if addr in to_raw:
                    sent_map[addr].append({
                        "subject": info.get("subject", ""),
                        "date": info.get("date", ""),
                    })
        except Exception:
            continue

    return sent_map


def check_inbox_for_replies(email_addresses: list, max_results: int = 200) -> dict:
    """
    Check the INBOX for messages FROM any of the given addresses (i.e. replies received).
    Returns a dict: {email_address: [{"subject": ..., "date": ...}, ...]}
    Raises PermissionError if read scopes are missing.
    """
    reply_map = {addr.lower(): [] for addr in email_addresses}

    try:
        data = _gmail_get("users/me/messages", {
            "labelIds": "INBOX",
            "maxResults": max_results,
        })
    except PermissionError:
        raise
    except Exception as e:
        logger.error("[Gmail] check_inbox_for_replies failed: %s", e)
        return reply_map

    message_stubs = data.get("messages", [])
    for stub in message_stubs:
        try:
            info = _get_message_headers(stub["id"])
            from_raw = info.get("from", "").lower()
            for addr in reply_map:
                if addr in from_raw:
                    reply_map[addr].append({
                        "subject": info.get("subject", ""),
                        "date": info.get("date", ""),
                    })
        except Exception:
            continue

    return reply_map


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
