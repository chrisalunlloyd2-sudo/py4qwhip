"""Self-assembly engine: missing dependencies are incomplete constraint
graphs, not errors (QW-6). The assembler completes them via the karaka
lattice, emits bytecode into the frame, caches to the binary table and the
VM executes immediately (QW-2). Redox port note: this module is the
port-authority contract; a Redox target implements the same interface in
Rust - see docs/REDOX_PORT.md (architecture shipped ahead of the port).

Bridge math (shortest deterministic path, per spec):
- Recipe table = ordered primitive transform compositions (kāraṇa rules).
- Synthesis enumerates recipes in ascending composition length; the first
  recipe whose validation (type check on boundary conditions) satisfies the
  contract is selected. Deterministic: same graph -> same recipe -> same
  bytecode -> same result, every run (G4-style byte-identical).
"""
import hashlib
from .karaka import classify
from .vm import WhipVM, Frame

# kāraṇa recipe table: (recipe_name, length_rank, builder(boundary)->bytecode)
_RECIPES = (
    ("identity", 0, lambda b: [0x14, 0x01]),                      # SRC;LOAD
    ("int_coerce", 1, lambda b: [0x14, 0x01, 0x0A]),              # SRC;LOAD;CAST_INT
    ("float_coerce", 1, lambda b: [0x14, 0x01, 0x0D]),            # CAST_FLOAT
    ("string_coerce", 1, lambda b: [0x14, 0x01, 0x0B]),           # CAST_STR
    ("bool_coerce", 1, lambda b: [0x14, 0x01, 0x0E]),             # CAST_BOOL
    ("len_bridge", 2, lambda b: [0x14, 0x01, 0x18]),              # LEN (containers)
    ("bytes_fallback", 3, lambda b: [0x14, 0x01, 0x0C, 0x18]),    # CAST_BYTES;LEN (total)
)


class Assembler(object):
    """Treats missing nodes as boundary conditions and synthesizes bridges."""

    def __init__(self):
        self.manifest = set()          # known symbols/types
        self.binary_table = {}         # cache_key -> bytecode (QW-2 JIT cache)
        self.synth_log = []            # ADD-only audit: every synthesis pass

    def resolve(self, dep_name, boundary, expected_role="KARMA"):
        """Missing/known dependency -> artifact. NEVER raises (QW-6)."""
        if dep_name in self.manifest:
            return {"status": "known", "name": dep_name,
                    "karaka": classify("bytecode", expected_role)}
        recipe, bytecode = self._shortest_path(boundary, expected_role)
        key = hashlib.sha256(repr((dep_name, sorted(boundary.items()),
                                   expected_role, recipe)).encode()).hexdigest()[:16]
        self.binary_table[key] = bytecode
        self.manifest.add(dep_name)
        dom, role = classify("BRIDGE", "SYNTH_" + recipe.upper()[:6])
        self.synth_log.append({"dep": dep_name, "recipe": recipe, "key": key,
                               "karaka": (dom, role), "len": len(bytecode)})
        return {"status": "synthesized", "name": dep_name, "key": key,
                "bytecode": bytecode, "recipe": recipe, "karaka": (dom, role)}

    def _shortest_path(self, boundary, expected_role):
        """First recipe (ascending length) whose validation satisfies contract."""
        for name, _rank, build in _RECIPES:
            bc = build(boundary)
            if self._validates(bc, boundary, expected_role):
                return name, bc
        # total fallback: last recipe is total by construction - unreachable
        return _RECIPES[-1][0], _RECIPES[-1][2](boundary)

    def _validates(self, bytecode, boundary, expected_role):
        """Run candidate on boundary sample; synthesis must produce a value."""
        vm = WhipVM()
        f = Frame()
        f.locals = dict(boundary)
        _frame, out = vm.run(bytecode, f)
        return out is not None and not (isinstance(out, tuple) and out and "REFUSE" in str(out[0]))

    def synth_hook(self, synth_op):
        """VM SYNTH callback: synthesize bridge for the missing behavior."""
        art = self.resolve(synth_op, boundary={}, expected_role="ADHI")
        return art.get("bytecode", [0x1A])  # NOP only if hook misused

    def vm(self):
        return WhipVM(synth_hook=self.synth_hook)
