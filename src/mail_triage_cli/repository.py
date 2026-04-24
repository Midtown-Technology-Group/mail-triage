from __future__ import annotations

from mail_triage_cli.models import MailItem


class MailRepository:
    def __init__(self, client) -> None:
        self.client = client

    def list_messages(self, limit: int, unread_only: bool = False, folder: str = "inbox") -> list[MailItem]:
        params = {
            "$top": limit,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,isRead,importance,webLink",
        }
        if unread_only:
            params["$filter"] = "isRead eq false"

        payload = self.client.get(f"/me/mailFolders/{folder}/messages", params=params)
        items = []
        for row in payload.get("value", []):
            sender = (row.get("from") or {}).get("emailAddress") or {}
            items.append(
                MailItem(
                    id=row["id"],
                    subject=row.get("subject") or "(no subject)",
                    sender=sender.get("name") or sender.get("address") or "Unknown",
                    sender_address=sender.get("address") or "",
                    received_at=row.get("receivedDateTime") or "",
                    is_read=bool(row.get("isRead", False)),
                    importance=row.get("importance") or "normal",
                    web_link=row.get("webLink"),
                )
            )
        return items
