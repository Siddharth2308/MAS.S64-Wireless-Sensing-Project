# YCB material labels: checklist (for Ivan)

File: `ycb_materials.csv`, one row per part. 72 objects (same IDs as mmRender's `generate_data/objs/ycb.csv`), 104 parts.
Drafted by Claude from object type, validated by Siddharth against real YCB photos (Nov 20).

## What's in it
- 24 multi-material objects; 17 of them mix metal with non-metal (cans with plastic lids, cutlery, skillet, drill, scissors, screwdrivers, hammer, clamps, timer).
- 6 all-metal objects (soup/tuna/meat cans, padlock, key, wrench).
- Materials used: plastic_solid 30, plastic_thin 26, steel 24, cardboard 5, glass 4, wood 4, rubber 4, foam 2, leather 2, fabric 1, aluminium 1, ceramic 1.

## Before using it
- [ ] `wall_mm` is not always a number: `solid` (22 rows) means a solid part. Parse it as a string.
- [ ] `wall_mm` is estimated, not measured. It only matters for non-metals. Metal reflects fully at 77 GHz at any thickness here.
- [ ] `area_share` is a rough share of the outer surface; it should add to 1 per object. Blank on 027 skillet (lid, lid handle) and 070 wood blocks (container).
- [ ] Parts are named, not located: the CSV says "fork: steel upper 40%, plastic lower 60%", but not which mesh vertices those are. Decide how to assign them in mmRender (manual split per mesh, or area-weighted per object as a first pass).
- [ ] Hidden parts: some rows are inside the object (drill motor and battery, steel spring in the windex sprayer, timer mechanism). Decide whether mmRender should include them.

## Known doubts in the labels
- [ ] 024 bowl, 025 mug, 029 plate are one matching set but labelled plastic / plastic / ceramic. They may be enamel steel (radar would see metal). Pick one for all three.
- [ ] 028 skillet_lid has no YCB photos; labelled from 027's photos (same lid).
- [ ] `contents` mostly "unknown if present" (are YCB boxes/bottles empty?). Liquid behind thin plastic would reflect strongly.
- [ ] Some `note` fields still say "check" after validation; the material column is the validated value.
- [ ] `category`: 55 from mmRender's `utils/ycb_obj_angles.csv`, 17 filled in by us.

## Reflectivity values (next step, not in this CSV)
- Measured (DCA1000 E5, vs aluminium, straight-on, 5 re-placements): 3 mm glass -11.9 ± 2.2 dB, 3 mm acrylic -6.7 ± 1.7, 3 mm epoxy glass -6.7 ± 1.6, 6 mm glass -8.0 ± 1.0, 7 mm acrylic -21.9 ± 3.9.
- Thickness matters as much as material, so reflectivity should depend on `material` + `wall_mm`.
- Other materials (cardboard, wood, rubber, ...) need model estimates. Planned: `material_reflectivity.csv`.

## For the mmRender plan (staff asked for tasks / outcome / metrics)
- Task: per-point reflectivity weight from these labels (mmRender currently weights all points equally).
- Expected: plastic/glass parts render weaker than metal (up to ~15 dB in E5).
- Metric: rendered vs real (MITO) radar images of the same objects, before vs after; later, reconstruction recall/precision on the 24 multi-material objects.
