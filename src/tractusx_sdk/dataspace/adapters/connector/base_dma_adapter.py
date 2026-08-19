#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

from requests.structures import CaseInsensitiveDict

from ..adapter import Adapter
from ...tools import HttpTools
from ...tools.tracing import Tracer


class BaseDmaAdapter(Adapter):
    dma_path: str = ""

    def __init__(self, base_url: str, dma_path: str, headers: dict = None, tracer: Tracer = None):
        """
        Create a new DMA adapter instance

        :param base_url: The base URL of the Connector
        :param dma_path: The path of the Connector Data Management API
        :param headers: The headers (i.e.: API Key) of the Connector to be requested
        :param tracer: Optional tracer recording the requests/responses, usually the
            one of the service this adapter belongs to
        """
        self.dma_path = dma_path

        dma_url = HttpTools.concat_into_url(base_url, dma_path)
        super().__init__(dma_url, headers, tracer=tracer)

    def request(self, method: str, path: str = "", **kwargs):
        """
        Perform a request against the Connector Data Management API

        The Connector models are serialized before being sent (`data=`), which does not
        set a content type by itself, and the API answers `415 Unsupported Media Type`
        without one. The Data Management API only speaks JSON, so the content type
        defaults to `application/json` for every request carrying a body, unless the
        caller already provided one.

        :param method: HTTP method to use with requests
        :param path: Path to append to the base adapter URL
        :param kwargs: Keyword arguments to include in the request

        :return: The response of the request
        """
        if kwargs.get("data") is not None:
            headers = CaseInsensitiveDict(self.session.headers)
            headers.update(kwargs.get("headers") or {})
            headers.setdefault("Content-Type", "application/json")
            kwargs["headers"] = headers

        return super().request(method, path, **kwargs)

    class _Builder(Adapter._Builder):
        def dma_path(self, dma_path: str):
            self._data["dma_path"] = dma_path
            return self
