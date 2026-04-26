from __future__ import annotations

from pydantic import BaseModel


class MailItem(BaseModel):
    id: str
    subject: str
    sender: str
    sender_address: str
    mailbox: str = "me"
    received_at: str
    is_read: bool
    importance: str = "normal"
    web_link: str | None = None


class SenderSummary(BaseModel):
    sender: str
    sender_address: str
    unread_count: int
    total_count: int


class MailActionResult(BaseModel):
    action: str
    mailbox: str
    count: int = 0
    folder: str | None = None
    ids: list[str] = []


class SentMessageResult(BaseModel):
    action: str = "send"
    mailbox: str
    to: list[str]
    subject: str
