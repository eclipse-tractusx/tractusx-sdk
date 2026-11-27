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

"""Connector E2E: provider offer -> consumer catalog -> negotiation -> transfer -> EDR -> data.

Every call to the dataspace goes through the SDK's Saturn connector services;
the only plain HTTP is the final pull with the EDR the SDK handed back.
"""

from __future__ import annotations

import time

import requests

from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory

from tests.e2e.settings import CATENAX_POLICY_CONTEXT, DSP_PROTOCOL

POLL_INTERVAL_SECONDS = 2


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _get(data: dict, key: str, prefix: str):
    """Read a JSON-LD key from a compacted or a prefixed EDC response."""
    return data.get(key, data.get(f"{prefix}:{key}"))


def _find_dataset(catalog: dict, asset_id: str) -> dict:
    datasets = _as_list(_get(catalog, "dataset", "dcat"))
    for dataset in datasets:
        if dataset.get("@id") == asset_id:
            return dataset
    ids = [dataset.get("@id") for dataset in datasets]
    raise AssertionError(f"asset {asset_id} not in the catalog; datasets offered: {ids}")


def _poll_state(fetch, terminal_ok: set, timeout_seconds: int) -> str:
    """Poll a `/state` endpoint until it reaches one of *terminal_ok* or TERMINATED."""
    deadline = time.monotonic() + timeout_seconds
    state = None
    while time.monotonic() < deadline:
        response = fetch()
        if response.status_code == 200:
            body = response.json()
            state = body.get("state", body.get("edc:state"))
            if state in terminal_ok:
                return state
            assert state != "TERMINATED", f"process was TERMINATED: {body}"
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError(f"timed out after {timeout_seconds}s; last state {state!r}")


def test_catalog_offers_the_asset(settings, consumer_service, offer):
    """The consumer sees the provider's new asset, with an offer, in the provider's catalog."""
    catalog = consumer_service.get_catalog_by_asset_id(
        counter_party_id=settings.provider.did,
        counter_party_address=settings.provider.dsp_url,
        asset_id=offer["asset_id"],
    )

    assert catalog, "the catalog request returned nothing"
    dataset = _find_dataset(catalog, offer["asset_id"])
    offers = _as_list(_get(dataset, "hasPolicy", "odrl"))
    assert offers, f"asset {offer['asset_id']} is in the catalog without an offer"
    assert offers[0].get("@id"), "the offer has no id"


def test_negotiate_transfer_and_pull_step_by_step(settings, consumer_service, offer, payload):
    """Negotiation, transfer and EDR through the SDK's controllers and models, one step at a time."""
    catalog = consumer_service.get_catalog_by_asset_id(
        counter_party_id=settings.provider.did,
        counter_party_address=settings.provider.dsp_url,
        asset_id=offer["asset_id"],
    )
    is_prefixed = "dcat:dataset" in catalog
    offer_policy = _as_list(_get(_find_dataset(catalog, offer["asset_id"]), "hasPolicy", "odrl"))[0]
    participant_id = _get(catalog, "participantId", "dspace") or settings.provider.did
    if is_prefixed:
        offer_policy_data = {
            f"odrl:{rule}": offer_policy.get(f"odrl:{rule}", offer_policy.get(rule, []))
            for rule in ("permission", "prohibition", "obligation")
        }
    else:
        offer_policy_data = {
            rule: offer_policy.get(rule, []) for rule in ("permission", "prohibition", "obligation")
        }

    # Contract negotiation
    negotiation = ModelFactory.get_contract_negotiation_model(
        dataspace_version=settings.dataspace_version,
        counter_party_address=settings.provider.dsp_url,
        offer_id=offer_policy["@id"],
        asset_id=offer["asset_id"],
        provider_id=participant_id,
        offer_policy=offer_policy_data,
        context=CATENAX_POLICY_CONTEXT,
        protocol=DSP_PROTOCOL,
    )
    created = consumer_service.contract_negotiations.create(obj=negotiation)
    assert created.status_code == 200, f"negotiation not started: {created.status_code} {created.text}"
    negotiation_id = created.json()["@id"]

    _poll_state(
        lambda: consumer_service.contract_negotiations.get_state_by_id(negotiation_id),
        {"FINALIZED"},
        settings.timeout_seconds,
    )
    negotiation_body = consumer_service.contract_negotiations.get_by_id(negotiation_id).json()
    agreement_id = negotiation_body.get("contractAgreementId", negotiation_body.get("edc:contractAgreementId"))
    assert agreement_id, f"FINALIZED negotiation without an agreement: {negotiation_body}"

    # Transfer process (HttpData-PULL)
    transfer = ModelFactory.get_transfer_process_model(
        dataspace_version=settings.dataspace_version,
        counter_party_address=settings.provider.dsp_url,
        contract_id=agreement_id,
        transfer_type="HttpData-PULL",
        protocol=DSP_PROTOCOL,
        data_destination={"type": "HttpProxy"},
    )
    started = consumer_service.transfer_processes.create(obj=transfer)
    assert started.status_code == 200, f"transfer not started: {started.status_code} {started.text}"
    transfer_id = started.json()["@id"]

    _poll_state(
        lambda: consumer_service.transfer_processes.get_state_by_id(transfer_id),
        {"STARTED", "COMPLETED"},
        settings.timeout_seconds,
    )

    # EDR, then the pull itself
    edr_response = consumer_service.edrs.get_data_address(transfer_id)
    assert edr_response.status_code == 200, f"no EDR: {edr_response.status_code} {edr_response.text}"
    edr = edr_response.json()
    endpoint = edr.get("endpoint", edr.get("edc:endpoint"))
    token = edr.get("authorization", edr.get("edc:authorization"))
    assert endpoint and token, f"EDR without endpoint or token: {sorted(edr)}"

    # Same URL `do_get(path="/")` builds; the backend ignores surrounding slashes.
    data = requests.get(f"{endpoint}/", headers={"Authorization": token}, timeout=30)
    assert data.status_code == 200, f"data plane answered {data.status_code}: {data.text}"
    assert data.json() == payload


def test_do_get_returns_the_payload(settings, consumer_service, offer, payload):
    """`do_get` does catalog, negotiation, transfer, EDR and GET in one SDK call."""
    filter_expression = [
        consumer_service.get_filter_expression(
            key=consumer_service.DEFAULT_ID_KEY,
            value=offer["asset_id"],
            operator="=",
        )
    ]

    response = consumer_service.do_get(
        counter_party_id=settings.provider.did,
        counter_party_address=settings.provider.dsp_url,
        filter_expression=filter_expression,
        policies=None,
        path="/",
        max_wait=settings.timeout_seconds,
        verify=False,
    )

    assert response.status_code == 200, f"do_get answered {response.status_code}: {response.text}"
    assert response.json() == payload
