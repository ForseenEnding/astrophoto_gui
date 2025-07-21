from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass
class Histogram:
    r: List[int]
    g: List[int]
    b: List[int]

def compute_histogram(rgb: np.ndarray, bins: int = 256) -> Histogram:
    """
    Compute a simple RGB histogram for a given NumPy array.
    Returns a list of three lists (R, G, B), each containing the histogram values.
    """
    # Flatten the image into R, G, B channels
    r = rgb[..., 0].flatten()
    g = rgb[..., 1].flatten()
    b = rgb[..., 2].flatten()

    # Compute histograms
    hist_r, _ = np.histogram(r, bins=bins, range=(0, 255))
    hist_g, _ = np.histogram(g, bins=bins, range=(0, 255))
    hist_b, _ = np.histogram(b, bins=bins, range=(0, 255))

    return Histogram(
        r=hist_r.tolist(),
        g=hist_g.tolist(),
        b=hist_b.tolist()
    )