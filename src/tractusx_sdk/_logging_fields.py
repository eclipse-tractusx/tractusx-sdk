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
Helpers for the structured context (``extra=``) of the SDK log records.

The SDK never configures logging; these helpers only make sure that the records
it emits carry a stable, documented set of fields, and that nothing sensitive
ends up in them:

* :func:`log_extra` is the only way the SDK builds the ``extra`` of a record. Its
  keyword arguments are the complete list of fields, none of which collides with
  an attribute reserved by :class:`logging.LogRecord`.
* :func:`safe_url` removes everything of a URL that could carry a secret (user
  information, query string, fragment and path parameters).
* The control characters of the values (line breaks, escape sequences...) are
  escaped, so that a value that comes from a remote party cannot forge a log line.

Headers, tokens, credentials and bodies are never part of the fields.
"""

import re
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

_INVALID_URL = "<invalid-url>"
_PATH_PARAMETERS = re.compile(r";[^/]*")
_CONTROL_CHARACTERS = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")

# Fields holding a URL, which are sanitised before being attached to a record.
_URL_FIELDS = ("url", "counter_party_address")


def escape_control_characters(value: Any) -> Any:
    """
    Escapes the control characters of a string (a line break becomes a backslash and an ``n``), leaving any other
    value untouched. A string that comes from a remote party goes through it before it is written to a log.
    """
    if not isinstance(value, str):
        return value
    return _CONTROL_CHARACTERS.sub(lambda match: match.group().encode("unicode_escape").decode("ascii"), value)


def safe_url(url: Any) -> Optional[str]:
    """
    Returns the URL without the parts that could leak a secret.

    The user information (``user:password@``), the query string, the fragment and
    the path parameters (``;jsessionid=...``) are removed. Only the scheme, the
    host (and port) and the path are kept.

    :param url: The URL to sanitise (anything else than a string is converted)
    :return: The sanitised URL, or None when no URL was given
    """
    if url is None:
        return None

    try:
        parts = urlsplit(str(url))
    except ValueError:
        return _INVALID_URL

    host = parts.netloc.rpartition("@")[2]
    path = _PATH_PARAMETERS.sub("", parts.path)
    return escape_control_characters(urlunsplit((parts.scheme, host, path, "", "")))


def http_status(response: Any) -> Optional[int]:
    """
    Returns the status code of a response, or None when it does not carry a usable one.
    """
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) and not isinstance(status, bool) else None


def log_extra(
    *,  # NOSONAR
    asset_id: Optional[str] = None,
    aas_id: Optional[str] = None,
    submodel_id: Optional[str] = None,
    message_id: Optional[str] = None,
    bpn: Optional[str] = None,
    policy_id: Optional[str] = None,
    negotiation_id: Optional[str] = None,
    agreement_id: Optional[str] = None,
    transfer_id: Optional[str] = None,
    edr_id: Optional[str] = None,
    counter_party_id: Optional[str] = None,
    counter_party_address: Optional[str] = None,
    dataspace_version: Optional[str] = None,
    http_method: Optional[str] = None,
    url: Optional[str] = None,
    status_code: Optional[int] = None,
    elapsed_ms: Optional[float] = None,
    adapter_type: Optional[str] = None,
    schema_urn: Optional[str] = None,
    model: Optional[str] = None,
    operation: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Builds the ``extra`` argument of a log call.

    Fields that are None are left out, the URL fields are sanitised with
    :func:`safe_url` and the control characters of the strings are escaped. Usage::

        logger.debug("Fetching %s", name, extra=log_extra(asset_id=asset_id, bpn=bpn))
    """
    fields = {
        "asset_id": asset_id,
        "aas_id": aas_id,
        "submodel_id": submodel_id,
        "message_id": message_id,
        "bpn": bpn,
        "policy_id": policy_id,
        "negotiation_id": negotiation_id,
        "agreement_id": agreement_id,
        "transfer_id": transfer_id,
        "edr_id": edr_id,
        "counter_party_id": counter_party_id,
        "counter_party_address": counter_party_address,
        "dataspace_version": dataspace_version,
        "http_method": http_method,
        "url": url,
        "status_code": status_code,
        "elapsed_ms": elapsed_ms,
        "adapter_type": adapter_type,
        "schema_urn": schema_urn,
        "model": model,
        "operation": operation,
    }
    extra: Dict[str, Any] = {}
    for key, value in fields.items():
        if value is None:
            continue
        extra[key] = safe_url(value) if key in _URL_FIELDS else escape_control_characters(value)
    return extra


# The complete list of fields a log record of the SDK may carry
EXTRA_FIELDS = frozenset(log_extra.__kwdefaults__ or {})
