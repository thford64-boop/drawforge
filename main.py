"""
DrawForge - Professional Drawing Application
Entry point for the application.
"""

import sys
import os
from app import DrawForgeApp


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource. Works for development and PyInstaller.
    PyInstaller stores temp files in sys._MEIPASS during runtime.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    app = DrawForgeApp(resource_path)
    app.run()
