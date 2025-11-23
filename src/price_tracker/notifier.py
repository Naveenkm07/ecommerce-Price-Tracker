"""Notifier module for sending price drop notifications.

Responsibilities:
- Provide an email notification interface using `smtplib`.
- Load SMTP configuration from environment variables or a config file
  (e.g., server, port, sender email, password).
- Expose a function to send a price drop email to the user.

Security note:
- Do NOT hardcode real credentials in this module.

Note: This file currently contains only function definitions and docstrings.
"""

import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional, Tuple


_LAST_NOTIFIED: Dict[Tuple[str, str], datetime] = {}
_COOLDOWN_MINUTES = 60


def _load_smtp_config(config_path: Optional[str]) -> Dict[str, object]:
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "SMTP_HOST": os.getenv("SMTP_HOST"),
            "SMTP_PORT": os.getenv("SMTP_PORT"),
            "SMTP_USER": os.getenv("SMTP_USER"),
            "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
            "SENDER_EMAIL": os.getenv("SENDER_EMAIL"),
        }

    host = data.get("SMTP_HOST") or data.get("smtp_host")
    port_raw = data.get("SMTP_PORT") or data.get("smtp_port")
    user = data.get("SMTP_USER") or data.get("smtp_user")
    password = data.get("SMTP_PASSWORD") or data.get("smtp_password")
    sender = data.get("SENDER_EMAIL") or data.get("sender_email")

    port: Optional[int]
    if port_raw is None or port_raw == "":
        port = 587
    else:
        try:
            port = int(port_raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            port = 587

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "sender": sender,
    }


def _can_send(key: Tuple[str, str]) -> bool:
    last = _LAST_NOTIFIED.get(key)
    if last is None:
        return True
    return datetime.utcnow() - last >= timedelta(minutes=_COOLDOWN_MINUTES)


def send_price_drop_email(
    user_email: str,
    product_name: str,
    product_url: str,
    current_price: float,
    target_price: float,
    config_path: Optional[str] = None,
) -> bool:
    """Send an email notification about a product price drop.

    Args:
        user_email (str): Recipient email address.
        product_name (str): Name of the product.
        product_url (str): URL of the product page.
        current_price (float): Latest price of the product.
        target_price (float): User-defined target price.
        config_path (Optional[str]): Optional path to a configuration file
            containing SMTP settings. If not provided, the implementation
            may fall back to environment variables.

    This implementation loads SMTP configuration, applies a simple
    in-memory cooldown per (recipient, product URL), and uses
    :mod:`smtplib` to send a text email.
    """

    key = (user_email, product_url)
    if not _can_send(key):
        return False

    cfg = _load_smtp_config(config_path)
    host = cfg["host"]
    port = cfg["port"]
    user = cfg["user"]
    password = cfg["password"]
    sender = cfg["sender"]

    if not (host and port and user and password and sender and user_email):
        return False

    subject = f"Price Drop Alert: {product_name}"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    body = (
        "Price drop detected for one of your tracked products.\n\n"
        f"Product: {product_name}\n"
        f"URL: {product_url}\n"
        f"Current price: {current_price}\n"
        f"Target price: {target_price}\n"
        f"Time: {timestamp}\n"
    )

    message = MIMEMultipart()
    message["From"] = str(sender)
    message["To"] = user_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    try:
        port_int = int(port)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        port_int = 587

    try:
        if port_int == 465:
            server: smtplib.SMTP = smtplib.SMTP_SSL(host, port_int, timeout=10)  # type: ignore[arg-type]
        else:
            server = smtplib.SMTP(host, port_int, timeout=10)  # type: ignore[arg-type]
            server.starttls()

        server.login(str(user), str(password))
        server.sendmail(str(sender), [user_email], message.as_string())
        server.quit()
    except Exception:
        return False

    _LAST_NOTIFIED[key] = datetime.utcnow()
    return True


def send_sms_notification(phone_number: str, message: str) -> bool:
    """Stub for future SMS notification integration.

    Returns ``False`` to indicate that SMS sending is not implemented in
    this mini-project version.
    """

    return False


def send_push_notification(title: str, message: str) -> bool:
    """Stub for future desktop or push notification integration.

    Returns ``False`` to indicate that push notifications are not
    implemented in this mini-project version.
    """

    return False
