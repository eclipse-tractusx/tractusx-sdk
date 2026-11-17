#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 LKS NEXT
# Copyright (c) 2025 CGI Deutschland B.V. & Co. KG
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


## Authorization Managment from Eclipse Tractus-X Simple Wallet (Renamed to tools)
## Author: Mathias Brunkow Moser
## License: Apache License, Version 2.0
## Source: https://github.com/eclipse-tractusx/digital-product-pass/blob/main/dpp-verification/simple-wallet/utilities/httpUtils.py
## Abstracted from the static method is_authorized

from fastapi import Request
from .auth_manager_interface import AuthManagerInterface

class AuthManager(AuthManagerInterface):
    configured_api_key: str
    api_key_header: str
    auth_enabled: bool
    
    def __init__(self, configured_api_key:str="password", api_key_header:str = "X-Api-Key", auth_enabled:bool = False):
        self.configured_api_key = configured_api_key
        self.api_key_header = api_key_header
        self.auth_enabled = auth_enabled
    
    def is_authenticated(self, request: Request):
        
        if(not self.auth_enabled):
            return True
        
        api_key_from_header = request.headers.get(self.api_key_header, None)
        if(api_key_from_header is None):
            return False
        

        if(api_key_from_header == self.configured_api_key):
            return True
        
        return False
    
    def add_auth_header(self, headers: dict={}) -> dict:
        if not self.auth_enabled:
            raise RuntimeError("Authentication is not enabled. Cannot get auth headers.")
        auth_header = {self.api_key_header: self.configured_api_key}
        return {**headers, **auth_header}
