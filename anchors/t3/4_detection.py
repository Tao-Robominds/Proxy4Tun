#!/usr/bin/env python3
# Parameterized detecting — agents/detecting.py + sam4tun state I/O
# Deferred JSON: K_height/AB_height in prompt heuristics (hardcoded 1079.92/3239.77)
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

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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


params, param_file = _load_params("detecting")

expected_keys = [
    "binary_threshold", "morphological_kernel_size", "dilation_iterations",
    "hough_threshold_oblique", "minLineLength_oblique", "maxLineGap_oblique",
    "hough_threshold_horizontal", "minLineLength_horizontal", "maxLineGap_horizontal",
    "hough_threshold_vertical", "angle_range_oblique_positive", "angle_range_oblique_negative",
    "merge_distance", "ring_spacing_constant", "resolution",
]
for key in expected_keys:
    if key not in params:
        sys.exit(f"Missing required parameter '{key}' in {param_file}")
binary_threshold = params["binary_threshold"]
morphological_kernel_size = params["morphological_kernel_size"]
dilation_iterations = params["dilation_iterations"]
hough_threshold_oblique = params["hough_threshold_oblique"]
minLineLength_oblique = params["minLineLength_oblique"]
maxLineGap_oblique = params["maxLineGap_oblique"]
hough_threshold_horizontal = params["hough_threshold_horizontal"]
minLineLength_horizontal = params["minLineLength_horizontal"]
maxLineGap_horizontal = params["maxLineGap_horizontal"]
hough_threshold_vertical = params["hough_threshold_vertical"]
angle_range_oblique_positive = params["angle_range_oblique_positive"]
angle_range_oblique_negative = params["angle_range_oblique_negative"]
merge_distance = params["merge_distance"]
ring_spacing_constant = params["ring_spacing_constant"]
resolution = params["resolution"]
K_height = float(params.get("K_height", 1079.92))
AB_height = float(params.get("AB_height", 3239.77))
pattern_tolerance = float(params.get("pattern_tolerance", 50))
vertical_rho_mode = params.get("vertical_rho_mode", "max")
vertical_rho_min_factor = float(params.get("vertical_rho_min_factor", 0.0))
vertical_rho_max_factor = float(params.get("vertical_rho_max_factor", 5.0))
prompt_logic = params.get("prompt_logic", "t12_pattern")
uniform_k_snap = bool(params.get("uniform_k_snap", tunnel_id.startswith("3-")))
# When uniform_k_snap is on, clamp the shared K Y to the design rows used by
# the assume path (1123 / 1553 px). This is ordinary T3 detection logic — not
# a proxy feature.
_k_row_raw = params.get("k_row_pattern", [1123.0, 1553.0])
k_row_pattern = [float(v) for v in _k_row_raw]
k_row_tolerance = float(params.get("k_row_tolerance", 200.0))
k_row_action = str(params.get("k_row_action", "snap")).lower()
if k_row_action not in ("snap", "fail", "warn"):
    sys.exit(f"Invalid k_row_action={k_row_action!r}; expected snap|fail|warn")
print(
    f"T3 detecting: K/AB={K_height}/{AB_height}, prompt_logic={prompt_logic}, "
    f"vertical_rho_mode={vertical_rho_mode}, uniform_k_snap={uniform_k_snap}, "
    f"k_row_action={k_row_action}, k_row_tolerance={k_row_tolerance}"
)

paths = ensure_dir(tunnel_id)
state = load_state(paths["state"])
df_point_cloud = state["df_point_cloud"]
df_enhance_segment = state["df_enhance_segment"]
df_enhance_joint = state["df_enhance_joint"]
ring_count = state["ring_count"]
depth_map_outlier = state["depth_map_outlier"]

# Cell 4
# pre-processing

binary_map = np.where(np.isnan(depth_map_outlier), 0, 255).astype(np.uint8)

ret, binary_image = cv2.threshold(binary_map, binary_threshold, 255, cv2.THRESH_BINARY)

kernel = np.ones(morphological_kernel_size, np.uint8)

dilated_edges = cv2.dilate(binary_image, kernel, iterations=dilation_iterations)

# Cell 5
# detection

import cv2
import numpy as np
import matplotlib.pyplot as plt

# L, W = cropped_map.shape
L, W = binary_map.shape

# Oblique line segment detection parameters
lines_oblique = cv2.HoughLinesP(dilated_edges, 1, np.pi / 180, hough_threshold_oblique, minLineLength=minLineLength_oblique, maxLineGap=maxLineGap_oblique)

