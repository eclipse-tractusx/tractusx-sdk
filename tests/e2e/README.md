# End-to-end tests against Tractus-X Umbrella

These tests drive a live Catena-X dataspace (Saturn, DSP 2025-1, DID based) **through the SDK's own methods**. They don't call the APIs by hand. Each run creates its own resources, with a unique run id, and deletes them afterwards.

| Module | What it covers | SDK methods |
|---|---|---|
| `conftest.py` (fixture `offer`) | Provider: two policies, an asset backed by a test payload, and a contract definition. All are cleaned up afterwards. | `ServiceFactory.get_connector_provider_service`, `create_policy`, `create_asset`, `create_contract`, `policies/assets/contract_definitions.delete` |
| `test_connector_e2e.py` | Consumer: catalog, contract negotiation, transfer (HttpData-PULL), EDR, and data pull. Done once step by step and once through `do_get`. The data must equal the payload the provider published. | `ServiceFactory.get_connector_consumer_service`, `get_catalog_by_asset_id`, `ModelFactory.get_contract_negotiation_model`, `contract_negotiations.create/get_state_by_id/get_by_id`, `ModelFactory.get_transfer_process_model`, `transfer_processes.create/get_state_by_id`, `edrs.get_data_address`, `get_filter_expression`, `do_get` |
| `test_dtr_e2e.py` | Digital Twin Registry: create a shell descriptor with one submodel descriptor, read it back three ways, then delete it. The registry only returns a shell to its owner or to a participant named in a specific asset id's `externalSubjectId`, so the shell names the provider's DID there and the reads pass it as `bpn` (the `Edc-Bpn` header). | `AasService.create_asset_administration_shell_descriptor`, `get_asset_administration_shell_descriptor_by_id`, `get_submodel_descriptors_by_aas_id`, `get_all_asset_administration_shell_descriptors`, `delete_asset_administration_shell_descriptor` |

The suite is **skipped unless `TX_SDK_E2E=1`**, so `poetry run pytest` (the unit test workflow) never needs a dataspace.

## In CI

[`.github/workflows/e2e-umbrella.yml`](../../.github/workflows/e2e-umbrella.yml) runs the suite on pushes to `main`, nightly, on demand, and on pull requests that touch `src/`, `tests/e2e/`, the workflow or the dependencies. The job does the following:

1. It creates a `kind` cluster inside the runner.
2. It deploys Tractus-X Umbrella `26.03.00` with the `values-adopter-decentralized-identityhub` profile. The deployment is the same one [Tractus-X TestLab's E2E workflow](https://github.com/eclipse-tractusx/tractusx-testlab/blob/main/.github/workflows/e2e-umbrella.yml) runs. TestLab's CI helpers (`tests/e2e/connector-dtr-smoke/ci/`) are checked out at the pinned commit `TESTLAB_REF`.
3. It issues the Catena-X credentials to both participants. It also deploys a small submodel server (`tck-submodel.local`), which backs the test asset.
4. It runs `pytest tests/e2e` and writes a results table to the job summary. The JUnit report is uploaded as the artifact `sdk-e2e-results-<run id>`. If the job fails, the cluster diagnostics are uploaded as `umbrella-diagnostics-<run id>`.

## Running it locally

You need a dataspace that you can reach from your machine. The simplest way is to replay the workflow's steps on a local `kind` cluster, add the hostnames from `DATASPACE_HOSTS` to `/etc/hosts`, and then run:

```bash
TX_SDK_E2E=1 \
E2E_PROVIDER_API_KEY=<provider management API key> \
E2E_CONSUMER_API_KEY=<consumer management API key> \
poetry run pytest tests/e2e -v
```

All other settings default to the Umbrella CI deployment and can be overridden:

| Variable | Default |
|---|---|
| `E2E_PROVIDER_MANAGEMENT_URL` / `E2E_CONSUMER_MANAGEMENT_URL` | `http://provider-management.local` / `http://consumer-management.local` |
| `E2E_PROVIDER_DMA_PATH` / `E2E_CONSUMER_DMA_PATH` | `/management` |
| `E2E_PROVIDER_DID` / `E2E_CONSUMER_DID` | `did:web:provider.local:identityhub:BPNL000000000001` / `did:web:consumer.local:identityhub:BPNL000000000002` |
| `E2E_PROVIDER_BPN` / `E2E_CONSUMER_BPN` | `BPNL000000000001` / `BPNL000000000002` |
| `E2E_PROVIDER_DSP_URL` | `http://provider-dsp.local/api/v1/dsp/2025-1` |
| `E2E_BACKEND_URL` | `http://tck-submodel.local` (must accept `POST`/`GET`/`DELETE` of JSON at any path) |
| `E2E_DTR_BASE_URL` / `E2E_DTR_API_PATH` | `http://provider-dtr.local/semantics/registry` / `/api/v3` |
| `E2E_TIMEOUT_SECONDS` | `120` (wait limit for the negotiation, the transfer and `do_get`) |

The management API keys have no default. If `TX_SDK_E2E=1` is set and a key is missing, the suite fails right away and names the missing variable.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
