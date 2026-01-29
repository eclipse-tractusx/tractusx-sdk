#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 LKS Next
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

from ..service import BaseService
from ...adapters.connector.adapter_factory import AdapterFactory
from ...controllers.connector.base_dma_controller import BaseDmaController
from ...controllers.connector.controller_factory import ControllerType, ControllerFactory
from ...models.connector.model_factory import ModelFactory
import logging


class BaseConnectorProviderService(BaseService):
    _asset_controller: BaseDmaController
    _contract_definition_controller: BaseDmaController
    _policy_controller: BaseDmaController

    def __init__(self, dataspace_version: str, base_url: str, dma_path: str, headers: dict = None, verbose: bool = True, logger: logging.Logger = None):
        self.dataspace_version = dataspace_version
        self.verbose = verbose
        self.logger = logger or logging.getLogger(__name__)

        dma_adapter = AdapterFactory.get_dma_adapter(
            dataspace_version=dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers
        )

        controllers = ControllerFactory.get_dma_controllers_for_version(
            dataspace_version=dataspace_version,
            adapter=dma_adapter,
            controller_types=[
                ControllerType.ASSET,
                ControllerType.CONTRACT_DEFINITION,
                ControllerType.POLICY
            ]
        )

        self._asset_controller = controllers.get(ControllerType.ASSET)
        self._contract_definition_controller = controllers.get(ControllerType.CONTRACT_DEFINITION)
        self._policy_controller = controllers.get(ControllerType.POLICY)

    class _Builder(BaseService._Builder):
        def dma_path(self, dma_path: str):
            self._data["dma_path"] = dma_path
            return self

    @property
    def assets(self):
        return self._asset_controller

    @property
    def contract_definitions(self):
        return self._contract_definition_controller

    @property
    def policies(self):
        return self._policy_controller

    ############################# Short cut section
    ## Code originally belonging to Industry Core Hub:
    # https://github.com/eclipse-tractusx/industry-core-hub

    def create_asset(
        self,
        asset_id: str,
        base_url: str,
        dct_type: str,
        version: str = "3.0",
        semantic_id: str = None,
        proxy_params: dict = {
            "proxyQueryParams": "false",
            "proxyPath": "true",
            "proxyMethod": "true",
            "proxyBody": "false"
        },
        headers: dict = None,
        private_properties: dict = None,
        oauth2_config: dict = None
    ):
        if self.verbose:
            self.logger.info(f"Creating asset {asset_id} at {base_url}.")

        context = {
            "edc": "https://w3id.org/edc/v0.0.1/ns/",
            "cx-common": "https://w3id.org/catenax/ontology/common#",
            "cx-taxo": "https://w3id.org/catenax/taxonomy#",
            "dct": "http://purl.org/dc/terms/"
        }

        data_address = {
            "@type": "DataAddress",
            "type": "HttpData",
            "baseUrl": base_url
        }

        if proxy_params is not None:
            data_address.update(proxy_params)

        if oauth2_config is not None:
            if "tokenUrl" not in oauth2_config or "clientId" not in oauth2_config:
                raise ValueError(
                    "During asset creation, OAuth2-protected data addresses require at least 'tokenUrl' and 'clientId' in the oauth2_config parameter."
                )
            data_address["oauth2:tokenUrl"] = oauth2_config["tokenUrl"]
            data_address["oauth2:clientId"] = oauth2_config["clientId"]
            if "clientSecretKey" in oauth2_config:
                data_address["oauth2:clientSecretKey"] = oauth2_config["clientSecretKey"]

        if headers is not None:
            for key, value in headers.items():
                data_address["header:" + key] = value

        properties: dict = {
            "dct:type": {
                "@id": dct_type
            }
        }

        if version is not None:
            properties["cx-common:version"] = version

        if semantic_id is not None:
            context["aas-semantics"] = "https://admin-shell.io/aas/3/0/HasSemantics/"
            properties["aas-semantics:semanticId"] = {"@id": semantic_id}

        asset = ModelFactory.get_asset_model(
            dataspace_version=self.dataspace_version,
            context=context,
            oid=asset_id,
            properties=properties,
            private_properties=private_properties,
            data_address=data_address
        )

        asset_response = self.assets.create(obj=asset)

        if asset_response.status_code != 200:
            self.logger.error(asset_response.text)
            raise ValueError(f"Failed to create asset {asset_id}. Status code: {asset_response.status_code}")

        if self.verbose:
            self.logger.info(f"Asset {asset_id} created successfully.")

        return asset_response.json()

    def create_contract(
        self,
        contract_id: str,
        usage_policy_id: str,
        access_policy_id: str,
        asset_id: str
    ) -> dict:
        if self.verbose:
            self.logger.info(f"Creating new contract with ID {contract_id}.")

        context = {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }

        asset_selector = [
            {
                "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id",
                "operator": "=",
                "operandRight": asset_id
            }
        ]

        contract = ModelFactory.get_contract_definition_model(
            context=context,
            dataspace_version=self.dataspace_version,
            oid=contract_id,
            assets_selector=asset_selector,
            contract_policy_id=usage_policy_id,
            access_policy_id=access_policy_id
        )

        created_contract = self.contract_definitions.create(obj=contract)

        if created_contract.status_code != 200:
            raise ValueError(f"Failed to create contract {contract_id}. Status code: {created_contract.status_code}")

        if self.verbose:
            self.logger.info(f"Contract {contract_id} created successfully.")

        return created_contract.json()

    def create_policy(
        self,
        policy_id: str,
        context: dict | list[dict] = {},
        permissions: dict | list[dict] = [],
        prohibitions: dict | list[dict] = [],
        obligations: dict | list[dict] = []
    ) -> dict:
        if self.verbose:
            self.logger.info(f"Creating new policy with ID {policy_id}.")

        policy = ModelFactory.get_policy_model(
            dataspace_version=self.dataspace_version,
            oid=policy_id,
            context=context,
            permissions=permissions,
            prohibitions=prohibitions,
            obligations=obligations
        )

        created_policy = self.policies.create(obj=policy)

        if created_policy.status_code != 200:
            raise ValueError(f"Failed to create policy {policy_id}. Status code: {created_policy.status_code}")

        if self.verbose:
            self.logger.info(f"Policy {policy_id} created successfully.")

        return created_policy.json()
