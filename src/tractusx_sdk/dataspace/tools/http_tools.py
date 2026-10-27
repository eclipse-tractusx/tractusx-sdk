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

import functools
import logging
import time
import urllib.parse
from io import BytesIO

import requests
from fastapi.responses import JSONResponse, Response

from tractusx_sdk._logging_fields import http_status, log_extra, safe_url

from .tracing import traced_http

logger = logging.getLogger(__name__)


def _resolve_session(session):
    """Returns the given session, or a one-off one when the caller did not provide it."""
    if session is None:
        logger.debug("No session provided, using a new requests.Session for this request")
        return requests.Session()
    return session


def _logged_http(method: str):
    """
    Logs the request line (method and URL, without query string) and the outcome of an HTTP helper.

    Headers, parameters and bodies are never logged. A response is logged at DEBUG, or at
    WARNING when the server failed (5xx): client errors (4xx) are an expected outcome for
    many callers, which are the ones that decide whether they matter. An exception raised
    by the call is logged with its traceback before being re-raised unchanged.

    :param method: The HTTP method performed by the decorated function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            url = safe_url(kwargs["url"] if "url" in kwargs else (args[0] if args else None))
            logger.debug("HTTP %s %s", method, url, extra=log_extra(http_method=method, url=url))

            started = time.perf_counter()
            try:
                response = func(*args, **kwargs)
            except Exception:
                elapsed_ms = (time.perf_counter() - started) * 1000
                logger.exception(
                    "HTTP %s %s failed after %.0f ms", method, url, elapsed_ms,
                    extra=log_extra(http_method=method, url=url, elapsed_ms=round(elapsed_ms)),
                )
                raise

            elapsed_ms = (time.perf_counter() - started) * 1000
            status = http_status(response)
            level = logging.WARNING if status is not None and status >= 500 else logging.DEBUG
            logger.log(
                level, "HTTP %s %s -> %s in %.0f ms", method, url, status, elapsed_ms,
                extra=log_extra(http_method=method, url=url, status_code=status, elapsed_ms=round(elapsed_ms)),
            )
            return response

        return wrapper

    return decorator


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
    @_logged_http("GET")
    def do_get(url,verify=True,headers=None,timeout=None,params=None,allow_redirects=False):
        return requests.get(url=url,verify=verify,
                            timeout=timeout,headers=headers,
                            params=params,allow_redirects=allow_redirects)
    
    # do get request with session
    @staticmethod
    @traced_http("GET")
    @_logged_http("GET")
    def do_get_with_session(url,session=None,verify=True,headers=None,timeout=None, params=None,allow_redirects=False):
        session = _resolve_session(session)
        return session.get(url=url,verify=verify,
                           timeout=timeout,headers=headers,
                           params=params,allow_redirects=allow_redirects)
    
    # do post request without session
    @staticmethod
    @traced_http("POST")
    @_logged_http("POST")
    def do_post(url,data=None,verify=True,headers=None,timeout=None,json=None,allow_redirects=False):
        return requests.post(url=url,verify=verify,
                             timeout=timeout,headers=headers,
                             data=data,json=json,
                             allow_redirects=allow_redirects)
    
    # do post request with session
    @staticmethod
    @traced_http("POST")
    @_logged_http("POST")
    def do_post_with_session(url,session=None,data=None,verify=True,headers=None,timeout=None,json=None,allow_redirects=False):
        session = _resolve_session(session)
        return session.post(url=url,verify=verify,
                            timeout=timeout,headers=headers,
                            data=data,json=json,
                            allow_redirects=allow_redirects)

    # do put request without session
    @staticmethod
    @traced_http("PUT")
    @_logged_http("PUT")
    def do_put(url, data=None, verify=True, headers=None, timeout=None, json=None, allow_redirects=False):
        return requests.put(url=url, verify=verify,
                            timeout=timeout, headers=headers,
                            data=data, json=json,
                            allow_redirects=allow_redirects)

    # do put request with session
    @staticmethod
    @traced_http("PUT")
    @_logged_http("PUT")
    def do_put_with_session(url, session=None, data=None, verify=True, headers=None, timeout=None, json=None, allow_redirects=False):
        session = _resolve_session(session)
        return session.put(url=url, verify=verify,
                           timeout=timeout, headers=headers,
                           data=data, json=json,
                           allow_redirects=allow_redirects)

    # do delete request without session
    @staticmethod
    @traced_http("DELETE")
    @_logged_http("DELETE")
    def do_delete(url, verify=True, headers=None, timeout=None, params=None, allow_redirects=False):
        return requests.delete(url=url, verify=verify,
                               timeout=timeout, headers=headers,
                               params=params, allow_redirects=allow_redirects)

    # do delete request with session
    @staticmethod
    @traced_http("DELETE")
    @_logged_http("DELETE")
    def do_delete_with_session(url, session=None, verify=True, headers=None, timeout=None, params=None, allow_redirects=False):
        session = _resolve_session(session)
        return session.delete(url=url, verify=verify,
                              timeout=timeout, headers=headers,
                              params=params, allow_redirects=allow_redirects)

    # prepare response
    @staticmethod
    def json_response(data, status_code: int = 200, headers: dict = None):
        response = JSONResponse(
            content=data,
            status_code=status_code,
            headers=headers
        )
        response.headers["Content-Type"] = 'application/json'
        return response

    @staticmethod
    def concat_into_url(*args):
        """
        Joins given arguments into an url. Trailing and leading slashes are stripped for each argument.

        :param args: The parts of a URL to be concatenated into one
        :return: Complete URL
        """

        return "/".join(map(lambda x: str(x).strip("/"), args))
    
    @staticmethod
    def get_host(url):
        return HttpTools.explode_url(url=url).netloc
    
    @staticmethod 
    def explode_url(url):
        return urllib.parse.urlparse(url=url)    

    @staticmethod
    def empty_response(status=204):
        return Response(status_code=status)
    
    @staticmethod
    def proxy(response: requests.Response) -> Response:
        media_type = response.headers.get('content-type')
        if media_type is None:
            logger.debug("The proxied response has no content-type, defaulting to application/json")
            media_type = 'application/json'
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=media_type
        )
        
    
    @staticmethod
    def file_response(buffer: BytesIO, filename: str, status=200, content_type='application/pdf'):
        headers = {'Content-Disposition': f'inline; filename="{filename}"'}
        return Response(buffer.getvalue(), status_code=status,headers=headers, media_type=content_type)
    
    # Generates a error response with message
    @staticmethod
    def get_error_response(status=500,message="It was not possible to process/execute this request!"):
        logger.debug("Building an error response with status %s", status, extra=log_extra(status_code=status))
        return HttpTools.json_response({
            "message": message,
            "status": status 
        }, status)
    
    @staticmethod
    async def get_body(request):
        return await request.json()
    
    @staticmethod
    def get_not_authorized():
        logger.debug("Building a not authorized (401) response", extra=log_extra(status_code=401))
        return HttpTools.json_response({
            "message": "Not Authorized",
            "status": 401
        }, 401)
    
    @staticmethod
    def join_path(url, path):
        return urllib.parse.urljoin(base=url, url=path)
