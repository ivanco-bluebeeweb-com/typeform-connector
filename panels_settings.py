"""The single 'App settings' screen (center slot) -- connection management
(disconnect per Typeform account) for Typeform Connector. Same convention
as every other connector this session's panels_settings.py.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or "Typeform account"
    return ui.Stack(direction="v", gap=1, align="start", children=[
        ui.Text(label, variant="body"),
        ui.Button(
            "Disconnect", variant="danger", size="sm",
            on_click=ui.Call("disconnect_typeform", {"connection_id": c.get("id")}),
        ),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Stack(direction="v", gap=1, children=[
            ui.Text("Connections", variant="heading"),
            ui.Text("No Typeform accounts connected yet.", variant="caption"),
        ])
    children: list[ui.UINode] = [ui.Text("Connections", variant="heading")]
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


@ext.panel("typeform_settings", slot="center")
async def typeform_settings(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    return ui.Stack(direction="v", gap=3, children=[
        ui.Text("Typeform -- App settings", variant="heading"),
        ui.Divider(),
        _connections_section(connections),
    ])
