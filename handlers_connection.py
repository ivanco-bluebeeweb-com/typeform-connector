"""Connection lifecycle: connect (verify via /forms), list, disconnect.

Same "secrets-store list of dicts" shape as every other BYOK connector
this session's handlers_connection.py.
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import typeform_client as tf
from app import chat
from schemas import (
    ConnectTypeformParams, ConnectTypeformResult,
    DisconnectTypeformParams, DeleteResult,
    TypeformConnection, ConnectionList, ListConnectionsParams,
)

_CONNECTIONS_SECRET = "typeform_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_CONNECTIONS_SECRET)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_CONNECTIONS_SECRET, json.dumps(connections))


async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        return next((c for c in connections if c.get("id") == connection_id), None)
    return connections[0]


async def resolve_or_error(ctx, connection_id: str = ""):
    conn = await resolve_connection(ctx, connection_id)
    if not conn:
        return None, ActionResult.error(
            "No Typeform account found. Connect one with connect_typeform first.",
            code=tf.TF_NOT_CONNECTED,
        )
    return conn, None


@chat.function(
    "connect_typeform",
    "Connect your own Typeform account by saving its Personal Access Token, after checking it actually works.",
    action_type="write", chain_callable=True, effects=["create:connection"], data_model=ConnectTypeformResult,
)
async def connect_typeform(ctx, params: ConnectTypeformParams) -> ActionResult:
    conn = {"id": str(uuid.uuid4()), "label": params.label, "access_token": params.access_token}
    try:
        resp = await tf.request(ctx, conn, "GET", "/forms", params={"page_size": 1}, action="verify connection")
    except tf.ClientFail as exc:
        return ActionResult.error(exc.payload["message"], code=exc.payload["code"])
    form_count = resp.get("total_items", 0) if isinstance(resp, dict) else 0
    connections = await _load_connections(ctx)
    connections.append(conn)
    await _save_connections(ctx, connections)
    return ActionResult.success(ConnectTypeformResult(
        connection_id=conn["id"], label=params.label, form_count=form_count,
    )), summary="Typeform connected."


@chat.function(
    "disconnect_typeform",
    "Disconnect a Typeform account: deletes the saved Personal Access Token. Nothing in Typeform itself is changed.",
    action_type="write", chain_callable=True, effects=["delete:connection"], data_model=DeleteResult,
)
async def disconnect_typeform(ctx, params: DisconnectTypeformParams) -> ActionResult:
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code=tf.TF_NOT_CONNECTED)
    await _save_connections(ctx, remaining)
    return ActionResult.success(DeleteResult(deleted=True, id=params.connection_id)), summary="Typeform disconnected."


@chat.function(
    "list_connections",
    "List the connected Typeform accounts.",
    action_type="read", chain_callable=True, data_model=ConnectionList,
)
async def list_connections(ctx, params: ListConnectionsParams) -> ActionResult:
    connections = await _load_connections(ctx)
    return ActionResult.success(ConnectionList(connections=[
        TypeformConnection(id=c.get("id", ""), label=c.get("label", "")) for c in connections
    ])), summary="Connections listed."
