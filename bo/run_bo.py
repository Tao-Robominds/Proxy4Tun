#!/usr/bin/env python3
"""GP-based BO campaign for GT-free mIoU proxy discovery.

Outputs under data/<case>-bo-proxy/ (never data/anchors, data/baseline, data/bo).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BO_DIR))

from intrinsics import (  # noqa: E402
    extract_intrinsics,
    has_complete_tier1,
    write_intrinsics,
)
from param_io import load_anchor_params, materialize_run_params  # noqa: E402
from spaces import (  # noqa: E402
    CASE_CONFIG,
    anchor_vector,
    decode_vector,
    denormalize,
    normalize,
    space_for_case,
)

VENV_PY = REPO_ROOT / "venv" / "bin" / "python"
STAGE_SCRIPTS = {
    1: "1_unfolding.py",
    2: "2_denoising.py",
    3: "3_enhancing.py",
    4: "4_detection.py",
    5: "5_sam.py",
    6: "6_evaluation.py",
}
PROFILE_SCRIPT_DIR = {
    "t1&2": REPO_ROOT / "anchors" / "t1&2",
    "t3": REPO_ROOT / "anchors" / "t3",
    "t4&5": REPO_ROOT / "anchors" / "t4&5",
}
CHECKPOINT_FILES = [
    "state.pkl",
    "unwrapped.csv",
    "projected_point_cloud_bbox.png",
    "slice_point_cloud_2d.png",
    "ellipse_centres_3d.png",
    "tunnel_centre_curve_3d.png",
]
MIoU_RE = re.compile(r"Mean IoU \(mIoU\):\s*([\d.]+)")


@dataclass
class TrialRecord:
    trial_id: str
    acquisition: str
    x: list[float]
    overlay: dict[str, dict[str, Any]]
    mIoU: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    elapsed_s: float = 0.0
    status: str = "pending"
    output_dir: str = ""
    log_path: str = ""
    start_stage: int = 1


def trial_run_id(case: str, index: int | str) -> str:
    """Run directory name must keep the tunnel-id prefix (e.g. '5-1-…').

    T4/T5 geometric SAM fallback keys off ``tunnel_id.split('-')[0]`` in
    ``anchors/t4&5/5_sam.py``. Plain ``trial_000`` would skip the fallback.
    """
    if isinstance(index, int):
        return f"{case}-t{index:03d}"
    return f"{case}-{index}"


def parse_miou(perf_path: Path) -> float | None:
    if not perf_path.exists():
        return None
    text = perf_path.read_text(encoding="utf-8")
    m = MIoU_RE.search(text)
    return float(m.group(1)) if m else None


def parse_performance(perf_path: Path) -> dict[str, float]:
    if not perf_path.exists():
        return {}
    text = perf_path.read_text(encoding="utf-8")
    out: dict[str, float] = {}
    patterns = {
        "OA": r"Overall Accuracy \(OA\):\s*([\d.]+)",
        "F1": r"F1 Score:\s*([\d.]+)",
        "mIoU": r"Mean IoU \(mIoU\):\s*([\d.]+)",
        "mAP": r"mAP:\s*([\d.]+)",
    }
    for k, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            out[k] = float(m.group(1))
    return out


class BOCampaign:
    def __init__(
        self,
        case: str,
        *,
        n_trials: int = 40,
        n_init: int = 12,
        study_root: Path | None = None,
        seed: int = 0,
    ):
        if case not in CASE_CONFIG:
            raise ValueError(f"Unknown case {case}; choose from {sorted(CASE_CONFIG)}")
        self.case = case
        self.cfg = CASE_CONFIG[case]
        self.n_trials = n_trials
        self.n_init = n_init
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.dims = space_for_case(case)
        self.profile = self.cfg["profile"]
        self.script_dir = PROFILE_SCRIPT_DIR[self.profile]
        self.params_base = load_anchor_params(REPO_ROOT / self.cfg["params_dir"])
        self.input_txt = REPO_ROOT / self.cfg["input_txt"]
        self.study_root = (
            Path(study_root).resolve()
            if study_root
            else (REPO_ROOT / "data" / f"{case}-bo-proxy").resolve()
        )
        self.runs_root = self.study_root / "runs"
        self.params_root = self.study_root / "params"
        self.logs_root = self.study_root / "logs"
        self.ckpt_dir = self.study_root / "checkpoints" / "after_1"
        for d in (self.runs_root, self.params_root, self.logs_root, self.ckpt_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.study_root / "manifest.json"
        self.trials: list[TrialRecord] = []
        self._load_manifest()

    def _load_manifest(self) -> None:
        if not self.manifest_path.exists():
            return
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.trials = [TrialRecord(**t) for t in data.get("trials", [])]

    def save_manifest(self) -> None:
        payload = {
            "case": self.case,
            "profile": self.profile,
            "study_root": str(self.study_root),
            "n_trials": self.n_trials,
            "n_init": self.n_init,
            "seed": self.seed,
            "dims": [d.name for d in self.dims],
            "anchor_miou": self.cfg["anchor_miou"],
            "created_at": datetime.now().isoformat(),
            "trials": [asdict(t) for t in self.trials],
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        # Flat results CSV
        rows = []
        for t in self.trials:
            row = {
                "trial_id": t.trial_id,
                "acquisition": t.acquisition,
                "status": t.status,
                "mIoU": t.mIoU if t.mIoU is not None else "",
                "elapsed_s": f"{t.elapsed_s:.1f}",
            }
            for k, v in (t.metrics or {}).items():
                if k in ("tier0_keys", "tier1_keys"):
                    continue
                row[k] = v if v is not None else ""
            rows.append(row)
        if rows:
            import csv

            keys = list(rows[0].keys())
            with open(self.study_root / "results.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)

    def _env(self, params_dir: Path, out_root: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        env["PROXY4TUN_OUT_ROOT"] = str(out_root.resolve())
        env["PROXY4TUN_INPUT_TXT"] = str(self.input_txt.resolve())
        env["PROXY4TUN_PARAMS_DIR"] = str(params_dir.resolve())
        env["PYTHONPATH"] = os.pathsep.join(
            [
                str(self.script_dir),
                str(REPO_ROOT / "sam4tun"),
                str(REPO_ROOT / "sam4tun" / "segment-anything"),
                env.get("PYTHONPATH", ""),
            ]
        ).rstrip(os.pathsep)
        return env

    def _run_stages(
        self,
        run_id: str,
        params_dir: Path,
        start_stage: int,
        end_stage: int = 6,
    ) -> tuple[str, float]:
        log_path = self.logs_root / f"{run_id}.log"
        t0 = time.time()
        lines: list[str] = []
        env = self._env(params_dir, self.runs_root)
        for stage in range(start_stage, end_stage + 1):
            script = self.script_dir / STAGE_SCRIPTS[stage]
            lines.append(f"\n=== stage {stage}: {script.name} ===\n")
            proc = subprocess.run(
                [str(VENV_PY), "-u", str(script), run_id],
                cwd=str(REPO_ROOT),
                env=env,
                capture_output=True,
                text=True,
            )
            lines.append(proc.stdout or "")
            if proc.stderr:
                lines.append(proc.stderr)
            if proc.returncode != 0:
                lines.append(f"\nFAILED stage {stage} exit={proc.returncode}\n")
                log_path.write_text("".join(lines), encoding="utf-8")
                raise RuntimeError(f"Stage {stage} failed for {run_id}; see {log_path}")
        elapsed = time.time() - t0
        text = "".join(lines)
        log_path.write_text(text, encoding="utf-8")
        return text, elapsed

    def _seed_unfolding_params(self, params_dir: Path, seed: int = 1) -> None:
        """Ensure unfolding JSON has random_seed for reproducible stage 1."""
        path = Path(params_dir) / "parameters_unfolding.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["random_seed"] = int(seed)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def ensure_stage1_checkpoint(self, *, prefer_frozen_anchor: bool = True) -> None:
        marker = self.ckpt_dir / "state.pkl"
        if marker.exists() and (self.ckpt_dir / "unwrapped.csv").exists():
            print(f"Stage-1 checkpoint exists: {self.ckpt_dir}")
            return

        # Prefer the promoted frozen anchor stage-1 artifacts (read-only copy).
        # This removes unseeded RANSAC variance from the campaign baseline.
        frozen = REPO_ROOT / "data" / "anchors" / self.case
        if prefer_frozen_anchor and (frozen / "state.pkl").exists() and (frozen / "unwrapped.csv").exists():
            for fname in CHECKPOINT_FILES:
                src = frozen / fname
                if src.exists():
                    shutil.copy2(src, self.ckpt_dir / fname)
            meta = {
                "source": str(frozen),
                "mode": "copy_from_frozen_anchor",
                "case": self.case,
            }
            (self.ckpt_dir / "checkpoint_meta.json").write_text(
                json.dumps(meta, indent=2) + "\n", encoding="utf-8"
            )
            print(f"Stage-1 checkpoint copied from frozen anchor {frozen}")
            return

        run_id = "_stage1_seed"
        params_dir = materialize_run_params(self.params_root / run_id, self.params_base, None)
        self._seed_unfolding_params(params_dir, seed=1)
        run_dir = self.runs_root / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"Building stage-1 checkpoint for {self.case} (random_seed=1)...")
        log_text, _ = self._run_stages(run_id, params_dir, start_stage=1, end_stage=1)
        if "Canonical invariant" in log_text:
            print("Canonical invariant line found in stage-1 log.")
        for fname in CHECKPOINT_FILES:
            src = run_dir / fname
            if src.exists():
                shutil.copy2(src, self.ckpt_dir / fname)
        if not (self.ckpt_dir / "state.pkl").exists():
            raise RuntimeError(f"Failed to create stage-1 checkpoint in {self.ckpt_dir}")
        print(f"Saved checkpoint -> {self.ckpt_dir}")

    def _restore_checkpoint(self, run_id: str) -> None:
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        for fname in CHECKPOINT_FILES:
            src = self.ckpt_dir / fname
            if src.exists():
                shutil.copy2(src, run_dir / fname)

    def run_trial(
        self,
        trial_id: str,
        x: list[float],
        acquisition: str,
        *,
        full_pipeline: bool = False,
        force: bool = False,
    ) -> TrialRecord:
        existing = next((t for t in self.trials if t.trial_id == trial_id), None)
        if existing and existing.status == "ok" and not force:
            return existing

        overlay = decode_vector(self.dims, x, self.params_base)
        params_dir = materialize_run_params(
            self.params_root / trial_id, self.params_base, overlay
        )
        start_stage = 1 if full_pipeline else 2
        if not full_pipeline:
            self.ensure_stage1_checkpoint()
            self._restore_checkpoint(trial_id)
        else:
            run_dir = self.runs_root / trial_id
            if run_dir.exists() and force:
                shutil.rmtree(run_dir)
            run_dir.mkdir(parents=True, exist_ok=True)

        try:
            log_text, elapsed = self._run_stages(
                trial_id, params_dir, start_stage=start_stage, end_stage=6
            )
            status = "ok"
        except RuntimeError as exc:
            print(f"FAILED {trial_id}: {exc}")
            log_text = ""
            log_path = self.logs_root / f"{trial_id}.log"
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8")
            elapsed = 0.0
            status = "failed"

        run_dir = self.runs_root / trial_id
        perf = parse_performance(run_dir / "evaluation" / "performance.md")
        miou = perf.get("mIoU")
        metrics = extract_intrinsics(
            run_dir,
            params_dir=params_dir,
            log_text=log_text,
            expected_rings=int(self.cfg["expected_rings"]),
        )
        metrics.update({f"perf_{k}": v for k, v in perf.items()})
        write_intrinsics(run_dir, metrics)

        rec = TrialRecord(
            trial_id=trial_id,
            acquisition=acquisition,
            x=[float(v) for v in x],
            overlay=overlay,
            mIoU=miou,
            metrics=metrics,
            elapsed_s=elapsed,
            status=status if miou is not None else ("failed" if status == "ok" else status),
            output_dir=str(run_dir),
            log_path=str(self.logs_root / f"{trial_id}.log"),
            start_stage=start_stage,
        )
        # Replace or append
        self.trials = [t for t in self.trials if t.trial_id != trial_id]
        self.trials.append(rec)
        self.save_manifest()
        print(
            f"{trial_id} [{acquisition}] status={rec.status} mIoU={rec.mIoU} "
            f"elapsed={elapsed:.1f}s tier1_ok={has_complete_tier1(metrics)}"
        )
        return rec

    def _sobol_like_init(self, n: int) -> list[list[float]]:
        """Sobol if available, else scrambled Latin-ish random in unit cube."""
        try:
            from scipy.stats import qmc

            eng = qmc.Sobol(d=len(self.dims), scramble=True, seed=self.seed)
            # Sobol prefers power-of-two; draw next power and trim
            m = max(1, int(math.ceil(math.log2(max(n, 2)))))
            sample = eng.random_base2(m)[:n]
        except Exception:
            sample = self.rng.random((n, len(self.dims)))
        return [denormalize(self.dims, list(row)) for row in sample]

    def _fit_gp(self) -> GaussianProcessRegressor | None:
        ok = [t for t in self.trials if t.status == "ok" and t.mIoU is not None]
        if len(ok) < 3:
            return None
        X = np.asarray([normalize(self.dims, t.x) for t in ok], dtype=float)
        y = np.asarray([t.mIoU for t in ok], dtype=float)
        kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(
            length_scale=np.ones(X.shape[1]),
            length_scale_bounds=(1e-2, 1e2),
            nu=2.5,
        ) + WhiteKernel(noise_level=1e-3, noise_level_bounds=(1e-6, 1e-1))
        gp = GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            n_restarts_optimizer=3,
            random_state=self.seed,
        )
        gp.fit(X, y)
        return gp

    def _propose(self, gp: GaussianProcessRegressor, mode: str, n_cand: int = 2048) -> list[float]:
        cand = self.rng.random((n_cand, len(self.dims)))
        mu, sigma = gp.predict(cand, return_std=True)
        sigma = np.maximum(sigma, 1e-9)
        if mode == "ei":
            y_best = max(t.mIoU for t in self.trials if t.mIoU is not None)
            z = (mu - y_best) / sigma
            ei = (mu - y_best) * norm.cdf(z) + sigma * norm.pdf(z)
            idx = int(np.argmax(ei))
        else:  # uncertainty
            idx = int(np.argmax(sigma))
        return denormalize(self.dims, list(cand[idx]))

    def run_gate(self, *, force: bool = False) -> dict[str, Any]:
        """Single-instance validation using frozen-anchor stage-1 + stages 2–6.

        Full stages 1–6 are stochastic without a historically frozen seed. The
        gate therefore reuses the promoted `data/anchors/<case>/` stage-1
        artifacts (read-only copy) and re-runs stages 2–6 with anchor params.
        Pass if mIoU is within 0.02 of the promoted canonical value.
        """
        x0 = anchor_vector(self.case, REPO_ROOT)
        # Force refresh of checkpoint from frozen anchor
        if force and self.ckpt_dir.exists():
            shutil.rmtree(self.ckpt_dir)
            self.ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_stage1_checkpoint(prefer_frozen_anchor=True)
        tid = trial_run_id(self.case, 0)
        rec = self.run_trial(
            tid, x0, "anchor_from_frozen_stage1", full_pipeline=False, force=force
        )
        target = float(self.cfg["anchor_miou"])
        miou = rec.mIoU if rec.mIoU is not None else float("nan")
        delta = abs(miou - target) if math.isfinite(miou) else float("inf")
        inv_ok = rec.metrics.get("orient_invariant_ok") == 1.0
        tier1_ok = has_complete_tier1(rec.metrics)
        if not inv_ok and rec.metrics.get("orient_h_ring_corr") is not None:
            corr = float(rec.metrics["orient_h_ring_corr"])
            h_sign = int(self.params_base["unfolding"].get("h_ring_sign", 1))
            inv_ok = (np.sign(corr) == np.sign(h_sign)) and abs(corr) > 0.5
        passed = (
            rec.status == "ok"
            and math.isfinite(miou)
            and delta <= 0.02
            and inv_ok
            and tier1_ok
        )
        cmd = (
            f"copy stage-1 from data/anchors/{self.case} → checkpoints/after_1; "
            f"then stages 2-6 via bo/run_bo.py with params {self.cfg['params_dir']}"
        )
        gate = {
            "case": self.case,
            "command": cmd,
            "lineage": (
                "bo/run_bo.py --gate: frozen data/anchors/<case> stage-1 checkpoint "
                "+ stages 2-6 with anchor params (avoids unseeded RANSAC drift)"
            ),
            "target_mIoU": target,
            "measured_mIoU": miou,
            "delta_mIoU": delta if math.isfinite(delta) else None,
            "pass_miou_tol": bool(delta <= 0.02),
            "orient_h_ring_corr": rec.metrics.get("orient_h_ring_corr"),
            "orient_invariant_ok": inv_ok,
            "tier1_complete": tier1_ok,
            "stage1_checkpoint_source": str(REPO_ROOT / "data" / "anchors" / self.case),
            "pass_fail_criteria": {
                "pipeline_ok": rec.status == "ok",
                "miou_within_0.02_of_anchor": bool(delta <= 0.02),
                "canonical_invariant_passed": inv_ok,
                "intrinsics_tier1_no_nan": tier1_ok,
            },
            "passed": passed,
            "evidence_path": str(self.study_root / "validation_gate.json"),
            "output_dir": rec.output_dir,
            "log_path": rec.log_path,
            "intrinsics_path": str(Path(rec.output_dir) / "intrinsics.json"),
            "performance_path": str(Path(rec.output_dir) / "evaluation" / "performance.md"),
        }
        gate_path = self.study_root / "validation_gate.json"
        gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(gate, indent=2))
        if not passed:
            raise RuntimeError(f"Validation gate FAILED for {self.case}; see {gate_path}")
        return gate

    def run_campaign(self, *, skip_gate: bool = False) -> None:
        if not skip_gate:
            gate_path = self.study_root / "validation_gate.json"
            if not gate_path.exists() or not json.loads(gate_path.read_text()).get("passed"):
                self.run_gate()
            else:
                print(f"Gate already passed: {gate_path}")
                # Ensure checkpoint from trial_000
                t0 = self.runs_root / "trial_000"
                if (t0 / "state.pkl").exists() and not (self.ckpt_dir / "state.pkl").exists():
                    for fname in CHECKPOINT_FILES:
                        src = t0 / fname
                        if src.exists():
                            shutil.copy2(src, self.ckpt_dir / fname)

        self.ensure_stage1_checkpoint()

        # Trial 0 already done as gate; fill init then BO
        done_ids = {t.trial_id for t in self.trials if t.status == "ok"}
        init_xs = self._sobol_like_init(self.n_init - 1)
        for i, x in enumerate(init_xs, start=1):
            tid = trial_run_id(self.case, i)
            if tid in done_ids:
                continue
            self.run_trial(tid, x, "sobol_init", full_pipeline=False)

        for i in range(self.n_init, self.n_trials):
            tid = trial_run_id(self.case, i)
            if tid in done_ids:
                continue
            gp = self._fit_gp()
            mode = "ei" if ((i - self.n_init) % 2 == 0) else "uncertainty"
            if gp is None:
                x = denormalize(self.dims, list(self.rng.random(len(self.dims))))
                acq = "random_fallback"
            else:
                x = self._propose(gp, mode)
                acq = mode
            self.run_trial(tid, x, acq, full_pipeline=False)

        print(f"Campaign complete: {self.study_root}")
        ok = [t for t in self.trials if t.status == "ok" and t.mIoU is not None]
        if ok:
            mious = [t.mIoU for t in ok]
            print(
                f"  n_ok={len(ok)} mIoU min={min(mious):.3f} "
                f"max={max(mious):.3f} mean={sum(mious)/len(mious):.3f}"
            )


def run_repeatability(case: str, *, n_anchor: int = 4, study_root: Path | None = None) -> None:
    """Anchor x n_anchor with varying random_seed + 1 degraded config; full stages 1-6."""
    camp = BOCampaign(case, study_root=study_root)
    base = camp.params_base
    x_anchor = anchor_vector(case, REPO_ROOT)
    x_deg = list(x_anchor)
    for j, d in enumerate(camp.dims):
        if d.name.startswith("hough_threshold") or d.name == "binary_threshold":
            x_deg[j] = d.high
        if d.name in ("curvature_threshold", "mask_r_low"):
            x_deg[j] = d.low

    for i in range(n_anchor):
        tid = trial_run_id(case, f"rep{i}")
        existing = next((t for t in camp.trials if t.trial_id == tid and t.status == "ok"), None)
        if existing:
            continue
        seed = int(10 + i)
        overlay = decode_vector(camp.dims, x_anchor, base)
        overlay.setdefault("unfolding", {})["random_seed"] = seed
        params_dir = materialize_run_params(camp.params_root / tid, base, overlay)
        u = json.loads((params_dir / "parameters_unfolding.json").read_text(encoding="utf-8"))
        u["random_seed"] = seed
        (params_dir / "parameters_unfolding.json").write_text(
            json.dumps(u, indent=2) + "\n", encoding="utf-8"
        )
        run_dir = camp.runs_root / tid
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            log_text, elapsed = camp._run_stages(tid, params_dir, start_stage=1, end_stage=6)
            status = "ok"
        except RuntimeError as exc:
            print(f"FAILED {tid}: {exc}")
            log_text = ""
            log_path = camp.logs_root / f"{tid}.log"
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8")
            elapsed = 0.0
            status = "failed"
        perf = parse_performance(run_dir / "evaluation" / "performance.md")
        miou = perf.get("mIoU")
        metrics = extract_intrinsics(
            run_dir,
            params_dir=params_dir,
            log_text=log_text,
            expected_rings=int(camp.cfg["expected_rings"]),
        )
        write_intrinsics(run_dir, metrics)
        rec = TrialRecord(
            trial_id=tid,
            acquisition=f"repeat_seed_{seed}",
            x=[float(v) for v in x_anchor],
            overlay=overlay,
            mIoU=miou,
            metrics=metrics,
            elapsed_s=elapsed,
            status=status if miou is not None else "failed",
            output_dir=str(run_dir),
            log_path=str(camp.logs_root / f"{tid}.log"),
            start_stage=1,
        )
        camp.trials = [t for t in camp.trials if t.trial_id != tid]
        camp.trials.append(rec)
        camp.save_manifest()
        print(f"{tid} mIoU={miou} seed={seed}")

    camp.run_trial(
        trial_run_id(case, "deg"), x_deg, "repeat_degraded", full_pipeline=True, force=False
    )
    print(f"Repeatability done for {case}")


def main() -> None:
    p = argparse.ArgumentParser(description="BO proxy experiment runner")
    p.add_argument("--case", choices=sorted(CASE_CONFIG), required=True)
    p.add_argument("--gate", action="store_true", help="Run single-instance validation gate only")
    p.add_argument("--campaign", action="store_true", help="Run full BO campaign")
    p.add_argument("--repeats", action="store_true", help="Run repeatability suite")
    p.add_argument("--n-trials", type=int, default=40)
    p.add_argument("--n-init", type=int, default=12)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--study-root", type=Path, default=None)
    p.add_argument("--force-gate", action="store_true")
    p.add_argument("--skip-gate", action="store_true")
    args = p.parse_args()

    camp = BOCampaign(
        args.case,
        n_trials=args.n_trials,
        n_init=args.n_init,
        study_root=args.study_root,
        seed=args.seed,
    )
    print(f"Study root: {camp.study_root}  dims={len(camp.dims)}")

    if args.gate:
        camp.run_gate(force=args.force_gate)
        return
    if args.repeats:
        run_repeatability(args.case, study_root=args.study_root)
        return
    if args.campaign or not (args.gate or args.repeats):
        camp.run_campaign(skip_gate=args.skip_gate)


if __name__ == "__main__":
    main()
