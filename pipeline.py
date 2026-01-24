"""
Pipeline for audio inference and analysis
"""
import numpy as np
import librosa
import json
from datetime import datetime
from config import CLASS_NAMES, TARGET_SR, N_MELS, HOP_LENGTH, N_FFT, SEGMENT_DURATION, HOP_DURATION, TARGET_FRAMES


def extract_mel_spectrogram(audio_path, sr=TARGET_SR, n_mels=N_MELS, hop_length=HOP_LENGTH, n_fft=N_FFT):
    """
    Extract mel spectrogram from audio file
    """
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=n_mels, hop_length=hop_length, n_fft=n_fft
    )
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    return mel_spec_db


def segment_audio(audio_path, segment_duration=SEGMENT_DURATION, hop_duration=HOP_DURATION, sr=TARGET_SR):
    """
    Segment audio into overlapping windows
    """
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    
    segment_samples = int(segment_duration * sr)
    hop_samples = int(hop_duration * sr)
    
    segments = []
    times = []
    
    for start in range(0, len(y), hop_samples):
        end = start + segment_samples
        if end > len(y):
            # Pad last segment if needed
            segment = np.pad(y[start:], (0, end - len(y)), mode='constant')
        else:
            segment = y[start:end]
        
        segments.append(segment)
        times.append(start / sr)
        
        # Break if we've processed the whole audio
        if end >= len(y):
            break
    
    return segments, times


def predict_segments(segments, model, sr=TARGET_SR, n_mels=N_MELS, hop_length=HOP_LENGTH, n_fft=N_FFT):
    """
    Predict instrument probabilities for each segment
    
    Model expects input shape: (batch, 128, 126, 1)
    """
    predictions = []
    
    for segment in segments:
        # Extract mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=segment, sr=sr, n_mels=n_mels, hop_length=hop_length, n_fft=n_fft
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Normalize
        mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / (mel_spec_db.std() + 1e-6)
        
        # Fix shape to match model input (128, TARGET_FRAMES)
        if mel_spec_db.shape[1] < TARGET_FRAMES:
            # Pad if too short
            pad_width = TARGET_FRAMES - mel_spec_db.shape[1]
            mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, pad_width)), mode='constant')
        elif mel_spec_db.shape[1] > TARGET_FRAMES:
            # Trim if too long
            mel_spec_db = mel_spec_db[:, :TARGET_FRAMES]
        
        # Add channel dimension and batch dimension: (1, 128, TARGET_FRAMES, 1)
        input_data = mel_spec_db[np.newaxis, ..., np.newaxis]
        
        # Predict
        pred = model.predict(input_data, verbose=0)[0]
        predictions.append(pred)
    
    return np.array(predictions)


def smooth_predictions(predictions, window_size=3):
    """
    Apply moving average smoothing to predictions
    """
    if window_size <= 1:
        return predictions
    
    smoothed = np.copy(predictions)
    n_segments, n_classes = predictions.shape
    
    for i in range(n_segments):
        start = max(0, i - window_size // 2)
        end = min(n_segments, i + window_size // 2 + 1)
        smoothed[i] = predictions[start:end].mean(axis=0)
    
    return smoothed


def aggregate_predictions(predictions, method='mean'):
    """
    Aggregate predictions across segments
    """
    if method == 'mean':
        return predictions.mean(axis=0)
    elif method == 'max':
        return predictions.max(axis=0)
    elif method == 'voting':
        # Hard voting: count segments where each class exceeds 0.5
        votes = (predictions > 0.5).sum(axis=0)
        return votes / len(predictions)
    else:
        raise ValueError(f"Unknown aggregation method: {method}")


def run_inference(audio_path, model, aggregation='mean', threshold=0.25, smoothing=3, audio_name=None):
    """
    Run complete inference pipeline
    
    Args:
        audio_path: Path to audio file
        model: Trained model
        aggregation: Aggregation method ('mean', 'max', 'voting')
        threshold: Detection threshold
        smoothing: Smoothing window size
        audio_name: Original audio filename (optional)
    
    Returns:
        smoothed: Smoothed predictions
        times: Time points for each segment
        aggregated: Aggregated predictions
        json_output: JSON output dictionary
    """
    # Segment audio
    segments, times = segment_audio(audio_path)
    
    # Predict for each segment
    predictions = predict_segments(segments, model)
    
    # Smooth predictions
    smoothed = smooth_predictions(predictions, window_size=smoothing)
    
    # Aggregate predictions
    aggregated = aggregate_predictions(smoothed, method=aggregation)
    
    # Generate JSON output
    timeline = []
    for i, time_sec in enumerate(times):
        intensity = {cls: float(smoothed[i, j]) for j, cls in enumerate(CLASS_NAMES)}
        timeline.append({
            "time_sec": float(time_sec),
            "intensity": intensity
        })
    
    # Use audio_name if provided, otherwise use audio_path
    display_name = audio_name if audio_name else audio_path
    
    json_output = {
        "audio_file": display_name,
        "segment_duration_sec": SEGMENT_DURATION,
        "hop_duration_sec": HOP_DURATION,
        "aggregation": aggregation,
        "smoothing": smoothing,
        "threshold": threshold,
        "classes": CLASS_NAMES,
        "timeline": timeline
    }
    
    return smoothed, times, aggregated, json_output