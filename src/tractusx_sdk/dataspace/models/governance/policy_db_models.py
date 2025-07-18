from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


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
    permission = "permission"
    prohibition = "prohibition"
    obligation = "obligation"


class Policy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str  # IRI of the Policy
    profile: Optional[str] = Field(default=None)
    type: PolicyType  # Offer, Agreement

    rules: List["Rule"] = Relationship(back_populates="policy")


class Rule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: RuleType  # Permission, Prohibition, Obligation
    policy_id: int = Field(foreign_key="policy.id")
    constraint_hash: Optional[str] = Field(index=True)
    action: str  # e.g., odrl:use

    policy: Optional[Policy] = Relationship(back_populates="rules")
    atomic_constraints: List["AtomicConstraint"] = Relationship(back_populates="rule")
    duties: List["Duty"] = Relationship(back_populates="rule")


class AtomicConstraint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: int = Field(foreign_key="rule.id")
    left_operand: str
    operator: OperatorEnum
    right_operand: str

    rule: Optional[Rule] = Relationship(back_populates="atomic_constraints")


class Duty(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rule_id: int = Field(foreign_key="rule.id")
    consequence_rule_id: Optional[int] = Field(default=None, foreign_key="rule.id")

    rule: Optional[Rule] = Relationship(back_populates="duties")
