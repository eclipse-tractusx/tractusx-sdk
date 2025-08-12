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

class JSONLDKeys:
    AT_ID = "@id"
    AT_TYPE = "@type"
    AT_CONTEXT = "@context"
class DCATKeys:
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
    POLICY = "odrl:hasPolicy"
    LEFT_OPERAND = "odrl:leftOperand"
    OPERATOR = f"odrl:{ODRLTypes.OPERATOR}"
    RIGHT_OPERAND = "odrl:rightOperand"
    ODRL_AND = "odrl:and"
    ODRL_OR = "odrl:or"
    PERMISSION: str = f"odrl:{ODRLTypes.PERMISSION}"
    PROHIBITION: str = f"odrl:{ODRLTypes.PROHIBITION}"
    OBLIGATION: str = f"odrl:{ODRLTypes.OBLIGATION}"
