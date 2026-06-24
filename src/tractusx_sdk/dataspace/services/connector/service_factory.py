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
import logging

from tractusx_sdk.dataspace.managers.connection.base_connection_manager import BaseConnectionManager


class ServiceType(Enum):
    """
    Enum for different service types. Each service type corresponds to a specific implementation,
    and must correspond exactly to the prefix of the service class it is associated with.
    """

    CONNECTOR_CONSUMER = "ConnectorConsumer"
    CONNECTOR_PROVIDER = "ConnectorProvider"
    CONNECTOR = "Connector"


class ServiceFactory:
    """
    Factory class to manage the creation of Service instances
    """
    # Dynamically load supported versions from the directory structure
    _services_base_path = path.dirname(__file__)
    SUPPORTED_VERSIONS = []
    for module in listdir(_services_base_path):
        module_path = path.join(_services_base_path, module)
        if path.isdir(module_path) and module != "__pycache__":
            SUPPORTED_VERSIONS.append(module)

    @staticmethod
    def _get_service_builder(
            service_type: ServiceType,
            dataspace_version: str,
    ):
        """
        Create a service, based on the specified service type and version.

        Different service types and versions may have different implementations and parameters, which should be the
        responsibility of the specific service class to handle. This factory method dynamically imports the correct
        service class, and returns it, with whatever parameters necessary for its initialization.

        :param service_type: The type of service to create, as per the AdapterType enum
        :param dataspace_version: The version of the Dataspace (e.g., "jupiter")
        :return: An instance of the specified Adapter subclass
        """

        # Check if the requested version is supported for the given service type
        if dataspace_version not in ServiceFactory.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version {dataspace_version}")

        # Compute the service module path dynamically, depending on the connector version
        connector_module = ".".join(__name__.split(".")[0:-1])
        module_name = f"{connector_module}.{dataspace_version}"

        # Compute the service class name based on the service type
        service_class_name = f"{service_type.value}Service"

        try:
            # Dynamically import the service class
            module = import_module(module_name)
            service_class = getattr(module, service_class_name)
            return service_class.builder()
        except AttributeError as attr_exception:
            raise AttributeError(
                f"Failed to import service class {service_class_name} for module {module_name}"
            ) from attr_exception
        except (ModuleNotFoundError, ImportError) as import_exception:
            raise ImportError(
                f"Failed to import module {module_name}. Ensure that the required packages are installed and the PYTHONPATH is set correctly."
            ) from import_exception

    @staticmethod
    def get_connector_consumer_service(
            dataspace_version: str,
            base_url: str,
            dma_path: str,
            headers: dict = None,
            connection_manager: BaseConnectionManager = None,
            verbose: bool = True,
            debug: bool = False,
            logger: logging.Logger = None,
            **kwargs
    ):
        """
        Create a Connector consumer service instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param base_url: The base URL of the Connector service
        :param dma_path: The DMA path of the Connector service
        :param headers: The extra headers to be used for requests to the service
        :param connection_manager: The connection manager to use for the service
        :param verbose: Verbose flag for the service
        :param debug: Debug flag to log request payloads before HTTP calls
        :return: An instance of the specified Service subclass
        """

        builder = ServiceFactory._get_service_builder(
            service_type=ServiceType.CONNECTOR_CONSUMER,
            dataspace_version=dataspace_version,
        )

        builder.dataspace_version(dataspace_version)
        builder.base_url(base_url)
        builder.dma_path(dma_path)
        builder.headers(headers)
        builder.connector_manager(connection_manager)

        # Include any additional parameters
        builder.data({**kwargs, "verbose": verbose, "debug": debug, "logger": logger})
        return builder.build()

    @staticmethod
    def get_connector_provider_service(
            dataspace_version: str,
            base_url: str,
            dma_path: str,
            headers: dict = None,
            verbose: bool = True,
            debug: bool = False,
            logger: logging.Logger = None,
            **kwargs
    ):
        """
        Create a Connector provider service instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param base_url: The base URL of the Connector service
        :param dma_path: The DMA path of the Connector service
        :param headers: The extra headers to be used for requests to the service
        :param verbose: Verbose flag for the service
        :param debug: Debug flag to log request payloads before HTTP calls
        :param logger: Logger instance for the service
        :return: An instance of the specified Service subclass
        """

        builder = ServiceFactory._get_service_builder(
            service_type=ServiceType.CONNECTOR_PROVIDER,
            dataspace_version=dataspace_version,
        )

        builder.dataspace_version(dataspace_version)
        builder.base_url(base_url)
        builder.dma_path(dma_path)
        builder.headers(headers)

        # Include any additional parameters
        builder.data({**kwargs, "verbose": verbose, "debug": debug, "logger": logger})
        return builder.build()

    @staticmethod
    def get_connector_service(
            dataspace_version: str,
            base_url: str,
            dma_path: str,
            headers: dict = None,
            connection_manager: BaseConnectionManager = None,
            logger: logging.Logger = None,
            verbose: bool = True,
            **kwargs
    ):
        """
        Create a complete Connector service instance, based a specific version.

        :param dataspace_version: The version of the Dataspace (i.e: "jupiter")
        :param base_url: The base URL of the Connector service
        :param dma_path: The DMA path of the Connector service
        :param headers: The extra headers to be used for requests to the service
        :param connection_manager: The connection manager to use for the service
        :return: An instance of the specified Service subclass
        """

        consumer = ServiceFactory.get_connector_consumer_service(
            dataspace_version=dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers,
            connection_manager=connection_manager,
            verbose=verbose,
            logger=logger
        )

        provider = ServiceFactory.get_connector_provider_service(
            dataspace_version=dataspace_version,
            base_url=base_url,
            dma_path=dma_path,
            headers=headers,
            verbose=verbose,
            logger=logger
        )

        builder = ServiceFactory._get_service_builder(
            service_type=ServiceType.CONNECTOR,
            dataspace_version=dataspace_version,
        )

        builder.dataspace_version(dataspace_version)
        builder.base_url(base_url)
        builder.dma_path(dma_path)
        builder.headers(headers)
        builder.consumer_service(consumer)
        builder.provider_service(provider)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()
