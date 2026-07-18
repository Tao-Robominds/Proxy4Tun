#!/usr/bin/env python3
# Parameterized enhancing — agents/enhancing.py + sam4tun state I/O
# Deferred JSON: none (ring_spacing_factor wired)
import sys
import os
import matplotlib
matplotlib.use("Agg")

import json

_PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_PIPELINE_DIR))
_SAM4TUN_PKG = os.path.join(_REPO_ROOT, "sam4tun")
for _p in (_PIPELINE_DIR, _SAM4TUN_PKG):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from helpers.pipeline_io import ensure_dir
from helpers.pipeline_state import load_state, save_state

import pandas as pd
import numpy as np
from scipy.spatial import KDTree, cKDTree
import numba as nb
from numba import njit, prange
from scipy.interpolate import griddata
from scipy import ndimage
from tqdm.auto import tqdm
from collections import defaultdict
import pickle
import matplotlib.pyplot as plt
import time

tunnel_id = sys.argv[1]


def _load_params(stage: str):
    _params_root = os.environ.get("PROXY4TUN_PARAMS_DIR", "").strip() or os.path.join(_PIPELINE_DIR, "parameters")
    path = os.path.join(_params_root, f"parameters_{stage}.json")
    if os.path.isfile(path):
        with open(path, "r") as f:
            data = json.load(f)
        print(f"Loaded {stage} parameters from {os.path.relpath(path, _REPO_ROOT)}")
        return data, path
    sys.exit(
        f"Missing parameters_{stage}.json under resolved params dir: {_params_root}"
    )


params, param_file = _load_params("enhancing")
denoise_params, _ = _load_params("denoising")
depth_vmin = float(denoise_params.get("mask_r_low", 2.70))
depth_vmax = float(denoise_params.get("mask_r_high", 2.80))

expected_keys = [
    "upsampling_stage1_target_distance", "upsampling_stage2_target_distance",
    "upsampling_stage3_target_distance", "curvature_threshold",
    "depth_threshold_low", "depth_threshold_high", "inter_radius",
    "duplicate_threshold", "n_segment_start", "n_segment_end",
    "num_neighbors", "num_interpolations", "resolution", "window_size",
]
for key in expected_keys:
    if key not in params:
        sys.exit(f"Missing required parameter '{key}' in {param_file}")
upsampling_stage1_target_distance = params["upsampling_stage1_target_distance"]
upsampling_stage2_target_distance = params["upsampling_stage2_target_distance"]
upsampling_stage3_target_distance = params["upsampling_stage3_target_distance"]
curvature_threshold = params["curvature_threshold"]
depth_threshold_low = params["depth_threshold_low"]
depth_threshold_high = params["depth_threshold_high"]
inter_radius = params["inter_radius"]
duplicate_threshold = params["duplicate_threshold"]
n_segment_start = params["n_segment_start"]
n_segment_end = params["n_segment_end"]
num_neighbors = params["num_neighbors"]
num_interpolations = params["num_interpolations"]
resolution = params["resolution"]
window_size = params["window_size"]
# Optional: some historical overlays omit it; default matches canonical t1&2.
ring_spacing_factor = float(params.get("ring_spacing_factor", 1.2))
coverage_mode = params.get("coverage_mode", "half_from_min")
use_upsampled_surface = bool(params.get("use_upsampled_surface", True))
enable_outlier_interpolation = bool(params.get("enable_outlier_interpolation", True))
curvature_outlier_min = params.get("curvature_outlier_min", None)
# Fill NaNs within this distance of valid depth (metres). 0 disables.
max_hole_fill_m = float(params.get("max_hole_fill_m", 0.0))
# Fully inpaint NaN components up to this area (px); skips the largest component.
max_enclosed_hole_px = int(params.get("max_enclosed_hole_px", 0))
# Fill interior row gaps between first/last valid sample; edge fill invents borders.
fill_depth_row_spans = bool(params.get("fill_depth_row_spans", False))
fill_depth_row_edges = bool(params.get("fill_depth_row_edges", False))
# Final bridge for leftover gaps (metres), e.g. full-nan theta bands. 0 disables.
max_gap_bridge_m = float(params.get("max_gap_bridge_m", 0.0))
# Drop leading/trailing columns with NaN fraction above this (None/1 disables).
trim_sparse_col_nan_frac = params.get("trim_sparse_col_nan_frac", None)
if trim_sparse_col_nan_frac is not None:
    trim_sparse_col_nan_frac = float(trim_sparse_col_nan_frac)
# Optional [lo, hi] percentile clip on axial h when building the depth-map bbox.
# Removes empty tails from sparse scan ends without inventing depth.
_h_clip = params.get("depth_map_h_percentile")
depth_map_h_percentile = None
if _h_clip is not None:
    if not (isinstance(_h_clip, (list, tuple)) and len(_h_clip) == 2):
        sys.exit("depth_map_h_percentile must be [low, high], e.g. [1, 99]")
    depth_map_h_percentile = (float(_h_clip[0]), float(_h_clip[1]))
