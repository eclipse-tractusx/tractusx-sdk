#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 DRÄXLMAIER Group
# (represented by Lisa Dräxlmaier GmbH)
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

import tempfile
import unittest
from pathlib import Path

from tractusx_sdk.industry.adapters.submodel_adapters import FileSystemAdapter


class TestFileSystemAdapter(unittest.TestCase):

    def test_write_auto_creates_missing_parent_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write_json({"path": "nested/folder/file.json"}, {"hello": "world"})

            written_file = Path(temp_dir) / "nested" / "folder" / "file.json"
            self.assertTrue(written_file.exists())

    def test_delete_removes_empty_parent_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write_json({"path": "nested/folder/file.json"}, {"hello": "world"})
            adapter.delete({"path": "nested/folder/file.json"})

            nested_folder = Path(temp_dir) / "nested" / "folder"
            nested_root = Path(temp_dir) / "nested"
            self.assertFalse(nested_folder.exists())
            self.assertFalse(nested_root.exists())
            self.assertTrue(Path(temp_dir).exists())

    def test_delete_keeps_parent_folder_when_other_files_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write_json({"path": "nested/folder/file1.json"}, {"id": 1})
            adapter.write_json({"path": "nested/folder/file2.json"}, {"id": 2})

            adapter.delete({"path": "nested/folder/file1.json"})

            nested_folder = Path(temp_dir) / "nested" / "folder"
            remaining_file = nested_folder / "file2.json"
            self.assertTrue(nested_folder.exists())
            self.assertTrue(remaining_file.exists())

    def test_submodel_metadata_mapping_with_default_path_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write_json({"path": "nested/folder/file.json"}, {"hello": "world"})

            self.assertTrue(adapter.exists({"path": "nested/folder/file.json"}))
            content = adapter.read({"path": "nested/folder/file.json"})
            self.assertEqual(content["hello"], "world")

    def test_submodel_metadata_mapping_with_custom_path_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(
                root_path=temp_dir,
                path_pattern="{asset_path}",
            )

            adapter.write_json({"asset_path": "nested/folder/file.json"}, {"id": 1})

            self.assertTrue(adapter.exists({"asset_path": "nested/folder/file.json"}))
            adapter.delete({"asset_path": "nested/folder/file.json"})
            self.assertFalse(adapter.exists({"asset_path": "nested/folder/file.json"}))

    def test_path_pattern_with_multiple_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(
                root_path=temp_dir,
                path_pattern="{asset}/{subdir}/{name}.json",
            )

            submodel_metadata = {"asset": "a1", "subdir": "b1", "name": "f1"}
            adapter.write_json(submodel_metadata, {"ok": True})

            expected_file = Path(temp_dir) / "a1" / "b1" / "f1.json"
            self.assertTrue(expected_file.exists())
            self.assertTrue(adapter.exists(submodel_metadata))

    def test_submodel_metadata_mapping_missing_key_raises_key_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(
                root_path=temp_dir,
                path_pattern="{asset_path}",
            )

            with self.assertRaises(KeyError):
                adapter.exists({"path": "nested/folder/file.json"})

    def test_write_json_serializes_and_persists_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write_json({"path": "nested/folder/file.json"}, {"hello": "world"})

            content = adapter.read({"path": "nested/folder/file.json"})
            self.assertEqual(content, {"hello": "world"})

    def test_write_persists_raw_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            adapter.write({"path": "nested/folder/file.bin"}, b"raw-bytes")

            file_path = Path(temp_dir) / "nested" / "folder" / "file.bin"
            self.assertEqual(file_path.read_bytes(), b"raw-bytes")

    def test_path_pattern_missing_key_raises_key_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(
                root_path=temp_dir,
                path_pattern="{asset}/{name}.json",
            )

            with self.assertRaises(KeyError):
                adapter.exists({"asset": "a1"})

    def test_string_submodel_metadata_is_not_supported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = FileSystemAdapter(root_path=temp_dir)

            with self.assertRaises(TypeError):
                adapter.exists("nested/folder/file.json")
