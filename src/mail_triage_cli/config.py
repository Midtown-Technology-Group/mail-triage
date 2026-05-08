from __future__ import annotations

import os
from uuid import UUID

from mtg_microsoft_auth import AuthConfig, AuthMode

REQUIRED_SCOPE = "Mail.ReadBasic"
WRITE_SCOPE = "Mail.ReadWrite"
SEND_SCOPE = "Mail.Send"
SHARED_WRITE_SCOPE = "Mail.ReadWrite.Shared"
SHARED_SEND_SCOPE = "Mail.Send.Shared"
DEFAULT_CACHE_NAMESPACE = "mtg-shared-microsoft-auth"
DEFAULT_CLIENT_ID = "e02be6f7-063a-46a6-b2cc-109d5f51055c"
PLACEHOLDER_CLIENT_ID = "11111111-1111-1111-1111-111111111111"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def configured_scopes() -> list[str]:
    raw = os.environ.get("MAIL_TRIAGE_SCOPES", REQUIRED_SCOPE)
    return [scope.strip() for scope in raw.split(",") if scope.strip()]


def load_auth_config() -> AuthConfig:
    return AuthConfig(
        client_id=_required_client_id(),
        tenant_id=os.environ.get("MAIL_TRIAGE_TENANT_ID", "common"),
        scopes=configured_scopes(),
        mode=AuthMode(os.environ.get("MAIL_TRIAGE_AUTH_MODE", "wam")),
        cache_namespace=os.environ.get(
            "MTG_AUTH_CACHE_NAMESPACE", DEFAULT_CACHE_NAMESPACE
        ),
        account_hint=os.environ.get("MTG_AUTH_ACCOUNT_HINT"),
        allow_broker=_env_bool("MAIL_TRIAGE_ALLOW_BROKER", True),
    )


def _required_client_id() -> str:
    client_id = os.environ.get("MAIL_TRIAGE_CLIENT_ID", DEFAULT_CLIENT_ID).strip()
    if not client_id:
        raise RuntimeError(
            "MAIL_TRIAGE_CLIENT_ID must be set to a real Entra public client application ID "
            "or omitted to use the shared Midtown app. Refusing to use the placeholder client ID."
        )
    try:
        parsed_client_id = UUID(client_id)
    except ValueError as exc:
        raise RuntimeError(
            "MAIL_TRIAGE_CLIENT_ID must be a valid Entra public client application ID UUID."
        ) from exc
    if parsed_client_id == UUID(PLACEHOLDER_CLIENT_ID):
        raise RuntimeError(
            "MAIL_TRIAGE_CLIENT_ID must be set to a real Entra public client application ID "
            "or omitted to use the shared Midtown app. Refusing to use the placeholder client ID."
        )
    return client_id


def has_required_scope() -> bool:
    scopes = set(configured_scopes())
    return REQUIRED_SCOPE in scopes or WRITE_SCOPE in scopes


def has_write_scope(shared_mailbox: bool = False) -> bool:
    scopes = set(configured_scopes())
    needed = {WRITE_SCOPE}
    if shared_mailbox:
        needed.add(SHARED_WRITE_SCOPE)
    return needed.issubset(scopes)


def has_send_scope(shared_mailbox: bool = False) -> bool:
    scopes = set(configured_scopes())
    needed = {WRITE_SCOPE, SEND_SCOPE}
    if shared_mailbox:
        needed.update({SHARED_WRITE_SCOPE, SHARED_SEND_SCOPE})
    return needed.issubset(scopes)
