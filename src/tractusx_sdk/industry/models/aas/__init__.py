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

## Where the models are stored
from .supported_versions import (
    AASSupportedVersionsEnum,
)

from .base_abstract import (
    # Enums
    AssetKind,
    ReferenceTypes,
    ReferenceKeyTypes,
    ProtocolInformationSecurityAttributesTypes,
    # Basic models
    BaseAbstractModel,
    AbstractMultiLanguage,
    AbstractReferenceKey,
    AbstractReference,
    AbstractProtocolInformationSecurityAttributes,
    AbstractProtocolInformation,
    AbstractEmbeddedDataSpecification,
    AbstractAdministrativeInformation,
    AbstractEndpoint,
    AbstractSpecificAssetId,
    # Major models
    AbstractSubModelDescriptor,
    AbstractShellDescriptor,
)

from .base_abstract_dto import (
    # Enums
    MessageTypeEnum,
    ProfileEnum,
    # Basic models
    AbstractMessage,
    # Major models
    # Response models
    AbstractServiceDescription,
    AbstractPagingMetadata,
    AbstractPaginatedResponse,
    AbstractGetAllShellDescriptorsResponse,
    AbstractGetSubmodelDescriptorsByAssResponse,
    AbstractResult,
)
