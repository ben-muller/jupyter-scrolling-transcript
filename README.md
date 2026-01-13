# Jupyter Scrolling Transcript Widget

<div align="center">
  <img src="./assets/demo.gif" width="600" alt="Jupyter Scrolling Transcript Demo">
</div>

A high-performance Jupyter widget for displaying streaming text with dual-mode scrolling behavior. Designed for live transcripts, logs, teleprompters, and subtitles.

## Features

- **Dual-Mode Scrolling**: 
    - **Fast Mode**: Instantly jumps to the bottom (ideal for loading history).
    - **Live Mode**: Smooth, slow-speed panning (configurable speed) for comfortable reading.
- **Sticky Scroll**: Auto-scroll pauses if the user manually scrolls up to read history, and resumes when they return to the bottom.
- **Manual Interrupt**: Any user interaction (wheel, click, touch) instantly cancels the auto-scroll animation to prevent "fighting" the user.
- **Newline Optimization**: Automatically strips newlines to present a continuous stream of text.
- **Keyword Highlighting**: Supports custom styles (color, bold, background) for specific words.

## Installation

You can install the widget directly from GitHub:

```bash
pip install git+https://github.com/ben-muller/jupyter-scrolling-transcript.git
```

## Usage

```python
from scrolling_transcript import ScrollingTranscriptWidget

# 1. Initialize
widget = ScrollingTranscriptWidget(
    height="400px", 
    theme="dark", 
    scroll_speed=0.05
)
widget.setup()

# 2. Append Text
widget.append_text("Hello world! ")

# 3. Highlight specific words
widget.append_text("WARNING: System overheat. ", styles={
    "warning": {"color": "red", "bold": True}
})

# 4. Switch Modes
widget.set_live_mode(True) # Turn on slow scrolling
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `height` | `"500px"` | CSS height of the widget container. |
| `theme` | `"dark"` | `"dark"` (light grey on dark bg) or `"light"`. |
| `scroll_speed` | `0.05` | Pixels per ms (0.05 = 50px/sec). |
| `sticky_threshold` | `150` | Distance from bottom (px) to consider "at bottom". |
