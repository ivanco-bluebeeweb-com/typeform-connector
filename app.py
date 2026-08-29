"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK, same reasoning as every other connector this session -- the
user's own Typeform account (forms, responses, webhooks, workspaces) is
managed via their own Personal Access Token.

WHY A STATIC PERSONAL ACCESS TOKEN (PAT), CONFIRMED against
developers.typeform.com/get-started/personal-access-token/, 2026-08-29:
Typeform's Create/Responses/Webhooks APIs support both OAuth2 apps and a
simpler long-lived Personal Access Token (format tfp_...) generated
directly in the user's Typeform account settings -- sent as
`Authorization: Bearer {token}` on every request to api.typeform.com.
This matches the same "paste your own long-lived token" pattern as
Klaviyo/HubSpot Private App tokens in this portfolio -- no client_id/
secret/refresh cycle to manage.

WHY EACH CONNECTION STORES access_token only, SAME SHAPE AS EVERY OTHER
STATIC-TOKEN CONNECTOR THIS SESSION.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "typeform-connector",
    version="0.1.0",
    display_name="Typeform",
    icon="icon.svg",
    capabilities=["typeform:read", "typeform:write"],
    description=(
        "Connect your own Typeform account (Personal Access Token) to "
        "manage forms, responses, webhooks, and workspaces."
    ),
)

chat = ChatExtension(ext)
