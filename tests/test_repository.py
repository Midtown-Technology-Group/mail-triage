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

    def get_all(self, path: str, params: dict | None = None, max_items: int | None = None) -> dict:
        self.get_all_calls.append((path, params, max_items))
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
            125,
        )
    ]


class FakeBatchClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = iter(responses)
        self.posts: list[tuple[str, dict]] = []

    def post(self, path: str, payload: dict) -> dict:
        self.posts.append((path, payload))
        return next(self.responses)


def test_mark_read_batched_retries_transient_subrequest_failures(monkeypatch):
    client = FakeBatchClient(
        [
            {
                "responses": [
                    {"id": "0", "status": 204},
                    {"id": "1", "status": 429},
                ]
            },
            {"responses": [{"id": "0", "status": 204}]},
        ]
    )
    sleeps = []
    monkeypatch.setattr("mail_triage_cli.repository.time.sleep", sleeps.append)

    completed, failed = MailRepository(client).mark_read_batched(["one", "two"])

    assert completed == ["one", "two"]
    assert failed == []
    assert len(client.posts) == 2
    assert client.posts[1][1]["requests"][0]["url"] == "/me/messages/two"
    assert sleeps == [1]


def test_mark_read_batched_reports_permanent_failures():
    client = FakeBatchClient(
        [
            {
                "responses": [
                    {"id": "0", "status": 204},
                    {"id": "1", "status": 403},
                ]
            }
        ]
    )

    completed, failed = MailRepository(client).mark_read_batched(["one", "two"])

    assert completed == ["one"]
    assert failed == ["two"]
