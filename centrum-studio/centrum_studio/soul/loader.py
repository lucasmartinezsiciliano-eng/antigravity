from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from ..config import get_config
from ..errors import SoulInvalidError, SoulNotFoundError
from .schema import Soul


class SoulLoader:
    def __init__(self, souls_dir: Path | None = None) -> None:
        self.souls_dir = souls_dir or get_config().souls_dir

    def list_souls(self) -> list[dict[str, Any]]:
        if not self.souls_dir.exists():
            return []
        result: list[dict[str, Any]] = []
        for name_dir in sorted(p for p in self.souls_dir.iterdir() if p.is_dir()):
            versions: list[str] = []
            active: str | None = None
            for v_dir in sorted(p for p in name_dir.iterdir() if p.is_dir() and p.name.startswith("v")):
                versions.append(v_dir.name)
            active_link = name_dir / "ACTIVE"
            if active_link.exists():
                try:
                    active = active_link.resolve().name
                except OSError:
                    active = None
            result.append({"name": name_dir.name, "versions": versions, "active": active})
        return result

    def active_path(self, soul_name: str | None = None) -> Path:
        name = soul_name or get_config().active_soul
        base = self.souls_dir / name
        if not base.exists():
            raise SoulNotFoundError(
                f"Soul '{name}' not found in {self.souls_dir}",
                details={"souls_dir": str(self.souls_dir), "soul_name": name},
            )
        active_link = base / "ACTIVE"
        if active_link.exists():
            try:
                target = active_link.resolve()
                if target.exists() and (target / "soul.json").exists():
                    return target
            except OSError:
                pass
        versions = sorted(
            [p for p in base.iterdir() if p.is_dir() and p.name.startswith("v")],
            key=lambda p: p.name,
            reverse=True,
        )
        for v in versions:
            if (v / "soul.json").exists():
                return v
        raise SoulNotFoundError(
            f"No active version with soul.json for soul '{name}'",
            details={"souls_dir": str(self.souls_dir), "soul_name": name},
        )

    def load(self, soul_name: str | None = None) -> Soul:
        version_path = self.active_path(soul_name)
        manifest = version_path / "soul.json"
        try:
            raw = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise SoulInvalidError(
                f"Failed to read soul manifest at {manifest}: {e}",
                details={"manifest_path": str(manifest)},
            ) from e
        try:
            return Soul.model_validate(raw)
        except Exception as e:
            raise SoulInvalidError(
                f"soul.json failed schema validation: {e}",
                details={"manifest_path": str(manifest)},
            ) from e

    def load_with_paths(self, soul_name: str | None = None) -> tuple[Soul, Path]:
        version_path = self.active_path(soul_name)
        soul = self.load(soul_name)
        return soul, version_path

    def inject_into_prompt(self, soul: Soul, scene_description: str) -> str:
        token = soul.trigger_token.strip()
        if token and token.lower() not in scene_description.lower():
            return f"{token}, {scene_description.strip()}"
        return scene_description.strip()

    def create_soul(
        self,
        name: str,
        version: str = "v1",
        trigger_token: str | None = None,
        character_name: str | None = None,
        activate: bool = True,
        notes: str | None = None,
    ) -> Path:
        if not version.startswith("v"):
            version = f"v{version}"
        version_dir = self.souls_dir / name / version
        if version_dir.exists():
            raise SoulInvalidError(
                f"Soul version already exists: {version_dir}",
                error_code="SOUL_EXISTS",
                recovery_action="use_different_version",
            )
        for sub in ("lora", "embeddings", "ip_adapter", "canonical", "workflows"):
            (version_dir / sub).mkdir(parents=True, exist_ok=True)
        soul = Soul(
            soul_id=name,
            version=version,
            character_name=character_name or name.title(),
            trigger_token=trigger_token or f"cs_{name}_{version}",
            notes=notes or "Avatar and voice TBD with Mariano — using placeholder for development",
        )
        manifest = version_dir / "soul.json"
        manifest.write_text(
            json.dumps(soul.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if activate:
            self.activate(name, version)
        return version_dir

    def activate(self, name: str, version: str) -> Path:
        if not version.startswith("v"):
            version = f"v{version}"
        base = self.souls_dir / name
        target = base / version
        if not target.exists():
            raise SoulNotFoundError(
                f"Cannot activate — version not found: {target}",
                details={"name": name, "version": version},
            )
        link = base / "ACTIVE"
        if link.exists() or link.is_symlink():
            if link.is_symlink() or link.is_file():
                link.unlink()
            elif link.is_dir():
                shutil.rmtree(link)
        try:
            os.symlink(version, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            (base / "ACTIVE.txt").write_text(version, encoding="utf-8")
        return target


_loader: SoulLoader | None = None


def get_soul_loader() -> SoulLoader:
    global _loader
    if _loader is None:
        _loader = SoulLoader()
    return _loader
