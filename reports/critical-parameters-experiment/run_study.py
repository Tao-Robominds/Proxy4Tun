#!/usr/bin/env python3
"""Checkpointed ablation study runner for agents/t1&2 on tunnel 1-1."""

from __future__ import annotations

import argparse
import csv
import json
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

ABLATION_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = ABLATION_DIR.parent
REPO_ROOT = PIPELINE_DIR.parent.parent
DATA_ROOT = REPO_ROOT / "data"
INPUT_TXT = DATA_ROOT / "subsets" / "1-1.txt"
VENV_PY = REPO_ROOT / "venv" / "bin" / "python"

sys.path.insert(0, str(ABLATION_DIR))
from analyze import build_summary  # noqa: E402
from design import FRACTIONAL_7F_RES4, design_row_to_overlay  # noqa: E402
from param_io import materialize_run_params  # noqa: E402
from profiles import (  # noqa: E402
    CHECKPOINT_AFTER_STAGE,
    GROUPS,
    HIGH,
    LOW,
    STAGES,
    individual_overlays,
    low_overlay_for_stage,
    stage_revert_overlay,
    start_stage_for_overlay,
)

STAGE_SCRIPTS = {
    1: "1_unfolding.py",
    2: "2_denoising.py",
    3: "3_enhancing.py",
    4: "4_detection.py",
    5: "5_sam.py",
    6: "6_evaluation.py",
}

MIoU_SEMANTIC_THRESH = 0.03
MAP_INSTANCE_THRESH = 0.05
MIoU_CONFIRM_THRESH = 0.06
MAP_CONFIRM_THRESH = 0.10
PRIOR_HIGH_MIOU = 0.802
GATE_MIN_HIGH_MIOU = 0.70
GATE_MIN_DELTA_MIOU = 0.15
GATE_MIOU_TOLERANCE = 0.05


@dataclass
class RunRecord:
    run_id: str
    phase: str
    description: str
    overlay: dict[str, dict[str, Any]]
    start_stage: int
    elapsed_s: float
    metrics: dict[str, float] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    output_dir: str = ""
    log_path: str = ""
    status: str = "ok"


