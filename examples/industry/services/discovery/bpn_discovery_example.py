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
## Code created partially using a LLM (Claude Sonnet 4) and reviewed by a human committer

"""
Discovery Services Quick Start Example

A minimal example showing how to quickly get started with discovery services.
Perfect for testing and initial setup.

CONFIGURATION REQUIRED:
Before running this example, you need to replace the placeholder values with your actual configuration:
- YOUR_REALM: Your OAuth2 realm (e.g., "CX-Central")
- YOUR_CLIENT_ID: Your OAuth2 client ID
- YOUR_CLIENT_SECRET: Your OAuth2 client secret  
- YOUR_AUTH_URL: Your authentication URL (e.g., "https://your-idp.example.com/auth/")
- YOUR_DISCOVERY_FINDER_URL: Your discovery finder service URL
- YOUR_MANUFACTURER_PART_ID: A valid manufacturer part ID for testing
"""

import logging
import sys
import os
import time

# Add the src directory to the Python path for imports (going up two levels from examples/discovery/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tractusx_sdk.dataspace.managers import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery.discovery_finder_service import DiscoveryFinderService
from tractusx_sdk.industry.services.discovery.bpn_discovery_service import BpnDiscoveryService


def quick_start():
    """
    Quick start example for discovery services.
    """
    print("Quick Start: Tractus-X Discovery Services")
    print("=" * 45)
    
    # 1. Set up basic logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    logger = logging.getLogger('discovery_quickstart')
    
    # 2. Set up OAuth2 authentication
    # Replace these placeholder values with your actual configuration
    # You can also use environment variables for security:
    # os.getenv('OAUTH_REALM', 'YOUR_REALM')
    oauth_manager = OAuth2Manager(
        realm="YOUR_REALM",  # e.g., "CX-Central"
        clientid="YOUR_CLIENT_ID",  # Your OAuth2 client ID
        clientsecret="YOUR_CLIENT_SECRET",  # Your OAuth2 client secret
        auth_url="YOUR_AUTH_URL"  # e.g., "https://your-idp.example.com/auth/"
    )
    discovery_finder = DiscoveryFinderService(
        oauth=oauth_manager,
        url="YOUR_DISCOVERY_FINDER_URL",  # e.g., "https://your-discovery-finder.example.com/api/v1.0/administration/connectors/discovery/search"
    )
    
    # For real usage: oauth_manager.connect()
    # Note: You need to call oauth_manager.connect() before making actual API calls

    # 3. Initialize services with enhanced logging
    logger.info("Initializing discovery services...")
    
    bpn_service = BpnDiscoveryService(
        oauth=oauth_manager,
        discovery_finder_service=discovery_finder,
        base_path="/api/v1.0/administration/connectors/bpnDiscovery",
        debug=True,    # Enable detailed cache logging
        logger=logger    # Provide logger for enhanced output
    )

    # Measure execution time for search_bpns
    start_search = time.perf_counter()
    response = bpn_service.search_bpns(
        keys=["YOUR_MANUFACTURER_PART_ID"], identifier_type="manufacturerPartId"  # Replace with your actual part ID
    )
    end_search = time.perf_counter()
    search_duration = end_search - start_search

    print("Raw Service Response:")
    print(response)
    print(f"search_bpns took {search_duration:.6f} seconds")

    # Measure execution time for find_bpns
    start_find = time.perf_counter()
    bpns = bpn_service.find_bpns(
        keys=["YOUR_MANUFACTURER_PART_ID"], identifier_type="manufacturerPartId"  # Replace with your actual part ID
    )
    end_find = time.perf_counter()
    find_duration = end_find - start_find

    print("BPNs Found:")
    print(bpns)
    print(f"find_bpns took {find_duration:.6f} seconds")

    # Compare the durations
    if search_duration < find_duration:
        print(f"search_bpns is faster by {find_duration - search_duration:.6f} seconds")
    elif find_duration < search_duration:
        print(f"find_bpns is faster by {search_duration - find_duration:.6f} seconds")
    else:
        print("Both functions took the same amount of time")
    

if __name__ == "__main__":
    quick_start()
