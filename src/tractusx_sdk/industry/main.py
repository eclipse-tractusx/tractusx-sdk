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


from datetime import datetime
import sys

# Set up imports configuration
import argparse
import logging.config
import logging
import yaml
import uvicorn
import urllib3
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

## FAST API example for keycloak
from fastapi_keycloak_middleware import CheckPermissions
from fastapi_keycloak_middleware import get_user

## Import paths
sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True


## Import Library Packeges
from tractusx_sdk.dataspace.tools import op, HttpTools
from tractusx_sdk.dataspace.managers import AuthManager
from tractusx_sdk.dataspace.services import EdcService
from tractusx_sdk.industry.services import AasService

## Declare Global Variables
app_configuration:dict
log_config:dict

## In memory storage/management services
edc_service: EdcService

## In memory authentication manager service
auth_manager: AuthManager

urllib3.disable_warnings()
logging.captureWarnings(True)

## Create Loggin Folder
op.make_dir("logs")

# Get the absolute path of the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_LOG_PATH = os.path.join(BASE_DIR, "config", "logging.yml")
CONFIG_CONFIG_PATH = os.path.join(BASE_DIR, "config", "configuration.yml")

# Load the logging config file
with open(CONFIG_LOG_PATH, 'rt') as f:
    # Read the yaml configuration
    log_config = yaml.safe_load(f.read())
    # Set logging filename with datetime
    date = op.get_filedate()
    op.make_dir(dir_name="logs/"+date)
    log_config["handlers"]["file"]["filename"] = f'logs/{date}/{op.get_filedatetime()}-industry-sdk.log'
    logging.config.dictConfig(log_config)

# Load the configuation for the application
with open(CONFIG_CONFIG_PATH, 'rt') as f:
    # Read the yaml configuration
    app_configuration = yaml.safe_load(f.read())

app = FastAPI(title="main")

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
    ## Load in memory data storages and authentication manager
    global edc_service, auth_manager, logger
    
    args = get_arguments()
    logger = logging.getLogger('staging')
    if(args.debug):
        logger = logging.getLogger('development')
        
    ## Start storage and edc communication service
    edc_service = EdcService()

    ## Start the authentication manager
    auth_manager = AuthManager()
    
    ## Once initial checks and configurations are done here is the place where it shall be included
    logger.info("[INIT] Application Startup Initialization Completed!")

    # Only start the Uvicorn server if not in test mode
    if not args.test_mode:
        uvicorn.run(app, host=args.host, port=args.port, log_level=("debug" if args.debug else "info"))      
    
def get_arguments():
    
    parser = argparse.ArgumentParser()

    parser.add_argument('--test-mode', action='store_true', help="Run in test mode (skips uvicorn.run())", required=False)
        
    parser.add_argument("--debug", default=False, action="store_false", help="Enable and disable the debug", required=False)
    
    parser.add_argument("--port", default=7000, help="The server port where it will be available", type=int, required=False,)
    
    parser.add_argument("--host", default="localhost", help="The server host where it will be available", type=str, required=False)
    
    args, unknown = parser.parse_known_args()
    return args


if __name__ == "__main__":
    
    print("\nEclipse Tractus-X\n"+
        "    ____          __           __                _____ ____  __ __\n"+
        "   /  _/___  ____/ /_  _______/ /________  __   / ___// __ \\/ //_/\n"+
        "   / // __ \\/ __  / / / / ___/ __/ ___/ / / /   \\__ \\/ / / / ,<   \n"+
        " _/ // / / / /_/ / /_/ (__  ) /_/ /  / /_/ /   ___/ / /_/ / /| |  \n"+
        "/___/_/ /_/\\__,_/\\__,_/____/\\__/_/   \\__, /   /____/_____/_/ |_|  \n"+
        "                                    /____/                        \n"+
        "\n\n\t\t\t\t\t\t\t\t\t\tv0.0.1")

    print("Application starting, listening to requests...\n")
        
    start()

    print("\nClosing the application... Thank you for using the Eclipse Tractus-X Software Development KIT!")
