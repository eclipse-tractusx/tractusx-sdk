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

# Part of this content was generated by Co-Pilot and reviewed by a human developer.

from typing import Dict, List, Any, TypeVar, Generic
from enum import Enum
from abc import ABC
from pydantic import BaseModel, Field
from tractusx_sdk.industry.models import (
    AASSupportedVersionsEnum,
)

# Defined Generic types for each Abstract class
# By bounding the Generic types to the specific class
# , we can ensure that it only accepts implementations of the abstract classes
# these implementations are the AAS version specific classes
TMultiLanguage = TypeVar("TMultiLanguage", bound="AbstractMultiLanguage")
TReferenceKey = TypeVar("TReferenceKey", bound="AbstractReferenceKey")
TReference = TypeVar("TReference", bound="AbstractReference")
TProtocolInfoSecAttr = TypeVar(
    "TProtocolInfoSecAttr", bound="AbstractProtocolInformationSecurityAttributes"
)
TProtocolInfo = TypeVar("TProtocolInfo", bound="AbstractProtocolInformation")
TEmbeddedDataSpec = TypeVar(
    "TEmbeddedDataSpec", bound="AbstractEmbeddedDataSpecification"
)
TAdminInfo = TypeVar("TAdminInfo", bound="AbstractAdministrativeInformation")
TEndpoint = TypeVar("TEndpoint", bound="AbstractEndpoint")
TSubModelDesc = TypeVar("TSubModelDesc", bound="AbstractSubModelDescriptor")
TSpecificAssetId = TypeVar("TSpecificAssetId", bound="AbstractSpecificAssetId")
TPagingMetadata = TypeVar("TPagingMetadata", bound="AbstractPagingMetadata")
TShellDescriptor = TypeVar("TShellDescriptor", bound="AbstractShellDescriptor")
TMessage = TypeVar("TMessage", bound="AbstractMessage")


class BaseAbstractModel(BaseModel, ABC):
    """
    Base model for all abstract models, providing methods for conversion to dictionary and JSON string.
    This class should not be used directly. Instead, use a version-specific implementation.
    Extending classes can add additional version-specific configuration.
    """

    _supported_version: AASSupportedVersionsEnum

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary representation."""
        return self.model_dump(exclude_none=True, by_alias=True)

    def to_json_string(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(exclude_none=True, by_alias=True)

    def get_version_info(self) -> str:
        """Get the AAS API supported version"""
        return f"Version {self._supported_version}"


class AbstractMultiLanguage(BaseAbstractModel):
    """
    Abstract class for language-specific text entries.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend the `MultiLanguage` class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    language: str
    text: str


class AssetKind(str, Enum):
    """Enum for Asset kinds"""

    INSTANCE = "Instance"
    NOT_APPLICABLE = "NotApplicable"
    TYPE = "Type"


class ReferenceTypes(str, Enum):
    """Enum for reference types."""

    MODEL_REFERENCE = "ModelReference"
    EXTERNAL_REFERENCE = "ExternalReference"


class ReferenceKeyTypes(str, Enum):
    """Enum for reference key types."""

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
    """Enum for security attributes types."""

    NONE = "NONE"
    RFC_TLSA = "RFC_TLSA"
    W3C_DID = "W3C_DID"

class MessageTypeEnum(str, Enum):
    """Enum for message types."""

    UNDEFINED = "Undefined"
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    EXCEPTION = "Exception"


class AbstractReferenceKey(BaseAbstractModel):
    """
    Abstract class for reference keys.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    type: ReferenceKeyTypes
    value: str = Field(min_length=1, max_length=2000)


class AbstractReference(BaseAbstractModel, Generic[TReferenceKey]):
    """
    Abstract class for external reference structure.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    type: ReferenceTypes
    keys: List[TReferenceKey] | None = None

    def add_key(self, key: TReferenceKey) -> None:
        """Add a reference key."""
        if self.keys is None:
            self.keys = []
        self.keys.append(key)


