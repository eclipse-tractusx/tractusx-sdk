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

from abc import ABC, abstractmethod

from ..tools.tracing import TraceableMixin


class BaseService(TraceableMixin, ABC):
    """
    Base service class of the SDK, and the class every service inherits from.

    Through `TraceableMixin`, it gives every service the optional `trace` flag,
    which records the requests sent to (and the responses received from) the
    external services contacted while its methods are executed. The collected
    trace is available through `get_trace()` (list of dicts) and
    `get_trace_json()`, and `set_tracer()` shares it with other services.
    `trace_operation()` groups the calls of a single `with` block, and hands
    them back on their own - whether or not the flag is set.

    The tracer is handed over to everything the service is built upon (its
    adapters, sessions, controllers and sub-services), which is discovered
    automatically, so a service only has to call `_init_tracing(trace=trace)`
    once it is built.
    """

    dataspace_version: str

    @abstractmethod
    def __init__(self, dataspace_version: str, base_url: str, headers: dict = None,
                 trace: bool = False):
        """
        A base init method for services inheriting this class.

        Each service should implement its own init method, with at least the version and base_url parameters,
        both of which are needed to instantiate the controllers and services corresponding with that service's version.

        :param dataspace_version: The version of the service
        :param base_url: The base URL of the service
        :param headers: The headers to be used for requests to the service
        :param trace: Flag enabling the tracing of the requests sent to (and the
            responses received from) the external services (default: False). The
            collected trace is available through `get_trace()`/`get_trace_json()`,
            and `set_tracer()` shares it with other services
        """
        raise NotImplementedError

    @classmethod
    def builder(cls):
        """
        This method is intended to return a builder for services inheriting this class.
        This means that such a service should implement its own `_Builder` inner class.
        By default, the `Service._Builder` class is used.

        :return: a builder for the model inheriting this class
        """
        return cls._Builder(cls)

    class _Builder:
        """
        Default _Builder class for a Service.
        """

        def __init__(self, cls):
            self.cls = cls
            self._data = {}

        def dataspace_version(self, dataspace_version: str):
            self._data["dataspace_version"] = dataspace_version
            return self

        def base_url(self, base_url: dict):
            self._data["base_url"] = base_url
            return self

        def headers(self, headers: dict):
            self._data["headers"] = headers
            return self

        def trace(self, trace: bool):
            """
            Enables the tracing of the requests/responses of this service.
            """
            self._data["trace"] = trace
            return self

        def data(self, data: dict):
            """
            This method is intended to set all the data of the services inheriting this class.

            It can be used to set all the data of the service in a single call, without the need to declare
            each builder method separately. This is useful for cases where a service may deviate from its base
            service implementation, and the base service builder methods are not sufficient to set all the necessary data.
            """

            self._data.update(data)
            return self

        def build(self):
            """
            :return: an instance of the class inheriting the base service
            """
            return self.cls(**self._data)
