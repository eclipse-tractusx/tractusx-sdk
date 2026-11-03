#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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
import datetime
import logging
from abc import ABC, abstractmethod

from tractusx_sdk._logging_fields import log_extra, safe_url
from tractusx_sdk.dataspace.managers.oauth2_manager import OAuth2Manager
from tractusx_sdk.dataspace.services.discovery import DiscoveryFinderService
from tractusx_sdk.dataspace.services.service import BaseService

logger = logging.getLogger(__name__)


class BaseDiscoveryService(BaseService, ABC):
    """
    Base class for discovery services with common caching and logging functionality.
    
    This abstract base class provides:
    - Time-based caching with configurable timeouts
    - Enhanced logging with cache status and validity information
    - Safety mechanisms preserving cached URLs during failures
    - Cache management methods (flush, invalidate, status)
    """

    def __init__(self, oauth: OAuth2Manager, discovery_finder_service: DiscoveryFinderService, cache_timeout_seconds: int = 60 * 60 * 12,
                 trace: bool = False):
        """
        Initialize the base discovery service.
        
        Args:
            oauth: OAuth2 manager for authentication.
            discovery_finder_service: DiscoveryFinderService instance for finding discovery URLs.
            discovery_finder_url (str): URL for the discovery finder service.
            cache_timeout_seconds (int): Cache timeout in seconds (default: 12 hours).
            trace (bool): Enable the tracing of the requests/responses (default: False).
                The trace is shared with the discovery finder service, so that the
                discovery lookups are part of it as well.
        """
        self.oauth = oauth
        self.discovery_finder_service = discovery_finder_service
        self.cache_timeout_seconds = cache_timeout_seconds
        self.discovery_cache = {}
        logger.debug("[%s] Initialised with a cache timeout of %s seconds", self.get_service_name(), cache_timeout_seconds)

        # Configured last: the trace is shared with the discovery finder service
        self._init_tracing(trace=trace)

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
                logger.debug(
                    "[%s] Discovery URL for key '%s' is %s, asking the discovery finder", self.get_service_name(), discovery_key,
                    "expired" if entry else "not cached yet", extra=log_extra(operation="discovery.refresh"))
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
                    if logger.isEnabledFor(logging.INFO):
                        valid_until = datetime.datetime.fromtimestamp(current_time + self.cache_timeout_seconds)
                        service_name = self.get_service_name()
                        logger.info("[%s] Updated cache with new discovery URL for key '%s': %s", service_name, discovery_key, safe_url(url),
                                    extra=log_extra(url=url, operation="discovery.refresh"))
                        logger.info("[%s] Cache status: %d URL(s) cached, valid until %s", service_name, len(self.discovery_cache), valid_until.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    logger.warning("[%s] The discovery finder returned no URL for key '%s'", self.get_service_name(), discovery_key,
                                   extra=log_extra(operation="discovery.refresh"))
                    
            except Exception as e:
                # If we have a cached entry, preserve it and continue using it
                if entry:
                    # Log the error but continue with cached URL
                    logger.warning("[%s] Failed to refresh discovery URL, using cached version. Error: %s", self.get_service_name(), e,
                                   extra=log_extra(url=entry["url"], operation="discovery.refresh"))
                    return entry["url"]
                else:
                    # No cached entry available, re-raise the exception
                    logger.error("[%s] Failed to get the discovery URL for key '%s' and there is no cached one to fall back to: %s",
                                 self.get_service_name(), discovery_key, e, extra=log_extra(operation="discovery.refresh"))
                    raise
        else:
            # Using valid cached URL
            if entry and logger.isEnabledFor(logging.DEBUG):
                valid_until = datetime.datetime.fromtimestamp(entry["timestamp"] + self.cache_timeout_seconds)
                service_name = self.get_service_name()
                logger.debug("[%s] Using cached discovery URL for key '%s': %s", service_name, discovery_key, safe_url(entry['url']),
                             extra=log_extra(url=entry['url'], operation="discovery.cache_hit"))
                logger.debug("[%s] Cache status: %d URL(s) cached, this entry valid until %s", service_name, len(self.discovery_cache), valid_until.strftime('%Y-%m-%d %H:%M:%S'))
            
        return self.discovery_cache[discovery_key]["url"]

    def flush_cache(self) -> int:
        """
        Flushes all cached discovery URLs.
        
        Returns:
            int: Number of cache entries that were removed.
        """
        cache_count = len(self.discovery_cache)
        self.discovery_cache.clear()
        
        logger.info("[%s] Cache flushed: %d entries removed", self.get_service_name(), cache_count)
        
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
            logger.info("[%s] Cache entry invalidated for key '%s'", self.get_service_name(), discovery_key)
        else:
            logger.debug("[%s] No cache entry found for key '%s' to invalidate", self.get_service_name(), discovery_key)
        
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
