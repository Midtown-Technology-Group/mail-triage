from __future__ import annotations

import time
from urllib.parse import quote

from mail_triage_cli.models import MailItem


class MailRepository:
    def __init__(self, client) -> None:
        self.client = client

    def list_messages(self, limit: int, unread_only: bool = False, folder: str = "inbox", mailbox: str = "me") -> list[MailItem]:
        page_size = min(limit, 100)
        params = {
            "$top": page_size,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,isRead,importance,webLink",
        }
        if unread_only:
            params["$filter"] = "isRead eq false"

        if limit > 100:
            payload = self.client.get_all(
                f"{self._mailbox_path(mailbox)}/mailFolders/{folder}/messages",
                params=params,
                max_items=limit,
            )
            rows = payload.get("value", [])[:limit]
        else:
            payload = self.client.get(f"{self._mailbox_path(mailbox)}/mailFolders/{folder}/messages", params=params)
            rows = payload.get("value", [])

        items = []
        for row in rows:
            sender = (row.get("from") or {}).get("emailAddress") or {}
            items.append(
                MailItem(
                    id=row["id"],
                    subject=row.get("subject") or "(no subject)",
                    sender=sender.get("name") or sender.get("address") or "Unknown",
                    sender_address=sender.get("address") or "",
                    mailbox=mailbox,
                    received_at=row.get("receivedDateTime") or "",
                    is_read=bool(row.get("isRead", False)),
                    importance=row.get("importance") or "normal",
                    web_link=row.get("webLink"),
                )
            )
        return items

    def mark_read(self, ids: list[str], mailbox: str = "me", is_read: bool = True) -> int:
        for message_id in ids:
            self.client.patch(
                f"{self._mailbox_path(mailbox)}/messages/{message_id}",
                {"isRead": is_read},
            )
        return len(ids)

    def mark_read_batched(
        self,
        ids: list[str],
        mailbox: str = "me",
        is_read: bool = True,
        max_attempts: int = 3,
    ) -> tuple[list[str], list[str]]:
        pending = list(ids)
        completed: list[str] = []
        failed: list[str] = []

        for attempt in range(max_attempts):
            retry_ids: list[str] = []
            for offset in range(0, len(pending), 20):
                batch = pending[offset : offset + 20]
                requests = [
                    {
                        "id": str(index),
                        "method": "PATCH",
                        "url": f"{self._mailbox_path(mailbox)}/messages/{message_id}",
                        "headers": {"Content-Type": "application/json"},
                        "body": {"isRead": is_read},
                    }
                    for index, message_id in enumerate(batch)
                ]
                payload = self.client.post("/$batch", {"requests": requests})
                responses = {str(row.get("id")): row for row in payload.get("responses", [])}

                for index, message_id in enumerate(batch):
                    response = responses.get(str(index), {})
                    status = int(response.get("status") or 0)
                    if 200 <= status < 300:
                        completed.append(message_id)
                    elif status in {429, 500, 502, 503, 504} and attempt + 1 < max_attempts:
                        retry_ids.append(message_id)
                    else:
                        failed.append(message_id)

            pending = retry_ids
            if not pending:
                break
            time.sleep(2**attempt)

        failed.extend(pending)
        return completed, failed

    def delete_messages(self, ids: list[str], mailbox: str = "me") -> int:
        for message_id in ids:
            self.client.delete(f"{self._mailbox_path(mailbox)}/messages/{message_id}")
        return len(ids)

    def move_messages(self, ids: list[str], destination: str, mailbox: str = "me") -> int:
        destination_id = self._resolve_folder_id(destination, mailbox=mailbox)
        for message_id in ids:
            self.client.post(
                f"{self._mailbox_path(mailbox)}/messages/{message_id}/move",
                {"destinationId": destination_id},
            )
        return len(ids)

    def send_message(self, to: list[str], subject: str, body: str, mailbox: str = "me") -> None:
        recipients = [{"emailAddress": {"address": address}} for address in to]
        self.client.post(
            f"{self._mailbox_path(mailbox)}/sendMail",
            {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "Text",
                        "content": body,
                    },
                    "toRecipients": recipients,
                },
                "saveToSentItems": True,
            },
        )

    def _resolve_folder_id(self, destination: str, mailbox: str = "me") -> str:
        try:
            payload = self.client.get(f"{self._mailbox_path(mailbox)}/mailFolders/{destination}")
            folder_id = payload.get("id")
            if folder_id:
                return folder_id
        except Exception:
            pass

        payload = self.client.get(
            f"{self._mailbox_path(mailbox)}/mailFolders",
            params={"$top": 200, "$select": "id,displayName"},
        )
        lowered = destination.lower()
        for row in payload.get("value", []):
            if (row.get("displayName") or "").lower() == lowered:
                return row["id"]
        raise ValueError(f"No folder found matching '{destination}'.")

    @staticmethod
    def _mailbox_path(mailbox: str) -> str:
        normalized = mailbox.strip()
        if not normalized or normalized.lower() == "me":
            return "/me"
        return f"/users/{quote(normalized)}"
