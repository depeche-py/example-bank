import pathlib as _pathlib

import pydantic as _pydantic
import pydantic_settings as _pydantic_settings


class _Config(_pydantic_settings.BaseSettings):
    model_config = _pydantic_settings.SettingsConfigDict(
        env_prefix="EXAMPLE_",
        env_file=_pathlib.Path(__file__).parent.parent / "run.env",
        env_file_encoding="utf-8",
    )
    db_dsn: _pydantic.SecretStr


def get() -> _Config:
    # mock point for tests
    return _Config()
