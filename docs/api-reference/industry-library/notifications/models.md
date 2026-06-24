<!--

Eclipse Tractus-X - Software Development KIT

Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This work is made available under the terms of the
Creative Commons Attribution 4.0 International (CC-BY-4.0) license,
which is available at
https://creativecommons.org/licenses/by/4.0/legalcode.

SPDX-License-Identifier: CC-BY-4.0

-->
# Notification Models

The Notification Models provide Pydantic-based data models for constructing and validating Industry Core notifications following the Catena-X standard schema (`io.catenax.shared.message_header_3.0.0`).

## Overview

| Model | Description |
|-------|-------------|
| `Notification` | Complete notification combining header and content |
| `NotificationHeader` | Message metadata (sender, receiver, context, timestamps) |
| `NotificationContent` | Flexible payload body with optional structured fields |

All models support:

- **Pydantic validation** — automatic type checking and BPN format validation
- **Builder pattern** — fluent API for constructing notifications
- **Serialization** — `to_data()` and `to_json_string()` for API-ready output
- **camelCase aliases** — fields follow the Industry Core JSON schema conventions

---

## Notification

The top-level model that combines `NotificationHeader` and `NotificationContent`.

### Using the Builder (recommended)

```python
from tractusx_sdk.industry.models.notifications import Notification

notification = (
    Notification.builder()
    .context("IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0")
    .sender_bpn("BPNL000000000001")
    .receiver_bpn("BPNL000000000002")
    .information("Part relationship update notification")
    .affected_items(["SN-12345", "SN-67890"])
    .build()
)
```

### Using Constructors Directly

```python
from tractusx_sdk.industry.models.notifications import (
    Notification,
    NotificationHeader,
    NotificationContent,
)

header = NotificationHeader(
    context="IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0",
    sender_bpn="BPNL000000000001",
    receiver_bpn="BPNL000000000002",
)

content = NotificationContent(
    information="Part relationship update",
    list_of_affected_items=["SN-12345"],
)

notification = Notification(header=header, content=content)
```

### Serialization

```python
# To dictionary (for API requests)
data = notification.to_data()
# {
#   "header": {
#     "messageId": "...",
#     "context": "IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0",
#     "sentDateTime": "2026-03-12T...",
#     "senderBpn": "BPNL000000000001",
#     "receiverBpn": "BPNL000000000002",
#     "version": "3.0.0"
#   },
#   "content": {
#     "information": "Part relationship update",
#     "listOfAffectedItems": ["SN-12345"]
#   }
# }

# To JSON string
json_str = notification.to_json_string()
```

---

## NotificationHeader

Based on `io.catenax.shared.message_header_3.0.0`.

### Fields

| Field | Type | Required | Alias | Description |
|-------|------|----------|-------|-------------|
| `message_id` | `UUID` | No (auto-generated) | `messageId` | Unique message identifier |
| `context` | `str` | **Yes** | — | Context string, e.g. `IndustryCore-DigitalTwinEventAPI-ConnectToParent:3.0.0` |
| `sent_date_time` | `datetime` | No (auto: now UTC) | `sentDateTime` | ISO 8601 timestamp |
| `sender_bpn` | `str` | **Yes** | `senderBpn` | Sender BPNL (pattern: `BPNL[0-9A-Za-z]{12}`) |
| `receiver_bpn` | `str` | **Yes** | `receiverBpn` | Receiver BPNL (pattern: `BPNL[0-9A-Za-z]{12}`) |
| `version` | `str` | No (default: `3.0.0`) | — | Semantic version of the header aspect model |
| `expected_response_by` | `datetime` | No | `expectedResponseBy` | Optional response deadline |
| `related_message_id` | `UUID` | No | `relatedMessageId` | Optional reference to a related message |

### BPN Validation

Sender and receiver BPNs are validated against the pattern `BPNL` followed by 12 alphanumeric characters:

```python
# Valid
header = NotificationHeader(
    context="...",
    sender_bpn="BPNL000000000001",
    receiver_bpn="BPNL000000000002",
)

# Invalid — raises ValidationError
header = NotificationHeader(
    context="...",
    sender_bpn="INVALID_BPN",
    receiver_bpn="BPNL000000000002",
)
```

---

## NotificationContent

Flexible content model that allows additional fields via Pydantic's `extra = "allow"`.

### Fields

| Field | Type | Required | Alias | Description |
|-------|------|----------|-------|-------------|
| `information` | `str` | No | — | Human-readable notification message |
| `list_of_affected_items` | `List[str]` | No (default: `[]`) | `listOfAffectedItems` | List of affected part/serial numbers |

### Adding Custom Fields

Since `extra = "allow"` is enabled, you can pass any additional fields:

```python
content = NotificationContent(
    information="Quality alert",
    list_of_affected_items=["SN-001"],
    severity="HIGH",
    classification="QualityInvestigation",
)

data = content.to_data()
# Includes: severity, classification alongside standard fields
```

---

## Builder API Reference

The `Notification.builder()` provides a fluent API that covers both header and content fields in a single chain:

| Builder Method | Sets | Target |
|---------------|------|--------|
| `.context(str)` | `header.context` | Header |
| `.sender_bpn(str)` | `header.sender_bpn` | Header |
| `.receiver_bpn(str)` | `header.receiver_bpn` | Header |
| `.message_id(UUID)` | `header.message_id` | Header |
| `.sent_date_time(datetime)` | `header.sent_date_time` | Header |
| `.version(str)` | `header.version` | Header |
| `.expected_response_by(datetime)` | `header.expected_response_by` | Header |
| `.related_message_id(UUID)` | `header.related_message_id` | Header |
| `.information(str)` | `content.information` | Content |
| `.affected_items(List[str])` | `content.list_of_affected_items` | Content |
| `.header(NotificationHeader)` | Complete header | Header |
| `.content(NotificationContent)` | Complete content | Content |
| `.build()` | — | Returns `Notification` |

---

## Schema Reference

The notification models follow the Catena-X Industry Core Notifications schema:

- **Message Header**: `io.catenax.shared.message_header_3.0.0`
- **Notification Schema**: [catenax-ev.github.io/assets/files/notification.schema.json](https://catenax-ev.github.io/assets/files/notification.schema.json)
- **Standard**: [CX-0149 Industry Core](https://catenax-ev.github.io/docs/next/standards/CX-0149-Industry-Core)

## NOTICE

This work is licensed under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

- SPDX-License-Identifier: CC-BY-4.0
- SPDX-FileCopyrightText: 2025, 2026 Contributors to the Eclipse Foundation
- SPDX-FileCopyrightText: 2025, 2026 Catena-X Automotive Network e.V.
- Source URL: [https://github.com/eclipse-tractusx/tractusx-sdk](https://github.com/eclipse-tractusx/tractusx-sdk)