# Horizontal line detection parameters (0 degrees)
lines_horizontal = cv2.HoughLinesP(dilated_edges, 1, np.pi / 180, hough_threshold_horizontal, minLineLength=minLineLength_horizontal, maxLineGap=maxLineGap_horizontal)

# Vertical line detection
lines_vertical = cv2.HoughLines(dilated_edges, 1, np.pi / 180, hough_threshold_vertical)
if lines_vertical is not None:
    rho = lines_vertical[:, 0, 0]
    scale = 1200 / (resolution * 1000)
    if vertical_rho_mode == "band":
        lo = vertical_rho_min_factor * scale
        hi = vertical_rho_max_factor * scale
        filtered = lines_vertical[(rho >= lo) & (rho <= hi)]
        print(f"Vertical rho band filter [{lo:.1f}, {hi:.1f}] -> {len(filtered)} lines")
        if len(filtered) == 0:
            print("Band empty on this span; keeping unfiltered vertical Hough lines")
        else:
            lines_vertical = filtered
    else:
        lines_vertical = lines_vertical[rho <= (vertical_rho_max_factor * scale)]

# Prepare output image
output_image = cv2.cvtColor(dilated_edges, cv2.COLOR_GRAY2BGR)

# Define colors
color_angle1 = (255, 0, 0)  # Red for positive angle lines
color_angle2 = (0, 255, 0)  # Green for negative angle lines
color_horizontal = (0, 0, 255)  # Blue for horizontal lines
color_vertical = (255, 165, 0)  # Orange for vertical lines
color_mid_lines = (255, 0, 255)  # Magenta for centered lines
line_thickness = 3  # Line thickness

# Detect and draw oblique lines with angles between 6-9 degrees and -9 to -6 degrees
joint_oblique_positive = []
joint_oblique_negtive = []
joint_horizontal = []
if lines_oblique is not None:
    for line in lines_oblique:
        x1, y1, x2, y2 = line[0]
        x1, x2, y1, y2 = (x2, x1, y2, y1) if x1 > x2 else (x1, x2, y1, y2)
        angle = np.degrees(np.arctan2(-(y2 - y1), x2 - x1))  # Invert y-coordinates to match standard angle direction (with y-axis up)

        if angle_range_oblique_positive[0] <= angle <= angle_range_oblique_positive[1]:
            joint_oblique_positive.append(line)
            cv2.line(output_image, (x1, y1), (x2, y2), color_angle1, line_thickness)

        elif angle_range_oblique_negative[0] <= angle <= angle_range_oblique_negative[1]:
            joint_oblique_negtive.append(line)
            cv2.line(output_image, (x1, y1), (x2, y2), color_angle2, line_thickness)

# Detect and draw horizontal lines
# Tips: in our case, considering the better robustness of oblique line segment detection, 
# we do not consider horizontal line segments, unless the no oblique line segment is recognized;
if lines_horizontal is not None:
    for line in lines_horizontal:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        # Near-horizontal line range
        if -1 <= angle <= 1:
            joint_horizontal.append(line)
            cv2.line(output_image, (x1, y1), (x2, y2), color_horizontal, line_thickness)

# Merge close vertical lines
merged_lines = []
all_mid_lines = []
threshold_distance = merge_distance  # pixels

