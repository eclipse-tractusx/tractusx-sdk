<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 LKS Next
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->

# 6. Runtime View

## Scenario 1: Catalog Discovery

An application queries an EDC connector to discover available offers by `dct:type`.

```mermaid
sequenceDiagram
    participant App as Application
    participant SF as ServiceFactory
    participant SVC as ConnectorConsumerService
    participant CTR as ConnectorController
    participant ADP as ConnectorAdapter
    participant EDC as EDC Connector

    App->>SF: get_connector_consumer_service(dataspace_version, base_url, headers)
    SF-->>App: connector_service

    App->>SVC: get_catalog_by_dct_type(provider_url, dct_type)
    SVC->>CTR: build_catalog_request(provider_url, dct_type)
    CTR->>ADP: POST /management/v3/catalog/request
    ADP->>EDC: HTTP POST (DSP catalog request)
    EDC-->>ADP: catalog response (JSON-LD)
    ADP-->>CTR: parsed response
    CTR-->>SVC: catalog offers
    SVC-->>App: list[CatalogOffer]
```

## Scenario 2: Contract Negotiation and EDR Retrieval

An application negotiates a contract and retrieves the EDR (Endpoint Data Reference) to access the actual data.

```mermaid
sequenceDiagram
    participant App as Application
    participant SVC as ConnectorConsumerService
    participant CM as ConnectionManager
    participant EDC as EDC Connector

    App->>SVC: do_get_by_dct_type(provider_url, dct_type, bpnl)
    SVC->>EDC: POST /management/v3/catalog/request
    EDC-->>SVC: catalog with matching offer

    SVC->>EDC: POST /management/v3/contractnegotiations
    EDC-->>SVC: negotiation id

    loop Poll until FINALIZED
        SVC->>EDC: GET /management/v3/contractnegotiations/{id}
        EDC-->>SVC: negotiation state
    end

    SVC->>EDC: POST /management/v3/transferprocesses
    EDC-->>SVC: transfer id

    loop Poll until STARTED
        SVC->>EDC: GET /management/v3/transferprocesses/{id}
        EDC-->>SVC: transfer state
    end

    SVC->>CM: store EDR in memory cache (keyed by BPN + dct_type)
    SVC-->>App: EDR (endpoint + token)

    App->>EDC: GET {EDR.endpoint} (Authorization: {EDR.token})
    EDC-->>App: actual data payload
```

## Scenario 3: Digital Twin Registration

An application registers a new shell descriptor and submodel descriptor in the DTR.

```mermaid
sequenceDiagram
    participant App as Application
    participant AAS as AasService
    participant DTR as Digital Twin Registry

    App->>AAS: create_shell_descriptor(shell)
    AAS->>DTR: POST /registry/shell-descriptors
    DTR-->>AAS: created shell (with id)
    AAS-->>App: ShellDescriptor

    App->>AAS: add_submodel_descriptor(shell_id, submodel)
    AAS->>DTR: POST /registry/shell-descriptors/{id}/submodel-descriptors
    DTR-->>AAS: created submodel descriptor
    AAS-->>App: SubmodelDescriptor
```

## Scenario 4: EDR Cache Eviction (Per Party)

When a Business Partner connection needs to be reset (e.g., token expiry or configuration change), the in-memory cache for that party is cleared.

```mermaid
sequenceDiagram
    participant App as Application
    participant SVC as ConnectorConsumerService
    participant CM as ConnectionManager

    App->>SVC: clear_connections_by_party(bpnl)
    SVC->>CM: remove all cached EDRs for bpnl
    CM-->>SVC: cleared
    SVC-->>App: (next call will re-negotiate)
```

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2026 LKS Next
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