print(
    f"T3 enhancing flags: coverage_mode={coverage_mode}, "
    f"use_upsampled_surface={use_upsampled_surface}, "
    f"enable_outlier_interpolation={enable_outlier_interpolation}, "
    f"curvature_outlier_min={curvature_outlier_min}, "
    f"max_hole_fill_m={max_hole_fill_m}, max_enclosed_hole_px={max_enclosed_hole_px}, "
    f"fill_depth_row_spans={fill_depth_row_spans}, fill_depth_row_edges={fill_depth_row_edges}, "
    f"max_gap_bridge_m={max_gap_bridge_m}, trim_sparse_col_nan_frac={trim_sparse_col_nan_frac}, "
    f"depth_map_h_percentile={depth_map_h_percentile}"
)

paths = ensure_dir(tunnel_id)
state = load_state(paths["state"])
df_point_cloud = state["df_point_cloud"]
ring_count = state["ring_count"]

# Cell 1
df_support_filtered = df_point_cloud[df_point_cloud['pred'] != 0]
df_support_filtered.tail()

# Cell 2
# curvature calculation or you can use cloudcompare
import numpy as np
from scipy.spatial import KDTree
import numba as nb
from numba import njit, prange

@njit(parallel=True)
def calculate_curvatures(points, indices, k):
    curvatures = np.zeros(len(points))
    for i in prange(len(points)):
        neighbors = points[indices[i, 1:]]
        cov_matrix = np.cov(neighbors.T)
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        curvatures[i] = eigenvalues[0] / np.sum(eigenvalues)
    return curvatures

def compute_curvature(df, k=20):
    points = df[['x', 'y', 'z']].values
    tree = KDTree(points)
    
    _, indices = tree.query(points, k=k+1)
    
    # curvature calculation
    curvatures = calculate_curvatures(points, indices, k)
    
    df = df.copy()  # Create a copy to ensure we're working with a new DataFrame
    df.loc[:, 'curvature'] = curvatures
    return df

df_support_filtered_curva = compute_curvature(df_support_filtered)
df_support_filtered_curva.head()

# ## 1. enhance the surface of segment

# Cell 5
import time
from scipy.spatial import cKDTree
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
import numba as nb
from numba import njit, prange

@njit(parallel=False)
def compute_midpoints_and_filter(points, indices, distances, target_distance, curvature_threshold):
    num_points = len(points)
    max_new_points = num_points * (len(indices[0]) - 1)
    new_points = np.zeros((max_new_points, points.shape[1]), dtype=np.float64)
    new_points_count = 0
    
    for i in nb.prange(len(points)):
        for j in range(1, len(indices[i])):
            dist = distances[i, j]
            idx = indices[i, j]
            curvature_diff = abs(points[i, 3] - points[idx, 3])
            if 0.9 * target_distance <= dist <= 2 * target_distance and curvature_diff <= curvature_threshold:
                mid_point = (points[i, :2] + points[idx, :2]) / 2
                mid_r = (points[i, 2] + points[idx, 2]) / 2
                mid_curvature = (points[i, 3] + points[idx, 3]) / 2
                mid_intensity = (points[i, 4] + points[idx, 4]) / 2
                new_point = np.array([mid_point[0], mid_point[1], mid_r, mid_curvature, mid_intensity])

                new_points[new_points_count] = new_point
                new_points_count += 1
    return new_points[:new_points_count]

@njit(parallel=False)
def _filter_points_to_keep(neighbors_array, valid_mask, num_points):

    keep_indices = np.zeros(num_points, dtype=np.int32)
    count = 0
    removed_indices = np.zeros(num_points, dtype=np.int32)

    for i in prange(num_points):
        if removed_indices[i] == 0:
            keep_indices[count] = i
            count += 1
            # Mark all neighbors as needing removal
            for j in range(neighbors_array.shape[1]):
                neighbor_idx = neighbors_array[i, j]
                if valid_mask[i, j] and removed_indices[neighbor_idx] == 0:
                    removed_indices[neighbor_idx] = 1

    return keep_indices[:count]

def optimized_radius_filter(df, target_distance):
    points = df[['h', 'theta']].values
    r_dist = 0.15 * target_distance
    num_points = len(points)
    tree = cKDTree(points)
    
    neighbors_list = tree.query_ball_point(points, r=r_dist)
    max_neighbors = max(len(neighbors) for neighbors in neighbors_list)
    neighbors_array = np.full((len(points), max_neighbors), -1, dtype=np.int32)
    valid_mask = np.zeros((len(points), max_neighbors), dtype=np.bool_)
    
    for i in range(len(points)):
        length = len(neighbors_list[i])
        neighbors_array[i, :length] = neighbors_list[i]
        valid_mask[i, :length] = True
    
    keep_indices = _filter_points_to_keep(neighbors_array, valid_mask, num_points)
    filtered_df = df.iloc[keep_indices].reset_index(drop=True)
    
    return filtered_df

