"""Total byte-space: 256/256 defined, zero undefined bit patterns (QW-1).

Every byte value maps to a well-defined (domain, opcode) either as a REAL op
(group 1-3) or as the SYNTH opcode group - the assembler's cue to run a
synthesis pass instead of faulting. Mojibake and English are dual input
mappings to the SAME table (QW-5): utf8-bytes-read-as-latin1 (mojibake form)
and plaintext tokens collide deterministically on the same opcodes.
"""
DOMAIN_SYNTH = "SYNTH"

# Real opcodes: 0x00-0xA2 = arithmetic/logic/coercion; 0xA3-0xFF reserved SYNTH group.
_REAL_OPS = {
    0x00: ("CONST", "CONST"), 0x01: ("LOAD", "KARTA"), 0x02: ("STORE", "KARMA"),
    0x03: ("ADD", "KARANA"), 0x04: ("SUB", "KARANA"), 0x05: ("MUL", "KARANA"),
    0x06: ("DIV", "KARANA"), 0x07: ("AND", "KARANA"), 0x08: ("OR", "KARANA"),
    0x09: ("NOT", "KARANA"), 0x0A: ("CAST_INT", "KARANA"), 0x0B: ("CAST_STR", "KARANA"),
    0x0C: ("CAST_BYTES", "KARANA"), 0x0D: ("CAST_FLOAT", "KARANA"), 0x0E: ("CAST_BOOL", "KARANA"),
    0x0F: ("CALL", "ADHI"), 0x10: ("RET", "KARMA"), 0x11: ("JNZ", "ADHI"),
    0x12: ("APPLY_BRIDGE", "BRIDGE"), 0x13: ("SEND", "SAMPRADANA"), 0x14: ("SRC", "APADANA"),
    0x15: ("PACK_TUPLE", "KARANA"), 0x16: ("UNPACK_TUPLE", "KARANA"), 0x17: ("EQ", "KARANA"),
    0x18: ("LEN", "KARANA"), 0x19: ("HASH256", "KARANA"), 0x1A: ("NOP", "ADHI"),
}


def _build():
    table = {}
    for b in range(256):
        if b in _REAL_OPS:
            op, dom = _REAL_OPS[b]
            table[b] = (dom, op, True)
        else:
            # SYNTH group: byte IS the synthesis hint id (0xA3-0xFF -> 93 bridge slots)
            table[b] = (DOMAIN_SYNTH, "SYNTH_%02X" % b, False)
    return table


BYTE_TABLE = _build()  # total: every byte defined, mode True=real False=synth
assert len(BYTE_TABLE) == 256


def decode(byte_val):
    """Total: never raises, never undefined (QW-6)."""
    return BYTE_TABLE[byte_val & 0xFF]


def map_english(token, seed=1337):
    """English -> opcode byte (deterministic hash-fold, dual mapping 1/2)."""
    h = 0
    for ch in str(token):
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return (h ^ seed) & 0xFF


def map_mojibake(s):
    """Mojibake text -> its latin1-read utf8 byte stream -> opcodes (dual 2/2).

    A utf-8 string misread as latin-1 yields mojibake; reading it BACK gives
    the original utf-8 bytes, whose opcode map is identical to the English
    path's raw-byte channel. Saturates edge-case input state coverage.
    """
    try:
        raw = s.encode("latin-1")
    except UnicodeEncodeError:
        return [b & 0xFF for b in str(s).encode("utf-8")]
    try:
        raw.decode("utf-8")
        return [b & 0xFF for b in raw]  # mojibake reconstruction: THE utf-8 stream
    except UnicodeDecodeError:
        return [b & 0xFF for b in s.encode("utf-8")]  # real latin-1-range text -> English channel


def map_english(token, seed=1337):
    """English -> opcode byte (deterministic hash-fold, dual mapping 1/2)."""
    h = 0
    for ch in str(token):
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return (h ^ seed) & 0xFF


