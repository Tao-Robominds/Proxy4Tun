"""Artifact persistence helpers shared by all stages."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def ensure_output_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_dataframe(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    df.to_csv(path, index=False)
    return path


def load_dataframe(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def save_pickle(value: Any, path: str | Path) -> Path:
    path = Path(path)
    with path.open("wb") as stream:
        pickle.dump(value, stream, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def load_pickle(path: str | Path) -> Any:
    with Path(path).open("rb") as stream:
        return pickle.load(stream)


def save_array(value: np.ndarray, path: str | Path) -> Path:
    path = Path(path)
    np.save(path, value)
    return path


def save_depth_png(
    depth_map: np.ndarray,
    path: str | Path,
    *,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap: str = "viridis",
) -> Path:
    """Save the notebook-compatible coloured depth-map artifact."""

    import matplotlib.pyplot as plt

    path = Path(path)
    plt.imsave(path, depth_map, cmap=cmap, vmin=vmin, vmax=vmax)
    return path