# -----main function-----
def enhance_segment_surface(df, target_distance=0.08, curvature_threshold_param=0.0005, num_neighbors_param=20):
    start_time = time.time()
    
    print('reading points ...')
    points = df[['h', 'theta', 'r', 'curvature', 'intensity']].values
    original_points = points[:, :2]

    print('KDTree generation ...')
    original_tree = cKDTree(original_points)
    
    distances, indices = original_tree.query(original_points, k=min(num_neighbors_param + 1, len(points)))

    print('midpoint calculation ...')
    all_new_points = compute_midpoints_and_filter(points, indices, distances, target_distance, curvature_threshold_param)

    print('filter out excess points ...')
    distances, _ = original_tree.query(all_new_points[:, :2], k=1)
        
    distances_flat = distances.flatten()
    valid_new_points = all_new_points[distances_flat >= 0.2 * target_distance]
        
    add_point_df = pd.DataFrame(valid_new_points, columns=['h', 'theta', 'r', 'curvature', 'intensity'])
    add_point_df = add_point_df[(add_point_df != 0).any(axis=1)]
            
    add_point_df['pred'] = 8
            
    add_point_df_rf = optimized_radius_filter(add_point_df, target_distance)

    new_df = add_point_df_rf.reset_index(drop=True)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"insert_midpoints function took {elapsed_time:.2f} seconds with target distance is", target_distance)
    print('The number of newly added interpolation points is', len(new_df))

    return new_df


# Cell 6
# Define the parameters for each upsampling step
upsampling_params = [
    {'target_distance': upsampling_stage1_target_distance},  # First upsampling
    {'target_distance': upsampling_stage2_target_distance},  # Second upsampling
    {'target_distance': upsampling_stage3_target_distance}   # Third upsampling
]

# Initialize the DataFrame for upsampling
df_upsampling_all = df_support_filtered_curva

if use_upsampled_surface:
    # Loop through the parameters and perform upsampling
    for params in upsampling_params:
        df_upsampling = enhance_segment_surface(
            df_upsampling_all,
            target_distance=params.get('target_distance'),
            curvature_threshold_param=curvature_threshold,
            num_neighbors_param=num_neighbors,
        )
        df_upsampling_all = pd.concat([df_upsampling_all, df_upsampling], ignore_index=False)
else:
    print("Literal mode: skipping surface upsampling (will project pred==7 later)")

df_enhance_segment = df_upsampling_all

# ## 2. enhance the outlier points

# Cell 9
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from tqdm.auto import tqdm
from numba import njit, prange
import time

