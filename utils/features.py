import librosa
import numpy as np
from config import N_MELS, EPS, SEGMENT_DURATION, HOP_LENGTH, TARGET_SR

def generate_log_mel(audio, sr):
    """
    Generate log-mel spectrogram from audio
    
    Args:
        audio: Audio time series
        sr: Sample rate
    
    Returns:
        Normalized log-mel spectrogram
    """
    mel = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_fft=2048,
        hop_length=512,
        win_length=2048,
        n_mels=N_MELS,
        power=2.0
    )
    mel_db = librosa.power_to_db(mel, ref=np.max)
    return (mel_db - mel_db.mean()) / (mel_db.std() + EPS)

def fix_mel_frames(mel, sr=TARGET_SR):
    """
    Fix mel spectrogram to target number of frames
    
    Args:
        mel: Mel spectrogram
        sr: Sample rate (default: TARGET_SR)
    
    Returns:
        Fixed mel spectrogram with target frames
    """
    # Calculate TARGET_FRAMES based on SEGMENT_DURATION and HOP_LENGTH
    TARGET_FRAMES = int(np.ceil(SEGMENT_DURATION * sr / HOP_LENGTH))
    
    if mel.shape[1] < TARGET_FRAMES:
        # Pad if too short
        mel = np.pad(mel, ((0, 0), (0, TARGET_FRAMES - mel.shape[1])), mode='constant')
    
    # Return only target frames
    return mel[:, :TARGET_FRAMES]