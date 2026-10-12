"""Runner tests: the six QW constraints. No external deps."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py4qwhip import (BYTE_TABLE, decode, map_english, map_mojibake,
                      DOMAINS, ROLES, classify, WhipVM, Frame, Assembler)


def test_QW1_bytespace_total_256():
    assert len(BYTE_TABLE) == 256
    for b in range(256):
        dom, op, real = decode(b)
        assert dom and op and isinstance(real, bool)


def test_QW4_paninian_lattice_never_undefined():
    assert len(DOMAINS) == 6 and len(ROLES) == 6
    for t in ("bytecode", "bridge", "contract", "value", "input", "weird_thing", ""):
        dom, role = classify(t, t)
        assert dom in DOMAINS and role in ROLES


def test_QW5_dual_mapping_deterministic():
    a1, a2 = map_english("load"), map_english("load")
    assert a1 == a2 and isinstance(a1, int)
    moji = "h\xc3\xa9llo".encode("latin-1").decode("utf-8")  # mojibake form of utf-8 hé
    m = map_mojibake(moji)  # reading mojibake BACK yields the original utf-8 stream
    assert m == [104, 0xC3, 0xA9, 108, 108, 111], m  # byte-exact utf-8 reconstruction


def test_QW6_missing_dependency_never_raises():
    asm = Assembler()
    art = asm.resolve("totally_missing_module", boundary={"x": 4})
    assert art["status"] == "synthesized" and art["bytecode"]
    assert art["karaka"] in {("BRIDGE", r) for r in ROLES} or art["karaka"][0] == "BRIDGE"
    again = asm.resolve("totally_missing_module", boundary={"x": 4})
    assert again["status"] == "known"  # JIT cache hit (QW-2)


def test_QW2_synthesized_bytecode_executes():
    asm = Assembler()
    art = asm.resolve("identity_thing", boundary={"1": 7})
    vm = WhipVM()
    frame, out = vm.run(art["bytecode"], None)
    assert out is not None  # bridge executes, produces a value


def test_G4_determinism_byte_identical_synthesis():
    key1 = Assembler().resolve("determinism_check", boundary={"a": 1})["key"]
    key2 = Assembler().resolve("determinism_check", boundary={"a": 1})["key"]
    assert key1 == key2


def test_loop_closure_synth_opcode_executes_not_faults():
    asm = Assembler()
    vm = asm.vm()
    bytecode = [0x00, 9, 0xF0]  # CONST 9; SYNTH_0xF0 (undefined-behavior byte)
    frame, out = vm.run(bytecode)
    assert out is not None  # SYNTH hooked -> bridge ran; zero-undefined honored
    assert "SYNTH_F0" in frame.trace


def test_vm_real_opcode_arithmetic():
    vm = WhipVM()
    frame, out = vm.run([0x00, 7, 0x00, 5, 0x03])  # CONST 7; CONST 5; ADD
    assert out == 12.0


def test_vm_refusals_are_reified_not_raised():
    vm = WhipVM(max_steps=3)
    frame, out = vm.run([0x1A] * 50)  # NOPs exceed max_steps -> reified refusal
    assert out and "REFUSE" in str(out)
