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

"""The factories have no logging arguments: asking for one fails at once, naming the argument."""

import logging

import pytest

from tractusx_sdk.dataspace.services.connector import ServiceFactory

REMOVED = [
    {"verbose": True},
    {"verbose": False},
    {"debug": True},
    {"logger": logging.getLogger("removed")},
]

FACTORIES = [
    ("get_connector_consumer_service", "saturn"),
    ("get_connector_provider_service", "jupiter"),
    ("get_connector_service", "jupiter"),
]


@pytest.mark.parametrize("removed", REMOVED, ids=lambda r: next(iter(r)) + "=" + type(next(iter(r.values()))).__name__)
@pytest.mark.parametrize("method, version", FACTORIES)
def test_the_removed_arguments_raise_a_type_error(method, version, removed):
    factory = getattr(ServiceFactory, method)

    with pytest.raises(TypeError, match=next(iter(removed))):
        factory(dataspace_version=version, base_url="https://connector.example.com", dma_path="/management",
                headers={}, **removed)


@pytest.mark.parametrize("method, version", FACTORIES)
def test_the_factories_build_without_them(method, version):
    service = getattr(ServiceFactory, method)(
        dataspace_version=version, base_url="https://connector.example.com", dma_path="/management", headers={})

    assert service is not None
    assert not hasattr(service, "verbose")
    assert not hasattr(service, "debug")
    assert not hasattr(service, "logger")