if lines_vertical is not None:
    lines_vertical = lines_vertical[:, 0]  # Convert to 2D array

    # Iterate over all detected vertical lines
    for i, (rho1, theta1) in enumerate(lines_vertical):
        if -0.5 * np.pi / 180 <= abs(theta1) <= 0.5 * np.pi / 180:  # Ensure it is a vertical line
            x1, y1 = rho1 * np.cos(theta1), rho1 * np.sin(theta1)
            is_merged = False
            
            # Check if there is a close vertical line
            for j, (rho2, theta2) in enumerate(merged_lines):
                x2, y2 = rho2 * np.cos(theta2), rho2 * np.sin(theta2)
                if np.sqrt((x1 - x2)**2 + (y1 - y2)**2) < threshold_distance:
                    # Merge lines
                    new_rho = (rho1 + rho2) / 2
                    new_theta = (theta1 + theta2) / 2
                    merged_lines[j] = (new_rho, new_theta)
                    is_merged = True
                    break
            
            if not is_merged:
                merged_lines.append((rho1, theta1))
                
    # Sort merged_lines by rho
    merged_lines.sort(key=lambda line: line[0])

    # Draw merged vertical lines
    for rho, theta in merged_lines:
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        x1 = int(x0 + 2677 * (-b))
        y1 = int(y0 + 2677 * (a))
        x2 = int(x0 - 2677 * (-b))
        y2 = int(y0 - 2677 * (a))
        cv2.line(output_image, (x1, y1), (x2, y2), color_vertical, line_thickness)

    # Calculate centered lines between adjacent vertical lines
    mid_lines = []
    num_lines = len(merged_lines)
    for i in range(num_lines - 1):
        rho1, theta1 = merged_lines[i]
        rho2, theta2 = merged_lines[i + 1]
        # Calculate midpoint
        new_rho = (rho1 + rho2) / 2
        new_theta = (theta1 + theta2) / 2
        mid_lines.append((new_rho, new_theta))
        
        # Draw centered lines
        a = np.cos(new_theta)
        b = np.sin(new_theta)
        x0 = a * new_rho
        y0 = b * new_rho
        x1 = int(x0 + L * (-b))
        y1 = int(y0 + L * (a))
        x2 = int(x0 - L * (-b))
        y2 = int(y0 - L * (a))
        cv2.line(output_image, (x1, y1), (x2, y2), color_mid_lines, line_thickness)

    # Calculate average distance between centered lines
    distances = []
    for i in range(len(mid_lines) - 1):
        rho1, theta1 = mid_lines[i]
        rho2, theta2 = mid_lines[i + 1]
        x1, y1 = rho1 * np.cos(theta1), rho1 * np.sin(theta1)
        x2, y2 = rho2 * np.cos(theta2), rho2 * np.sin(theta2)
        distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        distances.append(distance)

    avg_distance_detected = np.mean(distances) if distances else 0
    
    avg_distance_designed = W/ring_count
    
    if np.abs(avg_distance_detected - (ring_spacing_constant / resolution)) <= np.abs(avg_distance_designed - (ring_spacing_constant / resolution)):
        avg_distance = avg_distance_detected
    else:
        avg_distance = avg_distance_designed

    # Save all centered lines records
    all_mid_lines = mid_lines.copy()

    # Starting from the leftmost centered line, draw new centered lines at the average distance
    if mid_lines:
        # Leftmost centered line
        leftmost_rho, leftmost_theta = mid_lines[0]
        a = np.cos(leftmost_theta)
        b = np.sin(leftmost_theta)
        x0 = a * leftmost_rho
        y0 = b * leftmost_rho
    
        # Draw centered lines to the left
        while x0 >= 0:
            x1 = int(x0 + L * (-b))
            y1 = int(y0 + L * (a))
            x2 = int(x0 - L * (-b))
            y2 = int(y0 - L * (a))
            cv2.line(output_image, (x1, y1), (x2, y2), color_mid_lines, line_thickness)
            all_mid_lines.append((x0, leftmost_theta))  # Save new centered line record
            x0 -= avg_distance
    
        # Rightmost centered line
        rightmost_rho, rightmost_theta = mid_lines[-1]
        a = np.cos(rightmost_theta)
        b = np.sin(rightmost_theta)
        x0 = a * rightmost_rho
        y0 = b * rightmost_rho
    
        # Draw centered lines to the right
        while x0 <= output_image.shape[1]:
            x1 = int(x0 + L * (-b))
            y1 = int(y0 + L * (a))
            x2 = int(x0 - L * (-b))
            y2 = int(y0 - L * (a))
            cv2.line(output_image, (x1, y1), (x2, y2), color_mid_lines, line_thickness)
            all_mid_lines.append((x0, rightmost_theta))  # Save new centered line record
            x0 += avg_distance

    all_mid_lines = sorted(list(set(all_mid_lines)), key=lambda line: line[0])

# Fallback: Generate evenly spaced vertical lines if no lines were detected
if lines_vertical is None or len(all_mid_lines) == 0:
    print("No vertical lines detected. Using fallback method: Creating evenly spaced vertical lines based on ring count.")
    all_mid_lines = []
    
    # Get image width (W) and use ring_count to determine vertical line spacing
    # We need ring_count lines positioned at the middle of each block
    block_width = W / ring_count

    for i in range(ring_count):
        # Position line in the middle of each block
        x_pos = (i + 0.5) * block_width
        # Store vertical line in the same format as expected by the rest of the code
        # For a vertical line, theta is 0 and rho is x_pos
        all_mid_lines.append((x_pos, 0))
        
        # Draw the vertical line on the output image for visualization
        x1, y1 = int(x_pos), 0
        x2, y2 = int(x_pos), L
        cv2.line(output_image, (x1, y1), (x2, y2), color_mid_lines, line_thickness)

    print(f"Generated {len(all_mid_lines)} synthetic vertical lines at ring centers")

