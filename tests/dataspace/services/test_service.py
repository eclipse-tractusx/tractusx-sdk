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
from .utils import TestService


class TestBaseService(unittest.TestCase):
    def setUp(self):
        self.dataspace_version = "v1"
        self.base_url = "https://example.com"
        self.headers = {"Authorization": "Bearer token"}

    def test_builder_creates_service_instance(self):
        builder = TestService.builder()
        builder.dataspace_version("v1")
        builder.base_url("https://example.com")
        builder.headers({"Authorization": "Bearer token"})

        service = builder.build()

        self.assertIsInstance(service, TestService)
        self.assertEqual(self.dataspace_version, service.dataspace_version)
        self.assertEqual(self.base_url, service.base_url)
        self.assertEqual(self.headers, service.headers)

    def test_builder_fails_without_base_url(self):
        builder = TestService.builder()
        builder.dataspace_version(self.dataspace_version)
        with self.assertRaises(TypeError):
            builder.build()

    def test_builder_fails_without_version(self):
        builder = TestService.builder()
        builder.base_url(self.base_url)
        with self.assertRaises(TypeError):
            builder.build()
