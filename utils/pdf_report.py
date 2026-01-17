# utils/pdf_report.py

from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
import tempfile
import os
from datetime import datetime
from config import CLASS_DISPLAY_NAMES

def generate_pdf_report(
    audio_name,
    aggregation,
    threshold,
    smoothing,
    confidence_dict,
    visualizations=None
):
    """
    Generate a comprehensive PDF report with multiple visualizations
    
    Args:
        audio_name: Name of the audio file
        aggregation: Aggregation method used
        threshold: Detection threshold
        smoothing: Smoothing window size
        confidence_dict: Dictionary of {class: confidence} for detected instruments
        visualizations: Dictionary of matplotlib figures
    
    Returns:
        Path to generated PDF file
    """
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, f"{audio_name}_analysis.pdf")
    
    # Create canvas
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Page margins
    margin_left = 50
    margin_right = width - 50
    margin_top = height - 50
    margin_bottom = 50
    
    y_position = margin_top
    
    # =====================================
    # TITLE PAGE
    # =====================================
    
    # Main title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(0.4, 0.49, 0.9)  # Blue color
    c.drawString(margin_left, y_position, "InstruNet AI")
    y_position -= 30
    
    c.setFont("Helvetica", 16)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(margin_left, y_position, "Instrument Recognition Report")
    y_position -= 10
    
    # Decorative line
    c.setStrokeColorRGB(0.4, 0.49, 0.9)
    c.setLineWidth(2)
    c.line(margin_left, y_position, margin_right, y_position)
    y_position -= 40
    
    # Report metadata
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    
    report_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    c.drawString(margin_left, y_position, f"Generated: {report_date}")
    y_position -= 50
    
    # =====================================
    # ANALYSIS DETAILS
    # =====================================
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(margin_left, y_position, "Analysis Details")
    y_position -= 20
    
    c.setFont("Helvetica", 10)
    details = [
        f"Audio File: {audio_name}",
        f"Aggregation Method: {aggregation.capitalize()}",
        f"Detection Threshold: {threshold:.2f}",
        f"Smoothing Window: {smoothing} segments",
    ]
    
    for detail in details:
        c.drawString(margin_left + 10, y_position, detail)
        y_position -= 18
    
    y_position -= 20
    
    # =====================================
    # DETECTED INSTRUMENTS
    # =====================================
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(margin_left, y_position, "Detected Instruments")
    y_position -= 5
    
    # Underline
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    c.line(margin_left, y_position, margin_left + 180, y_position)
    y_position -= 20
    
    if confidence_dict:
        # Sort by confidence (descending)
        sorted_instruments = sorted(
            confidence_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        c.setFont("Helvetica", 10)
        
        for cls, score in sorted_instruments:
            display_name = CLASS_DISPLAY_NAMES.get(cls, cls.upper())
            
            # Instrument name
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin_left + 20, y_position, f"• {display_name}")
            
            # Confidence score
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.2, 0.6, 0.2)  # Green
            c.drawString(
                margin_left + 250,
                y_position,
                f"Confidence: {score * 100:.1f}%"
            )
            c.setFillColorRGB(0, 0, 0)  # Reset to black
            
            # Confidence bar
            bar_width = 150
            bar_height = 8
            bar_x = margin_left + 380
            bar_y = y_position - 2
            
            # Background (gray)
            c.setFillColorRGB(0.9, 0.9, 0.9)
            c.rect(bar_x, bar_y, bar_width, bar_height, fill=True, stroke=False)
            
            # Foreground (confidence level)
            bar_fill_width = bar_width * min(score, 1.0)
            
            # Color based on confidence
            if score >= 0.7:
                c.setFillColorRGB(0.2, 0.7, 0.2)  # Green
            elif score >= 0.5:
                c.setFillColorRGB(0.9, 0.7, 0.1)  # Yellow
            else:
                c.setFillColorRGB(0.9, 0.5, 0.2)  # Orange
            
            c.rect(bar_x, bar_y, bar_fill_width, bar_height, fill=True, stroke=False)
            c.setFillColorRGB(0, 0, 0)  # Reset
            
            y_position -= 25
            
            # Check if we need a new page
            if y_position < 150:
                c.showPage()
                y_position = margin_top
    else:
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawString(margin_left + 20, y_position, "No instruments detected above threshold")
        c.setFillColorRGB(0, 0, 0)
        y_position -= 25
    
    y_position -= 20
    
    # =====================================
    # SUMMARY STATISTICS
    # =====================================
    
    if confidence_dict:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin_left, y_position, "Summary Statistics")
        y_position -= 5
        
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.line(margin_left, y_position, margin_left + 180, y_position)
        y_position -= 20
        
        c.setFont("Helvetica", 10)
        
        avg_confidence = sum(confidence_dict.values()) / len(confidence_dict)
        max_confidence = max(confidence_dict.values())
        min_confidence = min(confidence_dict.values())
        
        stats = [
            f"Total Instruments Detected: {len(confidence_dict)}",
            f"Average Confidence: {avg_confidence * 100:.1f}%",
            f"Maximum Confidence: {max_confidence * 100:.1f}%",
            f"Minimum Confidence: {min_confidence * 100:.1f}%",
        ]
        
        for stat in stats:
            c.drawString(margin_left + 20, y_position, stat)
            y_position -= 18
    
    # =====================================
    # VISUALIZATIONS
    # =====================================
    
    if visualizations:
        # Start new page for visualizations
        c.showPage()
        y_position = margin_top
        
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(0.4, 0.49, 0.9)
        c.drawString(margin_left, y_position, "Visualizations")
        y_position -= 10
        
        c.setStrokeColorRGB(0.4, 0.49, 0.9)
        c.setLineWidth(2)
        c.line(margin_left, y_position, margin_right, y_position)
        y_position -= 40
        
        c.setFillColorRGB(0, 0, 0)
        
        # Mel Spectrogram
        if "mel_spec" in visualizations:
            mel_fig = visualizations["mel_spec"]
            mel_path = os.path.join(temp_dir, "mel_spectrogram.png")
            mel_fig.savefig(mel_path, dpi=150, bbox_inches="tight")
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin_left, y_position, "Mel Spectrogram")
            y_position -= 5
            
            c.setFont("Helvetica", 9)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(
                margin_left,
                y_position,
                "Frequency-domain representation used as CNN input"
            )
            c.setFillColorRGB(0, 0, 0)
            y_position -= 15
            
            # Insert image
            img_width = width - 2 * margin_left
            img_height = 200
            
            c.drawImage(
                mel_path,
                margin_left,
                y_position - img_height,
                width=img_width,
                height=img_height,
                preserveAspectRatio=True
            )
            y_position -= img_height + 30
        
        # Intensity Timeline
        if "timeline" in visualizations:
            # Check if we need a new page
            if y_position < 250:
                c.showPage()
                y_position = margin_top
            
            timeline_fig = visualizations["timeline"]
            timeline_path = os.path.join(temp_dir, "intensity_timeline.png")
            timeline_fig.savefig(timeline_path, dpi=150, bbox_inches="tight")
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin_left, y_position, "Instrument Intensity Timeline")
            y_position -= 5
            
            c.setFont("Helvetica", 9)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(
                margin_left,
                y_position,
                "Temporal evolution of instrument confidence over time"
            )
            c.setFillColorRGB(0, 0, 0)
            y_position -= 15
            
            # Insert image
            img_width = width - 2 * margin_left
            img_height = 250
            
            c.drawImage(
                timeline_path,
                margin_left,
                y_position - img_height,
                width=img_width,
                height=img_height,
                preserveAspectRatio=True
            )
            y_position -= img_height + 20
    
    # =====================================
    # INTERPRETATION
    # =====================================
    
    # Check if we need a new page
    if y_position < 200:
        c.showPage()
        y_position = margin_top
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(margin_left, y_position, "Interpretation")
    y_position -= 5
    
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    c.line(margin_left, y_position, margin_left + 150, y_position)
    y_position -= 20
    
    c.setFont("Helvetica", 9)
    
    interpretation_text = [
        "This report presents the results of automated instrument recognition analysis.",
        "",
        "The confidence scores represent the model's belief in the presence of each",
        "instrument, based on analysis of the audio's spectral characteristics.",
        "",
        f"Instruments with confidence above {threshold:.2f} are considered detected.",
        "",
        "The temporal timeline shows how confidence evolves over the duration of the",
        "audio track, allowing identification of when specific instruments are active.",
    ]
    
    for line in interpretation_text:
        c.drawString(margin_left + 10, y_position, line)
        y_position -= 14
    
    y_position -= 20
    
    # =====================================
    # METHODOLOGY NOTE
    # =====================================
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_left, y_position, "Methodology")
    y_position -= 5
    
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5)
    c.line(margin_left, y_position, margin_left + 120, y_position)
    y_position -= 18
    
    c.setFont("Helvetica", 9)
    
    methodology_text = [
        f"• Segmentation: 3.0-second windows with 1.5-second hop",
        f"• Feature Extraction: 128-band log-mel spectrograms",
        f"• Model: CNN with L2 regularization",
        f"• Aggregation: {aggregation.capitalize()} pooling across segments",
        f"• Smoothing: Moving average with window size {smoothing}",
    ]
    
    for line in methodology_text:
        c.drawString(margin_left + 10, y_position, line)
        y_position -= 14
    
    # =====================================
    # FOOTER
    # =====================================
    
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(
        margin_left,
        margin_bottom - 20,
        "Generated by InstruNet AI - Music Instrument Recognition System"
    )
    
    # Page numbers on all pages
    page_num = c.getPageNumber()
    for i in range(1, page_num + 1):
        c.drawString(
            width - margin_left - 50,
            margin_bottom - 20,
            f"Page {i} of {page_num}"
        )
    
    # Save PDF
    c.save()
    
    return pdf_path