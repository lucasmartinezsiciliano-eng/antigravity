from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Literal

import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    data_dir: Path = Field(default=Path("/srv/centrum-studio"), alias="CENTRUM_STUDIO_DATA_DIR")
    comfyui_url: str = Field(default="http://localhost:8188", alias="COMFYUI_URL")
    plur_url: str = Field(default="http://localhost:8420", alias="PLUR_URL")
    plur_scope: str = Field(default="project:centrum-studio", alias="PLUR_SCOPE")
    mcp_transport: Literal["stdio", "sse", "http"] = Field(default="stdio", alias="MCP_TRANSPORT")
    ui_host: str = Field(default="0.0.0.0", alias="UI_HOST")
    ui_port: int = Field(default=8788, alias="UI_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    gpu_mode_file: Path = Field(default=Path("/srv/centrum-studio/gpu_mode"), alias="GPU_MODE_FILE")
    gpu_mode_poll_seconds: int = Field(default=60, alias="GPU_MODE_POLL_SECONDS")
    active_soul: str = Field(default="placeholder", alias="ACTIVE_SOUL")

    @property
    def souls_dir(self) -> Path:
        return self.data_dir / "souls"

    @property
    def renders_dir(self) -> Path:
        return self.data_dir / "renders"

    @property
    def music_dir(self) -> Path:
        return self.data_dir / "music"

    @property
    def luts_dir(self) -> Path:
        return self.data_dir / "luts"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "centrum_studio.db"

    def ensure_directories(self) -> None:
        for d in (
            self.data_dir,
            self.souls_dir,
            self.renders_dir,
            self.music_dir,
            self.luts_dir,
            self.cache_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)
        if not self.gpu_mode_file.exists():
            self.gpu_mode_file.write_text("agents\n", encoding="utf-8")


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def configure_logging(level: str | None = None) -> structlog.stdlib.BoundLogger:
    cfg = get_config()
    log_level = (level or cfg.log_level).upper()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, log_level, logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level, logging.INFO)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger("centrum_studio")
