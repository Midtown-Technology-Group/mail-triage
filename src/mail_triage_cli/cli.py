from __future__ import annotations

import typer
from mtg_microsoft_auth import GraphAuthSession, GraphClient

from mail_triage_cli.config import (
    REQUIRED_SCOPE,
    SEND_SCOPE,
    SHARED_SEND_SCOPE,
    SHARED_WRITE_SCOPE,
    WRITE_SCOPE,
    has_required_scope,
    has_send_scope,
    has_write_scope,
    load_auth_config,
)
from mail_triage_cli.output import OutputRenderer
from mail_triage_cli.repository import MailRepository
from mail_triage_cli.service import MailTriageService

app = typer.Typer(help="Inbox triage and delegated mail actions for Microsoft 365.")


def build_service() -> MailTriageService:
    session = GraphAuthSession(load_auth_config())
    client = GraphClient(session)
    repo = MailRepository(client)
    return MailTriageService(repo)


def _renderer(output: str) -> OutputRenderer:
    return OutputRenderer(mode=output)


def _is_shared_mailbox(mailbox: str) -> bool:
    return mailbox.strip().lower() not in {"", "me"}


def _require_scope(mailbox: str = "me") -> None:
    if has_required_scope():
        if not _is_shared_mailbox(mailbox):
            return
        if has_write_scope(shared_mailbox=True):
            return
    typer.echo(
        "This command needs "
        f"{REQUIRED_SCOPE} for your own mailbox, or {WRITE_SCOPE} and {SHARED_WRITE_SCOPE} "
        "for shared mailbox access. Set MAIL_TRIAGE_SCOPES accordingly before running the mail toy."
    )
    raise typer.Exit(code=2)


def _require_write(mailbox: str = "me") -> None:
    shared = _is_shared_mailbox(mailbox)
    if has_write_scope(shared_mailbox=shared):
        return
    required = f"{WRITE_SCOPE}" if not shared else f"{WRITE_SCOPE},{SHARED_WRITE_SCOPE}"
    typer.echo(
        f"This command needs {required}. Set MAIL_TRIAGE_SCOPES to include the required write scopes."
    )
    raise typer.Exit(code=2)


def _require_send(mailbox: str = "me") -> None:
    shared = _is_shared_mailbox(mailbox)
    if has_send_scope(shared_mailbox=shared):
        return
    required = (
        f"{WRITE_SCOPE},{SEND_SCOPE}"
        if not shared
        else f"{WRITE_SCOPE},{SEND_SCOPE},{SHARED_WRITE_SCOPE},{SHARED_SEND_SCOPE}"
    )
    typer.echo(
        f"This command needs {required}. Set MAIL_TRIAGE_SCOPES to include the required send scopes."
    )
    raise typer.Exit(code=2)


@app.callback()
def root(
    ctx: typer.Context,
    output: str = typer.Option("interactive", "--output", "-o"),
) -> None:
    ctx.obj = {"output": output}


@app.command("inbox")
def inbox(
    ctx: typer.Context,
    limit: int = typer.Option(10, "--limit", "-n", min=1, max=100),
    unread_only: bool = typer.Option(False, "--unread-only"),
    folder: str = typer.Option("inbox", "--folder"),
    mailbox: str = typer.Option("me", "--mailbox"),
) -> None:
    _require_scope(mailbox=mailbox)
    renderer = _renderer(ctx.obj["output"])
    items = build_service().inbox(limit=limit, unread_only=unread_only, folder=folder, mailbox=mailbox)
    renderer.render_mail_items(items)


@app.command("senders")
def senders(
    ctx: typer.Context,
    limit: int = typer.Option(25, "--limit", "-n", min=1, max=200),
    unread_only: bool = typer.Option(False, "--unread-only"),
    folder: str = typer.Option("inbox", "--folder"),
    mailbox: str = typer.Option("me", "--mailbox"),
) -> None:
    _require_scope(mailbox=mailbox)
    renderer = _renderer(ctx.obj["output"])
    rows = build_service().top_senders(limit=limit, unread_only=unread_only, folder=folder, mailbox=mailbox)
    renderer.render_sender_summary(rows)


@app.command("read")
def mark_read(
    ctx: typer.Context,
    ids: list[str] = typer.Argument(...),
    mailbox: str = typer.Option("me", "--mailbox"),
) -> None:
    _require_write(mailbox=mailbox)
    renderer = _renderer(ctx.obj["output"])
    result = build_service().mark_read(ids=ids, mailbox=mailbox, is_read=True)
    renderer.render_status(result)


@app.command("unread")
def mark_unread(
    ctx: typer.Context,
    ids: list[str] = typer.Argument(...),
    mailbox: str = typer.Option("me", "--mailbox"),
) -> None:
    _require_write(mailbox=mailbox)
    renderer = _renderer(ctx.obj["output"])
    result = build_service().mark_read(ids=ids, mailbox=mailbox, is_read=False)
    renderer.render_status(result)


@app.command("move")
def move(
    ctx: typer.Context,
    ids: list[str] = typer.Argument(...),
    destination: str = typer.Option(..., "--to"),
    mailbox: str = typer.Option("me", "--mailbox"),
) -> None:
    _require_write(mailbox=mailbox)
    renderer = _renderer(ctx.obj["output"])
    result = build_service().move(ids=ids, destination=destination, mailbox=mailbox)
    renderer.render_status(result)


@app.command("delete")
def delete(
    ctx: typer.Context,
    ids: list[str] = typer.Argument(...),
    mailbox: str = typer.Option("me", "--mailbox"),
) -> None:
    _require_write(mailbox=mailbox)
    renderer = _renderer(ctx.obj["output"])
    result = build_service().delete(ids=ids, mailbox=mailbox)
    renderer.render_status(result)


@app.command("send")
def send(
    ctx: typer.Context,
    to: list[str] = typer.Option(..., "--to"),
    subject: str = typer.Option(..., "--subject"),
    body: str = typer.Option(..., "--body"),
    mailbox: str = typer.Option("me", "--mailbox"),
) -> None:
    _require_send(mailbox=mailbox)
    renderer = _renderer(ctx.obj["output"])
    result = build_service().send(to=to, subject=subject, body=body, mailbox=mailbox)
    renderer.render_status(result)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
