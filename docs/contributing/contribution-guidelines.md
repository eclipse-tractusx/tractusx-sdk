<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2025 LKS Next
Copyright (c) 2025 Mondragon Unibertsitatea
Copyright (c) 2025 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->
# Contributing to Eclipse Tractus-X SDK

Thanks for your interest in contributing to this project.

## Project description

The Tractus-X SDK is a modular Python library that provides simplified APIs and methods for interacting with dataspace infrastructure. It serves as a comprehensive toolkit for both **providing** and **consuming** data in the Tractus-X ecosystem.

## GitHub Repository

The project is available at GitHub in the [Eclipse-Tractusx-SDK Repository](https://github.com/eclipse-tractusx/tractusx-sdk)

## Project licenses

The Tractus-X project uses the following licenses:

* Apache-2.0 for code
* CC-BY-4.0 for non-code

## Terms of Use for Eclipse

This repository is subject to the [Terms of Use of the Eclipse Foundation](https://www.eclipse.org/legal/termsofuse.php)

More information on how to contribute to Eclipse Tractus-X is available at [Eclipse-TractusX-SDK](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CONTRIBUTING.md)

## Quick Links and Resources

### **Getting Started**
- [Installation Guide](../tutorials/getting-started.md) - Set up your development environment
- [First step: Creation of an asset](../tutorials/getting-started.md) - Build your first dataspace application

### **Core Concepts**
- [Dataspace Library](../core-concepts/dataspace-concepts/index.md) - Core connector services and Eclipse Tractus-X Connector integration
- [Industry Library](../core-concepts/industry-concepts/index.md) - Digital Twin Registry and Submodel Server integration
- [Extension Library](../api-reference/extension-library/semantics/semantics.md) - Use case-specific extensions and add-on functionality

### **Development**
- [GitHub Repository](https://github.com/eclipse-tractusx/tractusx-sdk) - Source code and issues
- [PyPI Package](https://pypi.org/project/tractusx-sdk/) - Latest releases
- [Changelog](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CHANGELOG.md) - Version history

### **Community**
- [Discussions](https://github.com/eclipse-tractusx/tractusx-sdk/discussions) - Ask questions and share ideas
- [Contributing Guidelines](https://github.com/eclipse-tractusx/tractusx-sdk/blob/main/CONTRIBUTING.md) - How to contribute
- [Community Meetings](https://eclipse-tractusx.github.io/community/open-meetings#Industry%20Core%20Hub%20&%20Tractus-X%20SDK%20Weekly) - Weekly developer meetings

### **Additional Resources**
- [Eclipse Tractus-X](https://eclipse-tractusx.github.io/) - Official project website
- [Tractus-X KITs](https://eclipse-tractusx.github.io/Kits) - Standard specifications

## Logging conventions

The SDK is a library: its logs end up in the platforms of the applications that use it, next to credentials and business data. The rules below are enforced by `tests/test_logging_hygiene.py`, and the full guide is [Logging and Error Handling](../admin/logging.md).

- Use one `logger = logging.getLogger(__name__)` per module. Never `print`, never configure logging, and do not add `verbose`, `debug` or `logger` arguments.
- Format lazily, with `%s` arguments.
- Build the context of a record only with `extra=log_extra(...)`, which accepts the documented fields, and give it an `operation=LogOperations.X` constant. A new constant goes in `src/tractusx_sdk/_logging_operations.py`, named after its value in upper case with the dot as an underscore (`consumer.get_catalog` is `CONSUMER_GET_CATALOG`).
- Log a failure with `log_failure(logger, "... (%s)", error, ...)`, which logs the **type** of the exception. Never log `str(error)`, a traceback, `logger.exception(...)` or `exc_info=True`: the messages of `requests`, `httpx` and SQLAlchemy quote the URL with its query string or the SQL parameters, which can hold access tokens.
- Log URLs with `safe_url`. Never log headers, tokens, credentials, response bodies or submodel data.
- Levels: the inner layers of a call log at `DEBUG` and let the exception travel, and the operation that reports the failure logs one `ERROR`. Expected outcomes (a `404`, a missing BPN) stay at `DEBUG`, and a polling loop does not log every iteration.
- A traceback is only allowed in the modules listed in `TRACEBACK_ALLOWED` in the hygiene test, each with the reason why what it catches holds nothing sensitive. A new entry is reviewed like any other security decision, and an entry that is no longer needed fails the test.
- Test it with `caplog`. `tests/test_logging_secret_leaks.py` renders the records the way a handler would, tracebacks included, and asserts that a secret in the failure never reaches them.

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- SPDX-FileCopyrightText: 2025, 2026 LKS Next
- SPDX-FileCopyrightText: 2025, 2026 Mondragon Unibertsitatea
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
