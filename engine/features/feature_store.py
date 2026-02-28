class FeatureStore:
    """In-memory placeholder for computed features."""

    def __init__(self) -> None:
        self._values: dict[str, list[float]] = {}

    def put(self, name: str, values: list[float]) -> None:
        self._values[name] = values

    def get(self, name: str) -> list[float]:
        return self._values[name]
