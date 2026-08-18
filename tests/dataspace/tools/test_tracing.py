#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

import base64
import json
import unittest
from unittest.mock import patch

import requests

from tractusx_sdk.dataspace.adapters.adapter import Adapter
from tractusx_sdk.dataspace.tools.http_tools import HttpTools
from tractusx_sdk.dataspace.tools.tracing import (
    REDACTED_VALUE,
    TRACER_ATTRIBUTE,
    TraceEntry,
    TraceableMixin,
    Tracer,
    get_active_operation,
    get_active_tracers,
    resolve_tracer,
    tracing_context,
)


def build_response(status_code: int = 200, body: dict = None, text: str = None,
                   content: bytes = None, content_type: str = "application/json") -> requests.Response:
    """Builds a real `requests.Response`, to keep the tests close to production."""
    response = requests.Response()
    response.status_code = status_code
    response.reason = "OK"
    response.headers["Content-Type"] = content_type
    if content is not None:
        response._content = content
    elif body is not None:
        response._content = json.dumps(body).encode()
    else:
        response._content = (text or "").encode()
    return response


class TestTracer(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com/api/data"

    @patch("requests.post")
    def test_records_request_and_response(self, mock_post):
        mock_post.return_value = build_response(body={"message": "success"})
        tracer = Tracer(name="test")

        HttpTools.do_post(url=self.url, json={"key": "value"}, headers={"Accept": "application/json"}, tracer=tracer)

        entries = tracer.to_list()
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual("POST", entry["request"]["method"])
        self.assertEqual(self.url, entry["request"]["url"])
        self.assertEqual({"key": "value"}, entry["request"]["body"])
        self.assertEqual({"Accept": "application/json"}, entry["request"]["headers"])
        self.assertEqual(200, entry["response"]["status_code"])
        self.assertEqual({"message": "success"}, entry["response"]["body"])
        self.assertIsNone(entry["error"])
        self.assertIsNotNone(entry["duration_ms"])

    @patch("requests.get")
    def test_nothing_is_recorded_by_default(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer()

        HttpTools.do_get(url=self.url)

        self.assertEqual([], tracer.to_list())
        self.assertEqual((), get_active_tracers())
        # The call is performed exactly as it was before tracing existed
        self.assertNotIn("tracer", mock_get.call_args.kwargs)

    @patch("requests.get")
    def test_disabled_tracer_does_not_record(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer().disable()

        HttpTools.do_get(url=self.url, tracer=tracer)

        self.assertEqual([], tracer.to_list())

    @patch("requests.post")
    def test_sensitive_headers_are_redacted(self, mock_post):
        mock_post.return_value = build_response(body={})
        tracer = Tracer()

        HttpTools.do_post(url=self.url, headers={"Authorization": "Bearer secret", "X-Api-Key": "key"}, tracer=tracer)

        headers = tracer.to_list()[0]["request"]["headers"]
        self.assertEqual(REDACTED_VALUE, headers["Authorization"])
        self.assertEqual(REDACTED_VALUE, headers["X-Api-Key"])

    @patch("requests.post")
    def test_redaction_can_be_disabled(self, mock_post):
        mock_post.return_value = build_response(body={})
        tracer = Tracer(redact_headers=False)

        HttpTools.do_post(url=self.url, headers={"Authorization": "Bearer secret"}, tracer=tracer)

        self.assertEqual("Bearer secret", tracer.to_list()[0]["request"]["headers"]["Authorization"])

    @patch("requests.post")
    def test_bodies_can_be_skipped(self, mock_post):
        mock_post.return_value = build_response(body={"message": "success"})
        tracer = Tracer(capture_bodies=False)

        HttpTools.do_post(url=self.url, json={"key": "value"}, tracer=tracer)

        entry = tracer.to_list()[0]
        self.assertIsNone(entry["request"]["body"])
        self.assertNotIn("body", entry["response"])

    @patch("requests.post")
    def test_serialized_json_bodies_stay_structured(self, mock_post):
        """The SDK models are sent as JSON strings, and recorded as objects."""
        mock_post.return_value = build_response(body={})
        tracer = Tracer()

        HttpTools.do_post(url=self.url, data='{"@type": "CatalogRequest"}', tracer=tracer)

        self.assertEqual({"@type": "CatalogRequest"}, tracer.to_list()[0]["request"]["body"])

    @patch("requests.post")
    def test_non_json_bodies_are_recorded_as_they_are(self, mock_post):
        mock_post.return_value = build_response(body={})
        tracer = Tracer()

        HttpTools.do_post(url=self.url, data="plain=text&value=1", tracer=tracer)

        self.assertEqual("plain=text&value=1", tracer.to_list()[0]["request"]["body"])

    @patch("requests.get")
    def test_content_type_is_recorded(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer()

        HttpTools.do_get(url=self.url, tracer=tracer)

        self.assertEqual("application/json", tracer.to_list()[0]["response"]["content_type"])

    @patch("requests.get")
    def test_html_bodies_are_recorded_as_text(self, mock_get):
        mock_get.return_value = build_response(text="<html><body>Bad Gateway</body></html>", content_type="text/html")
        tracer = Tracer()

        HttpTools.do_get(url=self.url, tracer=tracer)

        response = tracer.to_list()[0]["response"]
        self.assertEqual("text/html", response["content_type"])
        self.assertEqual("<html><body>Bad Gateway</body></html>", response["body"])

    @patch("requests.get")
    def test_binary_bodies_are_base64_encoded(self, mock_get):
        payload = b"%PDF-1.7\x00\x93\xff binary"
        mock_get.return_value = build_response(content=payload, content_type="application/pdf")
        tracer = Tracer()

        HttpTools.do_get(url=self.url, tracer=tracer)

        body = tracer.to_list()[0]["response"]["body"]
        self.assertEqual("base64", body["encoding"])
        self.assertEqual(len(payload), body["length"])
        self.assertEqual(payload, base64.b64decode(body["data"]))

    @patch("requests.post")
    def test_large_json_bodies_are_recorded_in_full(self, mock_post):
        assets = [{"@id": f"asset:{index}", "name": "y" * 500} for index in range(60)]
        mock_post.return_value = build_response(body=assets)
        tracer = Tracer()

        HttpTools.do_post(url=self.url, tracer=tracer)

        # No cap by default: the body is the JSON that came back, complete
        self.assertEqual(assets, tracer.to_list()[0]["response"]["body"])

    @patch("requests.post")
    def test_long_bodies_are_truncated(self, mock_post):
        mock_post.return_value = build_response(text="x" * 500)
        tracer = Tracer(max_body_chars=50)

        HttpTools.do_post(url=self.url, tracer=tracer)

        body = tracer.to_list()[0]["response"]["body"]
        self.assertTrue(body.startswith("x" * 50))
        self.assertIn("truncated", body)

    @patch("requests.post")
    def test_long_structured_bodies_stay_structured(self, mock_post):
        assets = [{"@id": f"asset:{index}", "name": "x" * 100} for index in range(20)]
        mock_post.return_value = build_response(body=assets)
        tracer = Tracer(max_body_chars=300)

        HttpTools.do_post(url=self.url, tracer=tracer)

        body = tracer.to_list()[0]["response"]["body"]
        self.assertIsInstance(body, list)
        self.assertIsInstance(body[0], dict)
        self.assertEqual("asset:0", body[0]["@id"])
        self.assertIn("truncated", body[-1])
        # navigable: the recorded body is still valid, parsable JSON
        self.assertEqual(body, json.loads(json.dumps(body)))

    @patch("requests.get")
    def test_errors_are_recorded_and_raised(self, mock_get):
        mock_get.side_effect = ConnectionError("connection refused")
        tracer = Tracer()

        with self.assertRaises(ConnectionError):
            HttpTools.do_get(url=self.url, tracer=tracer)

        entry = tracer.to_list()[0]
        self.assertEqual("ConnectionError", entry["error"]["type"])
        self.assertEqual("connection refused", entry["error"]["message"])
        self.assertIsNone(entry["response"])

    @patch("requests.Session.get")
    def test_tracer_bound_to_a_session(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer()
        session = tracer.attach(requests.Session())

        HttpTools.do_get_with_session(url=self.url, session=session)

        self.assertEqual(1, len(tracer))

        Tracer.detach(session)
        HttpTools.do_get_with_session(url=self.url, session=session)
        self.assertEqual(1, len(tracer))

    @patch("requests.get")
    def test_activate_traces_every_call_of_the_block(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer()

        with tracer.activate("my-flow") as operation:
            HttpTools.do_get(url=self.url)
        HttpTools.do_get(url=self.url)

        entries = tracer.to_list()
        self.assertEqual(1, len(entries))
        self.assertEqual("my-flow", entries[0]["operation"])
        self.assertEqual(operation.id, entries[0]["operation_id"])
        self.assertEqual(1, len(operation))

    @patch("requests.get")
    def test_several_tracers_share_the_same_entry(self, mock_get):
        mock_get.return_value = build_response(body={})
        first, second = Tracer(name="first"), Tracer(name="second")

        with tracing_context(first, second):
            HttpTools.do_get(url=self.url)

        self.assertEqual(1, len(first))
        self.assertEqual(1, len(second))
        self.assertEqual(first.to_list()[0]["id"], second.to_list()[0]["id"])

    @patch("requests.get")
    def test_context_is_inferred_from_the_caller(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer()

        class Caller:
            def fetch(self):
                return HttpTools.do_get(url="https://example.com", tracer=tracer)

        Caller().fetch()

        self.assertEqual("Caller.fetch", tracer.to_list()[0]["context"])

    @patch("requests.get")
    def test_oldest_entries_are_dropped(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer(max_entries=2)

        for index in range(4):
            HttpTools.do_get(url=f"{self.url}/{index}", tracer=tracer)

        entries = tracer.to_list()
        self.assertEqual(2, len(entries))
        self.assertEqual([3, 4], [entry["index"] for entry in entries])

    @patch("requests.get")
    def test_to_json_is_parsable(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer(name="parsable")

        HttpTools.do_get(url=self.url, tracer=tracer)
        parsed = json.loads(tracer.to_json())

        self.assertEqual("parsable", parsed["name"])
        self.assertEqual(1, parsed["count"])
        self.assertEqual(self.url, parsed["entries"][0]["request"]["url"])

    @patch("requests.get")
    def test_clear(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer()

        HttpTools.do_get(url=self.url, tracer=tracer)
        tracer.clear()

        self.assertEqual([], tracer.to_list())

    def test_resolve_tracer(self):
        existing = Tracer()

        self.assertIsNone(resolve_tracer())
        self.assertIsNone(resolve_tracer(trace=False))
        self.assertIsInstance(resolve_tracer(trace=True), Tracer)
        # An existing tracer is always reused, and enables tracing on its own
        self.assertIs(existing, resolve_tracer(tracer=existing))
        self.assertIs(existing, resolve_tracer(trace=True, tracer=existing))


class TestTraceFiltering(unittest.TestCase):
    """`filter()` selects entries by method, status, URL, context and outcome."""

    def setUp(self):
        self.tracer = Tracer(name="filtering")
        responses = [build_response(body={}), build_response(status_code=404, body={"error": "missing"})]
        with patch("requests.get", side_effect=responses), patch("requests.post", return_value=build_response(body={})):
            HttpTools.do_get(url="https://example.com/assets/1", tracer=self.tracer)
            HttpTools.do_post(url="https://example.com/assets", json={"id": "1"}, tracer=self.tracer)
            HttpTools.do_get(url="https://example.com/policies/1", tracer=self.tracer)
        with patch("requests.get", side_effect=ConnectionError("refused")):
            with self.assertRaises(ConnectionError):
                HttpTools.do_get(url="https://example.com/unreachable", tracer=self.tracer)

    def _indexes(self, entries):
        return [entry.index for entry in entries]

    def test_no_filter_returns_everything_in_order(self):
        self.assertEqual([1, 2, 3, 4], self._indexes(self.tracer.entries))

    def test_filter_by_method(self):
        self.assertEqual([2], self._indexes(self.tracer.filter(method="post")))
        self.assertEqual([1, 2, 3, 4], self._indexes(self.tracer.filter(method=["GET", "POST"])))

    def test_filter_by_status_code(self):
        self.assertEqual([3], self._indexes(self.tracer.filter(status_code=404)))
        self.assertEqual([1, 2], self._indexes(self.tracer.filter(status_code=[200, 201])))

    def test_filter_by_url_and_context(self):
        self.assertEqual([1, 2], self._indexes(self.tracer.filter(url="/assets")))
        self.assertEqual([1, 2, 3, 4], self._indexes(self.tracer.filter(context="setUp")))
        self.assertEqual([], self._indexes(self.tracer.filter(context="does-not-exist")))

    def test_filter_by_outcome(self):
        # The 404 and the connection error are both failures
        self.assertEqual([3, 4], self._indexes(self.tracer.failures))
        self.assertEqual([1, 2], self._indexes(self.tracer.filter(failed=False)))

    def test_filters_are_combined(self):
        self.assertEqual([3], self._indexes(self.tracer.filter(method="GET", failed=True, url="/policies")))

    def test_to_list_accepts_the_same_filters(self):
        entries = self.tracer.to_list(method="POST")
        self.assertEqual(1, len(entries))
        self.assertEqual("https://example.com/assets", entries[0]["request"]["url"])

    def test_min_duration(self):
        self.assertEqual([], self._indexes(self.tracer.filter(min_duration_ms=10_000)))
        self.assertEqual(4, len(self.tracer.filter(min_duration_ms=0)))


class TestTraceableMixin(unittest.TestCase):
    class Child(TraceableMixin):
        def __init__(self):
            self.session = requests.Session()

    class Service(TraceableMixin):
        def __init__(self, trace=False, tracer=None, child=None):
            self.child = child
            self._init_tracing(trace=trace, tracer=tracer)

        def call(self, url="https://example.com"):
            return HttpTools.do_get(url=url, **self._trace_kwargs())

    def test_components_are_discovered_and_share_the_tracer(self):
        child = self.Child()
        service = self.Service(trace=True, child=child)

        # The sub-service, and the session it holds, are traced as well
        self.assertIs(service.tracer, child.tracer)
        self.assertIs(service.tracer, getattr(child.session, TRACER_ATTRIBUTE))

        service.set_tracer(None)
        self.assertIsNone(child.tracer)
        self.assertIsNone(getattr(child.session, TRACER_ATTRIBUTE, None))

    def test_propagation_survives_a_cycle(self):
        first, second = self.Service(), self.Service()
        first.child, second.child = second, first
        tracer = Tracer()

        first.set_tracer(tracer)

        self.assertIs(tracer, second.tracer)

    @patch("requests.get")
    def test_trace_is_disabled_by_default(self, mock_get):
        mock_get.return_value = build_response(body={})
        service = self.Service()

        service.call()

        self.assertFalse(service.trace_enabled)
        self.assertIsNone(service.tracer)
        self.assertEqual([], service.get_trace())
        self.assertEqual({"enabled": False, "count": 0, "entries": []}, service.get_trace_dict())
        # Without tracing, the call is left untouched
        self.assertNotIn("tracer", mock_get.call_args.kwargs)

    @patch("requests.get")
    def test_trace_true_records_the_calls(self, mock_get):
        mock_get.return_value = build_response(body={"message": "success"})
        service = self.Service(trace=True)

        service.call()

        self.assertTrue(service.trace_enabled)
        trace = service.get_trace()
        self.assertEqual(1, len(trace))
        self.assertEqual("GET", trace[0]["request"]["method"])
        self.assertEqual(1, json.loads(service.get_trace_json())["count"])

    @patch("requests.get")
    def test_an_existing_tracer_is_shared_between_services(self, mock_get):
        mock_get.return_value = build_response(body={})
        shared = Tracer(name="shared", capture_headers=False)

        first = self.Service(tracer=shared)
        second = self.Service(tracer=shared)

        first.call()
        second.call()

        # Both services record into the very same trace, with its own options
        self.assertIs(shared, first.tracer)
        self.assertIs(shared, second.tracer)
        self.assertEqual(2, len(shared))
        self.assertIsNone(first.get_trace()[0]["request"]["headers"])

    @patch("requests.get")
    def test_get_trace_entries_returns_objects(self, mock_get):
        mock_get.return_value = build_response(body={})
        service = self.Service(trace=True)

        service.call()

        entries = service.get_trace_entries()
        self.assertEqual(1, len(entries))
        self.assertIsInstance(entries[0], TraceEntry)
        self.assertEqual("GET", entries[0].method)
        self.assertEqual(200, entries[0].status_code)
        self.assertFalse(entries[0].failed)
        # The same filters as get_trace(), and empty when tracing is off
        self.assertEqual([], service.get_trace_entries(failed=True))
        self.assertEqual([], self.Service().get_trace_entries())

    @patch("requests.get")
    def test_enable_disable_and_clear_at_runtime(self, mock_get):
        mock_get.return_value = build_response(body={})
        service = self.Service()

        service.enable_trace()
        service.call()
        self.assertEqual(1, len(service.get_trace()))

        service.disable_trace()
        service.call()
        self.assertEqual(1, len(service.get_trace()))

        service.clear_trace()
        self.assertEqual([], service.get_trace())


class TestTraceOperations(unittest.TestCase):
    """`trace_operation()` groups the calls of a `with` block, on their own."""

    class Service(TraceableMixin):
        def __init__(self, trace=False):
            self._init_tracing(trace=trace)

        def call(self, url="https://example.com"):
            return HttpTools.do_get(url=url, **self._trace_kwargs())

    @patch("requests.get")
    def test_operation_on_a_traced_service(self, mock_get):
        mock_get.return_value = build_response(body={})
        service = self.Service(trace=True)

        with service.trace_operation("first") as first:
            service.call()
        with service.trace_operation("second") as second:
            service.call()
        service.call()

        # Each operation holds only the calls of its own block...
        self.assertEqual(1, len(first))
        self.assertEqual(1, len(second))
        # ...while the service keeps accumulating everything
        self.assertEqual(3, len(service.get_trace()))
        self.assertEqual(1, len(service.get_trace(operation="first")))
        self.assertEqual(1, len(service.get_trace(operation_id=second.id)))
        self.assertIsNone(service.get_trace()[2]["operation"])

    @patch("requests.get")
    def test_repeated_operations_stay_apart(self, mock_get):
        mock_get.return_value = build_response(body={})
        service = self.Service(trace=True)

        with service.trace_operation("sync") as first:
            service.call()
        with service.trace_operation("sync") as second:
            service.call()

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(2, len(service.get_trace(operation="sync")))
        self.assertEqual(1, len(service.get_trace(operation_id=first.id)))

    @patch("requests.get")
    def test_operation_without_the_trace_flag(self, mock_get):
        mock_get.return_value = build_response(body={})
        service = self.Service()

        with service.trace_operation("ephemeral") as operation:
            service.call()

        # The block was recorded, and nothing is retained by the service
        self.assertEqual(1, len(operation))
        self.assertIsNone(service.tracer)
        self.assertEqual([], service.get_trace())

    @patch("requests.get")
    def test_nested_operations(self, mock_get):
        mock_get.return_value = build_response(body={})
        tracer = Tracer()

        with tracer.activate("outer") as outer:
            HttpTools.do_get(url="https://example.com/outer")
            with tracer.activate("inner") as inner:
                self.assertIs(inner, get_active_operation())
                HttpTools.do_get(url="https://example.com/inner")

        # The outer operation also contains the calls of the nested block,
        # which are stamped with the innermost operation
        self.assertEqual(2, len(outer))
        self.assertEqual(1, len(inner))
        self.assertEqual(["outer", "inner"], [entry["operation"] for entry in outer.to_list()])
        self.assertIsNone(get_active_operation())

    @patch("requests.get")
    def test_operation_to_json_and_failed(self, mock_get):
        mock_get.return_value = build_response(status_code=502, text="Bad Gateway", content_type="text/html")
        tracer = Tracer()

        with tracer.activate("failing") as operation:
            HttpTools.do_get(url="https://example.com")

        self.assertTrue(operation.failed)
        parsed = json.loads(operation.to_json())
        self.assertEqual("failing", parsed["name"])
        self.assertEqual(1, parsed["count"])
        self.assertTrue(parsed["failed"])
        self.assertIsNotNone(parsed["finished_at"])
        self.assertEqual(502, parsed["entries"][0]["response"]["status_code"])


class TestAdapterTracing(unittest.TestCase):
    @patch("requests.Session.request")
    def test_adapter_traces_its_requests(self, mock_request):
        mock_request.return_value = build_response(body={"message": "success"})
        adapter = Adapter(base_url="https://example.com", headers={"X-Api-Key": "secret"}, tracer=Tracer())

        adapter.post("resources", json={"key": "value"})

        trace = adapter.get_trace()
        self.assertEqual(1, len(trace))
        self.assertEqual("POST", trace[0]["request"]["method"])
        self.assertEqual("https://example.com/resources", trace[0]["request"]["url"])
        self.assertEqual({"key": "value"}, trace[0]["request"]["body"])
        self.assertEqual(REDACTED_VALUE, trace[0]["request"]["headers"]["X-Api-Key"])

    @patch("requests.Session.request")
    def test_adapter_without_trace(self, mock_request):
        mock_request.return_value = build_response(body={})
        adapter = Adapter(base_url="https://example.com")

        adapter.get("resources")

        self.assertEqual([], adapter.get_trace())

    @patch("requests.Session.request")
    def test_tracer_can_be_shared_with_an_adapter(self, mock_request):
        mock_request.return_value = build_response(body={})
        shared = Tracer(name="shared")
        adapter = Adapter(base_url="https://example.com")

        adapter.set_tracer(shared)
        adapter.get("resources")

        self.assertEqual(1, len(shared))
        self.assertIs(shared, adapter.tracer)


if __name__ == "__main__":
    unittest.main()
