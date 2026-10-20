# -*- coding: utf-8 -*-
"""Standalone Gate09 entry point for the locally authored fern model."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Fern_Cliffside", "--gate", "Gate09"]
runpy.run_path(str(engine), run_name="__main__")
