from pathlib import Path

from engine.utils.config import load_yaml


def test_load_yaml_reads_mapping(tmp_path: Path) -> None:
    p = tmp_path / "cfg.yaml"
    p.write_text("a:\n  b: 1\n", encoding="utf-8")
    data = load_yaml(p)
    assert data["a"]["b"] == 1


def test_load_yaml_parses_inline_list_without_pyyaml(tmp_path: Path, monkeypatch) -> None:
    p = tmp_path / "cfg.yaml"
    p.write_text("data:\n  symbols: [NVDA, MSFT, AAPL]\n", encoding="utf-8")

    import builtins

    real_import = builtins.__import__

    def _raise_for_yaml(name, *args, **kwargs):
        if name == "yaml":
            raise ModuleNotFoundError("yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _raise_for_yaml)
    data = load_yaml(p)
    assert data["data"]["symbols"] == ["NVDA", "MSFT", "AAPL"]
