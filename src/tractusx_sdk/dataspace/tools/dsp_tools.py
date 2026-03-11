#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 CGI Deutschland B.V. & Co. KG
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

## Code originally beloging to Industry Flag Service: 
# https://github.com/eclipse-tractusx/tractusx-sdk-services/tree/main/industry-flag-service

import json
import logging

from ..constants import (
    DSP_DATASET_KEY, DSP_POLICY_KEY,
    DSP2025_DATASET_KEY, DSP2025_POLICY_KEY,
)

logger = logging.getLogger(__name__)

## Ordered lookup: try DSP 2025-1 (unprefixed) first, then legacy (prefixed).
_DATASET_KEYS = (DSP2025_DATASET_KEY, DSP_DATASET_KEY)   # "dataset", "dcat:dataset"
_POLICY_KEYS  = (DSP2025_POLICY_KEY,  DSP_POLICY_KEY)    # "hasPolicy", "odrl:hasPolicy"


def _get_datasets(catalog: dict):
    """Return the ``dataset`` value from a catalog, trying DSP 2025-1 and legacy keys."""
    for key in _DATASET_KEYS:
        value = catalog.get(key)
        if value is not None:
            return value
    return None


def _get_policies(dataset: dict):
    """Return the ``hasPolicy`` value from a dataset, trying DSP 2025-1 and legacy keys."""
    for key in _POLICY_KEYS:
        value = dataset.get(key)
        if value is not None:
            return value
    return None


def _normalize_policy_value(value):
    """
    Recursively normalize a policy value for comparison.

    Normalization rules:
    - Value-reference dicts that carry **only** ``@id`` (and optionally
      ``@type``) are collapsed to their ``@id`` string, e.g.
      ``{"@id": "odrl:use"}`` becomes ``"odrl:use"``.
    - On dicts that have other meaningful keys besides ``@id``/``@type``,
      those metadata keys are stripped (they are instance-unique).
    - Single-element lists are unwrapped to their sole element, so
      ``"permission": [{...}]`` compares equal to ``"permission": {...}``.
    - Empty lists are dropped, so ``"prohibition": []`` is equivalent to
      the key not being present at all.
    - Lists of dicts (e.g. ``and`` constraints) are sorted by their
      canonical JSON representation, making order irrelevant.
    """
    if isinstance(value, dict):
        non_meta_keys = {k for k in value if k not in ("@id", "@type")}

        # Value-reference dict: only @id/@type keys → collapse to @id string
        if not non_meta_keys and "@id" in value:
            return value["@id"]

        # Container dict: strip @id/@type, normalize children
        result = {}
        for k, v in value.items():
            if k in ("@id", "@type"):
                continue
            normalized = _normalize_policy_value(v)
            # Drop empty lists (prohibition: [], obligation: [], etc.)
            if isinstance(normalized, list) and len(normalized) == 0:
                continue
            result[k] = normalized
        return result

    if isinstance(value, list):
        # Unwrap single-element lists
        if len(value) == 1:
            return _normalize_policy_value(value[0])
        # Normalize each item, then sort for order-insensitive comparison
        normalized_items = [_normalize_policy_value(item) for item in value]
        try:
            return sorted(normalized_items, key=lambda x: json.dumps(x, sort_keys=True))
        except (TypeError, ValueError):
            return normalized_items

    return value


## Keys used to detect an ODRL constraint dict (both Saturn and Jupiter).
_CONSTRAINT_LEFT_KEYS  = ("leftOperand", "odrl:leftOperand")
_CONSTRAINT_OP_KEYS    = ("operator", "odrl:operator")
_CONSTRAINT_RIGHT_KEYS = ("rightOperand", "odrl:rightOperand")

## ODRL rule key names (Saturn / Jupiter) — all get "any match" semantics
## when comparing catalog vs. allowed config.
_ODRL_RULE_KEYS = {
    "permission",  "odrl:permission",
    "obligation",  "odrl:obligation",
    "prohibition", "odrl:prohibition",
}

## Required structural keys in a well-formed policy.
_POLICY_REQUIRED_KEYS = {
    # key-name -> set of alternative key names (Saturn / Jupiter)
    "permission": {"permission", "odrl:permission"},
}
_PERMISSION_REQUIRED_KEYS = {
    "action":     {"action", "odrl:action"},
    "constraint": {"constraint", "odrl:constraint"},
}


