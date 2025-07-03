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
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################


import unittest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.responses import Response, JSONResponse
from io import BytesIO

from tractusx_sdk.dataspace.tools.http_tools import HttpTools

class TestHttpTools(unittest.TestCase):
    def setUp(self):
        """Set up shared test data."""
        self.test_url = "https://example.com/api/data"
        self.headers = {"Content-Type": "application/json"}
        self.payload = {"key": "value"}

    @patch("requests.get")
    def test_do_get_without_session_success(self, mock_get):
        """Test a successful GET request."""
        mock_get.return_value = Mock(status_code=200, json=lambda: {"message": "success"})
        
        response = HttpTools.do_get(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    @patch("requests.get")
    def test_do_get_without_session_failure(self, mock_get):
        """Test GET request when server returns an error."""
        mock_get.return_value = Mock(status_code=500, json=lambda: {"error": "Internal Server Error"})
        
        response = HttpTools.do_get(self.test_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "Internal Server Error"})

    @patch("requests.Session.get")
    def test_do_get_with_session_success(self, mock_get):
        """Test a successful GET request."""
        mock_get.return_value = Mock(status_code=200, json=lambda: {"message": "success"})
        
        response = HttpTools.do_get_with_session(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "success"})

    @patch("requests.Session.get")
    def test_do_get_with_session_failure(self, mock_get):
        """Test GET request when server returns an error."""
        mock_get.return_value = Mock(status_code=500, json=lambda: {"error": "Internal Server Error"})
        
        response = HttpTools.do_get_with_session(self.test_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "Internal Server Error"})

    @patch("requests.post")
    def test_do_post_without_session_success(self, mock_post):
        """Test a successful POST request."""
        mock_post.return_value = Mock(status_code=201, json=lambda: {"message": "created"})
        
        response = HttpTools.do_post(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"message": "created"})

    @patch("requests.post")
    def test_do_post_without_session_failure(self, mock_post):
        """Test POST request with bad request response."""
        mock_post.return_value = Mock(status_code=400, json=lambda: {"error": "Bad Request"})
        
        response = HttpTools.do_post(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Bad Request"})

    @patch("requests.Session.post")
    def test_do_post_with_session_success(self, mock_post):
        """Test a successful POST request."""
        mock_post.return_value = Mock(status_code=201, json=lambda: {"message": "created"})
        
        response = HttpTools.do_post_with_session(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"message": "created"})

    @patch("requests.Session.post")
    def test_do_post_with_session_failure(self, mock_post):
        """Test POST request with bad request response."""
        mock_post.return_value = Mock(status_code=400, json=lambda: {"error": "Bad Request"})
        
        response = HttpTools.do_post_with_session(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Bad Request"})

    @patch("requests.put")
    def test_do_put_without_session_success(self, mock_put):
        """Test a successful PUT request."""
        mock_put.return_value = Mock(status_code=200, json=lambda: {"message": "updated"})
        
        response = HttpTools.do_put(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "updated"})

    @patch("requests.put")
    def test_do_put_without_session_failure(self, mock_put):
        """Test PUT request with bad request response."""
        mock_put.return_value = Mock(status_code=400, json=lambda: {"error": "Bad Request"})
        
        response = HttpTools.do_put(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Bad Request"})

    @patch("requests.Session.put")
    def test_do_put_with_session_success(self, mock_put):
        """Test a successful PUT request."""
        mock_put.return_value = Mock(status_code=200, json=lambda: {"message": "updated"})
        
        response = HttpTools.do_put_with_session(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "updated"})

    @patch("requests.Session.put")
    def test_do_put_with_session_failure(self, mock_put):
        """Test PUT request with bad request response."""
        mock_put.return_value = Mock(status_code=400, json=lambda: {"error": "Bad Request"})
        
        response = HttpTools.do_put_with_session(self.test_url, json=self.payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Bad Request"})

    @patch("requests.delete")
    def test_do_delete_without_session_success(self, mock_delete):
        """Test a successful DELETE request."""
        mock_delete.return_value = Mock(status_code=204, json=lambda: {"message": "deleted"})
        
        response = HttpTools.do_delete(self.test_url)
        self.assertEqual(response.status_code, 204)

    @patch("requests.delete")
    def test_do_delete_without_session_failure(self, mock_delete):
        """Test DELETE request with not found response."""
        mock_delete.return_value = Mock(status_code=404, json=lambda: {"error": "Not Found"})
        
        response = HttpTools.do_delete(self.test_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Not Found"})

    @patch("requests.Session.delete")
    def test_do_delete_with_session_success(self, mock_delete):
        """Test a successful DELETE request."""
        mock_delete.return_value = Mock(status_code=204, json=lambda: {"message": "deleted"})
        
        response = HttpTools.do_delete_with_session(self.test_url)
        self.assertEqual(response.status_code, 204)

    @patch("requests.Session.delete")
    def test_do_delete_with_session_failure(self, mock_delete):
        """Test DELETE request with not found response."""
        mock_delete.return_value = Mock(status_code=404, json=lambda: {"error": "Not Found"})
        
        response = HttpTools.do_delete_with_session(self.test_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Not Found"})

    def test_response_json(self):
        """Ensure JSON response is properly structured."""
        response = HttpTools.json_response({"message": "OK"}, status_code=200)
        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 200)

    def test_concat_into_url(self):
        base_url = "https://example.com"
        path = "api/v1/resource"
        expected_url = "https://example.com/api/v1/resource"

        result = HttpTools.concat_into_url(base_url, path)
        self.assertEqual(expected_url, result)

    def test_concat_into_url_with_slashes(self):
        base_url = "https://example.com/"
        path = "/api/v1/resource/"
        expected_url = "https://example.com/api/v1/resource"

        result = HttpTools.concat_into_url(base_url, path)
        self.assertEqual(expected_url, result)

    def test_concat_into_url_with_empty_path(self):
        base_url = "https://example.com"
        path = ""
        expected_url = "https://example.com/"

        result = HttpTools.concat_into_url(base_url, path)
        self.assertEqual(expected_url, result)

    def test_empty_response(self):
        """Verify empty response creation."""
        response = HttpTools.empty_response(status=204)
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 204)

    def test_get_host(self):
        """Check if hostname extraction works."""
        self.assertEqual(HttpTools.get_host(self.test_url), "example.com")

    def test_explode_url(self):
        """Ensure URL parsing works as expected."""
        parsed_url = HttpTools.explode_url(self.test_url)
        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.netloc, "example.com")

    def test_join_path(self):
        """Verify URL path joining behaves correctly."""
        full_url = HttpTools.join_path("https://example.com/api/", "endpoint")
        self.assertEqual(full_url, "https://example.com/api/endpoint")

    def test_get_error_response(self):
        """Ensure error responses are properly structured."""
        response = HttpTools.get_error_response(500, "Server error")
        self.assertEqual(response.status_code, 500)

    def test_get_not_authorized(self):
        """Ensure unauthorized response returns correct status code."""
        response = HttpTools.get_not_authorized()
        self.assertEqual(response.status_code, 401)

    @patch("fastapi.Request.json", new_callable=AsyncMock)
    async def test_get_body(self, mock_json):
        """Check if request body can be retrieved asynchronously."""
        mock_json.return_value = self.payload
        mock_request = Mock()
        mock_request.json = mock_json

        body = await HttpTools.get_body(mock_request)
        self.assertEqual(body, self.payload)

    def test_file_response(self):
        """Test generating a file response."""
        buffer = BytesIO(b"sample pdf content")
        filename = "document.pdf"
        
        response = HttpTools.file_response(buffer, filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, b"sample pdf content")
        self.assertEqual(response.headers["Content-Disposition"], f'inline; filename="{filename}"')
        self.assertEqual(response.media_type, "application/pdf")

if __name__ == "__main__":
    unittest.main()
