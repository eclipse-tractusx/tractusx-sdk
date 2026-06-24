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

import threading
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine

from tractusx_sdk.dataspace.managers.connection.memory.memory_connection_manager import MemoryConnectionManager
from tractusx_sdk.dataspace.managers.connection.database.postgres_memory_connection_manager import PostgresMemoryConnectionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROVIDER_ID_KEY = "providerId"

def _make_entry(transfer_id: str, provider_did: str) -> dict:
    """Build a minimal EDR connection entry accepted by add_connection."""
    return {
        "@id": transfer_id,
        "@type": "edr:EndpointDataReference",
        "@context": {"edr": "https://w3id.org/edc/v0.0.1/ns/"},
        PROVIDER_ID_KEY: provider_did,
        "transferProcessId": transfer_id,
        "endpoint": "https://provider.example.com/api/data",
        "authorization": "Bearer some-token",
    }


def _add(cm: MemoryConnectionManager,
         counter_party_id: str,
         address: str = "https://provider.example.com/api",
         transfer_id: str = "tp-1") -> None:
    cm.add_connection(
        counter_party_id=counter_party_id,
        counter_party_address=address,
        query_checksum="qchk",
        policy_checksum="pchk",
        connection_entry=_make_entry(transfer_id, counter_party_id),
    )


# ---------------------------------------------------------------------------
# MemoryConnectionManager – clear_connections_by_party
# ---------------------------------------------------------------------------

class TestMemoryConnectionManagerClearByParty(unittest.TestCase):

    def setUp(self):
        self.cm = MemoryConnectionManager(provider_id_key=PROVIDER_ID_KEY)

    # --- match scenarios ---------------------------------------------------

    def test_jupiter_style_bpn_key_match(self):
        """Jupiter: cache key IS the raw BPN → exact substring match removes it."""
        _add(self.cm, "BPNL000000000065")

        removed = self.cm.clear_connections_by_party("BPNL000000000065")

        self.assertEqual(removed, 1)
        self.assertNotIn("BPNL000000000065", self.cm.open_connections)

    def test_saturn_style_did_key_match_with_bpn_substring(self):
        """Saturn: cache key is full DID but caller only knows the BPN → substring matches."""
        did = "did:web:ssi-dim-wallet-stub.example.com:BPNL000000000065"
        _add(self.cm, did)

        removed = self.cm.clear_connections_by_party("BPNL000000000065")

        self.assertEqual(removed, 1)
        self.assertNotIn(did, self.cm.open_connections)

    def test_exact_did_passed_as_substring(self):
        """Passing the full DID as the substring still matches the DID key."""
        did = "did:web:ssi-dim-wallet-stub.example.com:BPNL000000000065"
        _add(self.cm, did)

        removed = self.cm.clear_connections_by_party(did)

        self.assertEqual(removed, 1)
        self.assertNotIn(did, self.cm.open_connections)

    def test_multiple_parties_with_same_bpn_substring(self):
        """All parties whose key contains the substring are removed."""
        did_a = "did:web:wallet-a.example.com:BPNL000000000065"
        did_b = "did:web:wallet-b.example.com:BPNL000000000065"
        _add(self.cm, did_a, transfer_id="tp-a")
        _add(self.cm, did_b, transfer_id="tp-b")

        removed = self.cm.clear_connections_by_party("BPNL000000000065")

        self.assertEqual(removed, 2)
        self.assertNotIn(did_a, self.cm.open_connections)
        self.assertNotIn(did_b, self.cm.open_connections)

    # --- non-match / isolation scenarios -----------------------------------

    def test_no_match_returns_zero(self):
        """Unknown BPN → 0 entries removed, cache unchanged."""
        _add(self.cm, "BPNL000000000065")

        removed = self.cm.clear_connections_by_party("BPNL999999999999")

        self.assertEqual(removed, 0)
        self.assertIn("BPNL000000000065", self.cm.open_connections)

    def test_unrelated_parties_are_not_removed(self):
        """Only the matching party is evicted; others remain intact."""
        _add(self.cm, "did:web:wallet.example.com:BPNL000000000065", transfer_id="tp-1")
        _add(self.cm, "did:web:wallet.example.com:BPNL000000000099", transfer_id="tp-2")

        self.cm.clear_connections_by_party("BPNL000000000065")

        self.assertIn("did:web:wallet.example.com:BPNL000000000099", self.cm.open_connections)

    # --- internal counter key protection -----------------------------------

    def test_edrs_counter_key_is_never_removed(self):
        """The internal 'edrs' counter entry must survive even if substring matches."""
        # edrs_key defaults to "edrs"; force a substring that would match it
        cm = MemoryConnectionManager(provider_id_key=PROVIDER_ID_KEY, edrs_key="edrs")
        # add an entry to initialise the counter
        _add(cm, "BPNL000000000065")
        self.assertIn("edrs", cm.open_connections)

        # try to match the edrs key itself
        cm.clear_connections_by_party("edrs")

        self.assertIn("edrs", cm.open_connections)

    def test_edrs_counter_not_decremented_by_clear(self):
        """The 'edrs' count only tracks individual policy entries, not party keys."""
        _add(self.cm, "did:web:wallet.example.com:BPNL000000000065")
        count_before = self.cm.open_connections.get("edrs", 0)

        self.cm.clear_connections_by_party("BPNL000000000065")

        # counter is unchanged — clear_connections_by_party removes the top-level
        # party key but does not adjust the fine-grained EDR counter.
        self.assertEqual(self.cm.open_connections.get("edrs", 0), count_before)

    # --- return value and idempotency --------------------------------------

    def test_returns_int(self):
        removed = self.cm.clear_connections_by_party("BPNL000000000001")
        self.assertIsInstance(removed, int)

    def test_idempotent_second_call_returns_zero(self):
        """Calling twice with the same substring is safe; second call finds nothing."""
        _add(self.cm, "BPNL000000000065")
        self.cm.clear_connections_by_party("BPNL000000000065")

        removed = self.cm.clear_connections_by_party("BPNL000000000065")

        self.assertEqual(removed, 0)

    # --- thread safety -----------------------------------------------------

    def test_concurrent_clear_does_not_raise(self):
        """Parallel invocations must not cause data-race exceptions."""
        for i in range(20):
            _add(self.cm, f"BPNL{i:012d}", transfer_id=f"tp-{i}")

        errors = []

        def worker(bpn):
            try:
                self.cm.clear_connections_by_party(bpn)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(f"BPNL{i:012d}",)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])


