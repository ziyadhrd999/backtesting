from pathlib import Path

from engine.utils.config import load_yaml


def test_load_yaml_reads_mapping(tmp_path: Path) -> None:
    p = tmp_path / "cfg.yaml"
    p.write_text("a:\n  b: 1\n", encoding="utf-8")
    data = load_yaml(p)
    assert data["a"]["b"] == 1
