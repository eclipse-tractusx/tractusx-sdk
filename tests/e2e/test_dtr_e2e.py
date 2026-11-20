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
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

## This code was partially generated using artificial intelligence (AI) (Tool: Claude Code, Model: Claude Opus 5.5).
## It was reviewed and tested by a human committer.

"""Digital Twin Registry E2E: shell and submodel descriptor lifecycle through ``AasService``.

The tests in this module share one shell descriptor and run in file order:
create, read it back three ways, then delete it.

The Tractus-X registry filters reads by the caller that the ``Edc-Bpn`` header
names: a shell is only returned to its owner or to a participant named in one
of its specific asset ids' ``externalSubjectId``, and anyone else gets a 404.
Create and delete are checked against the caller's role only. So the shell
names the provider as its reader, and every read passes ``bpn=`` with that
same identity (as TestLab's ``dtr_roundtrip`` does).
"""

from __future__ import annotations

import logging
import uuid

import pytest

from tractusx_sdk.industry.models.aas.v3 import (
    GetAllShellDescriptorsResponse,
    GetSubmodelDescriptorsByAssResponse,
    Result,
    ShellDescriptor,
)

from tests.e2e.settings import SEMANTIC_ID

MAX_PAGES = 20

#: The provider's public data-plane API in the Umbrella CI deployment. The
#: registry only stores this href; these tests never dial it.
PROVIDER_PUBLIC_API = "http://provider.local/api/public"

logger = logging.getLogger("tractusx_sdk.e2e")


def _shell_descriptor(aas_id: str, submodel_id: str, run_id: str, dsp_url: str, reader: str) -> ShellDescriptor:
    """A Catena-X style shell with one submodel offered over DSP (the models take camelCase keys).

    *reader* is named as the specific asset id's ``externalSubjectId``, which is
    what lets that participant read the shell back.
    """
    return ShellDescriptor.model_validate(
        {
            "id": aas_id,
            "idShort": f"sdk-e2e-{run_id}",
            "globalAssetId": f"urn:uuid:{uuid.uuid4()}",
            "assetKind": "Instance",
            "specificAssetIds": [
                {
                    "name": "manufacturerPartId",
                    "value": f"sdk-e2e-part-{run_id}",
                    "externalSubjectId": {
                        "type": "ExternalReference",
                        "keys": [{"type": "GlobalReference", "value": reader}],
                    },
                }
            ],
            "submodelDescriptors": [
                {
                    "id": submodel_id,
                    "idShort": "BusinessPartnerCertificate",
                    "semanticId": {
                        "type": "ExternalReference",
                        "keys": [{"type": "GlobalReference", "value": SEMANTIC_ID}],
                    },
                    "endpoints": [
                        {
                            "interface": "SUBMODEL-3.0",
                            "protocolInformation": {
                                "href": f"{PROVIDER_PUBLIC_API}/data/{submodel_id}",
                                "endpointProtocol": "HTTP",
                                "endpointProtocolVersion": ["1.1"],
                                "subprotocol": "DSP",
                                "subprotocolBody": f"id=sdk-e2e-asset-{run_id};dspEndpoint={dsp_url}",
                                "subprotocolBodyEncoding": "plain",
                                "securityAttributes": [{"type": "NONE", "key": "NONE", "value": "NONE"}],
                            },
                        }
                    ],
                }
            ],
        }
    )


@pytest.fixture(scope="module")
def shell(settings, aas_service, run_id):
    """Ids for one shell descriptor; removes it afterwards if a test left it behind."""
    ids = {
        "aas_id": f"urn:uuid:{uuid.uuid4()}",
        "submodel_id": f"urn:uuid:{uuid.uuid4()}",
        # The provider's participant id (its DID), as TestLab's dtr_roundtrip uses it.
        "reader": settings.provider.did,
    }
    ids["descriptor"] = _shell_descriptor(
        ids["aas_id"], ids["submodel_id"], run_id, settings.provider.dsp_url, ids["reader"]
    )
    yield ids
    # A 404 here is normal: test_delete_shell_descriptor already removed it.
    try:
        aas_service.delete_asset_administration_shell_descriptor(ids["aas_id"])
    except Exception as exc:  # cleanup must not hide the test result
        logger.warning("could not delete shell %s: %s", ids["aas_id"], exc)


def test_create_shell_descriptor(aas_service, shell):
    created = aas_service.create_asset_administration_shell_descriptor(shell["descriptor"])

    assert isinstance(created, ShellDescriptor), f"DTR refused the shell: {created}"
    assert created.id == shell["aas_id"]


def test_get_shell_descriptor_by_id(aas_service, shell):
    found = aas_service.get_asset_administration_shell_descriptor_by_id(shell["aas_id"], bpn=shell["reader"])

    assert isinstance(found, ShellDescriptor), f"shell not found: {found}"
    assert found.id == shell["aas_id"]
    assert [sm.id for sm in found.submodel_descriptors or []] == [shell["submodel_id"]]


def test_get_submodel_descriptors_by_aas_id(aas_service, shell):
    found = aas_service.get_submodel_descriptors_by_aas_id(shell["aas_id"], bpn=shell["reader"])

    assert isinstance(found, GetSubmodelDescriptorsByAssResponse), f"no submodel descriptors: {found}"
    assert [sm.id for sm in found.result] == [shell["submodel_id"]]
    endpoint = found.result[0].endpoints[0]
    assert endpoint.protocol_information.subprotocol == "DSP"


def test_get_all_shell_descriptors_lists_the_shell(aas_service, shell):
    """Page through the registry with the SDK's cursor until the new shell shows up."""
    cursor = None
    for _ in range(MAX_PAGES):
        page = aas_service.get_all_asset_administration_shell_descriptors(limit=50, cursor=cursor)
        assert isinstance(page, GetAllShellDescriptorsResponse), f"listing failed: {page}"
        if any(descriptor.id == shell["aas_id"] for descriptor in page.result):
            return
        cursor = page.paging_metadata.cursor if page.paging_metadata else None
        if not cursor:
            break
    pytest.fail(f"shell {shell['aas_id']} not in the registry listing")


def test_delete_shell_descriptor(aas_service, shell):
    deleted = aas_service.delete_asset_administration_shell_descriptor(shell["aas_id"])
    assert deleted is None, f"delete failed: {deleted}"

    # Read as the shell's reader, so a 404 here means deleted and not just hidden.
    gone = aas_service.get_asset_administration_shell_descriptor_by_id(shell["aas_id"], bpn=shell["reader"])
    assert isinstance(gone, Result), f"shell still there after delete: {gone}"