class AbstractProtocolInformationSecurityAttributes(BaseAbstractModel):
    """
    Abstract class for protocol information security for endpoints.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    type: ProtocolInformationSecurityAttributesTypes | None
    key: str | None
    value: str | None


class AbstractProtocolInformation(BaseAbstractModel, Generic[TProtocolInfoSecAttr]):
    """
    Abstract class for protocol information for endpoints.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    href: str | None = None
    endpoint_protocol: str | None = Field(None, alias="endpointProtocol")
    endpoint_protocol_version: List[str] | None = Field(
        None, alias="endpointProtocolVersion"
    )
    subprotocol: str | None = None
    subprotocol_body: str | None = Field(None, alias="subprotocolBody")
    subprotocol_body_encoding: str | None = Field(None, alias="subprotocolBodyEncoding")
    security_attributes: List[TProtocolInfoSecAttr] | None = Field(
        None, alias="securityAttributes"
    )

    def add_endpoint_protocol_version(self, version: str) -> None:
        """Add an endpoint protocol version."""
        if self.endpoint_protocol_version is None:
            self.endpoint_protocol_version = []
        self.endpoint_protocol_version.append(version)

    def add_security_attribute(self, attribute: TProtocolInfoSecAttr) -> None:
        """Add a security attribute."""
        if self.security_attributes is None:
            self.security_attributes = []
        self.security_attributes.append(attribute)


class AbstractEmbeddedDataSpecification(BaseAbstractModel, Generic[TReference]):
    """
    Abstract class for embedded data specifications.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    data_specification: TReference | None = Field(None, alias="dataSpecification")
    dataSpecificationContent: Dict[str, Any] | None = Field(
        None, alias="dataSpecificationContent"
    )


class AbstractAdministrativeInformation(
    BaseAbstractModel, Generic[TEmbeddedDataSpec, TReference]
):
    """
    Abstract class for administrative information.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    embedded_data_specifications: TEmbeddedDataSpec | None = Field(
        None, alias="embeddedDataSpecifications"
    )
    version: str | None = Field(None, min_length=1, max_length=4)
    revision: str | None = Field(None, min_length=1, max_length=4)
    creator: TReference | None
    template_id: str | None = Field(
        None, min_length=1, max_length=2000, alias="templateId"
    )


class AbstractEndpoint(BaseAbstractModel, Generic[TProtocolInfo]):
    """
    Abstract class for endpoint information.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    interface: str
    protocol_information: TProtocolInfo = Field(alias="protocolInformation")


class AbstractSubModelDescriptor(
    BaseAbstractModel, Generic[TMultiLanguage, TAdminInfo, TEndpoint, TReference]
):
    """
    Abstract class for submodel descriptors in AAS.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    description: List[TMultiLanguage] | None = Field(None)
    display_name: List[TMultiLanguage] | None = Field(None, alias="displayName")
    administration: TAdminInfo | None = None
    endpoints: List[TEndpoint] | None = Field(None)
    id_short: str | None = Field(None, max_length=128, alias="idShort")
    id: str | None = Field(None, min_length=1, max_length=2000)
    semantic_id: TReference | None = Field(None, alias="semanticId")
    supplemental_semantic_ids: List[TReference] | None = Field(
        None, alias="supplementalSemanticIds"
    )

    def add_description(self, description: TMultiLanguage) -> None:
        """Add a description."""
        if self.description is None:
            self.description = []
        self.description.append(description)

    def add_display_name(self, display_name: TMultiLanguage) -> None:
        """Add a display name in the specified language."""
        if self.display_name is None:
            self.display_name = []
        self.display_name.append(display_name)

    def add_endpoint(self, endpoint: TEndpoint) -> None:
        """Add an endpoint."""
        if self.endpoints is None:
            self.endpoints = []
        self.endpoints.append(endpoint)

    def add_supplemental_semantic_id(self, semantic_id: TReference) -> None:
        """Add a supplemental semantic ID."""
        if self.supplemental_semantic_ids is None:
            self.supplemental_semantic_ids = []
        self.supplemental_semantic_ids.append(semantic_id)