def _get_constraint_parts(d: dict) -> tuple[str | None, str | None, str | None]:
    """
    Extract (leftOperand, operator, rightOperand) from a constraint dict.

    Returns ``(None, None, None)`` when the dict is not a constraint.
    """
    left = op = right = None
    for k in _CONSTRAINT_LEFT_KEYS:
        if k in d:
            left = d[k]
            break
    for k in _CONSTRAINT_OP_KEYS:
        if k in d:
            op = d[k]
            break
    for k in _CONSTRAINT_RIGHT_KEYS:
        if k in d:
            right = d[k]
            break
    if left is not None or op is not None or right is not None:
        return (left, op, right)
    return (None, None, None)


def _format_constraint(left, op, right) -> str:
    """Format a constraint as ``leftOperand OPERATOR rightOperand``."""
    return f"{_fmt(left)} {_fmt(op)} {_fmt(right)}"


def _is_constraint_dict(d: dict) -> bool:
    """Return ``True`` if *d* looks like an ODRL constraint (has at least leftOperand)."""
    return any(k in d for k in _CONSTRAINT_LEFT_KEYS)


def _to_set(value) -> set:
    """Coerce a value (string or list) into a set for subset checks."""
    if isinstance(value, list):
        return set(value)
    if isinstance(value, str):
        return {value}
    return {value} if value is not None else set()


def _right_operand_matches(catalog_right, allowed_right) -> bool:
    """
    Check whether the allowed rightOperand is satisfied by the catalog rightOperand.

    When either side is a list, ordering is ignored and **subset** semantics
    are applied: every value configured in ``allowed_right`` must appear in
    ``catalog_right``.  The catalog may contain additional values.

    For simple scalar values, exact equality is required.
    """
    if isinstance(catalog_right, list) or isinstance(allowed_right, list):
        cat_set = _to_set(catalog_right)
        allow_set = _to_set(allowed_right)
        return allow_set.issubset(cat_set)
    return catalog_right == allowed_right


def _constraint_matches(cat_dict: dict, allow_dict: dict) -> bool:
    """
    Compare two normalized constraint dicts.

    ``leftOperand`` and ``operator`` must match exactly.
    ``rightOperand`` uses subset semantics when either side is a list.
    """
    cat_left, cat_op, cat_right = _get_constraint_parts(cat_dict)
    allow_left, allow_op, allow_right = _get_constraint_parts(allow_dict)
    if cat_left != allow_left or cat_op != allow_op:
        return False
    return _right_operand_matches(cat_right, allow_right)


def _permission_matches(catalog_perm, allowed_perm) -> bool:
    """
    Check whether the catalog's permission(s) satisfy the allowed permission(s).

    When the catalog offers multiple permissions (a list after normalization),
    each allowed permission must be matched by **at least one** catalog
    permission.  Extra catalog permissions are tolerated.

    When both sides are single dicts, standard deep comparison is used.
    """
    cat_list = catalog_perm if isinstance(catalog_perm, list) else [catalog_perm]
    allow_list = allowed_perm if isinstance(allowed_perm, list) else [allowed_perm]

    # Every allowed permission must be satisfied by some catalog permission
    for allow_p in allow_list:
        if not any(_policies_match(cat_p, allow_p) for cat_p in cat_list):
            return False
    return True


def _policies_match(normalized_policy, normalized_allowed) -> bool:
    """
    Deep-compare two normalized policy structures.

    Identical to ``==`` except that:

    - **constraint rightOperand** arrays use subset semantics: every value
      in ``normalized_allowed``'s rightOperand must appear in
      ``normalized_policy``'s rightOperand (order-insensitive, extra values
      in the catalog are tolerated).
    - **permission / obligation / prohibition** arrays use "any match"
      semantics: when the catalog has multiple rules, each allowed rule
      only needs to match *one* of them.
    """
    # ODRL rule keys get special "any match" handling
    if isinstance(normalized_policy, dict) and isinstance(normalized_allowed, dict):
        # Constraint-level comparison with rightOperand subset logic
        if _is_constraint_dict(normalized_policy) and _is_constraint_dict(normalized_allowed):
            return _constraint_matches(normalized_policy, normalized_allowed)

        if normalized_policy.keys() != normalized_allowed.keys():
            return False
        for k in normalized_policy:
            if k in _ODRL_RULE_KEYS:
                if not _permission_matches(normalized_policy[k], normalized_allowed[k]):
                    return False
            else:
                if not _policies_match(normalized_policy[k], normalized_allowed[k]):
                    return False
        return True

    if type(normalized_policy) is not type(normalized_allowed):
        return False

    if isinstance(normalized_policy, list):
        if len(normalized_policy) != len(normalized_allowed):
            return False
        return all(
            _policies_match(c, a)
            for c, a in zip(normalized_policy, normalized_allowed)
        )

    return normalized_policy == normalized_allowed


