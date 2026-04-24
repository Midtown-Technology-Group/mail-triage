from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table


class OutputRenderer:
    def __init__(self, mode: str = "interactive") -> None:
        self.mode = mode
        self.console = Console(width=200)

    def render_mail_items(self, items) -> None:
        if self.mode == "json":
            print(json.dumps([item.model_dump() for item in items], separators=(",", ":")))
            return
        table = Table(title="Inbox")
        table.add_column("State")
        table.add_column("Received")
        table.add_column("Sender")
        table.add_column("Subject")
        for item in items:
            state = "Unread" if not item.is_read else "Read"
            table.add_row(state, item.received_at, item.sender, item.subject)
        self.console.print(table)

    def render_sender_summary(self, rows) -> None:
        if self.mode == "json":
            print(json.dumps([row.model_dump() for row in rows], separators=(",", ":")))
            return
        table = Table(title="Top Senders")
        table.add_column("Sender")
        table.add_column("Unread")
        table.add_column("Total")
        for row in rows:
            table.add_row(row.sender, str(row.unread_count), str(row.total_count))
        self.console.print(table)
