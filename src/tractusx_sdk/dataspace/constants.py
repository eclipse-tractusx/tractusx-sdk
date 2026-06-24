#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 LKS NEXT
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

## Legacy (EDC v0.8 / DSP HTTP 2024) — keys carry their namespace prefix.
DSP_DATASET_KEY:str="dcat:dataset"
DSP_POLICY_KEY:str="odrl:hasPolicy"

## DSP 2025-1 (Saturn / EDC v0.11+) — @vocab expands everything; no prefix needed.
DSP2025_DATASET_KEY:str="dataset"
DSP2025_POLICY_KEY:str="hasPolicy"

V3:str="/v3"
V4_ALPHA:str="/v4alpha"

class JSONLDKeys:
    AT_ID = "@id"
    AT_TYPE = "@type"
    AT_CONTEXT = "@context"

## ── Legacy keys (dcat:/odrl: prefixed) ──────────────────────────────────────
class DCATKeys:
    """Prefixed DCAT keys used by legacy EDC (v0.8 / DSP HTTP 2024) responses."""
    DATASET = "dcat:dataset"

class ODRLTypes:
    PERMISSION: str = "permission"
    PROHIBITION: str = "prohibition"
    OBLIGATION: str = "obligation"
    OPERAND_LEFT: str = "operandLeft"
    OPERATOR: str = "operator"
    OPERAND_RIGHT: str = "operandRight"
    EQUALS: str = "="

class ODRLKeys:
    """Prefixed ODRL keys used by legacy EDC (v0.8 / DSP HTTP 2024) responses."""
    POLICY = "odrl:hasPolicy"
    LEFT_OPERAND = "odrl:leftOperand"
    OPERATOR = f"odrl:{ODRLTypes.OPERATOR}"
    RIGHT_OPERAND = "odrl:rightOperand"
    ODRL_AND = "odrl:and"
    ODRL_OR = "odrl:or"
    PERMISSION: str = f"odrl:{ODRLTypes.PERMISSION}"
    PROHIBITION: str = f"odrl:{ODRLTypes.PROHIBITION}"
    OBLIGATION: str = f"odrl:{ODRLTypes.OBLIGATION}"

## ── DSP 2025-1 keys (unprefixed) ─────────────────────────────────────────────
class DCATKeysDSP2025:
    """Unprefixed DCAT keys used by Saturn / EDC v0.11+ (DSP 2025-1) responses.

    In DSP 2025-1, ``@context`` sets ``@vocab`` to the EDC namespace so every
    term is expanded automatically — no ``dcat:`` prefix appears in the
    serialised JSON.
    """
    DATASET = "dataset"

class ODRLKeysDSP2025:
    """Unprefixed ODRL keys used by Saturn / EDC v0.11+ (DSP 2025-1) responses.

    In DSP 2025-1, ``@context`` sets ``@vocab`` to the EDC namespace so every
    term is expanded automatically — no ``odrl:`` prefix appears in the
    serialised JSON.
    """
    POLICY = "hasPolicy"
    LEFT_OPERAND = "leftOperand"
    OPERATOR = ODRLTypes.OPERATOR          # "operator" — same both ways
    RIGHT_OPERAND = "rightOperand"
    ODRL_AND = "and"
    ODRL_OR = "or"
    PERMISSION: str = ODRLTypes.PERMISSION   # "permission"
    PROHIBITION: str = ODRLTypes.PROHIBITION  # "prohibition"
    OBLIGATION: str = ODRLTypes.OBLIGATION   # "obligation"