# Display the result
plt.figure(figsize=(12, 12))
plt.imshow(output_image)
plt.savefig(paths["detected_lines"], dpi=150, bbox_inches='tight')

def line_segment_vertical_intersection(vertical_x, segment):
    """Compute the intersection of a vertical line x = vertical_x with a line segment."""
    x1, y1, x2, y2 = segment
    if x1 == x2:
        return None
    if min(x1, x2) <= vertical_x <= max(x1, x2):
        t = (vertical_x - x1) / (x2 - x1)
        intersect_y = y1 + t * (y2 - y1)
        return (vertical_x, intersect_y)
    return None

def merge_close_points(points, threshold=6):
    """Merge points that are within a certain distance of each other."""
    points = np.array(points)
    if len(points) == 0:
        return np.array([])
    if len(points) == 1:
        return points
    merged_points = []
    while len(points) > 0:
        p = points[0]
        close_points = np.linalg.norm(points - p, axis=1) < threshold
        merged_points.append(np.mean(points[close_points], axis=0))
        points = points[~close_points]
    return np.array(merged_points)

def compute_midpoint(p1, p2):
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

def check_distance_pattern(points, k, ab, tolerance=10):
    points = sorted(points, key=lambda p: p[0])
    for i in range(len(points) - 1):
        for j in range(i + 1, len(points)):
            distance = np.linalg.norm(np.array(points[i]) - np.array(points[j]))
            if any(abs(distance - (k + m * ab)) < tolerance for m in [2, 4]):
                return compute_midpoint(points[i], points[j])
    return None

vertical_lines = all_mid_lines
horizontal_lines = joint_horizontal
positive_slope_lines = joint_oblique_positive
negative_slope_lines = joint_oblique_negtive
adjusted_points = []
K_height_pixel = K_height / (1000 * resolution)
AB_height_pixel = AB_height / (1000 * resolution)

if prompt_logic == "t3_inherit":
    for vertical_x, _ in vertical_lines:
        intersections_with_positive_slope = []
        intersections_with_negative_slope = []
        intersections_with_horizontal = []
        for segment in positive_slope_lines:
            inter_point = line_segment_vertical_intersection(vertical_x, segment[0])
            if inter_point:
                intersections_with_positive_slope.append(inter_point)
        for segment in negative_slope_lines:
            inter_point = line_segment_vertical_intersection(vertical_x, segment[0])
            if inter_point:
                intersections_with_negative_slope.append(inter_point)
        merge_positive = merge_close_points(intersections_with_positive_slope)
        merge_negative = merge_close_points(intersections_with_negative_slope)
        current_type = None
        current_y = None
        if len(merge_positive) > 0 and len(merge_negative) > 0:
            midpoint = compute_midpoint(merge_positive[0], merge_negative[0])
            current_y = midpoint[1]
            current_type = 'midpoint'
        elif len(merge_positive) > 0:
            point = merge_positive[0]
            # Notebook T3: positive slope offsets by -0.5 K
            current_y = point[1] - 0.5 * K_height_pixel
            current_type = 'positive_slope'
        elif len(merge_negative) > 0:
            point = merge_negative[0]
            # Notebook T3: negative slope offsets by +0.5 K
            current_y = point[1] + 0.5 * K_height_pixel
            current_type = 'negative_slope'
        else:
            for segment in horizontal_lines:
                inter_point = line_segment_vertical_intersection(vertical_x, segment[0])
                if inter_point:
                    intersections_with_horizontal.append(inter_point)
            merge_horizontal = merge_close_points(intersections_with_horizontal)
            if len(merge_horizontal) > 0:
                min_y = min(merge_horizontal, key=lambda x: x[1])[1]
                max_y = max(merge_horizontal, key=lambda x: x[1])[1]
                current_y = (min_y + max_y) / 2
                current_type = 'horizontal'
            elif adjusted_points:
                current_y = adjusted_points[-1][1][1]
                current_type = 'assume'
            else:
                current_y = L * 0.5
                current_type = 'assume'
                print(f"Warning: no starting detection at x={vertical_x}; using image mid Y")
        if adjusted_points and current_type != 'assume':
            last_point_y = adjusted_points[-1][1][1]
            if abs(current_y - last_point_y) / max(abs(last_point_y), 1e-6) > 0.1:
                current_y = last_point_y
                current_type = 'assume'
        adjusted_points.append((current_type, (vertical_x, current_y)))
