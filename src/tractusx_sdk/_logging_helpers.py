#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
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
Private helpers shared by the modules of the SDK that log a failure.

They are not part of the public API.
"""

import logging
import time
from typing import Any

from tractusx_sdk._logging_fields import http_status, log_extra, safe_url


def log_http_request(logger: logging.Logger, method: str, url: Any, **fields: Any) -> None:
    """
    Logs the request line of an HTTP call (method and URL without its query string) at DEBUG.

    Nothing is computed while DEBUG is disabled: it runs on the hot path of every request. Headers, parameters and
    bodies are never logged.
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("HTTP %s %s", method, safe_url(url), extra=log_extra(http_method=method, url=url, **fields), stacklevel=2)


def log_http_outcome(logger: logging.Logger, method: str, url: Any, response: Any, started: float, **fields: Any) -> None:
    """
    Logs the outcome of an HTTP call: a WARNING when the server failed (5xx), DEBUG otherwise.

    A client error (4xx) is an expected outcome for many callers, which are the ones that decide whether it matters.
    ``started`` is the ``time.perf_counter()`` taken before the call.
    """
    status = http_status(response)
    level = logging.WARNING if status is not None and status >= 500 else logging.DEBUG
    if not logger.isEnabledFor(level):
        return
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.log(level, "HTTP %s %s -> %s in %.0f ms", method, safe_url(url), status, elapsed_ms,
               extra=log_extra(http_method=method, url=url, status_code=status, elapsed_ms=round(elapsed_ms), **fields),
               stacklevel=2)


def log_http_failure(logger: logging.Logger, method: str, url: Any, error: BaseException, started: float, **fields: Any) -> None:
    """
    Logs, at DEBUG and by its type only, the exception of an HTTP call that is about to be re-raised unchanged.

    The message and the traceback of the exception quote the full URL, query string included.
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.debug("HTTP %s %s failed after %.0f ms (%s)", method, safe_url(url), elapsed_ms, type(error).__name__,
                 extra=log_extra(http_method=method, url=url, elapsed_ms=round(elapsed_ms), **fields), stacklevel=2)


def log_failure(
    logger: logging.Logger,
    message: str,
    error: BaseException,
    *args: Any,
    level: int = logging.ERROR,
    **fields: Any,
) -> None:
    """
    Logs a failure by the TYPE of its exception, never its message nor its traceback.

    The message and the traceback of a ``requests``/``httpx`` error quote the full URL, query string included,
    and a remote service may echo the request in them, so neither is ever logged. The record points at the line of
    the caller, and ``fields`` are the documented fields of :func:`~tractusx_sdk._logging_fields.log_extra`.

    :param logger: The logger of the calling module
    :param message: A lazy ``%`` format. It must end with the placeholder of the exception type, which is filled last
    :param error: The exception that was caught
    :param args: The arguments of ``message``, without the exception type
    :param level: The level of the record (ERROR by default)
    """
    logger.log(level, message, *args, type(error).__name__, extra=log_extra(**fields), stacklevel=2)
