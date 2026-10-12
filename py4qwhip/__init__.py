"""py4qwhip v2 - self-assembling Paninian bytecode runtime (2026-10-11 rebirth).

QW-1 total byte-space | QW-2 loop-closed self-assembly | QW-4 six domains/six
karakas | QW-5 mojibake+english dual mapping | QW-6 zero undefined states
(failures are reified artifacts, never exceptions).
"""
from .bytespace import BYTE_TABLE, decode, map_english, map_mojibake, DOMAIN_SYNTH
from .karaka import DOMAINS, ROLES, classify
from .vm import WhipVM, Frame, _num
from .synthesize import Assembler

__all__ = ["BYTE_TABLE", "decode", "map_english", "map_mojibake", "DOMAIN_SYNTH",
           "DOMAINS", "ROLES", "classify", "WhipVM", "Frame", "_num", "Assembler"]
