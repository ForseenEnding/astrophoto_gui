from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from core.analysis.analysis_manager import analysis_manager, ImageReadyEvent, AreaOfInterest
from datetime import datetime, timezone


class HistogramWorker(QRunnable):
    def __init__(self, event: ImageReadyEvent, bins: int, result: Signal):
        super().__init__()
        self.event = event
        self.rgb = event.rgb
        self.bins = bins
        self.result = result
        # Use event AOI if present, else fallback
        self.area_of_interest = event.aoi
    def run(self):
        rgb = self.rgb
        if self.area_of_interest is not None:
            x, y, w, h = self.area_of_interest.x, self.area_of_interest.y, self.area_of_interest.width, self.area_of_interest.height
            rgb = rgb[y:y+h, x:x+w]
        r = HistogramChannel.calculate('r', rgb[..., 0].flatten(), self.bins)
        g = HistogramChannel.calculate('g',  rgb[..., 1].flatten(), self.bins)
        b = HistogramChannel.calculate('b', rgb[..., 2].flatten(), self.bins)
        luminance = HistogramChannel.calculate('luminance',  
            (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).flatten(), self.bins)
        self.result.emit(Histogram(r, g, b, luminance, self.event.image_id))
    
@dataclass
class HistogramChannel:
    def __init__(self, name: str, hist: List[int], black_point: int, white_point: int, mean: float, median: float, std: float, mode: int, clipped_left: bool, clipped_right: bool):
        self.name = name
        self.hist = hist
        self.black_point = black_point
        self.white_point = white_point
        self.mean = mean
        self.median = median
        self.std = std
        self.mode = mode
        self.clipped_left = clipped_left
        self.clipped_right = clipped_right
        
    @classmethod
    def calculate(cls, name: str, channel_data: np.ndarray, bins: int = 256) -> 'HistogramChannel':
        hist, _ = np.histogram(channel_data, bins=bins, range=(0, 255))
        non_zero = np.nonzero(hist)[0]
        black_point = int(non_zero[0]) if len(non_zero) > 0 else 0
        white_point = int(non_zero[-1]) if len(non_zero) > 0 else bins - 1
        mean = float(np.mean(channel_data))
        median = float(np.median(channel_data))
        std = float(np.std(channel_data))
        mode = int(np.argmax(hist))
        clipped_left = hist[0] > 0
        clipped_right = hist[-1] > 0
        return cls(name, hist, black_point, white_point, mean, median, std, mode, clipped_left, clipped_right)

@dataclass
class Histogram:
            
    r: HistogramChannel
    g: HistogramChannel
    b: HistogramChannel
    luminance: HistogramChannel
    image_id: str
    timestamp: datetime
    
    def __init__(self, r: HistogramChannel, g: HistogramChannel, b: HistogramChannel, luminance: HistogramChannel, image_id: str):
        self.r = r
        self.g = g
        self.b = b
        self.luminance = luminance
        self.image_id = image_id
        self.timestamp = datetime.now(timezone.utc)

class HistogramManager(QObject):
    histogram_completed = Signal(Histogram)
    channels_changed = Signal(dict)
    _bins: int
    _r: bool
    
    def __init__(self):
        super().__init__()
        self._enabled = False
        self._bins = 256
        self._channels = {'r': True, 'g': True, 'b': True, 'luminance': True}
        analysis_manager.image_ready.connect(self._on_image_ready)
        
    def _on_image_ready(self, event: ImageReadyEvent):
        if not self._enabled:
            return
        QThreadPool.globalInstance().start(HistogramWorker(event, self._bins, self.histogram_completed))
        
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        
    def set_bins(self, bins: int):
        self._bins = bins
        
    def get_enabled(self) -> bool:
        return self._enabled
    
    def get_bins(self) -> int:
        return self._bins

    def set_channel_enabled(self, channel, enabled):
        if channel in self._channels:
            self._channels[channel] = enabled
            self.channels_changed.emit(self._channels.copy())

    def get_channels(self):
        return self._channels.copy()
        
histogram_manager = HistogramManager()