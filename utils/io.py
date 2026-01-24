# utils/io.py

import json
from config import CLASS_NAMES, WINDOW_SEC, HOP_SEC

def intensity_to_json(
    wav_name, times, intensities,
    aggregation, smoothing, threshold
):
    """
    Convert intensity data to JSON format
    
    Args:
        wav_name: Name of the audio file
        times: List of time points
        intensities: Array of intensity values
        aggregation: Aggregation method used
        smoothing: Smoothing window size
        threshold: Detection threshold
    
    Returns:
        Dictionary in JSON format
    """
    return {
        "audio_file": wav_name,
        "segment_duration_sec": WINDOW_SEC,
        "hop_duration_sec": HOP_SEC,
        "aggregation": aggregation,
        "smoothing": smoothing,
        "threshold": threshold,
        "classes": CLASS_NAMES,
        "timeline": [
            {
                "time_sec": float(t),
                "intensity": {
                    cls: float(vals[i])
                    for i, cls in enumerate(CLASS_NAMES)
                }
            }
            for t, vals in zip(times, intensities)
        ]
    }