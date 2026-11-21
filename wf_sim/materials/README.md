# YCB material labels

Per-part material labels for the 72 YCB objects in mmRender's object list (`mmRender/clean_code/generate_data/objs/ycb.csv`).
Drafted by Claude from object type, then validated by hand against real YCB photos (Nov 20).

## Files
| File | What |
|---|---|
| `ycb_materials.csv` | The labels: 72 objects, 104 parts, all `validated=yes` |
| `ycb_materials_draft.csv` | Claude's draft before validation (for comparison) |
| `ycb_materials_backup_before028.csv` | Backup from before 028 skillet_lid was filled in |
| `label_ui.py` | Tkinter UI: photo + editable parts, "OK, next" saves and moves on |
| `fetch_photos.py` | Downloads 4 photos per object from the official YCB server into `photos/` (git-ignored) |

## Run
From `wf_sim`, with `.venv-win` active (needs Pillow):
```powershell
python materials\fetch_photos.py     # once, ~2.5 min, ~18 MB; re-run resumes
python materials\label_ui.py
```
- Photos: < > or Alt+Left/Right. OK: Ctrl+Enter. OK warns if area_share is blank or doesn't add to 1.
- Don't edit the CSV while the UI is open: the next OK rewrites the whole file from the UI's copy.

## Columns: where they come from
| Column | Source |
|---|---|
| `id`, `object` | mmRender's YCB list (official YCB numbers and names) |
| `category` | mmRender's `utils/ycb_obj_angles.csv` for 55 objects; 17 filled in by us (blank or missing there) |
| `part`, `material`, `wall_mm`, `area_share`, `contents`, `confidence`, `note` | Ours. Drafted from object type, validated from photos. YCB publishes no material labels. |
| `validated` | Set by the UI |

- `wall_mm`: wall thickness of that part (`solid` = solid part). Estimated, not measured. Only matters for non-metals: at 77 GHz any metal thicker than ~1 µm reflects fully.
- `area_share`: rough share of the object's outer surface; should add to 1 per object.

## Photo source
- Server: `http://ycb-benchmarks.s3-website-us-east-1.amazonaws.com/data/` (`objects.json`, per-object archives).
- The high-res archive is ~1.6 GB per object; the script streams it and stops after 4 photos (random cameras/angles).
- 028 skillet_lid has no photos on the server (only a texture atlas). It's the same lid as on 027 skillet; labelled from 027's photos.
- Server quirk: `objects.json` says `027-skillet`, archives use `027_skillet`.

## Open
- Blank area_share: 027 skillet (cap, second handle), 070 wood blocks (container).
- 024 bowl, 025 mug, 029 plate are one matching set but labelled plastic / plastic / ceramic. Could be enamel steel or plastic; photos can't tell. Pick one for all three.
- Some notes still say "check" after validation (e.g. banana, apple, bowl, mug, clamps, timer, 002 lid).
- Next: `material_reflectivity.csv` (E5 measured values + model estimates) to map labels to reflectivity for mmRender.
