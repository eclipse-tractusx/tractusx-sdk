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
from pydantic import Field
from tractusx_sdk.industry.models import (
    BaseAbstractModel,
    AbstractMultiLanguage,
    AbstractPaginatedResponse,
    AbstractProtocolInformationSecurityAttributes,
    AbstractProtocolInformation,
    AbstractEmbeddedDataSpecification,
    AbstractAdministrativeInformation,
    AbstractEndpoint,
    AbstractReference,
    AbstractReferenceKey,
    AbstractSubModelDescriptor,
    AbstractSpecificAssetId,
    AbstractShellDescriptor,
    AbstractPagingMetadata,
    AbstractGetAllShellDescriptorsResponse,
    AbstractGetSubmodelDescriptorsByAssResponse,
    AbstractMessage,
    AbstractResult,
)
from tractusx_sdk.industry.models import (
    AASSupportedVersionsEnum,
)


class VersionedModel(BaseAbstractModel):
    """Base class that provides version 3.0 information to all models."""

    _supported_version: AASSupportedVersionsEnum = AASSupportedVersionsEnum.VERSION_3_0


class MultiLanguage(AbstractMultiLanguage, VersionedModel):
    """Language-specific text entry. AAS 3.0 specification."""

    pass


class AssetKind(str, Enum):
    """Enum for Asset kinds. AAS 3.0 specification."""

    INSTANCE = "Instance"
    NOT_APPLICABLE = "NotApplicable"
    TYPE = "Type"


class ReferenceTypes(str, Enum):
    """Enum for reference types. AAS 3.0 specification."""

    MODEL_REFERENCE = "ModelReference"
    EXTERNAL_REFERENCE = "ExternalReference"


class ReferenceKeyTypes(str, Enum):
    """Enum for reference key types. AAS 3.0 specification."""

    ANNOTATED_RELATIONSHIP_ELEMENT = "AnnotatedRelationshipElement"
    ASSET_ADMINISTRATION_SHELL = "AssetAdministrationShell"
    BASIC_EVENT_ELEMENT = "BasicEventElement"
    BLOB = "Blob"
    CAPABILITY = "Capability"
    CONCEPT_DESCRIPTION = "ConceptDescription"
    DATA_ELEMENT = "DataElement"
    ENTITY = "Entity"
    EVENT_ELEMENT = "EventElement"
    FILE = "File"
    FRAGMENT_REFERENCE = "FragmentReference"
    GLOBAL_REFERENCE = "GlobalReference"
    IDENTIFIABLE = "Identifiable"
    MULTI_LANGUAGE_PROPERTY = "MultiLanguageProperty"
    OPERATION = "Operation"
    PROPERTY = "Property"
    RANGE = "Range"
    REFERABLE = "Referable"
    REFERENCE_ELEMENT = "ReferenceElement"
    RELATIONSHIP_ELEMENT = "RelationshipElement"
    SUBMODEL = "Submodel"
    SUBMODEL_ELEMENT = "SubmodelElement"
    SUBMODEL_ELEMENT_COLLECTION = "SubmodelElementCollection"
    SUBMODEL_ELEMENT_LIST = "SubmodelElementList"


class ProtocolInformationSecurityAttributesTypes(str, Enum):
    """Enum for security attributes types. AAS 3.0 specification."""

    NONE = "NONE"
    RFC_TLSA = "RFC_TLSA"
    W3C_DID = "W3C_DID"


class MessageTypeEnum(str, Enum):
    """Enum for message types. AAS 3.0 specification."""

    UNDEFINED = "Undefined"
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    EXCEPTION = "Exception"


class ReferenceKey(AbstractReferenceKey, VersionedModel):
    """Reference key following the AAS 3.0 specification."""

    type: ReferenceKeyTypes


class Reference(AbstractReference[ReferenceKey], VersionedModel):
    """External reference structure following the AAS 3.0 specification."""

    type: ReferenceTypes


class ProtocolInformationSecurityAttributes(
    AbstractProtocolInformationSecurityAttributes, VersionedModel
):
    """Protocol information security for endpoints following the AAS 3.0 specification."""

    type: ProtocolInformationSecurityAttributesTypes | None


class ProtocolInformation(
    AbstractProtocolInformation[ProtocolInformationSecurityAttributes],
    VersionedModel,
):
    """Protocol information for endpoints following the AAS 3.0 specification."""

    pass


class EmbeddedDataSpecification(
    AbstractEmbeddedDataSpecification[Reference], VersionedModel
):
    """Embedded data specification following the AAS 3.0 specification."""

    pass


class AdministrativeInformation(
    AbstractAdministrativeInformation[EmbeddedDataSpecification, Reference],
    VersionedModel,
):
    """Administrative information following the AAS 3.0 specification."""

    pass


class Endpoint(AbstractEndpoint[ProtocolInformation], VersionedModel):
    """Class for endpoint information following the AAS 3.0 specification."""

    pass


class SubModelDescriptor(
    AbstractSubModelDescriptor[
        MultiLanguage, AdministrativeInformation, Endpoint, Reference
    ],
    VersionedModel,
):
    """Submodel descriptor following the AAS 3.0 specification."""

    pass


class SpecificAssetId(AbstractSpecificAssetId[Reference], VersionedModel):
    """Model for specific asset identifiers following the AAS 3.0 specification."""

    pass


class ShellDescriptor(
    AbstractShellDescriptor[
        MultiLanguage,
        AdministrativeInformation,
        Endpoint,
        SpecificAssetId,
        SubModelDescriptor,
    ],
    VersionedModel,
):
    """Asset Administration Shell (AAS) Descriptor following the AAS 3.0 specification."""

    asset_kind: AssetKind | None = Field(None, alias="assetKind")


class PagingMetadata(AbstractPagingMetadata, VersionedModel):
    """Paging metadata for the response following the AAS 3.0 specification."""

    pass


class PaginatedResponse(AbstractPaginatedResponse[PagingMetadata], VersionedModel):
    """Base class for paginated responses following the AAS 3.0 specification."""

    pass


class GetAllShellDescriptorsResponse(
    PaginatedResponse,
    AbstractGetAllShellDescriptorsResponse[PagingMetadata, ShellDescriptor],
):
    """Response model for the get_all_shell_descriptors method following the AAS 3.0 specification."""

    pass


class GetSubmodelDescriptorsByAssResponse(
    PaginatedResponse,
    AbstractGetSubmodelDescriptorsByAssResponse[PagingMetadata, SubModelDescriptor],
):
    """Response model for the get_submodel_descriptors method following the AAS 3.0 specification."""

    pass


class Message(AbstractMessage):
    """
    Abstract class for message in a not 2XX response following the AAS 3.0 specification.
    """

    pass


class Result(AbstractResult[Message]):
    """
    Abstract class for result in a not 2XX response following the AAS 3.0 specification.
    """

    pass
