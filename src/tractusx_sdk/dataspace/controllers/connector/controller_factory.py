#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
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

from enum import Enum
from importlib import import_module
from os import listdir, path

from ...adapters.connector.base_dma_adapter import BaseDmaAdapter


class ControllerType(Enum):
    """
    Enum for different controller types. Each controller type corresponds to a specific implementation,
    and must correspond exactly to the prefix of the controller class it is associated with.
    """

    ASSET = "Asset"
    CATALOG = "Catalog"
    CONTRACT_AGREEMENT = "ContractAgreement"
    CONTRACT_DEFINITION = "ContractDefinition"
    CONTRACT_NEGOTIATION = "ContractNegotiation"
    EDR = "Edr"
    POLICY = "Policy"
    TRANSFER_PROCESS = "TransferProcess"
    # TODO: Add any other existing controller types


class ControllerFactory:
    """
    Factory class to manage the creation of Controller instances
    """
    # Dynamically load supported versions from the directory structure
    _controllers_base_path = path.dirname(__file__)
    SUPPORTED_VERSIONS = []
    for module in listdir(_controllers_base_path):
        module_path = path.join(_controllers_base_path, module)
        if path.isdir(module_path) and module.startswith("v"):
            SUPPORTED_VERSIONS.append(module)

    @staticmethod
    def _get_controller_builder(
            controller_type: ControllerType,
            connector_version: str,
    ):
        """
        Create a controller, based on the specified controller type and version.

        Different controller types and versions may have different implementations and parameters, which should be the
        responsibility of the specific controller class to handle. This factory method dynamically imports the correct
        controller class, and returns it, with whatever parameters necessary for its initialization.

        :param controller_type: The type of controller to create, as per the AdapterType enum
        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :return: An instance of the specified Adapter subclass
        """

        # Check if the requested version is supported for the given controller type
        if connector_version not in ControllerFactory.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version {connector_version}")

        # Compute the controller module path dynamically, depending on the connector version
        connector_module = ".".join(__name__.split(".")[0:-1])
        module_name = f"{connector_module}.{connector_version}"

        # Compute the controller class name based on the controller type
        controller_class_name = f"{controller_type.value}Controller"

        try:
            # Dynamically import the controller class
            module = import_module(module_name)
            controller_class = getattr(module, controller_class_name)
            return controller_class.builder()
        except AttributeError as attr_exception:
            raise AttributeError(
                f"Failed to import controller class {controller_class_name} for module {module_name}"
            ) from attr_exception
        except (ModuleNotFoundError, ImportError) as import_exception:
            raise ImportError(
                f"Failed to import module {module_name}. Ensure that the required packages are installed and the PYTHONPATH is set correctly."
            ) from import_exception

    @staticmethod
    def get_asset_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create an asset controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.ASSET,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_catalog_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a catalog controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CATALOG,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_agreement_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a contract_agreement controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CONTRACT_AGREEMENT,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_definition_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a contract_definition controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CONTRACT_DEFINITION,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_negotiation_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a contract_negotiation controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CONTRACT_NEGOTIATION,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_edr_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create an EDR controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.EDR,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_policy_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a policy controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.POLICY,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_transfer_process_controller(
            connector_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a transfer_process controller instance, based a specific version.

        :param connector_version: The version of the Connector (i.e: "v0_9_0")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.TRANSFER_PROCESS,
            connector_version=connector_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()
