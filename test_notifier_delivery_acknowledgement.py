import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import notification_state


class RequestException(Exception):
    pass


def load_notifier():
    requests_stub = types.ModuleType("requests")
    requests_stub.RequestException = RequestException
    requests_stub.post = mock.Mock()
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda: None
    previous_requests = sys.modules.get("requests")
    previous_dotenv = sys.modules.get("dotenv")
    sys.modules["requests"] = requests_stub
    sys.modules["dotenv"] = dotenv_stub
    try:
        path = Path(__file__).resolve().parent / "notifier.py"
        spec = importlib.util.spec_from_file_location("_test_notifier", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if previous_requests is None:
            sys.modules.pop("requests", None)
        else:
            sys.modules["requests"] = previous_requests
        if previous_dotenv is None:
            sys.modules.pop("dotenv", None)
        else:
            sys.modules["dotenv"] = previous_dotenv
    return module, requests_stub


class NotificationDeliveryAcknowledgementTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "notification_state.json"
        self.original_state_file = notification_state.STATE_FILE
        notification_state.STATE_FILE = self.state_file
        self.notifier, self.requests = load_notifier()
        self.notifier.TOKEN = "test-token"
        self.notifier.CHAT_ID = "123"
        self.payload = {
            "level": "ERROR",
            "title": "SYSTEM · TEST FAILURE",
            "body": "A test failure occurred.",
            "details": {"Reason": "TEST"},
        }

    def tearDown(self):
        notification_state.STATE_FILE = self.original_state_file
        self.temp_dir.cleanup()

    @staticmethod
    def successful_response():
        response = mock.Mock()
        response.json.return_value = {"ok": True, "result": {"message_id": 1}}
        return response

    def notify(self):
        return self.notifier.notify(**self.payload)

    def test_new_event_commits_only_after_successful_delivery(self):
        events = []
        response = self.successful_response()
        self.requests.post.side_effect = lambda *args, **kwargs: (
            events.append("send") or response
        )
        original_commit = self.notifier.commit_delivery

        def commit(event_key, payload):
            events.append("commit")
            original_commit(event_key, payload)

        with mock.patch.object(
            self.notifier,
            "is_duplicate",
            side_effect=lambda *args: events.append("inspect") or False,
        ), mock.patch.object(
            self.notifier,
            "commit_delivery",
            side_effect=commit,
        ):
            result = self.notify()

        self.assertTrue(result["ok"])
        self.assertEqual(events, ["inspect", "send", "commit"])
        self.assertTrue(
            notification_state.is_duplicate(
                self.payload["title"].upper(),
                self.payload,
            )
        )

    def test_committed_duplicate_is_suppressed_without_state_rewrite(self):
        event_key = self.payload["title"].upper()
        notification_state.commit_delivery(event_key, self.payload)
        before = self.state_file.read_bytes()

        result = self.notify()

        self.assertIsNone(result)
        self.requests.post.assert_not_called()
        self.assertEqual(self.state_file.read_bytes(), before)

    def test_request_failure_does_not_commit_or_raise(self):
        self.requests.post.side_effect = RequestException("secret request URL")

        result = self.notify()

        self.assertIsNone(result)
        self.assertFalse(self.state_file.exists())

    def test_missing_credentials_do_not_commit(self):
        self.notifier.TOKEN = None

        result = self.notify()

        self.assertIsNone(result)
        self.assertFalse(self.state_file.exists())
        self.requests.post.assert_not_called()

    def test_malformed_json_does_not_commit_or_raise(self):
        response = mock.Mock()
        response.json.side_effect = ValueError("invalid JSON")
        self.requests.post.return_value = response

        result = self.notify()

        self.assertIsNone(result)
        self.assertFalse(self.state_file.exists())

    def test_non_dict_response_does_not_commit(self):
        response = mock.Mock()
        response.json.return_value = ["not", "an", "object"]
        self.requests.post.return_value = response

        self.assertIsNone(self.notify())
        self.assertFalse(self.state_file.exists())

    def test_ok_false_does_not_commit(self):
        response = mock.Mock()
        response.json.return_value = {"ok": False, "description": "rejected"}
        self.requests.post.return_value = response

        self.assertIsNone(self.notify())
        self.assertFalse(self.state_file.exists())

    def test_missing_ok_does_not_commit(self):
        response = mock.Mock()
        response.json.return_value = {"result": {}}
        self.requests.post.return_value = response

        self.assertIsNone(self.notify())
        self.assertFalse(self.state_file.exists())

    def test_identical_event_is_attempted_again_after_failed_send(self):
        failed = mock.Mock()
        failed.json.return_value = {"ok": False}
        self.requests.post.side_effect = [failed, self.successful_response()]

        first = self.notify()
        second = self.notify()

        self.assertIsNone(first)
        self.assertTrue(second["ok"])
        self.assertEqual(self.requests.post.call_count, 2)
        self.assertTrue(self.state_file.exists())

    def test_commit_never_occurs_when_send_fails(self):
        response = mock.Mock()
        response.json.return_value = {"ok": False}
        self.requests.post.return_value = response

        with mock.patch.object(self.notifier, "commit_delivery") as commit:
            self.notify()

        commit.assert_not_called()

    def test_commit_failure_after_delivery_is_observable_and_contained(self):
        successful_payload = {"ok": True, "result": {"message_id": 1}}
        response = mock.Mock()
        response.json.return_value = successful_payload
        self.requests.post.return_value = response
        output = io.StringIO()

        with mock.patch.object(
            self.notifier,
            "commit_delivery",
            side_effect=OSError("disk failure"),
        ), contextlib.redirect_stdout(output):
            result = self.notify()

        self.assertIs(result, successful_payload)
        self.assertIn("notification state error: OSError", output.getvalue())
        self.assertFalse(self.state_file.exists())

    def test_committed_fingerprint_is_seen_by_fresh_state_module(self):
        event_key = self.payload["title"].upper()
        notification_state.commit_delivery(event_key, self.payload)
        path = Path(__file__).resolve().parent / "notification_state.py"
        spec = importlib.util.spec_from_file_location("_fresh_state", path)
        fresh_state = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fresh_state)
        fresh_state.STATE_FILE = self.state_file

        self.assertTrue(fresh_state.is_duplicate(event_key, self.payload))

    def test_system_startup_bypasses_state_and_validates_success(self):
        self.requests.post.return_value = self.successful_response()

        with mock.patch.object(self.notifier, "is_duplicate") as inspect, \
                mock.patch.object(self.notifier, "commit_delivery") as commit:
            result = self.notifier.notify(
                level="INFO",
                title="SYSTEM STARTUP",
                body="Started.",
            )

        self.assertTrue(result["ok"])
        inspect.assert_not_called()
        commit.assert_not_called()

    def test_execution_approved_bypasses_state_and_validates_failure(self):
        response = mock.Mock()
        response.json.return_value = {"ok": False}
        self.requests.post.return_value = response

        with mock.patch.object(self.notifier, "is_duplicate") as inspect, \
                mock.patch.object(self.notifier, "commit_delivery") as commit:
            result = self.notifier.notify(
                level="SUCCESS",
                title="EXECUTION APPROVED",
                body="BTC · LONG",
            )

        self.assertIsNone(result)
        inspect.assert_not_called()
        commit.assert_not_called()

    def test_clear_preserves_existing_semantics(self):
        event_key = self.payload["title"].upper()
        notification_state.commit_delivery(event_key, self.payload)

        notification_state.clear(event_key)

        self.assertFalse(notification_state.is_duplicate(event_key, self.payload))

    def test_malformed_state_loads_as_empty(self):
        self.state_file.write_text("{broken", encoding="utf-8")

        self.assertFalse(
            notification_state.is_duplicate(
                self.payload["title"].upper(),
                self.payload,
            )
        )


if __name__ == "__main__":
    unittest.main()
