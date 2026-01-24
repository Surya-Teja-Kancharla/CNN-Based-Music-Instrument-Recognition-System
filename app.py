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
from supabase import create_client, Client
import re
from datetime import datetime
import time

from pipeline import run_inference
from utils.pdf_report import generate_pdf_report
from utils.visualization import create_intensity_timeline
from config import (
    CLASS_NAMES, CLASS_DISPLAY_NAMES, CLASS_ICONS,
    TARGET_SR, COLORS, SUPABASE_URL, SUPABASE_KEY
)
from dotenv import load_dotenv

load_dotenv()

# ==================================================
# SUPABASE CONFIGURATION
# ==================================================

# Initialize Supabase client
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "login_success" not in st.session_state:
    st.session_state.login_success = False   # 🔹 NEW FLAG

if "user" not in st.session_state:
    st.session_state.user = None

if "results" not in st.session_state:
    st.session_state.results = None

if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

if "visualizations" not in st.session_state:
    st.session_state.visualizations = {}

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"


# ==================================================
# AUTHENTICATION HELPER FUNCTIONS
# ==================================================

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def hash_password(password):
    """Hash password using bcrypt-like method"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(email, password):
    """Verify user credentials against Supabase"""
    try:
        hashed_password = hash_password(password)
        response = supabase.table("users").select("*").eq("email", email).eq("password_hash", hashed_password).execute()
        
        if response.data and len(response.data) > 0:
            return True, response.data[0]
        return False, None
    except Exception as e:
        st.error(f"Error verifying user: {str(e)}")
        return False, None

def create_user(username, email, password):
    """Create new user in Supabase"""
    try:
        hashed_password = hash_password(password)
        
        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", email).execute()
        if existing_user.data and len(existing_user.data) > 0:
            return False, "User with this email already exists"
        
        # Create new user
        user_data = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("users").insert(user_data).execute()
        
        if response.data and len(response.data) > 0:
            return True, "Account created successfully!"
        return False, "Failed to create account"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

# ==================================================
# LOGIN PAGE
# ==================================================

def login_page():
    st.set_page_config(
        page_title="InstruNet AI - Login",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # =======================
    # GLOBAL CSS
    # =======================
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }

        .block-container {
            padding-top: 3.0rem;
        }

        .stTextInput input {
            border-radius: 8px;
        }

        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem;
        }

        .auth-footer {
            text-align: center;
            margin-top: 1.5rem;
            font-size: 14px;
            color: #9ca3af;
        }

        .auth-footer a {
            color: #8b5cf6;
            font-weight: 500;
            text-decoration: underline;
        }

        .auth-footer a:hover {
            text-decoration: underline;
            color: #7c3aed;
        }
        </style>
    """, unsafe_allow_html=True)

    # =======================
    # HEADER
    # =======================
    st.markdown("""
        <div style="text-align:center; margin-bottom:1rem;">
            <h1 style="color:#667eea;">🎵 InstruNet AI</h1>
            <p style="font-size:18px; color:#9ca3af;">
                A CNN-Based Music Instrument Recognition System
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if not supabase:
            st.error("⚠️ Supabase is not configured.")
            st.stop()

        # =======================
        # WELCOME TEXT
        # =======================
        st.markdown("""
            <div style="text-align:center; margin-top:2.0rem; margin-bottom:1.5rem;">
                <p style="font-size:22px; font-weight:600; color:#e5e7eb;">
                    Welcome Back
                </p>
                <p style="color:#9ca3af; font-size:14px;">
                    Sign in to your account to continue
                </p>
            </div>
        """, unsafe_allow_html=True)

        # =======================
        # LOGIN SUCCESS MESSAGE (STEP 3)
        # =======================
        if st.session_state.get("login_success"):
            st.success("✅ Login successful! Redirecting to dashboard…")
            time.sleep(2)

            st.session_state.authenticated = True
            st.session_state.login_success = False
            st.rerun()

        # =======================
        # LOGIN FORM (STEP 2)
        # =======================
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="your.email@example.com")
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )

            if st.form_submit_button("🔐 Sign In", type="primary", use_container_width=True):
                if not email or not password:
                    st.error("❌ Please fill in all fields")
                elif not validate_email(email):
                    st.error("❌ Please enter a valid email address")
                else:
                    with st.spinner("Verifying..."):
                        success, user_data = verify_user(email, password)
                        if success:
                            st.session_state.user = user_data
                            st.session_state.login_success = True
                            st.query_params.clear()
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password")

        # =======================
        # REAL HYPERLINK (NO BUTTON)
        # =======================
        st.markdown("""
            <hr style="margin:2rem 0;">
            <div class="auth-footer">
                Don't have an account?
                <a href="?auth=signup" target="_self">Create new account</a>
            </div>
        """, unsafe_allow_html=True)

# ==================================================
# SIGNUP PAGE
# ==================================================

def signup_page():
    st.set_page_config(
        page_title="InstruNet AI – Sign Up",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # =======================
    # GLOBAL CSS (MATCH LOGIN)
    # =======================
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }

        .block-container {
            padding-top: 3.0rem;
        }

        .stTextInput input {
            border-radius: 8px;
        }

        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem;
        }

        .auth-footer {
            text-align: center;
            margin-top: 1.5rem;
            font-size: 14px;
            color: #9ca3af;
        }

        .auth-footer a {
            color: #8b5cf6;
            font-weight: 500;
            text-decoration: underline;
        }

        .auth-footer a:hover {
            color: #7c3aed;
        }
        </style>
    """, unsafe_allow_html=True)

    # =======================
    # HEADER
    # =======================
    st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <h1 style="color: #667eea;">🎵 InstruNet AI</h1>
            <p style="font-size: 18px; color: #9ca3af;">
                Music Instrument Recognition System
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if not supabase:
            st.error("⚠️ Supabase is not configured.")
            st.stop()

        st.markdown("""
            <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 1.5rem;">
                <p style="font-size: 22px; font-weight: 600; color: #e5e7eb;">
                    Create Account
                </p>
                <p style="color: #9ca3af; font-size: 14px;">
                    Join InstruNet AI to start analyzing music
                </p>
            </div>
        """, unsafe_allow_html=True)

        # =======================
        # SIGNUP FORM
        # =======================
        with st.form("signup_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email Address", placeholder="your.email@example.com")
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a strong password"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password"
            )

            if st.form_submit_button("🚀 Create Account", type="primary", use_container_width=True):
                if not username or not email or not password or not confirm_password:
                    st.error("❌ Please fill in all fields")
                elif not validate_email(email):
                    st.error("❌ Please enter a valid email address")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match")
                else:
                    valid, message = validate_password(password)
                    if not valid:
                        st.error(f"❌ {message}")
                    else:
                        with st.spinner("Creating your account..."):
                            success, msg = create_user(username, email, password)
                            if success:
                                st.success("✅ " + msg)
                                st.query_params["auth"] = "login"
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")

        # =======================
        # REAL HYPERLINK (NO BUTTON)
        # =======================
        st.markdown("""
            <hr style="margin:2rem 0;">
            <div class="auth-footer">
                Already have an account?
                <a href="?auth=login" target="_self">Sign in</a>
            </div>
        """, unsafe_allow_html=True)

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
            padding: 1rem 2rem;
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
        
        /* User profile - FIXED: Proper circle avatar */
        .user-profile {
            display: flex;
            align-items: center;
            gap: 12px;
            background: white;
            padding: 10px 16px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .user-avatar {
            width: 40px;
            height: 40px;
            min-width: 40px;
            min-height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 18px;
            flex-shrink: 0;
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
            background: #f0f9ff;
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
            border-top: 3px solid #667eea;
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
            background: #f0f9ff;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
        
        /* Sidebar styles - FIXED: Dark grey to blend with UI */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #374151 0%, #1f2937 100%);
        }
        
        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(180deg, #374151 0%, #1f2937 100%);
        }
        
        /* Sidebar content styling */
        [data-testid="stSidebar"] .stMarkdown {
            color: #e5e7eb !important;
        }
        
        [data-testid="stSidebar"] h3 {
            color: #f3f4f6 !important;
            font-weight: 700;
        }
        
        [data-testid="stSidebar"] label {
            color: #e5e7eb !important;
            font-weight: 500;
        }
        
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stSlider label {
            color: #e5e7eb !important;
        }
        
        /* Slider values visibility */
        [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
            color: #e5e7eb !important;
        }
        
        [data-testid="stSidebar"] .stSlider div[data-testid="stTickBar"] div {
            color: #d1d5db !important;
        }
        
        /* File uploader in sidebar */
        [data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background: rgba(55, 65, 81, 0.5);
            padding: 1rem;
            border-radius: 8px;
            border: 2px dashed #6b7280;
        }
        
        [data-testid="stSidebar"] [data-testid="stFileUploader"] label {
            color: #e5e7eb !important;
        }
        
        /* Success message in sidebar */
        [data-testid="stSidebar"] .element-container .stSuccess {
            background: rgba(55, 65, 81, 0.8);
            border-left: 4px solid #48bb78;
            padding: 0.75rem;
            border-radius: 4px;
        }
        
        [data-testid="stSidebar"] .element-container .stSuccess p {
            color: #e5e7eb !important;
        }
        
        /* Button styles */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Primary button color */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        
        /* Download button styles */
        .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            border-radius: 8px 8px 0 0;
        }
        
        /* Audio player styling */
        [data-testid="stAudio"] {
            border-radius: 8px;
            overflow: hidden;
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
        # FIXED: Circle avatar + "User" instead of email
        st.markdown(f"""
            <div class="user-profile">
                <div class="user-avatar">{initial}</div>
                <div class="user-info">
                    <div class="user-name">{st.session_state.user["username"]}</div>
                    <div class="user-role">User</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.results = None
            st.session_state.audio_data = None
            st.session_state.visualizations = {}
            st.session_state.auth_page = "login"
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
            1, 7, 3, 1,
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
                    <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
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
            st.session_state.visualizations["waveform"] = fig_wav
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
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%;
                                border-top: 3px solid #667eea;">
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
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%;
                                border-top: 3px solid #667eea;">
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
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(BASE_DIR, "model", "best_l2_regularized_model.h5")
            if not os.path.exists(model_path):
                st.error(f"❌ Model file not found: {model_path}")
                st.stop()
            
            model = tf.keras.models.load_model(model_path)
            
            # Run inference - pass audio_name for proper JSON metadata
            smoothed, times, aggregated, json_out = run_inference(
                temp_path, model, aggregation, threshold, smoothing, audio_name=audio_name
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

auth = st.query_params.get("auth", "login")

if not st.session_state.authenticated:
    if auth == "signup":
        signup_page()
    else:
        login_page()
else:
    main_app()