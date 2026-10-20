# -*- coding: utf-8 -*-
"""Standalone Gate14 entry point for the locally authored tideworn basalt slab."""
from pathlib import Path
import runpy
import sys

engine = Path(__file__).with_name("LocalNatureModelGenerator.py").resolve()
sys.argv = [str(engine), "--asset", "Basalt_TidewornSlab", "--gate", "Gate14"]
runpy.run_path(str(engine), run_name="__main__")
