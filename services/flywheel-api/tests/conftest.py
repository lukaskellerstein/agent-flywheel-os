from __future__ import annotations

import pytest
from helpers import FIXTURE

from flywheel_api.files import Files, read_folder
from flywheel_api.registry import Registry
from flywheel_api.store import FileStore


@pytest.fixture
def files() -> Files:
    """The hand-written sample use case, as a fresh dict each test may change."""
    return read_folder(FIXTURE)


@pytest.fixture
def registry(tmp_path) -> Registry:
    return Registry(FileStore(tmp_path / "store"))
