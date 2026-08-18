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
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

"""End-to-end tests of the optional `trace` option of the SDK services."""

import json
import unittest
from unittest.mock import patch

import requests

from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService
from tractusx_sdk.dataspace.tools.tracing import REDACTED_VALUE, Tracer
from tractusx_sdk.industry.services.aas_service import AasService


def build_response(body: dict = None, status_code: int = 200) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.reason = "OK"
    response.headers["Content-Type"] = "application/json"
    response._content = json.dumps(body if body is not None else {}).encode()
    return response


def connector_service(**kwargs):
    return ServiceFactory.get_connector_provider_service(
        dataspace_version="jupiter",
        base_url="https://connector.example.com",
        dma_path="/management",
        headers={"X-Api-Key": "secret"},
        verbose=False,
        **kwargs
    )


class TestConnectorServiceTracing(unittest.TestCase):
    @patch("requests.Session.request")
    def test_no_trace_by_default(self, mock_request):
        mock_request.return_value = build_response()
        service = connector_service()

        service.assets.get_all()

        self.assertFalse(service.trace_enabled)
        self.assertEqual([], service.get_trace())

    @patch("requests.Session.request")
    def test_trace_true_records_the_connector_calls(self, mock_request):
        mock_request.return_value = build_response({"result": "ok"})
        service = connector_service(trace=True)

        service.assets.get_all()

        trace = service.get_trace()
        self.assertEqual(1, len(trace))
        self.assertEqual("POST", trace[0]["request"]["method"])
        self.assertEqual(
            "https://connector.example.com/management/v3/assets/request",
            trace[0]["request"]["url"],
        )
        self.assertEqual({"result": "ok"}, trace[0]["response"]["body"])
        # The trace can be parsed as JSON
        self.assertEqual(1, json.loads(service.get_trace_json())["count"])

    @patch("requests.Session.request")
    def test_connector_service_traces_provider_and_consumer(self, mock_request):
        """Both sides of the connector service write into the same trace."""
        mock_request.return_value = build_response()
        service = ServiceFactory.get_connector_service(
            dataspace_version="jupiter",
            base_url="https://connector.example.com",
            dma_path="/management",
            verbose=False,
            trace=True,
        )

        service.provider.assets.get_all()
        service.provider.policies.get_all()
        service.consumer.contract_negotiations.get_all()
        service.contract_agreements.get_all()

        self.assertIs(service.tracer, service.provider.tracer)
        self.assertIs(service.tracer, service.consumer.tracer)
        self.assertEqual(
            [
                "https://connector.example.com/management/v3/assets/request",
                "https://connector.example.com/management/v3/policydefinitions/request",
                "https://connector.example.com/management/v3/contractnegotiations/request",
                "https://connector.example.com/management/v3/contractagreements/request",
            ],
            [entry["request"]["url"] for entry in service.get_trace()],
        )

    @patch("requests.Session.request")
    def test_connector_service_without_trace(self, mock_request):
        mock_request.return_value = build_response()
        service = ServiceFactory.get_connector_service(
            dataspace_version="jupiter",
            base_url="https://connector.example.com",
            dma_path="/management",
            verbose=False,
        )

        service.provider.assets.get_all()

        self.assertFalse(service.trace_enabled)
        self.assertIsNone(service.provider.tracer)
        self.assertIsNone(service.consumer.tracer)

    @patch("requests.Session.request")
    def test_an_existing_tracer_can_be_shared(self, mock_request):
        mock_request.return_value = build_response()
        tracer = Tracer(name="my-flow")
        service = connector_service()

        service.set_tracer(tracer)
        service.assets.get_all()

        self.assertIs(tracer, service.tracer)
        self.assertEqual("my-flow", json.loads(service.get_trace_json())["name"])

    @patch("requests.Session.request")
    def test_the_trace_of_a_service_can_be_filtered(self, mock_request):
        mock_request.side_effect = [build_response(), build_response(status_code=500, body={"error": "boom"})]
        service = connector_service(trace=True)

        service.assets.get_all()
        service.policies.get_all()

        self.assertEqual(2, len(service.get_trace()))
        self.assertEqual(1, len(service.get_trace(failed=True)))
        self.assertEqual(
            "https://connector.example.com/management/v3/policydefinitions/request",
            service.get_trace(failed=True)[0]["request"]["url"],
        )
        self.assertEqual(1, len(service.get_trace(url="/assets")))
        self.assertEqual(2, len(service.get_trace(method="POST")))

    @patch("requests.Session.request")
    def test_trace_can_be_enabled_and_cleared_at_runtime(self, mock_request):
        mock_request.return_value = build_response()
        service = connector_service()

        service.enable_trace()
        service.assets.get_all()
        self.assertEqual(1, len(service.get_trace()))

        service.clear_trace()
        service.disable_trace()
        service.assets.get_all()
        self.assertEqual([], service.get_trace())


