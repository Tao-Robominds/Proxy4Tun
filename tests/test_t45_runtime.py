"""T4&5 profile, geometry, and CLI contract tests."""

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


def test_canonical_t45_parameters_exist():
    params = REPO / "anchors" / "t4&5" / "4-1"
    for stage in ("unfolding", "denoising", "enhancing", "detecting", "sam"):
        path = params / f"parameters_{stage}.json"
        assert path.is_file(), path
    unfolding = json.loads((params / "parameters_unfolding.json").read_text())
    assert unfolding["diameter"] == 7.5
    assert unfolding["polynomial_degree"] == 2
    assert unfolding["slice_spacing_factor"] == 1.8
    assert unfolding["slice_filter_mode"] == "remove_top_tube"
    denoise = json.loads((params / "parameters_denoising.json").read_text())
    assert denoise["mask_r_low"] == 3.65
    assert denoise["mask_r_high"] == 3.9
    assert "mask_theta_low" not in denoise
    detect = json.loads((params / "parameters_detecting.json").read_text())
    assert detect["vertical_rho_mode"] == "w2_offset_band"
    assert detect["vertical_rho_spacing_mm"] == 1850
    assert detect["prompt_logic"] == "t12_pattern"
    sam = json.loads((params / "parameters_sam.json").read_text())
    assert sam["geometry_profile"] == "t45"
    assert sam["segment_per_ring"] == 7
    assert sam["segment_width"] == 1800
    assert "A4" in sam["segment_order"]


def test_resolve_params_dir_t45():
    from sam4tun.pipeline import _resolve_params_dir, _script_dir

    assert _resolve_params_dir("t4&5", None) == (
        REPO / "anchors" / "t4&5" / "4-1"
    ).resolve()
    assert _resolve_params_dir("t45", None) == (
        REPO / "anchors" / "t4&5" / "4-1"
    ).resolve()
    assert _script_dir("t4&5") == (REPO / "anchors" / "t4&5").resolve()
    assert _script_dir("t45") == (REPO / "anchors" / "t4&5").resolve()


def test_cli_profile_t45_dry_run(tmp_path):
    from sam4tun.pipeline import main

    cloud = tmp_path / "toy.txt"
    cloud.write_text("0 0 0 0 0 0\n")
    out = tmp_path / "t45-toy"
    main([str(cloud), str(out), "--profile", "t4&5", "--dry-run"])
    assert out.is_dir()


def test_t45_geometry_shapes():
    import sys

    sys.path.insert(0, str(REPO / "anchors" / "t4&5"))
    import t45_geometry

    verts = t45_geometry.template_vertices_mm(0.0, 0.0, "K")
    assert verts.shape == (4, 2)
    assert abs(verts[0, 0] + 900) < 1e-6
    pts, labels = t45_geometry.prompt_points_mm(0.0, 0.0, "K")
    assert len(pts) == len(labels) == 49
    assert int((labels == 0).sum()) == 29
    pts_a, labels_a = t45_geometry.prompt_points_mm(0.0, 0.0, "A4")
    assert len(pts_a) == len(labels_a) == 81


def test_t45_profile_uses_family_scripts():
    from sam4tun.pipeline import _script_dir

    t45 = (REPO / "anchors" / "t4&5").resolve()
    assert _script_dir("t4&5") == t45
    for stage in (
        "1_unfolding.py",
        "2_denoising.py",
        "3_enhancing.py",
        "4_detection.py",
        "5_sam.py",
        "6_evaluation.py",
    ):
        assert (t45 / stage).is_file()
    assert (t45 / "t45_geometry.py").is_file()
