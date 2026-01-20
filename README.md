# 🎵 InstruNet AI - Music Instrument Recognition System

A sophisticated CNN-based system for automatic detection and classification of musical instruments in audio tracks. Built as the culmination of a comprehensive internship project focusing on deep learning for audio analysis.

## 🔧 App Link 

https://cnn-based-music-instrument-recognition-system.streamlit.app/

## ✨ Features

### 🎼 Core Capabilities
- **Multi-Instrument Detection**: Recognizes 11 different instrument classes
- **Temporal Analysis**: Track instrument presence over time with sliding window approach
- **Polyphonic Support**: Handles multiple simultaneous instruments
- **Confidence Scoring**: Provides probability-based confidence for each detection

### 🖥️ User Interface
- **Secure Authentication**: Password-protected access with session management
- **Interactive Dashboard**: Modern, intuitive Streamlit-based interface
- **Real-time Visualizations**: Waveforms, spectrograms, and intensity timelines
- **Expandable Views**: Detailed probability analysis for all instrument classes

### 📊 Analysis Features
- **Three Aggregation Methods**: Mean, Max, and Voting
- **Adjustable Thresholds**: Customize detection sensitivity
- **Temporal Smoothing**: Reduce noise with moving average filters
- **Visual Indicators**: Color-coded confidence with instrument icons

### 📤 Export Options
- **JSON Export**: Machine-readable format with complete timeline data
- **PDF Reports**: Professional reports with visualizations and analysis
- **Structured Data**: Metadata, parameters, and per-segment predictions

## 🎸 Supported Instruments

| Code | Instrument | Icon | Code | Instrument | Icon |
|------|-----------|------|------|-----------|------|
| cel  | Cello | 🎻 | org | Organ | 🎹 |
| cla  | Clarinet | 🎷 | pia | Piano | 🎹 |
| flu  | Flute | 🪈 | sax | Saxophone | 🎷 |
| gac  | Acoustic Guitar | 🎸 | tru | Trumpet | 🎺 |
| gel  | Electric Guitar | 🎸 | vio | Violin | 🎻 |
| | | | voi | Voice | 🎤 |

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone or download the repository**
   ```bash
   cd InstruNet-AI
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv instrunet_env
   
   # Windows
   instrunet_env\Scripts\activate
   
   # Linux/Mac
   source instrunet_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify model file exists**
   - Ensure `model/best_l2_regularized_model.h5` is present
   - This is the trained CNN model file

5. **Set password (optional)**
   ```bash
   # Windows
   set INSTRUNET_PASSWORD=your_secure_password
   
   # Linux/Mac
   export INSTRUNET_PASSWORD=your_secure_password
   ```
   
   If not set, default password is `instrunet2025`

## 🎯 Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Using the Dashboard

1. **Login**
   - Enter your name
   - Use password: `instrunet2025` (or your custom password)

2. **Upload Audio**
   - Click "Choose audio file" in the sidebar
   - Select a WAV or MP3 file
   - File will be displayed with audio player

3. **Configure Analysis**
   - **Aggregation Method**: How to combine segment predictions
     - `mean`: Average confidence across segments
     - `max`: Peak confidence value
     - `voting`: Democratic decision across segments
   - **Detection Threshold**: Minimum confidence (0.0 - 1.0)
   - **Smoothing Window**: Temporal filter size (1 - 7)

4. **Analyze**
   - Click "▶️ Analyze Track"
   - Wait for processing to complete
   - View results in tabs

5. **Explore Results**
   - **Results Tab**: Detected instruments with confidence scores
   - **Visualizations Tab**: Waveforms, spectrograms, timelines
   - **Export Tab**: Download JSON or PDF reports

## 📁 Project Structure

```
InstruNet-AI/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration and constants
├── pipeline.py                 # Inference pipeline
├── requirements.txt            # Python dependencies
├── README.md                  # This file
│
├── model/
│   └── best_l2_regularized_model.h5  # Trained CNN model
│
├── utils/
│   ├── aggregation.py         # Prediction aggregation methods
│   ├── audio.py               # Audio loading and preprocessing
│   ├── features.py            # Feature extraction (mel spectrograms)
│   ├── io.py                  # JSON export utilities
│   ├── pdf_report.py          # PDF report generation
│   ├── segmentation.py        # Sliding window segmentation
│   └── visualization.py       # Plotting utilities
│
├── data/                      # Dataset (not included in repo)
├── notebooks/                 # Development notebooks
└── reports/                   # Generated analysis reports
```

## 🔬 Technical Details

### Model Architecture
- **Type**: Convolutional Neural Network (CNN)
- **Input**: 128-band log-mel spectrograms
- **Regularization**: L2 weight regularization + Dropout
- **Training**: SGD with momentum on IRMAS dataset
- **Classes**: 11 instrument categories (multi-label)

### Audio Processing Pipeline
1. **Load Audio**: Convert to mono, resample to 16kHz
2. **Segmentation**: 3-second windows with 1.5-second hop
3. **Preprocessing**: Peak normalization and silence trimming
4. **Feature Extraction**: Log-mel spectrogram generation
5. **Prediction**: CNN inference per segment
6. **Post-processing**: Smoothing and aggregation
7. **Export**: JSON and PDF report generation

### Performance Metrics
- **Micro F1-Score**: 0.677
- **Macro F1-Score**: 0.657
- **ROC-AUC**: 0.94+
- **Dataset**: IRMAS (6,705 samples)

## 🎓 Academic Context

This project was developed as **Task 19** - the final deliverable of a comprehensive internship focusing on:

- Data preprocessing and augmentation
- CNN architecture design and optimization
- Hyperparameter tuning (kernel size, optimizers, regularization)
- Evaluation metrics and model selection
- Production-ready deployment

### Key Experiments Conducted
- **Task 11**: Hyperparameter tuning (kernel size: 3×3 → 5×5)
- **Task 12**: Optimizer comparison (SGD, Adam, RMSProp)
- **Task 13**: L2 + Dropout regularization
- **Task 14**: Data segmentation strategy
- **Task 15**: Aggregation methods evaluation
- **Task 16**: Intensity timeline generation

## 🔒 Security Notes

### Authentication
- Default password: `instrunet2025`
- Set custom password via environment variable
- Session-based authentication
- Automatic logout functionality

### Production Deployment
For production use:
```bash
# Set secure password
export INSTRUNET_PASSWORD="your_very_secure_password_here"

