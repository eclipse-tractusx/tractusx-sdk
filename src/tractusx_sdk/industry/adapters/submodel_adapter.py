#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
#  Copyright (c) 2026 DRÄXLMAIER Group
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

from abc import ABC, abstractmethod
import json
from typing import Any, Mapping

class SubmodelAdapter(ABC):
    """
    Submodel Adapter class
    """

    @abstractmethod
    def read(self, submodel_metadata: Mapping[str, Any]):
        """
        Return the entire content of a file.

        :param submodel_metadata: Path information as key/value pairs for
            adapter-specific resolution.
        """
        raise NotImplementedError

    @abstractmethod
    def write(self, submodel_metadata: Mapping[str, Any], content: bytes) -> None:
        """
        Write a new file.

        :param submodel_metadata: Path information as key/value pairs for
            adapter-specific resolution.
        """
        raise NotImplementedError

    def write_json(self, submodel_metadata: Mapping[str, Any], content: Mapping[str, Any] | None) -> None:
        """
        Serialize JSON content to bytes and delegate to ``write``.

        :param submodel_metadata: Path information as key/value pairs for
            adapter-specific resolution.
        :param content: JSON object content or ``None``.
        :raises TypeError: If content is neither a mapping nor ``None``.
        """
        if content is not None and not isinstance(content, Mapping):
            raise TypeError("content must be a mapping or None")

        content_bytes = json.dumps(content).encode("utf-8")
        self.write(submodel_metadata, content_bytes)

    

    @abstractmethod
    def delete(self, submodel_metadata: Mapping[str, Any]) -> None:
        """
        Delete a specific file.

        :param submodel_metadata: Path information as key/value pairs for
            adapter-specific resolution.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, submodel_metadata: Mapping[str, Any]) -> bool:
        """
        Check if a file exists.

        :param submodel_metadata: Path information as key/value pairs for
            adapter-specific resolution.
        """
        raise NotImplementedError
