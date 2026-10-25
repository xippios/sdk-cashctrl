"""The reference refresh is a stub: CashCtrl ships no tenant data and no value set yet."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from xippios.cashctrl import enums, params

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "refresh_reference.py"


def load_script() -> Any:
    spec = importlib.util.spec_from_file_location("refresh_reference", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_stub_says_why_and_fails(capsys: pytest.CaptureFixture[str]) -> None:
    assert load_script().main([]) == 1
    err = capsys.readouterr().err
    assert "per-organisation data" in err
    assert "never packaged" in err


def test_nothing_is_packaged() -> None:
    assert params.PACKAGED_LISTS == ()
    assert params.packaged_values("account") is None
    assert enums.__all__ == []


def test_render_only_reproduces_the_committed_enums(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--render-only`` renders ``enums.py`` from the packaged files alone, ASCII-only.

    Nothing is packaged, so the module holds no enum; it is committed as core's renderer
    writes it (conventions §15, item 6).
    """
    script = load_script()
    committed = script.ENUMS.read_text(encoding="utf-8")
    monkeypatch.setattr(script, "ENUMS", tmp_path / "enums.py")
    assert script.main(["--render-only"]) == 0
    assert "0 enums" in capsys.readouterr().out
    rendered = (tmp_path / "enums.py").read_text(encoding="utf-8")
    assert rendered == committed
    assert rendered.isascii()
