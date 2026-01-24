from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from io import BytesIO
import tempfile

from config import CLASS_DISPLAY_NAMES


def generate_pdf_report(audio_name, aggregation, threshold, smoothing,
                        confidence_dict, visualizations):
    """
    Generate a professional PDF report
    """

    # Create temp file for PDF
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = pdf_file.name
    pdf_file.close()

    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    elements = []

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#f0f9ff'),
        leftIndent=10
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=8,
        leading=14
    )

    # ================= PAGE 1 =================

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("🎵 InstruNet AI", title_style))
    elements.append(Paragraph("Instrument Recognition Analysis Report", subtitle_style))

    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    metadata_data = [
        ['Generated:', current_time],
        ['Audio File:', audio_name],
        ['Analysis Date:', datetime.now().strftime("%Y-%m-%d")]
    ]

    metadata_table = Table(metadata_data, colWidths=[2 * inch, 4 * inch])

    metadata_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(metadata_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ================= SETTINGS =================

    elements.append(Paragraph("⚙️ Analysis Configuration", heading2_style))
    elements.append(Spacer(1, 0.1 * inch))

    settings_data = [
        ['Parameter', 'Value', 'Description'],
        ['Aggregation Method', aggregation.capitalize(),
         'Method used to combine predictions'],
        ['Detection Threshold', f'{threshold:.2f}',
         'Minimum confidence required'],
        ['Smoothing Window', f'{smoothing} segments',
         'Temporal smoothing window'],
    ]

    settings_table = Table(
        settings_data,
        colWidths=[1.8 * inch, 1.5 * inch, 3.2 * inch]
    )

    settings_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))

    elements.append(settings_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ================= SUMMARY =================

    elements.append(Paragraph("🎼 Detection Summary", heading2_style))
    elements.append(Spacer(1, 0.1 * inch))

    if confidence_dict:

        sorted_instruments = sorted(
            confidence_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )

        avg_conf = sum(confidence_dict.values()) / len(confidence_dict)

        summary_data = [
            ['Metric', 'Value'],
            ['Total Instruments', str(len(confidence_dict))],
            ['Average Confidence', f'{avg_conf * 100:.1f}%'],
            ['Highest Confidence', f'{max(confidence_dict.values()) * 100:.1f}%'],
            ['Lowest Confidence', f'{min(confidence_dict.values()) * 100:.1f}%']
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 3.5 * inch])

        summary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))

        # ================= INSTRUMENTS =================

        elements.append(Paragraph("✅ Detected Instruments", heading2_style))
        elements.append(Spacer(1, 0.1 * inch))

        instruments_data = [['Rank', 'Instrument', 'Confidence', 'Status']]

        for i, (cls, conf) in enumerate(sorted_instruments, 1):

            name = CLASS_DISPLAY_NAMES.get(cls, cls.upper())
            conf_pct = f'{conf * 100:.1f}%'
            status = '✓ Detected' if conf >= threshold else '○ Below Threshold'

            instruments_data.append(
                [str(i), name, conf_pct, status]
            )

        instruments_table = Table(
            instruments_data,
            colWidths=[0.7 * inch, 2.5 * inch, 1.5 * inch, 1.8 * inch]
        )

        instruments_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ]))

        elements.append(instruments_table)

    else:

        elements.append(
            Paragraph("⚠️ No instruments detected.", body_style)
        )

    # ================= PAGE 2 =================

    elements.append(PageBreak())

    elements.append(Paragraph("📊 Visualizations", heading2_style))
    elements.append(Spacer(1, 0.2 * inch))

    # -------- Waveform --------

    if 'waveform' in visualizations:

        elements.append(Paragraph("Audio Waveform", heading3_style))

        elements.append(Paragraph(
            "Time-domain representation of the original audio signal. "
            "This shows amplitude variations across time.",
            body_style
        ))

        elements.append(Spacer(1, 0.1 * inch))

        waveform_fig = visualizations['waveform']

        waveform_buf = BytesIO()
        waveform_fig.savefig(
            waveform_buf,
            format='png',
            dpi=150,
            bbox_inches='tight'
        )
        waveform_buf.seek(0)

        waveform_img = Image(
            waveform_buf,
            width=6.5 * inch,
            height=2.0 * inch
        )

        elements.append(waveform_img)
        elements.append(Spacer(1, 0.3 * inch))
        

    # -------- Mel Spectrogram --------

    if 'mel_spec' in visualizations:

        elements.append(Paragraph("Mel Spectrogram", heading3_style))

        elements.append(Paragraph(
            "Frequency-domain representation of the audio signal converted into "
            "mel-scaled bands. This visualization is used as the primary input "
            "feature for the CNN model, where brighter regions indicate higher "
            "energy concentrations at specific frequencies and time intervals.",
            body_style
        ))

        elements.append(Spacer(1, 0.1 * inch))

        mel_fig = visualizations['mel_spec']

        mel_buf = BytesIO()
        mel_fig.savefig(mel_buf, format='png', dpi=150, bbox_inches='tight')
        mel_buf.seek(0)

        mel_img = Image(mel_buf, width=6.5 * inch, height=2.5 * inch)

        elements.append(mel_img)
        elements.append(Spacer(1, 0.3 * inch))

    # -------- Timeline --------

    if 'timeline' in visualizations:
        
        elements.append(Paragraph("Instrument Intensity Timeline", heading3_style))

        elements.append(Paragraph(
            "Temporal representation of confidence scores for detected instruments "
            "across the audio duration. Each curve indicates the probability of an "
            "instrument being present over time, while the dashed line represents "
            "the detection threshold used for final classification.",
            body_style
        ))

        elements.append(Spacer(1, 0.1 * inch))

        timeline_fig = visualizations['timeline']


        timeline_buf = BytesIO()
        timeline_fig.savefig(timeline_buf, format='png', dpi=150, bbox_inches='tight')
        timeline_buf.seek(0)

        timeline_img = Image(
            timeline_buf,
            width=6.5 * inch,
            height=3.5 * inch
        )

        elements.append(timeline_img)

    # ================= PAGE 3 =================

    elements.append(Paragraph("🔬 Methodology & Interpretation", heading2_style))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Model Architecture", heading3_style))

    elements.append(Paragraph(
        "InstruNet AI employs a deep Convolutional Neural Network (CNN) "
        "specifically designed for multi-label music instrument recognition "
        "using log-scaled mel-spectrogram representations of audio signals.",
        body_style
    ))

    elements.append(Paragraph(
        "The input to the network is a two-dimensional mel-spectrogram treated "
        "as a single-channel image, preserving both temporal and spectral "
        "characteristics of the audio. The architecture consists of four "
        "hierarchical convolutional blocks with increasing filter depths of "
        "32, 64, 128, and 256 respectively. Each convolution uses a 5×5 kernel "
        "with same padding and ReLU activation, enabling the network to capture "
        "broad time–frequency patterns such as harmonic structures, timbral "
        "textures, and transient events.",
        body_style
    ))

    elements.append(Paragraph(
        "Each convolutional layer is followed by Batch Normalization to stabilize "
        "training and improve convergence. MaxPooling layers are applied after "
        "the first three convolutional blocks to progressively reduce spatial "
        "resolution while retaining salient features. The final convolutional "
        "block omits pooling to preserve high-level feature maps prior to global "
        "aggregation.",
        body_style
    ))

    elements.append(Paragraph(
        "Global Average Pooling is employed instead of fully connected layers, "
        "significantly reducing the number of trainable parameters and improving "
        "generalization. This design choice forces the network to learn "
        "class-specific activation maps rather than memorizing spatial positions. "
        "A Dropout layer with a rate of 0.4 is applied to further mitigate "
        "overfitting.",
        body_style
    ))

    elements.append(Paragraph(
        "The output layer consists of a dense layer with sigmoid activation, "
        "producing independent probability scores for each instrument class. "
        "This formulation supports multi-label classification, allowing multiple "
        "instruments to be detected simultaneously within the same audio segment.",
        body_style
    ))

    elements.append(Paragraph(
        "L2 weight regularization (λ = 1e-4) is applied to all convolutional and "
        "output layers to penalize large weights and enhance robustness. The model "
        "is trained using Stochastic Gradient Descent (SGD) with a learning rate of "
        "0.01, momentum of 0.9, and Nesterov acceleration. Binary cross-entropy is "
        "used as the loss function, and training is controlled using Early "
        "Stopping, learning rate reduction on plateau, and best-model checkpointing "
        "based on validation loss.",
        body_style
    ))

    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Analysis Process", heading3_style))

    process_data = [
        ['Step', 'Description'],
        ['1', 'Segmentation'],
        ['2', 'Feature Extraction'],
        ['3', 'Model Prediction'],
        ['4', 'Temporal Smoothing'],
        ['5', 'Aggregation'],
    ]

    process_table = Table(process_data, colWidths=[1.2 * inch, 5.3 * inch])

    process_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ]))

    elements.append(process_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ================= FOOTER =================

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )

    # ================= BUILD =================

    doc.build(elements)

    return pdf_path
