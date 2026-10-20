# -*- coding: utf-8 -*-
"""Standalone Gate15 entry point for the locally authored basalt rock cluster."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Basalt_RockCluster", "--gate", "Gate15"]
runpy.run_path(str(engine), run_name="__main__")