def enhance_outlier_points(df, depth_threshold_low=0.003, depth_threshold_high=0.008,
                           inter_radius=0.06, num_interpolations=2, duplicate_threshold=0.02, n_segment=[10,21], resolution=0.005):
    """
    Process point cloud data to find points with significant local depth changes,
    and interpolate new points between them to enhance boundaries.

    Parameters:
    - df: DataFrame containing the point cloud data.
    - depth_threshold_low/high: Threshold for depth variation to determine significant points in low/high density area.
    - inter_radius: Distance range between interpolation points. This is mainly decided by the distance from bolt to edge, avoiding unless interpolation.
    - num_interpolations: Number of interpolation points between each pair of points, default is 2.
    - duplicate_threshold: Distance threshold for determining duplicate points.
    - n_segment: Range of high-density area, total 11 rings, 5 before to 5 rings after plus the ring put scanner.
    - resolution: image resolution, like a lower bound to ensure that interpolated points are applied to every pixel.

    Returns:
    - df_upsample: The processed DataFrame including the original points, new interpolated points, and their attributes.
    - meaningful_df: DataFrame containing only the outlier points.
    - new_df: DataFrame containing only the interpolated points
    """
    start_time = time.time()
    
    # Extract relevant columns and values
    print('reading points ...')
    points = df[['h', 'theta', 'r', 'intensity']].values
    points_array = points[:, :3]  # (h, theta, r) coordinates
    z_values = df['r'].values  # z values for depth
    
    # Construct KDTree using (h, theta) coordinates
    print('KDTree generation ...')
    tree = cKDTree(points_array[:, :2])
    
    # Query each point's 20 nearest neighbors (excluding the point itself)
    distances, indices = tree.query(points_array[:, :2], k=21)
    x_min, x_max = np.min(points[:, 0]), np.max(points[:, 0])
    if coverage_mode == "asymmetric_full":
        high_lo = x_min + ring_spacing_factor * n_segment[0]
        high_hi = x_max - ring_spacing_factor * (ring_count - n_segment[1])
    else:
        high_lo = x_min + ring_spacing_factor * n_segment[0]
        high_hi = x_min + ring_spacing_factor * n_segment[1]
    print(f"High-density window [{high_lo:.3f}, {high_hi:.3f}] mode={coverage_mode}")
    
    # Define a function to find meaningful points in parallel
    @njit(parallel=True)
    def find_meaningful_indices(points_array, z_values, indices, depth_threshold_low, depth_threshold_high, high_lo, high_hi):
        meaningful_mask = np.zeros(len(points_array), dtype=np.bool_)
        
        for i in prange(len(points_array)):
            neighbors_indices = indices[i, 1:]  # Exclude the point itself
            
            if len(neighbors_indices) < 20:
                continue
            
            neighbors_z = z_values[neighbors_indices]
            
            # Compute the average local depth difference
            average_diff = points_array[i, 2] - np.mean(neighbors_z)
            
            # If the average depth difference exceeds the threshold, mark as meaningful
            if high_lo <= points_array[i, 0] <= high_hi:
                if average_diff > depth_threshold_high:
                    meaningful_mask[i] = True
            else:
                if average_diff > depth_threshold_low:
                    meaningful_mask[i] = True
        
        return meaningful_mask
    
    # Execute the function in numba
    print('searching outlier points ...')
    meaningful_mask = find_meaningful_indices(points_array, z_values, indices, depth_threshold_low, depth_threshold_high, high_lo, high_hi)
    meaningful_indices = np.where(meaningful_mask)[0]
    print(f"Number of outlier points: {len(meaningful_indices)}")
    
    # Extract a DataFrame of meaningful points
    meaningful_df = df.iloc[meaningful_indices]

    # Define the interpolation function
    @njit(parallel=False)
    def interpolate_points(filtered_indices, points, inter_radius, num_interpolations, duplicate_threshold, resolution):
        num_indices = len(filtered_indices)
        max_new_points = num_indices * num_indices * num_interpolations
        new_points = np.zeros((max_new_points, 4))
        count = 0
    
        for i in prange(num_indices):
            index1 = filtered_indices[i]
            point1 = points[index1]
            x1, y1, z1, i1 = point1
            
            for j in range(i + 1, num_indices):
                index2 = filtered_indices[j]
                point2 = points[index2]
                x2, y2, z2, i2 = point2
                
                # distance filter
                dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                if not (resolution < dist < inter_radius):
                    continue
                
                # interpolation
                for t in np.linspace(0, 1, num=num_interpolations + 2)[1:-1]:
                    new_x = (1 - t) * x1 + t * x2
                    new_y = (1 - t) * y1 + t * y2
                    new_z = (1 - t) * z1 + t * z2
                    new_i = (1 - t) * i1 + t * i2
    
                    # delete too close point
                    if count > 0:
                        dists = np.sqrt((new_points[:count, 0] - new_x) ** 2 + (new_points[:count, 1] - new_y) ** 2)
                        if np.any(dists < duplicate_threshold):
                            continue
    
                    new_points[count] = np.array([new_x, new_y, new_z, new_i])
                    count += 1
    
        return new_points[:count]

    # Generate interpolated points
    print("filter out high density part ...")

    # Get boundary values of the points and filter out high density part
    filtered_high_density_indices = []
    for idx in meaningful_indices:
        x = points[idx, 0]
        if not (high_lo <= x <= high_hi):
            filtered_high_density_indices.append(idx)
    
    filtered_indices = np.array(filtered_high_density_indices, dtype=np.int64)

    # interpolate_points preallocates num_indices² × num_interpolations rows → OOM for ~10⁵ outliers.
    _max_pairs = 2800
    _nfi = len(filtered_indices)
    if _nfi > _max_pairs:
        _rng = np.random.default_rng(42)
        _pick = _rng.choice(_nfi, size=_max_pairs, replace=False)
        filtered_indices = filtered_indices[_pick]
        print(
            f"Note: subsampled outliers for pairwise interpolation {_nfi} → {_max_pairs} (memory / O(n²) cap)."
        )

    print("Generating interpolated points ...")

    new_points_array = interpolate_points(filtered_indices, points, inter_radius, num_interpolations, duplicate_threshold, resolution)
    
    # Add new points to DataFrame
    new_df = pd.DataFrame(new_points_array, columns=['h', 'theta', 'r', 'intensity'])
    new_df['pred'] = 8
    print(f"Number of new added points: {len(new_df)}")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"enhance_outlier_points took {elapsed_time:.2f} seconds")
    
    return meaningful_df, new_df