def _explain_constraint_diff(cat_dict: dict, allow_dict: dict, path: str) -> list[str]:
    """
    Compare two constraint dicts and produce a readable triplet-based diff.

    Example output::

        permission.constraint.and[0]: constraint mismatch
          Catalog:  'cx-policy:Membership' 'eq' 'active'
          Allowed:  'cx-policy:Membership' 'eq' 'WRONG'
          Reason: rightOperand differs — catalog has 'active', allowed has 'WRONG'
    """
    cat_left, cat_op, cat_right = _get_constraint_parts(cat_dict)
    allow_left, allow_op, allow_right = _get_constraint_parts(allow_dict)

    field_diffs: list[str] = []
    if cat_left != allow_left:
        field_diffs.append(f"leftOperand differs — catalog has {_fmt(cat_left)}, allowed has {_fmt(allow_left)}")
    if cat_op != allow_op:
        field_diffs.append(f"operator differs — catalog has {_fmt(cat_op)}, allowed has {_fmt(allow_op)}")
    if not _right_operand_matches(cat_right, allow_right):
        if isinstance(cat_right, list) or isinstance(allow_right, list):
            cat_set = _to_set(cat_right)
            allow_set = _to_set(allow_right)
            missing = sorted(allow_set - cat_set)
            field_diffs.append(
                f"rightOperand mismatch — configured values {[str(v) for v in missing]} "
                f"not found in catalog's rightOperand {_fmt(cat_right)}"
            )
        else:
            field_diffs.append(f"rightOperand differs — catalog has {_fmt(cat_right)}, allowed has {_fmt(allow_right)}")

    if not field_diffs:
        return []

    lines = [
        f"{path}: constraint mismatch",
        f"  Catalog:  {_format_constraint(cat_left, cat_op, cat_right)}",
        f"  Allowed:  {_format_constraint(allow_left, allow_op, allow_right)}",
    ]
    for fd in field_diffs:
        lines.append(f"  Reason: {fd}")
    return ["\n".join(lines)]


def _explain_permission_diff(cat_val, allow_val, path: str) -> list[str]:
    """
    Produce diff output for the ``permission`` key, applying the same
    "any match" semantics used by ``_permission_matches``.

    When the catalog has multiple permissions and the allowed config has
    a single permission, the diff shows the best-effort comparison against
    each catalog permission.
    """
    cat_list = cat_val if isinstance(cat_val, list) else [cat_val]
    allow_list = allow_val if isinstance(allow_val, list) else [allow_val]

    diffs: list[str] = []
    for ai, allow_p in enumerate(allow_list):
        allow_label = f"{path}[{ai}]" if len(allow_list) > 1 else path
        matched = False
        per_perm_diffs: list[list[str]] = []
        for ci, cat_p in enumerate(cat_list):
            if _policies_match(cat_p, allow_p):
                matched = True
                break
            cat_label = f"catalog {path}[{ci}]" if len(cat_list) > 1 else path
            sub = _explain_policy_diff(cat_p, allow_p, cat_label)
            per_perm_diffs.append(sub)
        if not matched:
            if len(cat_list) > 1:
                diffs.append(
                    f"{allow_label}: no catalog permission (out of {len(cat_list)}) matched"
                )
                for ci, sub in enumerate(per_perm_diffs):
                    diffs.extend(sub)
            else:
                # Single catalog permission — straightforward diff
                if isinstance(cat_val, dict) and isinstance(allow_val, dict):
                    diffs.extend(_explain_policy_diff(cat_val, allow_val, path))
                elif isinstance(cat_val, list) and isinstance(allow_val, list):
                    if len(cat_val) != len(allow_val):
                        diffs.append(
                            f"{path}: different number of permissions "
                            f"(catalog has {len(cat_val)}, allowed has {len(allow_val)})"
                        )
                    else:
                        for i, (c, a) in enumerate(zip(cat_val, allow_val)):
                            diffs.extend(_explain_policy_diff(c, a, f"{path}[{i}]"))
                else:
                    diffs.append(
                        f"{path}: catalog has {_fmt(cat_val)}, allowed has {_fmt(allow_val)}"
                    )
    return diffs


