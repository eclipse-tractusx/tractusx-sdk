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

import unittest

from tractusx_sdk.dataspace.services.connector.service_factory import ServiceFactory
from unittest import mock
import tractusx_sdk.dataspace.services.connector.base_connector_consumer as bcc
from tractusx_sdk.dataspace.constants import JSONLDKeys, ODRLTypes
class TestBaseConsumerConnectorService(unittest.TestCase):
    def setUp(self):
        self.dataspace_version = "jupiter"
        self.base_url = "http://consumer-control.plane.url"
        self.dma_path = "/management"
        self.headers = {"X-Api-Key": "api-key-secret", "Content-Type": "application/json"}

        self.service = bcc.BaseConnectorConsumerService(
            dataspace_version=self.dataspace_version,
            base_url=self.base_url,
            dma_path=self.dma_path,
            headers=self.headers
        )

    def test_do_get_to_dtr(self):
        """Test the do_get method."""
        # Mock the do_get method to avoid real HTTP/network calls
        with mock.patch.object(self.service, "do_get") as mock_do_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_do_get.return_value = mock_response
            import requests
            session = requests.Session()
            response = self.service.do_get(
                session=session,
                counter_party_address="http://provider-control.plane.url",
                counter_party_id="<provider-bpn>",
                filter_expression=[
                    self.service.get_filter_expression(
                        key=f"'http://purl.org/dc/terms/type'.'{JSONLDKeys.AT_ID}'",
                        operator=ODRLTypes.EQUALS,
                        value="https://w3id.org/catenax/taxonomy#DigitalTwinRegistry"
                    )
                ],
                path="/shell-descriptors",
                policies=[
                    {
                        "odrl:permission": {
                            "odrl:action": {
                                "@id": "odrl:use"
                            },
                            "odrl:constraint": {
                                "odrl:and": [
                                    {
                                        "odrl:leftOperand": {
                                            "@id": "cx-policy:FrameworkAgreement"
                                        },
                                        "odrl:operator": {
                                            "@id": "odrl:eq"
                                        },
                                        "odrl:rightOperand": "DataExchangeGovernance:1.0"
                                    },
                                    {
                                        "odrl:leftOperand": {
                                            "@id": "cx-policy:Membership"
                                        },
                                        "odrl:operator": {
                                            "@id": "odrl:eq"
                                        },
                                        "odrl:rightOperand": "active"
                                    },
                                    {
                                        "odrl:leftOperand": {
                                            "@id": "cx-policy:UsagePurpose"
                                        },
                                        "odrl:operator": {
                                            "@id": "odrl:eq"
                                        },
                                        "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"
                                    }
                                ]
                            }
                        },
                        "odrl:prohibition": [],
                        "odrl:obligation": []
                    }
                ]
            )
            self.assertIsNotNone(response)
            self.assertEqual(response.status_code, 200)
        
    def create_mock_service(self):
        # Helper to create a mock BaseConnectorConsumerService with mocked controllers
        mock_catalog = mock.Mock()
        mock_edr = mock.Mock()
        mock_contract_negotiation = mock.Mock()
        mock_transfer_process = mock.Mock()

        service = bcc.BaseConnectorConsumerService(
            dataspace_version="jupiter",
            base_url="http://test",
            dma_path="/test",
            headers={},
            connection_manager=None,
            verbose=False,
            logger=None
        )
        service._catalog_controller = mock_catalog
        service._edr_controller = mock_edr
        service._contract_negotiation_controller = mock_contract_negotiation
        service._transfer_process_controller = mock_transfer_process
        return service, mock_catalog, mock_edr, mock_contract_negotiation, mock_transfer_process

    def test_get_data_plane_headers_with_content_type(self):
        service, *_ = self.create_mock_service()
        headers = service.get_data_plane_headers("token", content_type="application/json")
        self.assertEqual(headers["Authorization"], "token")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "*/*")

    def test_get_data_plane_headers_without_content_type(self):
        service, *_ = self.create_mock_service()
        headers = service.get_data_plane_headers("token")
        self.assertEqual(headers["Authorization"], "token")
        self.assertNotIn("Content-Type", headers)

    def test_get_filter_expression(self):
        service, *_ = self.create_mock_service()
        expr = service.get_filter_expression("foo", "bar", operator="!=")
        self.assertEqual(expr, {ODRLTypes.OPERAND_LEFT: "foo", ODRLTypes.OPERATOR: "!=", ODRLTypes.OPERAND_RIGHT: "bar"})

    def test_get_query_spec(self):
        service, *_ = self.create_mock_service()
        filter_expr = [{ODRLTypes.OPERAND_LEFT: "foo", ODRLTypes.OPERATOR: "=", ODRLTypes.OPERAND_RIGHT: "bar"}]
        spec = service.get_query_spec(filter_expr)
        self.assertEqual(spec["@type"], "QuerySpec")
        self.assertEqual(spec["filterExpression"], filter_expr)

    def test_get_catalog_request_with_filter(self):
        service, *_ = self.create_mock_service()
        mock_catalog_model = mock.Mock()
        service.get_catalog_request = mock.Mock(return_value=mock_catalog_model)
        filter_expr = [{ODRLTypes.OPERAND_LEFT: "foo", ODRLTypes.OPERATOR: "=", ODRLTypes.OPERAND_RIGHT: "bar"}]
        result = service.get_catalog_request_with_filter("bpn", "url", filter_expr)
        self.assertEqual(result.queryspec["filterExpression"], filter_expr)

    def test_get_catalog_raises_value_error(self):
        service, *_ = self.create_mock_service()
        with self.assertRaises(ValueError):
            service.get_catalog()

    def test_get_catalog_success(self):
        service, mock_catalog, *_ = self.create_mock_service()
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"catalog": "data"}
        mock_catalog.get_catalog = mock.Mock(return_value=mock_response)
        mock_request = mock.Mock()
        service.get_catalog_request = mock.Mock(return_value=mock_request)
        result = service.get_catalog(counter_party_id="bpn", counter_party_address="url")
        self.assertEqual(result, {"catalog": "data"})

    def test_get_edr_success(self):
        service, _, mock_edr, *_ = self.create_mock_service()
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"endpoint": "url", "authorization": "token"}
        mock_edr.get_data_address = mock.Mock(return_value=mock_response)
        result = service.get_edr("transfer_id")
        self.assertEqual(result["endpoint"], "url")

    def test_get_edr_failure(self):
        service, _, mock_edr, *_ = self.create_mock_service()
        mock_edr.get_data_address = mock.Mock(return_value=None)
        with self.assertRaises(ConnectionError):
            service.get_edr("transfer_id")

    def test_get_endpoint_with_token_success(self):
        service, *_ = self.create_mock_service()
        service.get_edr = mock.Mock(return_value={"endpoint": "url", "authorization": "token"})
        endpoint, token = service.get_endpoint_with_token("transfer_id")
        self.assertEqual(endpoint, "url")
        self.assertEqual(token, "token")

    def test_get_endpoint_with_token_failure(self):
        service, *_ = self.create_mock_service()
        service.get_edr = mock.Mock(return_value=None)
        with self.assertRaises(RuntimeError):
            service.get_endpoint_with_token("transfer_id")

    def test_do_get_no_dataplane_url(self):
        service, *_ = self.create_mock_service()
        service.do_dsp = mock.Mock(return_value=(None, None))
        with self.assertRaises(RuntimeError):
            service.do_get(
                counter_party_id="bpn",
                counter_party_address="url",
                filter_expression=[{"foo": "bar"}]
            )

    # Additional tests for coverage and regression

    def test_get_catalog_request_returns_model(self):
        service, *_ = self.create_mock_service()
        # Patch ModelFactory.get_catalog_model to return a mock
        with mock.patch("tractusx_sdk.dataspace.services.connector.base_connector_consumer.ModelFactory.get_catalog_model") as m:
            m.return_value = mock.Mock()
            result = service.get_catalog_request("bpn", "url")
            self.assertTrue(m.called)
            self.assertIsNotNone(result)

    def test_get_edr_negotiation_request_missing_id(self):
        service, *_ = self.create_mock_service()
        with self.assertRaises(ValueError):
            service.get_edr_negotiation_request("bpn", "url", "target", {})

    def test_get_edr_negotiation_request_success(self):
        service, *_ = self.create_mock_service()
        with mock.patch("tractusx_sdk.dataspace.services.connector.base_connector_consumer.ModelFactory.get_contract_negotiation_model") as m:
            m.return_value = mock.Mock()
            policy = {"@id": "offer1"}
            result = service.get_edr_negotiation_request("bpn", "url", "target", policy)
            self.assertTrue(m.called)
            self.assertIsNotNone(result)

    def test_get_catalog_by_dct_type_calls_get_catalog_with_filter(self):
        service, *_ = self.create_mock_service()
        service.get_catalog_with_filter = mock.Mock(return_value={"catalog": "data"})
        result = service.get_catalog_by_dct_type("bpn", "url", "dct_type")
        self.assertEqual(result, {"catalog": "data"})

    def test_get_catalog_with_filter_calls_get_catalog(self):
        service, *_ = self.create_mock_service()
        service.get_catalog = mock.Mock(return_value={"catalog": "data"})
        filter_expr = [{ODRLTypes.OPERAND_LEFT: "foo", ODRLTypes.OPERATOR: "=", ODRLTypes.OPERAND_RIGHT: "bar"}]
        result = service.get_catalog_with_filter("bpn", "url", filter_expr)
        self.assertEqual(result, {"catalog": "data"})

    def test_get_query_spec_structure(self):
        service, *_ = self.create_mock_service()
        filter_expr = [{ODRLTypes.OPERAND_LEFT: "foo", ODRLTypes.OPERATOR: "=", ODRLTypes.OPERAND_RIGHT: "bar"}]
        spec = service.get_query_spec(filter_expr)
        self.assertIn("@context", spec)
        self.assertIn("@type", spec)
        self.assertIn("filterExpression", spec)

    def test_get_filter_expression_default_operator(self):
        service, *_ = self.create_mock_service()
        expr = service.get_filter_expression("foo", "bar")
        self.assertEqual(expr[ODRLTypes.OPERATOR], "=")

    def test_get_data_plane_headers_accept(self):
        service, *_ = self.create_mock_service()
        headers = service.get_data_plane_headers("token")
        self.assertEqual(headers["Accept"], "*/*")

    def test_get_data_plane_headers_content_type(self):
        service, *_ = self.create_mock_service()
        headers = service.get_data_plane_headers("token", content_type="application/xml")
        self.assertEqual(headers["Content-Type"], "application/xml")
