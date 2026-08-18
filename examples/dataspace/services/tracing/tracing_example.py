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

Everything printed here is also written to a log file (`tracing_example.log` by
default, `TRACE_LOG_FILE` to change it), together with the messages logged by the
SDK itself, so a complete run can be inspected - or shared - afterwards.

CONFIGURATION REQUIRED:
    Replace the connector and Digital Twin Registry placeholders below with your
    own values, or provide them through the environment variables of the same
    name (CONSUMER_CONNECTOR_URL, CONNECTOR_URL, CONNECTOR_DMA_PATH,
    CONNECTOR_API_KEY, DTR_URL, COUNTER_PARTY_BPN).
"""

import json
import logging
import os
from pathlib import Path

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.tools import Tracer
from tractusx_sdk.industry.services.aas_service import AasService

# Replace the placeholders below, or set the matching environment variables.
# Never commit real URLs, API keys or credentials to this file.
CONSUMER_CONNECTOR_URL = os.getenv("CONSUMER_CONNECTOR_URL", "YOUR_CONSUMER_CONNECTOR_URL")  # e.g., "https://your-consumer-connector.example.com"
CONNECTOR_URL = os.getenv("CONNECTOR_URL", "YOUR_PROVIDER_CONNECTOR_DSP_URL")  # e.g., "https://your-provider-connector.example.com/api/v1/dsp/2025-1"
CONNECTOR_DMA_PATH = os.getenv("CONNECTOR_DMA_PATH", "/management")
CONNECTOR_API_KEY = os.getenv("CONNECTOR_API_KEY", "YOUR_CONNECTOR_API_KEY")  # the X-Api-Key of your connector management API
DTR_URL = os.getenv("DTR_URL", "YOUR_DTR_URL")  # e.g., "https://your-dtr.example.com"
COUNTER_PARTY_BPN = os.getenv("COUNTER_PARTY_BPN", "YOUR_COUNTER_PARTY_BPN")  # e.g., "BPNL0000000000XY" or a "did:web:..." identifier

LOG_FILE = Path(os.getenv("TRACE_LOG_FILE", "tracing_example.log"))

logger = logging.getLogger("tracing_example")


def configure_logging():
    """Sends everything - the traces and the SDK own messages - to `LOG_FILE`."""

    logging.basicConfig(
        filename=LOG_FILE,
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
    )


def report(title: str, payload: str = None):
    """Prints to the console and stores the same content in the log file."""

    print(payload if payload is not None else title)
    if payload is None:
        logger.info(title)
    else:
        logger.info("%s\n%s", title, payload)


def trace_a_single_service():
    """The `trace` flag, like `verbose`, records everything a service exchanges."""

    provider = ServiceFactory.get_connector_provider_service(
        dataspace_version="saturn",
        base_url=CONSUMER_CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
        logger=logger,
        trace=True,
    )

    provider.assets.get_all()

    # The trace as a JSON string, ready to be stored or forwarded
    report("single service trace", provider.get_trace_json())

    # ... or as plain dictionaries, to be filtered/inspected in code
    for entry in provider.get_trace():
        report(
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
        dataspace_version="saturn",
        base_url=CONSUMER_CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
        logger=logger,
    )

    # Both services record into the same trace
    registry.set_tracer(tracer)
    consumer.set_tracer(tracer)

    # A failing call is recorded like any other, so the trace is printed either way
    try:
        registry.get_all_asset_administration_shell_descriptors(bpn=COUNTER_PARTY_BPN)
        consumer.get_catalog(
            counter_party_id=COUNTER_PARTY_BPN,
            counter_party_address=CONNECTOR_URL
        )
    finally:
        # The complete trace of both services, in execution order
        report("complete flow trace", tracer.to_json())

        # ... or a summary built from the same entries, parsed back as JSON
        trace = json.loads(tracer.to_json())
        report(f"{trace['count']} calls recorded")
        for entry in trace["entries"]:
            status = entry["response"]["status_code"] if entry["response"] else entry["error"]["type"]
            report(f"  [{entry['context']}] {entry['request']['method']} {entry['request']['url']} -> {status}")


def trace_without_bodies():
    """Only the call sequence is kept, which is useful for large payloads."""

    tracer = Tracer(name="sequence-only", capture_bodies=False, max_entries=50)
    provider = ServiceFactory.get_connector_provider_service(
        dataspace_version="saturn",
        base_url=CONSUMER_CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
        logger=logger,
    )

    # A tracer built by hand configures what is recorded
    provider.set_tracer(tracer)
    provider.assets.get_all()
    report("sequence only trace", tracer.to_json())


def trace_at_runtime():
    """Tracing can also be switched on and off after the service was created."""

    provider = ServiceFactory.get_connector_provider_service(
        dataspace_version="saturn",
        base_url=CONSUMER_CONNECTOR_URL,
        dma_path=CONNECTOR_DMA_PATH,
        headers={"X-Api-Key": CONNECTOR_API_KEY},
        verbose=False,
        logger=logger,
    )

    provider.enable_trace()
    provider.assets.get_all()
    report("runtime enabled trace", provider.get_trace_json())

    provider.disable_trace()
    provider.assets.get_all()  # not recorded any more


if __name__ == "__main__":
    configure_logging()
    try:
        trace_a_single_service()
        trace_a_complete_flow()
        trace_without_bodies()
        trace_at_runtime()
    finally:
        # Written whether the run succeeded or failed
        print(f"\nComplete run stored in {LOG_FILE.resolve()}")
