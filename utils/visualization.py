# utils/visualization.py

import matplotlib.pyplot as plt
import numpy as np
from config import CLASS_NAMES, CLASS_DISPLAY_NAMES

def plot_intensity(times, intensities, threshold):
    """
    Basic intensity plot for all instruments
    """
    plt.figure(figsize=(12, 4))
    for i, cls in enumerate(CLASS_NAMES):
        plt.plot(times, intensities[:, i], label=cls, alpha=0.7)
    plt.axhline(threshold, linestyle="--", color="red", alpha=0.4, label="Threshold")
    plt.xlabel("Time (sec)")
    plt.ylabel("Intensity")
    plt.legend(ncol=4, fontsize=8)
    plt.tight_layout()
    return plt.gcf()


def create_intensity_timeline(times, intensities, threshold, class_names):
    """
    Create a professional instrument intensity timeline visualization
    showing only detected instruments or top instruments
    
    Args:
        times: List of time points
        intensities: Array of shape (n_segments, n_classes)
        threshold: Detection threshold
        class_names: List of class names
    
    Returns:
        matplotlib figure
    """
    # Convert to numpy array if needed
    intensities = np.array(intensities)
    times = np.array(times)
    
    # Find instruments that exceed threshold at any point
    max_per_class = np.max(intensities, axis=0)
    detected_indices = np.where(max_per_class >= threshold)[0]
    
    # If no instruments detected, show top 5
    if len(detected_indices) == 0:
        top_indices = np.argsort(max_per_class)[-5:]
        detected_indices = top_indices
        title_suffix = " (Top 5 by Peak Confidence)"
    else:
        title_suffix = " (Detected Instruments)"
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Color palette
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    
    # Plot each detected instrument
    for idx, class_idx in enumerate(detected_indices):
        cls = class_names[class_idx]
        display_name = CLASS_DISPLAY_NAMES.get(cls, cls.upper())
        
        ax.plot(
            times,
            intensities[:, class_idx],
            label=display_name,
            linewidth=2.5,
            alpha=0.8,
            color=colors[idx % len(colors)]
        )
    
    # Add threshold line
    ax.axhline(
        threshold,
        linestyle="--",
        color="red",
        alpha=0.6,
        linewidth=1.5,
        label=f"Threshold ({threshold:.2f})"
    )
    
    # Styling
    ax.set_xlabel("Time (seconds)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Confidence", fontsize=12, fontweight='bold')
    ax.set_title(
        f"Instrument Intensity Timeline{title_suffix}",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Legend
    ax.legend(
        loc='upper left',
        bbox_to_anchor=(1.02, 1),
        fontsize=10,
        framealpha=0.95,
        edgecolor='gray'
    )
    
    # Set y-axis limits
    ax.set_ylim(-0.05, 1.05)
    
    plt.tight_layout()
    return fig


def create_multi_instrument_comparison(times, intensities, instruments_to_compare, threshold):
    """
    Create a comparison plot for specific instruments
    
    Args:
        times: List of time points
        intensities: Array of shape (n_segments, n_classes)
        instruments_to_compare: List of instrument codes to compare
        threshold: Detection threshold
    
    Returns:
        matplotlib figure
    """
    fig, axes = plt.subplots(len(instruments_to_compare), 1, figsize=(12, 3 * len(instruments_to_compare)))
    
    if len(instruments_to_compare) == 1:
        axes = [axes]
    
    for idx, instrument in enumerate(instruments_to_compare):
        class_idx = CLASS_NAMES.index(instrument)
        display_name = CLASS_DISPLAY_NAMES.get(instrument, instrument.upper())
        
        ax = axes[idx]
        ax.fill_between(
            times,
            0,
            intensities[:, class_idx],
            alpha=0.3,
            color='blue'
        )
        ax.plot(times, intensities[:, class_idx], linewidth=2, color='blue')
        ax.axhline(threshold, linestyle="--", color="red", alpha=0.6)
        
        ax.set_ylabel("Confidence", fontsize=10)
        ax.set_title(f"{display_name} Intensity", fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-0.05, 1.05)
        
        if idx == len(instruments_to_compare) - 1:
            ax.set_xlabel("Time (seconds)", fontsize=10)
    
    plt.tight_layout()
    return fig


def create_confidence_heatmap(times, intensities, class_names):
    """
    Create a heatmap showing confidence over time for all instruments
    
    Args:
        times: List of time points
        intensities: Array of shape (n_segments, n_classes)
        class_names: List of class names
    
    Returns:
        matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create display names
    display_names = [CLASS_DISPLAY_NAMES.get(cls, cls.upper()) for cls in class_names]
    
    # Create heatmap
    im = ax.imshow(
        intensities.T,
        aspect='auto',
        cmap='YlOrRd',
        interpolation='nearest',
        vmin=0,
        vmax=1
    )
    
    # Set ticks
    ax.set_yticks(np.arange(len(class_names)))
    ax.set_yticklabels(display_names)
    
    # Set x-axis to show time
    n_time_points = len(times)
    tick_positions = np.linspace(0, n_time_points - 1, min(10, n_time_points))
    tick_labels = [f"{times[int(pos)]:.1f}s" for pos in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45)
    
    # Labels
    ax.set_xlabel("Time", fontsize=12, fontweight='bold')
    ax.set_ylabel("Instrument", fontsize=12, fontweight='bold')
    ax.set_title("Instrument Confidence Heatmap", fontsize=14, fontweight='bold', pad=15)
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Confidence", rotation=270, labelpad=20, fontsize=11)
    
    plt.tight_layout()
    return fig