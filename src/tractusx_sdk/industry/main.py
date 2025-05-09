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

from fastapi import FastAPI, Request

## Import FastAPI Router
from tractusx_sdk.industry.controllers import (
    checks_router
)

## FAST API example for keycloak
# from fastapi_keycloak_middleware import CheckPermissions
# from fastapi_keycloak_middleware import get_user

## Import Library Packeges
from tractusx_sdk.dataspace.tools import HttpTools, get_arguments

from tractusx_sdk.industry.config import (
    auth_manager,
    logger)

# Set up imports configuration
import uvicorn
import urllib3
urllib3.disable_warnings()

app = FastAPI(title="main")

app.include_router(checks_router, prefix="/api/check")

@app.get("/example")
async def api_call(request: Request):
    """
    Example documentation

    Returns:
        response: :obj:`__insert response here__`
    """
    try:
        ## Check if the api key is present and if it is authenticated
        if(not auth_manager.is_authenticated(request=request)):
            return HttpTools.get_not_authorized()
        
        ## Standard way to know if user is calling or the EDC.
        calling_bpn = request.headers.get('Edc-Bpn', None)
        if(calling_bpn is not None):
            logger.info(f"[Consumption Request] Incomming request from [{calling_bpn}] EDC Connector...")
        
        ## DO LOGIC HERE!!!
        return None
    
    except Exception as e:
        logger.exception(str(e))
        return HttpTools.get_error_response(
            status=500,
            message="It was not possible to execute the request!"
        )

def start():
    # Initialize the server environment and get the comand line arguments
    args = get_arguments()

    ## Once initial checks and configurations are done here is the place where it shall be included
    logger.info("[INIT] Application Startup Initialization Completed!")

    # Only start the Uvicorn server if not in test mode
    if not args.test_mode:
        uvicorn.run(app, host=args.host, port=args.port, log_level=("debug" if args.debug else "info"))      


if __name__ == "__main__":
    
    print("\nEclipse Tractus-X\n"+
        "    ____          __           __                _____ ____  __ __\n"+
        "   /  _/___  ____/ /_  _______/ /________  __   / ___// __ \\/ //_/\n"+
        "   / // __ \\/ __  / / / / ___/ __/ ___/ / / /   \\__ \\/ / / / ,<   \n"+
        " _/ // / / / /_/ / /_/ (__  ) /_/ /  / /_/ /   ___/ / /_/ / /| |  \n"+
        "/___/_/ /_/\\__,_/\\__,_/____/\\__/_/   \\__, /   /____/_____/_/ |_|  \n"+
        "                                    /____/                        \n"+
        "\n\n\t\t\t\t\t\t\t\t\t\tv0.0.5")

    print("Application starting, listening to requests...\n")
        
    start()

    print("\nClosing the application... Thank you for using the Eclipse Tractus-X Software Development KIT!")
