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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

from enum import Enum
from tractusx_sdk.industry.models.aas import (
    AbstractPaginatedResponse,
    AbstractPagingMetadata,
    AbstractGetAllShellDescriptorsResponse,
    AbstractGetSubmodelDescriptorsByAssResponse,
    AbstractMessage,
    AbstractResult,
)
from tractusx_sdk.industry.models.aas.v3 import (
    VersionedModel,
    ShellDescriptor,
    SubModelDescriptor,
)


class MessageTypeEnum(str, Enum):
    """Enum for message types. AAS 3.0 specification."""

    UNDEFINED = "Undefined"
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    EXCEPTION = "Exception"


class PagingMetadata(AbstractPagingMetadata, VersionedModel):
    """Paging metadata for the response following the AAS 3.0 specification."""

    pass


class PaginatedResponse(AbstractPaginatedResponse[PagingMetadata], VersionedModel):
    """Base class for paginated responses following the AAS 3.0 specification."""

    pass


class GetAllShellDescriptorsResponse(
    PaginatedResponse,
    AbstractGetAllShellDescriptorsResponse[PagingMetadata, ShellDescriptor],
    VersionedModel
):
    """Response model for the get_all_shell_descriptors method following the AAS 3.0 specification."""

    pass


class GetSubmodelDescriptorsByAssResponse(
    PaginatedResponse,
    AbstractGetSubmodelDescriptorsByAssResponse[PagingMetadata, SubModelDescriptor],
    VersionedModel
):
    """Response model for the get_submodel_descriptors method following the AAS 3.0 specification."""

    pass


class Message(AbstractMessage, VersionedModel):
    """
    Abstract class for message in a not 2XX response following the AAS 3.0 specification.
    """

    pass


class Result(AbstractResult[Message], VersionedModel):
    """
    Abstract class for result in a not 2XX response following the AAS 3.0 specification.
    """

    pass
