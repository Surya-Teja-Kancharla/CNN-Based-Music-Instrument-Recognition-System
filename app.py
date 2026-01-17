import streamlit as st
import tempfile
import json
import os
import tensorflow as tf
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

from pipeline import run_inference
from utils.pdf_report import generate_pdf_report
from utils.visualization import create_intensity_timeline
from config import (
    CLASS_NAMES, CLASS_DISPLAY_NAMES, CLASS_ICONS,
    TARGET_SR, COLORS
)

# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "results" not in st.session_state:
    st.session_state.results = None
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "visualizations" not in st.session_state:
    st.session_state.visualizations = {}

# ==================================================
# AUTHENTICATION
# ==================================================

# Use environment variable for password, fallback to default for development
# In production, set INSTRUNET_PASSWORD environment variable
DEFAULT_PASSWORD = "instrunet2025"
SHARED_PASSWORD = os.environ.get("INSTRUNET_PASSWORD", DEFAULT_PASSWORD)

# ==================================================
# LOGIN PAGE
# ==================================================

def login_page():
    st.set_page_config(page_title="InstruNet AI – Login", layout="centered")
    
    # Center content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>" * 3, unsafe_allow_html=True)
        
        # Logo and title
        st.markdown(
            """
            <div style="text-align: center;">
                <h1>🎵 InstruNet AI</h1>
                <p style="font-size: 18px; color: #6b7280;">
                    Music Instrument Recognition System
                </p>
                <p style="font-size: 14px; color: #9ca3af; margin-top: -10px;">
                    Secure access to audio analysis dashboard
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Your Name", placeholder="Enter your name")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not username.strip():
                    st.error("❌ Please enter your name")
                elif password != SHARED_PASSWORD:
                    st.error("❌ Invalid password")
                else:
                    st.session_state.authenticated = True
                    st.session_state.user = {"username": username.strip()}
                    st.success("✅ Login successful! Redirecting...")
                    st.rerun()
        
        # Info box
        st.info("💡 **Demo Access**: Use password `instrunet2025`")

# ==================================================
# HELPER FUNCTIONS
# ==================================================

def format_confidence(value):
    """Format confidence value as percentage"""
    return f"{value * 100:.1f}%"

def get_confidence_color(value, threshold):
    """Get color based on confidence value"""
    if value >= threshold:
        return COLORS["success"]
    elif value >= threshold * 0.5:
        return COLORS["warning"]
    else:
        return COLORS["muted"]

def create_instrument_card(instrument, confidence, threshold, is_detected):
    """Create a styled instrument card"""
    icon = CLASS_ICONS.get(instrument, "🎵")
    display_name = CLASS_DISPLAY_NAMES.get(instrument, instrument.upper())
    color = get_confidence_color(confidence, threshold)
    
    status_icon = "✓" if is_detected else "○"
    status_color = COLORS["success"] if is_detected else COLORS["muted"]
    
    card_html = f"""
    <div style="
        background: white;
        border-left: 4px solid {color};
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 24px;">{icon}</span>
                <div>
                    <div style="font-weight: 600; color: #1f2937;">{display_name}</div>
                    <div style="font-size: 12px; color: #6b7280;">Confidence: {format_confidence(confidence)}</div>
                </div>
            </div>
            <div style="
                background: {status_color};
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
            ">
                {status_icon}
            </div>
        </div>
    </div>
    """
    return card_html

# ==================================================
# MAIN APP
# ==================================================

def main_app():
    st.set_page_config(
        page_title="InstruNet AI - Music Instrument Recognition",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        /* Global styles */
        .block-container {
            padding-top: 1.5rem;
            padding-left: 2rem;
            padding-right: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Header styles */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .main-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .main-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        
        /* User profile */
        .user-profile {
            display: flex;
            align-items: center;
            gap: 12px;
            background: white;
            padding: 8px 16px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #667eea;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
        }
        
        .user-info {
            display: flex;
            flex-direction: column;
        }
        
        .user-name {
            font-weight: 600;
            font-size: 14px;
            color: #1f2937;
        }
        
        .user-role {
            font-size: 12px;
            color: #6b7280;
        }
        
        /* Results section */
        .results-header {
            background: #f9fafb;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        
        .results-header h3 {
            margin: 0;
            color: #1f2937;
        }
        
        /* Metric card */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }
        
        /* Expandable section */
        .expandable-section {
            background: #f9fafb;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
        
        /* Sidebar styles */
        [data-testid="stSidebar"] {
            background: #f9fafb;
        }
        
        /* Button styles */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Download button styles */
        .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ==================================================
    # HEADER
    # ==================================================
    
    col_header, col_user = st.columns([5, 1])
    
    with col_header:
        st.markdown("""
            <div class="main-header">
                <h1>🎵 InstruNet AI</h1>
                <p>Advanced Music Instrument Recognition System</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_user:
        st.markdown("<br>", unsafe_allow_html=True)
        initial = st.session_state.user["username"][0].upper()
        st.markdown(f"""
            <div class="user-profile">
                <div class="user-avatar">{initial}</div>
                <div class="user-info">
                    <div class="user-name">{st.session_state.user["username"]}</div>
                    <div class="user-role">Analyst</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.results = None
            st.session_state.audio_data = None
            st.session_state.visualizations = {}
            st.rerun()
    
    # ==================================================
    # SIDEBAR - INPUT CONTROLS
    # ==================================================
    
    with st.sidebar:
        st.markdown("### 🎵 Audio Upload")
        
        audio_file = st.file_uploader(
            "Choose audio file",
            type=["wav", "mp3"],
            help="Upload a WAV or MP3 file for analysis"
        )
        
        audio_bytes = None
        audio_name = "audio"
        
        if audio_file:
            audio_bytes = audio_file.read()
            audio_name = audio_file.name.rsplit(".", 1)[0]
            
            st.audio(audio_bytes)
            st.success(f"✅ **{audio_file.name}** loaded")
            
            # Store audio data in session state
            st.session_state.audio_data = {
                "bytes": audio_bytes,
                "name": audio_name
            }
        
        st.markdown("---")
        st.markdown("### ⚙️ Analysis Settings")
        
        aggregation = st.selectbox(
            "Aggregation Method",
            ["mean", "max", "voting"],
            help="Method to combine predictions across audio segments"
        )
        
        threshold = st.slider(
            "Detection Threshold",
            0.0, 1.0, 0.25, 0.05,
            help="Minimum confidence required to detect an instrument"
        )
        
        smoothing = st.slider(
            "Smoothing Window",
            1, 7, 3, 2,
            help="Window size for temporal smoothing (higher = smoother)"
        )
        
        st.markdown("---")
        
        run_clicked = st.button(
            "▶️ Analyze Track",
            use_container_width=True,
            type="primary",
            disabled=(audio_bytes is None)
        )
    
    # ==================================================
    # MAIN CONTENT AREA
    # ==================================================
    
    tab1, tab2, tab3 = st.tabs(["📊 Results", "📈 Visualizations", "📄 Export"])
    
    # ==================================================
    # TAB 1: RESULTS
    # ==================================================
    
    with tab1:
        if st.session_state.results is None:
            st.info("""
                ### 👋 Welcome to InstruNet AI!
                
                **Get Started:**
                1. 📁 Upload an audio file (WAV or MP3) using the sidebar
                2. ⚙️ Adjust analysis settings if needed
                3. ▶️ Click "Analyze Track" to begin
                
                **What You'll Get:**
                - 🎼 Detected instruments with confidence scores
                - 📊 Detailed probability analysis
                - 📈 Temporal intensity visualization
                - 📄 Professional PDF and JSON reports
            """)
        else:
            results = st.session_state.results
            confidence_dict = {
                cls: float(results["aggregated"][i])
                for i, cls in enumerate(CLASS_NAMES)
            }
            
            detected_instruments = {
                cls: score for cls, score in confidence_dict.items()
                if score >= threshold
            }
            
            # Summary Metrics
            st.markdown("""
                <div class="results-header">
                    <h3>🎼 Analysis Summary</h3>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{len(detected_instruments)}</div>
                        <div class="metric-label">Instruments Detected</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_confidence = np.mean(list(detected_instruments.values())) if detected_instruments else 0
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{format_confidence(avg_confidence)}</div>
                        <div class="metric-label">Avg Confidence</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                max_confidence = max(confidence_dict.values())
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{format_confidence(max_confidence)}</div>
                        <div class="metric-label">Peak Confidence</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{format_confidence(threshold)}</div>
                        <div class="metric-label">Threshold Used</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Detected Instruments
            if detected_instruments:
                st.markdown("""
                    <div class="results-header">
                        <h3>✅ Detected Instruments (Above Threshold)</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                # Sort by confidence (descending)
                sorted_detected = sorted(
                    detected_instruments.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                for cls, score in sorted_detected:
                    st.markdown(
                        create_instrument_card(cls, score, threshold, True),
                        unsafe_allow_html=True
                    )
            else:
                st.warning("⚠️ No instruments detected above the threshold. Try lowering the threshold value.")
            
            # Expandable: Full Probability View
            with st.expander("🔍 View All Class Probabilities", expanded=False):
                st.markdown("""
                    <div style="background: #f9fafb; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <p style="margin: 0; color: #6b7280; font-size: 14px;">
                            <strong>Note:</strong> This view shows confidence scores for all instrument classes, 
                            regardless of the detection threshold. Values below the threshold are shown with 
                            a muted indicator.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Sort all instruments by confidence
                sorted_all = sorted(
                    confidence_dict.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                for cls, score in sorted_all:
                    is_detected = score >= threshold
                    st.markdown(
                        create_instrument_card(cls, score, threshold, is_detected),
                        unsafe_allow_html=True
                    )
                
                # Data table view
                st.markdown("##### 📊 Tabular View")
                
                import pandas as pd
                df = pd.DataFrame([
                    {
                        "Instrument": CLASS_DISPLAY_NAMES.get(cls, cls.upper()),
                        "Class Code": cls,
                        "Confidence": format_confidence(score),
                        "Status": "✓ Detected" if score >= threshold else "○ Below Threshold"
                    }
                    for cls, score in sorted_all
                ])
                
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ==================================================
    # TAB 2: VISUALIZATIONS
    # ==================================================
    
    with tab2:
        if st.session_state.audio_data is None:
            st.info("📊 Upload and analyze an audio file to view visualizations")
        else:
            audio_bytes = st.session_state.audio_data["bytes"]
            y, sr = librosa.load(BytesIO(audio_bytes), sr=TARGET_SR, mono=True)
            
            # Waveform
            st.markdown("### 🌊 Waveform")
            st.caption("Time-domain representation showing amplitude variations")
            
            fig_wav, ax = plt.subplots(figsize=(12, 3))
            librosa.display.waveshow(y, sr=sr, ax=ax, color='#667eea')
            ax.set_xlabel("Time (seconds)", fontsize=11)
            ax.set_ylabel("Amplitude", fontsize=11)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig_wav)
            plt.close(fig_wav)
            
            st.markdown("---")
            
            # Mel Spectrogram
            st.markdown("### 🎨 Mel Spectrogram")
            st.caption("Frequency-domain representation used as CNN input")
            
            mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            mel_db = librosa.power_to_db(mel, ref=np.max)
            
            fig_mel, ax = plt.subplots(figsize=(12, 4))
            img = librosa.display.specshow(
                mel_db, sr=sr, x_axis="time", y_axis="mel",
                ax=ax, cmap='viridis'
            )
            fig_mel.colorbar(img, ax=ax, format="%+2.0f dB")
            ax.set_xlabel("Time (seconds)", fontsize=11)
            ax.set_ylabel("Frequency (Hz)", fontsize=11)
            plt.tight_layout()
            st.pyplot(fig_mel)
            
            # Store for PDF
            st.session_state.visualizations["mel_spec"] = fig_mel
            plt.close(fig_mel)
            
            # Intensity Timeline (if results available)
            if st.session_state.results:
                st.markdown("---")
                st.markdown("### 📈 Instrument Intensity Timeline")
                st.caption("Temporal confidence evolution for detected instruments")
                
                results = st.session_state.results
                times = results.get("times", [])
                smoothed = results.get("smoothed", [])
                
                if times and len(smoothed) > 0:
                    fig_timeline = create_intensity_timeline(
                        times, smoothed, threshold, CLASS_NAMES
                    )
                    st.pyplot(fig_timeline)
                    
                    # Store for PDF
                    st.session_state.visualizations["timeline"] = fig_timeline
                    plt.close(fig_timeline)
    
    # ==================================================
    # TAB 3: EXPORT
    # ==================================================
    
    with tab3:
        if st.session_state.results is None:
            st.info("📦 Complete an analysis to export results")
        else:
            st.markdown("### 📤 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                    <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%;">
                        <h4 style="margin-top: 0;">📄 JSON Export</h4>
                        <p style="color: #6b7280; font-size: 14px;">
                            Machine-readable format containing:
                        </p>
                        <ul style="color: #6b7280; font-size: 14px;">
                            <li>Audio metadata</li>
                            <li>Analysis parameters</li>
                            <li>Temporal timeline data</li>
                            <li>Per-class probabilities</li>
                        </ul>
                        <p style="color: #6b7280; font-size: 13px; font-style: italic;">
                            Best for: API integration, data pipelines, research
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                results = st.session_state.results
                json_str = json.dumps(results["json"], indent=2)
                
                st.download_button(
                    label="📥 Download JSON Report",
                    data=json_str,
                    file_name=f"{st.session_state.audio_data['name']}_analysis.json",
                    mime="application/json",
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                st.markdown("""
                    <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%;">
                        <h4 style="margin-top: 0;">📑 PDF Export</h4>
                        <p style="color: #6b7280; font-size: 14px;">
                            Professional report including:
                        </p>
                        <ul style="color: #6b7280; font-size: 14px;">
                            <li>Analysis summary</li>
                            <li>Detected instruments</li>
                            <li>Visualizations</li>
                            <li>Confidence metrics</li>
                        </ul>
                        <p style="color: #6b7280; font-size: 13px; font-style: italic;">
                            Best for: Presentations, documentation, reports
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                confidence_dict = {
                    cls: float(results["aggregated"][i])
                    for i, cls in enumerate(CLASS_NAMES)
                    if results["aggregated"][i] >= threshold
                }
                
                # Generate PDF
                pdf_path = generate_pdf_report(
                    audio_name=st.session_state.audio_data['name'],
                    aggregation=aggregation,
                    threshold=threshold,
                    smoothing=smoothing,
                    confidence_dict=confidence_dict,
                    visualizations=st.session_state.visualizations
                )
                
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=f,
                        file_name=f"{st.session_state.audio_data['name']}_analysis.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
    
    # ==================================================
    # INFERENCE EXECUTION
    # ==================================================
    
    if audio_bytes and run_clicked:
        with st.spinner("🔄 Analyzing audio... This may take a moment."):
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            # Load model
            model_path = "model/best_l2_regularized_model.h5"
            if not os.path.exists(model_path):
                st.error(f"❌ Model file not found: {model_path}")
                st.stop()
            
            model = tf.keras.models.load_model(model_path)
            
            # Run inference
            smoothed, times, aggregated, json_out = run_inference(
                temp_path, model, aggregation, threshold, smoothing
            )
            
            # Store results
            st.session_state.results = {
                "aggregated": aggregated,
                "json": json_out,
                "smoothed": smoothed,
                "times": times
            }
            
            # Clean up temp file
            os.unlink(temp_path)
            
            st.success("✅ Analysis complete!")
            st.rerun()

# ==================================================
# ENTRY POINT
# ==================================================

if not st.session_state.authenticated:
    login_page()
else:
    main_app()