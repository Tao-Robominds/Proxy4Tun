#!/usr/bin/env python3
"""Selector-policy table and parent-tunnel cluster bootstrap for all arms.

Reproduces manuscript panel statistics from stage-3 selection JSONs:
  - mean/median Δ, up/same/down, worst Δ
  - family and GT-stratum means
  - selector policies: start / random-round / round1 / max-proxy /
    monotone-accept / GT oracle (+ oracle recovery)
  - proposal yield / accepted precision / selector regret
  - paired parent-tunnel cluster bootstrap (5 clusters, 100k, fixed seed)

Usage:
  ./venv/bin/python bo/sc_general/selector_policies.py
  ./venv/bin/python bo/sc_general/selector_policies.py --arms fable,gpt56,gemini38
  ./venv/bin/python bo/sc_general/selector_policies.py --verify-llm
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from bo.sc_general.select_round import select_dir_for  # noqa: E402
from bo.sc_general.stage3_report import PANEL  # noqa: E402
from bo.runtime.spaces import FAMILY_MODE, family_of_subset  # noqa: E402

STAGE3 = _REPO / "data" / "sc-general" / "stage3"
EXPORT = _REPO / "exports" / "sc-general-random-evaluation"
TIE_MARGIN = 0.01
N_BOOT = 100_000
BOOT_SEED = 0
DUAL_BAND = ["1-4", "1-5", "2-2", "3-4", "4-1", "4-3"]

# Manuscript targets for the three LLM arms (verify before trusting random).
LLM_TARGETS = {
    "fable_fresh": {"mean_miou": 0.751, "mean_delta": 0.013},
    "gpt56": {"mean_miou": 0.760, "mean_delta": 0.022},
    "gemini38": {"mean_miou": 0.759, "mean_delta": 0.021},
}


def parent_tunnel(subset: str) -> str:
    return subset.split("-")[0]


def _load_selection(arm: str, subset: str) -> dict[str, Any] | None:
    path = select_dir_for(arm) / f"{subset}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _round_miou(sel: dict[str, Any]) -> dict[str, float]:
    out = {"anchor": float(sel["anchor"]["mIoU"])}
    for r in sel.get("rounds", []):
        if r.get("mIoU") is None:
            continue
        out[str(r["round"])] = float(r["mIoU"])
    return out


def _round_proxy(sel: dict[str, Any]) -> dict[str, float]:
    out = {"anchor": float(sel["anchor"]["proxy_scaled"])}
    for r in sel.get("rounds", []):
        out[str(r["round"])] = float(r["proxy_scaled"])
    return out


def _round_residual(sel: dict[str, Any]) -> dict[str, float]:
    out = {"anchor": float(sel["anchor"].get("recentre_residual_max_cm") or np.inf)}
    for r in sel.get("rounds", []):
        rr = r.get("recentre_residual_max_cm")
        out[str(r["round"])] = float(rr) if rr is not None else float("inf")
    return out


def _monotone_accept(sel: dict[str, Any]) -> str:
    """Recompute monotone-accept selection; should match stored selected.round."""
    proxies = _round_proxy(sel)
    residuals = _round_residual(sel)
    y0 = proxies["anchor"]
    candidates = [
        r for r, y in proxies.items() if r != "anchor" and y > y0
    ]
    if not candidates:
        return "anchor"
    best = max(proxies[r] for r in candidates)
    near = [r for r in candidates if proxies[r] >= best - TIE_MARGIN]
    # lex: lower residual, then higher proxy
    near.sort(key=lambda r: (residuals[r], -proxies[r]))
    return near[0]


def _max_proxy(sel: dict[str, Any]) -> str:
    proxies = _round_proxy(sel)
    # start eligible
    return max(proxies, key=lambda r: proxies[r])


def _oracle(sel: dict[str, Any]) -> str:
    mious = _round_miou(sel)
    return max(mious, key=lambda r: mious[r])


def _policy_miou(sel: dict[str, Any], policy: str) -> float:
    mious = _round_miou(sel)
    if policy == "start":
        return mious["anchor"]
    if policy == "round1":
        return mious.get("round1", mious["anchor"])
    if policy == "random_round":
        # expectation = mean of the three rounds (not including start)
        rs = [mious[r] for r in ("round1", "round2", "round3") if r in mious]
        return float(np.mean(rs)) if rs else mious["anchor"]
    if policy == "max_proxy":
        return mious[_max_proxy(sel)]
    if policy == "monotone_accept":
        key = sel["selected"]["round"]
        # map selected round name
        if key == "anchor":
            return mious["anchor"]
        return float(sel["selected"]["mIoU"])
    if policy == "oracle":
        return mious[_oracle(sel)]
    raise ValueError(policy)


def load_arm_panel(arm: str) -> pd.DataFrame:
    rows = []
    for subset in PANEL:
        sel = _load_selection(arm, subset)
        if sel is None:
            raise FileNotFoundError(f"missing selection for {arm}/{subset}")
        a_miou = float(sel["anchor"]["mIoU"])
        a_proxy = float(sel["anchor"]["proxy_scaled"])
        s = sel["selected"]
        s_miou = float(s["mIoU"])
        s_proxy = float(s["proxy_scaled"])
        delta = s_miou - a_miou
        fam = FAMILY_MODE[family_of_subset(subset)]
        # per-round for policies / yield
        round_mious = _round_miou(sel)
        round_proxies = _round_proxy(sel)
        candidates = [
            r for r in ("round1", "round2", "round3")
            if r in round_proxies and round_proxies[r] > a_proxy
        ]
        gt_useful = [
            r for r in candidates
            if round_mious.get(r, -1) > a_miou
        ]
        oracle_miou = max(round_mious.values())
        regret = oracle_miou - s_miou
        rows.append(
            {
                "subset": subset,
                "family": fam,
                "parent": parent_tunnel(subset),
                "arm": arm,
                "anchor_proxy": a_proxy,
                "anchor_mIoU": a_miou,
                "selected_round": s["round"],
                "selected_proxy": s_proxy,
                "selected_mIoU": s_miou,
                "delta_mIoU": delta,
                "refined": s["round"] != "anchor",
                "gt_low": a_miou < 0.7,
                "dual_band": subset in DUAL_BAND,
                "n_proxy_admissible": len(candidates),
                "n_gt_useful_of_admissible": len(gt_useful),
                "n_rounds": sum(1 for r in ("round1", "round2", "round3") if r in round_mious),
                "regret": regret,
                "policy_start": _policy_miou(sel, "start"),
                "policy_random_round": _policy_miou(sel, "random_round"),
                "policy_round1": _policy_miou(sel, "round1"),
                "policy_max_proxy": _policy_miou(sel, "max_proxy"),
                "policy_monotone": _policy_miou(sel, "monotone_accept"),
                "policy_oracle": _policy_miou(sel, "oracle"),
                "recomputed_monotone": _monotone_accept(sel),
                "stored_matches_recompute": _monotone_accept(sel) == s["round"],
            }
        )
    return pd.DataFrame(rows)


def summarize_arm(df: pd.DataFrame) -> dict[str, Any]:
    d = df["delta_mIoU"].astype(float)
    up = int((d > 1e-6).sum())
    same = int((d.abs() <= 1e-6).sum())
    down = int((d < -1e-6).sum())
    start = float(df["anchor_mIoU"].mean())
    selected = float(df["selected_mIoU"].mean())
    mean_delta = float(d.mean())
    oracle = float(df["policy_oracle"].mean())
    mono = float(df["policy_monotone"].mean())
    recovery = (
        (mono - start) / (oracle - start) if abs(oracle - start) > 1e-12 else float("nan")
    )
    # yield / precision over rounds
    n_cand = int(df["n_proxy_admissible"].sum())
    n_useful = int(df["n_gt_useful_of_admissible"].sum())
    n_rounds = int(df["n_rounds"].sum())
    return {
        "n": len(df),
        "mean_anchor_mIoU": start,
        "mean_selected_mIoU": selected,
        "mean_delta": mean_delta,
        "median_delta": float(d.median()),
        "up": up,
        "same": same,
        "down": down,
        "worst_delta": float(d.min()),
        "n_refined": int(df["refined"].sum()),
        "mean_regret": float(df["regret"].mean()),
        "proposal_yield": n_cand / n_rounds if n_rounds else float("nan"),
        "accepted_precision": n_useful / n_cand if n_cand else float("nan"),
        "n_proxy_admissible": n_cand,
        "n_gt_useful": n_useful,
        "n_rounds": n_rounds,
        "policies": {
            "start": start,
            "random_round": float(df["policy_random_round"].mean()),
            "round1": float(df["policy_round1"].mean()),
            "max_proxy": float(df["policy_max_proxy"].mean()),
            "monotone_accept": mono,
            "oracle": oracle,
            "oracle_recovery": recovery,
        },
        "by_family": {
            fam: {
                "n": int((df["family"] == fam).sum()),
                "mean_selected": float(df.loc[df["family"] == fam, "selected_mIoU"].mean()),
                "mean_delta": float(df.loc[df["family"] == fam, "delta_mIoU"].mean()),
            }
            for fam in sorted(df["family"].unique())
        },
        "by_gt_stratum": {
            "lt_0.7": {
                "n": int(df["gt_low"].sum()),
                "mean_delta": float(df.loc[df["gt_low"], "delta_mIoU"].mean())
                if df["gt_low"].any()
                else float("nan"),
            },
            "ge_0.7": {
                "n": int((~df["gt_low"]).sum()),
                "mean_delta": float(df.loc[~df["gt_low"], "delta_mIoU"].mean())
                if (~df["gt_low"]).any()
                else float("nan"),
            },
        },
        "stored_matches_recompute": bool(df["stored_matches_recompute"].all()),
    }


def cluster_bootstrap_ci(
    df: pd.DataFrame,
    *,
    n_boot: int = N_BOOT,
    seed: int = BOOT_SEED,
) -> dict[str, Any]:
    """Paired parent-tunnel cluster bootstrap for mean Δ and pairwise diffs."""
    parents = sorted(df["parent"].unique())
    # map parent -> array of deltas (aligned by subset order within parent)
    by_parent = {
        p: df.loc[df["parent"] == p, "delta_mIoU"].astype(float).to_numpy()
        for p in parents
    }
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for i in range(n_boot):
        draw = rng.choice(parents, size=len(parents), replace=True)
        sample = np.concatenate([by_parent[p] for p in draw])
        means[i] = sample.mean()
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "mean_delta": float(df["delta_mIoU"].mean()),
        "ci95": [float(lo), float(hi)],
        "n_boot": n_boot,
        "seed": seed,
        "parents": parents,
    }


def pairwise_cluster_ci(
    frames: dict[str, pd.DataFrame],
    arm_a: str,
    arm_b: str,
    *,
    n_boot: int = N_BOOT,
    seed: int = BOOT_SEED,
) -> dict[str, Any]:
    a = frames[arm_a].set_index("subset").sort_index()
    b = frames[arm_b].set_index("subset").sort_index()
    assert list(a.index) == list(b.index)
    diff = (a["delta_mIoU"] - b["delta_mIoU"]).astype(float)
    parents = sorted({parent_tunnel(s) for s in diff.index})
    by_parent = {
        p: diff[[s for s in diff.index if parent_tunnel(s) == p]].to_numpy()
        for p in parents
    }
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for i in range(n_boot):
        draw = rng.choice(parents, size=len(parents), replace=True)
        sample = np.concatenate([by_parent[p] for p in draw])
        means[i] = sample.mean()
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "comparison": f"{arm_a} - {arm_b}",
        "mean_difference": float(diff.mean()),
        "ci95": [float(lo), float(hi)],
    }


def verify_llm(frames: dict[str, pd.DataFrame], tol: float = 0.0015) -> bool:
    ok = True
    for arm, tgt in LLM_TARGETS.items():
        if arm not in frames:
            print(f"VERIFY skip {arm}: missing")
            continue
        s = summarize_arm(frames[arm])
        m = s["mean_selected_mIoU"]
        d = s["mean_delta"]
        m_ok = abs(m - tgt["mean_miou"]) <= tol
        d_ok = abs(d - tgt["mean_delta"]) <= tol
        print(
            f"VERIFY {arm}: mean_mIoU={m:.3f} (target {tgt['mean_miou']}) "
            f"{'OK' if m_ok else 'FAIL'}; "
            f"mean_Δ={d:.3f} (target {tgt['mean_delta']}) "
            f"{'OK' if d_ok else 'FAIL'}; "
            f"recompute_match={s['stored_matches_recompute']}"
        )
        ok = ok and m_ok and d_ok and s["stored_matches_recompute"]
    return ok


def write_exports(
    frames: dict[str, pd.DataFrame],
    summaries: dict[str, Any],
    cis: dict[str, Any],
    pairwise: list[dict[str, Any]],
) -> None:
    EXPORT.mkdir(parents=True, exist_ok=True)
    # panel CSV per arm + combined
    panels = []
    for arm, df in frames.items():
        df.to_csv(EXPORT / f"panel_{arm}.csv", index=False)
        panels.append(df)
    combined = pd.concat(panels, ignore_index=True)
    combined.to_csv(EXPORT / "panel_all_arms.csv", index=False)

    # policies table
    pol_rows = []
    for arm, s in summaries.items():
        row = {"arm": arm, **{f"policy_{k}": v for k, v in s["policies"].items()}}
        pol_rows.append(row)
    pd.DataFrame(pol_rows).to_csv(EXPORT / "selector_policies.csv", index=False)

    # CIs
    (EXPORT / "cluster_bootstrap.json").write_text(
        json.dumps({"per_arm": cis, "pairwise": pairwise, "n_boot": N_BOOT, "seed": BOOT_SEED}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (EXPORT / "summaries.json").write_text(
        json.dumps(summaries, indent=2) + "\n", encoding="utf-8"
    )

    # report
    lines = [
        "# Selector policies and cluster-bootstrap CIs",
        "",
        f"Panel: {len(PANEL)} proxy-admitted cases. Bootstrap: {N_BOOT} parent-tunnel resamples, seed {BOOT_SEED}.",
        "",
        "## Panel means",
        "",
        "| arm | start | selected | mean Δ | median Δ | up/same/down | worst |",
        "|---|---:|---:|---:|---:|---|---:|",
    ]
    for arm, s in summaries.items():
        lines.append(
            f"| {arm} | {s['mean_anchor_mIoU']:.3f} | {s['mean_selected_mIoU']:.3f} | "
            f"{s['mean_delta']:+.3f} | {s['median_delta']:+.3f} | "
            f"{s['up']}/{s['same']}/{s['down']} | {s['worst_delta']:+.3f} |"
        )
    lines += [
        "",
        "## Selector policies (mean mIoU)",
        "",
        "| arm | start | random round | round1 | max-proxy | monotone | oracle | recovery |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, s in summaries.items():
        p = s["policies"]
        rec = p["oracle_recovery"]
        rec_s = f"{100*rec:.0f}%" if rec == rec else "—"
        lines.append(
            f"| {arm} | {p['start']:.3f} | {p['random_round']:.3f} | {p['round1']:.3f} | "
            f"{p['max_proxy']:.3f} | {p['monotone_accept']:.3f} | {p['oracle']:.3f} | {rec_s} |"
        )
    lines += ["", "## Cluster-bootstrap 95% CI (mean Δ)", ""]
    for arm, ci in cis.items():
        lines.append(f"- **{arm}**: {ci['mean_delta']:+.3f} [{ci['ci95'][0]:+.3f}, {ci['ci95'][1]:+.3f}]")
    lines += ["", "## Pairwise differences", ""]
    for pw in pairwise:
        lines.append(
            f"- **{pw['comparison']}**: {pw['mean_difference']:+.3f} "
            f"[{pw['ci95'][0]:+.3f}, {pw['ci95'][1]:+.3f}]"
        )
    (EXPORT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {EXPORT}/")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--arms",
        default="fable_fresh,gpt56,gemini38,random",
        help="Comma-separated arms to include",
    )
    p.add_argument(
        "--verify-llm",
        action="store_true",
        help="Only verify LLM arm means against manuscript targets",
    )
    p.add_argument("--n-boot", type=int, default=N_BOOT)
    args = p.parse_args()
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    frames: dict[str, pd.DataFrame] = {}
    for arm in arms:
        try:
            frames[arm] = load_arm_panel(arm)
        except FileNotFoundError as exc:
            if args.verify_llm and arm == "random":
                continue
            print(f"skip {arm}: {exc}")
    if not frames:
        raise SystemExit("no arms loaded")

    if args.verify_llm:
        ok = verify_llm(frames)
        raise SystemExit(0 if ok else 1)

    summaries = {arm: summarize_arm(df) for arm, df in frames.items()}
    cis = {
        arm: cluster_bootstrap_ci(df, n_boot=args.n_boot)
        for arm, df in frames.items()
    }
    pairwise = []
    arm_list = list(frames)
    for i, a in enumerate(arm_list):
        for b in arm_list[i + 1 :]:
            pairwise.append(pairwise_cluster_ci(frames, a, b, n_boot=args.n_boot))

    # Always verify LLM numbers when present.
    if any(a in frames for a in LLM_TARGETS):
        verify_llm(frames)

    write_exports(frames, summaries, cis, pairwise)
    for arm, s in summaries.items():
        print(
            f"{arm}: selected={s['mean_selected_mIoU']:.3f} "
            f"Δ={s['mean_delta']:+.3f} "
            f"CI={cis[arm]['ci95']} "
            f"policies={s['policies']}"
        )


if __name__ == "__main__":
    main()
