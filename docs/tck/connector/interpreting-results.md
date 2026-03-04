<!--
Eclipse Tractus-X - Tractus-X SDK

Copyright (c) 2026 Catena-X Automotive Network e.V.
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License, Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0.

SPDX-License-Identifier: Apache-2.0
-->

# Interpreting Results

## Log Files

Test results are written to timestamped log files alongside the console output:

```bash
# Log file naming convention:
saturn_e2e_run_2026-02-24_140847_PASS.log
jupiter_simple_e2e_run_2026-02-24_140741_FAIL.log

# View recent test logs
ls -lt *_e2e_run_*.log | head

# Inspect a specific run
less saturn_e2e_run_2026-02-24_140847_PASS.log

# Search for errors in failed tests
grep -i "error\|exception\|fail" jupiter_e2e_run_*_FAIL.log
```

## Successful Run Example

```
2026-02-24 14:08:47,294 INFO [saturn_e2e] Logging to file: saturn_e2e_run_2026-02-24_140847.log
2026-02-24 14:08:47,425 INFO [saturn_e2e] ✓ Access Policy created: access-policy-bpn-1771938527
2026-02-24 14:08:47,520 INFO [saturn_e2e] ✓ Usage Policy created: usage-policy-framework-1771938527
2026-02-24 14:08:47,559 INFO [saturn_e2e] ✓ Asset created: vehicle-production-data-1771938527
2026-02-24 14:08:47,583 INFO [saturn_e2e] ✓ Contract Definition created: contract-def-1771938527

2026-02-24 14:08:51,583 INFO [saturn_e2e] [CATALOG RESPONSE]:
{
  "@id": "5e19371d-09dd-4616-b442-1f4ee888b052",
  "@type": "Catalog",
  "dataset": [{ ... }]
}

2026-02-24 14:08:55,691 INFO [saturn_e2e] ✓ Contract Agreement finalized: 056c594b-e344-41a0-8cc8-0737592e020b
2026-02-24 14:09:00,064 INFO [saturn_e2e] ✓ EDR received!

╔══════════════════════════════════════════════════════════════════════════════╗
║                              E2E TEST RUN SUMMARY                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  STEP                                          RESULT      TIME              ║
║  ──────────────────────────────────────────────────────────────────────────  ║
║  ✓ Phase 0 · Upload sample data to backend       PASS      0.1s              ║
║  ✓ Phase 1 · Provider data provision             PASS      0.2s              ║
║  ✓ Phase 2 · Consumer data consumption           PASS      9.5s              ║
║  ✓ Phase 3 · Access data with EDR                PASS      0.4s              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  RESULT: PASS  |  4 passed  0 failed  0 skipped  |  Total: 13.2s             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Structured Logging Markers

TCK tests annotate all HTTP interactions with structured markers:

| Marker | Description |
|--------|-------------|
| `[UPLOAD REQUEST]` / `[UPLOAD RESPONSE]` | Backend data upload |
| `[CATALOG RESPONSE]` | Provider catalog with datasets and offers |
| `[NEGOTIATION REQUEST]` / `[NEGOTIATION RESPONSE]` | Contract negotiation initiation |
| `[NEGOTIATION STATE RESPONSE]` | Negotiation state polling |
| `[TRANSFER REQUEST]` / `[TRANSFER RESPONSE]` | Transfer process initiation |
| `[EDR RESPONSE]` | Endpoint Data Reference (token + endpoint) |
| `[DATA RESPONSE]` | Final data payload retrieved from backend |

## PASS Criteria

A test is marked **PASS** when all four phases complete successfully:

- **Phase 0**: Sample data uploaded to backend (HTTP 200)
- **Phase 1**: All provider resources created (policies, asset, contract definition)
- **Phase 2**: Consumer successfully negotiates and obtains an EDR token
- **Phase 3**: Data retrieved using the EDR matches the uploaded payload

## Troubleshooting

### Phase 0 — Backend Upload Failures

```
HTTPError: 401 Unauthorized
```
→ Check backend API key (`backend.api_key` in config).

```
HTTPError: 404 Not Found
```
→ Verify `backend.base_url` is correct and does not include a trailing UUID.

---

### Phase 1 — Provider Provision Failures

```
HTTPError: 401 Unauthorized
```
→ Verify `provider.api_key` is correct.

```
HTTPError: 409 Conflict
```
→ Resource ID already exists. Change the timestamp seed or clean up existing resources.

---

### Phase 2 — Consumer Consumption Failures

**Asset not found in catalog**

- Wait longer after creating the contract definition (try 5+ seconds)
- Verify the Consumer BPN is in the Provider's access policy
- Check catalog filtering (asset ID, DCT type) is correct

**Contract negotiation timeout (state stuck in `REQUESTING`)**

- Verify the Consumer can reach the Provider DSP endpoint
- Check Provider logs for negotiation errors
- Verify ODRL context URLs match the EDC version
- Verify both parties are properly onboarded in the dataspace with valid Verifiable Credentials

**Contract negotiation `TERMINATED` by provider**

- Consumer lacks required Verifiable Credentials (BPN credential, Framework Agreement membership, etc.)
- Policy constraint not satisfied — check VC claims match `leftOperand` values in the policy
- SSI/credential verification failed on Provider side
- Check Provider EDC logs for credential validation errors

**EDR not available after transfer (state stuck in `REQUESTED`)**

- Check Provider Data Plane is running
- Verify backend URL is reachable from the Provider Data Plane
- Check backend authentication if required

---

### Phase 3 — Data Access Failures

```
HTTPError: 401 Unauthorized
```
→ EDR token expired — re-run from Phase 2, or check the `authorization` field format in the EDR.

```
HTTPError: 403 Forbidden
```
→ Token validation failed on Provider side — check Provider Data Plane token validation settings.

```
HTTPError: 502 Bad Gateway
```
→ Provider Data Plane cannot reach backend — check backend URL and credentials.

---

### SSL Certificate Errors

```
ssl.SSLCertVerificationError: certificate verify failed
```

Tests use `verify=False` for self-signed certificates in test environments. For production, pass a custom CA bundle:

```python
consumer_service.get_catalog_by_asset_id_with_bpnl(..., verify="/path/to/ca-bundle.crt")
```

---

### JSON-LD Context Mismatches

```
KeyError: 'dcat:dataset'   # or  KeyError: 'dataset'
```

Check that the EDC version matches the protocol:

- Jupiter expects prefixed keys (`dcat:dataset`, `odrl:hasPolicy`)
- Saturn may use unprefixed or prefixed keys (SDK handles both)

---

### Discovery Service Not Found (Saturn)

```
HTTPError: 404 Not Found (Discovery Finder)
```

1. Verify Discovery Finder URL is correct
2. Register the Provider BPN in the Discovery Service
3. Check BPN format (must match exactly, including the `BPNL` prefix)

---

### Transfer Stuck in `REQUESTED`

```
Transfer state: REQUESTED (polling timeout)
```

1. Check Provider Data Plane logs for backend connection errors
2. Verify backend API key is valid
3. Test backend accessibility from Data Plane network:
```bash
curl -v https://backend.example.com/api/data
```

## Common Issues

**Connection Problems**

Most failures come down to network paths. Make sure your Consumer EDC can actually reach the Provider's DSP endpoint, and the Provider Data Plane can hit your backend storage. Firewall rules are usually the culprit.

**Credential Validation**

For Saturn tests, both organizations need to be properly onboarded with valid BPN credentials. If contract negotiation gets terminated, check that the Consumer has the required Framework Agreement VCs (like `DataExchangeGovernance:1.0`) and that the claims match your policy constraints.

**Negotiation Trouble shooting**

If negotiation get stuck in `REQUESTED` state, verify on the logs of the control plane what went wrong. In case the transfer works and no data is retrieved, double-check API keys and that the backend accepts requests from the Data Plane.

## Documentation References

- **Tractus-X EDC**: [Management API Walkthrough](https://github.com/eclipse-tractusx/tractusx-edc/tree/main/docs/usage/management-api-walkthrough)
- **SDK API Reference**: [Connector Services](../../api-reference/dataspace-library/connector/services.md)
- **Industry Core Hub**: [Reference Implementation](https://github.com/eclipse-tractusx/industry-core-hub)
- **DSP Spec 2024-1 / 0.8**: [IDS Knowledgebase](https://docs.internationaldataspaces.org/ids-knowledgebase/v/dataspace-protocol)
- **DSP Spec 2025-1**: [Eclipse DSP Base](https://eclipse-dataspace-protocol-base.github.io/DataspaceProtocol/2025-1/)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
