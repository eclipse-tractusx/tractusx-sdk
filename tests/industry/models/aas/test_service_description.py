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

from tractusx_sdk.industry.models.aas.v3 import ProfileEnum, ServiceDescription

# Self-description example from CX-0002 (Digital Twins in Catena-X), which mixes
# profiles of AAS API versions 3/0, 3/1 and 3/2.
CX_0002_PROFILES = [
    "https://admin-shell.io/aas/API/3/0/DiscoveryServiceSpecification/SSP-001",
    "https://admin-shell.io/aas/API/3/1/DiscoveryServiceSpecification/SSP-002",
    "https://admin-shell.io/aas/API/3/2/DiscoveryServiceSpecification/SSP-002",
    "https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-002",
    "https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-005",
    "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-005",
    "https://admin-shell.io/aas/API/3/2/AssetAdministrationShellRegistryServiceSpecification/SSP-005",
]


def test_profiles_of_any_aas_api_version_are_kept():
    description = ServiceDescription(profiles=CX_0002_PROFILES)

    assert description.profiles == CX_0002_PROFILES


def test_known_profile_still_equals_enum_member():
    # Pins backward compatibility: items are plain strings now, but still equal the enum members.
    profile = ProfileEnum.DISCOVERYSERVICESPECIFICATION_SSP_001.value

    description = ServiceDescription(profiles=[profile])

    assert description.profiles[0] == ProfileEnum.DISCOVERYSERVICESPECIFICATION_SSP_001
