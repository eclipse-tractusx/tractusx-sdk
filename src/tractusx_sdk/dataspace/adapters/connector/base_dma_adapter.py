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

from ..adapter import Adapter
from ...tools import HttpTools


class BaseDmaAdapter(Adapter):
    dma_path: str = ""

    def __init__(self, base_url: str, dma_path: str, headers: dict = None):
        self.dma_path = dma_path

        dma_url = HttpTools.concat_into_url(base_url, dma_path)
        super().__init__(dma_url, headers)

    class _Builder(Adapter._Builder):
        def dma_path(self, dma_path: str):
            self._data["dma_path"] = dma_path
            return self