class TestTracerPropagation(unittest.TestCase):
    """The tracer reaches everything a service is built upon, without any wiring."""

    @patch("requests.Session.request")
    def test_the_adapter_and_controllers_share_the_service_tracer(self, mock_request):
        mock_request.return_value = build_response()
        service = connector_service(trace=True)

        self.assertIs(service.tracer, service.dma_adapter.tracer)
        self.assertIs(service.tracer, service.assets.adapter.tracer)

    @patch("requests.Session.request")
    def test_every_adapter_of_a_service_is_covered(self, mock_request):
        """Saturn builds a second adapter for its connector discovery controller."""
        mock_request.return_value = build_response()
        service = ServiceFactory.get_connector_consumer_service(
            dataspace_version="saturn",
            base_url="https://connector.example.com",
            dma_path="/management",
            verbose=False,
            trace=True,
        )

        discovery_adapter = service.connector_discovery.adapter
        self.assertIsNot(discovery_adapter, service.dma_adapter)
        self.assertIs(service.tracer, discovery_adapter.tracer)

    @patch("requests.Session.request")
    def test_set_tracer_walks_the_whole_service(self, mock_request):
        mock_request.return_value = build_response()
        tracer = Tracer(name="shared")
        service = ServiceFactory.get_connector_consumer_service(
            dataspace_version="saturn",
            base_url="https://connector.example.com",
            dma_path="/management",
            verbose=False,
        )

        service.set_tracer(tracer)

        self.assertIs(tracer, service.dma_adapter.tracer)
        self.assertIs(tracer, service.connector_discovery.adapter.tracer)

        # ... and stops it everywhere as well
        service.set_tracer(None)
        self.assertIsNone(service.dma_adapter.tracer)
        self.assertIsNone(service.connector_discovery.adapter.tracer)


class TestDataplaneTracing(unittest.TestCase):
    """Calls made without the adapter (the dataplane) are traced through HttpTools."""

    @patch("requests.get")
    @patch("requests.Session.request")
    def test_dataplane_calls_are_part_of_the_trace(self, mock_request, mock_get):
        mock_request.return_value = build_response()
        mock_get.return_value = build_response({"payload": "from the dataplane"})
        service = ServiceFactory.get_connector_consumer_service(
            dataspace_version="jupiter",
            base_url="https://connector.example.com",
            dma_path="/management",
            verbose=False,
            trace=True,
        )

        with patch.object(
            type(service), "do_dsp", return_value=("https://dataplane.example.com", "edr-token")
        ):
            service.do_get(
                counter_party_id="BPNL000000000000",
                counter_party_address="https://provider.example.com/api/v1/dsp",
                filter_expression=[],
                path="/data",
            )

        trace = service.get_trace()
        self.assertEqual(1, len(trace))
        self.assertEqual("https://dataplane.example.com/data", trace[0]["request"]["url"])
        # The EDR token never ends up in the trace
        self.assertEqual(REDACTED_VALUE, trace[0]["request"]["headers"]["Authorization"])
        self.assertEqual({"payload": "from the dataplane"}, trace[0]["response"]["body"])


class TestSharedTracing(unittest.TestCase):
    @patch("requests.Session.get")
    @patch("requests.Session.request")
    def test_one_tracer_for_several_services(self, mock_request, mock_get):
        mock_request.return_value = build_response()
        mock_get.return_value = build_response({"result": [], "paging_metadata": {}})
        tracer = Tracer(name="business-flow")

        registry = AasService(
            base_url="https://dtr.example.com",
            base_lookup_url="https://dtr.example.com",
            api_path="/api/v3",
        )
        connector = connector_service()

        # One single trace for the complete flow
        registry.set_tracer(tracer)
        connector.set_tracer(tracer)

        registry.get_all_asset_administration_shell_descriptors(bpn="BPNL0000000001")
        connector.assets.get_all()

        entries = tracer.to_list()
        self.assertEqual(2, len(entries))
        self.assertEqual(
            [
                "https://dtr.example.com/api/v3/shell-descriptors",
                "https://connector.example.com/management/v3/assets/request",
            ],
            [entry["request"]["url"] for entry in entries],
        )
        self.assertEqual(
            "AasService.get_all_asset_administration_shell_descriptors",
            entries[0]["context"],
        )


class TestDiscoveryServiceTracing(unittest.TestCase):
    class FakeOauth:
        connected = True

        def add_auth_header(self, headers=None):
            headers = headers or {}
            headers["Authorization"] = "Bearer token"
            return headers

    @patch("requests.post")
    def test_discovery_finder_trace(self, mock_post):
        mock_post.return_value = build_response(
            {"endpoints": [{"type": "bpn", "endpointAddress": "https://bpn.example.com"}]}
        )
        finder = DiscoveryFinderService(url="https://discovery.example.com", oauth=self.FakeOauth(), trace=True)

        finder.find_discovery_urls(keys=["bpn"])

        trace = finder.get_trace()
        self.assertEqual(1, len(trace))
        self.assertEqual({"types": ["bpn"]}, trace[0]["request"]["body"])
        # Credentials never end up in the trace
        self.assertNotIn("token", json.dumps(trace))

    @patch("requests.post")
    def test_discovery_finder_without_trace(self, mock_post):
        mock_post.return_value = build_response(
            {"endpoints": [{"type": "bpn", "endpointAddress": "https://bpn.example.com"}]}
        )
        finder = DiscoveryFinderService(url="https://discovery.example.com", oauth=self.FakeOauth())

        finder.find_discovery_urls(keys=["bpn"])

        self.assertEqual([], finder.get_trace())
        # The request is performed exactly as it was before tracing existed
        self.assertNotIn("tracer", mock_post.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
