#!/usr/bin/env python3
"""Build pose-data.db from a pose-book catalog.json.

Usage: python3 build_db.py catalog.json pose-data.db
The catalog is the import script's output: items with
variants[view][layer][size] = path. This script flattens it into
the items/assets tables in schema.sql, so SQLite becomes the
source of truth and catalog.json can be re-exported from it.
"""
import json
import sqlite3
import sys
from pathlib import Path

catalog_path, db_path = sys.argv[1], sys.argv[2]
catalog = json.loads(Path(catalog_path).read_text())
schema = Path(__file__).with_name("schema.sql").read_text()

db = Path(db_path)
if db.exists():
    db.unlink()
con = sqlite3.connect(db_path)
con.executescript(schema)
for item in catalog:
    names = item.get("names") or {}
    con.execute(
        "INSERT INTO items (id, type, name_zh, name_en, name_ja, name_ko,"
        " category, series, rating, description, source)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'shisei')",
        (item["id"], item["type"], item.get("name"), names.get("en"),
         names.get("ja"), names.get("ko"), item.get("category"),
         item.get("series"), item.get("rating", "general"),
         item.get("description", "")),
    )
    for view, layers in (item.get("variants") or {}).items():
        for layer, sizes in layers.items():
            for size, path in sizes.items():
                con.execute(
                    "INSERT INTO assets (item_id, view, layer, size, path)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (item["id"], view, layer, size, path),
                )
con.commit()
print("items:", con.execute("SELECT COUNT(*) FROM items").fetchone()[0])
print("assets:", con.execute("SELECT COUNT(*) FROM assets").fetchone()[0])
print("by type:", con.execute(
    "SELECT type, COUNT(*) FROM items GROUP BY type ORDER BY type"
).fetchall())
print("single view+layer items:", con.execute(
    "SELECT COUNT(*) FROM (SELECT item_id FROM assets"
    " GROUP BY item_id, view, layer HAVING COUNT(*) >= 1)"
    " WHERE item_id IN (SELECT item_id FROM (SELECT item_id, COUNT(DISTINCT view || '/' || layer) AS n"
    " FROM assets GROUP BY item_id) WHERE n = 1)"
).fetchone()[0])
con.close()
