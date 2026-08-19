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

"""
Optional request/response tracing for the Tractus-X SDK.

Tracing is completely opt-in and **never** changes the behaviour of a service:
when no tracer is active every instrumented call takes a fast path and simply
performs the original request.

Enabling it is a matter of passing ``trace=True`` to any SDK service, adapter or
factory, exactly like the ``verbose`` flag::

    service = ServiceFactory.get_connector_consumer_service(..., trace=True)
    service.get_catalog(...)

    print(service.get_trace_json())     # JSON string, ready to be parsed
    entries = service.get_trace()       # list[dict], one entry per HTTP call

Adapters do not have a flag of their own: they receive the ``tracer`` of the
service they belong to, which is either a :class:`Tracer` or ``None``.

Several services write into one single trace by sharing a tracer, which is also
how the recording is configured::

    tracer = Tracer(capture_bodies=False)
    consumer.set_tracer(tracer)
    dtr.set_tracer(tracer)

A single execution can be grouped - and handed back on its own - as a named
operation, whether or not the service was built with ``trace=True``::

    with service.trace_operation("negotiate") as operation:
        service.get_catalog(...)
    print(operation.to_json())           # only the calls of the block

The same block form works on a bare tracer, for code that spans several
services (or none)::

    tracer = Tracer()
    with tracer.activate("my-flow") as operation:
        ...                              # every SDK HTTP call is recorded
    print(tracer.to_json())
"""

import base64
import functools
import inspect
import json
import sys
import threading
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Iterator, Optional

import requests

# Attribute used to bind a tracer to a `requests.Session` (or any other object
# carrying the connection), so that every call made with that session is traced.
TRACER_ATTRIBUTE: str = "__tractusx_sdk_tracer__"

# Header names replaced by `REDACTED_VALUE` when `redact_headers` is enabled.
DEFAULT_REDACTED_HEADERS: frozenset = frozenset({
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "x-api-secret",
    "apikey",
    "api-key",
    "cookie",
    "set-cookie",
})

REDACTED_VALUE: str = "***"

DEFAULT_MAX_ENTRIES: int = 1000
# Bodies are recorded in full by default: set `max_body_chars` to cap them.
DEFAULT_MAX_BODY_CHARS: Optional[int] = None

# Marker recording what a body dropped, and the key holding it inside an object.
TRUNCATED_MARKER: str = "...[truncated {count} {unit}]"
TRUNCATED_KEY: str = "..."

# Modules skipped when guessing the "context" (the caller) of a traced call.
_CONTEXT_SKIPPED_MODULES: tuple = (
    "contextlib",
    "tractusx_sdk.dataspace.tools.tracing",
    "tractusx_sdk.dataspace.tools.http_tools",
    "tractusx_sdk.dataspace.adapters",
)

# Stack of tracers activated with `Tracer.activate()` / `tracing_context()`.
_active_tracers: ContextVar[tuple] = ContextVar("tractusx_sdk_active_tracers", default=())
# Optional label describing the operation currently being executed.
_active_context: ContextVar[Optional[str]] = ContextVar("tractusx_sdk_trace_context", default=None)
# Stack of operations opened with `trace_operation()` / `Tracer.activate()`.
_active_operations: ContextVar[tuple] = ContextVar("tractusx_sdk_active_operations", default=())