# Cell 10
# =================n_segment need to change!!!!===============
# The sample data is a half of one station, so n_segment should change when using entire station point cloud. 
meaningful_df, new_df = enhance_outlier_points(df_support_filtered_curva, 
                                               depth_threshold_low=depth_threshold_low,
                                               depth_threshold_high=depth_threshold_high,
                                               inter_radius=inter_radius,
                                               num_interpolations=num_interpolations,
                                               duplicate_threshold=duplicate_threshold,
                                               n_segment=[n_segment_start, n_segment_end],
                                               resolution=resolution)

if curvature_outlier_min is not None:
    before = len(meaningful_df)
    meaningful_df = meaningful_df[meaningful_df['curvature'] >= float(curvature_outlier_min)]
    print(f"Curvature filter >= {curvature_outlier_min}: {before} -> {len(meaningful_df)}")

if enable_outlier_interpolation:
    df_enhance_joint = pd.concat([meaningful_df, new_df], ignore_index=False)
else:
    print("Literal mode: skipping outlier interpolation; joints = meaningful outliers only")
    df_enhance_joint = meaningful_df.copy()

# Cell 11
# update pred 0 using meaningful_df, we believe outlier points are belong to background
df_point_cloud.loc[meaningful_df.index, 'pred'] = 0

# Cell 12
df_point_cloud.tail()

# ## 3. projection and record mapping index 

# Cell 15
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from tqdm.auto import tqdm
from collections import defaultdict

def _fill_nan_components(out, max_enclosed_hole_px):
    """Inpaint NaN components up to max area, skipping the single largest one."""
    nan_mask = np.isnan(out)
    if not np.any(nan_mask) or max_enclosed_hole_px <= 0:
        return out
    labeled, n_comp = ndimage.label(nan_mask)
    if n_comp == 0:
        return out
    sizes = np.asarray(
        ndimage.sum(nan_mask, labeled, index=np.arange(1, n_comp + 1))
    )
    largest_lab = int(np.argmax(sizes) + 1)
    _, nearest = ndimage.distance_transform_edt(nan_mask, return_indices=True)
    for lab in range(1, n_comp + 1):
        if lab == largest_lab:
            continue
        size = int(sizes[lab - 1])
        if size == 0 or size > max_enclosed_hole_px:
            continue
        comp = labeled == lab
        out[comp] = out[nearest[0][comp], nearest[1][comp]]
    return out


def _fill_row_spans_and_edges(out, fill_edges=True):
    """
    Per-row inpainting without circular distance disks.

    - Span fill: NaNs between the first and last valid sample on a row.
    - Edge fill (optional): leading/trailing NaNs outside that span. Prefer
      cropping sparse axial tails instead of edge fill when the left/right
      margin is mostly empty — edge fill invents streaky borders.
    """
    height, width = out.shape
    for y in range(height):
        row = out[y]
        valid = np.where(~np.isnan(row))[0]
        if valid.size == 0:
            continue
        lo, hi = int(valid[0]), int(valid[-1])
        if hi > lo:
            gap = np.isnan(row[lo : hi + 1])
            if np.any(gap):
                idx = valid
                xs = np.where(gap)[0] + lo
                # nearest valid along the same row
                j = np.searchsorted(idx, xs)
                j = np.clip(j, 1, len(idx) - 1)
                left = idx[j - 1]
                right = idx[j]
                use_right = (xs - left) > (right - xs)
                src = np.where(use_right, right, left)
                row[xs] = row[src]
        if fill_edges:
            if lo > 0:
                row[:lo] = row[lo]
            if hi + 1 < width:
                row[hi + 1 :] = row[hi]
        out[y] = row
    return out


def _trim_sparse_depth_margins(depth_map, max_col_nan_frac=0.25):
    """
    Drop leading/trailing columns whose NaN fraction exceeds max_col_nan_frac.

    Removes empty left/right scan tails (the large circular white bites) without
    inventing depth via edge extrapolation.

    Returns (trimmed_map, col_lo) where col_lo is the left crop offset in the
    pre-trim frame (0 if no trim).
    """
    if max_col_nan_frac is None or max_col_nan_frac >= 1.0:
        return depth_map, 0
    nan_frac = np.isnan(depth_map).mean(axis=0)
    keep = nan_frac <= float(max_col_nan_frac)
    if not np.any(keep):
        return depth_map, 0
    idx = np.where(keep)[0]
    lo, hi = int(idx[0]), int(idx[-1])
    # Keep a contiguous block from first to last acceptable column.
    trimmed = depth_map[:, lo : hi + 1]
    print(
        f"Trim sparse margins: cols [{lo}, {hi}] kept "
        f"(was W={depth_map.shape[1]} -> {trimmed.shape[1]}), "
        f"max_col_nan_frac={max_col_nan_frac}"
    )
    return trimmed, lo


