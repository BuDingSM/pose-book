#!/usr/bin/env python3
"""Export pose-data.db to one JSON file per category.

Usage: python3 export_per_type.py pose-data.db out_dir
Each file is a plain JSON array of items in the same shape the
frontend already understands, filtered to one type:
  [{ id, type, name, names{en,ja,ko}, category, series?,
     rating, description,
     variants: { view: { layer: { size: path } } } }, ...]
`series` appears only on poses (other types omit the key).
Also writes index.json: [{type, count, file}] so the frontend
can lazy-load only the category the user opens, instead of
downloading the whole 1051-item catalog up front.
"""
import json
import sqlite3
import sys
from pathlib import Path

db_path, out_dir = sys.argv[1], sys.argv[2]
out = Path(out_dir)
out.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row

index = []
for row in con.execute("SELECT DISTINCT type FROM items ORDER BY type"):
    t = row["type"]
    items = []
    for it in con.execute("SELECT * FROM items WHERE type = ? ORDER BY source, id", (t,)):
        item = {
            "id": it["id"],
            "type": it["type"],
            "name": it["name_zh"],
            "names": {"en": it["name_en"], "ja": it["name_ja"], "ko": it["name_ko"]},
            "category": it["category"],
        }
        if it["series"]:
            item["series"] = it["series"]
        item["rating"] = it["rating"]
        item["description"] = it["description"]
        # Match the committed catalogs: character always carries source,
        # costume carries it only for non-shisei (anime) items.
        if t == "character" or it["source"] != "shisei":
            item["source"] = it["source"]
        item["variants"] = {}
        for a in con.execute(
            "SELECT view, layer, size, path FROM assets WHERE item_id = ?"
            " ORDER BY view, layer, size",
            (it["id"],),
        ):
            item["variants"].setdefault(a["view"], {}).setdefault(a["layer"], {})[a["size"]] = a["path"]
        items.append(item)
    path = out / f"{t}.json"
    path.write_text(json.dumps(items, ensure_ascii=False, indent=1))
    rc = dict(con.execute("SELECT rating, COUNT(*) FROM items WHERE type = ? GROUP BY rating", (t,)).fetchall())
    index.append({"type": t, "count": len(items), "general": rc.get("general", 0), "suggestive": rc.get("suggestive", 0), "file": f"{t}.json"})
    print(f"{t}.json: {len(items)} items, {path.stat().st_size} bytes")

(out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
print("index.json:", index)
print("total:", sum(x["count"] for x in index))
