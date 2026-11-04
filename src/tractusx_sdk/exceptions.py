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

from typing import Any, Sequence

from requests import HTTPError


class TractusXSDKError(Exception):
    """Base class of every error raised intentionally by the SDK."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class ValidationError(TractusXSDKError, ValueError):
    """Input or data did not satisfy a validation rule."""


class _LegacyHTTPError(HTTPError):
    """
    Compatibility base for errors that used to be raised as ``requests.HTTPError``.

    ``ValueError`` ends the ``__init__`` chain before ``RequestException`` runs, so the
    attributes it would have set are given here as defaults (``e.response`` stays ``None``).
    """

    response = None
    request = None


class SubmodelValidationError(ValidationError, _LegacyHTTPError):
    """
    A submodel payload did not conform to its JSON schema.

    Also an ``HTTPError``: this is what the validation helpers used to raise, so
    callers that translate it to a ``422`` keep working.

    :param message: Summary of the failure.
    :param issues: One structured record per violation (``ValidationIssue`` instances),
        so callers can inspect them instead of parsing the message.
    """

    def __init__(self, message: str = "", issues: Sequence[Any] = ()) -> None:
        super().__init__(message)
        self.issues = tuple(issues)


class SchemaError(TractusXSDKError):
    """A schema could not be located, fetched or processed."""


class SchemaTranslationError(SchemaError):
    """A schema could not be translated (for example into a JSON-LD context)."""


class InvalidSemanticIdError(SchemaError, ValidationError, _LegacyHTTPError):
    """A semantic id does not follow the expected structure. Also an ``HTTPError``, as it used to be."""


class SchemaNotFoundError(SchemaError, _LegacyHTTPError):
    """The schema referenced by a semantic id could not be retrieved or parsed. Also an ``HTTPError``, as it used to be."""


class DiscoveryError(TractusXSDKError):
    """A discovery service (connector discovery, BPN discovery, ...) failed."""


class DiscoveryEndpointNotFoundError(DiscoveryError):
    """The discovery service did not list the endpoint that was looked for."""


class DiscoveryUnauthorizedError(DiscoveryError):
    """The discovery service refused the credentials that were used."""


class ConnectionManagerError(TractusXSDKError):
    """A connection manager could not store, load or reach its backend."""


class ConnectorError(TractusXSDKError, RuntimeError):
    """A call to an EDC connector failed."""


class CatalogError(ConnectorError):
    """A DCAT catalog could not be obtained, or it did not hold a usable offer."""


class EmptyCatalogError(CatalogError):
    """The catalog is missing, or the provider shared no dataset in it."""


class PolicyMismatchError(CatalogError, ValueError):
    """
    A catalog was read and no offer in it carried an acceptable policy.

    Still a ``ValueError``, so a caller that already catches one keeps working.
    What it adds is the evidence behind the verdict: the catalog that was read,
    the allow-list it was compared against and the evaluation of every rejected
    policy, so the caller can say which offers differed and how rather than
    repeating that nothing matched.

    :param message: What failed.
    :param catalog: The DCAT catalog the offers were taken from.
    :param allowed_policies: The allow-list they were compared against;
        ``None`` means no filtering was asked for and ``[]`` accepts nothing.
    :param evaluations: The ``PolicyEvaluation`` of each policy that was rejected.
    """

    def __init__(self, message: str = "", catalog: dict | None = None,
                 allowed_policies: list | None = None, evaluations: Sequence[Any] = ()) -> None:
        super().__init__(message)
        self.catalog = catalog
        self.allowed_policies = allowed_policies
        self.evaluations = tuple(evaluations)


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