def fill_depth_map_holes(
    depth_map,
    max_dist_px=0,
    max_enclosed_hole_px=0,
    fill_row_spans=False,
    fill_row_edges=False,
    max_gap_bridge_px=0,
    trim_sparse_col_nan_frac=None,
):
    """
    Inpaint NaN holes after sparse projection.

    - Component fill: inpaint every NaN connected component with area <=
      max_enclosed_hole_px (interior holes and small border indentations /
      theta-seam cutouts). The giant outside/coverage component is skipped.
    - Distance fill: nearest-valid grow for remaining NaNs within max_dist_px
      (seals thin corridors that keep fjord-holes attached to the exterior).
    - Second component fill: catches holes newly detached after the grow.
    - Optional row-span fill: closes gaps between first/last valid on each row.
    - Optional edge fill: extrapolate to image borders (usually worse than trim).
    - Optional gap bridge: final EDT fill for leftover gaps (e.g. full-nan
      theta bands) up to max_gap_bridge_px.
    - Optional margin trim: drop sparse leading/trailing columns.
    """
    if (
        max_dist_px <= 0
        and max_enclosed_hole_px <= 0
        and not fill_row_spans
        and not fill_row_edges
        and max_gap_bridge_px <= 0
        and trim_sparse_col_nan_frac is None
    ):
        return depth_map, 0

    out = depth_map.copy()
    if not np.any(np.isnan(out)) and trim_sparse_col_nan_frac is None:
        return out, 0

    # Trim empty axial tails first so EDT grow cannot scallop into them.
    trim_lo = 0
    if trim_sparse_col_nan_frac is not None:
        out, trim_lo = _trim_sparse_depth_margins(
            out, max_col_nan_frac=trim_sparse_col_nan_frac
        )

    if np.any(np.isnan(out)):
        out = _fill_nan_components(out, max_enclosed_hole_px)

        if max_dist_px > 0:
            still_nan = np.isnan(out)
            if np.any(still_nan):
                dist2, nearest2 = ndimage.distance_transform_edt(still_nan, return_indices=True)
                fillable = still_nan & (dist2 > 0) & (dist2 <= float(max_dist_px))
                if np.any(fillable):
                    out[fillable] = out[nearest2[0][fillable], nearest2[1][fillable]]

        # Corridors sealed by distance grow can detach fjord holes from the exterior.
        out = _fill_nan_components(out, max_enclosed_hole_px)

        if fill_row_spans or fill_row_edges:
            out = _fill_row_spans_and_edges(out, fill_edges=fill_row_edges)

        if max_gap_bridge_px > 0:
            still_nan = np.isnan(out)
            if np.any(still_nan):
                dist3, nearest3 = ndimage.distance_transform_edt(still_nan, return_indices=True)
                bridge = still_nan & (dist3 > 0) & (dist3 <= float(max_gap_bridge_px))
                if np.any(bridge):
                    out[bridge] = out[nearest3[0][bridge], nearest3[1][bridge]]

    n_filled = int(np.isnan(depth_map).sum() - np.isnan(out).sum())
    print(
        f"Hole fill: max_dist_px={max_dist_px}, max_enclosed_hole_px={max_enclosed_hole_px}, "
        f"fill_row_spans={fill_row_spans}, fill_row_edges={fill_row_edges}, "
        f"max_gap_bridge_px={max_gap_bridge_px}, "
        f"filled={n_filled}, nan% {np.isnan(depth_map).mean()*100:.2f} -> {np.isnan(out).mean()*100:.2f}, "
        f"shape {depth_map.shape} -> {out.shape}"
    )
    return out, trim_lo


