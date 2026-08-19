# Changelog

All notable changes to this repository will be documented in this file.
Further information can be found on the [README.md](README.md) file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

See also the overarching [CHANGELOG.md](https://eclipse-tractusx.github.io/changelog) for Tractus-X releases.

## [0.8.2] - 2026-08-18

### Added

- feat: `PolicyMismatchError` - a rejected catalog now says what was rejected. `DspTools.filter_assets_and_policies` raises it (a `ValueError`, so existing handlers are unaffected) carrying the `catalog` it read and the `allowed_policies` it compared against, and `_fetch_and_validate_catalog` chains it as the cause of its own `RuntimeError` instead of discarding it. Callers can report which offers were turned down and how they differed; before, the evidence was computed for a DEBUG log line and dropped

- feat: optional `trace` flag on the SDK services, adapters and factories, recording the requests sent to (and the responses received from) the external services and exposing them as JSON through `get_trace()` / `get_trace_json()`, or as `TraceEntry` objects through `get_trace_entries()`
- feat: named trace operations - `service.trace_operation(name)` and `Tracer.activate(name)` group the calls of a `with` block and hand them back on their own; traces now record the response `content_type`, keep non-JSON bodies (HTML as text, binary as base64), and can be filtered by `operation` / `operation_id`

### Changed

- feat: the EDR wait in `do_dsp` now polls the transfer process instead of re-querying the EDR cache until it stops returning an empty list. Once the negotiation is FINALIZED the contract agreement id is read from it and used to look up the transfer process (`get_transfer_process` / `get_transfer_process_filter`, filtered on `contractAgreementId`), which is created before the EDR is cached and reports a real state on every attempt. A transfer that ends in `TERMINATED` now fails immediately with the connector's `errorDetail` instead of timing out on an empty EDR query with "EDR entry was not found", and a transfer that stalls reports the state it was left in. The EDR entry is still read at the end, but by then it is guaranteed to be present. EDC names the agreement differently per entity and per connector version, and the queryable name is not always the one it returns, so the query probes `contractAgreementId`, `contractId` and `agreementId` in order, remembers whichever the connector accepts and sends a single request from then on; if all of them are rejected it raises with the connector's status and body instead of polling until the timeout. Callback addresses would be the event-driven alternative, but they require the consumer to expose a reachable HTTP endpoint, which local and batch executions cannot do

- chore: every state poll now reads the EDC `/state` endpoints through `get_state_by_id` instead of fetching the complete entity payload with `get_by_id` on each attempt. A tick returns just `{"@type": "NegotiationState", "state": "<STATE>"}` rather than the full object (policy, callback addresses, counterparty details, timestamps), which also keeps the request traces readable during long negotiations. Applied to the negotiation poll in `do_dsp` (`_check_single_negotiation_state`) and to both TCK connector runner steps - `_step_wait_for_agreement` and `_step_wait_for_edr`. No behaviour change: the state values compared are the same, and where the complete payload is genuinely needed it is now fetched once, after a terminal state is reached - `do_dsp` for the contract agreement id, the TCK runner for that id and its diagnostic dump

## [0.8.0] - 2026-06-15

### Added

- feat: add `clear_connections_by_party` method to connection managers for protocol-agnostic EDR cache eviction by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/220
- feat: add `do_get_by_dct_type_with_bpnl` and `do_put_by_dct_type_with_bpnl` convenience methods to `ConnectorConsumerService` (saturn) by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/218
- feat: add Python 3.13 and 3.14 compatibility test workflow by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/207

### Changed

- chore: qg x checks release r2606 — TRG compliance, Administrator's Guide, and architecture documentation by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/225
- chore: switch GitHub Actions checkout to SHA pins by @stephanbcbauer in https://github.com/eclipse-tractusx/tractusx-sdk/pull/214
- build(deps-dev): bump pymdown-extensions from 10.21 to 10.21.3 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/215
- build(deps): bump idna from 3.11 to 3.15 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/216
- build(deps): bump urllib3 from 2.6.3 to 2.7.0 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/213
- build(deps): bump python-multipart from 0.0.26 to 0.0.27 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/210
- build(deps): bump requests from 2.32.5 to 2.33.0 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/199
- build(deps): bump cryptography from 46.0.5 to 46.0.7 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/203
- build(deps-dev): bump pytest from 8.4.2 to 9.0.3 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/208
- build(deps): bump python-multipart from 0.0.22 to 0.0.26 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/204
- build(deps): bump pygments from 2.19.2 to 2.20.0 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/202
- build(deps): bump ecdsa from 0.19.1 to 0.19.2 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/200
- build(deps): bump pyasn1 from 0.6.2 to 0.6.3 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/196

## [0.7.2] - 2026-04-13

### Added

- feat: add caching tool by @gerbigf in https://github.com/eclipse-tractusx/tractusx-sdk/pull/197
- init: geometry aspect validator extension and reorganize examples directory by @HannesKrug in https://github.com/eclipse-tractusx/tractusx-sdk/pull/184

### Fixed

- hotfix: fix dependency download URLs in workflow to use eclipse repository by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/198

## [0.7.1] - R26.03

### Fixed

- hotfix/0.7.1: fixed policy parsing issues in `saturn`, enhanced error handling and (breaking) migrated `notifications api` to `industry` module before release. by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/194

## [0.7.0]

### Added

- feat/tck-docs: improved documentation of TCK in official website & improve stability of docs by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/189
- Complete Core Concepts and API References sections documentation (Industry Library and Extension Library) by @flarrinaga in https://github.com/eclipse-tractusx/tractusx-sdk/pull/185
- Feat/saturn-changes: dsp 2025-1 support, new saturn policies support and v0.11.X EDC support + added TCK by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/170
- feat: implement notification api services in sdk by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/183
- docs: changelog 0.6.2-rc1 by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/187
* Bugfix/0.7.0-rc3: Fixed important bugs when retrieveing catalogs by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/192
* feat: applied bugfix to sdk by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/191

### Changed

- build(deps): bump filelock from 3.18.0 to 3.20.1 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/177
- build(deps): bump urllib3 from 2.5.0 to 2.6.3 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/178
- build(deps): bump filelock from 3.20.1 to 3.20.3 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/179
- build(deps): bump pyasn1 from 0.6.1 to 0.6.2 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/180
- build(deps): bump python-multipart from 0.0.20 to 0.0.22 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/181
- build(deps): bump cryptography from 44.0.2 to 46.0.5 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/186

## [0.6.1] - R25.12

### Fixed

- feat: bumped version and prepared dependencies for eclipse tractus-x R25.12 release

## [0.6.0]

### Added

- docs: Introduce MkDocs for structured documentation by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/160
- docs: Fill the missing documentation by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/161
- chore(deps-dev): bump setuptools from 75.9.1 to 78.1.1 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/104
- feat: Trivy filesystem scan workflow by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/163
- chore(deps): bump requests from 2.32.3 to 2.32.4 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/116
- chore(deps): bump urllib3 from 2.3.0 to 2.5.0 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/118
- chore(deps): bump fastapi from 0.115.0 to 0.117 and starlette from 0.46.1 to 0.48.0 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/130
- Changes in the documentation files. Imply a new structure for the doc… by @flarrinaga in https://github.com/eclipse-tractusx/tractusx-sdk/pull/164
- build(deps): bump starlette from 0.48.0 to 0.49.1 by @dependabot[bot] in https://github.com/eclipse-tractusx/tractusx-sdk/pull/166
- feat: add GitHub Actions workflow for unit testing and coverage reporting by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/168
- fix: amend README by @yuri1969 in https://github.com/eclipse-tractusx/tractusx-sdk/pull/165


## [0.5.0] - 25.09

### Added

- feat: Adapt changes to 'saturn' release by @mgarciaLKS in https://github.com/eclipse-tractusx/tractusx-sdk/pull/146
- feat: added new Saturn apis and 2025-01 dsp protocol specifications by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/158
- feat: prepared final version of the ichub 0.5.0 and documentation by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/156

## [0.4.2] - 25.06

### Fixed

- fix: update parameters for POST request in BaseConnectorConsumerService to include json and body options by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/149
- fix: refactor get_catalogs_by_dct_type and get_catalogs_with_filter to use filter_expression by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/148
- fix: change logger level from info to debug for transfer_id cache logging by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/151

## [0.4.1]

### Fixed

-fix: bug on do_post resolved by `do_post_with_session` by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/142
  
## [0.4.0]

### Fixed

- fix: fixed configuration key propagation error & enhanced logging in discovery services by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/141

## [0.3.8]

### Fixed

- bugfix: add configurable prefix and resolved protected keys [`id` & `type`] issue by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/140

## [0.3.7]

### Added/Fixed

- feat: added documentation for the `SammSchemaContextTranslator` and fixed bug regarding the `allOf` property which was not being mapped by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/139
- fix: fixed the unit tests by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/138

## [0.3.6]

### Added

- hotfix/schema-ld: context fix enabled for flat contexts adding `@id` property by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/137

## [0.3.5]

### Added

- feat: enhance schema context with `x-samm-aspect-model-urn` and metadata handling by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/136

## [0.3.4]

### Added

- Added SammSchemaContextTranslator for converting SAMM schemas to JSON-LD contexts for verifiable credentials by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/134
- chore: eliminated trivy and docker files by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/135

## [0.3.3] - 2025-07-29

### Added

- Enhanced submodel validation to check submodel JSON against semantic model schema by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/133

## [0.3.2] - 2025-07-22

### Fixed

- Fixed a bug in the memory connection manager and added missing logger support by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/131

## [0.3.1] - 2025-07-18 - not released, included in v0.3.2

### Added

- feat: enhance connection management with Postgres support + memory Postgres connection caching by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/129

## [0.3.0] - 2025-07-16

- refactor(http-tools): update HttpTools methods to  avoid overriding by @samuelroywork in https://github.com/eclipse-tractusx/tractusx-sdk/pull/67
- feat: added dependencies: Fixed conflicts in dependencies + session management by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/124
- feat: implement AuthManagerInterface and update authentication handling in managers by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/122
- feat: Simplify usage of SDK with better models + methods by @CDiezRodriguez in https://github.com/eclipse-tractusx/tractusx-sdk/pull/123

## [0.2.0] - 2025-07-14

### Added

- feat: adjust dataspace version names to match major release names by @MDSBarbosa in https://github.com/eclipse-tractusx/tractusx-sdk/pull/120
- feat: added discovery finder, edc discovery and bpn discovery services by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/121

### Breaking Changes

- `EDCService` renamed to `ConnectorService`
- `version` parameter renamed to `dataspace_version` the content is not anymore `v0_9_0` but is `jupiter` if there is any breaking change in `saturn` something else will be used.

## [0.1.0] - 2025-07-03 - not released, included in v0.2.0

### Added

- feat/consumption: cleaned methods + added data consumption capabilities by @matbmoser in https://github.com/eclipse-tractusx/tractusx-sdk/pull/108

## [0.0.7] - 2025-05-27

### Added

- Added documentation with the usage of the SDK modules (dataspace, industry, extensions) [#105](https://github.com/eclipse-tractusx/tractusx-sdk/pull/105)

## [0.0.6] - 2025-05-13

### Fixed

- Fixed bug related to the response type which always needed to be parsed [#99](https://github.com/eclipse-tractusx/tractusx-sdk/issues/99)
  - PR [#102](https://github.com/eclipse-tractusx/tractusx-sdk/pull/102)


## [0.0.5] - 2025-05-07

### Fixed

- Improve dependency flexibility and configure dev/test groups [#79](https://github.com/eclipse-tractusx/tractusx-sdk/pull/79)

### Security

- Bump h11 from 0.14.0 to 0.16.0 [#98](https://github.com/eclipse-tractusx/tractusx-sdk/pull/98)

## [0.0.4] - 2025-05-06

### Added

- Documentation for TX-SDK Service [#94](https://github.com/eclipse-tractusx/tractusx-sdk/pull/94)

- Added tractus-x edc service sdk [#92](https://github.com/eclipse-tractusx/tractusx-sdk/pull/92)

### Changed

- Updated dependencies [#93](https://github.com/eclipse-tractusx/tractusx-sdk/pull/93)

## [0.0.3] - 2025-04-29

### Added

- Dataspace Connector 0.9.0 Adapters [#77](https://github.com/eclipse-tractusx/tractusx-sdk/pull/77)
- Dataspace Connector 0.9.0 Models [#82](https://github.com/eclipse-tractusx/tractusx-sdk/pull/82)
- Dataspace Connector 0.9.0 Controllers [#84](https://github.com/eclipse-tractusx/tractusx-sdk/pull/84)

- Submodel Server Adapter and FileSystemAdapter [#88](https://github.com/eclipse-tractusx/tractusx-sdk/pull/88)

### Changed

- Updated the pull request template [#81](https://github.com/eclipse-tractusx/tractusx-sdk/pull/81)

### Fixed

- Corrected incorrect test imports [#86](https://github.com/eclipse-tractusx/tractusx-sdk/pull/86)
- Add a default `sortField` value to the `QuerySpec` Model [#90](https://github.com/eclipse-tractusx/tractusx-sdk/pull/90)

### Removed

- Removed unnecessary imports [#85](https://github.com/eclipse-tractusx/tractusx-sdk/pull/85)

## [0.0.2] - 2025-04-07

### Added

- Added repository TRGs and Security Scans TRGs [#1](https://github.com/eclipse-tractusx/tractusx-sdk/issues/1)
- Added the workflow to publish the libraries to PyPi [#45](https://github.com/eclipse-tractusx/tractusx-sdk/pull/45)
- Added test for previously untested methods [#24](https://github.com/eclipse-tractusx/tractusx-sdk/pull/24), [#29](https://github.com/eclipse-tractusx/industry-core-hub/issues/29)
- Added the missing dependencies [#26](https://github.com/eclipse-tractusx/tractusx-sdk/pull/26)
- Added the health check router for Dataspace and Industry [#57](https://github.com/eclipse-tractusx/tractusx-sdk/issues/57)
- Added the DTR CRUD [#41](https://github.com/eclipse-tractusx/tractusx-sdk/pull/41), [#56](https://github.com/eclipse-tractusx/tractusx-sdk/pull/56), [#65](https://github.com/eclipse-tractusx/tractusx-sdk/pull/65), [#74](https://github.com/eclipse-tractusx/tractusx-sdk/pull/74)
- Added put and delete methods to `http_tools` [#48](https://github.com/eclipse-tractusx/tractusx-sdk/pull/48)

### Changed

- Updated project structure to follow Poetry conventions [#44](https://github.com/eclipse-tractusx/tractusx-sdk/pull/44)

### Fixed

- Fixed Dockerfile image generation issues [#53](https://github.com/eclipse-tractusx/tractusx-sdk/issues/53)

## [0.0.1] - 2025-01-24

### Added

- Added initial commit with open source requirements
- Added initial architecture documentation
