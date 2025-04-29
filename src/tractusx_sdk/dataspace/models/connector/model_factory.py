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

from .base_policy_model import BasePolicyModel
from .base_queryspec_model import BaseQuerySpecModel


class ModelType(Enum):
    """
    Enum for different model types. Each model type corresponds to a specific implementation,
    and must correspond exactly to the prefix of the model class it is associated with.
    """

    ASSET = "Asset"
    CATALOG = "Catalog"
    CONTRACT_DEFINITION = "ContractDefinition"
    CONTRACT_NEGOTIATION = "ContractNegotiation"
    POLICY = "Policy"
    QUERY_SPEC = "QuerySpec"
    TRANSFER_PROCESS = "TransferProcess"
    # TODO: Add any other existing model types


class ModelFactory:
    """
    Factory class to manage the creation of Model instances
    """
    # Dynamically load supported versions from the directory structure
    _models_base_path = path.dirname(__file__)
    SUPPORTED_VERSIONS = []
    for module in listdir(_models_base_path):
        module_path = path.join(_models_base_path, module)
        if path.isdir(module_path) and module.startswith("v"):
            SUPPORTED_VERSIONS.append(module)

    @staticmethod
    def _get_model_builder(
            model_type: ModelType,
            connector_version: str,
    ):
        """
        Instantiates a model builder, based on the specified model type and version.

        Different model types and versions may have different implementations and parameters, which should be the
        responsibility of the specific model class to handle. This factory method dynamically imports the correct
        model class, and returns a builder for it.

        :param model_type: The type of model to create, as per the ModelType enum
        :param connector_version: The version of the Connector (e.g., "v0_9_0")

        :return: An instance of the specified Model subclass' builder
        """

        # Check if the requested version is supported for the given model type
        if connector_version not in ModelFactory.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version {connector_version}")

        # Compute the model module path dynamically, depending on the connector version
        connector_module = ".".join(__name__.split(".")[0:-1])
        module_name = f"{connector_module}.{connector_version}"

        # Compute the model class name based on the model type
        model_class_name = f"{model_type.value}Model"

        try:
            # Dynamically import the model class
            module = import_module(module_name)
            model_class = getattr(module, model_class_name)

            # Return a builder for the model class
            return model_class.builder()
        except AttributeError as attr_exception:
            raise AttributeError(
                f"Failed to import model class {model_class_name} for module {module_name}"
            ) from attr_exception
        except (ModuleNotFoundError, ImportError) as import_exception:
            raise ImportError(
                f"Failed to import module {module_name}. Ensure that the required packages are installed and the PYTHONPATH is set correctly."
            ) from import_exception

    @staticmethod
    def get_asset_model(
            connector_version: str,
            oid: str,
            data_address: dict,
            context: dict | list | str = None,
            properties: dict = None,
            private_properties: dict = None,
            **kwargs
    ):
        """
        Create an Asset model instance for a specific version.

        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :param oid: The unique identifier for the asset
        :param data_address: The data address associated with the asset
        :param context: Optional context dictionary
        :param properties: Optional properties dictionary
        :param private_properties: Optional private properties dictionary
        :param kwargs: Any additional parameters, other than the base asset model parameters

        :return: An instance of the AssetModel subclass
        """
        builder = ModelFactory._get_model_builder(ModelType.ASSET, connector_version)

        # Add the required parameters
        builder.id(oid)
        builder.data_address(data_address)

        # Check for the optional parameters
        if context is not None:
            builder.context(context)

        if properties is not None:
            builder.properties(properties)

        if private_properties is not None:
            builder.private_properties(private_properties)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_catalog_model(
            connector_version: str,
            counter_party_address: str,
            counter_party_id: str,
            context: dict | list | str = None,
            additional_scopes: list = None,
            queryspec_model: BaseQuerySpecModel = None,
            queryspec: dict = None,
            **kwargs
    ):
        """
        Create a Catalog model instance for a specific version.

        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :param counter_party_address: The address of the counterparty
        :param counter_party_id: The ID of the counterparty
        :param context: Optional context dictionary
        :param additional_scopes: Optional list of additional scopes
        :param queryspec_model: Optional queryspec, as a QuerySpecModel instance.
            It takes precedence over queryspec
        :param queryspec: Optional queryspec, in dict format.
            Ignored if queryspec_model is provided
        :param kwargs: Any additional parameters, other than the base catalog model parameters

        :return: An instance of the CatalogModel subclass
        """
        builder = ModelFactory._get_model_builder(ModelType.CATALOG, connector_version)

        # Add the required parameters
        builder.counter_party_address(counter_party_address)
        builder.counter_party_id(counter_party_id)

        # Check for the optional parameters
        if context is not None:
            builder.context(context)

        if additional_scopes is not None:
            builder.additional_scopes(additional_scopes)

        if queryspec_model is not None:
            builder.queryspec_from_queryspec_model(queryspec_model)
        elif queryspec is not None:
            builder.queryspec(queryspec)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_definition_model(
            connector_version: str,
            oid: str,
            access_policy_id: str,
            contract_policy_id: str,
            context: dict | list | str = None,
            assets_selector: list = None,
            **kwargs
    ):
        """
        Create a Contract Definition model instance for a specific version.

        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :param oid: The unique identifier for the contract definition
        :param access_policy_id: The ID of the access policy
        :param contract_policy_id: The ID of the contract policy
        :param context: Optional context dictionary
        :param assets_selector: Optional list of assets selector
        :param kwargs: Any additional parameters, other than the base contract definition model parameters

        :return: An instance of the ContractDefinitionModel subclass
        """
        builder = ModelFactory._get_model_builder(ModelType.CONTRACT_DEFINITION, connector_version)

        # Add the required parameters
        builder.id(oid)
        builder.access_policy_id(access_policy_id)
        builder.contract_policy_id(contract_policy_id)

        # Check for the optional parameters
        if context is not None:
            builder.context(context)

        if assets_selector is not None:
            builder.assets_selector(assets_selector)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_contract_negotiation_model(
            connector_version: str,
            counter_party_address: str,
            offer_id: str,
            asset_id: str,
            provider_id: str,
            offer_policy_model: BasePolicyModel = None,
            offer_policy: dict = None,
            context: dict | list | str = None,
            callback_addresses: list = None,
            **kwargs
    ):
        """
        Create a Contract Negotiation model instance for a specific version.

        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :param counter_party_address: The address of the counterparty
        :param offer_id: The ID of the offer
        :param asset_id: The ID of the asset
        :param provider_id: The ID of the provider
        :param offer_policy_model: The policy associated with the offer, as a PolicyModel instance.
            It takes precedence over offer_policy.
            One of offer_policy_model or offer_policy must be provided
        :param offer_policy: The policy associated with the offer, in dict format.
            Ignored if offer_policy_model is provided.
            One of offer_policy_model or offer_policy must be provided
        :param context: Optional context dictionary
        :param callback_addresses: Optional list of callback addresses
        :param kwargs: Any additional parameters, other than the base contract negotiation model parameters

        :return: An instance of the ContractNegotiationModel subclass
        """
        builder = ModelFactory._get_model_builder(ModelType.CONTRACT_NEGOTIATION, connector_version)

        # Add the required parameters
        builder.counter_party_address(counter_party_address)
        builder.offer_id(offer_id)
        builder.asset_id(asset_id)
        builder.provider_id(provider_id)

        # Check for the optional parameters
        if offer_policy_model is not None:
            builder.offer_policy_from_policy_model(offer_policy_model)
        elif offer_policy is not None:
            builder.offer_policy(offer_policy)

        if context is not None:
            builder.context(context)

        if callback_addresses is not None:
            builder.callback_addresses(callback_addresses)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_policy_model(
            connector_version: str,
            oid: str,
            context: dict | list | str = None,
            permissions: dict | list[dict] = None,
            prohibitions: dict | list[dict] = None,
            obligations: dict | list[dict] = None,
            **kwargs
    ):
        """
        Create a Policy model instance for a specific version.

        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :param oid: The unique identifier for the policy
        :param context: Optional context dictionary
        :param permissions: Optional list of permissions
        :param prohibitions: Optional list of prohibitions
        :param obligations: Optional list of obligations
        :param kwargs: Any additional parameters, other than the base policy model parameters

        :return: An instance of the PolicyModel subclass
        """
        builder = ModelFactory._get_model_builder(ModelType.POLICY, connector_version)

        # Add the required parameters
        builder.id(oid)

        # Check for the optional parameters
        if context is not None:
            builder.context(context)

        if permissions is not None:
            builder.permissions(permissions)

        if prohibitions is not None:
            builder.prohibitions(prohibitions)

        if obligations is not None:
            builder.obligations(obligations)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()


    @staticmethod
    def get_queryspec_model(
            connector_version: str,
            context: dict | list | str = None,
            offset: int = 0,
            limit: int = 10,
            sort_order: str = "DESC",
            sort_field: str = "createdAt",
            filter_expression: list[dict] = None,
            **kwargs
    ):
        """
        Create a QuerySpec model instance for a specific version.

        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :param context: Optional context dictionary
        :param offset: Optional offset for pagination
        :param limit: Optional limit for pagination
        :param sort_order: Optional sort order (ASC or DESC)
        :param sort_field: Optional field to sort by
        :param filter_expression: Optional list of filter expressions
        :param kwargs: Any additional parameters, other than the base query spec model parameters

        :return: An instance of the QuerySpecModel subclass
        """
        builder = ModelFactory._get_model_builder(ModelType.QUERY_SPEC, connector_version)

        builder.offset(offset)
        builder.limit(limit)
        builder.sort_order(sort_order)
        builder.sort_field(sort_field)

        # Check for optional parameters
        if context is not None:
            builder.context(context)

        if filter_expression is not None:
            builder.filter_expression(filter_expression)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

    @staticmethod
    def get_transfer_process_model(
            connector_version: str,
            counter_party_address: str,
            transfer_type: str,
            contract_id: str,
            data_destination: dict,
            private_properties: dict = None,
            callback_addresses: list[dict] = None,
            context: dict | list | str = None,
            **kwargs
    ):
        """
        Create a TransferProcess model instance for a specific version.

        :param connector_version: The version of the Connector (e.g., "v0_9_0")
        :param counter_party_address: The address of the counterparty
        :param transfer_type: The type of transfer
        :param contract_id: The ID of the contract
        :param data_destination: The destination of the data
        :param private_properties: Optional private properties dictionary
        :param callback_addresses: Optional list of callback addresses
        :param context: Optional context dictionary
        :param kwargs: Any additional parameters, other than the base transfer process model parameters

        :return: An instance of the TransferProcessModel subclass
        """
        builder = ModelFactory._get_model_builder(ModelType.TRANSFER_PROCESS, connector_version)

        # Add the required parameters
        builder.counter_party_address(counter_party_address)
        builder.transfer_type(transfer_type)
        builder.contract_id(contract_id)
        builder.data_destination(data_destination)

        # Check for optional parameters
        if private_properties is not None:
            builder.private_properties(private_properties)

        if callback_addresses is not None:
            builder.callback_addresses(callback_addresses)

        if context is not None:
            builder.context(context)

        # Include any additional parameters
        builder.data(kwargs)
        return builder.build()

