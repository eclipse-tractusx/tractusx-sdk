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

import hashlib
import json

from ..constants import DCATKeys, ODRLKeys, JSONLDKeys

def extract_odrl_policy(offer: dict) -> dict:
    return offer.get(DCATKeys.DATASET, {}).get(ODRLKeys.POLICY, {})

def hash_constraints(constraints):
    canon = extract_constraints(constraints)
    canon_str = json.dumps(canon, separators=(",", ":"))
    return hashlib.sha256(canon_str.encode('utf-8')).hexdigest()

def extract_constraints(constraints):
    if isinstance(constraints, dict):
        constraints = constraints.get(ODRLKeys.ODRL_AND) or constraints.get(ODRLKeys.ODRL_OR) or []

    if not isinstance(constraints, list):
        return []

    return sorted([
        (
            c[ODRLKeys.LEFT_OPERAND][JSONLDKeys.AT_ID],
            c[ODRLKeys.OPERATOR][JSONLDKeys.AT_ID],
            c[ODRLKeys.RIGHT_OPERAND]
        )
        for c in constraints
    ])