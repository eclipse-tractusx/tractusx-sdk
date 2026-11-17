#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
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
The values of the ``operation`` field of the log records of the SDK.

An operation is ``<area>.<step>``: the area is where the record comes from (``consumer``, ``oauth2``...) and the step
is what it reports. The name of a constant is its value in upper case, with the dot as an underscore. Private to the
SDK: it is not part of the public API.
"""


class LogOperations:
    """The operations a log record of the SDK can report."""

    # adapter_factory
    ADAPTER_FACTORY = "adapter_factory"
    ADAPTER_FACTORY_FROM_CONFIG = "adapter_factory.from_config"
    ADAPTER_FACTORY_GET_BUILDER = "adapter_factory.get_builder"
    ADAPTER_FACTORY_REGISTER = "adapter_factory.register"
    ADAPTER_FACTORY_UNREGISTER = "adapter_factory.unregister"

    # auth
    AUTH_ADD_AUTH_HEADER = "auth.add_auth_header"
    AUTH_IS_AUTHENTICATED = "auth.is_authenticated"

    # bpn_discovery
    BPN_DISCOVERY_DELETE_IDENTIFIER = "bpn_discovery.delete_identifier"
    BPN_DISCOVERY_FIND_BPNS = "bpn_discovery.find_bpns"
    BPN_DISCOVERY_FIND_BPNS_MULTI_TYPE = "bpn_discovery.find_bpns_multi_type"
    BPN_DISCOVERY_GET_URL = "bpn_discovery.get_url"
    BPN_DISCOVERY_REQUEST = "bpn_discovery.request"
    BPN_DISCOVERY_SEARCH = "bpn_discovery.search"
    BPN_DISCOVERY_SEARCH_MULTI_TYPE = "bpn_discovery.search_multi_type"
    BPN_DISCOVERY_SET_IDENTIFIER = "bpn_discovery.set_identifier"
    BPN_DISCOVERY_SET_MULTIPLE_IDENTIFIERS = "bpn_discovery.set_multiple_identifiers"

    # consumer
    CONSUMER_ASSETS_EXISTS = "consumer.assets_exists"
    CONSUMER_CHECK_NEGOTIATION_STATE = "consumer.check_negotiation_state"
    CONSUMER_DATAPLANE_CALL = "consumer.dataplane_call"
    CONSUMER_DISCOVER_CONNECTOR_PROTOCOL = "consumer.discover_connector_protocol"
    CONSUMER_EXECUTE_HTTP_REQUEST = "consumer.execute_http_request"
    CONSUMER_FETCH_AND_VALIDATE_CATALOG = "consumer.fetch_and_validate_catalog"
    CONSUMER_GET_AGREEMENT_ID = "consumer.get_agreement_id"
    CONSUMER_GET_CATALOG = "consumer.get_catalog"
    CONSUMER_GET_CATALOG_WITH_FILTER_PARALLEL = "consumer.get_catalog_with_filter_parallel"
    CONSUMER_GET_CATALOGS_WITH_FILTER = "consumer.get_catalogs_with_filter"
    CONSUMER_GET_CATALOGS_WITH_FILTER_WITH_BPNL = "consumer.get_catalogs_with_filter_with_bpnl"
    CONSUMER_GET_CATALOGS_WITH_FILTER_WITH_BPNL_PARALLEL = "consumer.get_catalogs_with_filter_with_bpnl_parallel"
    CONSUMER_GET_DISCOVERY_INFO = "consumer.get_discovery_info"
    CONSUMER_GET_EDR = "consumer.get_edr"
    CONSUMER_GET_EDR_ENTRY = "consumer.get_edr_entry"
    CONSUMER_GET_EDR_NEGOTIATION_REQUEST = "consumer.get_edr_negotiation_request"
    CONSUMER_GET_ENDPOINT_WITH_TOKEN = "consumer.get_endpoint_with_token"
    CONSUMER_GET_TRANSFER_ID = "consumer.get_transfer_id"
    CONSUMER_GET_TRANSFER_PROCESS = "consumer.get_transfer_process"
    CONSUMER_NEGOTIATE_AND_TRANSFER = "consumer.negotiate_and_transfer"
    CONSUMER_POLL_NEGOTIATION_STATE = "consumer.poll_negotiation_state"
    CONSUMER_RESOLVE_POLICIES_FROM_CATALOG = "consumer.resolve_policies_from_catalog"
    CONSUMER_START_EDR_NEGOTIATION = "consumer.start_edr_negotiation"
    CONSUMER_START_NEGOTIATION_FOR_ASSETS = "consumer.start_negotiation_for_assets"
    CONSUMER_WAIT_FOR_EDR_ENTRY = "consumer.wait_for_edr_entry"
    CONSUMER_WAIT_FOR_TRANSFER_PROCESS = "consumer.wait_for_transfer_process"

    # discovery
    DISCOVERY_CACHE_HIT = "discovery.cache_hit"
    DISCOVERY_CONNECTOR = "discovery.connector"
    DISCOVERY_FIND_CONNECTOR_BY_BPN = "discovery.find_connector_by_bpn"
    DISCOVERY_FIND_URLS = "discovery.find_urls"
    DISCOVERY_REFRESH = "discovery.refresh"

    # fs
    FS_DELETE = "fs.delete"
    FS_EXISTS = "fs.exists"
    FS_LIST = "fs.list"
    FS_READ = "fs.read"
    FS_WRITE = "fs.write"
    FS_WRITE_JSON = "fs.write_json"

    # geometry
    GEOMETRY_BUILD_MAP = "geometry.build_map"
    GEOMETRY_LOAD_FILE = "geometry.load_file"
    GEOMETRY_LOAD_SCHEMA = "geometry.load_schema"
    GEOMETRY_VALIDATE = "geometry.validate"
    GEOMETRY_VALIDATE_FILE = "geometry.validate_file"

    # model_factory
    MODEL_FACTORY_FROM_PROTOCOL = "model_factory.from_protocol"
    MODEL_FACTORY_GET_BUILDER = "model_factory.get_builder"
    MODEL_FACTORY_GET_CONNECTOR_DISCOVERY_MODEL = "model_factory.get_connector_discovery_model"

    # notification
    NOTIFICATION_DISCOVER_ASSETS = "notification.discover_assets"
    NOTIFICATION_DISCOVER_ASSETS_BPNL = "notification.discover_assets_bpnl"
    NOTIFICATION_ENSURE_ASSET = "notification.ensure_asset"
    NOTIFICATION_ENSURE_CONSUMER = "notification.ensure_consumer"
    NOTIFICATION_FIND_ASSET = "notification.find_asset"
    NOTIFICATION_GET_ENDPOINT = "notification.get_endpoint"
    NOTIFICATION_GET_ENDPOINT_BPNL = "notification.get_endpoint_bpnl"
    NOTIFICATION_NEGOTIATE_ACCESS = "notification.negotiate_access"
    NOTIFICATION_NEGOTIATE_ACCESS_BPNL = "notification.negotiate_access_bpnl"
    NOTIFICATION_SEND = "notification.send"
    NOTIFICATION_SEND_BPNL = "notification.send_bpnl"
    NOTIFICATION_SEND_TO_ENDPOINT = "notification.send_to_endpoint"
    NOTIFICATION_SEND_TO_MANY = "notification.send_to_many"
    NOTIFICATION_VALIDATE = "notification.validate"

    # oauth2
    OAUTH2_ADD_AUTH_HEADER = "oauth2.add_auth_header"
    OAUTH2_CONNECT = "oauth2.connect"
    OAUTH2_GET_TOKEN = "oauth2.get_token"
    OAUTH2_IS_AUTHENTICATED = "oauth2.is_authenticated"

    # provider
    PROVIDER_CREATE_ASSET = "provider.create_asset"
    PROVIDER_CREATE_CONTRACT = "provider.create_contract"
    PROVIDER_CREATE_POLICY = "provider.create_policy"

    # s3
    S3_DELETE = "s3.delete"
    S3_EXISTS = "s3.exists"
    S3_LIST = "s3.list"
    S3_READ = "s3.read"
    S3_WRITE = "s3.write"
    S3_WRITE_JSON = "s3.write_json"

    # semantics
    SEMANTICS_CREATE_ARRAY_NODE = "semantics.create_array_node"
    SEMANTICS_CREATE_NODE = "semantics.create_node"
    SEMANTICS_CREATE_NODE_PROPERTY = "semantics.create_node_property"
    SEMANTICS_CREATE_OBJECT_NODE = "semantics.create_object_node"
    SEMANTICS_CREATE_SINGLE_PROPERTIES_CONTEXT = "semantics.create_single_properties_context"
    SEMANTICS_FETCH = "semantics.fetch"
    SEMANTICS_GET_SCHEMA_REF = "semantics.get_schema_ref"
    SEMANTICS_PREPARE = "semantics.prepare"
    SEMANTICS_SCHEMA_TO_JSONLD = "semantics.schema_to_jsonld"
    SEMANTICS_SCHEMA_TO_JSONLD_NESTED = "semantics.schema_to_jsonld_nested"

    # service
    SERVICE_BUILD = "service.build"

    # validate
    VALIDATE_JSON_VALIDATOR = "validate.json_validator"
    VALIDATE_SCHEMA_FINDER = "validate.schema_finder"
