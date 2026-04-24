from __future__ import annotations

import typer
from mtg_microsoft_auth import GraphAuthSession, GraphClient

from mail_triage_cli.config import REQUIRED_SCOPE, has_required_scope, load_auth_config
from mail_triage_cli.output import OutputRenderer
from mail_triage_cli.repository import MailRepository
from mail_triage_cli.service import MailTriageService

app = typer.Typer(help="Read-only inbox triage for Microsoft 365.")


def build_service() -> MailTriageService:
    session = GraphAuthSession(load_auth_config())
    client = GraphClient(session)
    repo = MailRepository(client)
    return MailTriageService(repo)


def _renderer(output: str) -> OutputRenderer:
    return OutputRenderer(mode=output)


def _require_scope() -> None:
    if has_required_scope():
        return
    typer.echo(
        f"This command needs {REQUIRED_SCOPE}. Set MAIL_TRIAGE_SCOPES={REQUIRED_SCOPE} "
        "before running the mail triage toy."
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
) -> None:
    _require_scope()
    renderer = _renderer(ctx.obj["output"])
    items = build_service().inbox(limit=limit, unread_only=unread_only, folder=folder)
    renderer.render_mail_items(items)


@app.command("senders")
def senders(
    ctx: typer.Context,
    limit: int = typer.Option(25, "--limit", "-n", min=1, max=200),
    unread_only: bool = typer.Option(False, "--unread-only"),
    folder: str = typer.Option("inbox", "--folder"),
) -> None:
    _require_scope()
    renderer = _renderer(ctx.obj["output"])
    rows = build_service().top_senders(limit=limit, unread_only=unread_only, folder=folder)
    renderer.render_sender_summary(rows)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
