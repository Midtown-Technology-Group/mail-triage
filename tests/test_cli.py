from typer.testing import CliRunner

from mail_triage_cli.cli import app
from mail_triage_cli.models import MailItem, SenderSummary


class FakeService:
    def inbox(self, limit: int, unread_only: bool = False, folder: str = "inbox"):
        return [
            MailItem(
                id="1",
                subject="Quarterly update",
                sender="Alex",
                sender_address="alex@example.com",
                received_at="2026-04-24T12:00:00Z",
                is_read=False,
            )
        ]

    def top_senders(self, limit: int, unread_only: bool = False, folder: str = "inbox"):
        return [
            SenderSummary(
                sender="Alex",
                sender_address="alex@example.com",
                unread_count=2,
                total_count=3,
            )
        ]


def test_inbox_command_supports_json_output(monkeypatch):
    monkeypatch.setattr("mail_triage_cli.cli.build_service", lambda: FakeService())
    runner = CliRunner()

    result = runner.invoke(app, ["--output", "json", "inbox", "--limit", "5"])

    assert result.exit_code == 0
    assert '"subject":"Quarterly update"' in result.stdout
    assert '"sender":"Alex"' in result.stdout


def test_senders_command_supports_json_output(monkeypatch):
    monkeypatch.setattr("mail_triage_cli.cli.build_service", lambda: FakeService())
    runner = CliRunner()

    result = runner.invoke(app, ["--output", "json", "senders"])

    assert result.exit_code == 0
    assert '"sender":"Alex"' in result.stdout
    assert '"unread_count":2' in result.stdout


def test_missing_scope_explains_required_mail_permission(monkeypatch):
    monkeypatch.setattr("mail_triage_cli.cli.has_required_scope", lambda: False)
    runner = CliRunner()

    result = runner.invoke(app, ["inbox"])

    assert result.exit_code != 0
    assert "Mail.ReadBasic" in result.stdout
