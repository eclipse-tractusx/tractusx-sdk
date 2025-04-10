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

from ..controller import Controller
from ...adapters.connector.base_dma_adapter import BaseDmaAdapter


class BaseDmaController(Controller):
    def __init__(self, adapter: BaseDmaAdapter):
        """
        Overwrite the default Controller constructor to force a BaseDmaAdapter-type adapter.
        """
        super().__init__(adapter)

    class _Builder(Controller._Builder):
        def adapter(self, adapter: BaseDmaAdapter):
            """
            Overwrite the default Controller builder adapter method to force a BaseDmaAdapter-type adapter.
            """
            return super().adapter(adapter)
