"""Offline regressions for bounded selection and opaque Graph identifiers."""

from urllib.parse import parse_qsl, urlsplit

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


def test_selection_follows_three_opaque_pages_and_stops_at_total_cap(monkeypatch):
    client = GraphClient(None)
    calls = []
    path = "/v1.0/users/shared%40example.com/mailFolders/folder%2Fid/messages"
    second_query = "$skiptoken=page%2Btwo%2F%3D%26%25&$top=2"
    third_query = "$skiptoken=page%2Bthree%2F%3D%26%25&$top=5"
    second_url = f"https://graph.microsoft.com{path}?{second_query}"
    third_url = f"https://graph.microsoft.com{path}?{third_query}"
    pages = iter(
        [
            {"value": [message(0)], "@odata.nextLink": second_url},
            {
                "value": [message(1), message(2)],
                "@odata.nextLink": third_url,
            },
            {
                "value": [message(i) for i in range(3, 8)],
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
        limit=5, unread_only=True, folder="folder/id", mailbox="shared@example.com"
    )

    assert [item.id for item in items] == [f"synthetic-{i}" for i in range(5)]
    assert len(calls) == 3
    assert calls[0] == (
        "GET",
        f"https://graph.microsoft.com{path}",
        {
            "params": {
                "$top": 5,
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,receivedDateTime,isRead,importance,webLink",
                "$filter": "isRead eq false",
            }
        },
    )
    for call, expected_url, expected_query, token, top in [
        (calls[1], second_url, second_query, "page+two/=&%", "2"),
        (calls[2], third_url, third_query, "page+three/=&%", "5"),
    ]:
        assert call == ("GET", expected_url, {"params": None})
        parsed = urlsplit(call[1])
        assert (parsed.scheme, parsed.netloc) == ("https", "graph.microsoft.com")
        assert parsed.path == path
        assert parsed.query == expected_query
        assert parsed.fragment == ""
        assert parse_qsl(parsed.query) == [("$skiptoken", token), ("$top", top)]


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
