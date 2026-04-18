"""
canvas_engine.py - Dual-layer canvas system.
Manages the Tkinter Canvas (display) and PIL Image (persistent storage).
"""

import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
from typing import Optional, Tuple, Callable


class CanvasEngine:
    """
    Dual-layer canvas:
      - self.pil_image  : PIL Image that stores all committed strokes permanently.
      - self.tk_canvas  : Tkinter Canvas used for real-time preview only.
      - self.overlay    : Ephemeral PIL Image for live stroke previews (cleared each commit).
    """

    def __init__(
        self,
        parent: tk.Widget,
        width: int = 1200,
        height: int = 800,
        bg_color: str = "#FFFFFF",
        on_coordinate_update: Optional[Callable[[int, int], None]] = None,
    ):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.on_coordinate_update = on_coordinate_update

        # --- PIL layers ---
        self.pil_image = Image.new("RGBA", (width, height), bg_color)
        self.pil_draw = ImageDraw.Draw(self.pil_image)

        # Overlay for ephemeral previews (shapes not yet committed)
        self.overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.overlay_draw = ImageDraw.Draw(self.overlay)

        # --- Tkinter Canvas ---
        self.tk_canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=bg_color,
            cursor="crosshair",
            highlightthickness=0,
        )
        self.tk_canvas.pack(expand=True, fill="both")

        # PhotoImage reference (must be kept alive to avoid GC)
        self._photo_image: Optional[ImageTk.PhotoImage] = None

        # Refresh the canvas display
        self._refresh_display()

    # ------------------------------------------------------------------ #
    #  Display helpers                                                     #
    # ------------------------------------------------------------------ #

    def _refresh_display(self):
        """Composite PIL image + overlay, push to Tkinter canvas."""
        composite = Image.alpha_composite(
            self.pil_image.convert("RGBA"), self.overlay
        )
        self._photo_image = ImageTk.PhotoImage(composite)
        self.tk_canvas.delete("all")
        self.tk_canvas.create_image(0, 0, anchor="nw", image=self._photo_image)

    def commit_overlay(self):
        """Flatten the overlay onto the permanent PIL image and clear overlay."""
        self.pil_image = Image.alpha_composite(
            self.pil_image.convert("RGBA"), self.overlay
        )
        self.pil_draw = ImageDraw.Draw(self.pil_image)
        self.clear_overlay()

    def clear_overlay(self):
        """Wipe the ephemeral overlay."""
        self.overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        self.overlay_draw = ImageDraw.Draw(self.overlay)

    def refresh(self):
        """Public refresh – call after any draw operation."""
        self._refresh_display()

    # ------------------------------------------------------------------ #
    #  Canvas operations                                                   #
    # ------------------------------------------------------------------ #

    def draw_stroke(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: str,
        size: int,
        tool: str = "brush",
    ):
        """Draw a brush/eraser stroke directly onto the permanent PIL image."""
        rgba = self._hex_to_rgba(color) if tool != "eraser" else (255, 255, 255, 255)
        fill = rgba if tool != "eraser" else (255, 255, 255, 255)

        self.pil_draw.ellipse(
            [x0 - size, y0 - size, x0 + size, y0 + size], fill=fill
        )
        self.pil_draw.line([x0, y0, x1, y1], fill=fill, width=size * 2)
        self.pil_draw.ellipse(
            [x1 - size, y1 - size, x1 + size, y1 + size], fill=fill
        )

    def draw_shape_preview(
        self,
        shape: str,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: str,
        size: int,
        filled: bool = False,
    ):
        """Draw a shape preview on the overlay (not yet committed)."""
        self.clear_overlay()
        rgba = self._hex_to_rgba(color)
        fill_color = rgba if filled else None
        w = max(1, size)

        if shape == "rectangle":
            self.overlay_draw.rectangle([x0, y0, x1, y1], outline=rgba, fill=fill_color, width=w)
        elif shape == "ellipse":
            self.overlay_draw.ellipse([x0, y0, x1, y1], outline=rgba, fill=fill_color, width=w)
        elif shape == "line":
            self.overlay_draw.line([x0, y0, x1, y1], fill=rgba, width=w)

    def commit_shape(
        self,
        shape: str,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: str,
        size: int,
        filled: bool = False,
    ):
        """Commit a shape permanently onto the PIL image."""
        rgba = self._hex_to_rgba(color)
        fill_color = rgba if filled else None
        w = max(1, size)

        if shape == "rectangle":
            self.pil_draw.rectangle([x0, y0, x1, y1], outline=rgba, fill=fill_color, width=w)
        elif shape == "ellipse":
            self.pil_draw.ellipse([x0, y0, x1, y1], outline=rgba, fill=fill_color, width=w)
        elif shape == "line":
            self.pil_draw.line([x0, y0, x1, y1], fill=rgba, width=w)

        self.clear_overlay()

    def import_image(self, img: Image.Image, x: int = 0, y: int = 0):
        """Paste an imported image at position (x, y) onto the PIL canvas."""
        img_rgba = img.convert("RGBA")
        # Fit within canvas bounds
        max_w = self.width - x
        max_h = self.height - y
        if img_rgba.width > max_w or img_rgba.height > max_h:
            img_rgba.thumbnail((max_w, max_h), Image.LANCZOS)
        self.pil_image.paste(img_rgba, (x, y), img_rgba)
        self.pil_draw = ImageDraw.Draw(self.pil_image)

    def apply_warp(self, cx: int, cy: int, radius: int, strength: float):
        """
        Liquify/warp effect: push pixels radially outward from (cx, cy).
        Uses PIL mesh transform for a pure-PIL implementation (no scipy required).
        """
        import numpy as np

        arr = np.array(self.pil_image.convert("RGBA"), dtype=np.float32)
        h, w = arr.shape[:2]
        result = arr.copy()

        r2 = radius * radius
        x_min = max(0, cx - radius)
        x_max = min(w, cx + radius)
        y_min = max(0, cy - radius)
        y_max = min(h, cy + radius)

        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                dx = x - cx
                dy = y - cy
                dist2 = dx * dx + dy * dy
                if dist2 < r2 and dist2 > 0:
                    dist = dist2 ** 0.5
                    factor = (1 - (dist / radius) ** 2) * strength
                    src_x = int(x - dx * factor)
                    src_y = int(y - dy * factor)
                    src_x = max(0, min(w - 1, src_x))
                    src_y = max(0, min(h - 1, src_y))
                    result[y, x] = arr[src_y, src_x]

        self.pil_image = Image.fromarray(result.astype(np.uint8), "RGBA")
        self.pil_draw = ImageDraw.Draw(self.pil_image)

    # ------------------------------------------------------------------ #
    #  Export                                                              #
    # ------------------------------------------------------------------ #

    def export(self, filepath: str):
        """Save the current canvas (with overlay flattened) to a file."""
        composite = Image.alpha_composite(
            self.pil_image.convert("RGBA"), self.overlay
        )
        if filepath.lower().endswith((".jpg", ".jpeg")):
            composite = composite.convert("RGB")
        composite.save(filepath)

    def clear_canvas(self):
        """Reset everything to a blank white canvas."""
        self.pil_image = Image.new("RGBA", (self.width, self.height), self.bg_color)
        self.pil_draw = ImageDraw.Draw(self.pil_image)
        self.clear_overlay()

    # ------------------------------------------------------------------ #
    #  Utilities                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b, alpha)
