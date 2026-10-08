"""Tests for engine.entropy — synthetic data only, no real user files."""

import math
import os

from engine.entropy import file_entropy, shannon_entropy


def test_empty_is_zero():
    assert shannon_entropy(b"") == 0.0


def test_uniform_bytes_is_zero():
    assert shannon_entropy(b"a" * 1000) == 0.0


def test_two_symbols_is_one_bit():
    assert shannon_entropy(b"ab" * 500) == math.log2(2)


def test_plaintext_is_low():
    text = b"The quick brown fox jumps over the lazy dog. " * 50
    assert shannon_entropy(text) < 5.5


def test_random_bytes_is_high():
    assert shannon_entropy(os.urandom(8192)) > 7.5


def test_file_entropy_reads_head(tmp_path):
    p = tmp_path / "note.txt"
    p.write_bytes(b"hello world, this is a calm text file. " * 200)
    e = file_entropy(p)
    assert 0.0 < e < 6.0


def test_file_entropy_missing_file_is_zero(tmp_path):
    assert file_entropy(tmp_path / "nope.bin") == 0.0
