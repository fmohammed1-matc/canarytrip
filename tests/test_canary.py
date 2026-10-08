"""Tests for engine.canary — deploys only inside tmp_path."""

from engine.canary import MARKER, deploy_canaries, is_canary


def test_deploy_creates_files(tmp_path):
    targets = [str(tmp_path / "vault" / n) for n in ("a.txt", "b.csv", "c.docx")]
    out = deploy_canaries(targets)
    assert out == targets
    for t in targets:
        content = open(t).read()
        assert MARKER in content


def test_deploy_is_idempotent(tmp_path):
    target = str(tmp_path / "decoy.txt")
    deploy_canaries([target])
    first = open(target).read()
    deploy_canaries([target])
    assert open(target).read() == first


def test_deploy_leaves_real_files_alone(tmp_path):
    target = tmp_path / "real.txt"
    target.write_text("my actual notes")
    deploy_canaries([str(target)])
    assert target.read_text() == "my actual notes"


def test_is_canary(tmp_path):
    target = str(tmp_path / "c.txt")
    deploy_canaries([target])
    assert is_canary(target) is True
    other = tmp_path / "plain.txt"
    other.write_text("nothing special")
    assert is_canary(str(other)) is False
