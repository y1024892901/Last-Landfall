# -*- coding: utf-8 -*-
"""Standalone Gate12 entry point for the locally authored basalt boulder A."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Basalt_Boulder_A", "--gate", "Gate12"]
runpy.run_path(str(engine), run_name="__main__")
