import importlib.util
from pathlib import Path


def test_public_surface_audit_passes() -> None:
    path = Path("tools/public_surface_audit.py")
    spec = importlib.util.spec_from_file_location("public_surface_audit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.audit(Path.cwd()) == []
