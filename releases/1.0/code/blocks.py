"""Block taxonomy for the three-block mIoU proxy ablation.

Block 1 — Coherence: internal self-consistency of the proposed segmentation
          in the pipeline's own frame (form / regularity / completeness).
Block 2 — Evidence quality: how much of the result rests on observed data
          versus interpolation / fallback.
Block 3 — Attainable priors: agreement with design / build-record geometry
          (phase, stagger). Defined in ``priors.py``; not Tier-1 keys.
"""

from __future__ import annotations

from typing import Iterable

# Every key in intrinsics.TIER1_KEYS is assigned to exactly one of {1, 2}.
BLOCK1_COHERENCE: tuple[str, ...] = (
    "det_x_spacing_cv",
    "det_y_std",
    "det_ring_count_error",
    "sam_fill_rate",
    "sam_ring_completeness",
    "sam_segment_size_cv",
    "sam_ontology_divergence",
)

BLOCK2_EVIDENCE: tuple[str, ...] = (
    "denoise_retained_ratio",
    "depth_nan_ratio",
    "depth_outlier_ratio",
    "det_midpoint_ratio",
    "det_real_detection_ratio",
    "det_fallback_ratio",
    "det_n_points",
)

# Lean B2 (rev2): minimal subset that passes the permutation control.
# depth_outlier_ratio drives the perm failure of full B2 (family-conditional);
# det_midpoint_ratio/det_n_points are regime-constant on t3.
BLOCK2_EVIDENCE_LEAN: tuple[str, ...] = (
    "denoise_retained_ratio",
    "depth_nan_ratio",
    "det_real_detection_ratio",
    "det_fallback_ratio",
)

# Block-3 feature names produced by priors.py (not Tier-1).
# Rev2 (minimal-prior): scored against the frozen per-tunnel datum only
# (one clock table per tunnel = deployment build-record analogue); no
# same-run GT at scoring time. Stagger dropped (weak, extra information).
BLOCK3_PRIOR: tuple[str, ...] = (
    "prior_phase_offset_frac",
    "prior_order_match",
    "prior_boundary_evidence_lag_frac",
)

FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "B1": BLOCK1_COHERENCE,
    "B2": BLOCK2_EVIDENCE,
    "B2lean": BLOCK2_EVIDENCE_LEAN,
    "B1+B2": BLOCK1_COHERENCE + BLOCK2_EVIDENCE,
    "B1+B2lean": BLOCK1_COHERENCE + BLOCK2_EVIDENCE_LEAN,
    "B1+B2+B3": BLOCK1_COHERENCE + BLOCK2_EVIDENCE + BLOCK3_PRIOR,
    "B1+B2lean+B3": BLOCK1_COHERENCE + BLOCK2_EVIDENCE_LEAN + BLOCK3_PRIOR,
}


def features_for(set_name: str) -> list[str]:
    if set_name not in FEATURE_SETS:
        raise KeyError(f"Unknown feature set {set_name!r}; choose from {list(FEATURE_SETS)}")
    return list(FEATURE_SETS[set_name])


def block_of(feature: str) -> int | None:
    if feature in BLOCK1_COHERENCE:
        return 1
    if feature in BLOCK2_EVIDENCE:
        return 2
    if feature in BLOCK3_PRIOR:
        return 3
    return None


def assert_tier1_partition(tier1_keys: Iterable[str]) -> None:
    """Raise if any Tier-1 key is missing or double-assigned."""
    assigned = set(BLOCK1_COHERENCE) | set(BLOCK2_EVIDENCE)
    keys = set(tier1_keys)
    missing = keys - assigned
    extra = assigned - keys
    overlap = set(BLOCK1_COHERENCE) & set(BLOCK2_EVIDENCE)
    if missing or extra or overlap:
        raise AssertionError(
            f"Block partition broken: missing={sorted(missing)} "
            f"extra={sorted(extra)} overlap={sorted(overlap)}"
        )


if __name__ == "__main__":
    from intrinsics import TIER1_KEYS

    assert_tier1_partition(TIER1_KEYS)
    print("Block partition OK")
    for name, feats in FEATURE_SETS.items():
        print(f"  {name}: {len(feats)} features")
