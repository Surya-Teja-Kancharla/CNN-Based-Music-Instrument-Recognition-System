import numpy as np
from config import TARGET_SR, WINDOW_SEC, HOP_SEC

def sliding_windows(audio, sr=TARGET_SR, window_sec=WINDOW_SEC, hop_sec=HOP_SEC):
    """
    Create sliding windows from audio
    
    Args:
        audio: Audio time series
        sr: Sample rate
        window_sec: Window duration in seconds
        hop_sec: Hop duration in seconds
    
    Returns:
        segments: List of audio segments
        times: List of start times for each segment
    """
    window_samples = int(window_sec * sr)
    hop_samples = int(hop_sec * sr)
    
    segments = []
    times = []
    
    for start in range(0, len(audio), hop_samples):
        end = start + window_samples
        
        if end > len(audio):
            # Pad last segment if needed
            segment = np.pad(audio[start:], (0, end - len(audio)), mode='constant')
        else:
            segment = audio[start:end]
        
        segments.append(segment)
        times.append(start / sr)
        
        # Break if we've processed the whole audio
        if end >= len(audio):
            break
    
    return segments, times