from pathlib import Path
from typing import Any


def _simple_yaml_parse(text: str) -> dict[str, Any]:
    """Tiny fallback parser for simple nested `key: value` mappings."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        key, sep, value = line.strip().partition(":")
        if not sep:
            raise ValueError(f"Invalid config line: {raw}")

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        parsed: Any
        value = value.strip()
        if value == "":
            parsed = {}
            parent[key] = parsed
            stack.append((indent, parsed))
            continue

        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            parsed = [] if inner == "" else [item.strip().strip('"').strip("'") for item in inner.split(",")]
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        else:
            try:
                parsed = int(value)
            except ValueError:
                try:
                    parsed = float(value)
                except ValueError:
                    parsed = value.strip('"').strip("'")

        parent[key] = parsed

    return root


def load_yaml(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")

    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("YAML config root must be a mapping")
        return data
    except ModuleNotFoundError:
        data = _simple_yaml_parse(text)
        if not isinstance(data, dict):
            raise ValueError("Config root must be a mapping")
        return data
