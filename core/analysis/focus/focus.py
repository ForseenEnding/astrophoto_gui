from dataclasses import dataclass
import os
from typing import Optional, Tuple
import numpy as np

@dataclass
class AreaOfInterest:
    x: int
    y: int
    width: int
    height: int

def detect_focus(
    rgb: np.ndarray,
    area_of_interest: Optional[AreaOfInterest] = None
) -> float:
    """
    Compute a simple focus metric (variance of Laplacian) for a RGB image.
    Optionally, restrict to an area of interest: (x, y, width, height).
    Returns a single float value (higher means sharper focus).
    """
    # Convert to grayscale
    gray = np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])

    # Crop to area of interest if specified
    if area_of_interest:
        x, y, w, h = area_of_interest
        gray = gray[y:y+h, x:x+w]

    # Compute Laplacian (simple kernel)
    laplacian = (
        -4 * gray +
        np.roll(gray, 1, axis=0) + np.roll(gray, -1, axis=0) +
        np.roll(gray, 1, axis=1) + np.roll(gray, -1, axis=1)
    )
    focus_metric = np.var(laplacian)
    return float(focus_metric)

# Example usage:
# sharpness = detect_focus('example.cr2', area_of_interest=(100, 100, 200, 200)) 