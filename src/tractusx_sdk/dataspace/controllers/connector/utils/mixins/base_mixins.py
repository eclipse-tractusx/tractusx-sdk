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

from typing import Any, Generic, TypeVar
from urllib.parse import quote

import requests

from tractusx_sdk.dataspace.controllers.connector.utils.decorators import controller_method
from tractusx_sdk.dataspace.adapters.adapter import Adapter
from tractusx_sdk.dataspace.models.model import BaseModel
from tractusx_sdk.dataspace.models.connector.base_queryspec_model import BaseQuerySpecModel

# Model accepted by the write methods of a mixin; concrete controllers narrow it to their own model
ModelT = TypeVar("ModelT", bound=BaseModel)


def _id_path(endpoint_url: str, oid: object) -> str:
    """Build the URL of a single resource; the id is URL-encoded as one path segment."""
    if not isinstance(oid, str) or not oid.strip() or oid in (".", ".."):
        raise ValueError("A non-empty id other than '.' or '..' is required to build the resource URL")
    return f"{endpoint_url}/{quote(oid, safe='')}"


class CreateControllerMixin(Generic[ModelT]):
    """
    This mixin injects a method to allow "create" requests
    to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def create(self, obj: ModelT, **kwargs: Any) -> requests.Response:
        kwargs["data"] = obj.to_data()
        return self.adapter.post(url=self.endpoint_url, **kwargs)


class GetControllerMixin:
    """
    This mixin injects a method to allow "get by id" requests
    to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def get_by_id(self, oid: str, **kwargs: Any) -> requests.Response:
        return self.adapter.get(url=f"{self.endpoint_url}/{oid}", **kwargs)


class UpdateControllerMixin(Generic[ModelT]):
    """
    This mixin injects a method to allow "update" requests
    to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def update(self, obj: ModelT, **kwargs: Any) -> requests.Response:
        kwargs["data"] = obj.to_data()
        return self.adapter.put(url=self.endpoint_url, **kwargs)


class UpdateByIdControllerMixin(Generic[ModelT]):
    """
    This mixin injects a method to allow "update" requests
    to any class that inherits from the Controller class.
    It updates the resource at its own URL: PUT {endpoint}/{id}.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def update(self, obj: ModelT, **kwargs: Any) -> requests.Response:
        url = _id_path(self.endpoint_url, getattr(obj, "oid", None))
        kwargs["data"] = obj.to_data()
        return self.adapter.put(url=url, **kwargs)


class DeleteControllerMixin:
    """
    This mixin injects a method to allow "delete" requests
    to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def delete(self, oid: str, **kwargs: Any) -> requests.Response:
        return self.adapter.delete(url=f"{self.endpoint_url}/{oid}", **kwargs)


class QueryControllerMixin:
    """
    This mixin injects a method to allow "query" requests
    to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def query(self, obj: BaseQuerySpecModel | None = None, **kwargs: Any) -> requests.Response:
        if obj:
            kwargs["data"] = obj.to_data()

        return self.adapter.post(url=f"{self.endpoint_url}/request", **kwargs)


class GetAllControllerMixin(QueryControllerMixin):
    """
    This mixin injects a method to allow "query" requests without
    any filter to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def get_all(self, **kwargs: Any) -> requests.Response:
        return self.query(**kwargs)


class GetStateControllerMixin:
    """
    This mixin injects a method to allow "state" requests
    to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def get_state_by_id(self, oid: str, **kwargs: Any) -> requests.Response:
        return self.adapter.get(url=f"{self.endpoint_url}/{oid}/state", **kwargs)


class TerminateControllerMixin(Generic[ModelT]):
    """
    This mixin injects a method to allow "terminate" requests
    to any class that inherits from the Controller class.
    """

    adapter: Adapter
    endpoint_url: str

    @controller_method
    def terminate_by_id(self, oid: str, obj: ModelT, **kwargs: Any) -> requests.Response:
        kwargs["data"] = obj.to_data()
        return self.adapter.post(url=f"{self.endpoint_url}/{oid}/terminate", **kwargs)
