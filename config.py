"""
Configuration file for InstruNet AI
"""

# Audio processing parameters
TARGET_SR = 22050  # Target sampling rate
N_MELS = 128  # Number of mel bands
HOP_LENGTH = 512  # Hop length for STFT
N_FFT = 2048  # FFT window size
SEGMENT_DURATION = 3.0  # Segment duration in seconds
HOP_DURATION = 1.5  # Hop duration in seconds
TARGET_FRAMES = 126  # Expected number of time frames in mel spectrogram

# Alternative names for compatibility
WINDOW_SEC = SEGMENT_DURATION  # Alias for segment duration
HOP_SEC = HOP_DURATION  # Alias for hop duration

# Numerical stability
EPS = 1e-8  # Epsilon for numerical stability

# Class names (instrument codes)
CLASS_NAMES = [
    "cel",  # Cello
    "cla",  # Clarinet
    "flu",  # Flute
    "gac",  # Acoustic Guitar
    "gel",  # Electric Guitar
    "org",  # Organ
    "pia",  # Piano
    "sax",  # Saxophone
    "tru",  # Trumpet
    "vio",  # Violin
    "voi"   # Voice
]

# Display names for instruments
CLASS_DISPLAY_NAMES = {
    "cel": "Cello",
    "cla": "Clarinet",
    "flu": "Flute",
    "gac": "Acoustic Guitar",
    "gel": "Electric Guitar",
    "org": "Organ",
    "pia": "Piano",
    "sax": "Saxophone",
    "tru": "Trumpet",
    "vio": "Violin",
    "voi": "Voice"
}

# Icons for instruments
CLASS_ICONS = {
    "cel": "🎻",
    "cla": "🎵",
    "flu": "🪈",
    "gac": "🎸",
    "gel": "🎸",
    "org": "🎹",
    "pia": "🎹",
    "sax": "🎷",
    "tru": "🎺",
    "vio": "🎻",
    "voi": "🎤"
}

# Color scheme
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#48bb78",
    "warning": "#ed8936",
    "danger": "#f56565",
    "muted": "#9ca3af",
    "background": "#f9fafb"
}

# ==================================================
# SUPABASE CONFIGURATION (SECRETS)
# ==================================================

import os
import streamlit as st

def get_secret(key: str, default=None):
    """
    Priority:
    1. Streamlit Cloud secrets
    2. OS environment variables (.env locally)
    """
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return os.getenv(key, default)


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials are not configured")
