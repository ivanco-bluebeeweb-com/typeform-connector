"""Forms, Responses, Workspaces, Webhooks for Typeform Connector.

Confirmed against developers.typeform.com, 2026-08-29:
GET /forms, GET /forms/{id}, DELETE /forms/{id}, PATCH /forms/{id} (title),
GET /forms/{id}/responses, DELETE /forms/{id}/responses?included_tokens=,
GET /workspaces, POST /workspaces,
GET /forms/{id}/webhooks, PUT /forms/{id}/webhooks/{tag},
DELETE /forms/{id}/webhooks/{tag}.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import typeform_client as tf
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    ListFormsParams, FormList, Form,
    GetFormParams, FormDetail,
    DeleteFormParams, DeleteResult,
    UpdateFormTitleParams,
    ListResponsesParams, ResponseList, Response,
    DeleteResponsesParams,
    ListWorkspacesParams, WorkspaceList, Workspace,
    CreateWorkspaceParams, WorkspaceCreateResult,
    ListWebhooksParams, WebhookList, Webhook,
    CreateWebhookParams, WebhookCreateResult,
    DeleteWebhookParams,
)


def _form_entity(f: dict) -> Form:
    return Form(
        id=f.get("id", ""), title=f.get("title", ""),
        last_updated_at=f.get("last_updated_at", ""),
        settings_language=(f.get("settings") or {}).get("language", ""),
    )


@chat.function(
    "list_forms",
    "List forms in the connected Typeform account, optionally filtered to one workspace.",
    action_type="read", chain_callable=True, data_model=FormList,
)
async def list_forms(ctx, params: ListFormsParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    query: dict = {"page_size": 200}
    if params.workspace_id:
        query["workspace_id"] = params.workspace_id
    try:
        resp = await tf.request(ctx, conn, "GET", "/forms", params=query, action="list forms")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    items = resp.get("items", []) if isinstance(resp, dict) else []
    return ActionResult.success(FormList(forms=[_form_entity(f) for f in items]), summary="Forms listed.")


@chat.function(
    "get_form",
    "Read one Typeform form's structure in full, including field count and language.",
    action_type="read", chain_callable=True, data_model=FormDetail,
)
async def get_form(ctx, params: GetFormParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        f = await tf.request(ctx, conn, "GET", f"/forms/{params.form_id}", action="get form")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    return ActionResult.success(FormDetail(
        id=f.get("id", ""), title=f.get("title", ""),
        language=(f.get("settings") or {}).get("language", ""),
        field_count=len(f.get("fields", []) or []),
        last_updated_at=f.get("last_updated_at", ""),
    ), summary="Form retrieved.")


@chat.function(
    "delete_form",
    "Move a Typeform form to trash. Recoverable from the Typeform UI for a limited time.",
    action_type="write", chain_callable=True, effects=["delete:form"], data_model=DeleteResult,
)
async def delete_form(ctx, params: DeleteFormParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        await tf.request(ctx, conn, "DELETE", f"/forms/{params.form_id}", action="delete form")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    return ActionResult.success(DeleteResult(deleted=True, id=params.form_id), summary="Form deleted.")


@chat.function(
    "update_form_title",
    "Rename an existing Typeform form.",
    action_type="write", chain_callable=True, effects=["update:form"], data_model=FormDetail,
)
async def update_form_title(ctx, params: UpdateFormTitleParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    body = [{"op": "replace", "path": "/title", "value": params.title}]
    try:
        f = await tf.request(ctx, conn, "PATCH", f"/forms/{params.form_id}", json_body=body, action="rename form")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    return ActionResult.success(FormDetail(
        id=f.get("id", params.form_id), title=f.get("title", params.title),
        language=(f.get("settings") or {}).get("language", ""),
        field_count=len(f.get("fields", []) or []),
        last_updated_at=f.get("last_updated_at", ""),
    ), summary="Form title updated.")


@chat.function(
    "list_responses",
    "List responses collected for a Typeform form, with optional date-range and completion filters.",
    action_type="read", chain_callable=True, data_model=ResponseList,
)
async def list_responses(ctx, params: ListResponsesParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    query: dict = {"page_size": params.page_size}
    if params.since:
        query["since"] = params.since
    if params.until:
        query["until"] = params.until
    if params.completed is not None:
        query["completed"] = "true" if params.completed else "false"
    try:
        resp = await tf.request(ctx, conn, "GET", f"/forms/{params.form_id}/responses", params=query, action="list responses")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    items = resp.get("items", []) if isinstance(resp, dict) else []
    responses = [
        Response(
            response_id=r.get("response_id") or r.get("token", ""),
            submitted_at=r.get("submitted_at", ""), landed_at=r.get("landed_at", ""),
            is_completed=bool(r.get("submitted_at")),
        ) for r in items
    ]
    return ActionResult.success(ResponseList(total_items=resp.get("total_items", 0) if isinstance(resp, dict) else 0, responses=responses), summary="Responses listed.")


@chat.function(
    "delete_responses",
    "Permanently delete one or more responses from a Typeform form. Cannot be undone.",
    action_type="write", chain_callable=True, effects=["delete:response"], data_model=DeleteResult,
)
async def delete_responses(ctx, params: DeleteResponsesParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    query = {"included_tokens": ",".join(params.response_ids)}
    try:
        await tf.request(ctx, conn, "DELETE", f"/forms/{params.form_id}/responses", params=query, action="delete responses")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    return ActionResult.success(DeleteResult(deleted=True, id=",".join(params.response_ids)), summary="Responses deleted.")


@chat.function(
    "list_workspaces",
    "List workspaces (folders that organize forms) in the connected Typeform account.",
    action_type="read", chain_callable=True, data_model=WorkspaceList,
)
async def list_workspaces(ctx, params: ListWorkspacesParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        resp = await tf.request(ctx, conn, "GET", "/workspaces", action="list workspaces")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    items = resp.get("items", []) if isinstance(resp, dict) else []
    workspaces = [
        Workspace(id=w.get("id", ""), name=w.get("name", ""), form_count=(w.get("forms") or {}).get("count", 0))
        for w in items
    ]
    return ActionResult.success(WorkspaceList(workspaces=workspaces), summary="Workspaces listed.")


@chat.function(
    "create_workspace",
    "Create a new workspace (folder) to organize Typeform forms.",
    action_type="write", chain_callable=True, effects=["create:workspace"], data_model=WorkspaceCreateResult,
)
async def create_workspace(ctx, params: CreateWorkspaceParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        w = await tf.request(ctx, conn, "POST", "/workspaces", json_body={"name": params.name}, action="create workspace")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    return ActionResult.success(WorkspaceCreateResult(id=w.get("id", ""), name=w.get("name", params.name)), summary="Workspace created.")


@chat.function(
    "list_webhooks",
    "List webhooks configured on one Typeform form.",
    action_type="read", chain_callable=True, data_model=WebhookList,
)
async def list_webhooks(ctx, params: ListWebhooksParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        resp = await tf.request(ctx, conn, "GET", f"/forms/{params.form_id}/webhooks", action="list webhooks")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    items = resp.get("webhooks", []) if isinstance(resp, dict) else []
    webhooks = [Webhook(tag=w.get("tag", ""), url=w.get("url", ""), enabled=w.get("enabled", False)) for w in items]
    return ActionResult.success(WebhookList(webhooks=webhooks), summary="Webhooks listed.")


@chat.function(
    "create_webhook",
    "Create (or overwrite) a webhook on a Typeform form: Typeform will POST each new response to your URL.",
    action_type="write", chain_callable=True, effects=["create:webhook"], data_model=WebhookCreateResult,
)
async def create_webhook(ctx, params: CreateWebhookParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    body = {"url": params.url, "enabled": params.enabled}
    try:
        w = await tf.request(ctx, conn, "PUT", f"/forms/{params.form_id}/webhooks/{params.tag}", json_body=body, action="create webhook")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    return ActionResult.success(WebhookCreateResult(tag=w.get("tag", params.tag), url=w.get("url", params.url), enabled=w.get("enabled", params.enabled)), summary="Webhook created.")


@chat.function(
    "delete_webhook",
    "Permanently remove a webhook from a Typeform form. Cannot be undone.",
    action_type="write", chain_callable=True, effects=["delete:webhook"], data_model=DeleteResult,
)
async def delete_webhook(ctx, params: DeleteWebhookParams) -> ActionResult:
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if err:
        return err
    try:
        await tf.request(ctx, conn, "DELETE", f"/forms/{params.form_id}/webhooks/{params.tag}", action="delete webhook")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    return ActionResult.success(DeleteResult(deleted=True, id=params.tag), summary="Webhook deleted.")