# ---------------------------------------------------------------------------
# PostgresMemoryConnectionManager – clear_connections_by_party
# ---------------------------------------------------------------------------

class TestPostgresMemoryConnectionManagerClearByParty(unittest.TestCase):
    """
    Uses an in-memory SQLite database so no real Postgres is required.
    The SQLModel ORM is compatible with SQLite, which is sufficient to verify
    that _trigger_save() is called and data is actually removed from the DB.
    """

    def _make_engine(self):
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )

    def setUp(self):
        self.engine = self._make_engine()
        self.cm = PostgresMemoryConnectionManager(
            engine=self.engine,
            provider_id_key=PROVIDER_ID_KEY,
            table_name="test_edr_connections",
        )

    def tearDown(self):
        # Ensure the background save thread finishes before the next test.
        self.cm.stop()

    # --- delegation to super() -------------------------------------------

    def test_delegates_to_memory_manager(self):
        """clear_connections_by_party must call the parent implementation."""
        did = "did:web:wallet.example.com:BPNL000000000065"
        _add(self.cm, did)

        removed = self.cm.clear_connections_by_party("BPNL000000000065")

        self.assertEqual(removed, 1)
        self.assertNotIn(did, self.cm.open_connections)

    # --- _trigger_save behaviour -----------------------------------------

    def test_trigger_save_called_when_entries_removed(self):
        """_trigger_save() must be called when at least one entry was evicted."""
        _add(self.cm, "did:web:wallet.example.com:BPNL000000000065")

        with patch.object(self.cm, "_trigger_save") as mock_save:
            self.cm.clear_connections_by_party("BPNL000000000065")
            mock_save.assert_called_once()

    def test_trigger_save_not_called_when_nothing_removed(self):
        """_trigger_save() must NOT be called if no match was found."""
        with patch.object(self.cm, "_trigger_save") as mock_save:
            self.cm.clear_connections_by_party("BPNL999999999999")
            mock_save.assert_not_called()

    # --- persistence ------------------------------------------------------

    def test_removed_entries_not_persisted_after_save(self):
        """After the background save, evicted parties must not be in the DB."""
        did = "did:web:wallet.example.com:BPNL000000000065"
        _add(self.cm, did)
        # Ensure the initial save completes.
        self.cm.stop()

        # Evict and force a synchronous save.
        self.cm.clear_connections_by_party("BPNL000000000065")
        self.cm.stop()

        # Reload a fresh manager from the same engine; the party must be absent.
        cm2 = PostgresMemoryConnectionManager(
            engine=self.engine,
            provider_id_key=PROVIDER_ID_KEY,
            table_name="test_edr_connections",
        )
        self.assertNotIn(did, cm2.open_connections)
        cm2.stop()

    def test_unrelated_entries_remain_after_save(self):
        """After eviction and save, parties that were not matched stay in the DB."""
        did_a = "did:web:wallet.example.com:BPNL000000000065"
        did_b = "did:web:wallet.example.com:BPNL000000000099"
        _add(self.cm, did_a, transfer_id="tp-a")
        _add(self.cm, did_b, transfer_id="tp-b")
        self.cm.stop()

        self.cm.clear_connections_by_party("BPNL000000000065")
        self.cm.stop()

        cm2 = PostgresMemoryConnectionManager(
            engine=self.engine,
            provider_id_key=PROVIDER_ID_KEY,
            table_name="test_edr_connections",
        )
        self.assertIn(did_b, cm2.open_connections)
        cm2.stop()

    # --- returns correct count -------------------------------------------

    def test_returns_count_from_memory_manager(self):
        _add(self.cm, "did:web:wallet.example.com:BPNL000000000001", transfer_id="tp-1")
        _add(self.cm, "did:web:wallet.example.com:BPNL000000000002", transfer_id="tp-2")

        removed = self.cm.clear_connections_by_party("BPNL000000000001")

        self.assertEqual(removed, 1)


if __name__ == "__main__":
    unittest.main()
