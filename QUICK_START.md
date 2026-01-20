# 🚀 InstruNet AI - Quick Start Guide

Get up and running in 5 minutes!

## ⚡ Fast Setup (3 Steps)

### Step 1: Install Dependencies

```bash
# Make sure you're in the InstruNet-AI directory
cd InstruNet-AI

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Verify Model File

```bash
# Check if model exists
ls -lh model/best_l2_regularized_model.h5
```

If missing, ensure the model file is in the `model/` directory.

### Step 3: Run the App

```bash
streamlit run app.py
```

The app will open in your browser at: `http://localhost:8501`

---

## 🔑 First Login

**Default Credentials:**

- **Username**: Your name (anything you want)
- **Password**: No password

---

## 🎵 First Analysis

1. **Click** "Choose audio file" in the sidebar
2. **Upload** a WAV or MP3 file
3. **Click** "▶️ Analyze Track" button
4. **View** results in the tabs!

---

## 📊 What You'll See

### Results Tab

- ✅ Detected instruments with confidence scores
- 📊 Summary statistics
- 🔍 Expandable view for all probabilities

### Visualizations Tab

- 🌊 Audio waveform
- 🎨 Mel spectrogram
- 📈 Intensity timeline

### Export Tab

- 📄 JSON report (machine-readable)
- 📑 PDF report (human-readable)

---

## ⚙️ Quick Settings Guide

### Aggregation Method

- **Mean** (recommended): Average confidence
- **Max**: Peak detection
- **Voting**: Democratic decision

### Detection Threshold

- **Lower** (0.15-0.25): More instruments detected
- **Higher** (0.30-0.50): Only high-confidence detections

### Smoothing Window

- **Lower** (1-3): More responsive
- **Higher** (5-7): Smoother results

---

## 🆘 Quick Troubleshooting

### "Model file not found"

```bash
# Make sure you're in the right directory
pwd
# Should show: .../InstruNet-AI

# Check model
ls model/
# Should show: best_l2_regularized_model.h5
```

### "Invalid password"

- Use: `instrunet2025` (all lowercase)
- Or set your own: `export INSTRUNET_PASSWORD=yourpassword`

### "Port already in use"

```bash
# Kill existing process
pkill -f streamlit

# Or use different port
streamlit run app.py --server.port 8502
```

### "Memory error"

- Close other applications
- Try shorter audio files
- Reduce file size

---

## 🔧 Optional: Change Password

### Linux/Mac:

```bash
streamlit run app.py
```

### Windows:

```cmd
streamlit run app.py
```

---

## 🎯 Supported File Formats

| Format | Supported   | Notes                    |
| ------ | ----------- | ------------------------ |
| WAV    | ✅ Yes      | Best quality             |
| MP3    | ✅ Yes      | Widely compatible        |
| FLAC   | ⚠️ May work | Convert to WAV if issues |
| OGG    | ⚠️ May work | Convert to WAV if issues |
| M4A    | ❌ No       | Convert to MP3/WAV       |

---

## 💡 Tips for Best Results

1. **Audio Quality**: Higher quality = better results
2. **File Length**: 30 seconds to 5 minutes optimal
3. **Clear Audio**: Less background noise = better detection
4. **Threshold Tuning**: Adjust based on your audio
5. **Multiple Runs**: Try different aggregation methods

---

## 🎵 Example Test Files

Don't have audio files? Try these:

- YouTube audio downloader (use royalty-free music)
- Free Music Archive: https://freemusicarchive.org/
- CCMixter: http://ccmixter.org/
- Jamendo: https://www.jamendo.com/

**Note**: Use only royalty-free or your own audio!

---

## 📞 Need Help?

1. Check error message in the app
2. Review [README.md](README.md) troubleshooting section
3. Verify all dependencies are installed

---

**🎵 Enjoy analyzing music with InstruNet AI!**

Made with ❤️ for music lovers and AI enthusiasts
