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

## Import Library Packeges
from logging import config
import logging
import yaml
logging.captureWarnings(True)
import os

from tractusx_sdk.dataspace.managers import AuthManager
from tractusx_sdk.dataspace.services import EdcService
from tractusx_sdk.dataspace.tools import op, get_arguments

global edc_service, auth_manager, logger, args, app_configuration, log_config

## In memory authentication manager service
auth_manager: AuthManager

## In memory storage/management services
edc_service: EdcService

app_configuration:dict

log_config:dict

# Get the absolute path of the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_LOG_PATH = os.path.join(BASE_DIR, "logging.yml")
CONFIG_CONFIG_PATH = os.path.join(BASE_DIR, "configuration.yml")

## Start storage and edc communication service
edc_service = EdcService()

## Start the authentication manager
auth_manager = AuthManager()
    
# Initialize the server environment and get the comand line arguments
args = get_arguments()

# Configure the logging confiuration depending on the configuration stated
logger = logging.getLogger('staging')
if(args.debug):
    logger = logging.getLogger('development')

## Create Loggin Folder
op.make_dir("logs")

# Load the logging config file
with open(CONFIG_LOG_PATH, 'rt') as f:
    # Read the yaml configuration
    log_config = yaml.safe_load(f.read())
    current_date = op.get_filedate()
    op.make_dir(dir_name="logs/"+current_date)
    log_config["handlers"]["file"]["filename"] = f'logs/{current_date}/{op.get_filedatetime()}-dataspace-sdk.log'
    config.dictConfig(log_config)

# Load the configuation for the application
with open(CONFIG_CONFIG_PATH, 'rt') as f:
    # Read the yaml configuration
    app_configuration = yaml.safe_load(f.read())