def _check_policy_structure(normalized: dict, label: str) -> list[str]:
    """
    Check that a normalized policy has the expected structural keys.

    Returns warnings like::

        Allowed policy config issue: missing 'permission' (looked for: permission, odrl:permission)
    """
    issues: list[str] = []
    for name, alternatives in _POLICY_REQUIRED_KEYS.items():
        if not any(k in normalized for k in alternatives):
            issues.append(
                f"{label} config issue: missing '{name}' "
                f"(looked for: {', '.join(sorted(alternatives))})"
            )
            continue
        # Check permission sub-structure
        perm_val = None
        for k in alternatives:
            perm_val = normalized.get(k)
            if perm_val is not None:
                break
        if isinstance(perm_val, dict):
            for sub_name, sub_alts in _PERMISSION_REQUIRED_KEYS.items():
                if not any(k in perm_val for k in sub_alts):
                    issues.append(
                        f"{label} config issue: missing '{sub_name}' inside permission "
                        f"(looked for: {', '.join(sorted(sub_alts))})"
                    )
    return issues


def _explain_policy_diff(normalized_policy: dict, normalized_allowed: dict, path: str = "") -> list[str]:
    """
    Recursively compare two normalized policy dicts and return
    human-readable descriptions of every difference found.

    Constraint dicts are detected and reported as readable triplets::

        permission.constraint.and[0]: constraint mismatch
          Catalog:  'cx-policy:Membership' 'eq' 'active'
          Allowed:  'cx-policy:Membership' 'eq' 'WRONG'
          Reason: rightOperand differs — catalog has 'active', allowed has 'WRONG'

    Missing structural keys in the allowed policy config are reported::

        Allowed policy config issue: missing 'constraint' inside permission
    """
    diffs: list[str] = []

    # --- Structural checks on the allowed policy config (only at root) ---
    if not path:
        diffs.extend(_check_policy_structure(normalized_allowed, "Allowed policy"))

    # --- Non-dict comparison ---
    if not isinstance(normalized_policy, dict) or not isinstance(normalized_allowed, dict):
        if normalized_policy != normalized_allowed:
            loc = path or "<root>"
            diffs.append(f"{loc}: catalog has {_fmt(normalized_policy)}, allowed has {_fmt(normalized_allowed)}")
        return diffs

    # --- If both are constraint dicts, use triplet comparison ---
    if _is_constraint_dict(normalized_policy) and _is_constraint_dict(normalized_allowed):
        return diffs + _explain_constraint_diff(normalized_policy, normalized_allowed, path or "<root>")

    all_keys = set(normalized_policy.keys()) | set(normalized_allowed.keys())

    for key in sorted(all_keys):
        child_path = f"{path}.{key}" if path else key
        cat_val = normalized_policy.get(key, "<missing>")
        allow_val = normalized_allowed.get(key, "<missing>")

        if cat_val == "<missing>":
            diffs.append(f"{child_path}: missing in catalog policy, present in allowed ({_fmt(allow_val)})")
        elif allow_val == "<missing>":
            diffs.append(f"{child_path}: present in catalog policy ({_fmt(cat_val)}), missing in allowed")
        elif key in _ODRL_RULE_KEYS:
            # ODRL rules: "any match" semantics – report diffs only if no
            # catalog rule satisfies the allowed rule(s).
            diffs.extend(_explain_permission_diff(cat_val, allow_val, child_path))
        elif isinstance(cat_val, dict) and isinstance(allow_val, dict):
            diffs.extend(_explain_policy_diff(cat_val, allow_val, child_path))
        elif isinstance(cat_val, list) and isinstance(allow_val, list):
            if len(cat_val) != len(allow_val):
                diffs.append(
                    f"{child_path}: different number of constraints "
                    f"(catalog has {len(cat_val)}, allowed has {len(allow_val)})"
                )
            else:
                for i, (c_item, a_item) in enumerate(zip(cat_val, allow_val)):
                    diffs.extend(_explain_policy_diff(c_item, a_item, f"{child_path}[{i}]"))
        elif cat_val != allow_val:
            diffs.append(f"{child_path}: catalog has {_fmt(cat_val)}, allowed has {_fmt(allow_val)}")

    return diffs


def _fmt(value) -> str:
    """Return a compact string representation for log messages."""
    if isinstance(value, str):
        return f"'{value}'"
    if value is None:
        return "<missing>"
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return repr(value)


