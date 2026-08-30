#!/usr/bin/env python3
from pathlib import Path
import argparse
import json

from memory_os.chatgpt_importer import import_chatgpt
from memory_os.sqlite_store import build_sqlite

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
canonical = args.output / "canonical"
manifest = import_chatgpt(args.source, canonical)
build_sqlite(canonical, args.output / "memory.sqlite")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
print(f"SQLite: {args.output / 'memory.sqlite'}")
