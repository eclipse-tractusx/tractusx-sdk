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


class AdapterType(Enum):
    """
    Enum for different adapter types. Each adapter type corresponds to a specific implementation,
    and must correspond exactly to the prefix of the adapter class it is associated with.
    """

    DMA_ADAPTER = "Dma"
    DATAPLANE_ADAPTER = "Dataplane"
    # TODO: Add any other existing adapter types


class AdapterFactory:
    """
    Factory class to manage the creation of Adapter instances
    """
    # Dynamically load supported versions from the directory structure
    _adapters_base_path = path.dirname(__file__)
    SUPPORTED_VERSIONS = []
    for module in listdir(_adapters_base_path):
        module_path = path.join(_adapters_base_path, module)
        if path.isdir(module_path) and module.startswith("v"):
            SUPPORTED_VERSIONS.append(module)

    @staticmethod
    def _get_adapter_builder(
            adapter_type: AdapterType,
            connector_version: str,
    ):
        """
        Create an adapter, based on the specified adapter type and version.

        Different adapter types and versions may have different implementations and parameters, which should be the
        responsibility of the specific adapter class to handle. This factory method dynamically imports the correct
        adapter class, and returns it, with whatever parameters necessary for its initialization.

        :param adapter_type: The type of adapter to create, as per the AdapterType enum
        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :return: An instance of the specified Adapter subclass
        """

        # Check if the requested version is supported for the given adapter type
        if connector_version not in AdapterFactory.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version {connector_version}")

        # Compute the adapter module path dynamically, depending on the connector version
        connector_module = ".".join(__name__.split(".")[0:-1])
        module_name = f"{connector_module}.{connector_version}"

        # Compute the adapter class name based on the adapter type
        adapter_class_name = f"{adapter_type.value}Adapter"

        try:
            # Dynamically import the adapter class
            module = import_module(module_name)
            adapter_class = getattr(module, adapter_class_name)
            return adapter_class.builder()
        except AttributeError as attr_exception:
            raise AttributeError(
                f"Failed to import adapter class {adapter_class_name} for module {module_name}"
            ) from attr_exception
        except (ModuleNotFoundError, ImportError) as import_exception:
            raise ImportError(
                f"Failed to import module {module_name}. Ensure that the required packages are installed and the PYTHONPATH is set correctly."
            ) from import_exception

    @staticmethod
    def get_dma_adapter(
            connector_version: str,
            base_url: str,
            dma_path: str,
            headers: dict = None,
            **kwargs
    ):
        """
        Create a (DMA) adapter instance, based a specific version.

        :param connector_version: The version of the Connector DMA (e.g., "v0_9_0")
        :param base_url: The URL of the Connector DMA to be requested
        :param dma_path: The path of the Connector Data Management API to be requested
        :param headers: The headers (i.e.: API Key) of the Connector to be requested
        :return: An instance of the specified Adapter subclass
        """

        builder = AdapterFactory._get_adapter_builder(
            adapter_type=AdapterType.DMA_ADAPTER,
            connector_version=connector_version,
        )

        builder.base_url(base_url)
        builder.headers(headers)
        builder.dma_path(dma_path)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_dataplane_adapter(
            connector_version: str,
            base_url: str,
            headers: dict = None,
            **kwargs
    ):
        """
        Create a dataplane adapter instance, based a specific version.

        :param connector_version: The version of the Connector dataplane (e.g., "v0_9_0")
        :param base_url: The URL of the Connector dataplane to be requested
        :param headers: The headers (i.e.: Edc-Bpn) of the Connector dataplane to be requested
        :return: An instance of the specified Adapter subclass
        """

        builder = AdapterFactory._get_adapter_builder(
            adapter_type=AdapterType.DATAPLANE_ADAPTER,
            connector_version=connector_version,
        )

        builder.base_url(base_url)
        builder.headers(headers)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()
