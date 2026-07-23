from mail_triage_cli.models import MailItem
from mail_triage_cli.service import MailTriageService


class FakeRepository:
    def __init__(self, messages: list[MailItem], completed: list[str], failed: list[str]) -> None:
        self.messages = messages
        self.completed = completed
        self.failed = failed
        self.batch_calls = []

    def list_messages(self, **kwargs) -> list[MailItem]:
        return self.messages

    def mark_read_batched(self, **kwargs) -> tuple[list[str], list[str]]:
        self.batch_calls.append(kwargs)
        return self.completed, self.failed


def _message(message_id: str, is_read: bool) -> MailItem:
    return MailItem(
        id=message_id,
        subject="Subject",
        sender="Sender",
        sender_address="sender@example.com",
        received_at="2026-07-23T12:00:00Z",
        is_read=is_read,
    )


def test_mark_matching_read_reports_completed_and_failed_ids():
    repo = FakeRepository(
        messages=[_message("one", False), _message("already-read", True), _message("two", False)],
        completed=["one"],
        failed=["two"],
    )

    result = MailTriageService(repo).mark_matching_read(limit=250, mailbox="shared@example.com")

    assert result.count == 1
    assert result.ids == ["one"]
    assert result.failed_ids == ["two"]
    assert repo.batch_calls == [
        {
            "ids": ["one", "two"],
            "mailbox": "shared@example.com",
            "is_read": True,
        }
    ]


def test_mark_matching_read_keeps_empty_selection_noop():
    repo = FakeRepository(messages=[_message("already-read", True)], completed=[], failed=[])

    result = MailTriageService(repo).mark_matching_read(limit=10)

    assert result.count == 0
    assert result.ids == []
    assert result.failed_ids == []
    assert repo.batch_calls == []
