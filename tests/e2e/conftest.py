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

"""Fixtures for the E2E suite: SDK services bound to the live dataspace, and one
provider offer (policies, asset, contract definition) shared by the connector tests.
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

import pytest
import requests

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.industry.services.aas_service import AasService

from tests.e2e.settings import (
    ACCESS_PERMISSIONS,
    CATENAX_POLICY_CONTEXT,
    DCT_TYPE,
    ENABLE_VARIABLE,
    PROXY_PARAMS,
    SEMANTIC_ID,
    USAGE_PERMISSIONS,
    E2ESettings,
    is_enabled,
)

logger = logging.getLogger("tractusx_sdk.e2e")

_E2E_DIR = Path(__file__).parent.resolve()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: needs a live Tractus-X dataspace (set TX_SDK_E2E=1 to run)"
    )


def pytest_collection_modifyitems(config, items):
    """Mark every test in this folder `e2e`, and skip them all unless the suite is enabled.

    A skip marker is evaluated before any fixture is set up, so a unit test run
    (`pytest tests/`) never tries to reach the dataspace.
    """
    skip = pytest.mark.skip(reason=f"E2E suite disabled; set {ENABLE_VARIABLE}=1 to run it")
    for item in items:
        if _E2E_DIR not in Path(str(item.path)).resolve().parents:
            continue
        item.add_marker(pytest.mark.e2e)
        if not is_enabled():
            item.add_marker(skip)


# ---------------------------------------------------------------------------
# Settings and SDK services
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def settings() -> E2ESettings:
    loaded = E2ESettings.from_env()
    if loaded.missing:
        pytest.fail(
            f"{ENABLE_VARIABLE}=1 but these variables are not set: {', '.join(loaded.missing)}",
            pytrace=False,
        )
    return loaded


@pytest.fixture(scope="session")
def run_id() -> str:
    """Unique per run, so repeated runs against one dataspace never collide."""
    return f"{int(time.time())}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def provider_service(settings):
    return ServiceFactory.get_connector_provider_service(
        dataspace_version=settings.dataspace_version,
        base_url=settings.provider.base_url,
        dma_path=settings.provider.dma_path,
        headers={settings.api_key_header: settings.provider.api_key, "Content-Type": "application/json"},
        verify_ssl=False,
    )


@pytest.fixture(scope="session")
def consumer_service(settings):
    return ServiceFactory.get_connector_consumer_service(
        dataspace_version=settings.dataspace_version,
        base_url=settings.consumer.base_url,
        dma_path=settings.consumer.dma_path,
        headers={settings.api_key_header: settings.consumer.api_key, "Content-Type": "application/json"},
        connection_manager=None,
        verify_ssl=False,
    )


@pytest.fixture(scope="session")
def aas_service(settings) -> AasService:
    return AasService(
        base_url=settings.dtr_base_url,
        base_lookup_url=settings.dtr_base_url,
        api_path=settings.dtr_api_path,
        verify_ssl=False,
    )


# ---------------------------------------------------------------------------
# The provider's offer
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def payload(run_id) -> dict:
    """What the provider publishes, and what every pull must return unchanged."""
    return {
        "source": "tractusx-sdk-e2e",
        "runId": run_id,
        "message": "Hello from the Tractus-X SDK E2E suite",
    }


@pytest.fixture(scope="session")
def offer(settings, provider_service, run_id, payload):
    """Upload the payload to the backend and publish it as an EDC offer with SDK methods.

    Yields the ids of everything created; deletes them again afterwards.
    """
    backend_item_url = f"{settings.backend_url}/urn:uuid:{uuid.uuid4()}"
    upload = requests.post(backend_item_url, json=payload, timeout=30)
    assert upload.status_code in (200, 201, 204), (
        f"backend upload to {backend_item_url} failed: {upload.status_code} {upload.text}"
    )

    ids = {
        "asset_id": f"sdk-e2e-asset-{run_id}",
        "access_policy_id": f"sdk-e2e-access-{run_id}",
        "usage_policy_id": f"sdk-e2e-usage-{run_id}",
        "contract_def_id": f"sdk-e2e-contract-{run_id}",
        "backend_item_url": backend_item_url,
    }
    created: list = []
    try:
        provider_service.create_policy(
            policy_id=ids["access_policy_id"],
            context=CATENAX_POLICY_CONTEXT,
            permissions=ACCESS_PERMISSIONS,
        )
        created.append((provider_service.policies, ids["access_policy_id"]))

        provider_service.create_policy(
            policy_id=ids["usage_policy_id"],
            permissions=USAGE_PERMISSIONS,
        )
        created.append((provider_service.policies, ids["usage_policy_id"]))

        provider_service.create_asset(
            asset_id=ids["asset_id"],
            base_url=backend_item_url,
            dct_type=DCT_TYPE,
            semantic_id=SEMANTIC_ID,
            version="1.0",
            proxy_params=dict(PROXY_PARAMS),
        )
        created.append((provider_service.assets, ids["asset_id"]))

        provider_service.create_contract(
            contract_id=ids["contract_def_id"],
            usage_policy_id=ids["usage_policy_id"],
            access_policy_id=ids["access_policy_id"],
            asset_id=ids["asset_id"],
        )
        created.append((provider_service.contract_definitions, ids["contract_def_id"]))

        yield ids
    finally:
        for controller, resource_id in reversed(created):
            try:
                controller.delete(resource_id)
            except Exception as exc:  # cleanup must not hide the test result
                logger.warning("could not delete %s: %s", resource_id, exc)
        try:
            requests.delete(backend_item_url, timeout=30)
        except requests.RequestException as exc:
            logger.warning("could not delete %s: %s", backend_item_url, exc)
