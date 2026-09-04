# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _aiplen_build import build
EDITS = json.load(open(sys.argv[1], encoding="utf-8"))
EDITS = {k: [tuple(x) for x in v] for k, v in EDITS.items()}
build(EDITS, sys.argv[2])
