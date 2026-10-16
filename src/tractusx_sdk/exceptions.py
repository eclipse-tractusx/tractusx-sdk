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
Exception hierarchy of the Tractus-X SDK.

Every error the SDK raises on purpose derives from :class:`TractusXSDKError`, so
an application can handle all of them with a single ``except`` clause. Outcomes
are reported through exceptions and return values, never through log output:
logging is diagnostic only and must not be parsed by callers.

Where an SDK error replaces a builtin exception that callers may already be
catching (``ConnectionError``, ``ValueError``, ...), it also inherits from that
builtin, so existing ``except`` clauses keep working.
"""


class TractusXSDKError(Exception):
    """Base class of every error raised intentionally by the SDK."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class ValidationError(TractusXSDKError, ValueError):
    """Input or data did not satisfy a validation rule."""


class SchemaError(TractusXSDKError):
    """A schema could not be located, fetched or processed."""


class InvalidSemanticIdError(SchemaError, ValidationError):
    """A semantic id does not follow the expected structure."""


class SchemaNotFoundError(SchemaError):
    """The schema referenced by a semantic id could not be retrieved or parsed."""


class DiscoveryError(TractusXSDKError):
    """A discovery service (connector discovery, BPN discovery, ...) failed."""


class ConnectionManagerError(TractusXSDKError):
    """A connection manager could not store, load or reach its backend."""


class ConnectorError(TractusXSDKError):
    """A call to an EDC connector failed."""


class CatalogError(ConnectorError):
    """A DCAT catalog could not be obtained, or it did not hold a usable offer."""


class CatalogRequestError(CatalogError, ConnectionError):
    """
    The connector answered a catalog request with an error, or did not answer.

    :param message: What failed.
    :param status_code: HTTP status code of the response, ``None`` when there was none.
    :param response_body: Body of the response, kept here instead of in the message
        so it only reaches the caller that asks for it.
    """

    def __init__(self, message: str = "", status_code: int | None = None, response_body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class NegotiationError(ConnectorError):
    """A contract negotiation failed or was terminated."""


class TransferError(ConnectorError):
    """A transfer process failed or was terminated."""
