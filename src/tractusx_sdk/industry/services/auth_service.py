#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

from abc import ABC, abstractmethod

class AuthService(ABC):
    """
    Abstract base class for authentication services.
    All authentication service implementations should inherit from this class.
    """
    
    @abstractmethod
    def get_token(self) -> str:
        """
        Get an authentication token.
        
        Returns:
            str: The authentication token
        """
        pass
    
    @abstractmethod
    def is_token_valid(self) -> bool:
        """
        Check if the current token is valid.
        
        Returns:
            bool: True if the token is valid, False otherwise
        """
        pass