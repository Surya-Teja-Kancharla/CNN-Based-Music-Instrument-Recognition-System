TARGET_SR = 16000

WINDOW_SEC = 3.0
HOP_SEC = 1.5

N_MELS = 128
TARGET_FRAMES = 126
EPS = 1e-8

NUM_CLASSES = 11

CLASS_NAMES = [
    "cel", "cla", "flu", "gac", "gel",
    "org", "pia", "sax", "tru", "vio", "voi"
]

# Instrument Display Names (User-Friendly)
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

# Instrument Icons (Emojis)
CLASS_ICONS = {
    "cel": "🎻",
    "cla": "🎷",
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

# Color Scheme for UI
COLORS = {
    "primary": "#3b82f6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "muted": "#6b7280",
    "background": "#f9fafb"
}