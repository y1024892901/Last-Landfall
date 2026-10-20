# -*- coding: utf-8 -*-
"""Standalone Gate10 entry point for the locally authored coral-cream flowers."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Wildflower_CoralCream", "--gate", "Gate10"]
runpy.run_path(str(engine), run_name="__main__")
