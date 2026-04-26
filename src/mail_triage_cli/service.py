from __future__ import annotations

from collections import defaultdict

from mail_triage_cli.models import MailActionResult, SenderSummary, SentMessageResult


class MailTriageService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def inbox(self, limit: int, unread_only: bool = False, folder: str = "inbox", mailbox: str = "me"):
        return self.repo.list_messages(limit=limit, unread_only=unread_only, folder=folder, mailbox=mailbox)

    def top_senders(self, limit: int, unread_only: bool = False, folder: str = "inbox", mailbox: str = "me") -> list[SenderSummary]:
        messages = self.repo.list_messages(limit=limit, unread_only=unread_only, folder=folder, mailbox=mailbox)
        buckets: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"total": 0, "unread": 0})
        for item in messages:
            key = (item.sender, item.sender_address)
            buckets[key]["total"] += 1
            if not item.is_read:
                buckets[key]["unread"] += 1

        ordered = sorted(
            buckets.items(),
            key=lambda entry: (-entry[1]["unread"], -entry[1]["total"], entry[0][0].lower()),
        )
        return [
            SenderSummary(
                sender=name,
                sender_address=address,
                unread_count=counts["unread"],
                total_count=counts["total"],
            )
            for (name, address), counts in ordered
        ]

    def mark_read(self, ids: list[str], mailbox: str = "me", is_read: bool = True) -> MailActionResult:
        count = self.repo.mark_read(ids=ids, mailbox=mailbox, is_read=is_read)
        return MailActionResult(
            action="mark-read" if is_read else "mark-unread",
            mailbox=mailbox,
            count=count,
            ids=ids,
        )

    def move(self, ids: list[str], destination: str, mailbox: str = "me") -> MailActionResult:
        count = self.repo.move_messages(ids=ids, destination=destination, mailbox=mailbox)
        return MailActionResult(
            action="move",
            mailbox=mailbox,
            count=count,
            folder=destination,
            ids=ids,
        )

    def delete(self, ids: list[str], mailbox: str = "me") -> MailActionResult:
        count = self.repo.delete_messages(ids=ids, mailbox=mailbox)
        return MailActionResult(
            action="delete",
            mailbox=mailbox,
            count=count,
            ids=ids,
        )

    def send(self, to: list[str], subject: str, body: str, mailbox: str = "me") -> SentMessageResult:
        self.repo.send_message(to=to, subject=subject, body=body, mailbox=mailbox)
        return SentMessageResult(
            mailbox=mailbox,
            to=to,
            subject=subject,
        )
