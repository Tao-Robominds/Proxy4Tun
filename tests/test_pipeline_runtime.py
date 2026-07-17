"""Focused tests for profile resolution, path isolation, and CLI contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SAM4TUN = REPO / "sam4tun"


@pytest.fixture(autouse=True)
def _sys_path(monkeypatch):
    monkeypatch.syspath_prepend(str(SAM4TUN))
    monkeypatch.syspath_prepend(str(REPO))
    for key in ("PROXY4TUN_OUT_ROOT", "PROXY4TUN_INPUT_TXT", "PROXY4TUN_PARAMS_DIR"):
        monkeypatch.delenv(key, raising=False)


def test_canonical_t12_parameters_exist():
    params = REPO / "agents" / "t1&2" / "parameters"
    for stage in ("unfolding", "denoising", "enhancing", "detecting", "sam"):
        path = params / f"parameters_{stage}.json"
        assert path.is_file(), path
        data = json.loads(path.read_text())
        assert isinstance(data, dict) and data
    unfolding = json.loads((params / "parameters_unfolding.json").read_text())
    assert "swap_tunnel_centers" in unfolding


def test_prepare_output_dir_rejects_existing_without_flags(tmp_path, monkeypatch):
    from helpers.pipeline_io import OutputPathError, prepare_output_dir

    monkeypatch.setenv("PROXY4TUN_OUT_ROOT", str(tmp_path))
    run = tmp_path / "case-a"
    run.mkdir()
    (run / "stale.csv").write_text("x\n")
    with pytest.raises(OutputPathError, match="already exists"):
        prepare_output_dir("case-a")
    prepare_output_dir("case-a", overwrite=True)
    prepare_output_dir("case-a", resume=True)


def test_prepare_output_dir_protects_baseline_and_bo(tmp_path, monkeypatch):
    from helpers.pipeline_io import OutputPathError, prepare_output_dir

    data = tmp_path / "data"
    monkeypatch.setenv("PROXY4TUN_OUT_ROOT", str(data))
    for name in ("baseline", "bo"):
        (data / name).mkdir(parents=True)
        with pytest.raises(OutputPathError, match="protected"):
            prepare_output_dir(name, overwrite=True)


def test_ensure_dir_isolates_out_root(tmp_path, monkeypatch):
    from helpers import pipeline_io

    monkeypatch.setenv("PROXY4TUN_OUT_ROOT", str(tmp_path / "runs"))
    paths = pipeline_io.ensure_dir("iso-1")
    assert paths["final_csv"].startswith(str(tmp_path / "runs" / "iso-1"))
    assert Path(paths["evaluation_dir"]).is_dir()


def test_cli_help_mentions_contract():
    from sam4tun.pipeline import build_parser

    help_text = build_parser().format_help()
    assert "--profile" in help_text
    assert "--overwrite" in help_text
    assert "--dry-run" in help_text
    assert "--params-dir" in help_text


def test_cli_dry_run_with_temp_input(tmp_path):
    from sam4tun.pipeline import main

    cloud = tmp_path / "toy.txt"
    cloud.write_text("0 0 0 0 0 0\n")
    out = tmp_path / "artifacts" / "toy"
    main([str(cloud), str(out), "--profile", "sample", "--dry-run"])
    assert out.is_dir()


def test_cli_dry_run_blocks_occupied_output(tmp_path):
    from sam4tun.pipeline import main

    cloud = tmp_path / "toy.txt"
    cloud.write_text("0 0 0 0 0 0\n")
    out = tmp_path / "occupied"
    out.mkdir()
    (out / "keep.txt").write_text("1\n")
    with pytest.raises(SystemExit) as exc:
        main([str(cloud), str(out), "--profile", "sample", "--dry-run"])
    assert exc.value.code == 2


def test_resolve_params_dir_default_and_override(tmp_path):
    from sam4tun.pipeline import PROFILE_SCRIPTS, _resolve_params_dir, _script_dir

    t12 = (REPO / "agents" / "t1&2").resolve()
    t3 = (REPO / "agents" / "t3").resolve()
    default = _resolve_params_dir("t1&2", None)
    assert default == (t12 / "parameters").resolve()
    assert _script_dir("t1&2") == t12
    assert _script_dir("t3") == t3
    assert _script_dir("sample") == REPO / "agents" / "sample"
    assert (t12 / "1_unfolding.py").is_file()
    assert (t3 / "1_unfolding.py").is_file()
    assert PROFILE_SCRIPTS["t12"] == t12

    overlay = tmp_path / "overlay"
    overlay.mkdir()
    for stage in ("unfolding", "denoising", "enhancing", "detecting", "sam"):
        (overlay / f"parameters_{stage}.json").write_text("{}")
    assert _resolve_params_dir("sample", str(overlay)) == overlay.resolve()


def test_t12_unfolding_accepts_optional_flags_defaults_off():
    """T1/T2 unfolding treats residual_recentre / deterministic_theta as optional."""
    unfolding = json.loads(
        (REPO / "agents" / "t1&2" / "parameters" / "parameters_unfolding.json").read_text()
    )
    assert "swap_tunnel_centers" in unfolding
    assert "residual_recentre" not in unfolding
    assert "deterministic_theta_orientation" not in unfolding
    src = (REPO / "agents" / "t1&2" / "1_unfolding.py").read_text()
    assert 'params.get("residual_recentre", False)' in src
    assert 'params.get("deterministic_theta_orientation", False)' in src