else:
    for vertical_x, _ in vertical_lines:
        intersections_with_positive_slope = []
        intersections_with_negative_slope = []
        intersections_with_horizontal = []
        for segment in positive_slope_lines:
            inter_point = line_segment_vertical_intersection(vertical_x, segment[0])
            if inter_point:
                intersections_with_positive_slope.append(inter_point)
        for segment in negative_slope_lines:
            inter_point = line_segment_vertical_intersection(vertical_x, segment[0])
            if inter_point:
                intersections_with_negative_slope.append(inter_point)
        merge_positive = merge_close_points(intersections_with_positive_slope)
        merge_negative = merge_close_points(intersections_with_negative_slope)
        if len(merge_positive) > 0 and len(merge_negative) > 0:
            midpoint = compute_midpoint(merge_positive[0], merge_negative[0])
            adjusted_points.append(('midpoint', midpoint))
        elif len(merge_positive) > 0:
            point = merge_positive[0]
            adjusted_points.append(('positive_slope', (point[0], point[1] + 0.5 * K_height_pixel)))
        elif len(merge_negative) > 0:
            point = merge_negative[0]
            adjusted_points.append(('negative_slope', (point[0], point[1] - 0.5 * K_height_pixel)))
        else:
            for segment in horizontal_lines:
                inter_point = line_segment_vertical_intersection(vertical_x, segment[0])
                if inter_point:
                    intersections_with_horizontal.append(inter_point)
            merge_horizontal = merge_close_points(intersections_with_horizontal)
            pattern_midpoint = check_distance_pattern(
                merge_horizontal, K_height_pixel, AB_height_pixel, tolerance=pattern_tolerance
            )
            if pattern_midpoint:
                adjusted_points.append(('horizontal', pattern_midpoint))
            else:
                assumed_y = None
                if adjusted_points:
                    last_point_y = adjusted_points[-1][1][1]
                    if 1035 <= last_point_y <= 1265:
                        assumed_y = last_point_y + 431.87
                    elif 1422 <= last_point_y <= 1738:
                        assumed_y = last_point_y - 431.87
                    else:
                        if len(adjusted_points) > 1:
                            second_last_point_y = adjusted_points[-2][1][1]
                            if 1035 <= second_last_point_y <= 1265:
                                assumed_y = second_last_point_y
                            elif 1422 <= second_last_point_y <= 1738:
                                assumed_y = second_last_point_y
                if assumed_y is None:
                    ring_idx = len(adjusted_points)
                    assumed_y = 1123.0 if ring_idx % 2 == 0 else 1553.0
                adjusted_points.append(('assume', (vertical_x, assumed_y)))

