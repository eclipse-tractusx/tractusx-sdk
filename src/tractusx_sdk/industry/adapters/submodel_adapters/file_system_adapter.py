#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 DRÄXLMAIER Group
# (represented by Lisa Dräxlmaier GmbH)
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

from .. import SubmodelAdapter
import os
from pathlib import Path
from tractusx_sdk.dataspace.tools import op
from typing import Any, List, Mapping

class FileSystemAdapter(SubmodelAdapter):

    def __init__(
            self,
            root_path: str,
            path_pattern: str | None = None,
    ):
        # Convert relative path to absolute path if needed
        if not os.path.isabs(root_path):
            root_path = os.path.abspath(root_path)
        
        # Ensure the directory exists and check permissions
        try:
            path_obj = Path(root_path)
            path_obj.mkdir(parents=True, exist_ok=True)
            
            # Check if we have write permissions using os.access()
            if not os.access(root_path, os.W_OK):
                raise PermissionError(
                    f"No write permission for directory: {root_path}"
                )
            
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied accessing submodel storage path: {root_path}. Error: {e}" 
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize submodel storage: {e}") from e
        self.root_path = root_path

        # Default pattern maps submodel_metadata["path"] directly to a file path.
        self.path_pattern = "{path}"

        # Explicit pattern can redefine how submodel_metadata fields map to a path.
        if path_pattern is not None:
            self.path_pattern = path_pattern

        if not isinstance(self.path_pattern, str) or not self.path_pattern.strip():
            raise ValueError("path_pattern must be a non-empty string")
        print("FileSystem initilized")

    @classmethod
    def builder(cls):
        return cls._Builder(cls)

    class _Builder:
        def __init__(self, cls):
            self.cls = cls
            self._data = {}

        def root_path(self, path: str):
            self._data["root_path"] = path
            return self

        def path_pattern(self, pattern: str):
            self._data["path_pattern"] = pattern
            return self
        
        def build(self):
            if "root_path" not in self._data:
                raise ValueError("Missing required buider parameter: root_path")
            return self.cls(**self._data)

    def _extract_relative_path(self, submodel_metadata: Mapping[str, Any]) -> str:
        """
        Resolve the relative file path from key/value input.
        """
        if not isinstance(submodel_metadata, Mapping):
            raise TypeError("submodel_metadata must be a mapping")

        try:
            relative_path = self.path_pattern.format(**submodel_metadata)
        except KeyError as key_error:
            raise KeyError(
                f"Missing required path key '{key_error.args[0]}' for pattern '{self.path_pattern}'"
            ) from key_error

        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("Resolved path value must be a non-empty string")

        return relative_path

    def _cleanup_empty_parent_directories(self, file_path: str) -> None:
        """
        Remove empty parent directories up to (but excluding) root_path.
        """
        current = Path(file_path).parent
        root = Path(self.root_path)

        while current != root and current.exists():
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent
    

    def read(self, submodel_metadata: Mapping[str, Any]):
        """
        Return the entire content of a file
        """
        path = self._extract_relative_path(submodel_metadata)
        total_path = op.join_paths(self.root_path, path)
        return op.read_json_file(total_path)
         

    def write(self, submodel_metadata: Mapping[str, Any], content: bytes) -> None:
        """
        Write raw bytes to a file.
        """
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")

        path = self._extract_relative_path(submodel_metadata)
        total_path = op.join_paths(self.root_path, path)
        Path(total_path).parent.mkdir(parents=True, exist_ok=True)
        Path(total_path).write_bytes(content)

    def write_json(self, submodel_metadata: Mapping[str, Any], content: Mapping[str, Any] | None) -> None:
        """
        Write JSON content to a file.
        """
        if content is not None and not isinstance(content, Mapping):
            raise TypeError("content must be a mapping or None")

        path = self._extract_relative_path(submodel_metadata)
        total_path = op.join_paths(self.root_path, path)
        Path(total_path).parent.mkdir(parents=True, exist_ok=True)
        op.to_json_file(content, json_file_path=total_path)

    def delete(self, submodel_metadata: Mapping[str, Any]) -> None:
        """
        Delete a specific file
        """
        path = self._extract_relative_path(submodel_metadata)
        total_path = op.join_paths(self.root_path, path)
        op.delete_file(total_path)
        self._cleanup_empty_parent_directories(total_path)

    def exists(self, submodel_metadata: Mapping[str, Any]) -> bool:
        """
        Check if a file exists
        """
        path = self._extract_relative_path(submodel_metadata)
        total_path = op.join_paths(self.root_path, path)
        return op.path_exists(total_path)

    def list_contents(self, directory_path: str) -> List[dict]:
        """
        Return a list of files based in a directory
        """
        results = []
        total_path = op.join_paths(self.root_path, directory_path)
        for entry_name in op.list_directories(total_path):
            entry_abs_path = op.join_paths(total_path, entry_name)
            if op.is_file(entry_abs_path):
                try:
                    results.append(entry_abs_path)
                except FileNotFoundError:
                    continue
                except PermissionError:
                    continue
        return results


