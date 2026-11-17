################################################################################
#
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
################################################################################

"""
One failure is one ERROR record, logged where the failure leaves the orchestration, and the callers cannot flood
the log with what they get wrong.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from tractusx_sdk.dataspace.managers.auth_manager import AuthManager
from tractusx_sdk.dataspace.managers.connection.memory import MemoryConnectionManager
from tractusx_sdk.dataspace.services.connector.base_connector_consumer import BaseConnectorConsumerService, op
from tractusx_sdk.dataspace.tools.encoding_tools import decode_base64_url_safe
from tractusx_sdk.exceptions import CatalogRequestError, NegotiationError, TransferError

ADDRESS = "https://provider.example.com/dsp"
POLICY = {"@id": "policy-1"}
ARGS = dict(counter_party_id="BPNL1", counter_party_address=ADDRESS, filter_expression=[], policies=[POLICY])


def _response(status=200, payload=None):
    response = Mock(status_code=status, text="")
    response.json.return_value = payload
    return response


@pytest.fixture
def service():
    service = BaseConnectorConsumerService(dataspace_version="jupiter", base_url="https://control.example.com", dma_path="/management",
                                           connection_manager=MemoryConnectionManager())
    service._catalog_controller = Mock()
    service._edr_controller = Mock()
    service._contract_negotiation_controller = Mock()
    service._transfer_process_controller = Mock()
    with patch.object(op, "wait"):
        yield service


def _problems(caplog):
    return [r for r in caplog.records if r.levelno >= logging.WARNING]


class TestOneErrorPerFailure:

    def _until_the_negotiation(self, service):
        """The catalog and the start of the negotiation work: what follows is up to the test."""
        patches = [patch.object(service, "_fetch_and_validate_catalog", return_value=[("a1", POLICY)]),
                   patch.object(service, "start_edr_negotiation", return_value="neg-1")]
        for p in patches:
            p.start()
        return patches

    def test_a_catalog_that_cannot_be_retrieved(self, service, caplog):
        service._catalog_controller.get_catalog.return_value = _response(503)
        with caplog.at_level(logging.DEBUG), pytest.raises(CatalogRequestError):
            service.negotiate_and_transfer(**ARGS)
        assert [r.levelno for r in _problems(caplog)] == [logging.ERROR]
        assert "catalog phase" in _problems(caplog)[0].getMessage()

    def test_a_terminated_negotiation(self, service, caplog):
        patches = self._until_the_negotiation(service)
        service._contract_negotiation_controller.get_state_by_id.return_value = _response(200, {"state": "TERMINATED"})
        try:
            with caplog.at_level(logging.DEBUG), pytest.raises(NegotiationError):
                service.negotiate_and_transfer(**ARGS)
        finally:
            for p in patches:
                p.stop()
        assert [r.levelno for r in _problems(caplog)] == [logging.ERROR]
        assert "negotiation state phase" in _problems(caplog)[0].getMessage()

    def test_a_negotiation_that_never_finalizes(self, service, caplog):
        patches = self._until_the_negotiation(service)
        service._contract_negotiation_controller.get_state_by_id.return_value = _response(200, {"state": "REQUESTED"})
        try:
            with caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
                service.negotiate_and_transfer(max_wait=3, **ARGS)
        finally:
            for p in patches:
                p.stop()
        assert [r.levelno for r in _problems(caplog)] == [logging.ERROR]

    def test_a_terminated_transfer_process(self, service, caplog):
        patches = self._until_the_negotiation(service) + [patch.object(service, "_poll_negotiation_state", return_value="agr-1")]
        patches[-1].start()
        process = {"@id": "tp-1", "state": "TERMINATED", "errorDetail": "provider refused"}
        try:
            with patch.object(service, "get_transfer_process", return_value=process), caplog.at_level(logging.DEBUG), \
                    pytest.raises(TransferError):
                service.negotiate_and_transfer(**ARGS)
        finally:
            for p in patches:
                p.stop()
        assert [r.levelno for r in _problems(caplog)] == [logging.ERROR]
        assert "transfer process phase" in _problems(caplog)[0].getMessage()

    def test_an_edr_entry_that_never_arrives(self, service, caplog):
        patches = self._until_the_negotiation(service) + [patch.object(service, "_poll_negotiation_state", return_value="agr-1"),
                                                           patch.object(service, "_wait_for_transfer_process", return_value="tp-1")]
        patches[-2].start()
        patches[-1].start()
        try:
            with patch.object(service, "get_edr_entry", return_value=None), caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
                service.negotiate_and_transfer(max_wait=3, **ARGS)
        finally:
            for p in patches:
                p.stop()
        assert [r.levelno for r in _problems(caplog)] == [logging.ERROR]

    def test_the_detail_of_the_failure_is_still_there_at_debug(self, service, caplog):
        service._catalog_controller.get_catalog.return_value = _response(503)
        with caplog.at_level(logging.DEBUG), pytest.raises(CatalogRequestError):
            service.negotiate_and_transfer(**ARGS)
        assert any(r.levelno == logging.DEBUG and getattr(r, "status_code", None) == 503 for r in caplog.records)


class TestNoFlooding:

    def test_rejected_api_keys_do_not_reach_the_info_level(self, caplog):
        manager = AuthManager(configured_api_key="configured", auth_enabled=True)
        request = Mock(headers={"X-Api-Key": "wrong"})
        missing = Mock(headers={})
        with caplog.at_level(logging.INFO):
            for _ in range(100):
                assert manager.is_authenticated(request) is False
                assert manager.is_authenticated(missing) is False
        assert caplog.records == []

    def test_undecodable_input_does_not_reach_the_info_level(self, caplog):
        with caplog.at_level(logging.INFO):
            for _ in range(100):
                with pytest.raises(Exception):
                    decode_base64_url_safe("/w")
        assert caplog.records == []
