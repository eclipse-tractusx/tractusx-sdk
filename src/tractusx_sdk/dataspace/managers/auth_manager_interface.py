#################################################################################
# Tractus-X - Industry Flag Service
#
# Copyright (c) 2025 LKS NEXT
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

class AuthManagerInterface:
    """
    Interface for authentication managers in the Tractus-X SDK.
    Implementations should provide a method to return authentication headers.
    """

    def get_auth_headers(self) -> dict:
        """
        Returns a dictionary of authentication headers to be included in HTTP requests.

        Returns:
            dict: A dictionary containing authentication headers.
        """
        raise NotImplementedError("get_headers must be implemented by subclasses")
