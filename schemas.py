"""Pydantic param/result models for Typeform Connector.

Same "explicit ConnectionScoped mixin + one params + one result class per
@chat.function" shape as every other connector this session's schemas.py.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ConnectionScoped(BaseModel):
    connection_id: str = Field("", description="Which saved Typeform account to use. Omit if only one is connected.")


# ── Connection lifecycle ────────────────────────────────────────────────

class ConnectTypeformParams(BaseModel):
    label: str = Field("", description="A friendly name for this account, e.g. 'Marketing team'.")
    access_token: str = Field(description="Your Typeform Personal Access Token (Account settings > Personal tokens).")


class ConnectTypeformResult(BaseModel):
    connection_id: str = ""
    label: str = ""
    form_count: int = 0


class DisconnectTypeformParams(BaseModel):
    connection_id: str = Field(description="The connection id to disconnect, from list_connections.")


class DeleteResult(BaseModel):
    deleted: bool = False
    id: str = ""


class TypeformConnection(BaseModel):
    id: str = ""
    label: str = ""


class ConnectionList(BaseModel):
    connections: list[TypeformConnection] = Field(default_factory=list)


class ListConnectionsParams(BaseModel):
    pass


# ── Forms ────────────────────────────────────────────────────────────────

class ListFormsParams(ConnectionScoped):
    workspace_id: str = Field("", description="Optionally filter forms to one workspace id.")


class Form(BaseModel):
    id: str = ""
    title: str = ""
    last_updated_at: str = ""
    settings_language: str = ""


class FormList(BaseModel):
    forms: list[Form] = Field(default_factory=list)


class GetFormParams(ConnectionScoped):
    form_id: str = Field(description="The form id, from list_forms.")


class FormDetail(BaseModel):
    id: str = ""
    title: str = ""
    language: str = ""
    field_count: int = 0
    last_updated_at: str = ""


class DeleteFormParams(ConnectionScoped):
    form_id: str = Field(description="The form id to permanently delete (moves to trash).")


class UpdateFormTitleParams(ConnectionScoped):
    form_id: str = Field(description="The form id to rename.")
    title: str = Field(description="The new title for the form.")


# ── Responses ────────────────────────────────────────────────────────────

class ListResponsesParams(ConnectionScoped):
    form_id: str = Field(description="The form id whose responses to list.")
    page_size: int = Field(25, description="How many responses to return, max 1000.")
    since: str = Field("", description="Only responses submitted after this ISO 8601 date/time.")
    until: str = Field("", description="Only responses submitted before this ISO 8601 date/time.")
    completed: bool | None = Field(None, description="Filter to only completed (true) or only partial (false) responses.")


class Response(BaseModel):
    response_id: str = ""
    submitted_at: str = ""
    landed_at: str = ""
    is_completed: bool = False


class ResponseList(BaseModel):
    total_items: int = 0
    responses: list[Response] = Field(default_factory=list)


class DeleteResponsesParams(ConnectionScoped):
    form_id: str = Field(description="The form id whose responses to delete.")
    response_ids: list[str] = Field(description="One or more response ids to permanently delete.")


# ── Workspaces ───────────────────────────────────────────────────────────

class ListWorkspacesParams(ConnectionScoped):
    pass


class Workspace(BaseModel):
    id: str = ""
    name: str = ""
    form_count: int = 0


class WorkspaceList(BaseModel):
    workspaces: list[Workspace] = Field(default_factory=list)


class CreateWorkspaceParams(ConnectionScoped):
    name: str = Field(description="The new workspace's name.")


class WorkspaceCreateResult(BaseModel):
    id: str = ""
    name: str = ""


# ── Webhooks ─────────────────────────────────────────────────────────────

class ListWebhooksParams(ConnectionScoped):
    form_id: str = Field(description="The form id whose webhooks to list.")


class Webhook(BaseModel):
    tag: str = ""
    url: str = ""
    enabled: bool = False


class WebhookList(BaseModel):
    webhooks: list[Webhook] = Field(default_factory=list)


class CreateWebhookParams(ConnectionScoped):
    form_id: str = Field(description="The form id to attach the webhook to.")
    tag: str = Field(description="A unique name for this webhook, e.g. 'zapier-sync'.")
    url: str = Field(description="The HTTPS URL Typeform will POST each new response to.")
    enabled: bool = Field(True, description="Whether the webhook is active immediately.")


class WebhookCreateResult(BaseModel):
    tag: str = ""
    url: str = ""
    enabled: bool = False


class DeleteWebhookParams(ConnectionScoped):
    form_id: str = Field(description="The form id the webhook is attached to.")
    tag: str = Field(description="The webhook's tag, from list_webhooks.")


# ── Reports ──────────────────────────────────────────────────────────────

class AuditTypeformAccountParams(ConnectionScoped):
    pass


class TypeformAccountReport(BaseModel):
    total_forms: int = 0
    total_workspaces: int = 0
    forms_with_no_responses: list[str] = Field(default_factory=list)
