"""Value-add reports for Typeform Connector -- account form overview,
same "aggregate raw records into one glance" shape as every other
connector's handlers_reports.py this session.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import typeform_client as tf
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    AuditTypeformAccountParams, TypeformAccountReport,
)


@chat.function(
    "audit_typeform_account",
    "Build one aggregated form activity report for the connected Typeform account: total forms and "
    "forms that appear stale (not updated recently).",
    action_type="read", chain_callable=True, data_model=TypeformAccountReport,
)
async def audit_typeform_account(ctx, params: AuditTypeformAccountParams) -> ActionResult:
    """Scan /forms and flag forms whose last_updated_at is oldest."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        resp = await tf.request(ctx, conn, "GET", "/forms", params={"page_size": 200}, action="list forms for audit")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    items = resp.get("items", []) if isinstance(resp, dict) else []
    sorted_items = sorted(items, key=lambda f: f.get("last_updated_at", ""))
    stalest = [f.get("title", "") for f in sorted_items[:10]]
    return ActionResult.success(TypeformAccountReport(
        total_forms=len(items),
        stalest_forms=stalest,
    ), summary="Typeform account audit ready.")
