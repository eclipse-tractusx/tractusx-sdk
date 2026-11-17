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


from unittest.mock import Mock, patch

from tractusx_sdk.industry.models.aas.v3 import ServiceDescription
from tractusx_sdk.industry.services.aas_service import AasService

PROFILES = [
    "https://admin-shell.io/aas/API/3/0/DiscoveryServiceSpecification/SSP-001",
    "https://admin-shell.io/aas/API/3/2/AssetAdministrationShellRegistryServiceSpecification/SSP-005",
]


def test_get_description_accepts_profiles_of_any_aas_api_version():
    service = AasService(base_url="http://dtr", base_lookup_url="http://dtr", api_path="/api/v3")
    response = Mock()
    response.json.return_value = {"profiles": PROFILES}

    with patch(
        "tractusx_sdk.industry.services.aas_service.HttpTools.do_get_with_session",
        return_value=response,
    ):
        description = service.get_description()

    assert isinstance(description, ServiceDescription)
    assert description.profiles == PROFILES