class DspTools:
    """
    Class responsible for doing trivial dsp operations.

    DSP Docs: https://docs.internationaldataspaces.org/ids-knowledgebase/dataspace-protocol
    """
    
    @staticmethod
    def filter_assets_and_policies(catalog:dict, allowed_policies:list=[]) -> list[tuple[str, dict]]:
        """
        Method to select a asset and policy from a DCAT Catalog.

        @returns: Success -> tuple[targetid:str, policy:dict] Fail -> Exception
        
        """

        if catalog is None:
            raise Exception("It was not possible to get the policy, because the catalog is empty!")
        
        dataset:list|dict = _get_datasets(catalog)
        ### Asset Evaluation

        valid_assets:list = []

        ## If just one asset is there
        if isinstance(dataset, dict):
            policy = DspTools.get_dataset_policy(dataset=dataset, allowed_policies=allowed_policies)
            if policy is None:
                raise ValueError("No valid asset and policy allowed at the DCAT Catalog dataset!")

            valid_assets.append((dataset.get("@id"), policy)) ## Return the assetid and the policy
            return valid_assets
        
        ## In case it is a empty list give error
        if(len(dataset) == 0):
            raise Exception("No dataset was found for the search asset! It is empty!")

        ## More than one asset, the prio is set by the allowed policies order
        for item in dataset:
            policy = DspTools.get_dataset_policy(dataset=item, allowed_policies=allowed_policies)
            if policy is not None:
                valid_assets.append((item.get("@id"), policy)) ## Return the assetid and the policy

        if len(valid_assets) == 0:
            raise ValueError("No valid policy was found for any item in the list. No valid asset found!")
        
        return valid_assets
    
    @staticmethod
    def is_catalog_empty(catalog:dict) -> bool:
        dataset:list|dict = _get_datasets(catalog)
        if(dataset is None):
            return False
        
        ## If just one asset is there
        if isinstance(dataset, dict):
            return False if "@id" in dataset else True
        
        return len(dataset) == 0
        
    @staticmethod
    def get_dataset_policy(dataset:dict, allowed_policies:list=[]) -> dict | None:
        """
        Gets a valid policy from an dataset.

        @returns: dict: the selected policy or None if no valid policy was found
        """
        ### Policy Evaluation
        policies:dict|list = _get_policies(dataset)    

        ## One Policy
        if isinstance(policies, dict):
            return policies if DspTools.is_policy_valid(policy=policies, allowed_policies=allowed_policies) else None ## Return the policy object if is valid

        ## More than one policy
        for policy in policies:
            ## In case the policy is not valid, continue
            if not DspTools.is_policy_valid(policy=policy, allowed_policies=allowed_policies):
               continue
            return policy
        
        # In case no policy was selected it will return None
        return None
    
    @staticmethod
    def is_policy_valid(policy:dict, allowed_policies:list=None) -> bool:
        """
        Checks whether a catalog offer policy is acceptable.

        allowed_policies semantics:
          None  – any policy is valid (no filtering applied).
          []    – no policy is valid; always returns False.
          [...] – the policy (stripped of ``@id`` / ``@type``) must appear in the list.

        When a policy is rejected, detailed DEBUG-level log messages are
        emitted explaining why it did not match each allowed policy.

        @returns: True if the policy is accepted, False otherwise.
        """
        ## None → accept everything
        if allowed_policies is None:
            return True

        ## Empty list → reject everything
        if len(allowed_policies) == 0:
            logger.debug("Policy rejected: allowed_policies list is empty.")
            return False
        
        ## Normalize the catalog policy (strips @id/@type, unwraps
        ## single-element lists, removes empty lists, sorts constraints).
        normalized_policy = _normalize_policy_value(policy)

        ## Compare against every allowed policy (also normalized).
        ## Uses _policies_match which applies subset semantics for
        ## rightOperand arrays (all configured values must be present
        ## in the catalog, order-insensitive, extras tolerated).
        mismatch_reports: list[str] = []
        for idx, allowed in enumerate(allowed_policies):
            normalized_allowed = _normalize_policy_value(allowed)
            if _policies_match(normalized_policy, normalized_allowed):
                logger.debug("Policy matched allowed policy at index %d.", idx)
                return True
            # Collect diff details for this candidate
            diffs = _explain_policy_diff(normalized_policy, normalized_allowed)
            mismatch_reports.append(
                f"  Allowed policy [{idx}] differences:\n"
                + "\n".join(f"    - {d}" for d in diffs)
            )

        # None matched – emit a comprehensive log
        policy_id = policy.get("@id", "<unknown>")
        logger.debug(
            "Policy '%s' did not match any of the %d allowed policies:\n%s",
            policy_id,
            len(allowed_policies),
            "\n".join(mismatch_reports),
        )
        return False

