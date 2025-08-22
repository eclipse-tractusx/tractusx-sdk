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

"""
Governance Managers for policy validation and management.

This module provides different implementations for managing and validating policies:

- BaseGovernanceManager: Abstract base class defining the interface
- InMemoryGovernanceManager: Fast in-memory storage for policies
- DatabaseGovernanceManager: Persistent database storage using PostgreSQL/SQLite
- FilesystemGovernanceManager: File-based storage using JSON files
- HybridGovernanceManager: Combination of in-memory and database storage

Example usage:

    # In-memory governance for fast validation
    memory_gov = InMemoryGovernanceManager()
    memory_gov.add_policy(policy_json)
    is_valid = memory_gov.is_policy_valid(new_policy)
    
    # Database governance for persistence
    db_gov = DatabaseGovernanceManager(db_session)
    db_gov.add_policy(policy_json)
    
    # Hybrid governance for best of both worlds
    hybrid_gov = HybridGovernanceManager(db_session)
    valid_assets = hybrid_gov.select_valid_assets_and_policies(catalog)
"""

from .base_governance_manager import BaseGovernanceManager
from .memory import MemoryGovernanceManager
from .database import PostgresGovernanceManager, PostgresMemoryGovernanceManager
from .file_system import FileSystemGovernanceManager

__all__ = [
    "BaseGovernanceManager",
    "MemoryGovernanceManager", 
    "PostgresGovernanceManager",
    "PostgresMemoryGovernanceManager",
    "FileSystemGovernanceManager"
]
