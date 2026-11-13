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
Private helpers shared by the modules of the SDK that log a failure.

They are not part of the public API.
"""

import logging
from typing import Any

from tractusx_sdk._logging_fields import log_extra


def log_failure(
    logger: logging.Logger,
    message: str,
    error: BaseException,
    *args: Any,
    level: int = logging.ERROR,
    **fields: Any,
) -> None:
    """
    Logs a failure by the TYPE of its exception, never its message nor its traceback.

    The message and the traceback of a ``requests``/``httpx`` error quote the full URL, query string included,
    and a remote service may echo the request in them, so neither is ever logged. The record points at the line of
    the caller, and ``fields`` are the documented fields of :func:`~tractusx_sdk._logging_fields.log_extra`.

    :param logger: The logger of the calling module
    :param message: A lazy ``%`` format. It must end with the placeholder of the exception type, which is filled last
    :param error: The exception that was caught
    :param args: The arguments of ``message``, without the exception type
    :param level: The level of the record (ERROR by default)
    """
    logger.log(level, message, *args, type(error).__name__, extra=log_extra(**fields), stacklevel=2)
