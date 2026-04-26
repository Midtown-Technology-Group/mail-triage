from typer.testing import CliRunner

from mail_triage_cli.cli import app
from mail_triage_cli.models import MailActionResult, MailItem, SenderSummary, SentMessageResult


class FakeService:
    def __init__(self) -> None:
        self.read_calls = []
        self.sent_calls = []

    def inbox(self, limit: int, unread_only: bool = False, folder: str = "inbox", mailbox: str = "me"):
        return [
            MailItem(
                id="1",
                subject="Quarterly update",
                sender="Alex",
                sender_address="alex@example.com",
                mailbox=mailbox,
                received_at="2026-04-24T12:00:00Z",
                is_read=False,
            )
        ]

    def top_senders(self, limit: int, unread_only: bool = False, folder: str = "inbox", mailbox: str = "me"):
        return [
            SenderSummary(
                sender="Alex",
                sender_address="alex@example.com",
                unread_count=2,
                total_count=3,
            )
        ]

    def mark_read(self, ids, mailbox: str = "me", is_read: bool = True):
        self.read_calls.append((ids, mailbox, is_read))
        return MailActionResult(
            action="mark-read" if is_read else "mark-unread",
            mailbox=mailbox,
            count=len(ids),
            ids=ids,
        )

    def send(self, to, subject: str, body: str, mailbox: str = "me"):
        self.sent_calls.append((to, subject, body, mailbox))
        return SentMessageResult(mailbox=mailbox, to=to, subject=subject)


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


def test_read_command_uses_write_path(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("mail_triage_cli.cli.build_service", lambda: service)
    monkeypatch.setattr("mail_triage_cli.cli.has_write_scope", lambda shared_mailbox=False: True)
    runner = CliRunner()

    result = runner.invoke(app, ["--output", "json", "read", "abc123"])

    assert result.exit_code == 0
    assert service.read_calls == [(["abc123"], "me", True)]


def test_send_command_uses_shared_mailbox_bundle(monkeypatch):
    service = FakeService()
    monkeypatch.setattr("mail_triage_cli.cli.build_service", lambda: service)
    monkeypatch.setattr("mail_triage_cli.cli.has_send_scope", lambda shared_mailbox=False: True)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "--output",
            "json",
            "send",
            "--to",
            "person@example.com",
            "--subject",
            "Test",
            "--body",
            "Hello",
            "--mailbox",
            "shared@example.com",
        ],
    )

    assert result.exit_code == 0
    assert service.sent_calls == [(["person@example.com"], "Test", "Hello", "shared@example.com")]
