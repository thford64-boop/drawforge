# DrawForge — Requirements & Build Guide

## Python Dependencies

Install via pip:

```
pip install pillow numpy pyinstaller
```

Full requirements.txt:
```
Pillow>=10.0.0
numpy>=1.24.0
pyinstaller>=6.0.0
```

---

## Project Structure

```
drawing_app/
├── main.py           # Entry point + resource_path helper
├── app.py            # UI: menus, topbar, sidebar, statusbar
├── canvas_engine.py  # Dual-layer PIL/Tkinter canvas system
├── tool_engine.py    # Modular tools: brush, eraser, shapes, warp, fill
├── drawforge.spec    # PyInstaller bundle spec
└── README.md         # This file
```

---

## Running in Development

```bash
python main.py
```

---

## Building a Standalone EXE (Windows)

### Option 1 — using the .spec file (recommended):
```bash
pyinstaller drawforge.spec
```

### Option 2 — one-liner command:
```bash
pyinstaller --onefile --windowed --name DrawForge \
  --hidden-import PIL \
  --hidden-import PIL.Image \
  --hidden-import PIL.ImageDraw \
  --hidden-import PIL.ImageTk \
  --hidden-import numpy \
  --hidden-import canvas_engine \
  --hidden-import tool_engine \
  --hidden-import app \
  main.py
```

### Option 3 — with a custom icon:
```bash
pyinstaller drawforge.spec --icon=assets/icon.ico
```
(Edit drawforge.spec to uncomment the icon line first.)

The finished EXE will be at:  `dist/DrawForge.exe`

---

## Adding a New Tool

1. Open `tool_engine.py`
2. Subclass `BaseTool` and implement `on_press`, `on_drag`, `on_release`
3. Add your class to `TOOL_REGISTRY`
4. Add a `(label, tool_name)` tuple to `TOOL_DEFS` in `app.py`

That's it — no other files need to change.

---

## Notes

- The `resource_path()` function in `main.py` handles PyInstaller's
  `sys._MEIPASS` temp directory automatically.
- All PIL drawing is done in RGBA mode for alpha compositing.
- The warp tool uses NumPy for pixel-level manipulation.
- Mouse drag events are throttled (minimum 2px movement) to avoid lag.
