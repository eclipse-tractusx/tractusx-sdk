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
## Code created partially using a LLM (GPT 4o) and reviewed by a human committer

from .postgres_memory_connection_manager import PostgresMemoryConnectionManager
from sqlalchemy.engine import Engine as E
from sqlalchemy.orm import Session as S
import threading
import time
import logging

class PostgresMemoryRefreshConnectionManager(PostgresMemoryConnectionManager):
    """
    Manages EDR connections using an in-memory cache synchronized with a Postgres database.
    Periodically persists changes and reloads updates from the database to ensure consistency.
    """
    def __init__(self, engine: E | S, persist_interval: int = 5, provider_id_key: str = "providerId", table_name: str = "edr_connections", edrs_key: str = "edrs", logger:logging.Logger=None, verbose: bool = False):
        """
        Initialize the connection manager with persistence and reload functionality.

        Args:
            engine (Engine | Session): SQLAlchemy engine or session.
            persist_interval (int): Time in seconds between persistence checks.
            provider_id_key (str): Key to identify provider ID.
            table_name (str): Table name for EDR connections.
            edrs_key (str): Key used for storing EDR counts.
            logger (Logger, optional): Logger instance for debug output.
            verbose (bool): Enable verbose logging.
        """
        super().__init__(engine=engine, provider_id_key=provider_id_key, table_name=table_name, edrs_key=edrs_key, logger=logger, verbose=verbose)
        self.persist_interval = persist_interval
        self._stop_event = threading.Event()
        self._start_background_tasks()

    def _start_background_tasks(self):
        """
        Start the background thread for periodic persistence and reloading from DB.
        """
        threading.Thread(target=self._persistence_loop, daemon=True).start()

    def _persistence_loop(self):
        """
        Periodically save current in-memory connections to DB and reload any changes.
        """
        while not self._stop_event.is_set():
            time.sleep(self.persist_interval)
            self._save_to_db()
            self._load_from_db()

    def stop(self):
        """
        Stop the background thread and perform a final save to the DB.
        """
        if self._save_thread:
            self._save_thread.join()
        self._stop_event.set()
        self._save_to_db()