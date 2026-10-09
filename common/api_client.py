
"""Envoi asynchrone des alertes IA vers l'API SENTINEL-X."""

import logging
import threading
from urllib.parse import urlsplit, urlunsplit

import requests

from . import config as C

log = logging.getLogger("api")


def _get_events_url() -> str:
    """Réutilise l'hôte configuré et cible la route d'événements existante."""

    configured_url = urlsplit(C.API_URL)

    return urlunsplit(
        (
            configured_url.scheme,
            configured_url.netloc,
            "/api/events",
            "",
            "",
        )
    )


def _post(payload: dict) -> None:
    headers = {"Content-Type": "application/json"}

    if C.API_TOKEN:
        headers["Authorization"] = f"Bearer {C.API_TOKEN}"

    try:
        response = requests.post(
            _get_events_url(),
            json=payload,
            headers=headers,
            timeout=5,
            verify=C.API_VERIFY,
        )
        response.raise_for_status()
    except requests.RequestException:
        log.exception("Échec de l'envoi d'une alerte IA vers l'API.")


def post_alert_async(
    alert_type: str,
    severity: str,
    message: str,
    details: dict | None = None,
    source: str = "ia-vision",
) -> None:
    """Envoie une alerte sans bloquer la boucle de détection."""

    event_details = {
        **(details or {}),
        "severity": severity,
        "message": message,
    }

    payload = {
        "type": alert_type,
        "source": source,
        "confidence": event_details.get("confidence"),
        "details": event_details,
    }

    thread = threading.Thread(
        target=_post,
        args=(payload,),
        daemon=True,
    )
    thread.start()