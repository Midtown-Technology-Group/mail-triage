from __future__ import annotations

from collections import defaultdict

from mail_triage_cli.models import SenderSummary


class MailTriageService:
    def __init__(self, repo) -> None:
        self.repo = repo

    def inbox(self, limit: int, unread_only: bool = False, folder: str = "inbox"):
        return self.repo.list_messages(limit=limit, unread_only=unread_only, folder=folder)

    def top_senders(self, limit: int, unread_only: bool = False, folder: str = "inbox") -> list[SenderSummary]:
        messages = self.repo.list_messages(limit=limit, unread_only=unread_only, folder=folder)
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
