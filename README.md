# Pose-book data

Source: Shisei (CC0). SQLite (pose-data.db) is the source of truth
for item/asset associations; catalog/*.json are exported snapshots,
one file per category, for the static site.

Layout:
  pose-data.db          # items + assets tables (see schema.sql)
  schema.sql            # table definitions and the UI rule
  build_db.py           # catalog.json -> pose-data.db
  export_per_type.py    # pose-data.db -> catalog/<type>.json + index.json
  catalog/              # pose/costume/scene/furniture/prop/light/animal.json, index.json
  assets/               # 10913 webp files, paths match catalog JSON paths

The static site does not read SQLite directly: it loads
catalog/<type>.json. Paid generation (later) is the only backend
piece; user-key generation stays in the browser.
