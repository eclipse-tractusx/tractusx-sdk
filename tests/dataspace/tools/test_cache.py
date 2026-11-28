#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

import asyncio
import unittest

from tractusx_sdk.dataspace.tools.cache import LocalCache


class TestLocalCache(unittest.TestCase):

    def setUp(self):
        self.cache = LocalCache()

    def test_delete_removes_cached_value(self):
        async def scenario():
            await self.cache.set("my-key", b"my-value", expire=60)
            self.assertEqual(await self.cache.get("my-key"), b"my-value")
            await self.cache.delete("my-key")
            self.assertIsNone(await self.cache.get("my-key"))

        asyncio.run(scenario())

    def test_delete_missing_key_does_not_raise(self):
        asyncio.run(self.cache.delete("key-that-does-not-exist"))

    def test_get_with_empty_key_raises_value_error(self):
        async def scenario():
            with self.assertRaises(ValueError):
                await self.cache.get("")

        asyncio.run(scenario())

    def test_set_with_empty_key_raises_value_error(self):
        async def scenario():
            with self.assertRaises(ValueError):
                await self.cache.set("", b"value")

        asyncio.run(scenario())

    def test_delete_with_empty_key_raises_value_error(self):
        async def scenario():
            with self.assertRaises(ValueError):
                await self.cache.delete("")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
