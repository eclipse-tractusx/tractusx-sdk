#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 DRÄXLMAIER Group
# (represented by Lisa Dräxlmaier GmbH)
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

from typing import Dict, Any, Mapping, Optional
from uuid import UUID
from urllib.parse import quote
import httpx

from tractusx_sdk.industry.adapters import SubmodelAdapter

class HttpSubmodelAdapter(SubmodelAdapter):
    """
    HTTP adapter for external submodel services.
    
    This adapter connects to external ICHub-compatible services that expose
    submodels via REST API. It implements the SubmodelAdapter interface from
    the Tractus-X SDK to provide seamless integration.
    
    The adapter uses key/value based submodel metadata for all operations.
    """

    @classmethod
    def builder(cls):
        return cls._Builder(cls)

    class _Builder:
        def __init__(self, cls):
            self.cls = cls
            self._data = {}

        def base_url(self, base_url: str):
            self._data["base_url"] = base_url
            return self

        def api_path(self, api_path: str):
            self._data["api_path"] = api_path
            return self

        def url_pattern(self, url_pattern: str):
            self._data["url_pattern"] = url_pattern
            return self

        def auth_type(self, auth_type: str):
            self._data["auth_type"] = auth_type
            return self

        def auth_token(self, auth_token: Optional[str]):
            self._data["auth_token"] = auth_token
            return self

        def auth_key_name(self, auth_key_name: Optional[str]):
            self._data["auth_key_name"] = auth_key_name
            return self

        def timeout(self, timeout: int):
            self._data["timeout"] = timeout
            return self

        def verify_ssl(self, verify_ssl: bool):
            self._data["verify_ssl"] = verify_ssl
            return self

        def build(self):
            if "base_url" not in self._data:
                raise ValueError("Missing required builder parameter: base_url")
            return self.cls(**self._data)
    
    def __init__(
        self,
        base_url: str,
        api_path: str = "",
        url_pattern: str | None = None,
        auth_type: str = "apikey",
        auth_token: Optional[str] = None,
        auth_key_name: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize the HTTP submodel adapter.
        
        Args:
            base_url: Base URL of the external submodel service (e.g., "https://external-ichub.com")
            api_path: Optional API path prefix (e.g., "/api/v1")
            url_pattern: Optional URL pattern used to resolve the target endpoint from
                submodel metadata. Defaults to "{base_url}{api_path}/{semantic_id}/{submodel_id}/submodel".
            auth_type: Authentication type - "bearer" or "apikey" (default: "apikey")
            auth_token: Authentication token/key value
            auth_key_name: Header name for API key (e.g., "X-Api-Key"), required when auth_type="apikey"
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.api_path = api_path.rstrip('/') if api_path else ""
        self.url_pattern = url_pattern or "{base_url}{api_path}/{semantic_id}/{submodel_id}/submodel"
        self.auth_type = auth_type.lower()
        self.auth_token = auth_token
        self.auth_key_name = auth_key_name
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Validate authentication configuration
        if self.auth_type not in ["bearer", "apikey", "none"]:
            raise ValueError(
                f"Invalid auth_type: {self.auth_type}. "
                f"Supported types: 'bearer', 'apikey', 'none'"
            )
        
        if self.auth_type == "apikey" and not self.auth_key_name:
            raise ValueError(
                "auth_key_name is required when auth_type='apikey'"
            )
        
        # Initialize HTTP client
        self.client = httpx.Client(
            timeout=timeout,
            verify=verify_ssl,
            follow_redirects=True
        )

        if not isinstance(self.url_pattern, str) or not self.url_pattern.strip():
            raise ValueError("url_pattern must be a non-empty string")

    def _build_url(self, submodel_metadata: Mapping[str, Any]) -> str:
        """
        Build the full URL for submodel operations from metadata and a URL pattern.
        """
        if not isinstance(submodel_metadata, Mapping):
            raise TypeError("submodel_metadata must be a mapping")

        encoded_metadata: dict[str, str] = {
            "base_url": self.base_url,
            "api_path": self.api_path,
        }

        for key, value in submodel_metadata.items():
            if isinstance(value, UUID):
                encoded_metadata[key] = quote(str(value), safe="")
            elif isinstance(value, str):
                if not value.strip():
                    raise ValueError(f"submodel_metadata['{key}'] must be a non-empty string")
                encoded_metadata[key] = quote(value, safe="")
            else:
                raise TypeError(
                    f"submodel_metadata['{key}'] must be a string or UUID"
                )

        try:
            return self.url_pattern.format(**encoded_metadata)
        except KeyError as key_error:
            raise KeyError(
                f"Missing required URL key '{key_error.args[0]}' for pattern '{self.url_pattern}'"
            ) from key_error
    
    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Build HTTP headers including authentication if configured."""
        headers = {
            "Content-Type": content_type,
            "Accept": "application/json"
        }
        
        if self.auth_token:
            if self.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.auth_token}"
            elif self.auth_type == "apikey" and self.auth_key_name:
                headers[self.auth_key_name] = self.auth_token
        
        return headers
    
    def _handle_response(self, response: httpx.Response, operation: str) -> Any:
        """
        Handle HTTP response and map status codes to appropriate exceptions.
        
        Args:
            response: HTTP response object
            operation: Operation name for logging (e.g., "read", "write", "delete")
            
        Returns:
            Response JSON content if applicable
            
        Raises:
            FileNotFoundError: For 404 responses
            ValueError: For 400, 422 responses
            PermissionError: For 401, 403 responses
            RuntimeError: For 5xx server errors
        """
        status = response.status_code
        
        # Success cases
        if status in (200, 201, 204):
            if status == 204 or not response.content:
                return None
            try:
                return response.json()
            except Exception:
                return None
        
        # Error cases
        error_msg = f"HTTP {operation} failed with status {status}"
        try:
            error_detail = response.json()
            error_msg += f": {error_detail}"
        except Exception:
            error_msg += f": {response.text[:200]}"
        
        if status == 404:
            raise FileNotFoundError(f"Submodel not found: {error_msg}")
        elif status in (400, 422):
            raise ValueError(f"Invalid request: {error_msg}")
        elif status in (401, 403):
            raise PermissionError(f"Authentication/Authorization failed: {error_msg}")
        elif status >= 500:
            raise RuntimeError(f"Server error: {error_msg}. Please retry later.")
        else:
            raise RuntimeError(f"Unexpected error: {error_msg}")

    def read(self, submodel_metadata: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Retrieve a submodel from the external service.
        """
        url = self._build_url(submodel_metadata)

        try:
            response = self.client.get(url, headers=self._get_headers())
            return self._handle_response(response, "GET")
        except httpx.RequestError as request_error:
            raise ConnectionError(f"Connection error while reading submodel: {request_error}") from request_error

    def write(self, submodel_metadata: Mapping[str, Any], content: bytes) -> None:
        """
        Upload/create a submodel in the external service using raw bytes.
        """
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")

        url = self._build_url(submodel_metadata)

        try:
            response = self.client.post(
                url,
                content=content,
                headers=self._get_headers(content_type="application/octet-stream")
            )
            self._handle_response(response, "POST")
        except httpx.RequestError as request_error:
            raise ConnectionError(f"Connection error while writing submodel: {request_error}") from request_error

    def write_json(self, submodel_metadata: Mapping[str, Any], content: Mapping[str, Any] | None) -> None:
        """
        Upload/create a submodel in the external service using a JSON body.
        """
        if content is not None and not isinstance(content, Mapping):
            raise TypeError("content must be a mapping or None")

        url = self._build_url(submodel_metadata)

        try:
            response = self.client.post(
                url,
                json=content,
                headers=self._get_headers(content_type="application/json")
            )
            self._handle_response(response, "POST")
        except httpx.RequestError as request_error:
            raise ConnectionError(f"Connection error while writing submodel JSON: {request_error}") from request_error

    def delete(self, submodel_metadata: Mapping[str, Any]) -> None:
        """
        Delete a submodel from the external service.
        """
        url = self._build_url(submodel_metadata)

        try:
            response = self.client.delete(url, headers=self._get_headers())
            self._handle_response(response, "DELETE")
        except httpx.RequestError as request_error:
            raise ConnectionError(f"Connection error while deleting submodel: {request_error}") from request_error

    def exists(self, submodel_metadata: Mapping[str, Any]) -> bool:
        """
        Check if a submodel exists in the external service.
        """
        url = self._build_url(submodel_metadata)

        try:
            response = self.client.head(url, headers=self._get_headers())
            if response.status_code == 404:
                return False
            self._handle_response(response, "HEAD")
            return True
        except httpx.RequestError as request_error:
            raise ConnectionError(f"Connection error while checking submodel existence: {request_error}") from request_error

    def __del__(self):
        """Cleanup HTTP client on adapter destruction."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except Exception:
            pass
