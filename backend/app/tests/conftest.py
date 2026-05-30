"""Make the app modules importable as top-level (matches runtime layout).

In the container the app is copied flat into /app and modules import each
other as `from game_analysis import ...`. Tests run from backend/app, so we
add the app directory (this file's parent's parent) to sys.path.
"""
import os
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)