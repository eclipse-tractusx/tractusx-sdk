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

import json
import os
import threading
import time
from filelock import FileLock
from ..memory import MemoryConnectionManager

class FileSystemConnectionManager(MemoryConnectionManager):
    
    file_path: str
    lock: FileLock
    persist_interval: int
    _last_modified_time: int
    _stop_event: threading.Event

    def __init__(self, path: str = "/data/connection_cache.json", persist_interval: int = 5, provider_id_key: str = "providerId", edrs_key: str = "edrs"):
        super().__init__(provider_id_key=provider_id_key, edrs_key=edrs_key)
        self.file_path = path
        self.lock = FileLock(f"{self.file_path}.lock")
        self.persist_interval = persist_interval
        self._last_modified_time = 0
        self._stop_event = threading.Event()
        self._start_background_tasks()

    def _start_background_tasks(self):
        threading.Thread(target=self._persistence_loop, daemon=True).start()

    def _persistence_loop(self):
        while not self._stop_event.is_set():
            time.sleep(self.persist_interval)
            self._save_to_file()
            self._load_if_updated()

    def _save_to_file(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with self.lock:
                with open(self.file_path, "w") as f:
                    json.dump(self.open_connections, f)
                self._last_modified_time = os.path.getmtime(self.file_path)
        except Exception as e:
            print(f"[FileSystemConnectionManager] Error saving to file: {e}")

    def _load_if_updated(self):
        try:
            if not os.path.exists(self.file_path):
                return
            modified_time = os.path.getmtime(self.file_path)
            if modified_time > self._last_modified_time:
                with self.lock:
                    with open(self.file_path, "r") as f:
                        self.open_connections = json.load(f)
                self._last_modified_time = modified_time
        except Exception as e:
            print(f"[FileSystemConnectionManager] Error loading from file: {e}")

    def stop(self):
        self._stop_event.set()