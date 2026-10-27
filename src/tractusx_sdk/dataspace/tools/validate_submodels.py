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
from dataclasses import dataclass, fields
from typing import Any, Optional

from requests import get
import jsonschema

from tractusx_sdk.exceptions import (
    InvalidSemanticIdError,
    SchemaNotFoundError,
    SubmodelValidationError,
)

logger = logging.getLogger(__name__)


class _DictAccess:
    """Read access by key (``result["schema"]``), kept so code written for the former ``dict`` results keeps working."""

    def __getitem__(self, key: str) -> Any:
        if key not in {f.name for f in fields(self)}:
            raise KeyError(key)
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass(frozen=True)
class SchemaLookupResult(_DictAccess):
    """
    The JSON schema found for a semantic id.

    :param schema: The JSON schema document.
    :param link: Where it was retrieved from.
    """

    schema: dict
    link: str = ""
    status: str = "ok"
    message: str = "Submodel validation schema retrieved successfully"


@dataclass(frozen=True)
class ValidationIssue:
    """One violation found while validating a JSON document against a schema."""

    path: str
    message: str
    validator: str
    expected: Any = "N/A"
    invalid_value: Any = None

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "message": self.message,
            "validator": self.validator,
            "expected": self.expected,
            "invalid_value": self.invalid_value,
        }


@dataclass(frozen=True)
class ValidationResult(_DictAccess):
    """
    The outcome of validating a JSON document against a schema.

    :param valid: ``True`` when the document conforms to the schema.
    :param issues: Every violation found; empty when ``valid``.
    """

    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    status: str = "ok"
    message: str = "Congratulations, your JSON file passed the validation test"


## Test Orchestrator of Eclipse Tractus-X SDK Services
## License: Apache License, Version 2.0
## Source: https://github.com/eclipse-tractusx/tractusx-sdk-services/blob/cfd73933ad7871891bee9f117b32643bc9abad40/test-orchestrator/test_orchestrator/utils.py#L176-L217

@staticmethod
def submodel_schema_finder(
        semantic_id,
        link_core: Optional[str] = 'https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/') -> SchemaLookupResult:
    """
    Function to facilitate the validation of the submodel output by retrieving the correct schema
    based on the semantic_id provided by the user

    :raises InvalidSemanticIdError: The semantic id does not follow the expected structure.
    :raises SchemaNotFoundError: The schema could not be retrieved, or is not valid JSON.
        Both are also ``requests.HTTPError``, as before.
    :return: The schema found. It still supports ``result["schema"]``-style access.
    """

    split_string = semantic_id.split(':')

    if len(split_string) < 4:
        raise InvalidSemanticIdError(f"422 Client Error: The semanticID provided does not follow the correct structure. subprotocolBody: {semantic_id}")

    loc_elements = split_string[3].split('#')
    if len(loc_elements) != 2 or not all(loc_elements):
        raise InvalidSemanticIdError(f"422 Client Error: The semanticID provided does not follow the correct structure. subprotocolBody: {semantic_id}")

    schema_link = link_core + split_string[2] + '/' + loc_elements[0] + '/gen/' + loc_elements[1] + '-schema.json'

    # Now we can use the link to pull in the correct schema.
    logger.debug("Retrieving the schema of '%s' from %s", semantic_id, schema_link)
    response = get(schema_link)

    if response.status_code != 200:
        raise SchemaNotFoundError(f"422 Client Error: Failed to obtain the required schema. schema link: {schema_link}")

    try:
        schema = response.json()
    except Exception as e:
        raise SchemaNotFoundError(f"422 Client Error: The schema obtained is not a valid json. schema link: {schema_link}") from e

    return SchemaLookupResult(schema=schema, link=schema_link)

@staticmethod
def json_validator(schema, json_to_validate, validation_type = 'jsonschema', raise_on_error: bool = True) -> ValidationResult:
    """
    Validates a JSON object against a given schema.

    This function uses the specified validation type to check whether a JSON object
    conforms to a given schema. Currently, only 'jsonschema' validation is supported.
    Violations are reported as structured ``ValidationIssue`` records.

    :param schema: The JSON schema object to validate against.
    :param json_to_validate: The JSON object to be validated.
    :param validation_type: The type of validation to perform. Default is 'jsonschema'.
    :param raise_on_error: When ``True`` (default) a violation raises, as before. When ``False``
        the violations are returned in the result instead.
    :raises SubmodelValidationError: Raised if violations are found and ``raise_on_error`` is set.
        Also a ``requests.HTTPError``, as before; the violations are in its ``issues``.
    :return: The result of the validation. It still supports ``result["status"]``-style access.
    """

    issues: list[ValidationIssue] = []

    if validation_type == 'jsonschema':
        validator = jsonschema.Draft7Validator(schema)

        for error in validator.iter_errors(json_to_validate):
            issues.append(ValidationIssue(
                path=".".join(str(p) for p in error.path) if error.path else "root",
                message=error.message,
                validator=error.validator,
                expected=error.schema.get("type", "N/A"),
                invalid_value=error.instance,
            ))

    if issues:
        logger.debug("The JSON document has %d validation issue(s)", len(issues))
        if raise_on_error:
            raise SubmodelValidationError(
                f"422 Client Error: Validation error - {len(issues)} validation errors found: {[i.as_dict() for i in issues]}",
                issues=issues,
            )
        return ValidationResult(
            valid=False,
            issues=tuple(issues),
            status="error",
            message=f"Validation error - {len(issues)} validation errors found",
        )

    return ValidationResult(valid=True)
