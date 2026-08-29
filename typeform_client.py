"""Thin HTTP client for Typeform API + Bearer PAT auth.

Same "fail()-dict + ClientFail exception + generic request() helper"
shape as every other connector this session's *_client.py. Confirmed
against developers.typeform.com, 2026-08-29:

- Base URL: https://api.typeform.com
- Auth header: Authorization: Bearer {access_token}
- Resources: /forms, /forms/{id}/responses, /workspaces, /webhooks
  (/forms/{form_id}/webhooks/{tag}).
"""
from __future__ import annotations

import json
from typing import Any

import httpx

TF_NOT_CONNECTED = "TYPEFORM_NOT_CONNECTED"
TF_UNAUTHORIZED = "TYPEFORM_UNAUTHORIZED"
TF_FORBIDDEN = "TYPEFORM_FORBIDDEN"
TF_NOT_FOUND = "TYPEFORM_NOT_FOUND"
TF_RATE_LIMITED = "TYPEFORM_RATE_LIMITED"
TF_BACKEND_ERROR = "TYPEFORM_BACKEND_ERROR"
TF_VALIDATION_FAILED = "TYPEFORM_VALIDATION_FAILED"
TF_RESPONSE_UNEXPECTED = "TYPEFORM_RESPONSE_UNEXPECTED"

_MESSAGES = {
    TF_NOT_CONNECTED: "No Typeform account connected. Connect one first.",
    TF_UNAUTHORIZED: "Typeform rejected the access token as invalid or expired.",
    TF_FORBIDDEN: "Typeform denied access to this resource.",
    TF_NOT_FOUND: "That Typeform record was not found.",
    TF_RATE_LIMITED: "Typeform rate-limited this request. Try again shortly.",
    TF_BACKEND_ERROR: "Typeform returned an error.",
    TF_VALIDATION_FAILED: "Typeform rejected the request as invalid.",
    TF_RESPONSE_UNEXPECTED: "Typeform returned an unexpected response shape.",
}


def fail(code: str, detail: str = "") -> dict:
    msg = _MESSAGES.get(code, "Typeform request failed.")
    if detail:
        msg = f"{msg} ({detail})"
    return {"code": code, "message": msg}


class ClientFail(Exception):
    def __init__(self, payload: dict):
        super().__init__(payload.get("message", "Typeform request failed."))
        self.payload = payload


def _base_url() -> str:
    return "https://api.typeform.com"


async def request(
    ctx, conn: dict, method: str, path: str,
    params: dict | None = None, json_body: Any = None, action: str = "",
) -> Any:
    token = conn.get("access_token", "")
    if not token:
        raise ClientFail(fail(TF_NOT_CONNECTED))
    url = f"{_base_url()}{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(method, url, params=params, json=json_body, headers=headers)
        except httpx.RequestError as exc:
            raise ClientFail(fail(TF_BACKEND_ERROR, str(exc))) from exc

    if resp.status_code == 401:
        raise ClientFail(fail(TF_UNAUTHORIZED))
    if resp.status_code == 403:
        raise ClientFail(fail(TF_FORBIDDEN))
    if resp.status_code == 404:
        raise ClientFail(fail(TF_NOT_FOUND))
    if resp.status_code == 429:
        raise ClientFail(fail(TF_RATE_LIMITED))
    if resp.status_code == 422 or resp.status_code == 400:
        detail = ""
        try:
            detail = resp.json().get("description", "") or resp.text[:200]
        except (json.JSONDecodeError, ValueError):
            detail = resp.text[:200]
        raise ClientFail(fail(TF_VALIDATION_FAILED, detail))
    if resp.status_code >= 500:
        raise ClientFail(fail(TF_BACKEND_ERROR, f"HTTP {resp.status_code} on {action or path}"))
    if resp.status_code >= 400:
        detail = ""
        try:
            detail = resp.json().get("description", "") or resp.text[:200]
        except (json.JSONDecodeError, ValueError):
            detail = resp.text[:200]
        raise ClientFail(fail(TF_BACKEND_ERROR, detail or f"HTTP {resp.status_code}"))

    if resp.status_code == 204 or not resp.content:
        return {}
    try:
        return resp.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise ClientFail(fail(TF_RESPONSE_UNEXPECTED, str(exc))) from exc
