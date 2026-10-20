# -*- coding: utf-8 -*-
"""Standalone Gate16 entry point for the locally authored salt-broken driftwood."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Driftwood_BrokenSaltLog", "--gate", "Gate16"]
runpy.run_path(str(engine), run_name="__main__")
