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


import logging

from tractusx_sdk._logging_fields import log_extra
from tractusx_sdk.dataspace.controllers.controller import Controller

logger = logging.getLogger(__name__)


def controller_method(func):
    """
    This function can be used as a decorator for controller mixins, in order to ensure that
    they are used only alongside a controller class (that have an adapter and an endpoint URL)

    :param func: The function to which the decorator will be applied
    :return: None, if the required attributes do not exist, otherwise the applied function's result
    """

    def inner_func(*args, **kwargs):
        self = args[0]

        class_name = type(self).__name__
        func_name = func.__name__

        if not isinstance(self, Controller):
            logger.error(
                "%s cannot use %s: it does not inherit from Controller", class_name, func_name,
                extra=log_extra(operation=f"{class_name}.{func_name}"),
            )
            raise ValueError(
                f"Please ensure that {class_name} inherits from Controller in order to use {func_name}."
            )

        if not hasattr(self, "endpoint_url"):
            logger.error(
                "%s cannot use %s: it does not define an endpoint_url", class_name, func_name,
                extra=log_extra(operation=f"{class_name}.{func_name}"),
            )
            raise ValueError(
                f"Please ensure that {class_name} defines an 'endpoint_url' attribute in order to use {func_name}."
            )

        logger.debug(
            "Controller operation %s.%s", class_name, func_name,
            extra=log_extra(operation=f"{class_name}.{func_name}"),
        )
        ret_val = func(*args, **kwargs)
        return ret_val

    return inner_func
