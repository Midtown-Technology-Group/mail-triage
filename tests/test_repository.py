from mail_triage_cli.repository import MailRepository


def _message(number: int) -> dict:
    return {
        "id": f"message-{number}",
        "subject": f"Subject {number}",
        "from": {
            "emailAddress": {
                "name": "Sender",
                "address": "sender@example.com",
            }
        },
        "receivedDateTime": "2026-07-23T12:00:00Z",
        "isRead": False,
        "importance": "normal",
        "webLink": f"https://example.com/messages/{number}",
    }


class FakeGraphClient:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.get_calls: list[tuple[str, dict | None]] = []
        self.get_all_calls: list[tuple[str, dict | None]] = []

    def get(self, path: str, params: dict | None = None) -> dict:
        self.get_calls.append((path, params))
        return {"value": self.rows}

    def get_all(self, path: str, params: dict | None = None) -> dict:
        self.get_all_calls.append((path, params))
        return {"value": self.rows}


def test_list_messages_uses_single_page_for_small_limits():
    client = FakeGraphClient([_message(1)])

    items = MailRepository(client).list_messages(limit=25, unread_only=True)

    assert [item.id for item in items] == ["message-1"]
    assert client.get_all_calls == []
    assert client.get_calls == [
        (
            "/me/mailFolders/inbox/messages",
            {
                "$top": 25,
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,receivedDateTime,isRead,importance,webLink",
                "$filter": "isRead eq false",
            },
        )
    ]


def test_list_messages_follows_pages_and_caps_the_requested_limit():
    client = FakeGraphClient([_message(number) for number in range(150)])

    items = MailRepository(client).list_messages(limit=125, mailbox="shared@example.com")

    assert len(items) == 125
    assert items[-1].id == "message-124"
    assert client.get_calls == []
    assert client.get_all_calls == [
        (
            "/users/shared%40example.com/mailFolders/inbox/messages",
            {
                "$top": 100,
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,receivedDateTime,isRead,importance,webLink",
            },
        )
    ]
