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

"""The log records of the connector consumer services (base and Saturn): the DSP state machine and the dataplane calls."""

import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

import tractusx_sdk.dataspace.services.connector.base_connector_consumer as bcc
from tractusx_sdk.dataspace.managers.connection.memory import MemoryConnectionManager
from tractusx_sdk.dataspace.services.connector.base_connector_consumer import (
    BaseConnectorConsumerService, policy_id_of, should_log_poll,
)
from tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service import ConnectorConsumerService as SaturnConsumer
from tractusx_sdk.exceptions import CatalogError, NegotiationError, TransferError

SECRET = "s3cr3t-value"
ADDRESS = f"https://provider.example.com/dsp?token={SECRET}"
SAFE_ADDRESS = "https://provider.example.com/dsp"
BASE = "tractusx_sdk.dataspace.services.connector.base_connector_consumer"
SATURN = "tractusx_sdk.dataspace.services.connector.saturn.connector_consumer_service"
POLICY = {"@id": "policy-1", "odrl:permission": []}


def _dump(caplog) -> str:
    """Everything a handler could ever render out of the captured records."""
    return "\n".join(f"{r.getMessage()} {r.__dict__} {r.exc_text or ''}" for r in caplog.records)


def _records(caplog, name=BASE):
    return [r for r in caplog.records if r.name == name]


def _response(status=200, payload=None, text=""):
    response = Mock(status_code=status, text=text)
    response.json.return_value = payload
    return response


@pytest.fixture
def service():
    service = BaseConnectorConsumerService(
        dataspace_version="jupiter", base_url="https://control.example.com", dma_path="/management",
        headers={"X-Api-Key": f"api-key-{SECRET}"}, connection_manager=MemoryConnectionManager())
    service._edr_controller = Mock()
    service._catalog_controller = Mock()
    service._contract_negotiation_controller = Mock()
    service._transfer_process_controller = Mock()
    with patch.object(bcc.op, "wait"):
        yield service


class TestHelpers:

    @pytest.mark.parametrize("attempt, expected", [(1, True), (2, False), (9, False), (10, True), (11, False), (20, True), (25, False)])
    def test_a_polling_loop_logs_its_first_attempt_and_then_one_in_ten(self, attempt, expected):
        assert should_log_poll(attempt) is expected

    def test_policy_id_of(self):
        assert policy_id_of(POLICY) == "policy-1"
        assert policy_id_of({}) is None
        assert policy_id_of(None) is None
        assert policy_id_of("x") is None


class TestConstructionAndEdr:

    def test_creation_is_logged_without_the_headers(self, caplog):
        with caplog.at_level(logging.DEBUG):
            BaseConnectorConsumerService(dataspace_version="jupiter", base_url="https://c.example.com", dma_path="/m",
                                         headers={"X-Api-Key": f"api-key-{SECRET}"})
        messages = [r.getMessage() for r in _records(caplog)]
        assert any("No connection manager given" in m for m in messages)
        assert any("Consumer service created for dataspace version jupiter" in m and "MemoryConnectionManager" in m for m in messages)
        assert SECRET not in _dump(caplog)

    def test_getting_an_edr_logs_the_transfer_and_never_the_credentials(self, service, caplog):
        service._edr_controller.get_data_address.return_value = _response(200, {"endpoint": "https://dp", "authorization": f"edr-{SECRET}"})
        with caplog.at_level(logging.DEBUG):
            assert service.get_endpoint_with_token("tp-1") == ("https://dp", f"edr-{SECRET}")
        assert _records(caplog)[0].transfer_id == "tp-1"
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("response, status", [(None, None), (Mock(status_code=404), 404)])
    def test_an_edr_that_cannot_be_read_is_logged_before_it_is_raised(self, service, caplog, response, status):
        service._edr_controller.get_data_address.return_value = response
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionError):
            service.get_edr("tp-1")
        error = _records(caplog)[-1]
        assert error.levelno == logging.ERROR and error.transfer_id == "tp-1"
        assert getattr(error, "status_code", None) == status

    def test_a_missing_edr_is_logged_before_it_is_raised(self, service, caplog):
        with patch.object(service, "get_edr", return_value=None), caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError):
            service.get_endpoint_with_token("tp-1")
        assert _records(caplog)[-1].levelno == logging.ERROR


