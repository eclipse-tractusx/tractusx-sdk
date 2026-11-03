#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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

import logging
import time

import requests

from tractusx_sdk._logging_fields import http_status, log_extra, safe_url

from ..tools import HttpTools
from ..tools.tracing import TraceableMixin, Tracer, trace_call

logger = logging.getLogger(__name__)


class Adapter(TraceableMixin):
    """
    Base adapter class
    """

    base_url: str
    session = None

    def __init__(
            self,
            base_url: str,
            headers: dict = None,
            tracer: Tracer = None
    ):
        """
        Create a new adapter instance

        :param base_url: The URL of the application to be requested
        :param headers: The headers (i.e.: API Key) of the application to be requested
        :param tracer: Optional tracer recording the requests/responses performed by
            this adapter. Adapters do not have a `trace` flag of their own: they
            receive the tracer of the service they belong to, or None
        """

        self.base_url = base_url
        self.session = requests.Session()

        if headers:
            self.session.headers.update(headers)

        # Only the number of default headers is logged: their values may be credentials
        logger.debug(
            "Adapter %s created for %s with %d default header(s)",
            type(self).__name__, safe_url(base_url), len(headers or {}),
            extra=log_extra(url=base_url, adapter_type=type(self).__name__),
        )

        self._init_tracing(tracer=tracer)

    @classmethod
    def builder(cls):
        """
        This method is intended to return a builder for adapters inheriting this class.
        This means that such an adapter should implement its own `_Builder` inner class.
        By default, the `Adapter._Builder` class is used.

        :return: a builder for the model inheriting this class
        """
        return cls._Builder(cls)

    class _Builder:
        """
        Default _Builder class for an Adapter.
        """

        def __init__(self, cls):
            self.cls = cls
            self._data = {}

        def base_url(self, base_url: str):
            self._data["base_url"] = base_url
            return self

        def headers(self, headers: dict):
            self._data["headers"] = headers
            return self

        def tracer(self, tracer: Tracer):
            """
            Sets the tracer recording the requests/responses of this adapter.
            """
            self._data["tracer"] = tracer
            return self

        def data(self, data: dict):
            """
            This method is intended to set all the data of the adapters inheriting this class.

            It can be used to set all the data of the adapter in a single call, without the need to declare
            each builder method separately. This is useful for cases where an adapter may deviate from its base
            adapter implementation, and the base adapter builder methods are not sufficient to set all the necessary data.
            """

            self._data.update(data)
            return self

        def build(self):
            """
            :return: an instance of the class inheriting the base adapter
            """
            return self.cls(**self._data)

    def close(self):
        """
        Close the requests session
        """

        logger.debug("Closing the session of adapter %s", type(self).__name__)
        self.session.close()

    def get(self, url: str, **kwargs):
        """
        Perform a GET request

        :param url: Partial URL to append to the base adapter URL
        :param kwargs: Keyword arguments to include in the request

        :return: The response of the request
        """

        return self.request("get", url, **kwargs)

    def post(self, url: str, **kwargs):
        """
        Perform a POST request

        :param url: Partial URL to append to the base adapter URL
        :param kwargs: Keyword arguments to include in the request

        :return: The response of the request
        """

        return self.request("post", url, **kwargs)

    def put(self, url: str, **kwargs):
        """
        Perform a PUT request

        :param url: Partial URL to append to the base adapter URL
        :param kwargs: Keyword arguments to include in the request

        :return: The response of the request
        """

        return self.request("put", url, **kwargs)

    def delete(self, url: str, **kwargs):
        """
        Perform a DELETE request

        :param url: Partial URL to append to the base adapter URL
        :param kwargs: Keyword arguments to include in the request

        :return: The response of the request
        """

        return self.request("delete", url, **kwargs)

    def request(self, method: str, path: str = "", **kwargs):
        """
        Main method for performing requests

        :param method: HTTP method to use with requests
        :param path: Path to append to the base adapter URL
        :param kwargs: Keyword arguments to include in the request

        :return: The response of the request
        """

        url = HttpTools.concat_into_url(self.base_url, path)
        http_method = str(method).upper()
        logged_url = safe_url(url)

        body = kwargs.get("json")
        if body is None:
            body = kwargs.get("data")

        # Headers, parameters and bodies are never logged: they carry credentials and business data
        logger.debug(
            "HTTP %s %s", http_method, logged_url,
            extra=log_extra(http_method=http_method, url=url, adapter_type=type(self).__name__),
        )
        started = time.perf_counter()

        try:
            with trace_call(
                    method=method,
                    url=url,
                    tracer=self._tracer,
                    headers=kwargs.get("headers", self.session.headers),
                    params=kwargs.get("params"),
                    body=body
            ) as call:
                response = self.session.request(
                    method=method,
                    url=url,
                    **kwargs
                )
                call.set_response(response)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "HTTP %s %s failed after %.0f ms", http_method, logged_url, elapsed_ms,
                extra=log_extra(http_method=http_method, url=url, elapsed_ms=round(elapsed_ms)),
            )
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000
        status = http_status(response)
        # A client error (4xx) is an expected outcome for many callers, so only a server failure is a warning
        level = logging.WARNING if status is not None and status >= 500 else logging.DEBUG
        logger.log(
            level, "HTTP %s %s -> %s in %.0f ms", http_method, logged_url, status, elapsed_ms,
            extra=log_extra(
                http_method=http_method, url=url, status_code=status, elapsed_ms=round(elapsed_ms),
                adapter_type=type(self).__name__,
            ),
        )

        return response
