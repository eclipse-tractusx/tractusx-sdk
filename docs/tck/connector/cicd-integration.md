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

# CI/CD Integration

This guide shows how to run TCK tests in continuous integration pipelines. The examples use GitHub Actions with [Tractus-X Umbrella](https://github.com/eclipse-tractusx/tractus-x-umbrella), which provides a complete Catena-X dataspace environment including EDC connectors, SSI DIM Wallet, Digital Twin Registry, and test data.

!!! info "Umbrella Deployment Configuration"
    The workflows use the **Data Exchange Subset** configuration from Tractus-X Umbrella via the [`values-adopter-data-exchange.yaml`](https://github.com/eclipse-tractusx/tractus-x-umbrella/blob/main/charts/umbrella/values-adopter-data-exchange.yaml) file. This enables:
    
    - `tx-data-provider` — EDC provider connector + Digital Twin Registry + simple-data-backend
    - `dataconsumerOne` — EDC consumer connector
    - `identity-and-trust-bundle` — SSI DIM wallet stub for credential management
    
    The current umbrella releases deploy **Saturn protocol (EDC 0.11.x+)** by default. For detailed deployment options, see the [Umbrella Installation Guide](https://github.com/eclipse-tractusx/tractus-x-umbrella/blob/main/docs/user/linux/installation/README.md).

## Overview

TCK CI/CD workflows typically:

1. **Deploy infrastructure** — Spin up a complete dataspace using Tractus-X Umbrella Helm charts
2. **Wait for readiness** — Ensure all connectors and services are healthy
3. **Run TCK tests** — Execute all 6 test scripts (or a subset)
4. **Report results** — Pass/fail the workflow based on test outcomes
5. **Cleanup** — Tear down the test environment

## Prerequisites

### Required Secrets

Configure these secrets in your GitHub repository settings:

| Secret | Description |
|--------|-------------|
| `KUBE_CONFIG` | Base64-encoded kubeconfig file for your Kubernetes cluster |
| `ACR_REGISTRY` (optional) | Azure Container Registry or other private registry URL |
| `ACR_USERNAME` (optional) | Registry username |
| `ACR_PASSWORD` (optional) | Registry password/token |

### Cluster Requirements

- **Kubernetes cluster**: 1.24+
- **Helm**: 3.10+
- **Ingress controller**: NGINX or Traefik
- **Storage**: Dynamic PV provisioner
- **Resources**: Minimum 8 CPU / 16GB RAM available

## Workflow: Saturn (EDC 0.11.x+)

This workflow deploys Tractus-X Umbrella with Saturn protocol (DSP 2025-1) and runs all Saturn TCK tests.

Create `.github/workflows/tck-saturn.yml`:

```yaml
name: TCK Saturn Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  tck-saturn:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - name: Checkout SDK
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install SDK
        run: |
          pip install --upgrade pip
          pip install -e .

      - name: Set up Helm
        uses: azure/setup-helm@v4
        with:
          version: '3.14.0'

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'v1.29.0'

      - name: Configure kubectl
        run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > ~/.kube/config
          kubectl config use-context default

      - name: Create namespace
        run: |
          NAMESPACE="tck-saturn-${{ github.run_id }}"
          echo "NAMESPACE=$NAMESPACE" >> $GITHUB_ENV
          kubectl create namespace $NAMESPACE

      - name: Add Tractus-X Helm repo
        run: |
          helm repo add tractusx-dev https://eclipse-tractusx.github.io/charts/dev
          helm repo update

      - name: Deploy Tractus-X Umbrella (Saturn)
        run: |
          helm install umbrella tractusx-dev/umbrella \
            --namespace ${{ env.NAMESPACE }} \
            -f https://raw.githubusercontent.com/eclipse-tractusx/tractus-x-umbrella/main/charts/umbrella/values-adopter-data-exchange.yaml \
            --set global.domain=tx.test \
            --timeout 15m \
            --wait
        # The values-adopter-data-exchange.yaml file enables:
        # - tx-data-provider (EDC provider + DTR + backend)
        # - dataconsumerOne (EDC consumer)
        # - identity-and-trust-bundle (SSI DIM wallet stub)
        # By default, this deploys Saturn protocol (EDC 0.11.x+)

      - name: Wait for EDC connectors
        run: |
          echo "Waiting for provider and consumer connectors to be ready..."
          kubectl wait --for=condition=ready pod \
            -l app.kubernetes.io/component=controlplane \
            -n ${{ env.NAMESPACE }} \
            --timeout=300s

      - name: Port-forward services
        run: |
          # Provider
          kubectl port-forward -n ${{ env.NAMESPACE }} \
            svc/dataprovider-controlplane 8080:8080 &
          
          # Consumer
          kubectl port-forward -n ${{ env.NAMESPACE }} \
            svc/dataconsumer-1-controlplane 8081:8080 &
          
          # Backend
          kubectl port-forward -n ${{ env.NAMESPACE }} \
            svc/dataprovider-submodelserver 8082:8080 &
          
          # Wait for port-forwards to establish
          sleep 10
          echo "Port-forwards established"

      - name: Generate TCK config for Saturn
        run: |
          cat > tck/connector/tck-config-ci-saturn.yaml <<EOF
          # Saturn configuration supports both BPNL and DID discovery modes
          # BPNL scripts use: dsp_url, access_policy
          # DID scripts use: dsp_url_did (via provider_did property), access_policy_did
          saturn:
            provider:
              base_url: "http://localhost:8080"
              dma_path: "/management"
              api_key: "TEST2"
              bpn: "BPNL00000003AYRE"
              dsp_url: "http://localhost:8080/api/v1/dsp"
              dsp_url_did: "http://localhost:8080/api/v1/dsp/2025-1"
              did: "did:web:dataprovider"
            consumer:
              base_url: "http://localhost:8081"
              dma_path: "/management"
              api_key: "TEST1"
              bpn: "BPNL00000003AZQP"
              did: "did:web:dataconsumer-1"
            backend:
              base_url: "http://localhost:8082"
              api_key: ~
            policies:
              protocol: "dataspace-protocol-http:2025-1"
              negotiation_context:
                - "https://w3id.org/catenax/2025/9/policy/odrl.jsonld"
                - "https://w3id.org/catenax/2025/9/policy/context.jsonld"
                - "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
              # BPNL discovery: BusinessPartnerNumber-based access
              access_policy:
                permissions:
                  - action: "access"
                    constraint:
                      leftOperand: "BusinessPartnerNumber"
                      operator: "isAnyOf"
                      rightOperand: ~   # auto-set to consumer BPN at runtime
              # DID discovery: Membership-based access with explicit context
              access_policy_did:
                context:
                  - "https://w3id.org/catenax/2025/9/policy/odrl.jsonld"
                  - "https://w3id.org/catenax/2025/9/policy/context.jsonld"
                  - "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                permissions:
                  - action: "access"
                    constraint:
                      leftOperand: "Membership"
                      operator: "eq"
                      rightOperand: "active"
              # Shared usage policy for both BPNL and DID discovery modes
              usage_policy:
                permissions:
                  - action: "use"
                    constraint:
                      and:
                        - leftOperand: "Membership"
                          operator: "eq"
                          rightOperand: "active"
                        - leftOperand: "FrameworkAgreement"
                          operator: "eq"
                          rightOperand: "DataExchangeGovernance:1.0"
                        - leftOperand: "UsagePurpose"
                          operator: "isAnyOf"
                          rightOperand: "cx.core.industrycore:1"
          EOF

      - name: Run Saturn TCK tests (BPNL discovery)
        run: |
          cd tck/connector
          python tck_e2e_saturn_0-11-X_simple.py --config tck-config-ci-saturn.yaml
          python tck_e2e_saturn_0-11-X_detailed.py --config tck-config-ci-saturn.yaml

      - name: Run Saturn TCK tests (DID discovery)
        run: |
          cd tck/connector
          python tck_e2e_saturn_0-11-X_simple_did.py --config tck-config-ci-saturn.yaml
          python tck_e2e_saturn_0-11-X_detailed_did.py --config tck-config-ci-saturn.yaml

      - name: Collect logs on failure
        if: failure()
        run: |
          mkdir -p ci-logs
          kubectl logs -n ${{ env.NAMESPACE }} -l app.kubernetes.io/component=controlplane --tail=500 > ci-logs/edc-logs.txt
          kubectl get pods -n ${{ env.NAMESPACE }} -o wide > ci-logs/pods.txt
          kubectl describe pods -n ${{ env.NAMESPACE }} > ci-logs/pods-describe.txt

      - name: Upload logs
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: tck-saturn-logs-${{ github.run_id }}
          path: ci-logs/
          retention-days: 7

      - name: Cleanup
        if: always()
        run: |
          helm uninstall umbrella -n ${{ env.NAMESPACE }} || true
          kubectl delete namespace ${{ env.NAMESPACE }} --wait=false || true
```

## Workflow: Jupiter (EDC 0.8.x–0.10.x)

This workflow deploys Tractus-X Umbrella with Jupiter protocol (legacy DSP) and runs Jupiter TCK tests.

Create `.github/workflows/tck-jupiter.yml`:

```yaml
name: TCK Jupiter Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  tck-jupiter:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - name: Checkout SDK
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install SDK
        run: |
          pip install --upgrade pip
          pip install -e .

      - name: Set up Helm
        uses: azure/setup-helm@v4
        with:
          version: '3.14.0'

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'v1.29.0'

      - name: Configure kubectl
        run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > ~/.kube/config
          kubectl config use-context default

      - name: Create namespace
        run: |
          NAMESPACE="tck-jupiter-${{ github.run_id }}"
          echo "NAMESPACE=$NAMESPACE" >> $GITHUB_ENV
          kubectl create namespace $NAMESPACE

      - name: Add Tractus-X Helm repo
        run: |
          helm repo add tractusx-dev https://eclipse-tractusx.github.io/charts/dev
          helm repo update

      - name: Deploy Tractus-X Umbrella (Jupiter)
        run: |
          helm install umbrella tractusx-dev/umbrella \
            --namespace ${{ env.NAMESPACE }} \
            -f https://raw.githubusercontent.com/eclipse-tractusx/tractus-x-umbrella/main/charts/umbrella/values-adopter-data-exchange.yaml \
            --set global.domain=tx.test \
            --timeout 15m \
            --wait
        # The values-adopter-data-exchange.yaml file enables the data exchange subset.
        # Note: Current umbrella releases use Saturn (EDC 0.11.x+) by default.
        # For Jupiter (EDC 0.8-0.10.x), you may need to use an older chart version
        # or create a custom values file with EDC version overrides.

      - name: Wait for EDC connectors
        run: |
          echo "Waiting for provider and consumer connectors to be ready..."
          kubectl wait --for=condition=ready pod \
            -l app.kubernetes.io/component=controlplane \
            -n ${{ env.NAMESPACE }} \
            --timeout=300s

      - name: Port-forward services
        run: |
          # Provider
          kubectl port-forward -n ${{ env.NAMESPACE }} \
            svc/dataprovider-controlplane 8080:8080 &
          
          # Consumer
          kubectl port-forward -n ${{ env.NAMESPACE }} \
            svc/dataconsumer-1-controlplane 8081:8080 &
          
          # Backend
          kubectl port-forward -n ${{ env.NAMESPACE }} \
            svc/dataprovider-submodelserver 8082:8080 &
          
          # Wait for port-forwards to establish
          sleep 10
          echo "Port-forwards established"

      - name: Generate TCK config for Jupiter
        run: |
          cat > tck/connector/tck-config-ci-jupiter.yaml <<EOF
          jupiter:
            provider:
              base_url: "http://localhost:8080"
              dma_path: "/management"
              api_key: "TEST2"
              bpn: "BPNL00000003AYRE"
              dsp_url: "http://localhost:8080/api/v1/dsp"
              did: ~
            consumer:
              base_url: "http://localhost:8081"
              dma_path: "/management"
              api_key: "TEST1"
              bpn: "BPNL00000003AZQP"
              did: ~
            backend:
              base_url: "http://localhost:8082"
              api_key: ~
            policies:
              protocol: "dataspace-protocol-http"
              negotiation_context:
                - "https://w3id.org/tractusx/policy/v1.0.0"
                - "http://www.w3.org/ns/odrl.jsonld"
                - "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
              access_policy:
                profile: "cx-policy:profile2405"
                context:
                  - "https://w3id.org/tractusx/policy/v1.0.0"
                  - "http://www.w3.org/ns/odrl.jsonld"
                  - tx: "https://w3id.org/tractusx/v0.0.1/ns/"
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                permissions:
                  - action: "use"
                    constraint:
                      leftOperand: "tx:BusinessPartnerNumber"
                      operator: "eq"
                      rightOperand: "BPNL00000003AZQP"
              usage_policy:
                profile: "cx-policy:profile2405"
                context:
                  - "https://w3id.org/tractusx/policy/v1.0.0"
                  - "http://www.w3.org/ns/odrl.jsonld"
                  - tx: "https://w3id.org/tractusx/v0.0.1/ns/"
                    "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
                permissions:
                  - action: "use"
                    constraint:
                      leftOperand: "tx:FrameworkAgreement"
                      operator: "eq"
                      rightOperand: "Traceability:1.0"
          EOF

      - name: Run Jupiter TCK tests
        run: |
          cd tck/connector
          python tck_e2e_jupiter_0-10-X_simple.py --config tck-config-ci-jupiter.yaml
          python tck_e2e_jupiter_0-10-X_detailed.py --config tck-config-ci-jupiter.yaml

      - name: Collect logs on failure
        if: failure()
        run: |
          mkdir -p ci-logs
          kubectl logs -n ${{ env.NAMESPACE }} -l app.kubernetes.io/component=controlplane --tail=500 > ci-logs/edc-logs.txt
          kubectl get pods -n ${{ env.NAMESPACE }} -o wide > ci-logs/pods.txt
          kubectl describe pods -n ${{ env.NAMESPACE }} > ci-logs/pods-describe.txt

      - name: Upload logs
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: tck-jupiter-logs-${{ github.run_id }}
          path: ci-logs/
          retention-days: 7

      - name: Cleanup
        if: always()
        run: |
          helm uninstall umbrella -n ${{ env.NAMESPACE }} || true
          kubectl delete namespace ${{ env.NAMESPACE }} --wait=false || true
```

## Workflow: All Tests (Comprehensive)

Run both Jupiter and Saturn tests in a single workflow with parallel jobs.

Create `.github/workflows/tck-all.yml`:

```yaml
name: TCK All Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:

jobs:
  test-jupiter:
    name: Jupiter Tests
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install SDK
        run: pip install -e .

      - name: Deploy and test
        run: |
          # Use the same steps as tck-jupiter.yml workflow above
          echo "See tck-jupiter.yml for full implementation"
          # This is a placeholder - copy steps from tck-jupiter.yml

  test-saturn:
    name: Saturn Tests
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install SDK
        run: pip install -e .

      - name: Deploy and test
        run: |
          # Use the same steps as tck-saturn.yml workflow above
          echo "See tck-saturn.yml for full implementation"
          # This is a placeholder - copy steps from tck-saturn.yml

  report:
    name: Test Report
    needs: [test-jupiter, test-saturn]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Check test results
        run: |
          if [ "${{ needs.test-jupiter.result }}" != "success" ] || \
             [ "${{ needs.test-saturn.result }}" != "success" ]; then
            echo "One or more TCK test suites failed"
            exit 1
          fi
          echo "All TCK tests passed"
```

## Local Testing with Kind

For local CI/CD testing without a cloud cluster, use [Kind (Kubernetes in Docker)](https://kind.sigs.k8s.io/).

### Setup

```bash
# Install Kind
brew install kind  # macOS
# or: curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64

# Create cluster
kind create cluster --name tck-test

# Install NGINX Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### Run Tests

```bash
# Deploy Umbrella (Saturn)
helm install umbrella tractusx-dev/umbrella \
  --namespace tck-local \
  --create-namespace \
  -f https://raw.githubusercontent.com/eclipse-tractusx/tractus-x-umbrella/main/charts/umbrella/values-adopter-data-exchange.yaml \
  --set global.domain=tx.test \
  --wait

# Port-forward and run tests
kubectl port-forward -n tck-local svc/dataprovider-controlplane 8080:8080 &
kubectl port-forward -n tck-local svc/dataconsumer-1-controlplane 8081:8080 &
kubectl port-forward -n tck-local svc/dataprovider-submodelserver 8082:8080 &

# Run TCK
cd tck/connector
./run_all_tests.sh --config tck-config-ci-saturn.yaml

# Cleanup
kind delete cluster --name tck-test
```

## Troubleshooting

### Tests fail during deployment

**Symptoms**: Helm install times out or pods never reach `Ready` state.

**Solutions**:

- Increase timeout: `--timeout 20m`
- Check pod logs: `kubectl logs -n $NAMESPACE <pod-name>`
- Verify resources: `kubectl describe pod -n $NAMESPACE <pod-name>`
- Check PVC binding: `kubectl get pvc -n $NAMESPACE`

### Port-forward connection refused

**Symptoms**: TCK tests cannot connect to `localhost:8080`.

**Solutions**:

- Verify port-forwards are running: `ps aux | grep port-forward`
- Check service exists: `kubectl get svc -n $NAMESPACE`
- Try different local ports to avoid conflicts
- Use `kubectl get endpoints -n $NAMESPACE` to verify service endpoints

### Policy validation fails

**Symptoms**: Contract negotiation stuck in `REQUESTING` or `TERMINATED`.

**Solutions**:

- Verify VC configuration matches policy `leftOperand` values
- Check SSI setup: `kubectl logs -n $NAMESPACE -l app=dim-wallet`
- Ensure BPN values in config match deployed VCs
- Review policy contexts match EDC version

### Namespace cleanup hangs

**Symptoms**: `kubectl delete namespace` never completes.

**Solutions**:

- Force delete: `kubectl delete namespace $NAMESPACE --grace-period=0 --force`
- Check for finalizers: `kubectl get namespace $NAMESPACE -o yaml`
- Delete stuck resources manually: `kubectl delete pvc --all -n $NAMESPACE`

## Best Practices

1. **Use unique namespaces** — Include `${{ github.run_id }}` to avoid conflicts
2. **Set timeouts** — Both at workflow level and individual steps
3. **Always cleanup** — Use `if: always()` for cleanup steps
4. **Collect logs on failure** — Upload pod logs and descriptions as artifacts
5. **Version pin** — Lock Helm chart and EDC versions for reproducibility
6. **Resource limits** — Set memory/CPU requests to avoid cluster saturation
7. **Parallel execution** — Run Jupiter and Saturn in separate jobs to save time

## Next Steps

| Topic | Description |
|-------|-------------|
| [Configuration](configuration.md) | Understand `tck-config.yaml` structure |
| [Running Tests](running-tests.md) | CLI options and parallel execution |
| [Interpreting Results](interpreting-results.md) | How to read TCK logs and diagnose failures |

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
