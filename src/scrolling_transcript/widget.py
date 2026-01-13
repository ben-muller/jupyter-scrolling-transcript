import html
import re
import ipywidgets as widgets
from IPython.display import display, Javascript

class ScrollingTranscriptWidget:
    """
    A Jupyter widget for displaying streaming text with:
    - Dual-mode scrolling (Fast jump for history, Slow smooth scroll for live)
    - Sticky scroll (pauses auto-scroll when user scrolls up)
    - High-performance rendering
    """
    def __init__(self, height="500px", font_size="18px", theme="dark", scroll_speed=0.05, sticky_threshold=150):
        """
        Args:
            height (str): CSS height of the widget (e.g. "500px").
            font_size (str): CSS font size (e.g. "18px").
            theme (str): "dark" or "light".
            scroll_speed (float): Pixels per millisecond for the slow scroll. 0.05 = 50px/sec.
            sticky_threshold (int): Distance from bottom in pixels to consider "at the bottom".
        """
        self.height = height
        self.font_size = font_size
        self.scroll_speed = scroll_speed
        self.sticky_threshold = sticky_threshold
        
        # Theme configuration
        if theme == "dark":
            self.text_color = "#e0e0e0"
            self.bg_color = "#2b2b2b"
        else:
            self.text_color = "#222222"
            self.bg_color = "#ffffff"
            
        self.chunks = {} 
        self.chunk_ids = []
        self.auto_scroll_enabled = True
        self.is_live = False # Toggled manually or by logic
        
        self.html_widget = widgets.HTML(
            value=f"<div style='color: #888; font-style: italic;'>Waiting for stream...</div>",
            layout=widgets.Layout(height=self.height, overflow="auto", width="100%")
        )
        self.container_id = f"transcript-render-{id(self)}"
        
    def setup(self):
        """Initializes the widget and injects the scrolling JavaScript."""
        # Unique class for this instance to avoid collisions
        self.unique_class = f"transcript-scroll-{id(self)}"
        self.html_widget.add_class(self.unique_class)
        
        display(self.html_widget)
        self._inject_js()

    def _inject_js(self):
        js = f"""
        (function() {{
            const targetClass = '{self.unique_class}';
            const SCROLL_SPEED = {self.scroll_speed}; 
            const STICKY_THRESHOLD = {self.sticky_threshold};

            function cancelAnim(element) {{
                if (element.currentScrollAnim) {{
                    cancelAnimationFrame(element.currentScrollAnim);
                    element.currentScrollAnim = null;
                }}
            }}

            function animateScroll(element, finalTarget) {{
                 cancelAnim(element);
                 const start = element.scrollTop;
                 const distance = finalTarget - start;
                 if (distance <= 0) return;

                 let duration = distance / SCROLL_SPEED;
                 if (duration < 1000) duration = 1000; 
                 
                 const startTime = performance.now();
                 let lastPos = start;
                 
                 function step(currentTime) {{
                    // Interruption Check
                    if (Math.abs(element.scrollTop - lastPos) > 1) {{
                        element.currentScrollAnim = null;
                        return;
                    }}

                    const elapsed = currentTime - startTime;
                    if (elapsed < duration) {{
                        const nextPos = start + (distance * (elapsed / duration));
                        element.scrollTop = nextPos;
                        lastPos = nextPos; 
                        element.currentScrollAnim = requestAnimationFrame(step);
                    }} else {{
                        element.scrollTop = finalTarget;
                        element.currentScrollAnim = null;
                    }}
                 }}
                 element.currentScrollAnim = requestAnimationFrame(step);
            }}

            const handleUserScroll = (e) => {{
                const el = e.target.closest && e.target.closest('.' + targetClass);
                if (el) cancelAnim(el);
            }};
            document.addEventListener('wheel', handleUserScroll, {{passive: true}});
            document.addEventListener('mousedown', handleUserScroll, {{passive: true}});
            document.addEventListener('touchstart', handleUserScroll, {{passive: true}});

            const observer = new MutationObserver((mutations) => {{
                const widgets = document.querySelectorAll('.' + targetClass);
                widgets.forEach(w => {{
                    const inner = w.querySelector('div[data-scroll-mode]');
                    const mode = inner ? inner.getAttribute('data-scroll-mode') : 'fast';
                    const target = w.scrollHeight - w.clientHeight;
                    
                    if (mode === 'fast') {{
                        w.scrollTop = target;
                    }} else {{
                        // Sticky Scroll Logic
                        const isNearBottom = w.scrollTop > target - STICKY_THRESHOLD;
                        if (isNearBottom && w.scrollTop < target - 2) {{
                            animateScroll(w, target);
                        }}
                    }}
                }});
            }});
            observer.observe(document.body, {{ childList: true, subtree: true }});
        }})();
        """
        display(Javascript(js))

    def append_text(self, text, styles=None):
        """
        Appends text to the widget.
        args:
            text (str): The text to append.
            styles (dict): Optional dictionary for keyword highlighting. 
                           Format: {"word": {"color": "red", "bold": True}}
        """
        cid = len(self.chunk_ids) + 1
        self.chunk_ids.append(cid)
        
        # Strip newlines for continuous flow as per best practice
        clean_text = text.replace("\n", " ")
        if styles:
            formatted = self._format_highlight_html(clean_text, styles)
        else:
            formatted = html.escape(clean_text)
            
        self.chunks[cid] = formatted + " "
        self._render()

    def set_live_mode(self, is_live: bool):
        """Switches between 'fast' jump (history) and 'slow' scroll (live)."""
        self.is_live = is_live
        self._render()

    def _format_highlight_html(self, text, styles):
        safe = html.escape(text)
        if not styles: return safe
        
        # Normalize keys
        norm_styles = {k.lower(): v for k, v in styles.items()}
        escaped_words = [re.escape(w).replace(r"\ ", r"\s+") for w in norm_styles.keys()]
        escaped_words.sort(key=len, reverse=True)
        
        if not escaped_words: return safe

        pattern = re.compile(r"\b(" + "|".join(escaped_words) + r")\b", re.IGNORECASE)

        def style_to_css(st):
            parts = []
            if st.get("color"): parts.append(f"color:{st['color']}")
            bg = st.get("bg") or st.get("background")
            if bg: parts.append(f"background:{bg};padding:0 2px;border-radius:2px")
            if st.get("bold"): parts.append("font-weight:700")
            if st.get("italic"): parts.append("font-style:italic")
            if st.get("underline"): parts.append("text-decoration:underline")
            return ";".join(parts)

        def repl(m):
            original = m.group(0)
            css = style_to_css(norm_styles.get(original.lower(), {}))
            return f"<span style='{css}'>{original}</span>" if css else original

        return pattern.sub(repl, safe)

    def _render(self):
        full_html = "".join(self.chunks[cid] for cid in self.chunk_ids)
        scroll_mode = "slow" if self.is_live else "fast"
        
        wrapped = f"""
        <div data-scroll-mode="{scroll_mode}" style="
            font-family: Inter, -apple-system, sans-serif; 
            font-size: {self.font_size}; 
            line-height: 1.6; 
            color: {self.text_color}; 
            background-color: {self.bg_color}; 
            padding: 5px; 
            border-radius: 4px; 
            white-space: pre-wrap;">
            {full_html}
        </div>
        """
        self.html_widget.value = wrapped
