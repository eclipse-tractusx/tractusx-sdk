#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026
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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

import base64
import logging

logger = logging.getLogger(__name__)

def encode_as_base64_url_safe(string: str) -> str:
    """
    Encodes as a URL-safe Base64 UTF-8 string without padding.
    

    Args:
        string (str): The string to encode

    Returns:
        str: The URL-safe Base64 encoded string
    """
    # Convert to bytes, encode to base64, convert to URL-safe, remove padding
    encoded = (
        base64.urlsafe_b64encode(string.encode("utf-8")).decode("ascii").rstrip("=")
    )
    return encoded


def decode_base64_url_safe(encoded_string: str) -> str:
    """
    Decodes a URL-safe Base64 encoded string.
    
    This function handles the padding automatically.

    Args:
        encoded_string (str): The URL-safe Base64 encoded string to decode

    Returns:
        str: The decoded string
    """
    # Add padding if necessary
    padding = 4 - (len(encoded_string) % 4)
    if padding < 4:
        encoded_string += "=" * padding
    
    # Decode the string
    try:
        decoded = base64.urlsafe_b64decode(encoded_string.encode("ascii")).decode("utf-8")
    except Exception:
        # Only the length is logged: the content of the string is not
        logger.exception("A base64 string of %d characters could not be decoded", len(encoded_string))
        raise
    return decoded
