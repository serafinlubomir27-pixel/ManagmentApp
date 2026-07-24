"""Odosielanie e-mailov cez Resend.

Rovnaký pattern degradácie ako logic/ai_parser.py: keď RESEND_API_KEY nie je
nastavený, e-mail sa NEODOŠLE — len sa zaloguje a vráti False. Appka teda funguje
aj bez e-mailov (dev / early stage), len bez reálnej notifikácie.

ENV:
  RESEND_API_KEY   — API kľúč z resend.com (bez neho no-op)
  MAIL_FROM        — odosielateľ, napr. "Nodus <noreply@tvoja-domena.sk>"
  APP_BASE_URL     — základ URL frontendu pre linky (napr. https://managmentapp.surge.sh)
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"


def app_base_url() -> str:
    return os.environ.get("APP_BASE_URL", "http://localhost:5173").rstrip("/")


def send_email(to: str, subject: str, html: str) -> bool:
    """Odošle e-mail cez Resend. Vráti True ak odoslané, False ak preskočené/zlyhalo.

    Bez RESEND_API_KEY je to no-op (zaloguje a vráti False) — nikdy nezhodí volajúci flow.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.info("[mailer] RESEND_API_KEY nie je nastavený — e-mail '%s' pre %s preskočený.", subject, to)
        return False

    mail_from = os.environ.get("MAIL_FROM", "Nodus <onboarding@resend.dev>")
    try:
        import httpx

        resp = httpx.post(
            _RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": mail_from, "to": [to], "subject": subject, "html": html},
            timeout=10.0,
        )
        if resp.status_code >= 400:
            logger.error("[mailer] Resend vrátil %s: %s", resp.status_code, resp.text[:300])
            return False
        return True
    except Exception:
        logger.exception("[mailer] Odoslanie e-mailu zlyhalo (to=%s, subject=%s)", to, subject)
        return False


# ── Šablóny ──────────────────────────────────────────────────────────────────

def _wrap(title: str, body_html: str) -> str:
    return (
        f'<div style="font-family:system-ui,Segoe UI,sans-serif;max-width:520px;margin:0 auto;'
        f'padding:24px;color:#0f172a">'
        f'<h1 style="font-size:20px;margin:0 0 16px">{title}</h1>{body_html}'
        f'<p style="color:#64748b;font-size:12px;margin-top:32px">Nodus — projektový manažment na kritickej ceste</p></div>'
    )


def _button(url: str, label: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;background:#4b7fff;color:#fff;'
        f'text-decoration:none;padding:10px 20px;border-radius:8px;font-weight:600">{label}</a>'
    )


def send_password_reset(to: str, token: str) -> bool:
    url = f"{app_base_url()}/reset-password/{token}"
    body = (
        "<p>Dostali sme žiadosť o reset hesla k tvojmu Nodus účtu. "
        "Odkaz je platný 1 hodinu:</p>"
        f'<p style="margin:24px 0">{_button(url, "Nastaviť nové heslo")}</p>'
        "<p style=\"color:#64748b;font-size:13px\">Ak si o reset nežiadal(a), tento e-mail ignoruj.</p>"
    )
    return send_email(to, "Reset hesla — Nodus", _wrap("Reset hesla", body))


def send_invite(to: str, token: str, org_name: str) -> bool:
    url = f"{app_base_url()}/invite/{token}"
    body = (
        f"<p>Bol(a) si pozvaný(á) do tímu <strong>{org_name}</strong> v aplikácii Nodus.</p>"
        f'<p style="margin:24px 0">{_button(url, "Prijať pozvánku")}</p>'
    )
    return send_email(to, f"Pozvánka do tímu {org_name} — Nodus", _wrap("Pozvánka do tímu", body))
