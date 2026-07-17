"""CLI entry point for the parameterized SAM4Tun agent pipelines."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .helpers.pipeline_io import (
    OutputPathError,
    REPO_ROOT,
    SAM4TUN_ROOT,
    prepare_output_dir,
)

_REPO = Path(REPO_ROOT)
PROFILES = {
    "sample": _REPO / "agents" / "sample",
    "t1&2": _REPO / "agents" / "t1&2",
    "t12": _REPO / "agents" / "t1&2",
}

STAGES = [
    "1_unfolding.py",
    "2_denoising.py",
    "3_enhancing.py",
    "4_detection.py",
    "5_sam.py",
    "6_evaluation.py",
]


def _resolve_params_dir(profile: str, params_dir: str | None) -> Path:
    if params_dir:
        path = Path(params_dir).expanduser().resolve()
    else:
        path = (PROFILES[profile] / "parameters").resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Parameter directory not found: {path}")
    required = [
        "parameters_unfolding.json",
        "parameters_denoising.json",
        "parameters_enhancing.json",
        "parameters_detecting.json",
        "parameters_sam.json",
    ]
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing parameter files under {path}: {', '.join(missing)}"
        )
    return path


def run_parameterized(
    *,
    input_txt: Path,
    tunnel_id: str,
    profile: str,
    out_root: Path,
    params_dir: Path,
    overwrite: bool = False,
    resume: bool = False,
    through_stage: int = 6,
) -> Path:
    """Run parameterized agent stages; return the run output directory."""
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile {profile!r}; choose from {sorted(PROFILES)}")
    if not 1 <= through_stage <= 6:
        raise ValueError("through_stage must be between 1 and 6")

    input_txt = input_txt.expanduser().resolve()
    if not input_txt.is_file():
        raise FileNotFoundError(f"Input point cloud not found: {input_txt}")

    out_root = out_root.expanduser().resolve()
    os.environ["PROXY4TUN_OUT_ROOT"] = str(out_root)
    os.environ["PROXY4TUN_INPUT_TXT"] = str(input_txt)
    os.environ["PROXY4TUN_PARAMS_DIR"] = str(params_dir.resolve())

    try:
        prepare_output_dir(tunnel_id, overwrite=overwrite, resume=resume)
    except OutputPathError:
        raise

    agent_dir = PROFILES[profile]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(SAM4TUN_ROOT),
            str(Path(SAM4TUN_ROOT) / "segment-anything"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)
    env["MPLBACKEND"] = env.get("MPLBACKEND", "Agg")

    for stage in STAGES[:through_stage]:
        script = agent_dir / stage
        if not script.is_file():
            raise FileNotFoundError(f"Stage script missing: {script}")
        print(f"\n=== {stage} ===", flush=True)
        subprocess.run(
            [sys.executable, "-u", str(script), tunnel_id],
            cwd=str(REPO_ROOT),
            env=env,
            check=True,
        )
    return out_root / tunnel_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the parameterized SAM4Tun pipeline "
            "(agents/sample or agents/t1&2) with explicit I/O paths."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Nx6 point-cloud TXT (default: data/subsets/<tunnel-id>.txt)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Output directory for this run (default: data/<tunnel-id>/)",
    )
    parser.add_argument(
        "--tunnel-id",
        help="Artifact subdirectory name under the output root (default: input stem)",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="t1&2",
        help="Agent family / default parameter profile (default: t1&2)",
    )
    parser.add_argument(
        "--params-dir",
        help="Override parameter directory (sets PROXY4TUN_PARAMS_DIR)",
    )
    parser.add_argument(
        "--out-root",
        help="Artifact root directory (default: <repo>/data). Ignored if output is set.",
    )
    parser.add_argument(
        "--through-stage",
        type=int,
        choices=range(1, 7),
        default=6,
        help="Stop after this stage number (1=unfolding … 6=evaluation)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing into an existing non-empty output directory",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Allow reusing an existing output directory (stage scripts may overwrite files)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve paths and validate params/output gates without running stages",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    tunnel_id = args.tunnel_id
    if args.input:
        input_txt = Path(args.input)
        if tunnel_id is None:
            tunnel_id = input_txt.stem
    else:
        if tunnel_id is None:
            parser.error("provide input path and/or --tunnel-id")
        input_txt = _REPO / "data" / "subsets" / f"{tunnel_id}.txt"

    params_dir = _resolve_params_dir(args.profile, args.params_dir)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        out_root = output_path.parent
        tunnel_id = output_path.name
    else:
        out_root = (
            Path(args.out_root).expanduser().resolve()
            if args.out_root
            else _REPO / "data"
        )

    if args.dry_run:
        os.environ["PROXY4TUN_OUT_ROOT"] = str(out_root.resolve())
        try:
            prepare_output_dir(
                tunnel_id, overwrite=args.overwrite, resume=args.resume
            )
        except OutputPathError as exc:
            print(f"DRY-RUN BLOCKED: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        print("dry-run ok")
        print(f"  input:      {input_txt.resolve()}")
        print(f"  out_root:   {out_root.resolve()}")
        print(f"  tunnel_id:  {tunnel_id}")
        print(f"  profile:    {args.profile}")
        print(f"  params_dir: {params_dir}")
        print(f"  through:    {args.through_stage}")
        return

    try:
        result = run_parameterized(
            input_txt=input_txt,
            tunnel_id=tunnel_id,
            profile=args.profile,
            out_root=out_root,
            params_dir=params_dir,
            overwrite=args.overwrite,
            resume=args.resume,
            through_stage=args.through_stage,
        )
    except OutputPathError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(result)


if __name__ == "__main__":
    main()
