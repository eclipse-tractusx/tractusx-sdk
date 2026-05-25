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

import json
import unittest
from unittest.mock import patch, MagicMock

from moto import mock_aws
import boto3

from tractusx_sdk.industry.adapters.submodel_adapters import S3Adapter
from tractusx_sdk.industry.adapters.submodel_adapter_factory import SubmodelAdapterFactory


@mock_aws
class TestS3Adapter(unittest.TestCase):
    """Test S3Adapter with fully mocked AWS S3 (using moto)"""

    def setUp(self):
        """Set up mocked S3 environment before each test"""
        # Create a mock S3 bucket
        self.bucket_name = "test-bucket"
        self.region_name = "eu-central-1"
        
        # Create the bucket using boto3 (which is mocked by @mock_s3)
        s3_client = boto3.client("s3", region_name=self.region_name)
        s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={"LocationConstraint": self.region_name}
        )

    def test_adapter_initialization_with_required_params(self):
        """Test S3Adapter initializes with required bucket_name and region_name"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        
        self.assertEqual(adapter.bucket_name, self.bucket_name)
        self.assertEqual(adapter.key_pattern, "{path}")

    def test_adapter_initialization_with_custom_key_pattern(self):
        """Test S3Adapter initializes with custom key_pattern"""
        key_pattern = "{semantic_id}/{submodel_id}.json"
        adapter = S3Adapter(
            bucket_name=self.bucket_name,
            region_name=self.region_name,
            key_pattern=key_pattern
        )
        
        self.assertEqual(adapter.key_pattern, key_pattern)

    def test_adapter_initialization_with_region(self):
        """Test S3Adapter initializes with custom region"""
        adapter = S3Adapter(
            bucket_name=self.bucket_name,
            region_name=self.region_name
        )
        
        self.assertIsNotNone(adapter.client)

    def test_adapter_initialization_missing_bucket_name(self):
        """Test S3Adapter raises ValueError when bucket_name is missing"""
        with self.assertRaises(ValueError) as context:
            S3Adapter(bucket_name="", region_name=self.region_name)
        
        self.assertIn("bucket_name must be a non-empty string", str(context.exception))

    def test_adapter_initialization_invalid_bucket_name_type(self):
        """Test S3Adapter raises ValueError when bucket_name is not a string"""
        with self.assertRaises(ValueError) as context:
            S3Adapter(bucket_name=None, region_name=self.region_name)
        
        self.assertIn("bucket_name must be a non-empty string", str(context.exception))

    def test_adapter_initialization_empty_key_pattern(self):
        """Test S3Adapter raises ValueError when key_pattern is empty"""
        with self.assertRaises(ValueError) as context:
            S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name, key_pattern="")
        
        self.assertIn("key_pattern must be a non-empty string", str(context.exception))

    def test_adapter_initialization_credentials_both_provided(self):
        """Test S3Adapter accepts credentials when both are provided"""
        adapter = S3Adapter(
            bucket_name=self.bucket_name,
            region_name=self.region_name,
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret"
        )
        
        self.assertIsNotNone(adapter.client)

    def test_adapter_initialization_only_access_key(self):
        """Test S3Adapter raises ValueError when only access key is provided"""
        with self.assertRaises(ValueError) as context:
            S3Adapter(
                bucket_name=self.bucket_name,
                region_name=self.region_name,
                aws_access_key_id="test-key"
            )
        
        self.assertIn("Both aws_access_key_id and aws_secret_access_key must be provided together", 
                     str(context.exception))

    def test_adapter_initialization_only_secret_key(self):
        """Test S3Adapter raises ValueError when only secret key is provided"""
        with self.assertRaises(ValueError) as context:
            S3Adapter(
                bucket_name=self.bucket_name,
                region_name=self.region_name,
                aws_secret_access_key="test-secret"
            )
        
        self.assertIn("Both aws_access_key_id and aws_secret_access_key must be provided together",
                     str(context.exception))

    def test_write_json_success(self):
        """Test successful JSON write to S3"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/test.json"}
        content = {"id": "test-id", "name": "test-submodel"}
        
        adapter.write_json(metadata, content)
        
        # Verify the object was written
        response = adapter.client.get_object(Bucket=self.bucket_name, Key="submodels/test.json")
        written_content = json.loads(response["Body"].read())
        self.assertEqual(written_content, content)

    def test_write_json_with_none_content(self):
        """Test writing None as JSON content"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/test.json"}
        
        adapter.write_json(metadata, None)
        
        # Verify null was written
        response = adapter.client.get_object(Bucket=self.bucket_name, Key="submodels/test.json")
        written_content = json.loads(response["Body"].read())
        self.assertIsNone(written_content)

    def test_write_json_invalid_content_type(self):
        """Test write_json raises TypeError for non-mapping content"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/test.json"}
        
        with self.assertRaises(TypeError) as context:
            adapter.write_json(metadata, ["not", "a", "mapping"])
        
        self.assertIn("content must be a mapping or None", str(context.exception))

    def test_write_json_with_custom_key_pattern(self):
        """Test write_json with custom key pattern"""
        key_pattern = "{semantic_id}/{submodel_id}.json"
        adapter = S3Adapter(
            bucket_name=self.bucket_name,
            region_name=self.region_name,
            key_pattern=key_pattern
        )
        metadata = {"semantic_id": "urn:example:semantic", "submodel_id": "sub-123"}
        content = {"data": "test"}
        
        adapter.write_json(metadata, content)
        
        # Verify object was written to correct key
        response = adapter.client.get_object(
            Bucket=self.bucket_name, 
            Key="urn:example:semantic/sub-123.json"
        )
        self.assertIsNotNone(response)

    def test_write_json_missing_pattern_key(self):
        """Test write_json raises KeyError when pattern key is missing"""
        key_pattern = "{semantic_id}/{submodel_id}.json"
        adapter = S3Adapter(
            bucket_name=self.bucket_name,
            region_name=self.region_name,
            key_pattern=key_pattern
        )
        metadata = {"semantic_id": "urn:example:semantic"}  # missing submodel_id
        
        with self.assertRaises(KeyError) as context:
            adapter.write_json(metadata, {"data": "test"})
        
        self.assertIn("submodel_id", str(context.exception))

    def test_write_bytes_success(self):
        """Test successful bytes write to S3"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "binary/data.bin"}
        content = b"binary content"
        
        adapter.write(metadata, content)
        
        # Verify the object was written
        response = adapter.client.get_object(Bucket=self.bucket_name, Key="binary/data.bin")
        written_content = response["Body"].read()
        self.assertEqual(written_content, content)

    def test_write_bytes_invalid_type(self):
        """Test write raises TypeError for non-bytes content"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "binary/data.bin"}
        
        with self.assertRaises(TypeError) as context:
            adapter.write(metadata, "not bytes")
        
        self.assertIn("Content must be bytes", str(context.exception))

    def test_read_success(self):
        """Test successful read from S3"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/test.json"}
        original_content = {"id": "test-id", "data": "test-data"}
        
        # Write first
        adapter.write_json(metadata, original_content)
        
        # Read back
        read_content = adapter.read(metadata)
        self.assertEqual(read_content, original_content)

    def test_read_after_raw_bytes_write_raises_json_decode_error(self):
        """Test read raises JSONDecodeError after writing non-JSON raw bytes"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "binary/non-json.bin"}

        adapter.write(metadata, b"not-a-json-document")

        with self.assertRaises(json.JSONDecodeError):
            adapter.read(metadata)

    def test_read_nonexistent_object(self):
        """Test read raises FileNotFoundError for nonexistent object"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/nonexistent.json"}
        
        with self.assertRaises(FileNotFoundError) as context:
            adapter.read(metadata)
        
        self.assertIn("Submodel not found in S3", str(context.exception))

    def test_read_invalid_metadata_type(self):
        """Test read raises TypeError for invalid metadata type"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        
        with self.assertRaises(TypeError) as context:
            adapter.read("not a mapping")
        
        self.assertIn("submodel_metadata must be a mapping", str(context.exception))

    def test_exists_true(self):
        """Test exists returns True for existing object"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/test.json"}
        
        adapter.write_json(metadata, {"test": "data"})
        
        self.assertTrue(adapter.exists(metadata))

    def test_exists_false(self):
        """Test exists returns False for nonexistent object"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/nonexistent.json"}
        
        self.assertFalse(adapter.exists(metadata))

    def test_delete_success(self):
        """Test successful delete from S3"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/test.json"}
        
        adapter.write_json(metadata, {"test": "data"})
        self.assertTrue(adapter.exists(metadata))
        
        adapter.delete(metadata)
        self.assertFalse(adapter.exists(metadata))

    def test_delete_nonexistent_object(self):
        """Test delete of nonexistent object doesn't raise error"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/nonexistent.json"}
        
        # Should not raise an error
        adapter.delete(metadata)

    def test_list_contents_empty_bucket(self):
        """Test list_contents returns empty list for empty bucket"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        
        contents = adapter.list_contents()
        self.assertEqual(contents, [])

    def test_list_contents_with_objects(self):
        """Test list_contents returns all objects"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        
        # Write multiple objects
        adapter.write_json({"path": "file1.json"}, {"id": 1})
        adapter.write_json({"path": "file2.json"}, {"id": 2})
        adapter.write_json({"path": "subdir/file3.json"}, {"id": 3})
        
        contents = adapter.list_contents()
        self.assertEqual(len(contents), 3)
        self.assertIn("file1.json", contents)
        self.assertIn("file2.json", contents)
        self.assertIn("subdir/file3.json", contents)

    def test_list_contents_with_prefix(self):
        """Test list_contents filters by prefix"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        
        # Write objects with different prefixes
        adapter.write_json({"path": "subdir1/file1.json"}, {"id": 1})
        adapter.write_json({"path": "subdir1/file2.json"}, {"id": 2})
        adapter.write_json({"path": "subdir2/file3.json"}, {"id": 3})
        
        contents = adapter.list_contents(prefix="subdir1/")
        self.assertEqual(len(contents), 2)
        self.assertTrue(all(key.startswith("subdir1/") for key in contents))

    def test_list_contents_invalid_prefix_type(self):
        """Test list_contents with None prefix works"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        adapter.write_json({"path": "file1.json"}, {"id": 1})
        
        contents = adapter.list_contents(prefix=None)
        self.assertEqual(len(contents), 1)

    def test_builder_pattern_basic(self):
        """Test S3Adapter builder with basic configuration"""
        adapter = (S3Adapter.builder()
                   .bucket_name(self.bucket_name)
                   .region_name(self.region_name)
                   .build())
        
        self.assertEqual(adapter.bucket_name, self.bucket_name)
        self.assertEqual(adapter.key_pattern, "{path}")

    def test_builder_pattern_all_options(self):
        """Test S3Adapter builder with all options"""
        key_pattern = "{id}/{name}.json"
        adapter = (S3Adapter.builder()
                   .bucket_name(self.bucket_name)
                   .key_pattern(key_pattern)
                   .region_name(self.region_name)
                   .endpoint_url("http://localhost:9000")
                   .aws_access_key_id("test-key")
                   .aws_secret_access_key("test-secret")
                   .build())
        
        self.assertEqual(adapter.bucket_name, self.bucket_name)
        self.assertEqual(adapter.key_pattern, key_pattern)

    def test_builder_pattern_missing_required_bucket_name(self):
        """Test builder raises ValueError when required parameters are not provided"""
        with self.assertRaises(ValueError) as context:
            S3Adapter.builder().build()
        
        self.assertIn("Missing required builder parameter", str(context.exception))

    def test_builder_pattern_chaining(self):
        """Test builder supports method chaining"""
        builder = S3Adapter.builder()
        result = (builder
                  .bucket_name(self.bucket_name)
                  .region_name(self.region_name)
                  .key_pattern("{path}"))
        
        # Verify chaining returns builder instance
        self.assertIs(result, builder)

    def test_extract_key_simple_pattern(self):
        """Test _extract_key with simple pattern"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name, key_pattern="{path}")
        metadata = {"path": "submodels/test.json"}
        
        key = adapter._extract_key(metadata)
        self.assertEqual(key, "submodels/test.json")

    def test_extract_key_complex_pattern(self):
        """Test _extract_key with complex multi-field pattern"""
        pattern = "{semantic_id}/{submodel_id}/{version}.json"
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name, key_pattern=pattern)
        metadata = {
            "semantic_id": "urn:example",
            "submodel_id": "sub-123",
            "version": "1.0"
        }
        
        key = adapter._extract_key(metadata)
        self.assertEqual(key, "urn:example/sub-123/1.0.json")

    def test_extract_key_invalid_metadata_type(self):
        """Test _extract_key raises TypeError for non-mapping metadata"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        
        with self.assertRaises(TypeError) as context:
            adapter._extract_key("not a mapping")
        
        self.assertIn("submodel_metadata must be a mapping", str(context.exception))

    def test_extract_key_missing_field(self):
        """Test _extract_key raises KeyError for missing pattern field"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name, key_pattern="{semantic_id}/{submodel_id}.json")
        metadata = {"semantic_id": "urn:example"}  # missing submodel_id
        
        with self.assertRaises(KeyError) as context:
            adapter._extract_key(metadata)
        
        self.assertIn("submodel_id", str(context.exception))

    def test_write_json_content_type_header(self):
        """Test write_json sets correct ContentType header"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "submodels/test.json"}
        
        adapter.write_json(metadata, {"test": "data"})
        
        # Verify ContentType is set to application/json
        response = adapter.client.head_object(Bucket=self.bucket_name, Key="submodels/test.json")
        self.assertEqual(response["ContentType"], "application/json")

    def test_write_bytes_preserves_content(self):
        """Test write preserves binary content exactly"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "binary/data.bin"}
        original_bytes = b"\x00\x01\x02\x03\x04\x05"
        
        adapter.write(metadata, original_bytes)
        
        response = adapter.client.get_object(Bucket=self.bucket_name, Key="binary/data.bin")
        written_bytes = response["Body"].read()
        self.assertEqual(written_bytes, original_bytes)

    def test_read_write_roundtrip_complex_object(self):
        """Test read/write roundtrip preserves complex nested objects"""
        adapter = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name)
        metadata = {"path": "complex/object.json"}
        original_object = {
            "id": "test-123",
            "nested": {
                "level1": {
                    "level2": ["a", "b", "c"]
                }
            },
            "data": [1, 2, 3],
            "flag": True,
            "value": None
        }
        
        adapter.write_json(metadata, original_object)
        read_object = adapter.read(metadata)
        
        self.assertEqual(read_object, original_object)

    def test_multiple_adapters_same_bucket(self):
        """Test multiple adapter instances can operate on same bucket"""
        adapter1 = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name, key_pattern="{file_a}")
        adapter2 = S3Adapter(bucket_name=self.bucket_name, region_name=self.region_name, key_pattern="{file_b}")
        
        adapter1.write_json({"file_a": "object1.json"}, {"source": "adapter1"})
        adapter2.write_json({"file_b": "object2.json"}, {"source": "adapter2"})
        
        # Both should be readable by either adapter
        content1 = adapter1.read({"file_a": "object1.json"})
        content2 = adapter2.read({"file_b": "object2.json"})
        
        self.assertEqual(content1["source"], "adapter1")
        self.assertEqual(content2["source"], "adapter2")

    def test_factory_plus_s3_adapter_integration(self):
        """Test factory-based S3 adapter integration for write/read/exists/list/delete"""
        adapter = SubmodelAdapterFactory.get_s3(
            bucket_name=self.bucket_name,
            key_pattern="{asset_id}/{submodel_id}.json",
            region_name=self.region_name,
        )

        self.assertIsInstance(adapter, S3Adapter)

        metadata = {"asset_id": "asset-001", "submodel_id": "sm-001"}
        content = {"asset": "asset-001", "submodel": "sm-001", "status": "ok"}

        adapter.write_json(metadata, content)
        self.assertTrue(adapter.exists(metadata))

        read_content = adapter.read(metadata)
        self.assertEqual(read_content, content)

        keys = adapter.list_contents(prefix="asset-001/")
        self.assertIn("asset-001/sm-001.json", keys)

        adapter.delete(metadata)
        self.assertFalse(adapter.exists(metadata))

    def test_factory_from_config_s3_adapter(self):
        """Test factory from_config directly with S3 adapter"""
        adapter = SubmodelAdapterFactory.from_config(
            adapter_type="s3",
            config={
                "bucket_name": self.bucket_name,
                "key_pattern": "{asset_id}/{submodel_id}.json",
                "region_name": self.region_name,
            }
        )

        self.assertIsInstance(adapter, S3Adapter)
        self.assertEqual(adapter.bucket_name, self.bucket_name)
        self.assertEqual(adapter.key_pattern, "{asset_id}/{submodel_id}.json")

        metadata = {"asset_id": "asset-002", "submodel_id": "sm-002"}
        content = {"test": "data from from_config"}

        adapter.write_json(metadata, content)
        self.assertTrue(adapter.exists(metadata))

        read_content = adapter.read(metadata)
        self.assertEqual(read_content, content)

        adapter.delete(metadata)
        self.assertFalse(adapter.exists(metadata))


if __name__ == "__main__":
    unittest.main()
