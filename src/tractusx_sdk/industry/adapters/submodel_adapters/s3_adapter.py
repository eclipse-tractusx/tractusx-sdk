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
from typing import Any, Mapping

from .. import SubmodelAdapter


class S3Adapter(SubmodelAdapter):
    """
    S3 submodel adapter for AWS S3 and S3-compatible stores (e.g. MinIO).

    Stores each submodel as a JSON object in an S3 bucket. The object key is
    resolved from submodel metadata using a configurable ``key_pattern``,
    following the same ``{field}`` substitution convention as ``FileSystemAdapter``.

    Credentials can be provided explicitly via ``aws_access_key_id`` and
    ``aws_secret_access_key``, or automatically via environment variables
    (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY), IAM roles, or AWS config files.

    Example::

        adapter = SubmodelAdapterFactory.get_s3(
            bucket_name="my-submodels",
            key_pattern="{semantic_id}/{submodel_id}.json",
            region_name="eu-central-1",
            aws_access_key_id="YOUR_ACCESS_KEY",
            aws_secret_access_key="YOUR_SECRET_KEY",
        )
    """

    @classmethod
    def builder(cls):
        return cls._Builder(cls)

    class _Builder:
        def __init__(self, cls):
            self.cls = cls
            self._data = {}

        def bucket_name(self, bucket_name: str):
            self._data["bucket_name"] = bucket_name
            return self

        def key_pattern(self, key_pattern: str):
            self._data["key_pattern"] = key_pattern
            return self

        def region_name(self, region_name: str):
            self._data["region_name"] = region_name
            return self

        def endpoint_url(self, endpoint_url: str | None):
            self._data["endpoint_url"] = endpoint_url
            return self

        def aws_access_key_id(self, aws_access_key_id: str | None):
            self._data["aws_access_key_id"] = aws_access_key_id
            return self

        def aws_secret_access_key(self, aws_secret_access_key: str | None):
            self._data["aws_secret_access_key"] = aws_secret_access_key
            return self

        def build(self):
            if "bucket_name" not in self._data:
                raise ValueError("Missing required builder parameter: bucket_name")
            if "region_name" not in self._data:
                raise ValueError("Missing required builder parameter: region_name")
            return self.cls(**self._data)

    def __init__(
            self,
            bucket_name: str,
            region_name: str,
            key_pattern: str = "{path}",
            endpoint_url: str | None = None,
            aws_access_key_id: str | None = None,
            aws_secret_access_key: str | None = None
    ):
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as e:
            raise ImportError(
                "boto3 is required for S3Adapter. Install it with: pip install tractusx_sdk[s3]"
            ) from e

        if not isinstance(bucket_name, str) or not bucket_name.strip():
            raise ValueError("bucket_name must be a non-empty string")

        if not isinstance(key_pattern, str) or not key_pattern.strip():
            raise ValueError("key_pattern must be a non-empty string")

        # Validate credentials are provided together
        has_access_key = bool(aws_access_key_id is not None and str(aws_access_key_id).strip())
        has_secret_key = bool(aws_secret_access_key is not None and str(aws_secret_access_key).strip())

        if has_access_key != has_secret_key:
            raise ValueError(
                "Both aws_access_key_id and aws_secret_access_key must be provided together, "
                "or neither (to use environment variables, IAM roles, or AWS config files)"
            )

        self.bucket_name = bucket_name
        self.key_pattern = key_pattern
        self.client_error = ClientError

        # Build client kwargs, only including credentials if both are provided
        client_kwargs = {
            "region_name": region_name,
        }
        
        if endpoint_url is not None:
            client_kwargs["endpoint_url"] = endpoint_url

        if has_access_key and has_secret_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.client = boto3.client("s3", **client_kwargs)

    def _extract_key(self, submodel_metadata: Mapping[str, Any]) -> str:
        """
        Resolve the S3 object key from submodel metadata using ``key_pattern``.
        """
        if not isinstance(submodel_metadata, Mapping):
            raise TypeError("submodel_metadata must be a mapping")

        try:
            key = self.key_pattern.format(**submodel_metadata)
        except KeyError as key_error:
            raise KeyError(
                f"Missing required key '{key_error.args[0]}' for pattern '{self.key_pattern}'"
            ) from key_error

        if not isinstance(key, str) or not key.strip():
            raise ValueError("Resolved key value must be a non-empty string")

        return key

    def read(self, submodel_metadata: Mapping[str, Any]) -> Any:
        """
        Retrieve a submodel JSON object from S3.
        """
        key = self._extract_key(submodel_metadata)
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(response["Body"].read())
        except self.client_error as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise FileNotFoundError(
                    f"Submodel not found in S3: bucket={self.bucket_name}, key={key}"
                ) from e
            raise

    def write(self, submodel_metadata: Mapping[str, Any], content: bytes) -> None:
        """
        Write raw bytes to an S3 object.
        """
        if not isinstance(content, bytes):
            raise TypeError("Content must be bytes!")

        key = self._extract_key(submodel_metadata)
        try:
            self.client.put_object(Bucket=self.bucket_name, Key=key, Body=content)
        except self.client_error as e:
            raise RuntimeError(
                f"Failed to write to S3: bucket={self.bucket_name}, key={key}"
            ) from e

    def write_json(self, submodel_metadata: Mapping[str, Any], content: Mapping[str, Any] | None) -> None:
        """
        Serialize JSON content and write it to S3 with ``ContentType=application/json``.
        """
        if content is not None and not isinstance(content, Mapping):
            raise TypeError("content must be a mapping or None")

        key = self._extract_key(submodel_metadata)
        body = json.dumps(content).encode("utf-8")
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType="application/json",
            )
        except self.client_error as e:
            raise RuntimeError(
                f"Failed to write JSON to S3: bucket={self.bucket_name}, key={key}"
            ) from e

    def delete(self, submodel_metadata: Mapping[str, Any]) -> None:
        """
        Delete an S3 object.
        """
        key = self._extract_key(submodel_metadata)
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except self.client_error as e:
            raise RuntimeError(
                f"Failed to delete S3 object: bucket={self.bucket_name}, key={key}"
            ) from e

    def exists(self, submodel_metadata: Mapping[str, Any]) -> bool:
        """
        Check if an S3 object exists.
        """
        key = self._extract_key(submodel_metadata)
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except self.client_error as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    def list_contents(self, prefix: str | None = None) -> list[str]:
        """
        List S3 objects with an optional prefix.
        """
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix or "")
            keys = []
            for page in page_iterator:
                contents = page.get("Contents", [])
                keys.extend(obj["Key"] for obj in contents)
            return keys
        except self.client_error as e:
            raise RuntimeError(
                f"Failed to list objects in S3: bucket={self.bucket_name}, prefix={prefix}"
            ) from e
