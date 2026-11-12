#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS NEXT
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

from unittest.mock import MagicMock

import pytest

from tractusx_sdk.extensions.notification_api.services import NotificationConsumerService


@pytest.mark.parametrize(
    ("max_retries", "retry_timeout"),
    [(3, 42), (6, 10), (3, None), (None, 10)],
)
def test_negotiate_notification_access_warns_and_uses_supported_connector_arguments(
    max_retries, retry_timeout
):
    connector = MagicMock()
    filter_expression = {
        "operandLeft": "dct:type",
        "operator": "=",
        "operandRight": "event-api",
    }
    connector.get_filter_expression.return_value = filter_expression
    connector.negotiate_and_transfer.return_value = {"transferProcessId": "transfer-123"}
    service = NotificationConsumerService(connector_consumer=connector)

    with pytest.warns(DeprecationWarning, match="max_retries"):
        service.negotiate_notification_access(
            provider_bpn="BPNL000000000002",
            provider_dsp_url="https://provider.com/dsp",
            policies=[],
            max_retries=max_retries,
            retry_timeout=retry_timeout,
            dct_type="event-api",
        )

    connector.negotiate_and_transfer.assert_called_once_with(
        counter_party_id="BPNL000000000002",
        counter_party_address="https://provider.com/dsp",
        filter_expression=[filter_expression],
        policies=[],
    )