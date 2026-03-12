# Connector Examples

This directory is reserved for connector service usage examples demonstrating provider and consumer operations with the Tractus-X SDK.

## Test Compatibility Kit (TCK)

For complete end-to-end examples of connector interactions — including asset provisioning, catalog discovery, contract negotiation, EDR token flow, and data consumption — see the **[Connector TCK](../../../../tck/connector/README.md)**.

The TCK provides 6 ready-to-run test scripts covering:

| Protocol | EDC Version | Scripts |
|----------|-------------|---------|
| **Saturn** (DSP 2025-1) | 0.11.x+ | `tck_e2e_saturn_0-11-X_detailed.py`, `tck_e2e_saturn_0-11-X_simple.py`, `*_did.py` variants |
| **Jupiter** (Legacy DSP) | 0.8.x–0.10.x | `tck_e2e_jupiter_0-10-X_detailed.py`, `tck_e2e_jupiter_0-10-X_simple.py` |

Each script demonstrates real SDK usage patterns (provider setup, consumer negotiation, data retrieval) and can serve as a reference for building your own connector integrations.

```bash
# Run all TCK tests
cd tck/connector
./run_all_tests.sh
```

See the [TCK documentation](../../../../docs/tck/index.md) for configuration and CI/CD integration guidance.
