#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
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


## HTTP Protocol Managment from Eclipse Tractus-X Simple Wallet (Renamed to tools)
## Author: Mathias Brunkow Moser
## License: Apache License, Version 2.0
## Source: https://github.com/eclipse-tractusx/digital-product-pass/blob/main/dpp-verification/simple-wallet/utilities/httpUtils.py
## Extended here for fastapi

import requests
from typing import Any
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from io import BytesIO
import urllib.parse

from .tracing import traced_http


class HttpTools:
    """
    HTTP helpers used by the SDK services.

    Every request method below is instrumented for tracing: they accept the
    optional `tracer` and `trace_context` keyword arguments, and record the
    request/response pair whenever a tracer is active. When tracing is off,
    the calls behave exactly as before, without any additional processing.
    """

    # do get request without session
    @staticmethod
    @traced_http("GET")
    def do_get(url: str, verify: bool = True, headers: dict | None = None, timeout: float | None = None,
               params: dict | None = None, allow_redirects: bool = False) -> requests.Response:
        return requests.get(url=url,verify=verify,
                            timeout=timeout,headers=headers,
                            params=params,allow_redirects=allow_redirects)
    
    # do get request with session
    @staticmethod
    @traced_http("GET")
    def do_get_with_session(url: str, session: requests.Session | None = None, verify: bool = True,
                            headers: dict | None = None, timeout: float | None = None,
                            params: dict | None = None, allow_redirects: bool = False) -> requests.Response:
        if session is None:
            session = requests.Session()
        return session.get(url=url,verify=verify,
                           timeout=timeout,headers=headers,
                           params=params,allow_redirects=allow_redirects)
    
    # do post request without session
    @staticmethod
    @traced_http("POST")
    def do_post(url: str, data: Any = None, verify: bool = True, headers: dict | None = None,
                timeout: float | None = None, json: Any = None, allow_redirects: bool = False) -> requests.Response:
        return requests.post(url=url,verify=verify,
                             timeout=timeout,headers=headers,
                             data=data,json=json,
                             allow_redirects=allow_redirects)
    
    # do post request with session
    @staticmethod
    @traced_http("POST")
    def do_post_with_session(url: str, session: requests.Session | None = None, data: Any = None, verify: bool = True,
                             headers: dict | None = None, timeout: float | None = None, json: Any = None,
                             allow_redirects: bool = False) -> requests.Response:
        if session is None:
            session = requests.Session()
        return session.post(url=url,verify=verify,
                            timeout=timeout,headers=headers,
                            data=data,json=json,
                            allow_redirects=allow_redirects)

    # do put request without session
    @staticmethod
    @traced_http("PUT")
    def do_put(url: str, data: Any = None, verify: bool = True, headers: dict | None = None,
               timeout: float | None = None, json: Any = None, allow_redirects: bool = False) -> requests.Response:
        return requests.put(url=url, verify=verify,
                            timeout=timeout, headers=headers,
                            data=data, json=json,
                            allow_redirects=allow_redirects)

    # do put request with session
    @staticmethod
    @traced_http("PUT")
    def do_put_with_session(url: str, session: requests.Session | None = None, data: Any = None, verify: bool = True,
                            headers: dict | None = None, timeout: float | None = None, json: Any = None,
                            allow_redirects: bool = False) -> requests.Response:
        if session is None:
            session = requests.Session()
        return session.put(url=url, verify=verify,
                           timeout=timeout, headers=headers,
                           data=data, json=json,
                           allow_redirects=allow_redirects)

    # do delete request without session
    @staticmethod
    @traced_http("DELETE")
    def do_delete(url: str, verify: bool = True, headers: dict | None = None, timeout: float | None = None,
                  params: dict | None = None, allow_redirects: bool = False) -> requests.Response:
        return requests.delete(url=url, verify=verify,
                               timeout=timeout, headers=headers,
                               params=params, allow_redirects=allow_redirects)

    # do delete request with session
    @staticmethod
    @traced_http("DELETE")
    def do_delete_with_session(url: str, session: requests.Session | None = None, verify: bool = True,
                               headers: dict | None = None, timeout: float | None = None,
                               params: dict | None = None, allow_redirects: bool = False) -> requests.Response:
        if session is None:
            session = requests.Session()
        return session.delete(url=url, verify=verify,
                              timeout=timeout, headers=headers,
                              params=params, allow_redirects=allow_redirects)

    # prepare response
    @staticmethod
    def json_response(data: Any, status_code: int = 200, headers: dict | None = None) -> JSONResponse:
        response = JSONResponse(
            content=data,
            status_code=status_code,
            headers=headers
        )
        response.headers["Content-Type"] = 'application/json'
        return response

    @staticmethod
    def concat_into_url(*args: Any) -> str:
        """
        Joins given arguments into an url. Trailing and leading slashes are stripped for each argument.

        :param args: The parts of a URL to be concatenated into one
        :return: Complete URL
        """

        return "/".join(map(lambda x: str(x).strip("/"), args))
    
    @staticmethod
    def get_host(url: str) -> str:
        return HttpTools.explode_url(url=url).netloc
    
    @staticmethod 
    def explode_url(url: str) -> urllib.parse.ParseResult:
        return urllib.parse.urlparse(url=url)    

    @staticmethod
    def empty_response(status: int = 204) -> Response:
        return Response(status_code=status)
    
    @staticmethod
    def proxy(response: requests.Response) -> Response:
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get('content-type', 'application/json')
        )
        
    
    @staticmethod
    def file_response(buffer: BytesIO, filename: str, status: int = 200, content_type: str = 'application/pdf') -> Response:
        headers = {'Content-Disposition': f'inline; filename="{filename}"'}
        return Response(buffer.getvalue(), status_code=status,headers=headers, media_type=content_type)
    
    # Generates a error response with message
    @staticmethod
    def get_error_response(status: int = 500,message: str = "It was not possible to process/execute this request!") -> JSONResponse:
        return HttpTools.json_response({
            "message": message,
            "status": status 
        }, status)
    
    @staticmethod
    async def get_body(request: Request) -> Any:
        return await request.json()
    
    @staticmethod
    def get_not_authorized() -> JSONResponse:
        return HttpTools.json_response({
            "message": "Not Authorized",
            "status": 401
        }, 401)
    
    @staticmethod
    def join_path(url: str, path: str) -> str:
        return urllib.parse.urljoin(base=url, url=path)
