"""
tool_engine.py - Modular tool system.
Each tool class handles its own mouse events. New tools can be added
by subclassing BaseTool without touching the UI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
import tkinter as tk

if TYPE_CHECKING:
    from canvas_engine import CanvasEngine


# ------------------------------------------------------------------ #
#  Tool state shared across all tools                                  #
# ------------------------------------------------------------------ #

@dataclass
class ToolState:
    color: str = "#000000"
    size: int = 8
    filled: bool = False
    warp_radius: int = 60
    warp_strength: float = 0.3


# ------------------------------------------------------------------ #
#  Base tool                                                           #
# ------------------------------------------------------------------ #

class BaseTool:
    NAME = "base"
    CURSOR = "crosshair"

    def __init__(self, canvas_engine: "CanvasEngine", state: ToolState):
        self.ce = canvas_engine
        self.state = state
        self._last_x: Optional[int] = None
        self._last_y: Optional[int] = None
        self._start_x: Optional[int] = None
        self._start_y: Optional[int] = None

    def on_press(self, event: tk.Event):
        self._last_x = event.x
        self._last_y = event.y
        self._start_x = event.x
        self._start_y = event.y

    def on_drag(self, event: tk.Event):
        pass

    def on_release(self, event: tk.Event):
        self._last_x = None
        self._last_y = None

    def reset(self):
        self._last_x = None
        self._last_y = None
        self._start_x = None
        self._start_y = None


# ------------------------------------------------------------------ #
#  Brush tool                                                          #
# ------------------------------------------------------------------ #

class BrushTool(BaseTool):
    NAME = "brush"
    CURSOR = "crosshair"

    def on_press(self, event: tk.Event):
        super().on_press(event)
        # Draw a dot at press point
        self.ce.draw_stroke(event.x, event.y, event.x, event.y,
                            self.state.color, self.state.size, "brush")
        self.ce.refresh()

    def on_drag(self, event: tk.Event):
        if self._last_x is None:
            return
        # Batch: only refresh every ~3px movement for performance
        dx = event.x - self._last_x
        dy = event.y - self._last_y
        if dx * dx + dy * dy < 4:
            return
        self.ce.draw_stroke(self._last_x, self._last_y, event.x, event.y,
                            self.state.color, self.state.size, "brush")
        self._last_x, self._last_y = event.x, event.y
        self.ce.refresh()

    def on_release(self, event: tk.Event):
        super().on_release(event)


# ------------------------------------------------------------------ #
#  Eraser tool                                                         #
# ------------------------------------------------------------------ #

class EraserTool(BaseTool):
    NAME = "eraser"
    CURSOR = "circle"

    def on_press(self, event: tk.Event):
        super().on_press(event)
        self.ce.draw_stroke(event.x, event.y, event.x, event.y,
                            "#FFFFFF", self.state.size * 2, "eraser")
        self.ce.refresh()

    def on_drag(self, event: tk.Event):
        if self._last_x is None:
            return
        dx = event.x - self._last_x
        dy = event.y - self._last_y
        if dx * dx + dy * dy < 4:
            return
        self.ce.draw_stroke(self._last_x, self._last_y, event.x, event.y,
                            "#FFFFFF", self.state.size * 2, "eraser")
        self._last_x, self._last_y = event.x, event.y
        self.ce.refresh()


# ------------------------------------------------------------------ #
#  Shape tools                                                         #
# ------------------------------------------------------------------ #

class RectangleTool(BaseTool):
    NAME = "rectangle"
    CURSOR = "crosshair"

    def on_drag(self, event: tk.Event):
        if self._start_x is None:
            return
        self.ce.draw_shape_preview("rectangle", self._start_x, self._start_y,
                                   event.x, event.y, self.state.color,
                                   self.state.size, self.state.filled)
        self.ce.refresh()

    def on_release(self, event: tk.Event):
        if self._start_x is not None:
            self.ce.commit_shape("rectangle", self._start_x, self._start_y,
                                 event.x, event.y, self.state.color,
                                 self.state.size, self.state.filled)
            self.ce.refresh()
        super().on_release(event)


class EllipseTool(BaseTool):
    NAME = "ellipse"
    CURSOR = "crosshair"

    def on_drag(self, event: tk.Event):
        if self._start_x is None:
            return
        self.ce.draw_shape_preview("ellipse", self._start_x, self._start_y,
                                   event.x, event.y, self.state.color,
                                   self.state.size, self.state.filled)
        self.ce.refresh()

    def on_release(self, event: tk.Event):
        if self._start_x is not None:
            self.ce.commit_shape("ellipse", self._start_x, self._start_y,
                                 event.x, event.y, self.state.color,
                                 self.state.size, self.state.filled)
            self.ce.refresh()
        super().on_release(event)


class LineTool(BaseTool):
    NAME = "line"
    CURSOR = "crosshair"

    def on_drag(self, event: tk.Event):
        if self._start_x is None:
            return
        self.ce.draw_shape_preview("line", self._start_x, self._start_y,
                                   event.x, event.y, self.state.color,
                                   self.state.size, False)
        self.ce.refresh()

    def on_release(self, event: tk.Event):
        if self._start_x is not None:
            self.ce.commit_shape("line", self._start_x, self._start_y,
                                 event.x, event.y, self.state.color,
                                 self.state.size, False)
            self.ce.refresh()
        super().on_release(event)


# ------------------------------------------------------------------ #
#  Warp / Liquify tool                                                 #
# ------------------------------------------------------------------ #

class WarpTool(BaseTool):
    NAME = "warp"
    CURSOR = "sizing"

    def on_drag(self, event: tk.Event):
        self.ce.apply_warp(event.x, event.y,
                           self.state.warp_radius,
                           self.state.warp_strength)
        self._last_x, self._last_y = event.x, event.y
        self.ce.refresh()


# ------------------------------------------------------------------ #
#  Fill tool                                                           #
# ------------------------------------------------------------------ #

class FillTool(BaseTool):
    NAME = "fill"
    CURSOR = "spraycan"

    def on_press(self, event: tk.Event):
        from PIL import ImageDraw
        from canvas_engine import CanvasEngine
        target_color = self.ce.pil_image.getpixel((event.x, event.y))[:3]
        fill_rgb = CanvasEngine._hex_to_rgba(self.state.color)[:3]
        if target_color == fill_rgb:
            return
        _flood_fill(self.ce.pil_image, event.x, event.y, target_color, fill_rgb)
        self.ce.pil_draw = ImageDraw.Draw(self.ce.pil_image)
        self.ce.refresh()


def _flood_fill(img, x, y, target, replacement):
    """Iterative flood fill (no recursion limit issues)."""
    w, h = img.size
    pixels = img.load()
    stack = [(x, y)]
    visited = set()
    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        if cx < 0 or cx >= w or cy < 0 or cy >= h:
            continue
        current = pixels[cx, cy][:3]
        if current != target:
            continue
        visited.add((cx, cy))
        pixels[cx, cy] = replacement + (255,)
        stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])


# ------------------------------------------------------------------ #
#  Tool registry                                                        #
# ------------------------------------------------------------------ #

TOOL_REGISTRY = {
    "brush": BrushTool,
    "eraser": EraserTool,
    "rectangle": RectangleTool,
    "ellipse": EllipseTool,
    "line": LineTool,
    "warp": WarpTool,
    "fill": FillTool,
}


class ToolManager:
    """Manages the active tool and routes canvas events to it."""

    def __init__(self, canvas_engine: "CanvasEngine"):
        self.ce = canvas_engine
        self.state = ToolState()
        self._active_tool: BaseTool = BrushTool(canvas_engine, self.state)

        # Bind mouse events
        c = canvas_engine.tk_canvas
        c.bind("<ButtonPress-1>", self._on_press)
        c.bind("<B1-Motion>", self._on_drag)
        c.bind("<ButtonRelease-1>", self._on_release)

    def set_tool(self, name: str):
        cls = TOOL_REGISTRY.get(name)
        if cls:
            self._active_tool = cls(self.ce, self.state)
            self.ce.tk_canvas.config(cursor=cls.CURSOR)

    def _on_press(self, event):
        self._active_tool.on_press(event)

    def _on_drag(self, event):
        self._active_tool.on_drag(event)
        if self.ce.on_coordinate_update:
            self.ce.on_coordinate_update(event.x, event.y)

    def _on_release(self, event):
        self._active_tool.on_release(event)