def _utc_now() -> str:
    """Returns the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any, max_chars: int) -> Any:
    """
    Converts a value into something that can safely be serialized to JSON.

    Strings and bytes are truncated to `max_chars`, mappings and sequences are
    kept as-is when they are JSON serializable - and shrunk, rather than
    stringified, when they are bigger than `max_chars` - everything else falls
    back to its string representation.
    """
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")

    if isinstance(value, str):
        return _truncate(value, max_chars)

    if isinstance(value, (dict, list, tuple)):
        try:
            serialized = json.dumps(value, default=str)
        except (TypeError, ValueError):
            return _truncate(str(value), max_chars)
        if max_chars is not None and max_chars > 0 and len(serialized) > max_chars:
            return _shrink(json.loads(serialized), max_chars)
        return json.loads(serialized)

    return _truncate(str(value), max_chars)


def _shrink(value: Any, max_chars: int) -> Any:
    """
    Reduces an oversized structured value, keeping it structured.

    Truncating the serialized form would turn the body into an escaped string,
    which can no longer be navigated, so the content itself is trimmed instead:
    long strings are cut and the trailing items/keys that do not fit are
    dropped, each omission being recorded with a marker.
    """
    return _shrink_value(value, [max_chars])


def _shrink_value(value: Any, budget: list) -> Any:
    """
    Trims `value` against a shared, mutable character `budget`.

    Only the types produced by a JSON round trip are handled, since the value
    was already normalized by `_json_safe`.
    """
    if isinstance(value, str):
        if len(value) <= budget[0]:
            budget[0] -= len(value)
            return value
        kept, budget[0] = max(budget[0], 0), 0
        if kept <= 0:
            return TRUNCATED_MARKER.format(count=len(value), unit="chars")
        return _truncate(value, kept)

    if isinstance(value, dict):
        shrunk = {}
        keys = list(value)
        for position, key in enumerate(keys):
            if budget[0] <= 0:
                shrunk[TRUNCATED_KEY] = TRUNCATED_MARKER.format(count=len(keys) - position, unit="keys")
                break
            budget[0] -= len(str(key))
            shrunk[str(key)] = _shrink_value(value[key], budget)
        return shrunk

    if isinstance(value, (list, tuple)):
        shrunk = []
        items = list(value)
        for position, item in enumerate(items):
            if budget[0] <= 0:
                shrunk.append(TRUNCATED_MARKER.format(count=len(items) - position, unit="items"))
                break
            shrunk.append(_shrink_value(item, budget))
        return shrunk

    budget[0] -= len(str(value))
    return value


def _safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    """
    Reads an attribute without ever raising.

    Response objects may guard their attributes (i.e. `httpx.Response.elapsed`
    raises until the response is read), and tracing must never break the call
    it observes.
    """
    try:
        return getattr(obj, name, default)
    except Exception:  # NOSONAR - tracing must not interfere with the request
        return default


def _body_safe(value: Any, max_chars: int) -> Any:
    """
    Records a request/response body, keeping it structured whenever possible.

    Payloads serialized before being sent (the SDK models are sent as JSON
    strings) are parsed back, so that the trace can be navigated - and parsed -
    as JSON instead of carrying an escaped string.
    """
    candidate = value
    if isinstance(candidate, (bytes, bytearray)):
        try:
            candidate = candidate.decode("utf-8")
        except UnicodeDecodeError:
            return _json_safe(value, max_chars)

    if isinstance(candidate, str) and candidate.strip()[:1] in ("{", "["):
        try:
            return _json_safe(json.loads(candidate), max_chars)
        except ValueError:  # not JSON after all, recorded as it is
            pass

    return _json_safe(value, max_chars)


def _truncate(value: str, max_chars: int) -> str:
    """Truncates a string, appending a marker when content was dropped."""
    if max_chars is None or max_chars <= 0 or len(value) <= max_chars:
        return value
    return value[:max_chars] + TRUNCATED_MARKER.format(count=len(value) - max_chars, unit="chars")


def _headers_to_dict(headers: Any, redact: bool, redacted_headers: frozenset) -> Optional[dict]:
    """Normalizes headers into a plain dict, optionally redacting secrets."""
    if headers is None:
        return None

    try:
        items = headers.items()
    except AttributeError:
        return {"headers": str(headers)}

    result: dict = {}
    for key, value in items:
        if redact and str(key).lower() in redacted_headers:
            result[str(key)] = REDACTED_VALUE
        else:
            result[str(key)] = value if isinstance(value, str) else str(value)
    return result


def _content_type(headers: Any) -> Optional[str]:
    """Reads the content type out of response headers, without ever raising."""
    if headers is None:
        return None
    try:
        return headers.get("Content-Type") or headers.get("content-type")
    except (AttributeError, TypeError):
        return None


def _infer_context() -> Optional[str]:
    """
    Best-effort discovery of the SDK method that triggered a traced call.

    Walks up the stack, skipping the tracing/HTTP plumbing, and builds a
    `ClassName.method_name` label out of the first relevant frame.
    """
    try:
        frame = sys._getframe(1)  # NOSONAR - only executed while tracing is enabled
    except (ValueError, AttributeError):  # pragma: no cover - platform dependent
        return None

    while frame is not None:
        module_name = frame.f_globals.get("__name__", "")
        if not module_name.startswith(_CONTEXT_SKIPPED_MODULES):
            instance = frame.f_locals.get("self")
            method = frame.f_code.co_name
            if instance is not None:
                return f"{type(instance).__name__}.{method}"
            return f"{module_name}.{method}"
        frame = frame.f_back

    return None


@dataclass
class TraceEntry:
    """
    A single traced interaction with an external service.

    An entry is created before the request is sent, and completed once the
    response (or the error) is known.
    """

    id: str
    index: int
    method: str
    url: str
    context: Optional[str] = None
    operation: Optional[str] = None
    operation_id: Optional[str] = None
    started_at: str = field(default_factory=_utc_now)
    finished_at: Optional[str] = None
    duration_ms: Optional[float] = None
    request: dict = field(default_factory=dict)
    response: Optional[dict] = None
    error: Optional[dict] = None

    @property
    def status_code(self) -> Optional[int]:
        """Convenience accessor for the response status code, when available."""
        return None if self.response is None else self.response.get("status_code")

    @property
    def failed(self) -> bool:
        """Whether the call raised, or came back with a 4xx/5xx status code."""
        if self.error is not None:
            return True

        status_code = self.status_code
        return status_code is not None and status_code >= 400

    def to_dict(self) -> dict:
        """Returns the entry as a plain, JSON serializable dictionary."""
        return {
            "id": self.id,
            "index": self.index,
            "context": self.context,
            "operation": self.operation,
            "operation_id": self.operation_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "request": self.request,
            "response": self.response,
            "error": self.error,
        }


class TraceCall:
    """
    Handle returned by :func:`trace_call`, used to complete a trace entry.

    The no-op flavour (``entry is None``) is returned when no tracer is active,
    keeping the instrumentation cost close to zero.
    """

    __slots__ = ("entry", "_tracers", "_started")

    def __init__(self, entry: Optional[TraceEntry] = None, tracers: tuple = ()):
        self.entry = entry
        self._tracers = tracers
        self._started = perf_counter()

    @property
    def enabled(self) -> bool:
        """Whether this call is actually being recorded."""
        return self.entry is not None

    def set_response(self, response: Any) -> Any:
        """
        Attaches a response (``requests`` or ``httpx``) to the trace entry.

        :param response: The response object returned by the HTTP client
        :return: The response, unchanged, so it can be used inline
        """
        if self.entry is None:
            return response

        # The entry is shared between the tracers, so it is completed only once
        self._tracers[0].complete_entry(self.entry, response=response, duration_ms=self._elapsed_ms())
        self._finish()
        return response

    def set_error(self, error: BaseException) -> None:
        """Attaches an exception to the trace entry."""
        if self.entry is None:
            return

        self._tracers[0].complete_entry(self.entry, error=error, duration_ms=self._elapsed_ms())
        self._finish()

    def complete(self) -> None:
        """Closes the entry without a response, for calls that returned early."""
        if self.entry is None:
            return

        self._tracers[0].complete_entry(self.entry, duration_ms=self._elapsed_ms())
        self._finish()

    def _elapsed_ms(self) -> float:
        return round((perf_counter() - self._started) * 1000, 3)

    def _finish(self) -> None:
        self.entry = None


class TraceOperation:
    """
    A named group of trace entries, collected while a ``with`` block executes.

    Operations are opened by :meth:`Tracer.activate` and
    :meth:`TraceableMixin.trace_operation`: every call recorded inside the
    block belongs to the operation, so the requests/responses of one specific
    execution can be handed back on their own - even when the tracer keeps
    accumulating the calls of a long-lived instance.
    """

    __slots__ = ("id", "name", "started_at", "finished_at", "_entries", "_lock")

    def __init__(self, name: Optional[str] = None):
        self.id = uuid.uuid4().hex
        self.name = name
        self.started_at = _utc_now()
        self.finished_at: Optional[str] = None
        self._entries: list = []
        self._lock = threading.RLock()

    def add(self, entry: TraceEntry) -> TraceEntry:
        """Adds an entry to this operation."""
        with self._lock:
            self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list:
        """Returns a copy of the recorded entries, in execution order."""
        with self._lock:
            return list(self._entries)

    @property
    def failed(self) -> bool:
        """Whether any call of the operation raised, or returned a 4xx/5xx."""
        return any(entry.failed for entry in self.entries)

    def to_list(self) -> list:
        """Returns the recorded entries as a list of dictionaries."""
        return [entry.to_dict() for entry in self.entries]

    def to_dict(self) -> dict:
        """Returns the operation, including its metadata, as a dictionary."""
        entries = self.entries
        return {
            "id": self.id,
            "name": self.name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "failed": any(entry.failed for entry in entries),
            "count": len(entries),
            "entries": [entry.to_dict() for entry in entries],
        }

    def to_json(self, indent: int = 2, **kwargs) -> str:
        """
        Returns the operation as a JSON string, ready to be parsed.

        :param indent: Indentation used by `json.dumps` (default: 2)
        :param kwargs: Any additional `json.dumps` keyword argument
        """
        kwargs.setdefault("default", str)
        return json.dumps(self.to_dict(), indent=indent, **kwargs)

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator:
        return iter(self.entries)

    def __repr__(self) -> str:
        return f"<TraceOperation name={self.name!r} id={self.id} entries={len(self.entries)}>"


class Tracer:
    """
    Collects the requests sent to (and the responses received from) external
    services during the execution of SDK methods.

    A tracer is thread safe and can be shared between several services, so a
    complete business flow ends up in a single, ordered trace.
    """

    def __init__(
        self,
        enabled: bool = True,
        name: Optional[str] = None,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        capture_bodies: bool = True,
        capture_headers: bool = True,
        max_body_chars: Optional[int] = DEFAULT_MAX_BODY_CHARS,
        redact_headers: bool = True,
        redacted_headers: Optional[set] = None,
    ):
        """
        Create a new tracer.

        :param enabled: Whether the tracer records calls (default: True)
        :param name: Optional name, useful when several tracers are used
        :param max_entries: Maximum number of entries kept (oldest are dropped)
        :param capture_bodies: Whether request/response bodies are recorded
        :param capture_headers: Whether request/response headers are recorded
        :param max_body_chars: Maximum size of a recorded body, in characters, or
            None (the default) to record the bodies in full
        :param redact_headers: Whether sensitive headers are masked
        :param redacted_headers: Custom set of header names to mask
        """
        self.enabled = enabled
        self.name = name
        self.max_entries = max_entries
        self.capture_bodies = capture_bodies
        self.capture_headers = capture_headers
        self.max_body_chars = max_body_chars
        self.redact_headers = redact_headers
        self.redacted_headers = frozenset(
            h.lower() for h in (redacted_headers if redacted_headers is not None else DEFAULT_REDACTED_HEADERS)
        )
        self.created_at = _utc_now()

        self._entries: list = []
        self._counter: int = 0
        self._lock = threading.RLock()

    ############################# Recording

    def start_entry(
        self,
        method: str,
        url: str,
        headers: Any = None,
        params: Any = None,
        body: Any = None,
        context: Optional[str] = None,
    ) -> TraceEntry:
        """
        Registers a new (incomplete) entry for an outgoing request.

        :param method: The HTTP method of the request
        :param url: The URL of the external service
        :param headers: The request headers
        :param params: The request query parameters
        :param body: The request body (json or data)
        :param context: Label describing the SDK method performing the call
        :return: The created trace entry
        """
        with self._lock:
            self._counter += 1
            index = self._counter

        entry = TraceEntry(
            id=uuid.uuid4().hex,
            index=index,
            method=str(method).upper(),
            url=url,
            context=context,
            request={
                "method": str(method).upper(),
                "url": url,
                "headers": _headers_to_dict(headers, self.redact_headers, self.redacted_headers)
                if self.capture_headers else None,
                "params": _json_safe(params, self.max_body_chars) if params is not None else None,
                "body": _body_safe(body, self.max_body_chars) if (self.capture_bodies and body is not None) else None,
            },
        )
        self.add(entry)
        return entry

    def complete_entry(
        self,
        entry: TraceEntry,
        response: Any = None,
        error: BaseException = None,
        duration_ms: float = None,
    ) -> TraceEntry:
        """
        Completes an entry with the response received, or the error raised.

        :param entry: The entry created by `start_entry`
        :param response: The response object (``requests`` or ``httpx``)
        :param error: The exception raised while performing the request
        :param duration_ms: The duration of the call, in milliseconds
        :return: The completed trace entry
        """
        entry.finished_at = _utc_now()
        entry.duration_ms = duration_ms

        if response is not None:
            entry.response = self._describe_response(response)

        if error is not None:
            entry.error = {
                "type": type(error).__name__,
                "message": _truncate(str(error), self.max_body_chars),
            }

        return entry

    def add(self, entry: TraceEntry) -> TraceEntry:
        """Adds an entry to the trace, dropping the oldest ones when full."""
        with self._lock:
            self._entries.append(entry)
            if self.max_entries and len(self._entries) > self.max_entries:
                del self._entries[0:len(self._entries) - self.max_entries]
        return entry

    def _describe_response(self, response: Any) -> dict:
        """Extracts the relevant information out of a response object."""
        headers = _safe_getattr(response, "headers")
        description: dict = {
            "status_code": _safe_getattr(response, "status_code"),
            "reason": _safe_getattr(response, "reason") or _safe_getattr(response, "reason_phrase"),
            "content_type": _content_type(headers),
        }

        if self.capture_headers:
            description["headers"] = _headers_to_dict(headers, self.redact_headers, self.redacted_headers)

        elapsed = _safe_getattr(response, "elapsed")
        if elapsed is not None:
            try:
                description["elapsed_ms"] = round(elapsed.total_seconds() * 1000, 3)
            except AttributeError:  # pragma: no cover - non standard response
                description["elapsed_ms"] = None

        if self.capture_bodies:
            description["body"] = self._extract_body(response)

        return description

    def _extract_body(self, response: Any) -> Any:
        """
        Reads the response body, preferring JSON and falling back to text.

        Non-JSON textual bodies (HTML error pages, plain text) are recorded as
        they are, and binary bodies (files, archives) are recorded base64
        encoded. Bodies that cannot be read at all (streamed responses) are
        skipped, rather than breaking the call being traced.
        """
        try:
            return _json_safe(response.json(), self.max_body_chars)
        except Exception:  # NOSONAR - any parsing issue falls back to the raw content
            pass

        content = _safe_getattr(response, "content")
        if isinstance(content, (bytes, bytearray)):
            try:
                return _body_safe(content.decode("utf-8"), self.max_body_chars)
            except UnicodeDecodeError:
                encoded = base64.b64encode(bytes(content)).decode("ascii")
                return {
                    "encoding": "base64",
                    "length": len(content),
                    "data": _truncate(encoded, self.max_body_chars),
                }

        try:
            return _body_safe(response.text, self.max_body_chars)
        except Exception:  # NOSONAR - streamed responses may not expose their content
            return None

    ############################# Consumption

    @property
    def entries(self) -> list:
        """Returns a copy of the recorded entries, in execution order."""
        with self._lock:
            return list(self._entries)

    @property
    def failures(self) -> list:
        """Returns the entries that raised, or came back with a 4xx/5xx status."""
        return self.filter(failed=True)

    def filter(
        self,
        method: Any = None,
        status_code: Any = None,
        url: str = None,
        context: str = None,
        operation: str = None,
        operation_id: str = None,
        failed: bool = None,
        min_duration_ms: float = None,
    ) -> list:
        """
        Returns the entries matching every given criterion.

        All the parameters are optional, and are combined with an AND::

            tracer.filter(method="POST", failed=True)
            tracer.filter(url="/catalog/request")
            tracer.filter(status_code=[200, 201], min_duration_ms=500)

        :param method: An HTTP method, or a list of them (case insensitive)
        :param status_code: A response status code, or a list of them
        :param url: Substring the URL must contain (case insensitive)
        :param context: Substring the context must contain (case insensitive)
        :param operation: Substring the operation name must contain (case
            insensitive), see `trace_operation()`
        :param operation_id: Exact id of one operation, so repeated executions
            of the same (equally named) operation stay apart
        :param failed: `True` keeps the calls that raised or returned a 4xx/5xx,
            `False` keeps only the successful ones
        :param min_duration_ms: Minimum duration of the call, in milliseconds
        :return: The matching trace entries, in execution order
        """
        methods = _as_lookup(method, upper=True)
        status_codes = _as_lookup(status_code)
        url_part = url.lower() if url else None
        context_part = context.lower() if context else None
        operation_part = operation.lower() if operation else None

        return [
            entry for entry in self.entries
            if _entry_matches(entry, methods, status_codes, url_part, context_part, failed, min_duration_ms)
            and _entry_matches_operation(entry, operation_part, operation_id)
        ]

    def to_list(self, **filters) -> list:
        """
        Returns the recorded entries as a list of dictionaries.

        :param filters: Any keyword argument accepted by `filter()`
        """
        entries = self.filter(**filters) if filters else self.entries
        return [entry.to_dict() for entry in entries]

    def to_dict(self) -> dict:
        """Returns the complete trace, including its metadata, as a dictionary."""
        entries = self.entries
        return {
            "name": self.name,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "count": len(entries),
            "entries": [entry.to_dict() for entry in entries],
        }

    def to_json(self, indent: int = 2, **kwargs) -> str:
        """
        Returns the complete trace as a JSON string, ready to be parsed.

        :param indent: Indentation used by `json.dumps` (default: 2)
        :param kwargs: Any additional `json.dumps` keyword argument
        """
        kwargs.setdefault("default", str)
        return json.dumps(self.to_dict(), indent=indent, **kwargs)

    def clear(self) -> None:
        """Removes every recorded entry."""
        with self._lock:
            self._entries.clear()

    def enable(self) -> "Tracer":
        """Enables recording."""
        self.enabled = True
        return self

    def disable(self) -> "Tracer":
        """Disables recording, without discarding the entries already recorded."""
        self.enabled = False
        return self

    ############################# Binding

    def attach(self, session: Any) -> Any:
        """
        Binds this tracer to a session, tracing every call performed with it.

        :param session: A `requests.Session` (or any object used as one)
        :return: The session, unchanged
        """
        if session is not None:
            try:
                setattr(session, TRACER_ATTRIBUTE, self)
            except AttributeError:  # pragma: no cover - immutable objects
                pass
        return session

    @staticmethod
    def detach(session: Any) -> Any:
        """Removes the tracer bound to a session, if any."""
        if session is not None and getattr(session, TRACER_ATTRIBUTE, None) is not None:
            try:
                delattr(session, TRACER_ATTRIBUTE)
            except AttributeError:  # pragma: no cover - immutable objects
                pass
        return session

    @contextmanager
    def activate(self, name: Optional[str] = None):
        """
        Records every SDK call performed inside the block, as one operation.

        The yielded :class:`TraceOperation` groups only the calls of the block,
        while the tracer keeps everything it has recorded::

            with tracer.activate("negotiate") as operation:
                ...                      # every SDK HTTP call is recorded
            print(operation.to_json())   # only the calls of the block

        :param name: Optional name of the operation, stored in its entries
        """
        with tracing_context(self):
            with _operation_scope(name) as operation:
                yield operation

    ############################# Dunder helpers

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator:
        return iter(self.entries)

    def __bool__(self) -> bool:
        # A tracer is always truthy, even when no entry was recorded yet.
        return True

    def __repr__(self) -> str:
        return f"<Tracer name={self.name!r} enabled={self.enabled} entries={len(self.entries)}>"


def get_active_tracers() -> tuple:
    """Returns the tracers activated for the current execution context."""
    return _active_tracers.get()


def get_active_context() -> Optional[str]:
    """Returns the label of the operation currently being traced, if any."""
    return _active_context.get()


def get_active_operation() -> Optional[TraceOperation]:
    """Returns the innermost operation currently being recorded, if any."""
    operations = _active_operations.get()
    return operations[-1] if operations else None


@contextmanager
def _operation_scope(name: Optional[str] = None):
    """
    Opens a new operation, nested inside the ones already active.

    Every entry recorded while the scope is open belongs to the new operation
    and to the enclosing ones, so an outer operation also contains the calls of
    the blocks nested inside it.
    """
    operation = TraceOperation(name=name)
    token = _active_operations.set(_active_operations.get() + (operation,))
    try:
        yield operation
    finally:
        operation.finished_at = _utc_now()
        _active_operations.reset(token)


@contextmanager
def tracing_context(*tracers: Tracer, context: Optional[str] = None):
    """
    Activates one or more tracers (and an optional label) for a block of code.

    :param tracers: The tracers that should record the calls made in the block
    :param context: Optional label stored in the entries created inside
    """
    valid_tracers = tuple(tracer for tracer in tracers if tracer is not None)
    tracers_token = None
    context_token = None

    if valid_tracers:
        current = _active_tracers.get()
        merged = current + tuple(tracer for tracer in valid_tracers if not _contains(current, tracer))
        tracers_token = _active_tracers.set(merged)

    if context is not None:
        context_token = _active_context.set(context)

    try:
        yield
    finally:
        if tracers_token is not None:
            _active_tracers.reset(tracers_token)
        if context_token is not None:
            _active_context.reset(context_token)


def _contains(tracers: tuple, tracer: Tracer) -> bool:
    """Identity based membership check (tracers are not comparable by value)."""
    return any(item is tracer for item in tracers)


def resolve_tracers(tracer: Any = None, session: Any = None, extra: Any = None) -> tuple:
    """
    Collects, without duplicates, every tracer that should record a call.

    :param tracer: An explicitly provided tracer
    :param session: A session that may have a tracer bound to it
    :param extra: Any other object that may have a tracer bound to it
    :return: The tuple of enabled tracers, empty when tracing is off
    """
    resolved: list = []

    for candidate in (
        tracer,
        getattr(session, TRACER_ATTRIBUTE, None) if session is not None else None,
        getattr(extra, TRACER_ATTRIBUTE, None) if extra is not None else None,
    ):
        if isinstance(candidate, Tracer) and candidate.enabled and not _contains(tuple(resolved), candidate):
            resolved.append(candidate)

    for candidate in _active_tracers.get():
        if candidate.enabled and not _contains(tuple(resolved), candidate):
            resolved.append(candidate)

    return tuple(resolved)


@contextmanager
def trace_call(
    method: str,
    url: str,
    tracer: Any = None,
    session: Any = None,
    headers: Any = None,
    params: Any = None,
    body: Any = None,
    context: Optional[str] = None,
):
    """
    Traces a single call to an external service.

    The block is executed unchanged when no tracer is active::

        with trace_call("GET", url, tracer=self.tracer) as call:
            call.set_response(requests.get(url))

    :param method: The HTTP method used
    :param url: The URL of the external service
    :param tracer: An explicit tracer, if any
    :param session: A session that may have a tracer bound to it
    :param headers: The request headers
    :param params: The request query parameters
    :param body: The request body (json or data)
    :param context: Label describing the SDK method performing the call
    """
    tracers = resolve_tracers(tracer=tracer, session=session)

    if not tracers:
        yield TraceCall()
        return

    entry_context = context or get_active_context() or _infer_context()
    entry = tracers[0].start_entry(
        method=method, url=url, headers=headers, params=params, body=body, context=entry_context
    )
    # Additional tracers share the very same entry, keeping the traces aligned.
    for additional_tracer in tracers[1:]:
        additional_tracer.add(entry)

    # The entry belongs to every operation on the stack (an outer operation
    # also contains the calls of the blocks nested inside it), and is stamped
    # with the innermost one.
    operations = _active_operations.get()
    if operations:
        entry.operation = operations[-1].name
        entry.operation_id = operations[-1].id
        for operation in operations:
            operation.add(entry)

    call = TraceCall(entry=entry, tracers=tracers)
    try:
        yield call
    except BaseException as exception:
        call.set_error(exception)
        raise
    else:
        # The caller never attached a response (e.g. it returned early)
        call.complete()


def resolve_tracer(
    trace: bool = False,
    tracer: Optional["Tracer"] = None,
    name: Optional[str] = None,
) -> Optional["Tracer"]:
    """
    Builds (or reuses) the tracer described by the `trace`/`tracer` parameters.

    This is the single place where the tracing options of the SDK are
    interpreted, so every service, adapter and factory behaves the same way:

    * `trace=True` starts recording into a new tracer
    * `tracer=<Tracer>` records into an existing tracer, which is how a single
      trace is shared between several services
    * neither of them (the default) disables tracing entirely

    :param trace: Flag enabling the tracing of the requests/responses
    :param tracer: An existing tracer to write the entries into, or None
    :param name: Name given to the tracer when a new one has to be created
    :return: The tracer to be used, or None when tracing is disabled
    """
    if tracer is not None:
        return tracer
    if trace:
        return Tracer(name=name)
    return None


def _has_bound_tracer(args: tuple, kwargs: dict) -> bool:
    """Cheap check for a tracer bound to one of the arguments (i.e. a session)."""
    if getattr(kwargs.get("session"), TRACER_ATTRIBUTE, None) is not None:
        return True
    return any(getattr(argument, TRACER_ATTRIBUTE, None) is not None for argument in args)


def traced_http(method: str):
    """
    Instruments an HTTP helper function, so that its calls can be traced.

    The wrapped function keeps its original behaviour and accepts two extra
    (optional) keyword arguments:

    * ``tracer``: the :class:`Tracer` that should record the call
    * ``trace_context``: a label describing the operation being performed

    When no tracer is active the call takes a fast path, and the original
    function is invoked without any additional processing.

    :param method: The HTTP method performed by the decorated function
    """

    def decorator(func):
        signature = None

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = kwargs.pop("tracer", None)
            context = kwargs.pop("trace_context", None)

            if tracer is None and not _active_tracers.get() and not _has_bound_tracer(args, kwargs):
                return func(*args, **kwargs)

            nonlocal signature
            if signature is None:
                signature = inspect.signature(func)

            try:
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                arguments = bound.arguments
            except TypeError:  # pragma: no cover - invalid calls are left to the callee
                arguments = kwargs

            body = arguments.get("json")
            if body is None:
                body = arguments.get("data")

            with trace_call(
                method=method,
                url=arguments.get("url"),
                tracer=tracer,
                session=arguments.get("session"),
                headers=arguments.get("headers"),
                params=arguments.get("params"),
                body=body,
                context=context,
            ) as call:
                return call.set_response(func(*args, **kwargs))

        return wrapper

    return decorator


def _as_lookup(value: Any, upper: bool = False) -> Optional[set]:
    """Normalizes a filter value (a scalar or a list of them) into a set."""
    if value is None:
        return None

    values = [value] if isinstance(value, (str, int)) else list(value)
    return {str(item).upper() if upper else item for item in values}


def _entry_matches(
    entry: TraceEntry,
    methods: Optional[set],
    status_codes: Optional[set],
    url_part: Optional[str],
    context_part: Optional[str],
    failed: Optional[bool],
    min_duration_ms: Optional[float],
) -> bool:
    """Whether a trace entry matches every given filter criterion."""
    if methods is not None and entry.method not in methods:
        return False
    if status_codes is not None and entry.status_code not in status_codes:
        return False
    if url_part is not None and url_part not in (entry.url or "").lower():
        return False
    if context_part is not None and context_part not in (entry.context or "").lower():
        return False
    if failed is not None and entry.failed is not failed:
        return False
    if min_duration_ms is not None and (entry.duration_ms is None or entry.duration_ms < min_duration_ms):
        return False
    return True


def _entry_matches_operation(
    entry: TraceEntry,
    operation_part: Optional[str],
    operation_id: Optional[str],
) -> bool:
    """Whether a trace entry belongs to the given operation."""
    if operation_part is not None and operation_part not in (entry.operation or "").lower():
        return False
    if operation_id is not None and entry.operation_id != operation_id:
        return False
    return True


def _traceable_components(value: Any) -> Iterator:
    """
    Yields the traceable components held by an attribute value.

    Recognizes the shapes used across the SDK: traceable objects (services,
    adapters), `requests` sessions, collections of them, and the controllers
    that delegate to an adapter.

    :param value: The value of an attribute of a traceable instance
    """
    if isinstance(value, (TraceableMixin, requests.Session)):
        yield value
        return

    if isinstance(value, dict):
        items = value.values()
    elif isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = (value,)

    for item in items:
        if isinstance(item, (TraceableMixin, requests.Session)):
            yield item
            continue
        # Controllers (and similar wrappers) expose the adapter they delegate to
        adapter = _safe_getattr(item, "adapter")
        if isinstance(adapter, TraceableMixin):
            yield adapter


class TraceableMixin:
    """
    Adds an optional `trace` capability to services, adapters and managers.

    Classes using this mixin accept a `trace` parameter, and expose the
    collected requests/responses through `get_trace()` and `get_trace_json()`.

    The tracer is shared with everything the instance is built upon: the
    adapters, sessions and sub-services it holds are discovered automatically
    (see `_traceable_targets`), so a service does not have to forward it by hand.
    """

    _tracer: Optional[Tracer] = None

    def _init_tracing(self, trace: bool = False, tracer: Optional[Tracer] = None) -> Optional[Tracer]:
        """
        Configures tracing for this instance.

        Call it once the instance is built: the tracer is shared with every
        component it is composed of.

        :param trace: Flag enabling the tracing of the requests/responses
        :param tracer: An existing tracer to write the entries into, or None
        :return: The tracer used by this instance, or None when disabled
        """
        resolved = resolve_tracer(trace=trace, tracer=tracer, name=type(self).__name__)
        if resolved is None:
            self._tracer = None
            return None

        return self.set_tracer(resolved)

    @property
    def tracer(self) -> Optional[Tracer]:
        """The tracer used by this instance, or None when tracing is disabled."""
        return self._tracer

    @property
    def trace_enabled(self) -> bool:
        """Whether this instance is currently tracing its external calls."""
        return self._tracer is not None and self._tracer.enabled

    def set_tracer(self, tracer: Optional[Tracer]) -> Optional[Tracer]:
        """
        Replaces (or shares) the tracer used by this instance.

        The tracer is handed over to every component this instance is built
        upon, so that one single trace contains the complete flow.

        :param tracer: The tracer to use, or None to stop tracing
        :return: The tracer used by this instance
        """
        return self._apply_tracer(tracer, set())

    def _apply_tracer(self, tracer: Optional[Tracer], visited: set) -> Optional[Tracer]:
        """
        Sets the tracer of this instance and of its components, only once each.

        :param tracer: The tracer to use, or None to stop tracing
        :param visited: The components already handled, guarding against cycles
        :return: The tracer used by this instance
        """
        if id(self) in visited:
            return self._tracer

        visited.add(id(self))
        self._tracer = tracer

        for target in self._traceable_targets():
            if isinstance(target, TraceableMixin):
                target._apply_tracer(tracer, visited)  # NOSONAR - same class, shared propagation
            elif id(target) not in visited:
                # Sessions carry the tracer, so every call made with them is traced
                visited.add(id(target))
                if tracer is None:
                    Tracer.detach(target)
                else:
                    tracer.attach(target)

        return self._tracer

    def _traceable_targets(self) -> Iterator:
        """
        The components whose calls belong to the trace of this instance.

        The adapters, sessions, controllers and sub-services held as attributes
        are discovered automatically. Override this method (yielding from the
        parent implementation) when a component cannot be reached that way.

        :return: The traceable components this instance is built upon
        """
        for value in list(getattr(self, "__dict__", {}).values()):
            yield from _traceable_components(value)

    def enable_trace(self, tracer: Optional[Tracer] = None) -> Optional[Tracer]:
        """
        Enables tracing at runtime.

        :param tracer: An existing tracer to write the entries into, or None to
            keep (or create) the tracer of this instance
        :return: The tracer used by this instance
        """
        if tracer is not None or self._tracer is None:
            self.set_tracer(resolve_tracer(trace=True, tracer=tracer, name=type(self).__name__))
        else:
            self._tracer.enable()

        return self._tracer

    def disable_trace(self) -> None:
        """Stops recording, keeping the entries collected so far."""
        if self._tracer is not None:
            self._tracer.disable()

    @contextmanager
    def trace_operation(self, name: Optional[str] = None):
        """
        Records the calls performed inside the block, as one named operation.

        The yielded :class:`TraceOperation` groups only the calls of the block,
        so the requests/responses of one specific execution can be found - and
        parsed - on their own, even when the same instance keeps executing
        other methods::

            with service.trace_operation("negotiate") as operation:
                service.get_catalog(...)
            print(operation.to_json())      # only the calls of the block

        When this instance was built with ``trace=True`` the calls also
        accumulate in its own trace, where `get_trace(operation=name)` (or
        `get_trace(operation_id=operation.id)`) finds them again later. Without
        the flag, a temporary tracer records the block, and nothing is retained
        once the operation is consumed.

        :param name: Optional name of the operation, stored in its entries
        """
        tracer = self._tracer if self.trace_enabled else Tracer(name=name)
        with tracer.activate(name) as operation:
            yield operation

    def get_trace(self, **filters) -> list:
        """
        Returns the recorded requests and responses.

        :param filters: Any keyword argument accepted by `Tracer.filter()`, i.e.
            `get_trace(method="POST")` or `get_trace(failed=True)`
        :return: A list of dictionaries, empty when tracing is disabled
        """
        return [] if self._tracer is None else self._tracer.to_list(**filters)

    def get_trace_entries(self, **filters) -> list:
        """
        Returns the recorded requests and responses as `TraceEntry` objects.

        The object flavour of `get_trace()`: same filters, but the entries keep
        their typed accessors (`method`, `url`, `status_code`, `failed`,
        `duration_ms`, ...) instead of being converted to dictionaries::

            for entry in service.get_trace_entries(failed=True):
                print(entry.method, entry.url, entry.status_code)

        :param filters: Any keyword argument accepted by `Tracer.filter()`
        :return: A list of `TraceEntry` objects, empty when tracing is disabled
        """
        return [] if self._tracer is None else self._tracer.filter(**filters)

    def get_trace_dict(self) -> dict:
        """Returns the complete trace (metadata included) as a dictionary."""
        return {"enabled": False, "count": 0, "entries": []} if self._tracer is None else self._tracer.to_dict()

    def get_trace_json(self, indent: int = 2, **kwargs) -> str:
        """
        Returns the complete trace as a JSON string, ready to be parsed.

        :param indent: Indentation used by `json.dumps` (default: 2)
        """
        kwargs.setdefault("default", str)
        return json.dumps(self.get_trace_dict(), indent=indent, **kwargs)

    def clear_trace(self) -> None:
        """Removes every recorded entry."""
        if self._tracer is not None:
            self._tracer.clear()

    def _trace_kwargs(self, context: Optional[str] = None) -> dict:
        """
        Extra keyword arguments forwarding this instance's tracer to `HttpTools`.

        The returned dictionary is **empty** when tracing is disabled, so that
        the resulting call is exactly the one performed before tracing existed::

            HttpTools.do_post(url=url, json=body, **self._trace_kwargs())

        :param context: Optional label describing the operation being performed
        :return: The tracing keyword arguments, empty when tracing is disabled
        """
        if self._tracer is None:
            return {}

        kwargs: dict = {"tracer": self._tracer}
        if context is not None:
            kwargs["trace_context"] = context
        return kwargs
