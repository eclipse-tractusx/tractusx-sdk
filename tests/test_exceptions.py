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

import inspect

import pytest

from tractusx_sdk import exceptions
from tractusx_sdk.exceptions import (
    CatalogError,
    CatalogRequestError,
    ConnectionManagerError,
    ConnectorError,
    DiscoveryError,
    InvalidSemanticIdError,
    NegotiationError,
    SchemaError,
    SchemaNotFoundError,
    TractusXSDKError,
    TransferError,
    ValidationError,
)
from tractusx_sdk.extensions.notification_api import exceptions as extension_notification_exceptions
from tractusx_sdk.industry.services.notifications import exceptions as industry_notification_exceptions


def _sdk_error_classes(module):
    return [
        cls for _, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__ and issubclass(cls, Exception)
    ]


class TestHierarchy:

    def test_every_sdk_error_derives_from_the_base(self):
        classes = _sdk_error_classes(exceptions)
        assert TractusXSDKError in classes
        assert all(issubclass(cls, TractusXSDKError) for cls in classes)

    @pytest.mark.parametrize("module", [industry_notification_exceptions, extension_notification_exceptions])
    def test_notification_errors_derive_from_the_base(self, module):
        classes = _sdk_error_classes(module)
        assert len(classes) == 4
        assert all(issubclass(cls, TractusXSDKError) for cls in classes)

    @pytest.mark.parametrize("child, parent", [
        (InvalidSemanticIdError, SchemaError),
        (InvalidSemanticIdError, ValidationError),
        (SchemaNotFoundError, SchemaError),
        (CatalogError, ConnectorError),
        (CatalogRequestError, CatalogError),
        (NegotiationError, ConnectorError),
        (TransferError, ConnectorError),
    ])
    def test_specialisations(self, child, parent):
        assert issubclass(child, parent)

    @pytest.mark.parametrize("cls, builtin", [
        (ValidationError, ValueError),
        (InvalidSemanticIdError, ValueError),
        (CatalogRequestError, ConnectionError),
    ])
    def test_builtin_compatibility_is_kept(self, cls, builtin):
        with pytest.raises(builtin):
            raise cls("boom")

    @pytest.mark.parametrize("cls", [DiscoveryError, ConnectionManagerError, SchemaError, ConnectorError])
    def test_single_clause_catches_everything(self, cls):
        with pytest.raises(TractusXSDKError):
            raise cls("boom")


class TestPayload:

    def test_message_is_exposed_and_rendered(self):
        error = TractusXSDKError("it failed")
        assert error.message == "it failed"
        assert str(error) == "it failed"

    def test_catalog_request_error_carries_the_response(self):
        error = CatalogRequestError("no catalog", status_code=502, response_body="bad gateway")
        assert error.status_code == 502
        assert error.response_body == "bad gateway"
        assert str(error) == "no catalog"
        assert "bad gateway" not in str(error)

    def test_catalog_request_error_defaults_when_there_was_no_response(self):
        error = CatalogRequestError("no answer")
        assert error.status_code is None
        assert error.response_body is None

    def test_notification_error_keeps_its_message(self):
        error = industry_notification_exceptions.UnknownNotificationTypeError("X")
        assert error.notification_type == "X"
        assert error.message == "Unknown notification type: X"
