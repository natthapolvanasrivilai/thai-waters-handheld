# Offline digital model-extrusion guard

Use the actual G-code inside a single native sliced Bambu Studio archive, and its **matching** native `result.json`. Do not give the verifier an editable unsliced archive, earlier report, or independently saved G-code. Retain and cross-check the editable input digest, exact placement/material settings, and the intended object/plate list separately. This tool is read-only and does not run a slicer or connect to a printer.

```sh
python3 tools/verify_model_extrusion.py SLICED.3mf result.json
python3 tools/verify_model_extrusion.py SLICED.3mf result.json --features witnesses.json --height-tolerance-mm 0.12
```

It joins the native report’s placed-object bounds to unique names and instance IDs within each listed plate, tracks positive XY model extrusion per instance, and compares the **bottom and top** deposited model-layer extents with the native placed mesh. Supports, support interfaces/transitions, brim, skirt, purge/tower and other non-model roles are not credited. `--height-tolerance-mm` sets a fixed allowable offset at both ends; otherwise the heuristic of one boundary layer plus 0.03 mm, at least 0.27 mm, allows discretized slicing. Tighten this tolerance where the intended feature or layer height warrants it. This heuristic is not a manufacturing tolerance.

Object-level coverage can pass while an individual flange, pin, ear, wall, or latch is missing. Define separate **independent** local feature witnesses on critical heights selected from checked CAD/print registration and an agreed path requirement, not from a suspect result. Example synthetic witness:

```json
{"features":[
  {"plate":1,"object_id":"101","name":"right tab",
   "reference":"controlled drawing, tab cross-section",
   "xy_mm":[[9.3,11.0],[0.9,1.1]],
   "required_layers_z_mm":[1.0,1.2],
   "minimum_path_mm":0.6}
]}
```

The XY window and the layer-top heights are in G-code machine millimetres. Require at least the specified model centerline length through the **interior** of the XY window on every listed layer. Record the chosen sample heights, registration and minimum independently; multiple narrow windows can guard separate branches. Location and length alone do not measure bead width, connectedness, first-layer stability, local fill, exact support/removability, bore clearance or material behavior. Those need the independent native toolpath and fit checks in the [slicer skill](../.agents/skills/fdm-slicer-dfm/SKILL.md).

- Exit **0**: scoped digital extents/path checks pass for the reported plate entries only.
- Exit **1**: a native warning or model-height/local-path requirement fails.
- Exit **2**: malformed or unsupported evidence, ambiguous identity, unknown deposition role, unsupported motion, or missing registered object/plate. Do not waive the condition or assume pass. Use a validated exporter/version/alternative observation.

Supported dialect: Bambu Studio’s annotated mm G-code, stable `; OBJECT_ID:`, `; FEATURE:`, and layer markers, G0/G1, XY I/J-centered G2/G3, and explicit M82/M83. G-code without compatible metadata needs a separate parser. Only the listed plates can be checked; separately verify all intended plates were included, physical spool/bed, native reopen, and as-printed status. Do not attach proprietary inputs to public reports.
