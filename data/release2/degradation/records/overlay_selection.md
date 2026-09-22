# Degradation overlays

Lowest-GT-mIoU valid development trial per family. Unfolding keys dropped.

| family | source | GT mIoU | stage 2-5 keys |
| --- | --- | ---: | --- |
| staggered | 2-1/s017 | 0.0320 | denoising.mask_r_low, denoising.mask_r_high, denoising.z_step, denoising.grad_threshold, enhancing.curvature_threshold, enhancing.inter_radius, detecting.binary_threshold, detecting.hough_threshold_oblique, detecting.hough_threshold_horizontal, detecting.hough_threshold_vertical, detecting.maxLineGap_oblique, sam.processing.y_bounds |
| continuous | 3-1/s030 | 0.0420 | denoising.mask_r_low, denoising.mask_r_high, denoising.mask_theta_low, denoising.mask_theta_high, enhancing.curvature_threshold, detecting.binary_threshold, detecting.hough_threshold_oblique, detecting.hough_threshold_horizontal, detecting.hough_threshold_vertical, detecting.pattern_tolerance, sam.segment_width, sam.K_height, sam.angle |
| complex | 5-1/g001 | 0.0360 | denoising.mask_r_low, denoising.mask_r_high, enhancing.curvature_threshold, detecting.binary_threshold, detecting.hough_threshold_oblique, detecting.hough_threshold_horizontal, detecting.hough_threshold_vertical, detecting.maxLineGap_oblique, detecting.maxLineGap_horizontal, detecting.pattern_tolerance, sam.segment_width, sam.K_height, sam.angle |
