import importlib.util
from pathlib import Path


def test_release_metadata_is_consistent() -> None:
    path = Path("tools/validate_release_metadata.py")
    spec = importlib.util.spec_from_file_location("validate_release_metadata", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validate(Path.cwd()) == []
