#!/usr/bin/env python3
"""Train-case runner for bo-unified (gates + optional stage-1 checkpointed trials).

Outputs under data/bo-unified/<case>-bo-proxy/ (never data/bo, data/anchors).
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
BO_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BO_DIR))

from intrinsics import extract_intrinsics, has_complete_tier1, write_intrinsics  # noqa: E402
from param_io import load_anchor_params, load_family_params, materialize_run_params  # noqa: E402
from pipeline import (  # noqa: E402
    DATA_ROOT,
    copy_checkpoint,
    parse_performance,
    run_stages,
    trial_run_id,
)
from spaces import CASE_CONFIG, anchor_vector, decode_vector, space_for_case  # noqa: E402


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


class BOCampaign:
    def __init__(self, case: str, *, study_root: Path | None = None):
        if case not in CASE_CONFIG:
            raise ValueError(f"Unknown case {case}; choose from {sorted(CASE_CONFIG)}")
        self.case = case
        self.cfg = CASE_CONFIG[case]
        self.dims = space_for_case(case)
        self.params_dir_src = REPO_ROOT / self.cfg["params_dir"]
        self.params_base = load_anchor_params(self.params_dir_src)
        self.family_params = load_family_params(self.params_dir_src)
        self.input_txt = REPO_ROOT / self.cfg["input_txt"]
        self.study_root = (
            Path(study_root).resolve()
            if study_root
            else (DATA_ROOT / f"{case}-bo-proxy").resolve()
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
            "profile": "unified",
            "study_root": str(self.study_root),
            "dims": [d.name for d in self.dims],
            "anchor_miou": self.cfg["anchor_miou"],
            "unified_ref_miou": self.cfg.get("unified_ref_miou"),
            "created_at": datetime.now().isoformat(),
            "trials": [asdict(t) for t in self.trials],
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _materialize(self, run_id: str, overlay: dict[str, dict[str, Any]] | None = None) -> Path:
        return materialize_run_params(
            self.params_root / run_id,
            self.params_base,
            overlay,
            family_params=self.family_params,
        )

    def ensure_stage1_checkpoint(self) -> None:
        marker = self.ckpt_dir / "state.pkl"
        if marker.exists() and (self.ckpt_dir / "unwrapped.csv").exists():
            print(f"Stage-1 checkpoint exists: {self.ckpt_dir}")
            return

        # Prefer prior unified stage-1 artifacts (determinism already baked in).
        u_out = self.cfg.get("unified_out")
        if u_out:
            unified = REPO_ROOT / "data" / "unified" / u_out
            if (unified / "state.pkl").exists() and (unified / "unwrapped.csv").exists():
                n = copy_checkpoint(unified, self.ckpt_dir)
                meta = {
                    "source": str(unified),
                    "mode": "copy_from_data_unified",
                    "n_files": n,
                }
                (self.ckpt_dir / "checkpoint_meta.json").write_text(
                    json.dumps(meta, indent=2) + "\n", encoding="utf-8"
                )
                print(f"Stage-1 checkpoint copied from {unified}")
                return

        run_id = "_stage1"
        params_dir = self._materialize(run_id, None)
        run_dir = self.runs_root / run_id
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"Building stage-1 checkpoint for {self.case} via unified pipeline...")
        log_path = self.logs_root / f"{run_id}.log"
        run_stages(
            run_id=run_id,
            params_dir=params_dir,
            input_txt=self.input_txt,
            out_root=self.runs_root,
            log_path=log_path,
            start_stage=1,
            end_stage=1,
        )
        copy_checkpoint(run_dir, self.ckpt_dir)
        if not (self.ckpt_dir / "state.pkl").exists():
            raise RuntimeError(f"Failed to create stage-1 checkpoint in {self.ckpt_dir}")
        print(f"Saved checkpoint -> {self.ckpt_dir}")

    def run_full(
        self,
        trial_id: str,
        acquisition: str,
        *,
        overlay: dict[str, dict[str, Any]] | None = None,
        force: bool = False,
    ) -> TrialRecord:
        existing = next((t for t in self.trials if t.trial_id == trial_id), None)
        if existing and existing.status == "ok" and not force:
            return existing

        params_dir = self._materialize(trial_id, overlay)
        run_dir = self.runs_root / trial_id
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.logs_root / f"{trial_id}.log"

        try:
            log_text, elapsed = run_stages(
                run_id=trial_id,
                params_dir=params_dir,
                input_txt=self.input_txt,
                out_root=self.runs_root,
                log_path=log_path,
                start_stage=1,
                end_stage=6,
            )
            status = "ok"
        except RuntimeError as exc:
            print(f"FAILED {trial_id}: {exc}")
            log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            elapsed = 0.0
            status = "failed"

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

        x = anchor_vector(self.case, REPO_ROOT) if overlay is None else []
        if overlay is not None and not x:
            try:
                from spaces import encode_params

                x = encode_params(self.dims, overlay, self.params_base)
            except Exception:
                x = []

        rec = TrialRecord(
            trial_id=trial_id,
            acquisition=acquisition,
            x=[float(v) for v in x],
            overlay=overlay or {},
            mIoU=miou,
            metrics=metrics,
            elapsed_s=elapsed,
            status=status if miou is not None else ("failed" if status == "ok" else status),
            output_dir=str(run_dir),
            log_path=str(log_path),
            start_stage=1,
        )
        self.trials = [t for t in self.trials if t.trial_id != trial_id]
        self.trials.append(rec)
        self.save_manifest()
        print(
            f"{trial_id} [{acquisition}] status={rec.status} mIoU={rec.mIoU} "
            f"elapsed={elapsed:.1f}s tier1_ok={has_complete_tier1(metrics)}"
        )
        return rec

    def run_gate(self, *, force: bool = False) -> dict[str, Any]:
        """Gate A: reuse data/unified stage-1, re-run stages 2–6.

        1-1/2-1 params omit random_seed, so a full 1–6 re-run is not a fair
        parity check. Copying the promoted unified stage-1 and replaying 2–6
        validates the bo-unified driver seam against data/unified/<case>.
        """
        tid = trial_run_id(self.case, "gate")
        u_out = self.cfg.get("unified_out")
        if not u_out:
            raise RuntimeError(f"No unified_out mapping for train gate case {self.case}")
        unified = REPO_ROOT / "data" / "unified" / u_out
        if not (unified / "state.pkl").exists():
            raise FileNotFoundError(f"Missing unified stage-1 at {unified}")

        params_dir = self._materialize(tid, None)
        run_dir = self.runs_root / tid
        if run_dir.exists():
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        copy_checkpoint(unified, run_dir)
        log_path = self.logs_root / f"{tid}.log"

        try:
            log_text, elapsed = run_stages(
                run_id=tid,
                params_dir=params_dir,
                input_txt=self.input_txt,
                out_root=self.runs_root,
                log_path=log_path,
                start_stage=2,
                end_stage=6,
            )
            status = "ok"
        except RuntimeError as exc:
            print(f"FAILED {tid}: {exc}")
            log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            elapsed = 0.0
            status = "failed"

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
            trial_id=tid,
            acquisition="unified_stage1_replay_2to6",
            x=anchor_vector(self.case, REPO_ROOT),
            overlay={},
            mIoU=miou,
            metrics=metrics,
            elapsed_s=elapsed,
            status=status if miou is not None else "failed",
            output_dir=str(run_dir),
            log_path=str(log_path),
            start_stage=2,
        )
        self.trials = [t for t in self.trials if t.trial_id != tid]
        self.trials.append(rec)
        self.save_manifest()

        target_raw = self.cfg.get("unified_ref_miou")
        if target_raw is None:
            target_raw = self.cfg.get("anchor_miou")
        target = float(target_raw) if target_raw is not None else float("nan")
        miou_f = rec.mIoU if rec.mIoU is not None else float("nan")
        delta = abs(miou_f - target) if math.isfinite(miou_f) and math.isfinite(target) else float("inf")
        inv_ok = rec.metrics.get("orient_invariant_ok") == 1.0
        tier1_ok = has_complete_tier1(rec.metrics)
        if not inv_ok and rec.metrics.get("orient_h_ring_corr") is not None:
            corr = float(rec.metrics["orient_h_ring_corr"])
            h_sign = int(self.params_base["unfolding"].get("h_ring_sign", 1))
            inv_ok = (np.sign(corr) == np.sign(h_sign)) and abs(corr) > 0.5
        miou_tol_ok = bool(math.isfinite(delta) and delta <= 0.02)
        passed = rec.status == "ok" and math.isfinite(miou_f) and miou_tol_ok and inv_ok and tier1_ok

        gate = {
            "case": self.case,
            "gate_kind": "train_parity",
            "command": (
                f"./venv/bin/python bo-unified/run_bo.py --case {self.case} --gate "
                f"# copy data/unified/{u_out} stage-1; stages 2–6 via anchors/unified"
            ),
            "lineage": (
                f"bo-unified gate: stage-1 from data/unified/{u_out} + "
                f"{self.cfg['params_dir']} stages 2–6 → "
                f"data/bo-unified/{self.case}-bo-proxy/runs/{tid}"
            ),
            "target_mIoU": target if math.isfinite(target) else None,
            "target_source": "unified_ref_miou" if self.cfg.get("unified_ref_miou") is not None else "anchor_miou",
            "measured_mIoU": miou_f if math.isfinite(miou_f) else None,
            "delta_mIoU": delta if math.isfinite(delta) else None,
            "pass_fail_criteria": {
                "pipeline_ok": rec.status == "ok",
                "miou_within_0.02_of_target": miou_tol_ok,
                "canonical_invariant_passed": inv_ok,
                "intrinsics_tier1_no_nan": tier1_ok,
            },
            "orient_h_ring_corr": rec.metrics.get("orient_h_ring_corr"),
            "orient_invariant_ok": inv_ok,
            "tier1_complete": tier1_ok,
            "passed": passed,
            "evidence_path": str(self.study_root / "validation_gate.json"),
            "output_dir": rec.output_dir,
            "log_path": rec.log_path,
        }
        gate_path = self.study_root / "validation_gate.json"
        gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
        fam_dir = BO_DIR / "family"
        fam_dir.mkdir(parents=True, exist_ok=True)
        (fam_dir / f"gate_{self.case}.json").write_text(
            json.dumps(gate, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(gate, indent=2))
        if not passed:
            raise RuntimeError(f"Validation gate FAILED for {self.case}; see {gate_path}")
        return gate


def main() -> None:
    p = argparse.ArgumentParser(description="bo-unified train-case runner")
    p.add_argument("--case", choices=sorted(CASE_CONFIG), required=True)
    p.add_argument("--gate", action="store_true", help="Run train-parity gate (full 1–6)")
    p.add_argument("--force", action="store_true")
    p.add_argument("--study-root", type=Path, default=None)
    args = p.parse_args()

    camp = BOCampaign(args.case, study_root=args.study_root)
    print(f"Study root: {camp.study_root}")
    if args.gate:
        camp.run_gate(force=args.force)
        return
    p.error("Specify --gate (campaigns reuse historical data/bo trials)")


if __name__ == "__main__":
    main()
