#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 Catena-X Automotive Network e.V.
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

from ..base_connector_consumer import BaseConnectorConsumerService


class ConnectorConsumerService(BaseConnectorConsumerService):

    EDC_NAMESPACE: str = "https://w3id.org/edc/v0.0.1/ns/"
    DSP_0_8: str = "dataspace-protocol-http"
    # Jupiter / legacy DSP uses Tractus-X v1.0.0 and W3C ODRL JSON-LD context URLs.
    # (Saturn replaces these with Catena-X 2025-9 URLs.)
    DEFAULT_NEGOTIATION_CONTEXT: list = [
        "https://w3id.org/tractusx/policy/v1.0.0",
        "http://www.w3.org/ns/odrl.jsonld",
        {"@vocab": EDC_NAMESPACE},
    ]
    DEFAULT_CONTEXT: dict = {
        "edc": EDC_NAMESPACE,
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "dct": "https://purl.org/dc/terms/",
    }
    DEFAULT_DCT_TYPE_KEY: str = "'http://purl.org/dc/terms/type'.'@id'"
    DEFAULT_ID_KEY: str = "https://w3id.org/edc/v0.0.1/ns/id"

    def get_transfer_id(
        self,
        counter_party_id: str,
        counter_party_address: str,
        filter_expression: list[dict],
        policies: list = None,
        max_wait: int = 60,
        poll_interval: int = 1,
        protocol: str = DSP_0_8,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: list = DEFAULT_NEGOTIATION_CONTEXT,
    ) -> str:
        """
        Jupiter (legacy) override of :meth:`BaseConnectorConsumerService.get_transfer_id`.

        Sets ``dataspace-protocol-http`` (legacy DSP) and the Tractus-X / W3C ODRL
        JSON-LD contexts as default values for protocol, catalog context, and
        negotiation context.  All other behaviour is inherited from the base class.

        @param counter_party_id: The Business Partner Number (BPN) of the provider.
        @param counter_party_address: The DSP URL of the EDC provider.
        @param filter_expression: Filter expressions for the catalog lookup.
        @param policies: Optional list of accepted policies. ``None`` uses the base-class behaviour.
        @param max_wait: Maximum seconds to wait for negotiation / EDR availability. Defaults to 60.
        @param poll_interval: Seconds between status-poll attempts. Defaults to 1.
        @param protocol: DSP protocol version. Defaults to ``"dataspace-protocol-http"`` (Jupiter legacy).
        @param catalog_context: JSON-LD context for catalog requests. Defaults to :attr:`DEFAULT_CONTEXT`.
        @param negotiation_context: JSON-LD context for negotiation requests. Defaults to :attr:`DEFAULT_NEGOTIATION_CONTEXT`.
        @returns: The transfer-process ID string.
        @raises RuntimeError: If negotiation is terminated or EDR is not available within *max_wait*.
        """
        return super().get_transfer_id(
            counter_party_id=counter_party_id,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            policies=policies,
            max_wait=max_wait,
            poll_interval=poll_interval,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context,
        )