# Run with production settings
streamlit run app.py --server.port=8501 --server.headless=true
```

## 📊 Example Outputs

### JSON Export Structure
```json
{
  "audio_file": "song.wav",
  "segment_duration_sec": 3.0,
  "hop_duration_sec": 1.5,
  "aggregation": "mean",
  "smoothing": 3,
  "threshold": 0.25,
  "classes": ["cel", "cla", "flu", ...],
  "timeline": [
    {
      "time_sec": 0.0,
      "intensity": {
        "cel": 0.042,
        "cla": 0.003,
        ...
      }
    },
    ...
  ]
}
```

### PDF Report Contents
- Analysis metadata and parameters
- Detected instruments with confidence bars
- Summary statistics
- Mel spectrogram visualization
- Instrument intensity timeline
- Interpretation and methodology notes

## 🛠️ Troubleshooting

### Common Issues

**Model file not found**
```
Error: Model file not found: model/best_l2_regularized_model.h5
```
- Ensure the model file exists in the `model/` directory
- Download from the original repository if missing

**Memory errors during processing**
```
tensorflow.python.framework.errors_impl.ResourceExhaustedError
```
- Close other applications to free memory
- Try shorter audio files
- Reduce batch processing if modified

**Authentication issues**
```
Invalid password
```
- Check if environment variable is set correctly
- Use default password `instrunet2025` if no custom password set
- Clear browser cache and try again

## 🤝 Contributing

This is an academic project completed for internship requirements. Contributions, suggestions, and feedback are welcome for educational purposes.

## 👥 Authors

Developed as part of Infosys Springboard Virtual Internship 6.0

## 🙏 Acknowledgments

- **Dataset**: IRMAS (Instrument Recognition in Musical Audio Signals)
- **Framework**: TensorFlow/Keras, Streamlit
- **Libraries**: Librosa, NumPy, Matplotlib, ReportLab

## 📧 Contact

For questions or feedback regarding this project, please refer to the project documentation.

---

**🎵 InstruNet AI** - Where Deep Learning Meets Music