#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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
FileSystem-based connection manager for persisting EDR connections to disk.
Extends MemoryConnectionManager to support persistence using JSON files with file-based locking.
"""
## Code created partially using a LLM (GPT 4o) and reviewed by a human committer

import json
import logging
import os
import threading
import time
from filelock import FileLock
from ..memory import MemoryConnectionManager
import hashlib

logger = logging.getLogger(__name__)

class FileSystemConnectionManager(MemoryConnectionManager):
    """
    Manages EDR connections with persistence to the filesystem using JSON files.
    Periodically saves and reloads data from disk to keep in-memory cache synchronized.
    """
    
    file_path: str
    lock: FileLock
    persist_interval: int
    _stop_event: threading.Event
    
    def __init__(self, path: str = "./data/connection_cache.json", persist_interval: int = 5):
        """
        Initialize the file system connection manager with periodic persistence.

        Args:
            path (str): Path to the JSON file used for persisting connections.
            persist_interval (int): Time interval in seconds for saving and reloading connections.
        """
        # Set up the file path, file lock, and background persistence thread.
        super().__init__()
        self.file_path = path
        self.lock = FileLock(f"{self.file_path}.lock")
        self.persist_interval = persist_interval
        self._stop_event = threading.Event()
        self._last_loaded_hash = None
        self._load_if_updated()
        logger.debug("[FileSystemConnectionManager] Persisting the connections to '%s' every %s seconds", self.file_path, self.persist_interval)
        self._start_background_tasks()

    def _start_background_tasks(self):
        """
        Start the background thread for periodic persistence.
        """
        threading.Thread(target=self._persistence_loop, daemon=True).start()

    def _persistence_loop(self):
        """
        Background thread loop to periodically save to and load from the JSON file.
        """
        while not self._stop_event.is_set():
            time.sleep(self.persist_interval)
            self._save_to_file()
            self._load_if_updated()

    def _save_to_file(self):
        """
        Save current in-memory connections to a JSON file with file locking if it differs from the last saved state.
        """
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            current_hash = self._calculate_hash(self.open_connections)
            if current_hash == self._last_loaded_hash:
                return
            with self.lock:
                with open(self.file_path, "w") as f:
                    json.dump(self.open_connections, f)
                self._last_loaded_hash = current_hash
            logger.debug("[FileSystemConnectionManager] Saved the connections to '%s'", self.file_path)
        except Exception:
            logger.exception("[FileSystemConnectionManager] Error saving to file '%s'", self.file_path)

    def _load_if_updated(self):
        """
        Load connections from the JSON file if the content differs from the current in-memory state.
        """
        try:
            if not os.path.exists(self.file_path):
                return
            with self.lock:
                with open(self.file_path, "r") as f:
                    file_connections = json.load(f)
                file_hash = self._calculate_hash(file_connections)
                if file_hash != self._last_loaded_hash:
                    self.open_connections = file_connections
                    self._last_loaded_hash = file_hash
                    logger.debug("[FileSystemConnectionManager] Reloaded the connections from '%s' (changed on disk)", self.file_path)
        except Exception:
            logger.exception("[FileSystemConnectionManager] Error loading from file '%s'", self.file_path)

    def _calculate_hash(self, data):
        """
        Generate a hash from the current connections data for change detection.
        """
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

    def stop(self):
        """
        Stop the background persistence thread.
        """
        logger.debug("[FileSystemConnectionManager] Stopping the persistence thread")
        self._stop_event.set()