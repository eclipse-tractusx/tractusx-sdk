[![Contributors][contributors-shield]][contributors-url]
[![Stargazers][stars-shield]][stars-url]
[![Apache 2.0 License][license-shield]][license-url-code]
[![CC-BY-4.0][license-shield-non-code]][license-url-non-code]
[![Latest Release][release-shield]][release-url]

# Tractus-X Software Development KIT (SDK)

Eclipse Tractus-X Software Development KIT - The Dataspace &amp; Industry Foundation Libraries

A modular library/toolbox/framework, that helps you to build applications/scripts/microservices which can use the Connector, DTR, Discovery Services for providing and consuming data (any data).

It aims to provide a reference implementation for the various interactions between applications and services like the EDC, Digital Twin Registry and Submodel Service.
This "tool box" helps you to provide data and consume data on a Dataspace Context, how you orchestrate it is then up to you and your use case.

Additionally to this various microservices are provided at the [eclipse-tractusx/tractusx-sdk-services](https://github.com/eclipse-tractusx/tractusx-sdk-services) repository, giving an lighthouse implementation on how to use the SDK for various purposes. Other examples of solutions which are built with this SDK is the [Industry Core Hub](https://github.com/eclipse-tractusx/industry-core-hub).

This SDK will manage automatically the version updates from the EDC and the Digital Twin Registry, that will be maintained by the community.

No specific use case logic will be configured here, only the bare minimum for interacting in a Dataspace and developing your own applications with this stack, based on the KITs which adopt the core data exchange functionalities, in concrete the following ones:

- [Connector KIT](https://eclipse-tractusx.github.io/docs-kits/kits/connector-kit/adoption-view)
- [Digital Twin KIT](https://eclipse-tractusx.github.io/docs-kits/kits/digital-twin-kit/adoption-view)
- [Industry Core KIT](https://eclipse-tractusx.github.io/docs-kits/kits/industry-core-kit/adoption-view)

## Installation

Install the package directly from PyPI:

```bash
pip install tractusx-sdk
```

## Documentation

Our latest documentation can be found here:

[https://eclipse-tractusx.github.io/tractusx-sdk/main/](https://eclipse-tractusx.github.io/tractusx-sdk/main/)

## Usage

You can find some examples in the [dedicated section](./examples/).

> [!NOTE]
> We are working to make the SDK documentation more accessible and easy to adopt.
> Our objective is to have an "Open Specification" at our github pages domain.
> Support us by joining our [open meetings](https://eclipse-tractusx.github.io/community/open-meetings#Industry%20Core%20Hub%20&%20Tractus-X%20SDK%20Weekly) or contributing with documentation.

We have an advanced usage guide in [docs/user](https://github.com/eclipse-tractusx/tractusx-sdk/tree/docs/sdk-usage/docs/user).

Here we also have a quick guide:

**📖 Quick Guide:**

- [**Consumption**](#consumption) - Consuming data from the dataspace
  - [Call endpoints with one click](#call-endpoints-with-one-click) - Quick data access
  - [Get access to endpoints behind connectors & reuse connections](#get-access-to-the-endpoints-behind-the-connector--reuse-connections) - Easy connection management
  - [Want more?](#want-more) - Advanced catalog operations
  - [Advanced Usage](#advanced-usage) - Low-level contract negotiations
  - [**Discovery**](#discovery) - Finding connectors and services
- [**Provision**](#provision) - Setting up data provision and asset creation
  - [Digital Twin Registry](#digital-twin-registry) - Working with AAS shell descriptors
- [**All in one**](#all-in-one) - Combined provider and consumer usage

### Consumption

```py
from tractusx_sdk.dataspace.managers.connection import PostgresMemoryRefreshConnectionManager, FileSystemConnectionManager, MemoryConnectionManager
from tractusx_sdk.dataspace.services.connector import ServiceFactory
from tractusx_sdk.dataspace.services import BaseConnectorService

#####################################################

# Select a connection manager

# Postgres Synced Option with Memory
from sqlmodel import create_engine

engine = create_engine(str("postgresql://user:password@localhost:5432/db"))
connection_manager = PostgresMemoryRefreshConnectionManager(
    engine=engine, logger=logger, verbose=True)

# Another Postgres-Only option is available but is not recommended

# FileSystem
connection_manager = FileSystemConnectionManager(
    path="./data/my-connections.json", logger=logger, verbose=True)

# Memory Only
connection_manager = MemoryConnectionManager(logger=logger, verbose=True)

#####################################################

consumer_connector_headers: dict = {
    "X-Api-Key": "my-api-key",
    "Content-Type": "application/json"
}

consumer_connector_service: BaseConnectorService = ServiceFactory.get_connector_consumer_service(
    dataspace_version="jupiter",  # "saturn" is also
    base_url="https://my-connector-controlplane.url",
    dma_path="/management",
    headers=consumer_connector_headers,
    connection_manager=connection_manager,  # Select one from above
    logger=logger,  # You can remove this to keep logs disabled
    verbose=True  # You can remove this to keep logs disabled
)
```

#### Call endpoints with one click

```py
policies_to_accept: list = [{"odrl:permission": {"odrl:action": {"@id": "odrl:use"}, "odrl:constraint": {"odrl:and": [{"odrl:leftOperand": {"@id": "cx-policy:FrameworkAgreement"}, "odrl:operator": {"@id": "odrl:eq"}, "odrl:rightOperand": "DataExchangeGovernance:1.0"}, {"odrl:leftOperand": {
    "@id": "cx-policy:Membership"}, "odrl:operator": {"@id": "odrl:eq"}, "odrl:rightOperand": "active"}, {"odrl:leftOperand": {"@id": "cx-policy:UsagePurpose"}, "odrl:operator": {"@id": "odrl:eq"}, "odrl:rightOperand": "cx.core.digitalTwinRegistry:1"}]}}, "odrl:prohibition": [], "odrl:obligation": []}]

digital_twins = consumer_connector_service.do_get(
    counter_party_id="BPNL00000003AYRE",
    counter_party_address="https://connector-edc-controlplane.tractusx.io/api/v1/dsp",
    filter_expression=consumer_connector_service.get_filter_expression(
        key="'http://purl.org/dc/terms/type'.'@id'",
        operator="=",
        value="https://w3id.org/catenax/taxonomy#DigitalTwinRegistry"
    ),
    path="/shell-descriptors",
    params={"limit": 5},
    policies=policies_to_accept
)

# Here are the digital twins
print(digital_twins.json())
```

#### Get access to the endpoints behind the connector & reuse connections

You can do more! Explore other methods from the service.

```py
# Don't want to make the one click approach? Feel free to implement your own logic

dataplane_url, access_token = consumer_connector_service.do_dsp(
    counter_party_id="BPNL00000003AYRE",
    counter_party_address="https://connector-edc-controlplane.tractusx.io/api/v1/dsp",
    filter_expression=consumer_connector_service.get_filter_expression(
        key="'http://purl.org/dc/terms/type'.'@id'",
        operator="=",
        value="https://w3id.org/catenax/taxonomy#DigitalTwinRegistry"
    ),
    policies=policies_to_accept
)

# Using the dataplane proxy and the access token, you can call how much times you like different APIs behind the proxy, reusing the open connection!
```

#### Want more?

```py
# Get Catalog by yourself

catalog = consumer_connector_service.get_catalog_by_dct_type(
    dct_type="https://w3id.org/catenax/taxonomy#DigitalTwinRegistry",
    counter_party_id="BPNL00000003AYRE",
    counter_party_address="https://edc1-controlplane/api/v1/dsp",
    timeout=15
)

# One is not enough? Call in parallel!
catalogs = consumer_connector_service.get_catalogs_by_dct_type(
    dct_type="https://w3id.org/catenax/taxonomy#DigitalTwinRegistry",
    counter_party_id="BPNL00000003AYRE",
    edcs=[
        "https://edc1-controlplane/api/v1/dsp",
        "https://edc2-controlplane/api/v1/dsp",
        "https://edc3-controlplane/api/v1/dsp"
    ],
    timeout=15
)
```

#### Advanced Usage

```py
# You can even implement it in the granularity you want!
from tractusx_sdk.dataspace.models.connector.base_contract_negotiation_model import BaseContractNegotiationModel
from tractusx_sdk.dataspace.models.connector.model_factory import ModelFactory

request: BaseContractNegotiationModel = ModelFactory. get_contract_negotiation_model(
    dataspace_version="jupiter",
    context=[
        "https://w3id.org/tractusx/policy/v1.0.0",
        "http://www.w3.org/ns/odrl.jsonld",
        {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        }
    ],
    counter_party_address="https://edc1-controlplane/api/v1/dsp",
    offer_id="offer-id",
    asset_id="asset-id",
    provider_id="BPNL00000003AYRE",
    # Add here the policy you want to accept
    offer_policy=policies_to_accept[0]
)

# Build catalog api url
response: Response = self.edrs.create(request)
# In case the response code is not successful or the response is null
if (response is None or response.status_code != 200):
    return None

negotiation_id = response.json().get("@id", None)

response: Response = self.edrs.get_data_address(
    oid=negotiation_id, params={"auto_refresh": True})
```

### Discovery

```py
from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import ConnectorDiscoveryService, DiscoveryFinderService

discovery_oauth = OAuth2Manager(
    auth_url="https://central-idp/auth/",
    realm="CX-Central",
    clientid="456as2id",
    clientsecret="asbadjsk2as4sad574s",
)

discovery_finder_service = DiscoveryFinderService(
    url="https://discovery-finder.url/api/v1.0/administration/connectors/discovery/search",
    oauth=discovery_oauth
)

# Create the connector discovery service for the consumer
connector_discovery_service = ConnectorDiscoveryService(
    oauth=discovery_oauth,
    discovery_finder_service=discovery_finder_service
)

connector_discovery_service.find_connector_by_bpn("BPNL00000000TS1D")
```

### Provision

```py
from tractusx_sdk.dataspace.services.connector import ServiceFactory, BaseConnectorService

provider_connector_headers: dict = {
    "X-Api-Key": "my-api-key",
    "Content-Type": "application/json"
}

# Create the connector provider service
provider_connector_service: BaseConnectorService = ServiceFactory.get_connector_provider_service(
    dataspace_version="jupiter",  # "saturn" is also available
    base_url="https://my-connector-controlplane.url",
    dma_path="/management",
    headers=provider_connector_headers,
    logger=logger,  # You can remove this to keep logs disabled
    verbose=True  # You can remove this to keep logs disabled
)
provider_connector_service.create_asset(
    asset_id="my-asset-id",
    base_url="https://submodel-service.url/",
    dct_type="cx-taxo:SubmodelBundle",
    version="3.0",
    semantic_id="urn:samm:io.catenax.part_type_information:1.0.0#PartTypeInformation",
    headers={
        "X-Api-Key": "my-secret-to-the-submodel-service"
    }
)
provider_connector_service.create_asset(
    asset_id="digital-twin-registry",
    base_url="https://digital-twin-registry.tractusx.io/api/v3",
    dct_type="https://w3id.org/catenax/taxonomy#DigitalTwinRegistry",
    version="3.0",
    proxy_params={
        "proxyQueryParams": "true",
        "proxyPath": "true",
        "proxyMethod": "true",
        "proxyBody": "true"
    }
)

# And you can do much more! Create Policies, Contracts, etc
```

#### Digital Twin Registry

```py
from tractusx_sdk.industry.models.aas.v3 import (
    ShellDescriptor, MultiLanguage, SpecificAssetId, AssetKind, ReferenceTypes, Reference, ReferenceKey, ReferenceKeyTypes
)
from tractusx_sdk.industry.services import AasService
aas_service = AasService(
    base_url="https://digital-twin-registry.tractusx.io",
    # Here you can add another one if you want.
    base_lookup_url="https://aas-discovery.tractusx.io",
    api_path="/api/v3",
)

# Get shells or one shell
existing_shell: ShellDescriptor = aas_service.get_asset_administration_shell_descriptor_by_id(
    aas_identifier="urn:uuid:ad7bc88c-fa31-40d8-8f17-2ceaf1295ff6"
)

########
# Create Shells

# Create display name with multiple languages
display_name_en = MultiLanguage(language="en", text="Vehicle Battery Shell")
display_name_de = MultiLanguage(language="de", text="Fahrzeugbatterie Shell")
display_names = [display_name_en, display_name_de]

# Create description with multiple languages
description_en = MultiLanguage(
    language="en", text="Digital twin shell for electric vehicle battery component")
description_de = MultiLanguage(
    language="de", text="Digitaler Zwilling für Elektrofahrzeug-Batteriekomponente")
descriptions = [description_en, description_de]

bpns_list = ["BPNL00000003AYRE", "BPNL000000000TEA4"]
manufacturer_id = "BPNL000000032ASTT"
# Create specific asset identifiers to allow shell descriptors to be seen.
manufacturer_part_id = SpecificAssetId(
    name="manufacturerPartId",
    value="BAT-12345-ABC",
    externalSubjectId=Reference(
        type=ReferenceTypes.EXTERNAL_REFERENCE,
        keys=[ReferenceKey(type=ReferenceKeyTypes.GLOBAL_REFERENCE, value=bpn) for bpn in bpn_keys] or
        [ReferenceKey(type=ReferenceKeyTypes.GLOBAL_REFERENCE,
                      value=manufacturer_id)]
    ),
    supplementalSemanticIds=supplemental_semantic_ids
)(
    name="manufacturerPartId",
    value="BAT-12345-ABC",
    external_subject_id={"type": "GlobalReference",
                         "keys": ["BPNL00000003AYRE"]}
)

vehicle_identification_number = SpecificAssetId(
    name="van",
    value="WVWZZZ1JZ3W386752"
)

specific_asset_ids = [manufacturer_part_id, vehicle_identification_number]

# Create the shell descriptor
shell = ShellDescriptor(
    id="urn:uuid:ad7bc88c-fa31-40d8-8f17-2ceaf1295ff6",
    idShort="VehicleBatteryShell001",
    displayName=display_names,
    description=descriptions,
    assetType="Battery",
    assetKind=AssetKind.INSTANCE,
    globalAssetId="urn:uuid:550e8400-e29b-41d4-a716-446655440000",
    specificAssetIds=specific_asset_ids,
)
res = aas_service.create_asset_administration_shell_descriptor(
    shell_descriptor=shell)

# Congrats! You created a shell according to the AAS 3.0 standards!
```

### All in one

Combine provider and consumer in one module to take the best from your connector!

```py
from tractusx_sdk.dataspace.services.connector import ServiceFactory

connector_service:dict = {
    "X-Api-Key": "my-api-key",
    "Content-Type": "application/json"
}
connector_service = ServiceFactory.get_connector_service(
      dataspace_version="jupiter", ## "saturn" is also available
      base_url="https://my-connector-controlplane.url",
      dma_path="/management",
      headers=connector_connector_headers,
      connection_manager=connection_manager,
      logger=logger, ## You can remove this to keep logs disabled
      verbose=True ## You can remove this to keep logs disabled
)

connector_service.consumer.get_catalog(...)
connector_service.provider.assets.create(...)
```

## Roadmap

The development roadmap is the same as the industry core hub.

```text
February 3 2025     R25.06             R25.09          R25.12
Kickoff              MVP                Stable          NEXT            2026 -> Beyond
| ------------------> | ----------------> | -----------> |  ----------------> |
                Data Provision     Data Consumption    IC-HUB             + KIT Use Cases
                     SDK                 SDK             + Integrate First
                                                           Use Case (e.g. DPP) (Another usage for the SDK)
```

> [!IMPORTANT]
> Currently this SDK is not 100% compatible and tested against the `v0.11.x` connector. The issue is being worked here [tractusx-sdk#159](https://github.com/eclipse-tractusx/tractusx-sdk/issues/159)

## What can you do with this SDK?

- You can create a frontend for your use case (with any technology) and build your own Backend Apis with this tool box.
- Furthermore, you can use this in a Jupyter notebook for example, or create your personal scripts for using the Connector, DTR and Submodel Service.
- It enables you to build your own use case logic over it, without needing to worry about versioning (Jupiter and Saturn supported).
- Base yourself in the [Industry Core Hub](https://github.com/eclipse-tractusx/industry-core-hub) which provides you a "lighthouse" for using this SDK.

## Applications that use this SDK

- [Industry Core Hub](https://github.com/eclipse-tractusx/industry-core-hub): Example on how to use the SDK to develop an application.
  - [Backend](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/ichub-backend): An example of how to use the SDK dataspace & industry libaries in your application.
  - [Frontend](https://github.com/eclipse-tractusx/industry-core-hub/tree/main/ichub-frontend): An example of how to use the SDK API interfaces from each microservice.
  - The use case add-ons from the IC-Hub will also use this!

- [Tractus-X SDK Services](https://github.com/eclipse-tractusx/tractusx-sdk-services): Repository where the reusable APIs/Services for the SDK are available as microservices.
  - [DT Pull Service](https://github.com/eclipse-tractusx/tractusx-sdk-services): Provides a service that pulls digital twins from data providers.
  - [Test Orchestrator](https://github.com/eclipse-tractusx/tractusx-sdk-services): Provides a test agent service that can check if the configuration of your data provision services is compliant with the standard schemas & syntaxis.

- [Tractus-X AAS Suite](https://github.com/eclipse-tractusx/aas-suite): A integration project between the Tractus-X SDK (being used as client for the Connector) and the BaSyx Python SDK.

- Open for more collaboration!

## Module Logic Architecture

To ease the understanding what is the tool box (SDK) here is a resumed diagram:

![Logic Architecture](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/docs/media/logic-resume.svg)

## Why was this Tractus-X SDK Created?

Here you will find a design decision which was taken at the beginning of the industry core hub development:

[Industry Core Hub Decision Record 0002](https://github.com/eclipse-tractusx/industry-core-hub/blob/main/docs/architecture/decision-records/0002-tractus-x-sdk.md)

While developing the Industry Core Hub, in parallel we decided to create a SDK for Tractus-X.

[Industry Core Hub Decision Record 0003 Create new Repository](https://github.com/eclipse-tractusx/industry-core-hub/blob/main/docs/architecture/decision-records/0003-tractus-x-sdk-individual-repository.md)

Having an individual SDK repository, we are creating a reusable and modular middleware/library for all use cases and applications that want to easily interact with the Tractus-X Datapaces Components required for data provision and data consumption:

- [Tractus-X Eclipse Dataspace Connector (EDC)](https://github.com/eclipse-tractusx/tractusx-edc)
- [Tractus-X Digital Twin Registry (DTR)](https://github.com/eclipse-tractusx/sldt-digital-twin-registry)
- [Simple Data Backend](https://github.com/eclipse-tractusx/tractus-x-umbrella/tree/main/simple-data-backend)

And other core services like:

**Additional Services**:

- Discovery Services:
  - [Discovery Finder](https://github.com/eclipse-tractusx/sldt-discovery-finder)
  - [BPN Discovery](https://github.com/eclipse-tractusx/sldt-bpn-discovery)
  - [EDC Discovery](https://github.com/eclipse-tractusx/portal-backend)

- [Portal IAM/IDP](https://github.com/eclipse-tractusx/portal-iam)

Our aim is to automate the target releases and compatibility with this systems using DevOps mechanisms.

## High Level Architecture

Providing reusable modules:

- [Dataspace Foundation Library](./src/tractusx_sdk/dataspace)
  - Enables your "bytes" data exchange using the EDC and the core services from Catena-X.
  - It provides tools for your exchange agnostic from your use case.
- [Industry Foundation Library](./src/tractusx_sdk/industry)
  - Enables your data exchange using the dataspace foundation library but for the usage of Digital Twins in the Digital Twin Registry.

- [Extensions](./src/tractusx_sdk/extensions)
  - Allows you to extend the SDK tool box with your use case specifics and reusable components.

![Architecture](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/docs/media/catena-x-speedway-sdk.svg)

## Industry Core Hub Example

![context sdk](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/docs/media/sdk-context.png)

You can use it to build you use case application how you want, based on the industry core foundation or not:

![modular sdk](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/docs/media/modular-microservices-architecture.svg)

## Dataspace Architecture Patterns

This SDK will be developed based and will follow the Dataspace & Industry Usage Patterns recommended in Eclipse Tractus-X [sig-architecture](https://github.com/eclipse-tractusx/sig-architecture).

## How to Get Involved

- **Get onboarded**: [Getting started](https://eclipse-tractusx.github.io/docs/oss/getting-started/). Join the Eclipse Tractus-X open source community as a contributor!
- Attend the [official community office hours](https://eclipse-tractusx.github.io/community/open-meetings/#Community%20Office%20Hour) and raise your issue!
- Attend our [Industry Core Hub Weekly](https://eclipse-tractusx.github.io/community/open-meetings#[IC-Hub]%20Industry%20Core%20Hub%20Weekly)
- Join our [Tractus-X SDK Matrix Chat](https://matrix.to/#/#tractusx-tractusx-sdk:matrix.eclipse.org)

### Found a bug?

👀 If you have identified a bug or want to fix an existing documentation, feel free to create a new issue at our project's corresponding [GitHub Issues page](https://github.com/eclipse-tractusx/tractusx-sdk/issues/new/choose)

 ⁉️ Before doing so, please consider searching for potentially suitable [existing issues](https://github.com/eclipse-tractusx/tractusx-sdk/issues).

🙋 **Assign to yourself** - Show others that you are working on this issue by assigning it to yourself.
<br> To do so, click the cog wheel next to the Assignees section just to the right of this issue.

### Discuss

📣 If you want to share an idea to further enhance the project, please feel free to contribute to the [discussions](https://github.com/eclipse-tractusx/tractusx-sdk/discussions),
otherwise [create a new discussion](https://github.com/eclipse-tractusx/tractusx-sdk/discussions/new/choose)

## Reporting a Security Issue

Please follow the [Security Issue Reporting Guidelines](https://eclipse-tractusx.github.io/docs/release/trg-7/trg-7-01#security-file) if you come across any security vulnerabilities or concerns.

## Licenses

- [Apache-2.0](https://raw.githubusercontent.com/eclipse-tractusx/tractusx-sdk/main/LICENSE) for code
- [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) for non-code

---

Thank you for using Software Development KIT! If you have any questions or need further assistance, please feel free to reach out.

[contributors-shield]: https://img.shields.io/github/contributors/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge
[contributors-url]: https://github.com/eclipse-tractusx/tractusx-sdk/graphs/contributors
[stars-shield]: https://img.shields.io/github/stars/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge
[stars-url]: https://github.com/eclipse-tractusx/tractusx-sdk/stargazers
[license-shield]: https://img.shields.io/github/license/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge
[license-url-code]: https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/LICENSE
[license-shield-non-code]: https://img.shields.io/badge/NON--CODE%20LICENSE-CC--BY--4.0-8A2BE2?style=for-the-badge
[license-url-non-code]: https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/LICENSE_non-code
[release-shield]: https://img.shields.io/github/v/release/eclipse-tractusx/tractusx-sdk.svg?style=for-the-badge

[release-url]: https://github.com/eclipse-tractusx/tractusx-sdk/releases
