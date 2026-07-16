"""Persistent inter-stage state and artifact references."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Artifact:
    """A persisted stage artifact."""

    path: str
    media_type: str
    description: str = ""

    def resolve(self, manifest_path: str | Path) -> Path:
        path = Path(self.path)
        return path if path.is_absolute() else Path(manifest_path).parent / path


@dataclass
class StageState:
    """Serializable contract passed from one stage to the next."""

    stage: int
    name: str
    status: str
    config_profile: str
    parameters: dict[str, Any]
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    upstream_manifest: str | None = None
    notes: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def add_artifact(
        self, key: str, path: str | Path, media_type: str, description: str = ""
    ) -> None:
        self.artifacts[key] = Artifact(str(path), media_type, description)

    def require(self, key: str, manifest_path: str | Path) -> Path:
        if key not in self.artifacts:
            raise KeyError(f"Stage {self.stage} state has no artifact {key!r}")
        return self.artifacts[key].resolve(manifest_path)

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    @classmethod
    def read(cls, path: str | Path) -> "StageState":
        path = Path(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["artifacts"] = {
            key: Artifact(**value) for key, value in payload.get("artifacts", {}).items()
        }
        return cls(**payload)


def relative_artifact(path: Path, output_dir: Path) -> str:
    """Use compact manifest-relative paths whenever possible."""

    try:
        return str(path.relative_to(output_dir))
    except ValueError:
        return str(path)
