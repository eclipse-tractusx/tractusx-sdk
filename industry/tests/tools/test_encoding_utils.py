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

from industry.tools.encoding_utils import encode_as_base64_url_safe, decode_base64_url_safe


class TestEncodingUtils:
    def test_encode_simple_string(self):
        """Test encoding a simple string."""
        input_str = "test"
        expected = "dGVzdA"
        assert encode_as_base64_url_safe(input_str) == expected

    def test_encode_with_special_chars(self):
        """Test encoding a string with special characters."""
        input_str = "test+/="
        expected = "dGVzdCsvPQ"
        assert encode_as_base64_url_safe(input_str) == expected

    def test_encode_with_unicode(self):
        """Test encoding a string with Unicode characters."""
        input_str = "测试"  # Chinese for "test"
        expected = "5rWL6K-V"
        assert encode_as_base64_url_safe(input_str) == expected

    def test_decode_simple_string(self):
        """Test decoding a simple encoded string."""
        encoded_str = "dGVzdA"
        expected = "test"
        assert decode_base64_url_safe(encoded_str) == expected

    def test_decode_with_special_chars(self):
        """Test decoding a string that contained special characters."""
        encoded_str = "dGVzdCsvPQ"
        expected = "test+/="
        assert decode_base64_url_safe(encoded_str) == expected

    def test_decode_with_unicode(self):
        """Test decoding a string with Unicode characters."""
        encoded_str = "5rWL6K-V"
        expected = "测试"  # Chinese for "test"
        assert decode_base64_url_safe(encoded_str) == expected

    def test_encode_empty_string(self):
        """Test encoding an empty string."""
        assert encode_as_base64_url_safe("") == ""

    def test_decode_empty_string(self):
        """Test decoding an empty string."""
        assert decode_base64_url_safe("") == ""

    def test_padding_handling(self):
        """Test that decoding works with different padding requirements."""
        # These strings require different amounts of padding
        test_cases = [
            ("YQ", "a"),           # Requires 2 padding chars
            ("YWI", "ab"),         # Requires 1 padding char
            ("YWJj", "abc"),       # Requires no padding
        ]
        
        for encoded, expected in test_cases:
            assert decode_base64_url_safe(encoded) == expected
