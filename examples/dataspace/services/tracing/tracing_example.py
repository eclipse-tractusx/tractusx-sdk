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

"""
Request Tracing Example

Shows how to record the requests sent to (and the responses received from) the
external services contacted by the SDK, and how to parse the result as JSON.

CONFIGURATION REQUIRED:
    Replace the connector and Digital Twin Registry values below with your own.
"""

import json

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.tools import Tracer
from tractusx_sdk.industry.services.aas_service import AasService

CONNECTOR_URL = "https://connector.example.com"
CONNECTOR_DMA_PATH = "/management"
CONNECTOR_API_KEY = "<your-api-key>"
DTR_URL = "https://dtr.example.com"
COUNTER_PARTY_BPN = "BPNL000000000000"


def trace_a_single_service():
    """The `trace` flag, like `verbose`, records everything a service exchanges."""

    provider = ServiceFactory.get_connector_provider_service(
        dataspace_version="jupiter",
        base_url=CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
        trace=True,
    )

    provider.assets.get_all()

    # The trace as a JSON string, ready to be stored or forwarded
    print(provider.get_trace_json())

    # ... or as plain dictionaries, to be filtered/inspected in code
    for entry in provider.get_trace():
        print(
            f"{entry['request']['method']} {entry['request']['url']} "
            f"-> {entry['response']['status_code']} in {entry['duration_ms']} ms"
        )

    provider.clear_trace()


def trace_a_complete_flow():
    """One tracer shared by several services produces one single, ordered trace."""

    tracer = Tracer(name="get-part-data")

    registry = AasService(
        base_url=DTR_URL,
        base_lookup_url=DTR_URL,
        api_path="/api/v3",
    )
    consumer = ServiceFactory.get_connector_consumer_service(
        dataspace_version="jupiter",
        base_url=CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
    )

    # Both services record into the same trace
    registry.set_tracer(tracer)
    consumer.set_tracer(tracer)

    registry.get_all_asset_administration_shell_descriptors(bpn=COUNTER_PARTY_BPN)
    consumer.get_catalog(
        counter_party_id=COUNTER_PARTY_BPN,
        counter_party_address=f"{CONNECTOR_URL}/api/v1/dsp",
    )

    trace = json.loads(tracer.to_json())
    print(f"{trace['count']} calls recorded")
    for entry in trace["entries"]:
        print(f"  [{entry['context']}] {entry['request']['method']} {entry['request']['url']}")


def trace_without_bodies():
    """Only the call sequence is kept, which is useful for large payloads."""

    tracer = Tracer(name="sequence-only", capture_bodies=False, max_entries=50)
    provider = ServiceFactory.get_connector_provider_service(
        dataspace_version="jupiter",
        base_url=CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
    )

    # A tracer built by hand configures what is recorded
    provider.set_tracer(tracer)
    provider.assets.get_all()
    print(tracer.to_json())


def trace_at_runtime():
    """Tracing can also be switched on and off after the service was created."""

    provider = ServiceFactory.get_connector_provider_service(
        dataspace_version="jupiter",
        base_url=CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
    )

    provider.enable_trace()
    provider.assets.get_all()
    print(provider.get_trace_json())

    provider.disable_trace()
    provider.assets.get_all()  # not recorded any more


if __name__ == "__main__":
    trace_a_single_service()
    trace_a_complete_flow()
    trace_without_bodies()
    trace_at_runtime()
