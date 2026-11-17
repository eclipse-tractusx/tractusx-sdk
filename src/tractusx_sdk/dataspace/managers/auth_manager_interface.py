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

from fastapi import Request

class AuthManagerInterface:
    """
    Interface for authentication managers in the Tractus-X SDK.
    Implementations should provide a method to return authentication headers.
    """

    def add_auth_header(self, headers: dict={}) -> dict:
        """
        Adds authentication information to the provided HTTP headers.

        Args:
            headers (dict, optional): A dictionary of existing HTTP headers to which authentication information will be added. Defaults to an empty dictionary.

        Returns:
            dict: The updated headers dictionary including authentication information.
        """
        raise NotImplementedError("add_auth_header must be implemented by subclasses")
    
    def is_authenticated(self, request: Request) -> bool:
        """
        Checks if the request is authenticated.
        Args:
            request (Request): The FastAPI request object to check for authentication.
        Returns:
            bool: True if the request is authenticated, False otherwise.
        """
        raise NotImplementedError("is_authenticated must be implemented by subclasses")
