"""T3 profile, flags, and CLI contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
SAM4TUN = REPO / "sam4tun"


@pytest.fixture(autouse=True)
def _sys_path(monkeypatch):
    monkeypatch.syspath_prepend(str(SAM4TUN))
    monkeypatch.syspath_prepend(str(REPO))
    for key in ("PROXY4TUN_OUT_ROOT", "PROXY4TUN_INPUT_TXT", "PROXY4TUN_PARAMS_DIR"):
        monkeypatch.delenv(key, raising=False)


def test_canonical_t3_parameters_exist():
    params = REPO / "anchors" / "t3" / "3-1-1"
    for stage in ("unfolding", "denoising", "enhancing", "detecting", "sam"):
        path = params / f"parameters_{stage}.json"
        assert path.is_file(), path
    unfolding = json.loads((params / "parameters_unfolding.json").read_text())
    assert unfolding["diameter"] == 5.9
    assert unfolding["polynomial_degree"] == 2
    assert unfolding["canonical_orientation"] is True
    assert unfolding["h_ring_sign"] == -1
    assert unfolding["random_seed"] == 1
    # Centreline residual recentring compensates for the degree-2 fit on short
    # subsets; without it the narrow T3 denoising r-band discards ~46% of points.
    assert unfolding["residual_recentre"] is True
    assert unfolding["recentre_bin_size"] == 0.5
    denoise = json.loads((params / "parameters_denoising.json").read_text())
    assert denoise["mask_theta_high_column"] == "theta"
    sam = json.loads((params / "parameters_sam.json").read_text())
    assert sam["geometry_profile"] == "t3"
    assert sam["K_height"] == 823.8
    assert sam["segment_order"] == ["K", "B2", "A3", "A2", "A1", "B1"]


def test_resolve_params_dir_t3():
    from sam4tun.pipeline import _resolve_params_dir

    assert _resolve_params_dir("t3", None) == (
        REPO / "anchors" / "t3" / "3-1-1"
    ).resolve()


def test_cli_profile_t3_dry_run(tmp_path):
    from sam4tun.pipeline import main

    cloud = tmp_path / "toy.txt"
    cloud.write_text("0 0 0 0 0 0\n")
    out = tmp_path / "t3-toy"
    main([str(cloud), str(out), "--profile", "t3", "--dry-run"])
    assert out.is_dir()


def test_t3_geometry_shapes():
    import sys

    sys.path.insert(0, str(REPO / "anchors" / "t3"))
    import t3_geometry

    verts = t3_geometry.template_vertices_mm(0.0, 0.0, "K")
    assert verts.shape == (4, 2)
    pts, labels = t3_geometry.prompt_points_mm(0.0, 0.0, "K")
    assert len(pts) == len(labels) == 45
    assert int((labels == 0).sum()) == 27


def test_t3_profile_uses_family_scripts():
    from sam4tun.pipeline import _script_dir

    t3 = (REPO / "anchors" / "t3").resolve()
    assert _script_dir("t3") == t3
    for stage in (
        "1_unfolding.py",
        "2_denoising.py",
        "3_enhancing.py",
        "4_detection.py",
        "5_sam.py",
        "6_evaluation.py",
    ):
        assert (t3 / stage).is_file()
    assert (t3 / "t3_geometry.py").is_file()


def test_theta_gate_semantics():
    """Corrected uses theta column; literal notebook uses r for the high clause."""
    theta = np.array([1.0, 10.0, 18.0])
    r = np.array([2.9, 2.9, 2.9])
    low, high = 1.55, 17.15
    corrected = (theta < low) | (theta > high)
    literal = (theta < low) | (r > high)
    assert corrected.tolist() == [True, False, True]
    assert literal.tolist() == [True, False, False]


def test_asymmetric_coverage_window():
    x_min, x_max = 0.0, 12.0
    ring_count = 10
    factor = 1.2
    n0, n1 = 2, 8
    high_lo = x_min + factor * n0
    high_hi = x_max - factor * (ring_count - n1)
    assert high_lo == pytest.approx(2.4)
    assert high_hi == pytest.approx(9.6)