class TestCatalog:

    def test_a_catalog_request_is_logged_with_a_sanitised_address(self, service, caplog):
        service._catalog_controller.get_catalog.return_value = _response(200, {"dcat:dataset": []})
        with caplog.at_level(logging.DEBUG):
            service.get_catalog(request=Mock(to_data=lambda: {}), counter_party_id="BPNL1", counter_party_address=ADDRESS)
        record = [r for r in _records(caplog) if "Requesting the catalog" in r.getMessage()][0]
        assert record.counter_party_address == SAFE_ADDRESS and SAFE_ADDRESS in record.getMessage()
        assert SECRET not in _dump(caplog)

    def test_a_failed_catalog_is_logged_before_it_is_raised(self, service, caplog):
        from tractusx_sdk.exceptions import CatalogRequestError
        service._catalog_controller.get_catalog.return_value = _response(503, text="down")
        with caplog.at_level(logging.DEBUG), pytest.raises(CatalogRequestError):
            service.get_catalog(request=Mock(to_data=lambda: {}), counter_party_id="BPNL1", counter_party_address=ADDRESS)
        error = [r for r in _records(caplog) if r.levelno == logging.ERROR][0]
        assert (error.status_code, error.counter_party_id) == (503, "BPNL1")
        assert SECRET not in _dump(caplog)

    def test_a_catalog_request_without_the_needed_arguments_is_logged_before_it_is_raised(self, service, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            service.get_catalog()
        assert _records(caplog)[-1].levelno == logging.ERROR

    def test_the_catalogs_of_several_connectors_are_logged_and_a_failure_is_kept_in_the_result(self, service, caplog):
        def fake(counter_party_id, counter_party_address, **kwargs):
            if "bad" in counter_party_address:
                raise ConnectionError("boom")
            return {"ok": True}

        with patch.object(service, "get_catalog_with_filter", side_effect=fake), caplog.at_level(logging.DEBUG):
            result = service.get_catalogs_with_filter_with_bpnl("BPNL1", ["https://ok.example.com", f"https://bad.example.com?token={SECRET}"],
                                                               filter_expression=[])
        assert result["https://ok.example.com"] == {"ok": True} and "error" in result[f"https://bad.example.com?token={SECRET}"]
        warning = [r for r in _records(caplog) if r.levelno == logging.WARNING][0]
        assert warning.bpn == "BPNL1" and "https://bad.example.com" in warning.getMessage()
        assert SECRET not in warning.getMessage() and SECRET not in str(warning.counter_party_address)

    def test_the_parallel_fetch_logs_the_failure_with_its_traceback_and_re_raises_it(self, service, caplog):
        catalogs = {}
        with patch.object(service, "get_catalog_with_filter", side_effect=ConnectionError("boom")), caplog.at_level(logging.DEBUG):
            with pytest.raises(ConnectionError):
                service.get_catalog_with_filter_parallel("BPNL1", ADDRESS, [], catalogs=catalogs)
        failure = _records(caplog)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info is not None
        assert (failure.counter_party_id, failure.counter_party_address) == ("BPNL1", SAFE_ADDRESS)
        assert SECRET not in failure.getMessage()

    def test_a_fan_out_logs_how_many_catalogs_arrived(self, service, caplog):
        with patch.object(service, "get_catalog_with_filter", return_value={}), caplog.at_level(logging.DEBUG):
            service.get_catalogs_with_filter("BPNL1", ["https://a.example.com", "https://b.example.com"], filter_expression=[])
        messages = [r.getMessage() for r in _records(caplog)]
        assert any("from 2 connector(s) in parallel" in m for m in messages)
        assert any("Received 2 of 2 catalog(s)" in m for m in messages)


class TestNegotiationStart:

    def _start(self, service, response):
        service._edr_controller.create.return_value = response
        with patch.object(service, "get_edr_negotiation_request", return_value=Mock(to_data=lambda: {})):
            return service.start_edr_negotiation("BPNL1", ADDRESS, "asset-1", POLICY)

    def test_a_started_negotiation_is_a_milestone_with_every_identifier(self, service, caplog):
        with caplog.at_level(logging.DEBUG):
            assert self._start(service, _response(200, {"@id": "neg-1"})) == "neg-1"
        info = [r for r in _records(caplog) if r.levelno == logging.INFO][0]
        assert (info.negotiation_id, info.asset_id, info.policy_id, info.counter_party_id) == ("neg-1", "asset-1", "policy-1", "BPNL1")
        assert info.counter_party_address == SAFE_ADDRESS
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("response, status", [(None, None), (Mock(status_code=409), 409)])
    def test_a_negotiation_that_cannot_start_is_an_error_even_though_it_returns_none(self, service, caplog, response, status):
        with caplog.at_level(logging.DEBUG):
            assert self._start(service, response) is None
        error = _records(caplog)[-1]
        assert error.levelno == logging.ERROR and error.asset_id == "asset-1" and getattr(error, "status_code", None) == status

    def test_an_answer_without_a_negotiation_id_is_an_error(self, service, caplog):
        with caplog.at_level(logging.DEBUG):
            assert self._start(service, _response(200, {})) is None
        assert "returned no negotiation id" in _records(caplog)[-1].getMessage()

    def test_the_offers_are_tried_in_turn_with_a_warning_for_each_one_that_fails(self, service, caplog):
        with patch.object(service, "start_edr_negotiation", side_effect=[None, "neg-2"]), caplog.at_level(logging.DEBUG):
            assert service._start_negotiation_for_assets("BPNL1", ADDRESS, [("a1", POLICY), ("a2", POLICY)]) == "neg-2"
        warning = [r for r in _records(caplog) if r.levelno == logging.WARNING][0]
        assert warning.asset_id == "a1" and warning.policy_id == "policy-1"

    def test_no_offer_that_can_be_negotiated_is_an_error_before_it_is_raised(self, service, caplog):
        with patch.object(service, "start_edr_negotiation", return_value=None), caplog.at_level(logging.DEBUG):
            with pytest.raises(NegotiationError):
                service._start_negotiation_for_assets("BPNL1", ADDRESS, [("a1", POLICY)])
        assert _records(caplog)[-1].levelno == logging.ERROR and "1 offer(s) tried" in _records(caplog)[-1].getMessage()


class TestCatalogValidation:

    def _validate(self, service, catalog=None, filtered=None, error=None):
        with patch.object(service, "get_catalog_with_filter", return_value=catalog), \
                patch.object(bcc.DspTools, "filter_assets_and_policies", side_effect=error, return_value=filtered):
            return service._fetch_and_validate_catalog("BPNL1", ADDRESS, [], policies=[POLICY])

    def test_a_valid_catalog_is_logged_at_debug(self, service, caplog):
        with caplog.at_level(logging.DEBUG):
            assert self._validate(service, catalog={"x": 1}, filtered=[("a1", POLICY)]) == [("a1", POLICY)]
        assert any("1 valid asset and policy pair(s)" in r.getMessage() for r in _records(caplog))
        assert SECRET not in _dump(caplog)

    def test_an_empty_catalog_is_logged_before_it_is_raised(self, service, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(CatalogError):
            self._validate(service, catalog=None)
        assert _records(caplog)[-1].levelno == logging.ERROR

    def test_a_policy_mismatch_is_logged_with_its_traceback_and_context(self, service, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(CatalogError):
            self._validate(service, catalog={"x": 1}, error=ValueError("no policy matches"))
        failure = [r for r in _records(caplog) if r.exc_info][0]
        assert failure.levelno == logging.ERROR
        assert (failure.counter_party_id, failure.counter_party_address) == ("BPNL1", SAFE_ADDRESS)

    def test_no_valid_pair_is_logged_before_it_is_raised(self, service, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(CatalogError):
            self._validate(service, catalog={"x": 1}, filtered=[])
        assert _records(caplog)[-1].levelno == logging.ERROR


class TestStateMachine:

    def _states(self, service, *states):
        service._contract_negotiation_controller.get_state_by_id.side_effect = [_response(200, {"state": s}) for s in states]

    def test_a_state_change_is_logged_once_with_the_negotiation_id(self, service, caplog):
        self._states(service, "REQUESTED", "REQUESTED", "AGREED")
        with caplog.at_level(logging.DEBUG):
            last = None
            for _ in range(3):
                _, last = service._check_single_negotiation_state("neg-1", ADDRESS, last)
        infos = [r for r in _records(caplog) if r.levelno == logging.INFO]
        assert [r.getMessage().rsplit(": ", 1)[-1] for r in infos] == ["REQUESTED", "AGREED"]
        assert {r.negotiation_id for r in infos} == {"neg-1"}
        assert SECRET not in _dump(caplog)

    def test_a_terminated_negotiation_is_logged_before_it_is_raised(self, service, caplog):
        self._states(service, "TERMINATED")
        with caplog.at_level(logging.DEBUG), pytest.raises(NegotiationError):
            service._check_single_negotiation_state("neg-1", ADDRESS, None)
        error = _records(caplog)[-1]
        assert (error.levelno, error.negotiation_id) == (logging.ERROR, "neg-1")

    def test_the_agreement_id_is_logged_when_the_negotiation_is_finalized(self, service, caplog):
        service._contract_negotiation_controller.get_by_id.return_value = _response(200, {"contractAgreementId": "agr-1"})
        with caplog.at_level(logging.DEBUG):
            assert service._get_agreement_id("neg-1") == "agr-1"
        assert (_records(caplog)[-1].negotiation_id, _records(caplog)[-1].agreement_id) == ("neg-1", "agr-1")

    @pytest.mark.parametrize("response", [None, Mock(status_code=500), _response(200, {})])
    def test_an_unreadable_negotiation_is_logged_before_it_is_raised(self, service, caplog, response):
        service._contract_negotiation_controller.get_by_id.return_value = response
        with caplog.at_level(logging.DEBUG), pytest.raises(NegotiationError):
            service._get_agreement_id("neg-1")
        assert _records(caplog)[-1].levelno == logging.ERROR and _records(caplog)[-1].negotiation_id == "neg-1"

    def test_polling_logs_the_attempts_at_debug_without_logging_every_iteration(self, service, caplog):
        service._contract_negotiation_controller.get_state_by_id.return_value = _response(200, {"state": "REQUESTED"})
        with caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
            service._poll_negotiation_state("neg-1", ADDRESS, max_wait=25, poll_interval=1)

        polling = [r.getMessage() for r in _records(caplog) if "Polling the state" in r.getMessage()]
        assert [m.split("attempt ")[1].split(" ")[0] for m in polling] == ["1", "10", "20"]
        assert {r.levelno for r in _records(caplog) if "Polling the state" in r.getMessage()} == {logging.DEBUG}

    def test_a_timeout_is_an_error_with_the_attempts_and_the_last_state_before_it_is_raised(self, service, caplog):
        service._contract_negotiation_controller.get_state_by_id.return_value = _response(200, {"state": "REQUESTED"})
        with caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
            service._poll_negotiation_state("neg-1", ADDRESS, max_wait=3, poll_interval=1)
        error = _records(caplog)[-1]
        assert error.levelno == logging.ERROR and "3 attempt(s) (last state: REQUESTED)" in error.getMessage()
        assert error.negotiation_id == "neg-1"

    def test_a_transient_failure_is_a_warning_once_in_a_while_and_debug_otherwise(self, service, caplog):
        service._contract_negotiation_controller.get_state_by_id.side_effect = ConnectionError("down")
        with caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
            service._poll_negotiation_state("neg-1", ADDRESS, max_wait=12, poll_interval=1)
        failures = [r for r in _records(caplog) if "Failed to check negotiation state" in r.getMessage()]
        assert len(failures) == 12
        assert [r.levelno for r in failures if r.levelno == logging.WARNING] == [logging.WARNING] * 2

    def test_a_finalized_negotiation_ends_the_polling(self, service, caplog):
        self._states(service, "REQUESTED", "FINALIZED")
        with patch.object(service, "_get_agreement_id", return_value="agr-1"), caplog.at_level(logging.DEBUG):
            assert service._poll_negotiation_state("neg-1", ADDRESS, max_wait=10, poll_interval=1) == "agr-1"

    def test_a_transfer_process_that_does_not_exist_yet_is_logged_per_throttled_attempt(self, service, caplog):
        with patch.object(service, "get_transfer_process", return_value=None), caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
            service._wait_for_transfer_process("agr-1", ADDRESS, max_wait=22, poll_interval=1)
        waiting = [r.getMessage() for r in _records(caplog) if "not yet created" in r.getMessage()]
        assert [m.split("attempt ")[1].split(",")[0] for m in waiting] == ["1", "10", "20"]
        error = _records(caplog)[-1]
        assert error.levelno == logging.ERROR and error.agreement_id == "agr-1"

    def test_a_terminated_transfer_process_is_logged_with_its_reason_before_it_is_raised(self, service, caplog):
        process = {"@id": "tp-1", "state": "TERMINATED", "errorDetail": "provider refused"}
        with patch.object(service, "get_transfer_process", return_value=process), caplog.at_level(logging.DEBUG), pytest.raises(TransferError):
            service._wait_for_transfer_process("agr-1", ADDRESS, max_wait=5, poll_interval=1)
        error = _records(caplog)[-1]
        assert error.levelno == logging.ERROR and (error.transfer_id, error.agreement_id) == ("tp-1", "agr-1")
        assert "provider refused" in error.getMessage()

    def test_a_started_transfer_process_logs_its_state_change_with_the_ids(self, service, caplog):
        with patch.object(service, "get_transfer_process", return_value={"@id": "tp-1", "state": "STARTED"}), caplog.at_level(logging.DEBUG):
            assert service._wait_for_transfer_process("agr-1", ADDRESS, max_wait=5, poll_interval=1) == "tp-1"
        info = [r for r in _records(caplog) if r.levelno == logging.INFO][0]
        assert (info.transfer_id, info.agreement_id) == ("tp-1", "agr-1")

    def test_a_transfer_process_check_that_fails_is_a_throttled_warning(self, service, caplog):
        with patch.object(service, "get_transfer_process", side_effect=[ConnectionError("x")] * 2 + [{"@id": "tp", "state": "STARTED"}]), \
                caplog.at_level(logging.DEBUG):
            service._wait_for_transfer_process("agr-1", ADDRESS, max_wait=5, poll_interval=1)
        failures = [r for r in _records(caplog) if "Failed to check the transfer process" in r.getMessage()]
        assert [r.levelno for r in failures] == [logging.WARNING, logging.DEBUG]

    def test_the_edr_entry_wait_is_throttled_and_times_out_with_an_error(self, service, caplog):
        with patch.object(service, "get_edr_entry", return_value=None), caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
            service._wait_for_edr_entry("neg-1", ADDRESS, max_wait=12, poll_interval=1)
        waiting = [r for r in _records(caplog) if "not yet available" in r.getMessage()]
        assert len(waiting) == 2 and {r.levelno for r in waiting} == {logging.DEBUG}
        assert _records(caplog)[-1].levelno == logging.ERROR


class TestEdrEntryAndTransferProcess:

    def test_an_existing_entry_is_logged_by_identifier_only(self, service, caplog):
        entry = {"transferProcessId": "tp-1", "authorization": f"edr-{SECRET}"}
        service._edr_controller.query.return_value = _response(200, [entry])
        with caplog.at_level(logging.DEBUG):
            assert service.get_edr_entry("neg-1") == entry
        assert (_records(caplog)[-1].negotiation_id, _records(caplog)[-1].transfer_id) == ("neg-1", "tp-1")
        assert SECRET not in _dump(caplog)

    def test_a_missing_entry_is_a_debug_record_and_a_failed_query_an_error(self, service, caplog):
        service._edr_controller.query.return_value = _response(200, [])
        with caplog.at_level(logging.DEBUG):
            assert service.get_edr_entry("neg-1") is None
        assert _records(caplog)[-1].levelno == logging.DEBUG

        service._edr_controller.query.return_value = Mock(status_code=500)
        with caplog.at_level(logging.DEBUG), pytest.raises(ConnectionError):
            service.get_edr_entry("neg-1")
        assert (_records(caplog)[-1].levelno, _records(caplog)[-1].status_code) == (logging.ERROR, 500)

    def test_a_transfer_process_query_rejected_for_every_key_is_logged_with_the_keys_but_not_the_bodies(self, service, caplog):
        service._transfer_process_agreement_id_key = None
        service._transfer_process_controller.query.return_value = _response(400, text=f"body with {SECRET}")
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            service.get_transfer_process("agr-1")
        error = _records(caplog)[-1]
        assert error.levelno == logging.ERROR and error.agreement_id == "agr-1"
        assert "contractAgreementId" in error.getMessage() and SECRET not in _dump(caplog)

    def test_a_transient_lack_of_response_is_a_debug_record(self, service, caplog):
        service._transfer_process_controller.query.return_value = None
        with caplog.at_level(logging.DEBUG):
            assert service.get_transfer_process("agr-1") is None
        assert _records(caplog)[-1].levelno == logging.DEBUG


class TestOrchestration:
    ARGS = dict(counter_party_id="BPNL1", counter_party_address=ADDRESS, filter_expression=[], policies=[POLICY])

    def _patch_phases(self, service, **overrides):
        phases = {
            "_fetch_and_validate_catalog": [("a1", POLICY)],
            "_start_negotiation_for_assets": "neg-1",
            "_poll_negotiation_state": "agr-1",
            "_wait_for_transfer_process": "tp-1",
            "_wait_for_edr_entry": {"transferProcessId": "tp-1", "authorization": f"edr-{SECRET}"},
        }
        phases.update(overrides)
        return [patch.object(service, name, **({"side_effect": value} if isinstance(value, Exception) else {"return_value": value}))
                for name, value in phases.items()]

    def _run(self, service, **overrides):
        patches = self._patch_phases(service, **overrides)
        for p in patches:
            p.start()
        try:
            return service.negotiate_and_transfer(**self.ARGS)
        finally:
            for p in patches:
                p.stop()

    def test_a_completed_exchange_is_a_milestone_with_every_identifier(self, service, caplog):
        with caplog.at_level(logging.DEBUG):
            self._run(service)
        done = _records(caplog)[-1]
        assert done.levelno == logging.INFO
        assert (done.negotiation_id, done.agreement_id, done.transfer_id) == ("neg-1", "agr-1", "tp-1")
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("failing, phase, known", [
        ("_fetch_and_validate_catalog", "catalog", (None, None, None)),
        ("_start_negotiation_for_assets", "negotiation", (None, None, None)),
        ("_poll_negotiation_state", "negotiation state", ("neg-1", None, None)),
        ("_wait_for_transfer_process", "transfer process", ("neg-1", "agr-1", None)),
        ("_wait_for_edr_entry", "EDR entry", ("neg-1", "agr-1", "tp-1")),
    ])
    def test_a_failure_is_logged_once_with_the_traceback_the_phase_and_the_ids_known_so_far(self, service, caplog, failing, phase, known):
        with caplog.at_level(logging.DEBUG), pytest.raises(TimeoutError):
            self._run(service, **{failing: TimeoutError("late")})

        failure = [r for r in _records(caplog) if "The DSP exchange" in r.getMessage()]
        assert len(failure) == 1
        record = failure[0]
        assert record.levelno == logging.ERROR and record.exc_info[0] is TimeoutError
        assert f"failed at the {phase} phase" in record.getMessage()
        assert (getattr(record, "negotiation_id", None), getattr(record, "agreement_id", None),
                getattr(record, "transfer_id", None)) == known
        assert (record.counter_party_id, record.counter_party_address) == ("BPNL1", SAFE_ADDRESS)
        assert SECRET not in _dump(caplog)

    def test_the_cache_hit_returns_without_a_negotiation_and_is_logged_with_the_transfer_id(self, service, caplog):
        with patch.object(service.connection_manager, "get_connection_transfer_id", return_value="tp-9"), \
                patch.object(service, "negotiate_and_transfer") as negotiate, caplog.at_level(logging.DEBUG):
            assert service.get_transfer_id(policies=[POLICY], counter_party_id="BPNL1", counter_party_address=ADDRESS,
                                           filter_expression=[]) == "tp-9"
        negotiate.assert_not_called()
        hit = _records(caplog)[-1]
        assert (hit.transfer_id, hit.counter_party_address) == ("tp-9", SAFE_ADDRESS)

    def test_a_cache_miss_negotiates_and_caches_the_connection(self, service, caplog):
        edr = {"transferProcessId": "tp-1", "@id": "tp-1", "@type": "x", "@context": {}, "providerId": "BPNL1",
               "authorization": f"edr-{SECRET}"}
        with patch.object(service, "negotiate_and_transfer", return_value=edr), caplog.at_level(logging.DEBUG):
            assert service.get_transfer_id(policies=[POLICY], counter_party_id="BPNL1", counter_party_address=ADDRESS,
                                           filter_expression=[]) == "tp-1"
        infos = [r for r in _records(caplog) if r.levelno == logging.INFO]
        assert len(infos) == 2 and infos[-1].transfer_id == "tp-1"
        assert SECRET not in _dump(caplog)

    def test_no_policies_is_a_warning_with_a_sanitised_address(self, service, caplog):
        with patch.object(service, "negotiate_and_transfer", side_effect=RuntimeError("stop")), caplog.at_level(logging.DEBUG):
            with pytest.raises(RuntimeError):
                service.get_transfer_id(policies=None, counter_party_id="BPNL1", counter_party_address=ADDRESS, filter_expression=[])
        warning = [r for r in _records(caplog) if r.levelno == logging.WARNING][0]
        assert SAFE_ADDRESS in warning.getMessage() and SECRET not in _dump(caplog)

    def test_an_empty_exchange_result_is_logged_before_it_is_raised(self, service, caplog):
        with patch.object(service, "negotiate_and_transfer", return_value=None), caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError):
            service.get_transfer_id(policies=[POLICY], counter_party_id="BPNL1", counter_party_address=ADDRESS, filter_expression=[])
        assert _records(caplog)[-1].levelno == logging.ERROR

    def test_checking_that_an_asset_exists_logs_the_outcome_or_the_failure(self, service, caplog):
        with patch.object(service, "get_catalog_with_filter", return_value={"x": 1}), \
                patch.object(bcc.DspTools, "is_catalog_empty", return_value=False), caplog.at_level(logging.DEBUG):
            assert service.assets_exists("BPNL1", ADDRESS, []) is True
        assert "The asset exists" in _records(caplog)[-1].getMessage()

        caplog.clear()
        with patch.object(service, "get_catalog_with_filter", side_effect=OSError("boom")), caplog.at_level(logging.DEBUG):
            with pytest.raises(ConnectionError):
                service.assets_exists("BPNL1", ADDRESS, [])
        failure = _records(caplog)[-1]
        assert failure.levelno == logging.ERROR and failure.exc_info[0] is OSError and failure.counter_party_id == "BPNL1"


class TestDataplaneCalls:

    def test_a_call_logs_the_method_and_the_path_but_never_the_edr_authorization(self, service, caplog):
        with patch.object(service, "do_dsp", return_value=("https://dp.example.com", f"edr-{SECRET}")), \
                patch.object(bcc.HttpTools, "do_get", return_value=Mock(status_code=200)) as do_get, caplog.at_level(logging.DEBUG):
            service.do_get("BPNL1", ADDRESS, [], path=f"/data?token={SECRET}", policies=[POLICY])

        assert do_get.call_args.kwargs["headers"]["Authorization"] == f"edr-{SECRET}"
        messages = [r.getMessage() for r in _records(caplog)]
        assert any(m == f"[Connector Service] GET /data through the connector of [BPNL1] at {SAFE_ADDRESS}" for m in messages)
        assert any("TLS verification of the dataplane request is disabled by default" in m for m in messages)
        assert SECRET not in _dump(caplog)

    @pytest.mark.parametrize("method, patched", [("do_post", "do_post"), ("do_put", "do_put")])
    def test_posting_and_putting_are_logged_and_an_explicit_verify_is_not_reported_as_a_default(self, service, caplog, method, patched):
        with patch.object(service, "do_dsp", return_value=("https://dp.example.com", f"edr-{SECRET}")), \
                patch.object(bcc.HttpTools, patched, return_value=Mock(status_code=200)), caplog.at_level(logging.DEBUG):
            getattr(service, method)("BPNL1", ADDRESS, [], path="/x", policies=[POLICY], json={"k": SECRET}, verify=True)

        messages = [r.getMessage() for r in _records(caplog)]
        assert any(m.startswith(f"[Connector Service] {method[3:].upper()} /x through the connector") for m in messages)
        assert not any("disabled by default" in m for m in messages)
        assert SECRET not in _dump(caplog)


@pytest.fixture
def saturn():
    consumer = SaturnConsumer(dataspace_version="saturn", base_url="https://control.example.com", dma_path="/management",
                              headers={"X-Api-Key": f"api-key-{SECRET}"}, connection_manager=MemoryConnectionManager())
    consumer._edr_controller = Mock()
    consumer._catalog_controller = Mock()
    consumer._connector_discovery_controller = Mock()
    with patch.object(bcc.op, "wait"):
        yield consumer


class TestSaturnConsumer:

    def test_an_unsupported_version_is_logged_before_it_is_raised(self, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            SaturnConsumer(dataspace_version="jupiter", base_url="https://x", dma_path="/m")
        error = _records(caplog, SATURN)[-1]
        assert (error.levelno, error.dataspace_version) == (logging.ERROR, "jupiter")

    def test_a_dataplane_request_logs_the_method_and_the_path_but_never_the_authorization(self, saturn, caplog):
        with patch(f"{SATURN}.HttpTools.do_get", return_value=Mock(status_code=200)) as do_get, caplog.at_level(logging.DEBUG):
            saturn._execute_http_request("GET", "https://dp.example.com", f"edr-{SECRET}", path=f"/data?token={SECRET}", verify=True)
        assert do_get.call_args.kwargs["headers"]["Authorization"] == f"edr-{SECRET}"
        message = _records(caplog, SATURN)[-1].getMessage()
        assert message == "[Connector Service] Dataplane GET /data (TLS verification: True, session: False)"
        assert SECRET not in _dump(caplog)

    def test_an_unsupported_http_method_is_logged_before_it_is_raised(self, saturn, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError):
            saturn._execute_http_request("DELETE", "https://dp", "tok", path="/")
        assert _records(caplog, SATURN)[-1].levelno == logging.ERROR

    def test_the_resolution_of_the_counter_party_never_logs_the_query_string(self, saturn, caplog):
        with patch.object(saturn, "get_discovery_info", return_value=(ADDRESS, "BPNL1", "dsp")), caplog.at_level(logging.DEBUG):
            assert saturn._resolve_counter_party_info(bpnl="BPNL1", verify=True) == (ADDRESS, "BPNL1", "dsp")
            saturn._resolve_counter_party_info(counter_party_id="BPNL1", counter_party_address=ADDRESS)
        assert SECRET not in _dump(caplog) and SAFE_ADDRESS in _dump(caplog)

    def test_a_negotiation_is_logged_like_the_base_one(self, saturn, caplog):
        saturn._edr_controller.create.return_value = _response(200, {"@id": "neg-1"})
        with patch.object(saturn, "get_edr_negotiation_request", return_value=Mock(to_data=lambda: {})), caplog.at_level(logging.DEBUG):
            assert saturn.start_edr_negotiation("BPNL1", ADDRESS, "asset-1", POLICY) == "neg-1"
        info = [r for r in _records(caplog, SATURN) if r.levelno == logging.INFO][0]
        assert (info.negotiation_id, info.asset_id, info.policy_id) == ("neg-1", "asset-1", "policy-1")
        assert info.counter_party_address == SAFE_ADDRESS

        saturn._edr_controller.create.return_value = None
        with patch.object(saturn, "get_edr_negotiation_request", return_value=Mock(to_data=lambda: {})), caplog.at_level(logging.DEBUG):
            assert saturn.start_edr_negotiation("BPNL1", ADDRESS, "asset-1", POLICY) is None
        assert _records(caplog, SATURN)[-1].levelno == logging.ERROR

    def test_an_offer_without_an_id_is_logged_before_it_is_raised(self, saturn, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="Policy offer id"):
            saturn.get_edr_negotiation_request("BPNL1", ADDRESS, "asset-1", {"no": "id"})
        assert _records(caplog, SATURN)[-1].asset_id == "asset-1"

    def test_an_empty_policy_list_is_logged_before_it_is_raised(self, saturn, caplog):
        with caplog.at_level(logging.DEBUG), pytest.raises(ValueError, match="No policy has been selected"):
            saturn.get_transfer_id("BPNL1", ADDRESS, [], policies=[])
        assert _records(caplog, SATURN)[-1].levelno == logging.ERROR

    def test_the_auto_selection_of_a_policy_is_logged_and_its_failures_are_logged_with_context(self, saturn, caplog):
        with patch.object(saturn, "get_catalog_with_filter", return_value={"x": 1}), \
                patch(f"{SATURN}.DspTools.filter_assets_and_policies", return_value=[("a1", {"@id": "p1", "@type": "t", "k": "v"})]), \
                caplog.at_level(logging.DEBUG):
            assert saturn._resolve_policies_from_catalog("BPNL1", ADDRESS, [], "dsp", {}) == [{"k": "v"}]
        records = _records(caplog, SATURN)
        assert records[0].levelno == logging.WARNING and SAFE_ADDRESS in records[0].getMessage()
        assert records[-1].policy_id == "p1"

        caplog.clear()
        with patch.object(saturn, "get_catalog_with_filter", return_value={"x": 1}), \
                patch(f"{SATURN}.DspTools.filter_assets_and_policies", side_effect=ValueError("none")), \
                caplog.at_level(logging.DEBUG), pytest.raises(CatalogError):
            saturn._resolve_policies_from_catalog("BPNL1", ADDRESS, [], "dsp", {})
        failure = [r for r in _records(caplog, SATURN) if r.exc_info][0]
        assert (failure.counter_party_id, failure.counter_party_address) == ("BPNL1", SAFE_ADDRESS)

        caplog.clear()
        with patch.object(saturn, "get_catalog_with_filter", return_value=None), caplog.at_level(logging.DEBUG), pytest.raises(CatalogError):
            saturn._resolve_policies_from_catalog("BPNL1", ADDRESS, [], "dsp", {})
        assert _records(caplog, SATURN)[-1].levelno == logging.ERROR

    def test_the_discovery_of_a_connector_is_logged_and_its_failure_too(self, saturn, caplog):
        saturn._connector_discovery_controller.get_discover.return_value = _response(200, {"counterPartyAddress": ADDRESS})
        with patch(f"{SATURN}.ModelFactory.get_connector_discovery_model"), caplog.at_level(logging.DEBUG):
            assert saturn.discover_connector_protocol("BPNL1", ADDRESS) == {"counterPartyAddress": ADDRESS}
        assert _records(caplog, SATURN)[0].bpn == "BPNL1"

        saturn._connector_discovery_controller.get_discover.return_value = _response(500)
        with patch(f"{SATURN}.ModelFactory.get_connector_discovery_model"), caplog.at_level(logging.DEBUG), pytest.raises(ConnectionError):
            saturn.discover_connector_protocol("BPNL1", ADDRESS)
        error = [r for r in _records(caplog, SATURN) if r.levelno == logging.ERROR][0]
        assert (error.bpn, error.status_code) == ("BPNL1", 500)

    def test_a_discovery_response_without_a_key_is_logged_before_it_is_raised(self, saturn, caplog):
        with patch.object(saturn, "discover_connector_protocol", return_value={"counterPartyAddress": "a"}), \
                caplog.at_level(logging.DEBUG), pytest.raises(KeyError):
            saturn.get_discovery_info("BPNL1")
        error = [r for r in _records(caplog, SATURN) if r.levelno == logging.ERROR][0]
        assert error.bpn == "BPNL1" and "counterPartyId" in error.getMessage()

    def test_a_failing_catalog_of_several_connectors_is_a_sanitised_warning(self, saturn, caplog):
        with patch.object(saturn, "get_catalog_request_with_filter", side_effect=ConnectionError("boom")), caplog.at_level(logging.DEBUG):
            result = saturn.get_catalogs_with_filter("BPNL1", [ADDRESS], filter_expression=[])
        assert "error" in result[ADDRESS]
        warning = [r for r in _records(caplog, SATURN) if r.levelno == logging.WARNING][0]
        assert warning.counter_party_address == SAFE_ADDRESS and SECRET not in warning.getMessage()
