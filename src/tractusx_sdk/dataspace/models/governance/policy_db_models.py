#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
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

from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from ...constants import ODRLTypes

RULE_ID_KEY:str = "rule.id"
POLICY_ID_KEY:str = "policy.id"

class OperatorEnum(str, Enum):
    eq = "eq"
    gt = "gt"
    gteq = "gteq"
    lteq = "lteq"
    hasPart = "hasPart"
    isA = "isA"
    isAllOf = "isAllOf"
    isAnyOf = "isAnyOf"
    isNoneOf = "isNoneOf"
    isPartOf = "isPartOf"
    lt = "lt"
    term_lteq = "term-lteq"
    neq = "neq"


class PolicyType(str, Enum):
    set = "Set"
    offer = "Offer"
    agreement = "Agreement"


class RuleType(str, Enum):
    permission = ODRLTypes.PERMISSION
    prohibition = ODRLTypes.PROHIBITION
    obligation = ODRLTypes.OBLIGATION


class Policy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str  # IRI of the Policy
    profile: Optional[str] = Field(default=None)
    type: PolicyType  # Offer, Agreement

    rules: List["Rule"] = Relationship(back_populates="policy")


class Rule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: RuleType  # Permission, Prohibition, Obligation
    policy_id: int = Field(foreign_key=POLICY_ID_KEY)
    constraint_hash: Optional[str] = Field(index=True)
    action: str  # e.g., odrl:use

    policy: Optional[Policy] = Relationship(back_populates="rules")
    atomic_constraints: List["AtomicConstraint"] = Relationship(back_populates="rule")
    duties: List["Duty"] = Relationship(back_populates="rule")


class AtomicConstraint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: int = Field(foreign_key=RULE_ID_KEY)
    left_operand: str
    operator: OperatorEnum
    right_operand: str

    rule: Optional[Rule] = Relationship(back_populates="atomic_constraints")


class Duty(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: int = Field(foreign_key=RULE_ID_KEY)
    consequence_rule_id: Optional[int] = Field(default=None, foreign_key=RULE_ID_KEY)

    rule: Optional[Rule] = Relationship(back_populates="duties")
