"""
app.py - DrawForge Main Application UI
Assembles the top bar, sidebar, canvas, and status bar.
Keeps all UI logic separate from tool/canvas logic.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image

from canvas_engine import CanvasEngine
from tool_engine import ToolManager

# ── Palette ─────────────────────────────────────────────────────────
DARK_BG    = "#1A1A2E"
PANEL_BG   = "#16213E"
ACCENT     = "#E94560"
ACCENT2    = "#0F3460"
TEXT_COLOR = "#E0E0E0"
MUTED      = "#8892A4"
BTN_BG     = "#1E2A45"
BTN_HOVER  = "#2A3F6B"
CANVAS_BG  = "#F8F8F8"

TOOL_DEFS = [
    ("✏️ Brush",     "brush"),
    ("◻ Eraser",    "eraser"),
    ("⬛ Rectangle", "rectangle"),
    ("⭕ Ellipse",   "ellipse"),
    ("╱  Line",      "line"),
    ("🪣 Fill",      "fill"),
    ("🌊 Warp",      "warp"),
]

QUICK_COLORS = [
    "#000000", "#FFFFFF", "#E94560", "#FF6B35",
    "#FFD93D", "#6BCB77", "#4D96FF", "#C77DFF",
    "#8B4513", "#708090",
]


class DrawForgeApp:
    def __init__(self, resource_path_fn):
        self.resource_path = resource_path_fn
        self.root = tk.Tk()
        self.root.title("DrawForge — Professional Drawing Studio")
        self.root.configure(bg=DARK_BG)
        self.root.geometry("1400x900")
        self.root.minsize(900, 600)

        self._apply_styles()
        self._build_ui()
        self._configure_grid()

    # ── Styles ─────────────────────────────────────────────────────
    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=DARK_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("TLabel",
                        background=DARK_BG, foreground=TEXT_COLOR,
                        font=("Segoe UI", 9))
        style.configure("Title.TLabel",
                        background=PANEL_BG, foreground=TEXT_COLOR,
                        font=("Segoe UI", 8, "bold"))
        style.configure("Status.TLabel",
                        background=ACCENT2, foreground=TEXT_COLOR,
                        font=("Consolas", 9), padding=(6, 2))
        style.configure("TScale",
                        background=PANEL_BG,
                        troughcolor=BTN_BG,
                        sliderlength=14)
        style.configure("TCheckbutton",
                        background=PANEL_BG, foreground=TEXT_COLOR,
                        font=("Segoe UI", 9))
        style.map("TCheckbutton",
                  background=[("active", BTN_HOVER)])

    # ── UI Construction ────────────────────────────────────────────
    def _build_ui(self):
        self._build_menubar()
        self._build_topbar()
        self._build_main_area()
        self._build_statusbar()
        self._select_tool("brush")  # initialise after all widgets exist

    def _configure_grid(self):
        self.root.rowconfigure(0, weight=0)  # menubar
        self.root.rowconfigure(1, weight=0)  # topbar
        self.root.rowconfigure(2, weight=1)  # main area
        self.root.rowconfigure(3, weight=0)  # status
        self.root.columnconfigure(0, weight=1)

    # ── Menu ───────────────────────────────────────────────────────
    def _build_menubar(self):
        mb = tk.Menu(self.root, bg=PANEL_BG, fg=TEXT_COLOR,
                     activebackground=ACCENT, activeforeground="#FFF",
                     relief="flat", tearoff=False)
        self.root.config(menu=mb)

        file_menu = tk.Menu(mb, bg=PANEL_BG, fg=TEXT_COLOR,
                            activebackground=ACCENT, activeforeground="#FFF",
                            relief="flat", tearoff=False)
        mb.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Canvas",        command=self._new_canvas)
        file_menu.add_command(label="Import Image...",   command=self._import_image)
        file_menu.add_separator()
        file_menu.add_command(label="Save As...",        command=self._save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",              command=self.root.quit)

        edit_menu = tk.Menu(mb, bg=PANEL_BG, fg=TEXT_COLOR,
                            activebackground=ACCENT, activeforeground="#FFF",
                            relief="flat", tearoff=False)
        mb.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear Canvas", command=self._clear_canvas)

    # ── Top bar ────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=PANEL_BG, height=52)
        bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        bar.grid_propagate(False)

        # App title
        title = tk.Label(bar, text="⬡ DrawForge", bg=PANEL_BG,
                         fg=ACCENT, font=("Segoe UI", 14, "bold"), padx=14)
        title.pack(side="left")

        sep = tk.Frame(bar, bg=ACCENT2, width=1)
        sep.pack(side="left", fill="y", padx=6, pady=8)

        # Brush size
        tk.Label(bar, text="Size", bg=PANEL_BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="left", padx=(6, 2))
        self._size_var = tk.IntVar(value=8)
        self._size_label = tk.Label(bar, textvariable=self._size_var,
                                    bg=PANEL_BG, fg=TEXT_COLOR,
                                    font=("Consolas", 9), width=3)
        self._size_label.pack(side="left")
        size_slider = ttk.Scale(bar, from_=1, to=80,
                                variable=self._size_var,
                                orient="horizontal", length=120,
                                command=self._on_size_change)
        size_slider.pack(side="left", padx=(0, 8))

        sep2 = tk.Frame(bar, bg=ACCENT2, width=1)
        sep2.pack(side="left", fill="y", padx=6, pady=8)

        # Color picker button
        tk.Label(bar, text="Color", bg=PANEL_BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="left", padx=(6, 4))
        self._color_swatch = tk.Label(bar, bg="#000000", width=4, relief="solid",
                                      cursor="hand2")
        self._color_swatch.pack(side="left", padx=(0, 2), ipady=10)
        self._color_swatch.bind("<Button-1>", lambda e: self._pick_color())

        # Hex entry
        self._hex_var = tk.StringVar(value="#000000")
        hex_entry = tk.Entry(bar, textvariable=self._hex_var,
                             bg=BTN_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                             width=8, relief="flat", font=("Consolas", 9))
        hex_entry.pack(side="left", padx=(2, 8))
        hex_entry.bind("<Return>", self._on_hex_entry)

        # Quick color swatches
        for c in QUICK_COLORS:
            btn = tk.Label(bar, bg=c, width=2, cursor="hand2", relief="raised")
            btn.pack(side="left", padx=1, ipady=8)
            btn.bind("<Button-1>", lambda e, col=c: self._set_color(col))

        sep3 = tk.Frame(bar, bg=ACCENT2, width=1)
        sep3.pack(side="left", fill="y", padx=6, pady=8)

        # Fill toggle
        self._fill_var = tk.BooleanVar(value=False)
        fill_chk = ttk.Checkbutton(bar, text="Fill", variable=self._fill_var,
                                   command=self._on_fill_change, style="TCheckbutton")
        fill_chk.pack(side="left", padx=6)

        # Warp settings (shown only when warp active)
        self._warp_frame = tk.Frame(bar, bg=PANEL_BG)

        tk.Label(self._warp_frame, text="Radius", bg=PANEL_BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="left", padx=(6, 2))
        self._warp_radius_var = tk.IntVar(value=60)
        ttk.Scale(self._warp_frame, from_=10, to=200,
                  variable=self._warp_radius_var,
                  orient="horizontal", length=80,
                  command=self._on_warp_change).pack(side="left")

        tk.Label(self._warp_frame, text="Strength", bg=PANEL_BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="left", padx=(8, 2))
        self._warp_strength_var = tk.DoubleVar(value=0.3)
        ttk.Scale(self._warp_frame, from_=0.05, to=1.0,
                  variable=self._warp_strength_var,
                  orient="horizontal", length=80,
                  command=self._on_warp_change).pack(side="left")

        # Action buttons (right side)
        save_btn = self._make_topbar_btn(bar, "💾 Save", self._save_as)
        save_btn.pack(side="right", padx=4)
        import_btn = self._make_topbar_btn(bar, "📂 Import", self._import_image)
        import_btn.pack(side="right", padx=4)
        new_btn = self._make_topbar_btn(bar, "🗋 New", self._new_canvas)
        new_btn.pack(side="right", padx=4)

    def _make_topbar_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, command=cmd,
                        bg=BTN_BG, fg=TEXT_COLOR, relief="flat",
                        font=("Segoe UI", 8, "bold"),
                        activebackground=ACCENT, activeforeground="#FFF",
                        padx=10, pady=4, cursor="hand2")
        btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=BTN_BG))
        return btn

    # ── Main area ─────────────────────────────────────────────────
    def _build_main_area(self):
        main = tk.Frame(self.root, bg=DARK_BG)
        main.grid(row=2, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # Left sidebar
        self._sidebar = tk.Frame(main, bg=PANEL_BG, width=80)
        self._sidebar.grid(row=0, column=0, sticky="ns")
        self._sidebar.grid_propagate(False)

        self._tool_buttons = {}
        self._active_tool_name = tk.StringVar(value="brush")

        tk.Label(self._sidebar, text="TOOLS", bg=PANEL_BG, fg=MUTED,
                 font=("Segoe UI", 7, "bold")).pack(pady=(12, 6))

        for label, tool_name in TOOL_DEFS:
            btn = tk.Button(
                self._sidebar, text=label,
                command=lambda t=tool_name: self._select_tool(t),
                bg=BTN_BG, fg=TEXT_COLOR, relief="flat",
                font=("Segoe UI", 8), anchor="w",
                padx=8, pady=6, cursor="hand2",
                width=10, wraplength=70
            )
            btn.pack(fill="x", padx=6, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BTN_HOVER)
                     if b != self._tool_buttons.get("_active") else None)
            btn.bind("<Leave>", lambda e, b=btn, t=tool_name: b.config(
                bg=ACCENT if t == self._active_tool_name.get() else BTN_BG))
            self._tool_buttons[tool_name] = btn

        # Canvas area with scroll
        canvas_frame = tk.Frame(main, bg="#2A2A3E")
        canvas_frame.grid(row=0, column=1, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        # Scrollable container
        self._canvas_scroll_frame = tk.Frame(canvas_frame, bg="#2A2A3E")
        self._canvas_scroll_frame.grid(row=0, column=0, sticky="nsew")
        self._canvas_scroll_frame.rowconfigure(0, weight=1)
        self._canvas_scroll_frame.columnconfigure(0, weight=1)

        canvas_inner = tk.Frame(self._canvas_scroll_frame, bg=CANVAS_BG,
                                bd=2, relief="solid")
        canvas_inner.grid(row=0, column=0)

        self.canvas_engine = CanvasEngine(
            parent=canvas_inner,
            width=1100, height=750,
            bg_color=CANVAS_BG,
            on_coordinate_update=self._update_coords,
        )

        self.tool_manager = ToolManager(self.canvas_engine)

        # Track mouse position even without click
        self.canvas_engine.tk_canvas.bind(
            "<Motion>", lambda e: self._update_coords(e.x, e.y))

    # ── Status bar ────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=ACCENT2, height=24)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_propagate(False)

        self._coord_var = tk.StringVar(value="X: 0   Y: 0")
        ttk.Label(bar, textvariable=self._coord_var,
                  style="Status.TLabel").pack(side="left")

        self._tool_status_var = tk.StringVar(value="Tool: Brush")
        ttk.Label(bar, textvariable=self._tool_status_var,
                  style="Status.TLabel").pack(side="left", padx=20)

        ttk.Label(bar, text="Canvas: 1100 × 750 px",
                  style="Status.TLabel").pack(side="right")

    # ── Event handlers ────────────────────────────────────────────
    def _update_coords(self, x, y):
        if hasattr(self, "_coord_var"):
            self._coord_var.set(f"X: {x:4d}   Y: {y:4d}")

    def _select_tool(self, tool_name: str):
        self.tool_manager.set_tool(tool_name)
        self._active_tool_name.set(tool_name)

        # Update button highlights
        for name, btn in self._tool_buttons.items():
            btn.config(bg=ACCENT if name == tool_name else BTN_BG)

        # Show/hide warp controls in topbar
        if tool_name == "warp":
            self._warp_frame.pack(side="left", padx=4)
        else:
            self._warp_frame.pack_forget()

        label = next((l for l, t in TOOL_DEFS if t == tool_name), tool_name)
        self._tool_status_var.set(f"Tool: {label.strip()}")

    def _on_size_change(self, val):
        size = int(float(val))
        self.tool_manager.state.size = size

    def _pick_color(self):
        current = self.tool_manager.state.color
        result = colorchooser.askcolor(
            color=current, title="Choose Brush Color", parent=self.root)
        if result and result[1]:
            self._set_color(result[1])

    def _set_color(self, hex_color: str):
        self.tool_manager.state.color = hex_color
        self._color_swatch.config(bg=hex_color)
        self._hex_var.set(hex_color)

    def _on_hex_entry(self, event=None):
        val = self._hex_var.get().strip()
        if not val.startswith("#"):
            val = "#" + val
        try:
            self.root.winfo_rgb(val)  # validates
            self._set_color(val)
        except Exception:
            self._hex_var.set(self.tool_manager.state.color)

    def _on_fill_change(self):
        self.tool_manager.state.filled = self._fill_var.get()

    def _on_warp_change(self, val=None):
        self.tool_manager.state.warp_radius = self._warp_radius_var.get()
        self.tool_manager.state.warp_strength = self._warp_strength_var.get()

    # ── File operations ───────────────────────────────────────────
    def _new_canvas(self):
        if messagebox.askyesno("New Canvas",
                               "Clear the current canvas? This cannot be undone.",
                               parent=self.root):
            self.canvas_engine.clear_canvas()
            self.canvas_engine.refresh()

    def _import_image(self):
        path = filedialog.askopenfilename(
            title="Import Image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff"),
                ("All files", "*.*"),
            ],
            parent=self.root,
        )
        if not path:
            return
        try:
            img = Image.open(path)
            self.canvas_engine.import_image(img, x=0, y=0)
            self.canvas_engine.refresh()
        except Exception as exc:
            messagebox.showerror("Import Error", str(exc), parent=self.root)

    def _clear_canvas(self):
        self.canvas_engine.clear_canvas()
        self.canvas_engine.refresh()

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Canvas As",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("BMP Image", "*.bmp"),
                ("All files", "*.*"),
            ],
            parent=self.root,
        )
        if not path:
            return
        try:
            self.canvas_engine.export(path)
            messagebox.showinfo("Saved", f"Canvas saved to:\n{path}", parent=self.root)
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc), parent=self.root)

    # ── Entry point ───────────────────────────────────────────────
    def run(self):
        self.root.mainloop()
