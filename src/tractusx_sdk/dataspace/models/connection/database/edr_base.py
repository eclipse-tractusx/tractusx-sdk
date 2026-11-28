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

from typing import Any
from sqlmodel import SQLModel, Field
from sqlalchemy import JSON, String
from sqlmodel import Column

class EDRBase(SQLModel):
    transfer_id: str = Field(primary_key=True)
    counter_party_id: str
    counter_party_address: str
    query_checksum: str
    policy_checksum: str
    edr_data: dict[str, Any] = Field(sa_column=Column(JSON))
    edr_hash: str = Field(default=None, sa_column=Column(String))