def project_to_depth_map_inter(
    data1,
    data2,
    resolution=0.005,
    window_size=5,
    outlier_mode=False,
    max_hole_fill_m=0.0,
    max_enclosed_hole_px=0,
    depth_map_h_percentile=None,
    fill_row_spans=False,
    fill_row_edges=False,
    max_gap_bridge_m=0.0,
    trim_sparse_col_nan_frac=None,
):
    """
    Optimized version of the function that projects 2D point cloud data into a depth map.
    This version maintains the original filling logic and interpolation process.

    Parameters:
    data1, data2: pandas DataFrames or dictionaries containing 'x', 'y', 'z', 'pred' keys
    resolution: Float, the resolution of the depth map
    window_size: Integer, the size of the window used for interpolation

    Returns:
    depth_map: numpy array of shape (L, W) representing the depth map
    pixel_to_point: list of dictionaries mapping pixels to point indices
    """
    # Save the original indices of data1
    data1_index = data1['index']

    # Convert input to numpy arrays if they're dictionaries or DataFrames
    def to_numpy_arrays(data):
        if isinstance(data, dict):
            return np.array([data['x'], data['y'], data['z'], data['pred']])
        elif isinstance(data, pd.DataFrame):
            return data[['x', 'y', 'z', 'pred']].values.T
        return data

    data1 = to_numpy_arrays(data1)
    data2 = to_numpy_arrays(data2)
    data1_index = np.asarray(data1_index)

    # Optional axial percentile clip drops empty scan tails from the depth-map bbox.
    if depth_map_h_percentile is not None:
        h_all = np.concatenate([data1[0], data2[0]])
        x_lo, x_hi = np.percentile(h_all, list(depth_map_h_percentile))
        m1 = (data1[0] >= x_lo) & (data1[0] <= x_hi)
        m2 = (data2[0] >= x_lo) & (data2[0] <= x_hi)
        if int(m1.sum()) == 0:
            print("Depth-map h percentile clip removed all segment points; keeping full span")
        else:
            print(
                f"Depth-map h percentile clip {depth_map_h_percentile}: "
                f"h=[{x_lo:.3f}, {x_hi:.3f}] "
                f"(segment {int(m1.sum())}/{data1.shape[1]}, joint {int(m2.sum())}/{data2.shape[1]})"
            )
            data1 = data1[:, m1]
            data1_index = data1_index[m1]
            if int(m2.sum()) > 0:
                data2 = data2[:, m2]
            else:
                data2 = data1[:, :0]

    x_min = min(data1[0].min(), data2[0].min()) if data2.shape[1] else float(data1[0].min())
    x_max = max(data1[0].max(), data2[0].max()) if data2.shape[1] else float(data1[0].max())
    y_min = min(data1[1].min(), data2[1].min()) if data2.shape[1] else float(data1[1].min())
    y_max = max(data1[1].max(), data2[1].max()) if data2.shape[1] else float(data1[1].max())

    # Calculate grid dimensions
    L = int((y_max - y_min) / resolution)
    W = int((x_max - x_min) / resolution)
    print('L', L, 'W', W)

    # Initialize depth map
    depth_map = np.full((L, W), np.nan, dtype=np.float32)

    def process_data(data, index, depth_map, record_mapping=False):
        # Calculate grid indices
        grid_x = np.clip(((data[0] - x_min) / resolution).astype(int), 0, W - 1)
        grid_y = np.clip(((data[1] - y_min) / resolution).astype(int), 0, L - 1)

        # Use defaultdict to collect z values for each pixel
        pixel_z_values = defaultdict(list)
        pixel_to_point = []

        # If index is None, use default range
        if index is None:
            index = range(len(data[0]))

        for idx, (x, y, z, pred) in zip(index, zip(grid_x, grid_y, data[2], data[3])):
            pixel_z_values[(y, x)].append(z)
        
            if record_mapping and pred != 8:
                pixel_to_point.append({'pixel_x': x, 'pixel_y': y, 'index': idx})

        # Calculate median z value for each pixel and update depth map
        for (y, x), z_values in pixel_z_values.items():
            depth_map[y, x] = np.mean(z_values)

        return pixel_to_point if record_mapping else None

    # Process data1 and data2
    with tqdm(total=2 if not outlier_mode else 1, desc="Processing point clouds") as pbar:
        # Process data1 with index
        if outlier_mode == False:
            pixel_to_point = process_data(data1, data1_index, depth_map, record_mapping=True)
            pbar.update(1)
        # Process data2 without index (None is passed)
        process_data(data2, None, depth_map)
        pbar.update(1)

    if outlier_mode == False:
        print(f"Total mapped points: {len(pixel_to_point)}")

    # Use a sliding window to check if there is valid data in the neighborhood
    valid_points = []
    if window_size != 1:
        for i in tqdm(range(window_size // 2, L - window_size // 2), desc="Checking neighborhood"):
            for j in range(window_size // 2, W - window_size // 2):
                if np.isnan(depth_map[i, j]):
                    # Check if there is valid data in the window_size x window_size neighborhood
                    window = depth_map[i - window_size // 2 : i + window_size // 2 + 1,
                                       j - window_size // 2 : j + window_size // 2 + 1]
                    if np.any(~np.isnan(window)):
                        valid_points.append((i, j))

    # Get the valid (x, y) coordinates and corresponding z-values for interpolation
    interp_points = np.array(valid_points)
    if interp_points.size > 0:
        known_points = np.argwhere(~np.isnan(depth_map))
        known_values = depth_map[~np.isnan(depth_map)]
        
        # Perform interpolation using the nearest method
        with tqdm(total=1, desc="Interpolating") as pbar:
            interp_values = griddata(known_points, known_values, interp_points, method='nearest')
            pbar.update(1)
        
        # Fill in the interpolated results into the depth map
        depth_map[interp_points[:, 0], interp_points[:, 1]] = interp_values

    if outlier_mode is False and (
        max_hole_fill_m > 0
        or max_enclosed_hole_px > 0
        or fill_row_spans
        or fill_row_edges
        or max_gap_bridge_m > 0
        or trim_sparse_col_nan_frac is not None
    ):
        max_dist_px = int(round(float(max_hole_fill_m) / float(resolution))) if max_hole_fill_m > 0 else 0
        max_gap_bridge_px = (
            int(round(float(max_gap_bridge_m) / float(resolution))) if max_gap_bridge_m > 0 else 0
        )
        depth_map, trim_lo = fill_depth_map_holes(
            depth_map,
            max_dist_px=max_dist_px,
            max_enclosed_hole_px=max_enclosed_hole_px,
            fill_row_spans=fill_row_spans,
            fill_row_edges=fill_row_edges,
            max_gap_bridge_px=max_gap_bridge_px,
            trim_sparse_col_nan_frac=trim_sparse_col_nan_frac,
        )
        if trim_lo and pixel_to_point:
            w = depth_map.shape[1]
            h = depth_map.shape[0]
            shifted = []
            for rec in pixel_to_point:
                x = int(rec["pixel_x"]) - trim_lo
                y = int(rec["pixel_y"])
                if 0 <= x < w and 0 <= y < h:
                    shifted.append({"pixel_x": x, "pixel_y": y, "index": rec["index"]})
            print(
                f"pixel_to_point trim-shift lo={trim_lo}: "
                f"{len(pixel_to_point)} -> {len(shifted)}"
            )
            pixel_to_point = shifted

    if outlier_mode==True:
        pixel_to_point = []

    return depth_map, pixel_to_point


# Cell 16
if not use_upsampled_surface:
    # Notebook literal: discard upsampled cloud and project remaining lining candidates.
    print("Literal mode: projecting pred==7 surface instead of upsampled cloud")
    df_enhance_segment = df_point_cloud[df_point_cloud['pred'] == 7].copy()

data_segment = {
    'index': df_enhance_segment.index,
    'x': df_enhance_segment['h'],
    'y': df_enhance_segment['theta'],
    'z': df_enhance_segment['r'],
    'pred': df_enhance_segment['pred']
}

data_joint = {
    'x': df_enhance_joint['h'],
    'y': df_enhance_joint['theta'],
    'z': df_enhance_joint['r'],
    'pred': df_enhance_joint['pred']
}

# depth map generation, and record pixel to point
depth_map, pixel_to_point = project_to_depth_map_inter(
    data_segment,
    data_joint,
    resolution=resolution,
    window_size=window_size,
    max_hole_fill_m=max_hole_fill_m,
    max_enclosed_hole_px=max_enclosed_hole_px,
    depth_map_h_percentile=depth_map_h_percentile,
    fill_row_spans=fill_depth_row_spans,
    fill_row_edges=fill_depth_row_edges,
    max_gap_bridge_m=max_gap_bridge_m,
    trim_sparse_col_nan_frac=trim_sparse_col_nan_frac,
)
plt.figure(figsize=(12, 24))
plt.imshow(depth_map, cmap='viridis', vmin=depth_vmin, vmax=depth_vmax)
plt.axis('off')
plt.savefig(os.path.join(os.path.dirname(paths["state"]), "depth_map_viridis.png"), dpi=150, bbox_inches='tight')

def save_depth_map_exact(depth_map, resolution, filename=paths["depth_map"]):
    height, width = depth_map.shape
    dpi = 1.0 / resolution
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.imshow(depth_map, cmap='viridis', vmin=depth_vmin, vmax=depth_vmax)
    plt.savefig(filename, dpi=dpi, bbox_inches='tight', pad_inches=0)
    plt.close()

save_depth_map_exact(depth_map, resolution=resolution, filename=paths["depth_map"])

data_joint_2 = {
    'x': df_enhance_joint['h'],
    'y': df_enhance_joint['theta'],
    'z': df_enhance_joint['r'],
    'pred': df_enhance_joint['pred'],
    'intensity': df_enhance_joint['intensity'],
}
df_joint = pd.DataFrame(data_joint_2)
depth_map_outlier, _ = project_to_depth_map_inter(data_segment, df_joint, window_size=1, outlier_mode=True)
np.save(paths["depth_map_outlier"], depth_map_outlier)

np.save(os.path.join(os.path.dirname(paths["depth_map"]), "depth_map.npy"), depth_map)
df_point_cloud.to_csv(paths["enhanced_csv"], index=False)
with open(paths["pixel_to_point"], "wb") as f:
    pickle.dump(pixel_to_point, f)
state.update({
    "df_point_cloud": df_point_cloud,
    "df_enhance_segment": df_enhance_segment,
    "df_enhance_joint": df_enhance_joint,
    "depth_map": depth_map,
    "depth_map_outlier": depth_map_outlier,
    "pixel_to_point": pixel_to_point,
    "resolution": resolution,
})
save_state(paths["state"], state)
print(f"Enhancing complete -> {paths['enhanced_csv']}, {paths['depth_map']}")

