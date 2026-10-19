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

Headers, tokens, credentials and bodies are never part of the fields.
"""

import re
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

_INVALID_URL = "<invalid-url>"
_PATH_PARAMETERS = re.compile(r";[^/]*")

# Fields holding a URL, which are sanitised before being attached to a record.
_URL_FIELDS = ("url", "counter_party_address")


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
    return urlunsplit((parts.scheme, host, path, "", ""))


def http_status(response: Any) -> Optional[int]:
    """
    Returns the status code of a response, or None when it does not carry a usable one.
    """
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) and not isinstance(status, bool) else None


def log_extra(
    *,
    asset_id: Optional[str] = None,
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

    Fields that are None are left out, and the URL fields are sanitised with
    :func:`safe_url`. Usage::

        logger.debug("Fetching %s", name, extra=log_extra(asset_id=asset_id, bpn=bpn))
    """
    values = dict(locals())  # the arguments only: nothing else is defined yet
    fields = {key: value for key, value in values.items() if value is not None}
    for name in _URL_FIELDS:
        if name in fields:
            fields[name] = safe_url(fields[name])
    return fields


# The complete list of fields a log record of the SDK may carry
EXTRA_FIELDS = frozenset(log_extra.__kwdefaults__)
