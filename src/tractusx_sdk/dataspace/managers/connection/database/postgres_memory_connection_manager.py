#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
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
## Code created partially using a LLM (GPT 4o) and reviewed by a human committer

import threading
import hashlib
import json
from ....models.connection.database.edr_base import EDRBase
from sqlmodel import select, delete, Session, SQLModel
from sqlalchemy.exc import SQLAlchemyError
from ..memory.memory_connection_manager import MemoryConnectionManager
import logging
from ....constants import JSONLDKeys  


class PostgresMemoryConnectionManager(MemoryConnectionManager):
    """
    Connection manager for storing and synchronizing EDR connections between memory and a Postgres database.
    Inherits from MemoryConnectionManager to maintain an in-memory cache and extends it with persistent storage functionality.
    """

    def __init__(self, engine, provider_id_key="providerId", table_name="edr_connections", edrs_key="edrs", logger:logging.Logger=None, verbose:bool=False):
        """
        Initialize the Postgres memory-backed connection manager.

        Args:
            engine: SQLAlchemy engine or session for database operations.
            provider_id_key: Key for identifying the provider ID.
            table_name: Name of the database table for storing EDR connections.
            edrs_key: Key used to store EDR counts within open_connections.
            logger: Optional logger instance for debug output.
            verbose: Flag for enabling verbose logging.
        """
        # Initialize base memory connection manager and configure database.
        # Dynamically define the SQLModel table for EDR connections.
        # Load existing data from the database into memory.
        super().__init__(provider_id_key=provider_id_key, edrs_key=edrs_key, logger=logger, verbose=verbose)
        self.engine = engine
        self.provider_id_key = provider_id_key
        self.table_name = table_name
        self.open_connections = {}
        self._stop_event = threading.Event()
        self.edrs_key = edrs_key
        self._save_thread = None
        self._last_saved_hash = None
        SQLModel.metadata.create_all(engine)
        class DynamicEDRConnection(EDRBase, table=True):
            __tablename__ = table_name
            __table_args__ = {"extend_existing": True}

        self.EDRConnection = DynamicEDRConnection
        DynamicEDRConnection.metadata.create_all(engine)
        self._load_from_db()

    def add_connection(self, counter_party_id, counter_party_address, query_checksum, policy_checksum, connection_entry) -> str:
        """
        Add a new EDR connection and trigger database persistence.

        Args:
            counter_party_id: ID of the counter party.
            counter_party_address: Address of the counter party.
            query_checksum: Checksum identifying the query.
            policy_checksum: Checksum identifying the policy.
            connection_entry: Dictionary of connection metadata.

        Returns:
            The transfer process ID of the added connection.
        """
        # Delegate to the base memory manager and trigger persistence in the background.
        response = super().add_connection(counter_party_id, counter_party_address, query_checksum, policy_checksum, connection_entry)
        self._trigger_save()
        return response

    def delete_connection(self, counter_party_id, counter_party_address, query_checksum, policy_checksum) -> bool:
        """
        Delete an EDR connection and trigger database persistence.

        Args:
            counter_party_id: ID of the counter party.
            counter_party_address: Address of the counter party.
            query_checksum: Checksum identifying the query.
            policy_checksum: Checksum identifying the policy.

        Returns:
            True if the connection was deleted successfully.
        """
        # Delegate to the base memory manager and trigger persistence in the background.
        super().delete_connection(counter_party_id, counter_party_address, query_checksum, policy_checksum)

        self._trigger_save()
        return True

    def clear_connections_by_party(self, counter_party_id_substring: str) -> int:
        """
        Removes all cached EDR connections whose ``counter_party_id`` key contains
        ``counter_party_id_substring`` and triggers database persistence.

        Args:
            counter_party_id_substring (str): Substring to match against each
                ``counter_party_id`` key (e.g. ``"BPNL000000000065"``).

        Returns:
            int: Number of top-level party entries removed from the cache.
        """
        removed = super().clear_connections_by_party(counter_party_id_substring)
        if removed > 0:
            self._trigger_save()
        return removed

    def _trigger_save(self):
        """
        Trigger a background thread to persist current connections to the database.
        Skips if a save is already in progress.
        """
        if self._save_thread and self._save_thread.is_alive():
            return
        self._save_thread = threading.Thread(target=self._save_to_db, daemon=True)
        self._save_thread.start()
        
    def _load_from_db(self):
        """
        Reload connections from the DB if any hashes have changed compared to memory.
        """
        # Calculate current hashes and skip if unchanged.
        # Rebuild in-memory connections from DB rows.
        with self._lock:
            try:
                with Session(self.engine) as session:
                    db_hashes = {
                        hash for hash in session.exec(select(self.EDRConnection.edr_hash)).all()
                    }
                    current_hashes = {
                        self._calculate_connection_hash(provider_id, endpoint, query_checksum, policy_checksum)
                        for provider_id, endpoints in self.open_connections.items() if provider_id != self.edrs_key
                        for endpoint, queries in endpoints.items() if endpoint != self.edrs_key
                        for query_checksum in queries
                        for policy_checksum in queries[query_checksum]
                    }
                    if current_hashes == db_hashes:
                        return

                    _loaded_edrs = 0
                    self.open_connections = {}
                    result = session.exec(select(self.EDRConnection)).all()
                    for row in result:
                        provider_id = row.counter_party_id
                        endpoint = row.counter_party_address
                        query_checksum = row.query_checksum
                        policy_checksum = row.policy_checksum
                        edr_data = row.edr_data

                        if provider_id not in self.open_connections:
                            self.open_connections[provider_id] = {}
                        if endpoint not in self.open_connections[provider_id]:
                            self.open_connections[provider_id][endpoint] = {}
                        if query_checksum not in self.open_connections[provider_id][endpoint]:
                            self.open_connections[provider_id][endpoint][query_checksum] = {}
                        self.open_connections[provider_id][endpoint][query_checksum][policy_checksum] = edr_data
                        _loaded_edrs += 1

                    self.open_connections[self.edrs_key] = _loaded_edrs
                if self.logger and self.verbose:
                    self.logger.info(f"[PostgresMemoryConnectionManager] Loaded {_loaded_edrs} edrs from the database.")
                self._last_saved_hash = hashlib.sha256(json.dumps(self.open_connections, sort_keys=True, default=str).encode()).hexdigest()
            except SQLAlchemyError as e:
                if self.logger and self.verbose:
                    self.logger.error(f"[PostgresMemoryConnectionManager] Error loading from db: {e}")
    
    def _calculate_connection_hash(self, provider_id, endpoint, query_checksum, policy_checksum):
        """
        Generate a SHA256 hash based on connection keys for change detection.
        """
        base_string = f"{provider_id}:{endpoint}:{query_checksum}:{policy_checksum}"
        return hashlib.sha256(base_string.encode()).hexdigest()
          
    def _save_to_db(self):
        """
        Persist current in-memory connections to the DB only if changes are detected.
        """
        # Clear table and repopulate from in-memory state.
        # Update saved hash after committing changes.
        with self._lock:
            current_hash = hashlib.sha256(json.dumps(self.open_connections, sort_keys=True, default=str).encode()).hexdigest()
            if current_hash == self._last_saved_hash:
                return
            try:
                _saved_edrs=0
                with Session(self.engine) as session:
                    session.exec(delete(self.EDRConnection))
                    for provider_id, endpoints in self.open_connections.items():
                        if provider_id == self.edrs_key:
                            continue
                        for endpoint, queries in endpoints.items():
                            for query_checksum, policies in queries.items():
                                for policy_checksum, edr_data in policies.items():
                                    hash_value = self._calculate_connection_hash(provider_id, endpoint, query_checksum, policy_checksum)
                                    session.add(self.EDRConnection(
                                        transfer_id=edr_data.get(JSONLDKeys.AT_ID),
                                        counter_party_id=provider_id,
                                        counter_party_address=endpoint,
                                        query_checksum=query_checksum,
                                        policy_checksum=policy_checksum,
                                        edr_data=edr_data,
                                        edr_hash=hash_value
                                    ))
                                    _saved_edrs+=1
                                    
                    session.commit()
                    self._last_saved_hash = current_hash
                    if self.logger and self.verbose:
                        self.logger.info(f"[PostgresMemoryConnectionManager] Saved {_saved_edrs} edrs to the database.")
            except SQLAlchemyError as e:
                if self.logger and self.verbose:
                    self.logger.error(f"[PostgresMemoryConnectionManager] Error saving to db: {e}")

    def stop(self):
        """
        Stop the background thread and perform a final save to the database.
        """
        if self._save_thread:
            self._save_thread.join()
        self._save_to_db()