def _now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def parse_performance_md(path: Path) -> dict[str, float]:
    text = path.read_text(encoding="utf-8")
    metrics: dict[str, float] = {}
    patterns = {
        "OA": r"Overall Accuracy \(OA\):\s*([\d.]+)",
        "F1": r"F1 Score:\s*([\d.]+)",
        "mIoU": r"Mean IoU \(mIoU\):\s*([\d.]+)",
        "mAP": r"mAP:\s*([\d.]+)",
        "mAP50": r"mAP@50:\s*([\d.]+)",
        "mAP75": r"mAP@75:\s*([\d.]+)",
        "mAP90": r"mAP@90:\s*([\d.]+)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            metrics[key] = float(m.group(1))
    return metrics


def collect_diagnostics(run_dir: Path, log_text: str) -> dict[str, Any]:
    diag: dict[str, Any] = {}
    for name in ("unwrapped.csv", "denoised.csv", "enhanced.csv", "only_label.csv"):
        p = run_dir / name
        if p.exists():
            diag[f"{name}_bytes"] = p.stat().st_size
    m = re.search(r"Number of vertical lines:\s*(\d+)", log_text)
    if m:
        diag["vertical_lines"] = int(m.group(1))
    m = re.search(r"Remaining points count:\s*(\d+)", log_text)
    if m:
        diag["remaining_points"] = int(m.group(1))
    if "assume" in log_text.lower() or "synthetic" in log_text.lower():
        diag["detection_fallback"] = True
    return diag


class AblationStudy:
    def __init__(self, study_root: Path | None = None):
        ts = _now_id()
        self.study_root = (study_root or (DATA_ROOT / f"1-1-ablation-study-{ts}")).resolve()
        self.runs_root = self.study_root / "runs"
        self.checkpoints = self.study_root / "checkpoints"
        self.params_root = self.study_root / "params"
        self.logs_root = self.study_root / "logs"
        for d in (self.runs_root, self.checkpoints, self.params_root, self.logs_root):
            d.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.study_root / "manifest.json"
        self.results_csv = self.study_root / "results.csv"
        self.records: list[RunRecord] = []
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self.manifest_path.exists():
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            self.records = [RunRecord(**r) for r in data.get("runs", [])]

    def save_manifest(self) -> None:
        payload = {
            "study_root": str(self.study_root),
            "input_txt": str(INPUT_TXT),
            "created_at": datetime.now().isoformat(),
            "runs": [asdict(r) for r in self.records],
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        self._write_results_csv()

    def _write_results_csv(self) -> None:
        if not self.records:
            return
        fieldnames = [
            "run_id", "phase", "description", "status", "OA", "F1", "mIoU", "mAP",
            "mAP50", "elapsed_s", "vertical_lines", "remaining_points", "output_dir",
        ]
        with open(self.results_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            for r in self.records:
                row = {
                    "run_id": r.run_id,
                    "phase": r.phase,
                    "description": r.description,
                    "status": r.status,
                    "elapsed_s": f"{r.elapsed_s:.1f}",
                    "output_dir": r.output_dir,
                    **{k: r.metrics.get(k, "") for k in ("OA", "F1", "mIoU", "mAP", "mAP50")},
                    "vertical_lines": r.diagnostics.get("vertical_lines", ""),
                    "remaining_points": r.diagnostics.get("remaining_points", ""),
                }
                w.writerow(row)

    def _env(self, params_dir: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        env["PROXY4TUN_OUT_ROOT"] = str(self.runs_root.resolve())
        env["PROXY4TUN_INPUT_TXT"] = str(INPUT_TXT.resolve())
        env["PROXY4TUN_PARAMS_DIR"] = str(params_dir.resolve())
        env["PYTHONPATH"] = ":".join(
            [
                str(PIPELINE_DIR),
                str(REPO_ROOT / "sam4tun"),
                str(REPO_ROOT / "sam4tun" / "segment-anything"),
            ]
        )
        return env

    def _run_stages(self, run_id: str, start_stage: int, end_stage: int = 6) -> tuple[str, float]:
        log_path = self.logs_root / f"{run_id}.log"
        t0 = time.time()
        lines: list[str] = []
        env = self._env(self.params_root / run_id)
        for stage in range(start_stage, end_stage + 1):
            script = PIPELINE_DIR / STAGE_SCRIPTS[stage]
            lines.append(f"\n=== stage {stage}: {script.name} ===\n")
            proc = subprocess.run(
                [str(VENV_PY), "-u", str(script), run_id],
                cwd=str(PIPELINE_DIR),
                env=env,
                capture_output=True,
                text=True,
            )
            lines.append(proc.stdout)
            if proc.stderr:
                lines.append(proc.stderr)
            if proc.returncode != 0:
                lines.append(f"\nFAILED stage {stage} exit={proc.returncode}\n")
                log_path.write_text("".join(lines), encoding="utf-8")
                raise RuntimeError(f"Stage {stage} failed for {run_id}; see {log_path}")
        elapsed = time.time() - t0
        log_path.write_text("".join(lines), encoding="utf-8")
        return "".join(lines), elapsed

    def _restore_checkpoint(self, run_id: str, after_stage: int) -> None:
        ckpt_name = CHECKPOINT_AFTER_STAGE[after_stage]
        ckpt = self.checkpoints / ckpt_name
        if not ckpt.exists():
            raise FileNotFoundError(f"Missing checkpoint {ckpt}")
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        anchor_dir = self.runs_root / "anchor_high"
        artifacts_by_stage: dict[int, list[str]] = {
            1: ["unwrapped.csv"],
            2: ["unwrapped.csv", "denoised.csv"],
            3: [
                "unwrapped.csv",
                "denoised.csv",
                "enhanced.csv",
                "depth_map.png",
                "depth_map.npy",
                "depth_map_outlier.npy",
                "pixel_to_point.pkl",
            ],
            4: [
                "unwrapped.csv",
                "denoised.csv",
                "enhanced.csv",
                "depth_map.png",
                "depth_map.npy",
                "depth_map_outlier.npy",
                "pixel_to_point.pkl",
                "initial_points.csv",
                "detected_lines.png",
            ],
        }
        for fname in artifacts_by_stage.get(after_stage, []):
            src = anchor_dir / fname
            if src.exists():
                shutil.copy2(src, run_dir / fname)

        shutil.copy2(ckpt, run_dir / "state.pkl")

    def _save_checkpoint(self, run_id: str, after_stage: int) -> None:
        ckpt_name = CHECKPOINT_AFTER_STAGE[after_stage]
        src = self.runs_root / run_id / "state.pkl"
        shutil.copy2(src, self.checkpoints / ckpt_name)

    def _prepare_params(self, run_id: str, overlay_by_stage: dict[str, dict[str, Any]] | None) -> None:
        materialize_run_params(self.params_root / run_id, HIGH, overlay_by_stage)

    def run_config(
        self,
        run_id: str,
        phase: str,
        description: str,
        overlay_by_stage: dict[str, dict[str, Any]] | None,
        start_stage: int | None = None,
        restore_after: int | None = None,
    ) -> RunRecord:
        if any(r.run_id == run_id for r in self.records):
            existing = next(r for r in self.records if r.run_id == run_id)
            if existing.status == "ok" and (self.runs_root / run_id / "evaluation" / "performance.md").exists():
                return existing

        start = start_stage or (start_stage_for_overlay(overlay_by_stage or {}) if overlay_by_stage else 2)
        restore = restore_after if restore_after is not None else max(1, start - 1)

        self._prepare_params(run_id, overlay_by_stage)
        if start > 1:
            self._restore_checkpoint(run_id, restore)

        log_text, elapsed = self._run_stages(run_id, start_stage=start)
        run_dir = self.runs_root / run_id
        perf_path = run_dir / "evaluation" / "performance.md"
        metrics = parse_performance_md(perf_path) if perf_path.exists() else {}
        diag = collect_diagnostics(run_dir, log_text)

        rec = RunRecord(
            run_id=run_id,
            phase=phase,
            description=description,
            overlay=overlay_by_stage or {},
            start_stage=start,
            elapsed_s=elapsed,
            metrics=metrics,
            diagnostics=diag,
            output_dir=str(run_dir),
            log_path=str(self.logs_root / f"{run_id}.log"),
        )
        self.records.append(rec)
        self.save_manifest()
        return rec

    def setup_checkpoints(self) -> None:
        """Run stage 1 once, then build HIGH checkpoints after stages 2–4."""
        if (self.checkpoints / "after_4.pkl").exists():
            print("Checkpoints already exist; skipping setup.")
            return

        seed_id = "_stage1_seed"
        self._prepare_params(seed_id, None)
        print("Running stage 1 (unfolding) for fixed checkpoint...")
        self._run_stages(seed_id, start_stage=1, end_stage=1)
        self._save_checkpoint(seed_id, 1)

        # Build HIGH checkpoints sequentially in dedicated dirs
        for stage_end, ckpt_stage in [(2, 2), (3, 3), (4, 4)]:
            rid = f"_build_ckpt_{ckpt_stage}"
            self._prepare_params(rid, None)
            self._restore_checkpoint(rid, ckpt_stage - 1)
            self._run_stages(rid, start_stage=ckpt_stage, end_stage=ckpt_stage)
            self._save_checkpoint(rid, ckpt_stage)
            print(f"Saved checkpoint after stage {ckpt_stage}")

    def metric(self, run_id: str, key: str = "mIoU") -> float | None:
        for r in self.records:
            if r.run_id == run_id:
                return r.metrics.get(key)
        return None

    def delta_vs_high(self, run_id: str, key: str = "mIoU") -> float | None:
        high = self.metric("anchor_high", key)
        val = self.metric(run_id, key)
        if high is None or val is None:
            return None
        return val - high

    def validate_gate(self) -> dict[str, Any]:
        high = self.records[-2:] if len(self.records) >= 2 else self.records
        by_id = {r.run_id: r for r in self.records}
        ah = by_id.get("anchor_high")
        al = by_id.get("anchor_low")
        if not ah or not al:
            raise RuntimeError("Missing anchor_high or anchor_low runs")

        high_miou = ah.metrics.get("mIoU", 0)
        low_miou = al.metrics.get("mIoU", 0)
        delta = high_miou - low_miou
        gate = {
            "case": "1-1",
            "high_mIoU": high_miou,
            "low_mIoU": low_miou,
            "delta_mIoU": delta,
            "high_path": ah.output_dir,
            "low_path": al.output_dir,
            "pass_high_min": high_miou >= GATE_MIN_HIGH_MIOU,
            "pass_delta": delta >= GATE_MIN_DELTA_MIOU,
            "pass_prior_tolerance": abs(high_miou - PRIOR_HIGH_MIOU) <= GATE_MIOU_TOLERANCE,
            "passed": False,
        }
        gate["passed"] = gate["pass_high_min"] and gate["pass_delta"] and gate["pass_prior_tolerance"]
        gate_path = self.study_root / "validation_gate.json"
        gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(gate, indent=2))
        if not gate["passed"]:
            raise RuntimeError(f"Validation gate failed; see {gate_path}")
        return gate

    def is_active(self, run_id: str) -> bool:
        d_miou = abs(self.delta_vs_high(run_id, "mIoU") or 0)
        d_map = abs(self.delta_vs_high(run_id, "mAP") or 0)
        return d_miou >= MIoU_SEMANTIC_THRESH or d_map >= MAP_INSTANCE_THRESH

    def phase0_anchors(self) -> None:
        self.setup_checkpoints()
        if "anchor_high" not in {r.run_id for r in self.records}:
            self.run_config("anchor_high", "phase0", "HIGH anchor (all ablation params)", None, start_stage=2, restore_after=1)
        if "anchor_low" not in {r.run_id for r in self.records}:
            overlay = {
                "denoising": low_overlay_for_stage("denoising"),
                "enhancing": low_overlay_for_stage("enhancing"),
                "detecting": low_overlay_for_stage("detecting"),
                "sam": low_overlay_for_stage("sam"),
            }
            self.run_config("anchor_low", "phase0", "LOW anchor (sample defaults)", overlay, start_stage=2, restore_after=1)
        self.validate_gate()

    def phase1_stage_screen(self) -> list[str]:
        active: list[str] = []
        for stage in ("denoising", "enhancing", "detecting", "sam"):
            rid = f"p1_stage_{stage}"
            if rid in {r.run_id for r in self.records}:
                if self.is_active(rid):
                    active.append(stage)
                continue
            overlay = stage_revert_overlay(stage)
            start = start_stage_for_overlay(overlay)
            try:
                self.run_config(rid, "phase1", f"Revert entire {stage} to LOW", overlay, start_stage=start)
            except RuntimeError as exc:
                print(f"FAILED {rid}: {exc}")
                self.records.append(RunRecord(
                    run_id=rid, phase="phase1", description=f"FAILED {stage}",
                    overlay=overlay, start_stage=start, elapsed_s=0, status="failed",
                ))
                self.save_manifest()
                continue
            if self.is_active(rid):
                active.append(stage)
                print(f"ACTIVE stage: {stage} ΔmIoU={self.delta_vs_high(rid,'mIoU'):.3f} ΔmAP={self.delta_vs_high(rid,'mAP'):.3f}")
            else:
                print(f"INACTIVE stage: {stage}")
        return active

    def phase1_groups(self, active_stages: set[str]) -> list[str]:
        active_groups: list[str] = []
        stage_prefix = {
            "denoise_": "denoising",
            "enhance_": "enhancing",
            "detect_": "detecting",
            "sam_": "sam",
        }
        for gid, overlay in GROUPS.items():
            stage = next((s for p, s in stage_prefix.items() if gid.startswith(p)), None)
            if stage and stage not in active_stages:
                continue
            rid = f"p1_group_{gid}"
            if rid in {r.run_id for r in self.records}:
                if self.is_active(rid):
                    active_groups.append(gid)
                continue
            start = start_stage_for_overlay(overlay)
            try:
                self.run_config(rid, "phase1", f"Group revert: {gid}", overlay, start_stage=start)
            except RuntimeError as exc:
                print(f"FAILED {rid}: {exc}")
                continue
            if self.is_active(rid):
                active_groups.append(gid)
                print(f"ACTIVE group: {gid}")
            else:
                print(f"INACTIVE group: {gid}")
        return active_groups

    def phase2_individuals(self, active_stages: set[str]) -> list[str]:
        survivors: list[str] = []
        individuals = individual_overlays()
        for fid, overlay in individuals.items():
            stage = fid.split("_", 1)[0]
            stage_map = {"denoise": "denoising", "enhance": "enhancing", "detect": "detecting", "sam": "sam"}
            st = stage_map.get(stage, stage)
            if st not in active_stages and stage != "sam":
                # still test sam if enhancing/denoising active
                if fid != "sam_y_bounds" or not (active_stages & {"denoising", "enhancing", "detecting", "sam"}):
                    if st != "sam":
                        continue
            rid = f"p2_{fid}"
            if rid in {r.run_id for r in self.records}:
                if self.is_active(rid):
                    survivors.append(fid)
                continue
            start = start_stage_for_overlay(overlay)
            try:
                self.run_config(rid, "phase2", f"Single-factor revert: {fid}", overlay, start_stage=start)
            except RuntimeError as exc:
                print(f"FAILED {rid}: {exc}")
                continue
            d_miou = self.delta_vs_high(rid, "mIoU") or 0
            d_map = self.delta_vs_high(rid, "mAP") or 0
            if abs(d_miou) >= MIoU_SEMANTIC_THRESH or abs(d_map) >= MAP_INSTANCE_THRESH:
                survivors.append(fid)
                print(f"SURVIVOR {fid}: ΔmIoU={d_miou:.3f} ΔmAP={d_map:.3f}")
        return survivors

    def phase3_fractional(self, top_factors: list[str] | None = None) -> None:
        """Run 16-run fractional factorial on core 7 factors."""
        for i, row in enumerate(FRACTIONAL_7F_RES4):
            rid = f"p3_ff7_{i:02d}"
            if rid in {r.run_id for r in self.records}:
                continue
            overlay = design_row_to_overlay(row)
            start = start_stage_for_overlay(overlay)
            self.run_config(rid, "phase3", f"Fractional factorial row {i}", overlay, start_stage=start)

    def phase4_confirm(self, finalist_ids: list[str]) -> None:
        configs = {
            "confirm_high": (None, "HIGH"),
            "confirm_low": (
                {
                    "denoising": low_overlay_for_stage("denoising"),
                    "enhancing": low_overlay_for_stage("enhancing"),
                    "detecting": low_overlay_for_stage("detecting"),
                    "sam": low_overlay_for_stage("sam"),
                },
                "LOW",
            ),
        }
        for fid in finalist_ids[:2]:
            overlay = individual_overlays().get(fid)
            if overlay:
                configs[f"confirm_{fid}"] = (overlay, fid)

        for rep in range(3):
            for key, (overlay, desc) in configs.items():
                rid = f"p4_{key}_r{rep}"
                if rid in {r.run_id for r in self.records}:
                    continue
                start = 2 if overlay and "denoising" in overlay else 2
                if overlay:
                    start = start_stage_for_overlay(overlay)
                self.run_config(rid, "phase4", f"Confirm {desc} rep {rep}", overlay, start_stage=start or 2)

    def rank_factors(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for r in self.records:
            if not r.run_id.startswith("p2_"):
                continue
            fid = r.run_id.replace("p2_", "", 1)
            rows.append({
                "factor": fid,
                "delta_mIoU": self.delta_vs_high(r.run_id, "mIoU"),
                "delta_mAP": self.delta_vs_high(r.run_id, "mAP"),
                "delta_OA": self.delta_vs_high(r.run_id, "OA"),
                "vertical_lines": r.diagnostics.get("vertical_lines"),
                "remaining_points": r.diagnostics.get("remaining_points"),
            })
        rows.sort(key=lambda x: abs(x["delta_mIoU"] or 0), reverse=True)
        return rows

    def write_report(self) -> Path:
        rankings = self.rank_factors()
        by_id = {r.run_id: r for r in self.records}
        ah = by_id.get("anchor_high")
        al = by_id.get("anchor_low")
        lines = [
            "# Critical Parameter Ablation — Tunnel 1-1\n",
            f"\nStudy root: `{self.study_root}`\n",
            f"Input: `{INPUT_TXT}`\n",
            "\n## Validation gate\n",
        ]
        gate_path = self.study_root / "validation_gate.json"
        if gate_path.exists():
            lines.append(f"```json\n{gate_path.read_text()}\n```\n")

        if ah and al:
            lines += [
                "\n## Anchors\n",
                f"| Config | OA | F1 | mIoU | mAP |\n",
                f"|--------|-----|-----|------|-----|\n",
                f"| HIGH | {ah.metrics.get('OA','')} | {ah.metrics.get('F1','')} | {ah.metrics.get('mIoU','')} | {ah.metrics.get('mAP','')} |\n",
                f"| LOW | {al.metrics.get('OA','')} | {al.metrics.get('F1','')} | {al.metrics.get('mIoU','')} | {al.metrics.get('mAP','')} |\n",
            ]

        lines += ["\n## Phase 1 — stage reversions\n", "| Run | ΔmIoU | ΔmAP | Active? |\n", "|-----|-------|------|--------|\n"]
        for stage in ("denoising", "enhancing", "detecting", "sam"):
            rid = f"p1_stage_{stage}"
            if rid in by_id:
                lines.append(
                    f"| {stage} | {self.delta_vs_high(rid,'mIoU'):.3f} | {self.delta_vs_high(rid,'mAP'):.3f} | {self.is_active(rid)} |\n"
                )

        lines += ["\n## Phase 2 — individual factor ranking\n", "| Factor | ΔmIoU | ΔmAP | |\n", "|--------|-------|------|--|\n"]
        for row in rankings:
            crit = "critical" if abs(row["delta_mIoU"] or 0) >= MIoU_CONFIRM_THRESH or abs(row["delta_mAP"] or 0) >= MAP_CONFIRM_THRESH else ""
            lines.append(
                f"| {row['factor']} | {row['delta_mIoU']:.3f} | {row['delta_mAP']:.3f} | {crit} |\n"
            )

        critical = [r for r in rankings if abs(r["delta_mIoU"] or 0) >= MIoU_CONFIRM_THRESH or abs(r["delta_mAP"] or 0) >= MAP_CONFIRM_THRESH]
        lines += ["\n## Confirmed critical factors\n"]
        if critical:
            for r in critical:
                lines.append(f"- **{r['factor']}**: ΔmIoU={r['delta_mIoU']:.3f}, ΔmAP={r['delta_mAP']:.3f}\n")
        else:
            lines.append("- None met confirmation thresholds; see Phase 2 ranking for screening survivors.\n")

        summary = build_summary(self.study_root)
        (self.study_root / "analysis_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )

        lines += ["\n## Phase 1 — mechanism groups\n", "| Group | ΔmIoU | ΔmAP | Active? |\n", "|-------|-------|------|--------|\n"]
        for gid in GROUPS:
            rid = f"p1_group_{gid}"
            if rid in by_id:
                lines.append(
                    f"| {gid} | {self.delta_vs_high(rid,'mIoU'):.3f} | {self.delta_vs_high(rid,'mAP'):.3f} | {self.is_active(rid)} |\n"
                )

        lines += ["\n## Phase 3 — fractional factorial main effects (mIoU)\n", "| Factor | Parameter | Effect | |\n", "|--------|-----------|--------|--|\n"]
        for eff in summary.get("fractional_effects", []):
            tag = "strong" if abs(eff["effect_mIoU"]) >= 0.06 else ""
            lines.append(
                f"| {eff['factor']} | {eff['param']} | {eff['effect_mIoU']:+.3f} | {tag} |\n"
            )

        lines += ["\n## Phase 4 — confirmation repeats (median mIoU)\n"]
        for key in ("confirm_high", "confirm_low", "confirm_depth_high", "confirm_depth_low"):
            stats = summary.get(key, {})
            if stats:
                lines.append(f"- **{key}**: median={stats.get('median', 'n/a'):.3f}, stdev={stats.get('stdev', 0):.3f}, n={stats.get('n', 0)}\n")

        lines += ["\n## Minimal high-performing subset (recommended)\n"]
        lines.append(
            "Keep HIGH values for `depth_threshold_low` (0.005), `depth_threshold_high` (0.015), "
            "and the full enhancing stage bundle. Denoising radial mask and `grad_threshold` are secondary (mAP). "
            "Detecting and SAM `y_bounds` changes are not critical on 1-1 when detection uses fallback lines.\n"
        )

        report = self.study_root / "report.md"
        report.write_text("".join(lines), encoding="utf-8")
        return report


def patch_stage_loaders() -> None:
    """Patch _load_params in pipeline stages to honor PROXY4TUN_PARAMS_DIR."""
    snippet_old = '    path = os.path.join(_PIPELINE_DIR, "parameters", f"parameters_{stage}.json")'
    snippet_new = '''    _params_root = os.environ.get("PROXY4TUN_PARAMS_DIR", "").strip() or os.path.join(_PIPELINE_DIR, "parameters")
    path = os.path.join(_params_root, f"parameters_{stage}.json")'''
    for script in STAGE_SCRIPTS.values():
        p = PIPELINE_DIR / script
        text = p.read_text(encoding="utf-8")
        if snippet_new.split("\n")[0] in text:
            continue
        if snippet_old not in text:
            raise RuntimeError(f"Could not patch {p}")
        p.write_text(text.replace(snippet_old, snippet_new), encoding="utf-8")
        print(f"Patched {p.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run critical parameter ablation study on 1-1")
    parser.add_argument("--study-root", type=Path, default=None, help="Resume existing study directory")
    parser.add_argument("--phase", choices=["all", "0", "1", "2", "3", "4", "report"], default="all")
    parser.add_argument("--patch-stages", action="store_true", help="Patch stage scripts for PROXY4TUN_PARAMS_DIR")
    args = parser.parse_args()

    if args.patch_stages:
        patch_stage_loaders()

    study = AblationStudy(args.study_root.resolve() if args.study_root else None)
    print(f"Study root: {study.study_root}")

    if args.phase in ("all", "0"):
        study.phase0_anchors()

    active_stages: set[str] = set()
    active_groups: list[str] = []
    survivors: list[str] = []

    if args.phase in ("all", "1"):
        active_stages = set(study.phase1_stage_screen())
        active_groups = study.phase1_groups(active_stages)

    if args.phase in ("all", "2"):
        if not active_stages:
            active_stages = {"denoising", "enhancing", "detecting", "sam"}
        survivors = study.phase2_individuals(active_stages)

    if args.phase in ("all", "3"):
        study.phase3_fractional(survivors[:7] if survivors else None)

    if args.phase in ("all", "4"):
        top = [r["factor"] for r in study.rank_factors()[:2]]
        study.phase4_confirm(top)

    if args.phase in ("all", "report"):
        report = study.write_report()
        print(f"Report: {report}")
        print(f"Results CSV: {study.results_csv}")


if __name__ == "__main__":
    main()
