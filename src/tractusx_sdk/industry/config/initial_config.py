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
from tractusx_sdk.dataspace.tools import op, get_arguments, get_app_config, get_log_config
from tractusx_sdk.industry.services import AasService

global auth_manager, edc_service, aas_service, logger, args, app_configuration, log_config

auth_manager: AuthManager

edc_service: EdcService

aas_service: AasService

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
log_config = get_log_config(CONFIG_LOG_PATH, "industry-sdk")

# Load the configuation for the application
app_configuration = get_app_config(CONFIG_CONFIG_PATH)

## Start storage and aas communication service
base_url = app_configuration["AasService"]["base_url"]
base_lookup_url= app_configuration["AasService"]["base_lookup_url"]
api_path = app_configuration["AasService"]["api_path"]
aas_service = AasService(base_url, base_lookup_url, api_path)
