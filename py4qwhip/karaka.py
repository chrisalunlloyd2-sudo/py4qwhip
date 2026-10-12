"""Paninian classification lattice: 6 domains x 6 karaka roles (QW-4).

Every artifact the runtime ever produces - bytecode, bridges, values, failures
(nothing fails: refusals are artifacts too) - is born with its (domain, role)
tag. Deterministic, total: classify() cannot return undefined.
"""
DOMAINS = ("SOURCE", "CONTRACT", "OPERATOR", "FRAME", "RESULT", "BRIDGE")
ROLES = ("KARTA", "KARMA", "KARANA", "SAMPRADANA", "APADANA", "ADHI")

def classify(artifact_type, tag=""):
    """Total classifier: (artifact_type, tag) -> (domain, role), never undefined."""
    t = str(artifact_type).upper()
    g = str(tag).upper()
    if g in ROLES:
        role = g
    elif "DEP" in g or "MISS" in g:
        role = "APADANA"
    elif "OUT" in g or "RET" in g:
        role = "KARMA"
    elif "OP" in g or "CAST" in g or "ADD" in g:
        role = "KARANA"
    else:
        role = "ADHI"
    if "BRIDGE" in t or "SYNTH" in t:
        dom = "BRIDGE"
    elif "BYTECODE" in t or "BIN" in t:
        dom = "OPERATOR"
    elif "CONTRACT" in t or "SIG" in t:
        dom = "CONTRACT"
    elif "RESULT" in t or "VALUE" in t:
        dom = "RESULT"
    elif "SOURCE" in t or "INPUT" in t:
        dom = "SOURCE"
    else:
        dom = "FRAME"
    return dom, role
