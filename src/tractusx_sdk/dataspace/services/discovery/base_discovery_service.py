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

import time
import logging
from typing import Optional
from abc import ABC, abstractmethod

from tractusx_sdk.dataspace.managers.oauth2_manager import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService


class BaseDiscoveryService(ABC):
    """
    Base class for discovery services with common caching and logging functionality.
    
    This abstract base class provides:
    - Time-based caching with configurable timeouts
    - Enhanced logging with cache status and validity information
    - Safety mechanisms preserving cached URLs during failures
    - Cache management methods (flush, invalidate, status)
    """

    def __init__(self, oauth: OAuth2Manager, discovery_finder_service: DiscoveryFinderService, cache_timeout_seconds: int = 60 * 60 * 12,
                 debug: bool = False, logger: Optional[logging.Logger] = None):
        """
        Initialize the base discovery service.
        
        Args:
            oauth: OAuth2 manager for authentication.
            discovery_finder_service: DiscoveryFinderService instance for finding discovery URLs.
            discovery_finder_url (str): URL for the discovery finder service.
            cache_timeout_seconds (int): Cache timeout in seconds (default: 12 hours).
            debug (bool): Enable debug logging with request/response bodies (default: False).
            logger (Optional[logging.Logger]): Logger instance for logging (default: None).
        """
        self.oauth = oauth
        self.discovery_finder_service = discovery_finder_service
        self.cache_timeout_seconds = cache_timeout_seconds
        self.debug = debug
        self.logger = logger
        self.discovery_cache = {}

    @abstractmethod
    def get_service_name(self) -> str:
        """Returns the service name for logging purposes."""
        pass

    @abstractmethod
    def get_discovery_url(self, discovery_finder_service,  discovery_key: str) -> str:
        """
        Fetches the discovery URL for the given key.
        
        Args:
            discovery_finder_service: DiscoveryFinderService instance for finding discovery URLs.
            discovery_key (str): The key used to identify the discovery type.
            
        Returns:
            str: The discovery URL for the given key.
            
        Raises:
            Exception: If no discovery endpoint is found for the given key.
        """
        pass

    def _get_or_update_discovery_url(self, discovery_key: str) -> str:
        """
        Retrieves a cached discovery URL or updates the cache if expired.
        
        Safety mechanism: If the refresh attempt fails, the cached URL is preserved
        to maintain service availability during temporary connectivity issues.

        Args:
            discovery_key (str): The identifier key for the discovery type.

        Returns:
            str: A valid discovery URL.
            
        Raises:
            Exception: If no cached URL exists and the initial discovery fails.
        """
        current_time = time.time()
        entry: dict = self.discovery_cache.get(discovery_key)
        
        # Check if the entry exists and if it is still valid
        if (
            not entry or
            (current_time - entry.get("timestamp", 0)) > self.cache_timeout_seconds
        ):
            try:
                url = self.get_discovery_url(
                    discovery_finder_service=self.discovery_finder_service,
                    discovery_key=discovery_key
                )
                if url:
                    # Update cache only if successful
                    self.discovery_cache[discovery_key] = {
                        "url": url,
                        "timestamp": current_time
                    }
                    if self.debug and self.logger:
                        import datetime
                        cache_count = len(self.discovery_cache)
                        valid_until = datetime.datetime.fromtimestamp(current_time + self.cache_timeout_seconds)
                        service_name = self.get_service_name()
                        self.logger.info(f"[{service_name}] Updated cache with new discovery URL for key '{discovery_key}': {url}")
                        self.logger.info(f"[{service_name}] Cache status: {cache_count} URL(s) cached, valid until {valid_until.strftime('%Y-%m-%d %H:%M:%S')}")
                    
            except Exception as e:
                # If we have a cached entry, preserve it and continue using it
                if entry:
                    # Log the error but continue with cached URL
                    if self.debug and self.logger:
                        service_name = self.get_service_name()
                        self.logger.warning(f"[{service_name}] Failed to refresh discovery URL, using cached version. Error: {str(e)}")
                    return entry["url"]
                else:
                    # No cached entry available, re-raise the exception
                    raise e
        else:
            # Using valid cached URL
            if self.debug and self.logger and entry:
                import datetime
                cache_count = len(self.discovery_cache)
                valid_until = datetime.datetime.fromtimestamp(entry["timestamp"] + self.cache_timeout_seconds)
                service_name = self.get_service_name()
                self.logger.debug(f"[{service_name}] Using cached discovery URL for key '{discovery_key}': {entry['url']}")
                self.logger.debug(f"[{service_name}] Cache status: {cache_count} URL(s) cached, this entry valid until {valid_until.strftime('%Y-%m-%d %H:%M:%S')}")
            
        return self.discovery_cache[discovery_key]["url"]

    def flush_cache(self) -> int:
        """
        Flushes all cached discovery URLs.
        
        Returns:
            int: Number of cache entries that were removed.
        """
        cache_count = len(self.discovery_cache)
        self.discovery_cache.clear()
        
        if self.debug and self.logger:
            service_name = self.get_service_name()
            self.logger.info(f"[{service_name}] Cache flushed: {cache_count} entries removed")
        
        return cache_count

    def invalidate_cache_entry(self, discovery_key: str) -> bool:
        """
        Invalidates a specific cache entry for a discovery key.
        
        Args:
            discovery_key (str): The discovery key to invalidate.
        
        Returns:
            bool: True if the entry was found and removed, False if it didn't exist.
        """
        entry_existed = discovery_key in self.discovery_cache
        
        if entry_existed:
            del self.discovery_cache[discovery_key]
            if self.debug and self.logger:
                service_name = self.get_service_name()
                self.logger.info(f"[{service_name}] Cache entry invalidated for key '{discovery_key}'")
        else:
            if self.debug and self.logger:
                service_name = self.get_service_name()
                self.logger.debug(f"[{service_name}] No cache entry found for key '{discovery_key}' to invalidate")
        
        return entry_existed

    def get_cache_status(self) -> dict:
        """
        Returns detailed information about the current cache state.
        
        Returns:
            dict: Cache status information including:
                - total_entries: Number of cached entries
                - entries: List of cache entry details with keys, URLs, and expiration times
        """
        import datetime
        current_time = time.time()
        
        entries = []
        for key, entry in self.discovery_cache.items():
            expires_at = entry["timestamp"] + self.cache_timeout_seconds
            is_expired = current_time > expires_at
            
            entries.append({
                "key": key,
                "url": entry["url"],
                "cached_at": datetime.datetime.fromtimestamp(entry["timestamp"]).strftime('%Y-%m-%d %H:%M:%S'),
                "expires_at": datetime.datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S'),
                "is_expired": is_expired,
                "age_seconds": current_time - entry["timestamp"]
            })
        
        return {
            "total_entries": len(self.discovery_cache),
            "cache_timeout_seconds": self.cache_timeout_seconds,
            "entries": entries
        }
