import hashlib
import json

from ..constants import DCATKeys, ODRLKeys, JSONLDKeys

def extract_odrl_policy(offer: dict) -> dict:
    return offer.get(DCATKeys.DATASET, {}).get(ODRLKeys.POLICY, {})

def hash_constraints(constraints):
    canon = extract_constraints(constraints)
    canon_str = json.dumps(canon, separators=(",", ":"))
    return hashlib.sha256(canon_str.encode('utf-8')).hexdigest()

def extract_constraints(constraints):
    if isinstance(constraints, dict):
        constraints = constraints.get(ODRLKeys.ODRL_AND) or constraints.get(ODRLKeys.ODRL_OR) or []

    if not isinstance(constraints, list):
        return []

    return sorted([
        (
            c[ODRLKeys.LEFT_OPERAND][JSONLDKeys.AT_ID],
            c[ODRLKeys.OPERATOR][JSONLDKeys.AT_ID],
            c[ODRLKeys.RIGHT_OPERAND]
        )
        for c in constraints
    ])