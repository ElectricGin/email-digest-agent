# tests/test_gmail_fetch.py
import gmail_fetch


class FakeMessagesResource:
    def __init__(self, list_response, get_responses):
        self._list_response = list_response
        self._get_responses = get_responses

    def list(self, userId, q, maxResults):
        return FakeExecutable(self._list_response)

    def get(self, userId, id, format, metadataHeaders):
        return FakeExecutable(self._get_responses[id])


class FakeExecutable:
    def __init__(self, response):
        self._response = response

    def execute(self):
        return self._response


class FakeUsersResource:
    def __init__(self, messages_resource):
        self._messages_resource = messages_resource

    def messages(self):
        return self._messages_resource


class FakeService:
    def __init__(self, messages_resource):
        self._users_resource = FakeUsersResource(messages_resource)

    def users(self):
        return self._users_resource


def test_fetch_messages_since_returns_parsed_messages():
    list_response = {"messages": [{"id": "msg1"}, {"id": "msg2"}]}
    get_responses = {
        "msg1": {
            "payload": {"headers": [
                {"name": "From", "value": "a@example.com"},
                {"name": "Subject", "value": "Hello"},
                {"name": "Date", "value": "Mon, 1 Jan 2026 10:00:00 -0700"},
            ]},
            "snippet": "Hi there",
        },
        "msg2": {
            "payload": {"headers": [
                {"name": "From", "value": "b@example.com"},
                {"name": "Subject", "value": "Reminder"},
                {"name": "Date", "value": "Mon, 1 Jan 2026 11:00:00 -0700"},
            ]},
            "snippet": "Don't forget",
        },
    }
    service = FakeService(FakeMessagesResource(list_response, get_responses))

    result = gmail_fetch.fetch_messages_since(service, since_epoch_seconds=1735689600)

    assert result == [
        {"id": "msg1", "from": "a@example.com", "subject": "Hello",
         "date": "Mon, 1 Jan 2026 10:00:00 -0700", "snippet": "Hi there"},
        {"id": "msg2", "from": "b@example.com", "subject": "Reminder",
         "date": "Mon, 1 Jan 2026 11:00:00 -0700", "snippet": "Don't forget"},
    ]


def test_fetch_messages_since_returns_empty_list_when_no_messages():
    service = FakeService(FakeMessagesResource({}, {}))
    result = gmail_fetch.fetch_messages_since(service, since_epoch_seconds=1735689600)
    assert result == []
