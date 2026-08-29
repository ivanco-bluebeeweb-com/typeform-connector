"""Panel UI -- connections list/connect form + the one required "App
settings" entry point. Uses slot="left" (SDK valid slots are
['bottom','center','chat-sidebar','left','overlay','right'] -- confirmed
against the SDK's own ValueError after SurveyMonkey Connector's build
failure) and the corrected Form/Input kwargs (ui.Form(submit_label=...),
ui.Text(variant="label") for each Input).

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule. Disconnect lives only in the
"App settings" screen (panels_settings.py). The one secondary "App
settings" button is always the LAST element at the bottom of the sidebar.

PER ~/UI_INTERFACE_STANDARD.md (2026-08-21 addendum): every Input carries
its own visible label, the placeholder text is always contextually
specific, the form's own container is stretched to the full width of the
left sidebar, and the form's inner content is stretched to fill that
container. The "How do I set this up?" instructions live ONLY in the help
modal below -- never duplicated as static sidebar text.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__typeform_settings"),
    )


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or "Typeform account"
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(label, variant="body"),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No Typeform accounts connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


def _help_modal() -> ui.UINode:
    return ui.Modal(
        trigger=ui.Button("How do I set this up?", variant="link", size="sm"),
        title="Connecting Typeform",
        children=[
            ui.Stack(direction="v", gap=2, children=[
                ui.Text("1. In Typeform, go to Account settings > Personal tokens.", variant="body"),
                ui.Text("2. Click 'Generate a new token', name it, and copy the value (starts with tfp_).", variant="body"),
                ui.Text("3. Paste it below along with an optional label for this account.", variant="body"),
            ]),
        ],
    )


def _connect_form() -> ui.UINode:
    return ui.Form(
        submit_label="Connect Typeform",
        action=ui.Call("connect_typeform"),
        children=[
            ui.Stack(direction="v", gap=3, children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Account label", variant="label"),
                    ui.Input(param_name="label", placeholder="e.g. Marketing team"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Personal Access Token", variant="label"),
                    ui.Input(param_name="access_token", placeholder="tfp_..."),
                ]),
            ]),
        ],
    )


@ext.panel("typeform_sidebar", slot="left")
async def typeform_sidebar(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    return ui.Stack(direction="v", gap=3, children=[
        ui.Text("Typeform", variant="heading"),
        _connections_section(connections),
        ui.Divider(),
        _connect_form(),
        _help_modal(),
        ui.Divider(),
        _settings_button(),
    ])
