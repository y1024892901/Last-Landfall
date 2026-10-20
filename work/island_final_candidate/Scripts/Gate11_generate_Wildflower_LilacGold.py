# -*- coding: utf-8 -*-
"""Standalone Gate11 entry point for the locally authored lilac-gold flowers."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Wildflower_LilacGold", "--gate", "Gate11"]
runpy.run_path(str(engine), run_name="__main__")
