# -*- coding: utf-8 -*-
"""Standalone Gate13 entry point for the locally authored basalt boulder B."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Basalt_Boulder_B", "--gate", "Gate13"]
runpy.run_path(str(engine), run_name="__main__")
