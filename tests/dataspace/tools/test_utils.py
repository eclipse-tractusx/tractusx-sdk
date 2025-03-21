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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

from unittest import TestCase
from unittest.mock import patch

from tractusx_sdk.dataspace.tools import get_arguments

class TestUtils(TestCase):

    @patch('sys.argv', ['script_name', '--test-mode', '--debug', '--port', '8080', '--host', 'example.com'])
    def test_get_all_arguments_initialized(self):
        args = get_arguments()
        assert args.test_mode == True
        assert args.debug == True
        assert args.port == 8080
        assert args.host == 'example.com'

    @patch('sys.argv', [''])
    def test_get_all_arguments_not_initialized(self):
        args = get_arguments()
        assert args.test_mode == False
        assert args.debug == False
        assert args.port == 9000
        assert args.host == 'localhost'
