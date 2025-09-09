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
    DATAPLANE_SELECTOR = "DataplaneSelector"
    APPLICATION_OBSERVABILITY = "ApplicationObservability"
    CONNECTOR_DISCOVERY = "ConnectorDiscovery"
    PROTOCOL_VERSION = "ProtocolVersion"
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
        if path.isdir(module_path) and module != "__pycache__" and module != "utils":
            SUPPORTED_VERSIONS.append(module)

    @staticmethod
    def _get_controller_builder(
            controller_type: ControllerType,
            dataspace_version: str,
    ):
        """
        Create a controller, based on the specified controller type and version.

        Different controller types and versions may have different implementations and parameters, which should be the
        responsibility of the specific controller class to handle. This factory method dynamically imports the correct
        controller class, and returns it, with whatever parameters necessary for its initialization.

        :param controller_type: The type of controller to create, as per the AdapterType enum
        :param dataspace_version: The version of the Dataspace (e.g., "jupiter")
        :return: An instance of the specified Adapter subclass
        """

        # Check if the requested version is supported for the given controller type
        if dataspace_version not in ControllerFactory.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version {dataspace_version}")

        # Compute the controller module path dynamically, depending on the connector version
        connector_module = ".".join(__name__.split(".")[0:-1])
        module_name = f"{connector_module}.{dataspace_version}"

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
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create an asset controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.ASSET,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_catalog_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a catalog controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CATALOG,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_agreement_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a contract_agreement controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CONTRACT_AGREEMENT,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_definition_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a contract_definition controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CONTRACT_DEFINITION,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_negotiation_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a contract_negotiation controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CONTRACT_NEGOTIATION,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_edr_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create an EDR controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.EDR,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_policy_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a policy controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.POLICY,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_transfer_process_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a transfer_process controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.TRANSFER_PROCESS,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()
    
    @staticmethod
    def get_dataplane_selector_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a dataplane_selector controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "saturn")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.DATAPLANE_SELECTOR,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()
    
    @staticmethod
    def get_application_observability_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create an application_observability controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "saturn")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.APPLICATION_OBSERVABILITY,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_connector_discovery_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a connector_discovery controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "saturn")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.CONNECTOR_DISCOVERY,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_protocol_version_controller(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create a protocol_version controller instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "saturn")
        :param adapter: The DMA adapter to use for the controller

        :return: An instance of the specified Controller subclass
        """

        builder = ControllerFactory._get_controller_builder(
            controller_type=ControllerType.PROTOCOL_VERSION,
            dataspace_version=dataspace_version,
        )

        builder.adapter(adapter)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_dma_controllers_for_version(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            controller_types: list[ControllerType],
            **kwargs
    ):
        """
        Create controllers of a specific connector version, for a list of controller types.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller
        :param controller_types: The controller types to instantiate, as a list of ControllerTypes
        :param kwargs: Additional parameters to pass to the controller builder
        :return: A dictionary of controller instances, keyed by controller type
        """

        controllers = {}
        for controller_type in controller_types:
            # For each controller type in ControllerType, call the corresponding get_controller method
            method_name = f"get_{controller_type.name.lower()}_controller"
            if hasattr(ControllerFactory, method_name):
                method = getattr(ControllerFactory, method_name)
                try:
                    controllers[controller_type] = method(
                        dataspace_version=dataspace_version,
                        adapter=adapter,
                        **kwargs
                    )
                except AttributeError:
                    raise ValueError(
                        f"A controller for {controller_type.name} does not exist for version {dataspace_version}")

        return controllers

    @staticmethod
    def get_all_dma_controllers_for_version(
            dataspace_version: str,
            adapter: BaseDmaAdapter,
            **kwargs
    ):
        """
        Create all DMA controllers for a specific connector version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param adapter: The DMA adapter to use for the controller
        :param kwargs: Additional parameters to pass to the controller builder
        :return: A dictionary of controller instances, keyed by controller type
        """

        return ControllerFactory.get_dma_controllers_for_version(
            dataspace_version=dataspace_version,
            adapter=adapter,
            controller_types=[controller_type for controller_type in ControllerType],
            **kwargs
        )
