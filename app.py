import streamlit as st
import tempfile
import json
import tensorflow as tf
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import bcrypt
from io import BytesIO

from pipeline import run_inference
from utils.pdf_report import generate_pdf_report
from config import CLASS_NAMES, TARGET_SR

# ==================================================
# SESSION STATE
# ==================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "results" not in st.session_state:
    st.session_state.results = None
if "pdf_figure" not in st.session_state:
    st.session_state.pdf_figure = None

# ==================================================
# SHARED PASSWORD
# ==================================================

SHARED_PASSWORD_HASH = bcrypt.hashpw(b"instrunet123", bcrypt.gensalt())

# ==================================================
# LOGIN PAGE
# ==================================================

def login_page():
    st.set_page_config(page_title="InstruNet AI – Login", layout="centered")

    st.markdown("## 🎵 InstruNet AI")
    st.markdown(
        "**Music Instrument Recognition System**  \n"
        "Secure access to the audio analysis and visualization dashboard."
    )

    username = st.text_input("Your Name")
    password = st.text_input("Access Password", type="password")

    if st.button("Login"):
        if not username.strip():
            st.error("Please enter your name.")
            return

        if bcrypt.checkpw(password.encode(), SHARED_PASSWORD_HASH):
            st.session_state.authenticated = True
            st.session_state.user = {"username": username.strip()}
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid password")

# ==================================================
# MAIN APP
# ==================================================

def main_app():
    st.set_page_config(
        page_title="InstruNet AI - Music Instrument Recognition",
        layout="wide"
    )

    st.markdown("""
        <style>
        /* ---------- GLOBAL LAYOUT FIX ---------- */
        .block-container {
            padding-top: 1.2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            padding-bottom: 2rem;
        }

        .block-container h1:first-of-type {
            margin-top: 0rem;
        }

        /* ---------- PROFILE / HEADER ---------- */
        .profile-horizontal {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: -25px;
        }

        .user-text-block {
            display: flex;
            flex-direction: column;
            justify-content: center;
            line-height: 1.1;
        }

        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: #3b82f6;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
            flex-shrink: 0;
        }

        .role-text {
            font-size: 12px;
            color: #9aa0a6;
        }

        /* ---------- LOGOUT BUTTON ---------- */
        .logout-container button {
            font-size: 12px !important;
            padding: 6px 14px !important;
            height: 36px !important;
            border-radius: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    # Using vertical_alignment="center" to keep the app title and user block level
    col_title, col_user = st.columns([4, 1.8], vertical_alignment="center")

    with col_title:
        st.title("InstruNet AI: Music Instrument Recognition")
        st.markdown(
            "Upload an audio file to analyze instrument presence, confidence, "
            "and temporal intensity."
        )

    with col_user:
        # Create two sub-columns to place info and button side-by-side
        # vertical_alignment="center" is the key for perfect horizontal alignment
        u_info, u_logout = st.columns([2, 1], vertical_alignment="center")
        
        initial = st.session_state.user["username"][0].upper()

        with u_info:
            st.markdown(
                f"""
                <div class="profile-horizontal">
                    <div class="avatar">{initial}</div>
                    <div class="user-text-block">
                        <div style="font-size: 14px; white-space: nowrap;">
                            <b>{st.session_state.user["username"]}</b>
                        </div>
                        <div class="role-text">User</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with u_logout:
            # use_container_width ensures the button doesn't look tiny in the sub-column
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.results = None
                st.session_state.pdf_figure = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ==================================================
    # SIDEBAR
    # ==================================================

    with st.sidebar:
        st.markdown("### 🎵 Upload Audio")

        audio_file = st.file_uploader(
            "Choose WAV or MP3 file",
            type=["wav", "mp3"]
        )

        audio_bytes = None
        if audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes)
            st.markdown(f"**Now Playing:** {audio_file.name}")

        st.markdown("---")
        st.markdown("### ⚙️ Analysis Settings")

        aggregation = st.selectbox(
            "Aggregation Method",
            ["mean", "max", "voting"]
        )

        threshold = st.slider(
            "Confidence Threshold",
            0.0, 1.0, 0.25
        )

        smoothing = st.slider(
            "Smoothing Window",
            1, 7, 3
        )

        run_clicked = st.button("▶ Analyze Track", use_container_width=True)

    # ==================================================
    # MAIN CONTENT
    # ==================================================

    col_main, col_right = st.columns([3, 1.4])

    with col_main:
        st.markdown("## 📊 Audio Visualization")

        if audio_bytes:
            y, sr = librosa.load(BytesIO(audio_bytes), sr=TARGET_SR, mono=True)

            st.markdown("### Waveform (Time–Amplitude Domain)")
            st.caption(
                "Displays amplitude variations over time. Useful for detecting "
                "silence, clipping, and alignment issues."
            )

            fig_wav, ax = plt.subplots(figsize=(10, 2))
            librosa.display.waveshow(y, sr=sr, ax=ax)
            ax.set_xlabel("Time (seconds)")
            ax.set_ylabel("Amplitude")
            st.pyplot(fig_wav)

            st.markdown("### Mel Spectrogram (Time–Frequency Domain)")
            st.caption(
                "Shows how spectral energy is distributed over time. This "
                "representation is the actual CNN input."
            )

            mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            mel_db = librosa.power_to_db(mel, ref=np.max)

            fig_mel, ax = plt.subplots(figsize=(10, 3))
            img = librosa.display.specshow(
                mel_db, sr=sr, x_axis="time", y_axis="mel", ax=ax
            )
            fig_mel.colorbar(img, ax=ax, format="%+2.0f dB")
            st.pyplot(fig_mel)

            st.session_state.pdf_figure = fig_mel
        else:
            st.info("Upload an audio file to view waveform and spectrogram.")

    # ==================================================
    # INFERENCE
    # ==================================================

    if audio_bytes and run_clicked:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes)
            temp_path = f.name

        model = tf.keras.models.load_model("model/best_l2_regularized_model.h5")

        _, _, aggregated, json_out = run_inference(
            temp_path, model, aggregation, threshold, smoothing
        )

        st.session_state.results = {
            "aggregated": aggregated,
            "json": json_out
        }

    # ==================================================
    # RESULTS + EXPORT
    # ==================================================

    with col_right:
        if st.session_state.results:
            st.markdown("## 🎼 Detected Instruments")

            results = st.session_state.results
            confidence_dict = {
                cls: float(results["aggregated"][i])
                for i, cls in enumerate(CLASS_NAMES)
                if results["aggregated"][i] >= threshold
            }

            for cls, score in confidence_dict.items():
                st.markdown(f"**{cls.upper()}**")
                st.progress(min(score, 1.0))

            st.markdown("---")
            st.markdown("## 📤 Export Results")

            st.download_button(
                "Export JSON",
                json.dumps(results["json"], indent=2),
                file_name="analysis.json",
                mime="application/json",
                use_container_width=True
            )

            if st.session_state.pdf_figure:
                pdf_path = generate_pdf_report(
                    audio_name="audio",
                    aggregation=aggregation,
                    threshold=threshold,
                    smoothing=smoothing,
                    confidence_dict=confidence_dict,
                    plot_figure=st.session_state.pdf_figure
                )

                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Export PDF",
                        f,
                        file_name="analysis.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

# ==================================================
# ENTRY POINT
# ==================================================

if not st.session_state.authenticated:
    login_page()
else:
    main_app()
    