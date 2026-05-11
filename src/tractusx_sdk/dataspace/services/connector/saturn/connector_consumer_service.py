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

from requests import Response

from ..base_connector_consumer import BaseConnectorConsumerService
from ....models.connector.model_factory import ModelFactory


class ConnectorConsumerService(BaseConnectorConsumerService):
    EDC_NAMESPACE = "https://w3id.org/edc/v0.0.1/ns/"

    def __init__(
        self,
        dataspace_version: str,
        base_url: str,
        dma_path: str,
        headers: dict = None,
        connection_manager=None,
        debug: bool = False,
        logger=None,
        verbose: bool = False,
        verify_ssl: bool = True,
        connector_discovery_controller=None,
    ):
        super().__init__(
            dataspace_version=dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers,
            connection_manager=connection_manager,
            debug=(debug or verbose),
            logger=logger,
        )
        self.verify_ssl = verify_ssl
        self.controllers = {
            "CATALOG": self._catalog_controller,
            "EDR": self._edr_controller,
            "CONTRACT_NEGOTIATION": self._contract_negotiation_controller,
            "TRANSFER_PROCESS": self._transfer_process_controller,
            "CONNECTOR_DISCOVERY": connector_discovery_controller,
        }
        self._connector_discovery_controller = self.controllers["CONNECTOR_DISCOVERY"]

    def discover_connector_protocol(
        self,
        bpnl: str,
        counter_party_address: str = None,
        verify: bool = None,
    ) -> dict | None:
        if verify is None:
            verify = self.verify_ssl

        request = ModelFactory.get_connector_discovery_model(
            dataspace_version=self.dataspace_version,
            bpnl=bpnl,
            counter_party_address=counter_party_address,
        )
        if self.connector_discovery is None:
            raise RuntimeError("[Connector Service] Connector discovery controller is not configured.")
        response: Response = self.connector_discovery.get_discover(request, verify=verify)
        if response is None or response.status_code != 200:
            status_code = None if response is None else response.status_code
            raise ConnectionError(
                f"[Connector Service] It was not possible to discover connector protocol because the response was not successful! Status: {status_code}"
            )
        return response.json()

    def get_discovery_info(
        self,
        bpnl: str,
        counter_party_address: str = None,
        namespace: str = EDC_NAMESPACE,
        verify: bool = None,
    ) -> tuple[str, str, str]:
        discovery_info = self.discover_connector_protocol(
            bpnl=bpnl,
            counter_party_address=counter_party_address,
            verify=verify,
        )

        def _get(key: str):
            namespaced = f"{namespace}{key}"
            if namespaced in discovery_info:
                return discovery_info[namespaced]
            if key in discovery_info:
                return discovery_info[key]
            raise KeyError(f"Missing key '{key}' in discovery response")

        return _get("counterPartyAddress"), _get("counterPartyId"), _get("protocol")

    @property
    def connector_discovery(self):
        return self._connector_discovery_controller