class AbstractSpecificAssetId(BaseAbstractModel, Generic[TReference]):
    """
    Abstract class for specific asset identifiers.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    name: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=2000)
    semantic_id: TReference | None = Field(None, alias="semanticId")
    supplemental_semantic_ids: List[TReference] | None = Field(
        None, alias="supplementalSemanticIds"
    )
    external_subject_id: TReference | None = Field(None, alias="externalSubjectId")

    def add_supplemental_semantic_id(self, semantic_id: TReference) -> None:
        """Add a supplemental semantic ID."""
        if self.supplemental_semantic_ids is None:
            self.supplemental_semantic_ids = []
        self.supplemental_semantic_ids.append(semantic_id)


class AbstractShellDescriptor(
    BaseAbstractModel,
    Generic[TMultiLanguage, TAdminInfo, TEndpoint, TSpecificAssetId, TSubModelDesc],
):
    """
    Abstract class for Asset Administration Shell (AAS) Descriptor.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    description: List[TMultiLanguage] | None = Field(None)
    display_name: List[TMultiLanguage] | None = Field(None, alias="displayName")
    administration: TAdminInfo | None = None
    id_short: str | None = Field(None, alias="idShort", max_length=128)
    asset_kind: AssetKind | None = Field(None, alias="assetKind")
    asset_type: str | None = Field(None, alias="assetType")
    endpoints: List[TEndpoint] | None = Field(None)
    id: str = Field(min_length=1, max_length=2000)
    global_asset_id: str | None = Field(
        None,
        alias="globalAssetId",
        min_length=1,
        max_length=2000,
    )
    specific_asset_ids: List[TSpecificAssetId] | None = Field(
        None, alias="specificAssetIds"
    )
    submodel_descriptors: List[TSubModelDesc] | None = Field(
        None, alias="submodelDescriptors"
    )

    def add_description(self, description: TMultiLanguage) -> None:
        """Add a description."""
        if self.description is None:
            self.description = []
        self.description.append(description)

    def add_display_name(self, display_name: TMultiLanguage) -> None:
        """Add a display name in the specified language."""
        if self.display_name is None:
            self.display_name = []
        self.display_name.append(display_name)

    def add_specific_asset_id(self, asset_id: TSpecificAssetId) -> None:
        """Add a specific asset ID."""
        if self.specific_asset_ids is None:
            self.specific_asset_ids = []
        self.specific_asset_ids.append(asset_id)

    def add_submodel(self, submodel: TSubModelDesc) -> None:
        """Add a submodel descriptor."""
        if self.submodel_descriptors is None:
            self.submodel_descriptors = []
        self.submodel_descriptors.append(submodel)


class AbstractPagingMetadata(BaseAbstractModel):
    """
    Abstract class for paging metadata for responses.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    cursor: str | None = Field(None)


class AbstractPaginatedResponse(BaseAbstractModel, Generic[TPagingMetadata]):
    """
    Abstract base class for paginated responses.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    paging_metadata: TPagingMetadata | None = Field(None)


class AbstractGetAllShellDescriptorsResponse(
    AbstractPaginatedResponse[TPagingMetadata],
    Generic[TPagingMetadata, TShellDescriptor],
):
    """
    Abstract response model for the get_all_shell_descriptors method.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    result: List[TShellDescriptor]


class AbstractGetSubmodelDescriptorsByAssResponse(
    AbstractPaginatedResponse[TPagingMetadata], Generic[TPagingMetadata, TSubModelDesc]
):
    """
    Abstract response model for the get_submodel_descriptors method.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    result: List[TSubModelDesc]

class AbstractMessage(BaseAbstractModel):
    """
    Abstract class for message in a not 2XX response.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    code: str | None = Field(None)
    correlationId: str | None = Field(None)
    messageType: MessageTypeEnum | None = Field(None)
    text: str | None = Field(None)
    timestamp: str | None = Field(None)

class AbstractResult(BaseAbstractModel, Generic[TMessage]):
    """
    Abstract class for result in a not 2XX response.
    This class should not be used directly. Instead, use a version-specific implementation.
    Supported versions extend this class with modifications specific to that API version.
    Extending classes can add additional version-specific configuration.
    """

    messages: List[TMessage] | None = Field(None)