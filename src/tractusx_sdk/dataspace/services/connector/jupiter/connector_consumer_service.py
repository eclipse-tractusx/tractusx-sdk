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

from multiprocessing import context

from requests import Response
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
        "dct": "http://purl.org/dc/terms/",
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

    def do_get_with_bpnl(  # NOSONAR pylint: disable=too-many-arguments
        self,
        bpnl: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        policies: list = None,
        max_wait: int = 60,
        poll_interval: int = 1,
        verify: bool = False,
        headers: dict = {},
        timeout: int = None,
        params: dict = None,
        allow_redirects: bool = False,
        session=None,
        protocol: str = DSP_0_8,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: list = DEFAULT_NEGOTIATION_CONTEXT,
    ) -> Response:
        """
        Executes a HTTP GET request to an asset behind an EDC using BPNL as counter party ID.
        
        This is a convenience wrapper that uses the BPNL directly as the counter_party_id
        parameter when calling the parent class do_get method.

        @param bpnl: The Business Partner Number (BPN) of the provider.
        @param counter_party_address: The DSP URL of the EDC provider.
        @param filter_expression: Filter expressions for the catalog lookup.
        @param path: The path to be appended to the dataplane URL. Defaults to "/".
        @param policies: Optional list of accepted policies. ``None`` uses the base-class behaviour.
        @param max_wait: Maximum seconds to wait for negotiation / EDR availability. Defaults to 60.
        @param poll_interval: Seconds between status-poll attempts. Defaults to 1.
        @param verify: Whether to verify SSL certificates. Defaults to False.
        @param headers: Additional headers to include in the request. Defaults to {}.
        @param timeout: Request timeout in seconds. Defaults to None.
        @param params: URL parameters for the request. Defaults to None.
        @param allow_redirects: Whether to allow redirects. Defaults to False.
        @param session: Session object for connection pooling. Defaults to None.
        @param protocol: DSP protocol version. Defaults to ``"dataspace-protocol-http"`` (Jupiter legacy).
        @param catalog_context: JSON-LD context for catalog requests. Defaults to :attr:`DEFAULT_CONTEXT`.
        @param negotiation_context: JSON-LD context for negotiation requests. Defaults to :attr:`DEFAULT_NEGOTIATION_CONTEXT`.
        @returns: The HTTP response from the GET request.
        @raises RuntimeError: If the request fails or no dataplane URL/token can be retrieved.
        """
        # For Jupiter, BPNL is used directly as counter_party_id
        return super().do_get(
            counter_party_id=bpnl,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            path=path,
            policies=policies,
            verify=verify,
            headers=headers,
            timeout=timeout,
            params=params,
            allow_redirects=allow_redirects,
            session=session,
            max_wait=max_wait,
            poll_interval=poll_interval,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

    def do_post_with_bpnl(  # NOSONAR pylint: disable=too-many-arguments
        self,
        bpnl: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        content_type: str = "application/json",
        json=None,
        data=None,
        policies: list = None,
        max_wait: int = 60,
        poll_interval: int = 1,
        verify: bool = False,
        headers: dict = None,
        timeout: int = None,
        allow_redirects: bool = False,
        session=None,
        protocol: str = DSP_0_8,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: list = DEFAULT_NEGOTIATION_CONTEXT,
    ) -> Response:
        """
        Performs a HTTP POST request to an asset behind an EDC using BPNL as counter party ID.
        
        This is a convenience wrapper that uses the BPNL directly as the counter_party_id
        parameter when calling the parent class do_post method.

        @param bpnl: The Business Partner Number (BPN) of the provider.
        @param counter_party_address: The DSP URL of the EDC provider.
        @param filter_expression: Filter expressions for the catalog lookup.
        @param path: The path to be appended to the dataplane URL. Defaults to "/".
        @param content_type: The content type of the POST request. Defaults to "application/json".
        @param json: The JSON data to be sent in the POST request. Defaults to None.
        @param data: The data to be sent in the POST request. Defaults to None.
        @param policies: Optional list of accepted policies. ``None`` uses the base-class behaviour.
        @param max_wait: Maximum seconds to wait for negotiation / EDR availability. Defaults to 60.
        @param poll_interval: Seconds between status-poll attempts. Defaults to 1.
        @param verify: Whether to verify SSL certificates. Defaults to False.
        @param headers: Additional headers to include in the request. Defaults to None.
        @param timeout: Request timeout in seconds. Defaults to None.
        @param allow_redirects: Whether to allow redirects. Defaults to False.
        @param session: Session object for connection pooling. Defaults to None.
        @param protocol: DSP protocol version. Defaults to ``"dataspace-protocol-http"`` (Jupiter legacy).
        @param catalog_context: JSON-LD context for catalog requests. Defaults to :attr:`DEFAULT_CONTEXT`.
        @param negotiation_context: JSON-LD context for negotiation requests. Defaults to :attr:`DEFAULT_NEGOTIATION_CONTEXT`.
        @returns: The HTTP response from the POST request.
        @raises RuntimeError: If the request fails or no dataplane URL/token can be retrieved.
        """
        # For Jupiter, BPNL is used directly as counter_party_id
        return super().do_post(
            counter_party_id=bpnl,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            path=path,
            content_type=content_type,
            json=json,
            data=data,
            policies=policies,
            verify=verify,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            session=session,
            max_wait=max_wait,
            poll_interval=poll_interval,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )

    def do_put_with_bpnl(  # NOSONAR pylint: disable=too-many-arguments
        self,
        bpnl: str,
        counter_party_address: str,
        filter_expression: list[dict],
        path: str = "/",
        content_type: str = "application/json",
        json=None,
        data=None,
        policies: list = None,
        max_wait: int = 60,
        poll_interval: int = 1,
        verify: bool = False,
        headers: dict = None,
        timeout: int = None,
        allow_redirects: bool = False,
        session=None,
        protocol: str = DSP_0_8,
        catalog_context: dict = DEFAULT_CONTEXT,
        negotiation_context: list = DEFAULT_NEGOTIATION_CONTEXT,
    ) -> Response:
        """
        Performs a HTTP PUT request to an asset behind an EDC using BPNL as counter party ID.
        
        This is a convenience wrapper that uses the BPNL directly as the counter_party_id
        parameter when calling the parent class do_put method.

        @param bpnl: The Business Partner Number (BPN) of the provider.
        @param counter_party_address: The DSP URL of the EDC provider.
        @param filter_expression: Filter expressions for the catalog lookup.
        @param path: The path to be appended to the dataplane URL. Defaults to "/".
        @param content_type: The content type of the PUT request. Defaults to "application/json".
        @param json: The JSON data to be sent in the PUT request. Defaults to None.
        @param data: The data to be sent in the PUT request. Defaults to None.
        @param policies: Optional list of accepted policies. ``None`` uses the base-class behaviour.
        @param max_wait: Maximum seconds to wait for negotiation / EDR availability. Defaults to 60.
        @param poll_interval: Seconds between status-poll attempts. Defaults to 1.
        @param verify: Whether to verify SSL certificates. Defaults to False.
        @param headers: Additional headers to include in the request. Defaults to None.
        @param timeout: Request timeout in seconds. Defaults to None.
        @param allow_redirects: Whether to allow redirects. Defaults to False.
        @param session: Session object for connection pooling. Defaults to None.
        @param protocol: DSP protocol version. Defaults to ``"dataspace-protocol-http"`` (Jupiter legacy).
        @param catalog_context: JSON-LD context for catalog requests. Defaults to :attr:`DEFAULT_CONTEXT`.
        @param negotiation_context: JSON-LD context for negotiation requests. Defaults to :attr:`DEFAULT_NEGOTIATION_CONTEXT`.
        @returns: The HTTP response from the PUT request.
        @raises RuntimeError: If the request fails or no dataplane URL/token can be retrieved.
        """
        # For Jupiter, BPNL is used directly as counter_party_id
        return super().do_put(
            counter_party_id=bpnl,
            counter_party_address=counter_party_address,
            filter_expression=filter_expression,
            path=path,
            content_type=content_type,
            json=json,
            data=data,
            policies=policies,
            verify=verify,
            headers=headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            session=session,
            max_wait=max_wait,
            poll_interval=poll_interval,
            protocol=protocol,
            catalog_context=catalog_context,
            negotiation_context=negotiation_context
        )


    def get_catalog_by_asset_id_with_bpnl(
        self,
        bpnl: str,
        counter_party_address: str,
        asset_id: str,
        id_key: str = DEFAULT_ID_KEY,
        operator: str = "=",
        timeout: int = None,
        verify: bool = None,
        context: dict = DEFAULT_CONTEXT
    ) -> dict:
        """
        Retrieves a catalog filtered by a specific asset ID, using BPNL as counter party ID.

        This is a convenience wrapper for Jupiter protocol where the BPNL is used directly
        as the counter_party_id parameter when calling :meth:`get_catalog_by_asset_id`.

        @param bpnl: The Business Partner Number (BPN) of the provider.
        @param counter_party_address: The DSP URL of the EDC provider.
        @param asset_id: The asset ID to filter by.
        @param id_key: The operand key used to match the asset ID. Defaults to :attr:`DEFAULT_ID_KEY`.
        @param operator: The filter operator. Defaults to "=".
        @param timeout: Request timeout in seconds. Defaults to None.
        @param verify: Whether to verify SSL certificates. If None, uses service default.
        @param context: JSON-LD context for the catalog request. Defaults to :attr:`DEFAULT_CONTEXT`.
        @returns: The filtered EDC catalog as a dictionary.
        @raises Exception: If the catalog request fails.
        """
        # For Jupiter, BPNL is used directly as counter_party_id
        return super().get_catalog_by_asset_id(
            counter_party_id=bpnl,
            counter_party_address=counter_party_address,
            asset_id=asset_id,
            id_key=id_key,
            operator=operator,
            verify=verify,
            context=context,
            timeout=timeout
        )

    def get_catalog_by_dct_type_with_bpnl(
        self,
        bpnl: str,
        counter_party_address: str,
        dct_type: str,
        dct_type_key: str = DEFAULT_DCT_TYPE_KEY,
        operator: str = "=",
        timeout: int = None,
        context: dict = DEFAULT_CONTEXT
    ) -> dict:
        """
        Retrieves a catalog filtered by a specific DCT type, using BPNL as counter party ID.

        This is a convenience wrapper for Jupiter protocol where the BPNL is used directly
        as the counter_party_id parameter when calling :meth:`get_catalog_by_dct_type`.

        @param bpnl: The Business Partner Number (BPN) of the provider.
        @param counter_party_address: The DSP URL of the EDC provider.
        @param dct_type: The DCT type to filter by (e.g., "https://w3id.org/catenax/taxonomy#Submodel").
        @param dct_type_key: The operand key used to match the DCT type. Defaults to :attr:`DEFAULT_DCT_TYPE_KEY`.
        @param operator: The filter operator. Defaults to "=".
        @param timeout: Request timeout in seconds. Defaults to None.
        @param context: JSON-LD context for the catalog request. Defaults to :attr:`DEFAULT_CONTEXT`.
        @returns: The filtered EDC catalog as a dictionary.
        @raises Exception: If the catalog request fails.
        """
        # For Jupiter, BPNL is used directly as counter_party_id
        return super().get_catalog_by_dct_type(
            counter_party_id=bpnl,
            counter_party_address=counter_party_address,
            dct_type=dct_type,
            dct_type_key=dct_type_key,
            operator=operator,
            timeout=timeout,
            context=context
        )
