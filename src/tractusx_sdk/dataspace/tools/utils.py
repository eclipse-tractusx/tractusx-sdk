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

import argparse
import yaml
import logging.config
from tractusx_sdk.dataspace.tools import op

def get_arguments():
    
    parser = argparse.ArgumentParser()

    parser.add_argument('--test-mode', action='store_true', help="Run in test mode (skips uvicorn.run())", required=False)
    
    parser.add_argument("--debug", default=False, action="store_true", help="Enable and disable the debug", required=False)
    
    parser.add_argument("--port", default=9000, help="The server port where it will be available", type=int, required=False,)
    
    parser.add_argument("--host", default="localhost", help="The server host where it will be available", type=str, required=False)
    
    args = parser.parse_args()
    return args

def get_log_config(path, type):
    with open(path,'rt') as f:
        log_config = yaml.safe_load(f.read())
        current_date = op.get_filedate()
        log_config = create_log(log_config, current_date, type)
        logging.config.dictConfig(log_config)
        return log_config

def create_log(log_config, current_date, type):
    op.make_dir(dir_name="logs/"+current_date)
    log_config["handlers"]["file"]["filename"] = f'logs/{current_date}/{op.get_filedatetime()}-{type}.log'
    return log_config

def get_app_config(path):
    with open(path, 'rt') as f:
        app_configuration = yaml.safe_load(f.read())
        return app_configuration
