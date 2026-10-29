"""Offline regressions for bounded selection and opaque Graph identifiers."""

import pytest
from mtg_microsoft_auth import GraphClient

from mail_triage_cli.repository import MailRepository
from mail_triage_cli.service import MailTriageService


def message(number):
    return {"id": f"synthetic-{number}", "isRead": False}


@pytest.mark.parametrize("limit", [1, 25, 100, 125])
def test_selection_follows_short_pages_without_exceeding_limit(monkeypatch, limit):
    client = GraphClient(None)
    calls = []
    first_size = min(2, limit - 1)
    pages = iter(
        [
            {
                "value": [message(i) for i in range(first_size)],
                "@odata.nextLink": "https://graph.microsoft.com/v1.0/synthetic-next?$skiptoken=opaque",
            },
            {
                "value": [message(i) for i in range(first_size, limit + 5)],
                "@odata.nextLink": "https://graph.microsoft.com/v1.0/never-request",
            },
        ]
    )

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return Response(next(pages))

    monkeypatch.setattr(client, "_request_with_retry", request)
    items = MailTriageService(MailRepository(client)).inbox(
        limit=limit, unread_only=True, mailbox="shared@example.com"
    )

    assert [item.id for item in items] == [f"synthetic-{i}" for i in range(limit)]
    assert len(calls) == 2
    assert calls[0][2]["params"]["$top"] == min(limit, 100)
    assert calls[0][2]["params"]["$filter"] == "isRead eq false"
    assert calls[1][2]["params"] is None
    assert all(item.mailbox == "shared@example.com" for item in items)


class RecordingGraph:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        return {"id": "resolved-folder", "value": []}

    def get_all(self, path, params=None, max_items=None):
        return self.get(path, params)

    def patch(self, path, payload):
        self.calls.append(("PATCH", path, payload))

    def delete(self, path):
        self.calls.append(("DELETE", path, None))

    def post(self, path, payload):
        self.calls.append(("POST", path, payload))
        return {"responses": [{"id": "0", "status": 204}]}


@pytest.mark.parametrize(
    "mailbox,root",
    [
        ("me", "/me"),
        ("shared@example.com", "/users/shared%40example.com"),
        (
            "shared/team@example.com?x#y%",
            "/users/shared%2Fteam%40example.com%3Fx%23y%25",
        ),
    ],
)
@pytest.mark.parametrize(
    "operation", ["list", "read", "batch", "delete", "move", "send"]
)
def test_identifiers_are_opaque_path_segments(operation, mailbox, root):
    client = RecordingGraph()
    repo = MailRepository(client)
    identifier = "opaque/id+?x#y%="
    encoded = "opaque%2Fid%2B%3Fx%23y%25%3D"

    if operation == "list":
        repo.list_messages(5, folder=identifier, mailbox=mailbox)
        assert client.calls[0][1] == f"{root}/mailFolders/{encoded}/messages"
    elif operation == "read":
        repo.mark_read([identifier], mailbox=mailbox)
        assert client.calls[0][1] == f"{root}/messages/{encoded}"
    elif operation == "batch":
        completed, failed = repo.mark_read_batched([identifier], mailbox=mailbox)
        assert client.calls[0][2]["requests"][0]["url"] == f"{root}/messages/{encoded}"
        assert completed == [identifier]
        assert failed == []
    elif operation == "delete":
        repo.delete_messages([identifier], mailbox=mailbox)
        assert client.calls[0][1] == f"{root}/messages/{encoded}"
    elif operation == "move":
        repo.move_messages([identifier], destination=identifier, mailbox=mailbox)
        assert client.calls[0][1] == f"{root}/mailFolders/{encoded}"
        assert client.calls[1][1] == f"{root}/messages/{encoded}/move"
        assert client.calls[1][2] == {"destinationId": "resolved-folder"}
    else:
        repo.send_message(
            ["recipient@example.com"], "Synthetic", "Synthetic", mailbox=mailbox
        )
        assert client.calls[0][1] == f"{root}/sendMail"
