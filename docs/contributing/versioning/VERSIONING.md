# Documentation Versioning

This project uses automated documentation versioning with MkDocs Material and Mike.

## How It Works

The documentation versioning is fully automated through GitHub Actions:

### Automatic Deployments

- **Tagged Releases**: When you create a tag like `v0.5.0`, the workflow automatically:
  - Deploys documentation for that version
  - Updates the `latest` alias to point to the new version
  - Sets it as the default version

- **Main Branch**: Every push to `main` automatically deploys the development docs to a `main` version

- **Pull Requests**: PRs are validated by building the docs (but not deploying)

### Version Selector

Users will see a version selector in the documentation header allowing them to switch between:
- Latest stable release (e.g., `0.5.0`)
- Development version (`main`)  
- Previous versions (e.g., `0.4.0`)

### Usage

1. **For new releases**: Just create and push a git tag starting with `v`:
   ```bash
   git tag v0.6.0
   git push origin v0.6.0
   ```

2. **For development**: Simply push to main - docs are automatically updated

No manual intervention needed! 🚀

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025 Contributors to the Eclipse Foundation
- Source URL: https://github.com/eclipse-tractusx/tractusx-sdk
