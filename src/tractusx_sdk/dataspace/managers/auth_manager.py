#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025,2026 LKS Next
# Copyright (c) 2025 CGI Deutschland B.V. & Co. KG
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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


## Authorization Managment from Eclipse Tractus-X Simple Wallet (Renamed to tools)
## Author: Mathias Brunkow Moser
## License: Apache License, Version 2.0
## Source: https://github.com/eclipse-tractusx/digital-product-pass/blob/main/dpp-verification/simple-wallet/utilities/httpUtils.py
## Abstracted from the static method is_authorized

import logging

from fastapi import Request
from .auth_manager_interface import AuthManagerInterface

from tractusx_sdk._logging_fields import log_extra

# Security: the configured API key and the key sent by the caller are never logged
logger = logging.getLogger(__name__)

class AuthManager(AuthManagerInterface):
    configured_api_key: str
    api_key_header: str
    auth_enabled: bool
    
    def __init__(self, configured_api_key:str="password", api_key_header:str = "X-Api-Key", auth_enabled:bool = False):
        self.configured_api_key = configured_api_key
        self.api_key_header = api_key_header
        self.auth_enabled = auth_enabled
        logger.debug("API key authentication %s", "enabled" if auth_enabled else "disabled")
    
    def is_authenticated(self, request: Request):
        
        if(not self.auth_enabled):
            logger.debug("API key authentication is disabled, the request is accepted")
            return True
        
        api_key_from_header = request.headers.get(self.api_key_header, None)
        if(api_key_from_header is None):
            logger.warning("Request rejected: the API key header is missing",
                           extra=log_extra(operation="auth.is_authenticated"))
            return False
        

        if(api_key_from_header == self.configured_api_key):
            logger.debug("Request authenticated with an API key", extra=log_extra(operation="auth.is_authenticated"))
            return True
        
        logger.warning("Request rejected: the API key does not match the configured one",
                       extra=log_extra(operation="auth.is_authenticated"))
        return False
    
    def add_auth_header(self, headers: dict={}) -> dict:
        if not self.auth_enabled:
            logger.error("An auth header was requested but the authentication is not enabled")
            raise RuntimeError("Authentication is not enabled. Cannot get auth headers.")
        auth_header = {self.api_key_header: self.configured_api_key}
        logger.debug("API key header added", extra=log_extra(operation="auth.add_auth_header"))
        return {**headers, **auth_header}
