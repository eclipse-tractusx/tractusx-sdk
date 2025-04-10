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

from src.tractusx_sdk.dataspace.adapters.adapter import Adapter
from src.tractusx_sdk.dataspace.controllers.connector.decorators import controller_method
from src.tractusx_sdk.dataspace.controllers.controller import Controller

ENDPOINT_URL = "/some/endpoint"


def generic_controller_setup(obj) -> None:
    obj.adapter = Adapter("https://example.com")
    obj.endpoint_url = ENDPOINT_URL

    return obj


class SampleController(Controller):
    """
    A very basic, template-like class inheriting Controller
    """

    endpoint_url = ENDPOINT_URL

    @controller_method
    def func(self):
        return "Hello world!"


class ControllerPropertiesMixin:
    adapter = None
    endpoint_url = None
