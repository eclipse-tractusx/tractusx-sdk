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

from typing import Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field


class MultiLanguage(BaseModel):
    """Language-specific text entry."""

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


class ReferenceKey(BaseModel):
    """Reference key"""

    type: ReferenceKeyTypes
    value: str = Field(min_length=1, max_length=2000)


class Reference(BaseModel):
    """External reference structure."""

    type: ReferenceTypes
    keys: List[ReferenceKey] = Field(default_factory=list)


class ProtocolInformationSecurityAttributesTypes(str, Enum):
    """Enum for security attributes types."""

    NONE = "NONE"
    RFC_TLSA = "RFC_TLSA"
    W3C_DID = "W3C_DID"


class ProtocolInformationSecurityAttributes(BaseModel):
    """Protocol information security for endpoints."""

    type: ProtocolInformationSecurityAttributesTypes | None
    key: str | None
    value: str | None


class ProtocolInformation(BaseModel):
    """Protocol information for endpoints."""

    href: str | None = None
    endpoint_protocol: str | None = Field(None, alias="endpointProtocol")
    endpoint_protocol_version: List[str] | None = Field(
        None, alias="endpointProtocolVersion"
    )
    subprotocol: str | None = None
    subprotocol_body: str | None = Field(None, alias="subprotocolBody")
    subprotocol_body_encoding: str | None = Field(None, alias="subprotocolBodyEncoding")
    security_attributes: List[ProtocolInformationSecurityAttributes] = Field(
        default_factory=list, alias="securityAttributes"
    )


class EmbeddedDataSpecification(BaseModel):
    data_specification: Reference | None = Field(None, alias="dataSpecification")
    dataSpecificationContent: Dict[str, Any] | None = Field(
        None, alias="dataSpecificationContent"
    )


class AdministrativeInformation(BaseModel):
    embedded_data_specifications: EmbeddedDataSpecification | None = Field(
        alias="embeddedDataSpecifications"
    )
    version: str | None = Field(None, min_length=1, max_length=4)
    revision: str | None = Field(None, min_length=1, max_length=4)
    creator: Reference | None
    template_id: str | None = Field(
        None, min_length=1, max_length=2000, alias="templateId"
    )


class Endpoint(BaseModel):
    """Class for endpoint information."""

    interface: str
    protocol_information: ProtocolInformation = Field(alias="protocolInformation")


class SubModelDescriptor(BaseModel):
    """Submodel descriptor for AAS."""

    description: List[MultiLanguage] | None = Field(None)
    display_name: List[MultiLanguage] | None = Field(None)
    administration: AdministrativeInformation | None = None
    endpoints: List[Endpoint] | None = Field(None)
    id_short: str | None = Field(None, max_length=128)
    id: str | None = Field(None, min_length=1, max_length=2000)
    semantic_id: Reference | None = None
    supplemental_semantic_ids: List[Reference] | None = Field(
        None, alias="supplementalSemanticIds"
    )

    def to_json_string(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(exclude_none=True, by_alias=True)


class SpecificAssetId(BaseModel):
    """Model for specific asset identifiers."""

    name: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=2000)
    semantic_id: Reference | None = Field(None, alias="semanticId")
    supplemental_semantic_ids: List[Reference] | None = Field(
        None, alias="supplementalSemanticIds"
    )
    external_subject_id: Reference | None = Field(None, alias="externalSubjectId")


class ShellDescriptor(BaseModel):
    """Asset Administration Shell (AAS) Descriptor."""

    description: List[MultiLanguage] | None = Field(None)
    display_name: List[MultiLanguage] | None = Field(None, alias="displayName")
    administration: AdministrativeInformation | None = None
    id_short: str | None = Field(None, alias="idShort", max_length=128)
    asset_kind: AssetKind | None = Field(None, alias="assetKind")
    asset_type: str | None = Field(None, alias="assetType")
    endpoints: List[Endpoint] | None = Field(None)
    id: str = Field(min_length=1, max_length=2000
    )
    global_asset_id: str | None = Field(
        None,
        alias="globalAssetId",
        min_length=1,
        max_length=2000,
    )
    specific_asset_ids: List[SpecificAssetId] | None = Field(alias="specificAssetIds")
    submodel_descriptors: List[SubModelDescriptor] | None = Field(
        None, alias="submodelDescriptors"
    )

    def add_description(self, text: str, language: str = "en") -> None:
        """Add a description in the specified language."""
        if self.description is None:
            self.description = []
        self.description.append(MultiLanguage(language=language, text=text))

    def add_display_name(self, text: str, language: str = "en") -> None:
        """Add a display name in the specified language."""
        if self.display_name is None:
            self.display_name = []
        self.display_name.append(MultiLanguage(language=language, text=text))

    def add_specific_asset_id(self, asset_id: SpecificAssetId) -> None:
        """Add a specific asset ID."""
        if self.specific_asset_ids is None:
            self.specific_asset_ids = []
        self.specific_asset_ids.append(asset_id)

    def add_submodel(self, submodel: SubModelDescriptor) -> None:
        """Add a submodel descriptor."""
        if self.submodel_descriptors is None:
            self.submodel_descriptors = []
        self.submodel_descriptors.append(submodel)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary representation."""
        return self.model_dump(exclude_none=True, by_alias=True)

    def to_json_string(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(exclude_none=True, by_alias=True)


class PagingMetadata(BaseModel):
    """Paging metadata for the response."""

    cursor: str | None = Field(None)


class BasePaginatedResponse(BaseModel):
    """Base class for paginated responses."""

    paging_metadata: PagingMetadata | None = Field(None)


class GetAllShellDescriptorsResponse(BasePaginatedResponse):
    """Response model for the get_all_shell_descriptors method."""

    result: List[ShellDescriptor]


class GetSubmodelDescriptorsByAssResponse(BasePaginatedResponse):
    """Response model for the get_submodel_descriptors method."""

    result: List[SubModelDescriptor]
