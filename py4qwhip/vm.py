"""WhipVM: deterministic stack machine over the total byte-space (QW-1/QW-2).

Zero-undefined by construction: SYNTH group bytes (0xA3-0xFF) trigger the
self-assembly hook instead of faulting - missing behavior is synthesized,
spliced, and execution continues. Loop closure lives HERE.
"""
from .bytespace import decode, DOMAIN_SYNTH


class Frame(object):
    __slots__ = ("stack", "locals", "trace")

    def __init__(self):
        self.stack = []
        self.locals = {}
        self.trace = []


class WhipVM(object):
    """Bytecode interpreter; synth_hook = assembler.synthesize(name) -> bytes."""

    def __init__(self, synth_hook=None, max_steps=10000):
        self.synth_hook = synth_hook
        self.max_steps = max_steps

    def run(self, bytecode, frame=None):
        frame = frame or Frame()
        pc = 0
        steps = 0
        while pc < len(bytecode):
            steps += 1
            if steps > self.max_steps:
                return frame, ("REFUSE_MAXSTEPS",)  # reified, never raised
            b = bytecode[pc] & 0xFF
            pc += 1
            dom, op, real = decode(b)
            frame.trace.append(op)
            if not real:  # SYNTH group: self-assembly hook
                if self.synth_hook is None:
                    frame.stack.append(("SYNTH_MISSING", op))
                    continue
                bridge_bc = self.synth_hook(op)
                frame.stack.append(self.run(bridge_bc, frame)[1])
                continue
            st = frame.stack
            if op == "CONST":
                if pc < len(bytecode):
                    st.append(bytecode[pc]); pc += 1
            elif op == "LOAD":
                st.append(frame.locals.get(st.pop() if st else "", ("UNDEF", op))) if op else None
            elif op == "ADD":
                if len(st) >= 2:
                    a, bb = st.pop(), st.pop()
                    st.append(_num(a) + _num(bb))
            elif op == "SUB" and len(st) >= 2:
                a, bb = st.pop(), st.pop(); st.append(_num(bb) - _num(a))
            elif op == "MUL" and len(st) >= 2:
                a, bb = st.pop(), st.pop(); st.append(_num(a) * _num(bb))
            elif op == "EQ" and len(st) >= 2:
                a, bb = st.pop(), st.pop(); st.append(1.0 if a == bb else 0.0)
            elif op == "LEN":
                st.append(float(len(st.pop()))) if st else None
            elif op == "CAST_INT":
                st.append(int(_num(st[-1]))) if st else None
            elif op == "NOT" and st:
                st.append(0.0 if st.pop() in (0, 0.0, "", False) else 1.0)
            elif op in ("NOP", "APPLY_BRIDGE", "PACK_TUPLE", "UNPACK_TUPLE", "SEND", "SRC"):
                continue
            else:
                st.append(("REFUSE_OP", op))  # reified refusal, still not an exception
        return frame, (frame.stack[-1] if frame.stack else None)


def _num(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    if isinstance(v, bytes):
        try:
            return float(v.decode("utf-8").strip() or 0)
        except Exception:
            return float(len(v))
    if isinstance(v, str):
        try:
            return float(v.strip() or 0)
        except Exception:
            return float(len(v))
    return 0.0  # total coercion: nothing maps to undefined
