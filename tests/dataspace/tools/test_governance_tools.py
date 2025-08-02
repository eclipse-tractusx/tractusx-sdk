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
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

import pytest
import hashlib
import json
from tractusx_sdk.dataspace.tools import governance_tools
from tractusx_sdk.dataspace.constants import DCATKeys, ODRLKeys, JSONLDKeys


def test_extract_odrl_policy_found():
    offer = {
        DCATKeys.DATASET: {
            ODRLKeys.POLICY: {"foo": "bar"}
        }
    }
    assert governance_tools.extract_odrl_policy(offer) == {"foo": "bar"}


def test_extract_odrl_policy_missing():
    offer = {}
    assert governance_tools.extract_odrl_policy(offer) == {}


def test_extract_constraints_list():
    constraints = [
        {
            ODRLKeys.LEFT_OPERAND: {JSONLDKeys.AT_ID: "foo"},
            ODRLKeys.OPERATOR: {JSONLDKeys.AT_ID: "eq"},
            ODRLKeys.RIGHT_OPERAND: 42
        },
        {
            ODRLKeys.LEFT_OPERAND: {JSONLDKeys.AT_ID: "bar"},
            ODRLKeys.OPERATOR: {JSONLDKeys.AT_ID: "neq"},
            ODRLKeys.RIGHT_OPERAND: 7
        }
    ]
    result = governance_tools.extract_constraints(constraints)
    assert result == [
        ('bar', 'neq', 7),
        ('foo', 'eq', 42)
    ]


def test_extract_constraints_dict_and():
    constraints = {
        ODRLKeys.ODRL_AND: [
            {
                ODRLKeys.LEFT_OPERAND: {JSONLDKeys.AT_ID: "foo"},
                ODRLKeys.OPERATOR: {JSONLDKeys.AT_ID: "eq"},
                ODRLKeys.RIGHT_OPERAND: 1
            }
        ]
    }
    result = governance_tools.extract_constraints(constraints)
    assert result == [('foo', 'eq', 1)]


def test_extract_constraints_dict_or():
    constraints = {
        ODRLKeys.ODRL_OR: [
            {
                ODRLKeys.LEFT_OPERAND: {JSONLDKeys.AT_ID: "foo"},
                ODRLKeys.OPERATOR: {JSONLDKeys.AT_ID: "eq"},
                ODRLKeys.RIGHT_OPERAND: 2
            }
        ]
    }
    result = governance_tools.extract_constraints(constraints)
    assert result == [('foo', 'eq', 2)]


def test_extract_constraints_empty():
    assert governance_tools.extract_constraints({}) == []
    assert governance_tools.extract_constraints(None) == []


def test_hash_constraints():
    constraints = [
        {
            ODRLKeys.LEFT_OPERAND: {JSONLDKeys.AT_ID: "foo"},
            ODRLKeys.OPERATOR: {JSONLDKeys.AT_ID: "eq"},
            ODRLKeys.RIGHT_OPERAND: 42
        }
    ]
    canon = [('foo', 'eq', 42)]
    canon_str = json.dumps(canon, separators=(",", ":"))
    expected_hash = hashlib.sha256(canon_str.encode('utf-8')).hexdigest()
    assert governance_tools.hash_constraints(constraints) == expected_hash


def test_extract_constraints_invalid_type():
    assert governance_tools.extract_constraints("notalistordict") == []


def test_extract_constraints_missing_keys():
    constraints = [
        {
            ODRLKeys.LEFT_OPERAND: {JSONLDKeys.AT_ID: "foo"},
            ODRLKeys.OPERATOR: {JSONLDKeys.AT_ID: "eq"},
            # ODRLKeys.RIGHT_OPERAND missing
        }
    ]
    with pytest.raises(KeyError):
        governance_tools.extract_constraints(constraints)