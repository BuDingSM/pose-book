-- Pose-book data model: one SQLite file manages the association
-- between items and their image files. Views, layers and sizes are
-- attributes of an asset row, not separate tables, so the UI can ask
-- "which attributes does THIS item actually have?" instead of
-- assuming every item has every view.
--
-- items: one row per material (pose, costume, scene, furniture,
--   prop, light, animal). id is globally unique by prefix
--   (P/C/E/T/F/L/A) and is the stable public id.
-- assets: one row per physical file. A pose front/line/w900 and the
--   same view's w300 thumbnail are two rows for the same view+layer;
--   a single-image item has exactly one view+layer combination
--   (usually two rows: w300 + w900 of that one image).
CREATE TABLE IF NOT EXISTS items (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL,          -- pose | costume | scene | furniture | prop | light | animal
    name_zh     TEXT,
    name_en     TEXT,
    name_ja     TEXT,
    name_ko     TEXT,
    category    TEXT,                   -- e.g. 坐姿, 中国历代, 居家, 单椅
    series      TEXT,                   -- pose only: std | upper | sexy | duo, else NULL
    rating      TEXT NOT NULL DEFAULT 'general',  -- general | suggestive
    description TEXT,                   -- English prompt description
    source      TEXT NOT NULL DEFAULT 'shisei'    -- shisei (CC0) for v1
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id  TEXT NOT NULL REFERENCES items(id),
    view     TEXT NOT NULL,  -- front | diag | side | back | above | below | eye
    layer    TEXT NOT NULL,  -- line | clay | depth | normal | photo | image
    size     TEXT NOT NULL,  -- w300 | w900  (width tier; height follows the source)
    path     TEXT NOT NULL UNIQUE,  -- repo-relative, e.g. assets/line/w900/std_P001_front.webp
    format   TEXT NOT NULL DEFAULT 'webp'
);
CREATE INDEX IF NOT EXISTS idx_assets_item ON assets(item_id);
CREATE INDEX IF NOT EXISTS idx_assets_item_view_layer ON assets(item_id, view, layer);

-- UI rule, in SQL terms:
--   SELECT view, layer FROM assets WHERE item_id = ? GROUP BY view, layer;
-- If that returns exactly 1 row, the item is a single image: show it
-- (prefer w900, fall back to w300) with no view/layer switcher.
-- Otherwise show only the views/layers that query actually returns.
