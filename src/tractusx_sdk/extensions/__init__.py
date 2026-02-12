#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS NEXT
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
Tractus-X SDK Extensions.

This module contains extensions for the Tractus-X SDK, including:
- notification_api: Industry Core Notifications services and models
- semantics: Schema to context translation utilities
"""

__version__ = '0.6.2'
__author__ = 'Eclipse Tractus-X Contributors'
__license__ = "Apache License, Version 2.0"

# Notification API Extension
from .notification_api import (
    # Models
    NotificationHeader,
    NotificationContent,
    Notification,
    # Services
    NotificationService,
    # Exceptions
    NotificationError,
    NotificationValidationError,
    NotificationParsingError,
    UnknownNotificationTypeError,
)

__all__ = [
    # Notification API Models
    "NotificationHeader",
    "NotificationContent",
    "Notification",
    # Notification API Services
    "NotificationService",
    # Notification API Exceptions
    "NotificationError",
    "NotificationValidationError",
    "NotificationParsingError",
    "UnknownNotificationTypeError",
]
