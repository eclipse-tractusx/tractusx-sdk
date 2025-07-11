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


## HTTP Protocol Managment from Eclipse Tractus-X Simple Wallet (Renamed to tools)
## Author: Mathias Brunkow Moser
## License: Apache License, Version 2.0
## Source: https://github.com/eclipse-tractusx/digital-product-pass/blob/main/dpp-verification/simple-wallet/utilities/httpUtils.py
## Extended here for fastapi

import requests
from fastapi.responses import JSONResponse, Response
from io import BytesIO
import urllib.parse
class HttpTools:

    # do get request without session
    @staticmethod
    def do_get(url,verify=True,headers=None,timeout=None,params=None,allow_redirects=False):
        return requests.get(url=url,verify=verify,
                            timeout=timeout,headers=headers,
                            params=params,allow_redirects=allow_redirects)
    
    # do get request with session
    @staticmethod
    def do_get_with_session(url,session=None,verify=True,headers=None,timeout=None, params=None,allow_redirects=False):
        if session is None:
            session = requests.Session()
        return session.get(url=url,verify=verify,
                           timeout=timeout,headers=headers,
                           params=params,allow_redirects=allow_redirects)
    
    # do post request without session
    @staticmethod
    def do_post(url,data=None,verify=True,headers=None,timeout=None,json=None,allow_redirects=False):
        return requests.post(url=url,verify=verify,
                             timeout=timeout,headers=headers,
                             data=data,json=json,
                             allow_redirects=allow_redirects)
    
    # do post request with session
    @staticmethod
    def do_post_with_session(url,session=None,data=None,verify=True,headers=None,timeout=None,json=None,allow_redirects=False):
        if session is None:
            session = requests.Session()
        return session.post(url=url,verify=verify,
                            timeout=timeout,headers=headers,
                            data=data,json=json,
                            allow_redirects=allow_redirects)

    # do put request without session
    @staticmethod
    def do_put(url, data=None, verify=True, headers=None, timeout=None, json=None, allow_redirects=False):
        return requests.put(url=url, verify=verify,
                            timeout=timeout, headers=headers,
                            data=data, json=json,
                            allow_redirects=allow_redirects)

    # do put request with session
    @staticmethod
    def do_put_with_session(url, session=None, data=None, verify=True, headers=None, timeout=None, json=None, allow_redirects=False):
        if session is None:
            session = requests.Session()
        return session.put(url=url, verify=verify,
                           timeout=timeout, headers=headers,
                           data=data, json=json,
                           allow_redirects=allow_redirects)

    # do delete request without session
    @staticmethod
    def do_delete(url, verify=True, headers=None, timeout=None, params=None, allow_redirects=False):
        return requests.delete(url=url, verify=verify,
                               timeout=timeout, headers=headers,
                               params=params, allow_redirects=allow_redirects)

    # do delete request with session
    @staticmethod
    def do_delete_with_session(url, session=None, verify=True, headers=None, timeout=None, params=None, allow_redirects=False):
        if session is None:
            session = requests.Session()
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
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get('content-type', 'application/json')
        )
        
    
    @staticmethod
    def file_response(buffer: BytesIO, filename: str, status=200, content_type='application/pdf'):
        headers = {'Content-Disposition': f'inline; filename="{filename}"'}
        return Response(buffer.getvalue(), status_code=status,headers=headers, media_type=content_type)
    
    # Generates a error response with message
    @staticmethod
    def get_error_response(status=500,message="It was not possible to process/execute this request!"):
        return HttpTools.json_response({
            "message": message,
            "status": status 
        }, status)
    
    @staticmethod
    async def get_body(request):
        return await request.json()
    
    @staticmethod
    def get_not_authorized():
        return HttpTools.json_response({
            "message": "Not Authorized",
            "status": 401
        }, 401)
    
    @staticmethod
    def join_path(url, path):
        return urllib.parse.urljoin(base=url, url=path)