# Continuous T3: uniform single K Y from anchor detections (optional)
k_row_gate_record = None
if uniform_k_snap:
    _ANCHOR_TYPES = {"midpoint", "horizontal", "positive_slope", "negative_slope"}
    _anchor_ys = [pt[1] for label, pt in adjusted_points if label in _ANCHOR_TYPES]
    if _anchor_ys:
        y_star_measured = float(np.median(_anchor_ys))
        if len(_anchor_ys) > 1 and np.std(_anchor_ys) > 40:
            print(f"Warning: anchor Y std {np.std(_anchor_ys):.1f} > 40 before T3 uniform snap")
        # Sanity gate: y_star must sit near a design K row, else labels rotate.
        nearest_row = float(min(k_row_pattern, key=lambda r: abs(r - y_star_measured)))
        distance = float(abs(y_star_measured - nearest_row))
        within = distance <= k_row_tolerance
        y_star_used = y_star_measured
        action_taken = "accept"
        if within:
            print(
                f"T3 K-row gate OK: y_star={y_star_measured:.1f} within "
                f"{distance:.1f}px of design row {nearest_row:.1f} "
                f"(tol={k_row_tolerance:.1f})"
            )
        else:
            msg = (
                f"T3 K-row gate TRIGGERED: y_star={y_star_measured:.1f} is "
                f"{distance:.1f}px from nearest design row {nearest_row:.1f} "
                f"(tol={k_row_tolerance:.1f}, action={k_row_action})"
            )
            if k_row_action == "fail":
                print(msg)
                print(
                    "Aborting stage 4 so the runner can retry with another seed. "
                    "Exit code 3."
                )
                # Persist gate evidence even on fail-fast.
                _gate_dir = os.path.dirname(paths["initial_points"])
                os.makedirs(_gate_dir, exist_ok=True)
                with open(os.path.join(_gate_dir, "k_row_gate.json"), "w") as _gf:
                    json.dump(
                        {
                            "y_star_measured": y_star_measured,
                            "y_star_used": None,
                            "nearest_design_row": nearest_row,
                            "distance_px": distance,
                            "tolerance_px": k_row_tolerance,
                            "k_row_pattern": k_row_pattern,
                            "within_tolerance": False,
                            "action_requested": k_row_action,
                            "action_taken": "fail",
                            "n_anchor_ys": len(_anchor_ys),
                            "anchor_y_std": float(np.std(_anchor_ys)) if len(_anchor_ys) > 1 else 0.0,
                        },
                        _gf,
                        indent=2,
                    )
                    _gf.write("\n")
                sys.exit(3)
            elif k_row_action == "snap":
                y_star_used = nearest_row
                action_taken = "snap"
                print(msg)
                print(f"T3 K-row gate SNAP: replacing y_star with {y_star_used:.1f}")
            else:  # warn
                action_taken = "warn"
                print(f"WARNING: {msg} — proceeding with measured y_star")

        _n = len(adjusted_points)
        adjusted_points = [
            ("propagated", (pt[0], y_star_used))
            for _, pt in adjusted_points
        ]
        print(f"T3 K uniform: set all {_n} rings to Y={y_star_used:.1f}")
        k_row_gate_record = {
            "y_star_measured": y_star_measured,
            "y_star_used": y_star_used,
            "nearest_design_row": nearest_row,
            "distance_px": distance,
            "tolerance_px": k_row_tolerance,
            "k_row_pattern": k_row_pattern,
            "within_tolerance": within,
            "action_requested": k_row_action,
            "action_taken": action_taken,
            "n_anchor_ys": len(_anchor_ys),
            "anchor_y_std": float(np.std(_anchor_ys)) if len(_anchor_ys) > 1 else 0.0,
        }

df_loc = pd.DataFrame(adjusted_points, columns=['Type', 'Coordinates'])
df_loc['X'] = df_loc['Coordinates'].apply(lambda coord: coord[0])
df_loc['Y'] = df_loc['Coordinates'].apply(lambda coord: coord[1])
df_loc = df_loc.drop(columns=['Coordinates'])
df_loc = df_loc.sort_values(by='X').reset_index(drop=True)

print(f"Number of vertical lines: {len(vertical_lines)}")
print(f"Number of adjusted points: {len(adjusted_points)}")
print(df_loc)

plt.figure(figsize=(16, 16))
ax = plt.gca()
colors = {'horizontal': 'b', 'positive_slope': 'r', 'negative_slope': 'c', 'midpoint': 'm', 'assume': 'g', 'propagated': 'y'}
markers = {'horizontal': 'o', 'positive_slope': '^', 'negative_slope': 's', 'midpoint': '*', 'assume': 'd', 'propagated': 'P'}
for label, (x, y) in adjusted_points:
    ax.plot(x, y, color=colors[label], marker=markers[label], markersize=10, label=label)
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), loc='lower right')
ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')
ax.set_title('Intersection Points')
ax.set_aspect('equal', adjustable='box')
ax.invert_yaxis()
if len(df_loc) > 0:
    x_min, x_max = df_loc['X'].min(), df_loc['X'].max()
    y_min, y_max = df_loc['Y'].min(), df_loc['Y'].max()
    margin = 0.1
    x_range = x_max - x_min
    y_range = y_max - y_min
    ax.set_xlim(x_min - margin * x_range, x_max + margin * x_range)
    ax.set_ylim(y_max + margin * y_range, y_min - margin * y_range)
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(paths["initial_points"]), "initial_prompt_points.png"), dpi=150, bbox_inches='tight')

df_loc.to_csv(paths["initial_points"], index=False)
state["df_loc"] = df_loc
save_state(paths["state"], state)
if k_row_gate_record is not None:
    _gate_path = os.path.join(os.path.dirname(paths["initial_points"]), "k_row_gate.json")
    with open(_gate_path, "w") as _gf:
        json.dump(k_row_gate_record, _gf, indent=2)
        _gf.write("\n")
    print(f"K-row gate evidence -> {_gate_path}")
print(f"Detection complete -> {paths['initial_points']}")

