// Progress Report 2 deck skeleton: figures placed, short grey prompts for Siddharth to replace.
//   cd presentation && node build_deck.js        (after prep_assets.py)
// Output: progress_report_2.pptx (import into Google Slides: File > Import slides).
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const SKILL = "C:/Users/siddh/.claude/skills/synced/3c8798ef-c310-41d1-8ed4-1d7026fdc7a8_92245bf0-52fb-4337-9f80-20eefe34f295/pptx/scripts/apply_theme.js";
const { applyTheme } = require(SKILL);

const A = path.join(__dirname, "assets");
const SIZES = JSON.parse(fs.readFileSync(path.join(A, "sizes.json"), "utf8"));
const OUT = path.join(__dirname, "progress_report_2.pptx");

const THEME = {
  name: "MAS.S64 Radar",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "1F2A33", lt1: "FFFFFF", dk2: "55636C", lt2: "F2F4F5",
    accent1: "C2410C", accent2: "1F6FB2", accent3: "55636C", accent4: "2E8B57",
    accent5: "8A949B", accent6: "D9DEE2", hlink: "1F6FB2", folHlink: "55636C",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                 // 13.333 x 7.5 in
pres.theme = { headFontFace: "Arial", bodyFontFace: "Arial" };
pres.title = "Progress Report 2";
pres.author = "Siddharth Kulkarni, Ivan Wren";
const C = pres.SchemeColor;
const W = 13.333, M = 0.6;                   // slide width, side margin
const TOP = 1.55, BOT = 6.85;                // content area

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: M, y: 0.32, w: 9, h: 0.32, fontSize: 12,
        bold: true, color: C.accent1, charSpacing: 1, margin: 0, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.62, w: W - 2 * M, h: 0.8, fontSize: 30,
        bold: true, color: C.text1, margin: 0, valign: "top", align: "left" }, text: "" } },
    { text: { text: "MAS.S64 · Progress Report 2", options: { x: M, y: 7.05, w: 5, h: 0.3, fontSize: 10,
        color: C.text2, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: HEX.dk2, align: "right" },
});
pres.defineSlideMaster({ title: "TITLE", background: { color: "FFFFFF" }, objects: [] });

// ---------- helpers ----------
function img(slide, name, x, y, w, h, align = "center", valign = "top") {
  const [pw, ph] = SIZES[name];
  const r = pw / ph;
  let iw = w, ih = w / r;
  if (ih > h) { ih = h; iw = h * r; }
  const ix = align === "left" ? x : align === "right" ? x + w - iw : x + (w - iw) / 2;
  const iy = valign === "top" ? y : valign === "bottom" ? y + h - ih : y + (h - ih) / 2;
  slide.addImage({ path: path.join(A, name), x: ix, y: iy, w: iw, h: ih, altText: name, objectName: name });
  return { x: ix, y: iy, w: iw, h: ih };
}
function caption(slide, text, box, opts = {}) {
  slide.addText(text, { x: box.x, y: box.y + box.h + 0.06, w: box.w, h: 0.3, fontSize: 11, color: C.text2,
    margin: 0, isTextBox: true, align: opts.align || "left", ...opts });
}
// grey 1-2 word prompts that Siddharth replaces with his own text
function prompts(slide, items, x, y, w, h, size = 16) {
  slide.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
    { x, y, w, h, fontSize: size, color: C.accent5, paraSpaceAfter: 10, valign: "top", margin: 0.05,
      isTextBox: true, objectName: "prompts" });
}
// row of single prompts side by side (for slides where figures take the full width)
function promptRow(slide, items, x, y, w) {
  const cw = w / items.length;
  items.forEach((t, i) => prompts(slide, [t], x + i * cw, y, cw - 0.2, 0.45, 15));
}
// place an image by height (for rows of photos with equal height); returns its box
function imgH(slide, name, x, y, h) {
  const [pw, ph] = SIZES[name];
  const w = h * pw / ph;
  slide.addImage({ path: path.join(A, name), x, y, w, h, altText: name, objectName: name });
  return { x, y, w, h };
}
function stat(slide, big, label, x, y, w, color = C.accent1) {
  slide.addText(big, { x, y, w, h: 0.75, fontSize: 36, bold: true, color, margin: 0, isTextBox: true });
  slide.addText(label, { x, y: y + 0.75, w, h: 0.5, fontSize: 13, color: C.text2, margin: 0, valign: "top",
    isTextBox: true });
}
function card(slide, x, y, w, h) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 },
    line: { color: C.background2 } });
}
function content(section, eyebrow, title) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(eyebrow, { placeholder: "eyebrow" });
  s.addText(title, { placeholder: "title" });
  return s;
}
function flow(slide, steps, x, y, w, h) {
  const gap = 0.35, bw = (w - gap * (steps.length - 1)) / steps.length;
  steps.forEach((t, i) => {
    const bx = x + i * (bw + gap);
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y, w: bw, h, rectRadius: 0.06,
      fill: { color: C.background2 }, line: { color: C.accent6 } });
    slide.addText(t, { x: bx, y, w: bw, h, fontSize: 13, color: C.text1, align: "center", valign: "middle",
      margin: 0.05, isTextBox: true });
    if (i < steps.length - 1)
      slide.addShape(pres.shapes.RIGHT_TRIANGLE, { x: bx + bw + 0.11, y: y + h / 2 - 0.09, w: 0.13, h: 0.18,
        rotate: 90, fill: { color: C.accent5 }, line: { color: C.accent5 } });
  });
}

// ---------- 1. title ----------
pres.addSection({ title: "Intro" });
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Intro" });
  s.addText("MAS.S64 · PROGRESS REPORT 2", { x: M, y: 2.0, w: 7, h: 0.35, fontSize: 13, bold: true,
    color: C.accent1, charSpacing: 1, margin: 0, isTextBox: true });
  s.addText("Material-Aware\nWave-Former", { x: M, y: 2.45, w: 7.4, h: 1.5, fontSize: 40, bold: true,
    color: C.text1, margin: 0, valign: "top", isTextBox: true });
  s.addText("Reflectivity measurements and per-part material labels", { x: M, y: 3.95, w: 7, h: 0.5,
    fontSize: 18, color: C.text2, margin: 0, isTextBox: true });
  s.addText("Siddharth Kulkarni · Ivan Wren  |  Nov 20, 2026", { x: M, y: 4.75, w: 7, h: 0.4, fontSize: 14,
    color: C.text2, margin: 0, isTextBox: true });
  img(s, "s2_stack.jpg", 8.4, 0.6, 4.33, 6.3, "right", "middle");
}

// ---------- 2. proposal ----------
pres.addSection({ title: "Proposal" });
{
  const s = content("Proposal", "RECAP · PROPOSAL", "Per-part materials in synthetic training data");
  const b = img(s, "pipeline.png", M, TOP + 0.1, 8.3, 4.6, "left");
  caption(s, "Tags A = per-part materials, B = orientation (Proposal B). wf_sim: our simplified model, not Wave-Former's simulator.", b, { h: 0.5 });
  prompts(s, ["Idea", "Why reflectivity", "Proposal B (tag B)"], 9.4, TOP + 0.2, 3.3, 3.5);
}

// ---------- 3. simulation recap ----------
{
  const s = content("Proposal", "RECAP · SIMULATION", "What our simplified model predicted");
  const a = img(s, "jar_partials.png", M, TOP, 5.2, 4.9, "left");
  caption(s, "Lidded jar: visible points by material model", a);
  const b = img(s, "fresnel.png", 6.1, TOP, 4.7, 3.9, "left");
  caption(s, "Fresnel reflectivity, approx. εr", b);
  prompts(s, ["Prediction", "Assumption"], 11.0, TOP + 0.1, 1.8, 3);
}

// ---------- 4. stage 1 setup ----------
pres.addSection({ title: "Stage 1" });
{
  const s = content("Stage 1", "STAGE 1 · ON-CHIP RADAR (OCT 30)", "First experiments");
  prompts(s, ["Radar", "Tests", "Readout"], M, TOP + 0.1, 1.7, 3);
  const y = TOP + 0.55, h = 3.4, g = 0.3;
  const p1 = imgH(s, "s1_radar.jpg", 2.5, y, h);
  caption(s, "IWR1443BOOST", p1);
  const p2 = imgH(s, "s1_distance.jpg", p1.x + p1.w + g, y, h);
  caption(s, "Distance test", p2);
  const p3 = imgH(s, "s1_transmission.jpg", p2.x + p2.w + g, y, h);
  caption(s, "Sheet in front of plate", p3);
}

// ---------- 5. stage 1 results ----------
{
  const s = content("Stage 1", "STAGE 1 · RESULTS", "Reflection and transmission, on-chip");
  const a = img(s, "iwr_validation.png", M, TOP, 7.9, 4.95, "left");
  caption(s, "One sample each, no repeats, on-chip dB", a);
  const b = img(s, "s1_sheets.jpg", 9.0, TOP, 3.7, 2.9, "left");
  caption(s, "Sheets: glass, plastic, aluminium", b);
  prompts(s, ["Reflection", "Transmission"], 9.0, TOP + 3.45, 3.7, 1.6);
}

// ---------- 6. conclusions to revisit ----------
{
  const s = content("Stage 1", "STAGE 1 · WHAT WE CONCLUDED", "Conclusions we had to revisit");
  const items = [
    ["0.3 dB", "plastic vs glass → \"glass ≈ plastic\""],
    ["139 dB", "same level from 40 to 120 cm"],
    ["18 → 7 dB", "back-off barely moved the reading"],
  ];
  const cw = 3.8, gap = 0.37, y = TOP + 0.1, ch = 3.6;
  items.forEach(([big, lab], i) => {
    const x = M + i * (cw + gap);
    card(s, x, y, cw, ch);
    stat(s, big, lab, x + 0.3, y + 0.3, cw - 0.6);
    prompts(s, ["Why it misled us"], x + 0.3, y + 1.8, cw - 0.6, 1.4);
  });
  prompts(s, ["Staff feedback", "What we changed"], M, y + ch + 0.35, 12, 1.2);
}

// ---------- 7. new experiment design ----------
pres.addSection({ title: "Stage 2" });
{
  const s = content("Stage 2", "STAGE 2 · RAW ADC CAPTURE (NOV 19)", "New experiment design");
  const p = img(s, "s2_stack.jpg", M, TOP, 3.6, 5.0, "left");
  caption(s, "IWR1443 + DCA1000", p);
  const x = p.x + p.w + 0.45, w = W - M - x;
  flow(s, ["Radar\n77–81 GHz", "DCA1000\nraw ADC", "Ethernet\nUDP", "Python\nrange FFT"], x, TOP, w, 0.85);
  const b = img(s, "studio_postproc.png", x, TOP + 1.2, w, 2.4, "left");
  caption(s, "mmWave Studio cross-check of the first raw capture", b);
  prompts(s, ["Why raw data", "Repeats", "Controls"], x, b.y + b.h + 0.5, w, 1.4);
}

// ---------- 8. five experiments overview ----------
{
  const s = content("Stage 2", "STAGE 2 · PLAN", "Six checks, E0 to E5");
  const hdr = { bold: true, color: HEX.dk2, fontSize: 13, fill: { color: HEX.lt2 } };
  const rows = [
    [{ text: "Exp", options: hdr }, { text: "Setup", options: hdr }, { text: "Checks", options: hdr }],
    ["E0", "Empty scene", "Background"],
    ["E1", "Plate 40 vs 60 cm", "Range, level"],
    ["E2", "60 s still", "Phase stability"],
    ["E3", "Move ~1 mm", "Phase tracks motion"],
    ["E4", "TX back-off 0–18 dB", "Linearity, dB scale"],
    ["E5", "7 samples × 5 placements", "Material reflectivity"],
  ];
  s.addTable(rows, { x: M, y: TOP + 0.05, w: 7.4, colW: [0.9, 3.3, 3.2], fontSize: 14, color: HEX.dk1,
    rowH: 0.52, border: { type: "solid", pt: 0.75, color: HEX.accent6 }, valign: "middle", margin: 0.08 });
  const a = img(s, "s2_layout.jpg", 8.5, TOP, 4.23, 3.4, "left");
  caption(s, "Radar and tape at 40 / 60 cm", a);
  prompts(s, ["Order", "Pass rule"], 8.5, a.y + a.h + 0.55, 4.23, 1.2);
}

// ---------- 9. E0 + E1 ----------
{
  const s = content("Stage 2", "STAGE 2 · E0 + E1", "Empty scene and distance");
  const a = img(s, "e0_plate_vs_empty.png", M, TOP, 5.9, 3.1, "left");
  caption(s, "E0: plate vs empty scene", a);
  const b = img(s, "e1_40_vs_60.png", 6.83, TOP, 5.9, 3.1, "left");
  caption(s, "E1: plate at 40 and 60 cm", b);
  const y = a.y + a.h + 0.55;
  stat(s, "38 dB", "plate above background", M, y, 3.0);
  stat(s, "+7.2 cm", "range offset, constant", 6.83, y, 3.0);
  stat(s, "≈ flat", "level 40 → 60 cm", 9.9, y, 2.8);
  prompts(s, ["E0 meaning"], M, y + 1.3, 5.9, 0.45, 15);
  prompts(s, ["E1 meaning"], 6.83, y + 1.3, 5.9, 0.45, 15);
}

// ---------- 10. E2 + E3 ----------
{
  const s = content("Stage 2", "STAGE 2 · E2 + E3", "Phase is stable and tracks motion");
  const a = img(s, "e2_still.png", M, TOP, 5.2, 5.0, "left");
  caption(s, "E2: plate still for 60 s", a);
  const x = a.x + a.w + 0.8;
  stat(s, "0.18°", "phase sd over 60 s (0.9 µm)", x, TOP + 0.2, 5);
  stat(s, "0.91 mm", "E3: measured for a ~1 mm move", x, TOP + 1.7, 5);
  prompts(s, ["Why it matters (SAR)"], x, TOP + 3.3, 5, 1.2);
}

// ---------- 11. E4 ----------
{
  const s = content("Stage 2", "STAGE 2 · E4", "Power back-off: raw data is linear");
  const a = img(s, "e4_backoff.png", M, TOP, 7.3, 4.9, "left");
  caption(s, "Plate peak vs TX back-off (raw DCA data)", a);
  const x = a.x + a.w + 0.6, w = W - M - x;
  stat(s, "−6.5 dB", "per 6 dB step, 0–12 dB", x, TOP + 0.1, w);
  stat(s, "−9 dB", "extra drop at 18 dB", x, TOP + 1.5, w);
  stat(s, "bo6", "chosen for E5", x, TOP + 2.9, w, C.text1);
  prompts(s, ["On-chip vs raw"], x, TOP + 4.3, w, 0.8);
}

// ---------- 12. E5 design ----------
{
  const s = content("Stage 2", "STAGE 2 · E5 DESIGN", "Seven samples, five placements each");
  const names = ["s2_alu_sq.jpg", "s2_glass_sq.jpg", "s2_acrylic_sq.jpg", "s2_white_sq.jpg"];
  const gw = 2.4, gap = 0.2;
  names.forEach((n, i) => {
    const x = M + (i % 2) * (gw + gap), y = TOP + Math.floor(i / 2) * (gw + gap);
    s.addImage({ path: path.join(A, n), x, y, w: gw, h: gw, altText: n, objectName: n });
  });
  s.addText("Samples at 40 cm against a fixed stop", { x: M, y: TOP + 2 * gw + gap + 0.08, w: 2 * gw + gap, h: 0.3,
    fontSize: 11, color: C.text2, margin: 0, isTextBox: true });
  const x = M + 2 * gw + gap + 0.6, w = W - M - x;
  const hdr = { bold: true, color: HEX.dk2, fontSize: 13, fill: { color: HEX.lt2 } };
  s.addTable([
    [{ text: "Sample", options: hdr }, { text: "Thickness", options: hdr }],
    ["Aluminium (ref.)", "6 mm"], ["Aluminium, 90°", "control"], ["Glass", "3, 6 mm"],
    ["Acrylic", "3, 7 mm"], ["Epoxy glass", "3 mm"],
  ], { x, y: TOP + 0.05, w, colW: [w * 0.6, w * 0.4], fontSize: 14, color: HEX.dk1, rowH: 0.45,
    border: { type: "solid", pt: 0.75, color: HEX.accent6 }, valign: "middle", margin: 0.08 });
  prompts(s, ["Placement", "Settings", "Pass rule"], x, TOP + 3.1, w, 1.9);
}

// ---------- 13. E5 results ----------
{
  const s = content("Stage 2", "STAGE 2 · E5 RESULTS", "Reflection depends on material and thickness");
  const a = img(s, "e5_levels.png", M, TOP, 6.9, 4.1, "left");
  caption(s, "Each dot = one placement; bar = mean ± sd", a);
  const b = img(s, "e5_curves.png", 7.75, TOP, 4.98, 4.1, "left");
  caption(s, "Level across 78–80.4 GHz (mean ± sd)", b);
  promptRow(s, ["Glass vs acrylic", "Thickness", "Control"], M, a.y + a.h + 0.55, W - 2 * M);
}

// ---------- 14. E5 takeaways ----------
{
  const s = content("Stage 2", "STAGE 2 · E5 TAKEAWAYS", "Which pairs can we tell apart?");
  const hdr = { bold: true, color: HEX.dk2, fontSize: 13, fill: { color: HEX.lt2 } };
  const yes = { color: HEX.accent4, bold: true }, no = { color: HEX.dk2 };
  const r = (pair, diff, p, one, shape) => [pair, diff, p, { text: one[0], options: one[1] ? yes : no },
    { text: shape[0], options: shape[1] ? yes : no }];
  s.addTable([
    [{ text: "Pair", options: hdr }, { text: "Mean diff", options: hdr }, { text: "Welch p", options: hdr },
     { text: "One capture (level)", options: hdr }, { text: "Shape (post-hoc)", options: hdr }],
    r("Al vs Al 90° (control)", "1.7 dB", "0.11", ["no ✓", false], ["no", false]),
    r("Glass 3 vs acrylic 3", "5.2 dB", "0.004", ["no (2.4)", false], ["yes", true]),
    r("Acrylic 3 vs epoxy 3", "0.0 dB", "0.97", ["no", false], ["no", false]),
    r("Glass 3 vs glass 6", "3.9 dB", "0.012", ["no", false], ["yes", true]),
    r("Acrylic 3 vs acrylic 7", "15.2 dB", "0.0004", ["yes", true], ["no", false]),
    r("Glass 6 vs acrylic 7", "13.9 dB", "0.0009", ["yes", true], ["no", false]),
  ], { x: M, y: TOP + 0.05, w: 8.4, colW: [2.6, 1.2, 1.1, 1.9, 1.6], fontSize: 13, color: HEX.dk1, rowH: 0.5,
    border: { type: "solid", pt: 0.75, color: HEX.accent6 }, valign: "middle", margin: 0.07 });
  s.addText("Separable from one capture = mean difference ≥ 3 × single-capture sd.", { x: M, y: TOP + 3.75,
    w: 8.4, h: 0.3, fontSize: 11, color: C.text2, margin: 0, isTextBox: true });
  const x = 9.6, w = W - M - x;
  stat(s, "5.2 dB", "glass vs acrylic, 3 mm (p = 0.004)", x, TOP + 0.05, w);
  stat(s, "15 dB", "acrylic 3 → 7 mm", x, TOP + 1.5, w);
  stat(s, "± 2 dB", "placement uncertainty", x, TOP + 2.95, w, C.text1);
  prompts(s, ["Answer to staff", "For the simulator"], M, TOP + 4.3, 8.4, 1.0);
}

// ---------- 15. labelling method ----------
pres.addSection({ title: "Labels" });
{
  const s = content("Labels", "MATERIAL LABELS · METHOD", "Per-part labels for 72 YCB objects");
  flow(s, ["Draft from\nobject type", "YCB photos\n4 per object", "Validate\nin UI", "CSV\n104 parts"], M, TOP,
    W - 2 * M, 0.85);
  const a = img(s, "label_ui.png", M, TOP + 1.25, 9.6, 3.9, "left");
  caption(s, "Validation UI: photo + editable parts (027 skillet)", a);
  const x = a.x + a.w + 0.5, w = W - M - x;
  prompts(s, ["Columns", "Sources", "Thickness"], x, TOP + 1.35, w, 2.5);
}

// ---------- 16. labelling results ----------
{
  const s = content("Labels", "MATERIAL LABELS · RESULTS", "One in three objects mixes materials");
  const mats = ["plastic solid", "plastic thin", "steel", "cardboard", "glass", "wood", "rubber", "foam", "leather",
    "fabric", "aluminium", "ceramic"];
  const vals = [30, 26, 24, 5, 4, 4, 4, 2, 2, 1, 1, 1];
  s.addChart(pres.charts.BAR, [{ name: "Parts", labels: mats, values: vals }], {
    x: M, y: TOP - 0.05, w: 6.6, h: 3.3, barDir: "bar", catAxisOrientation: "maxMin",
    chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10,
    dataLabelColor: HEX.dk2, dataLabelFontFace: "+mn-lt", catAxisLabelFontSize: 11, catAxisLabelColor: HEX.dk2,
    catAxisLabelFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" },
    catGridLine: { style: "none" }, showLegend: false, showTitle: true, title: "Parts per material",
    titleFontSize: 12, titleColor: HEX.dk2, titleFontFace: "+mn-lt", barGapWidthPct: 40,
  });
  const sx = 7.7;
  stat(s, "72", "objects", sx, TOP, 2.3, C.text1);
  stat(s, "104", "parts", sx + 2.6, TOP, 2.3, C.text1);
  stat(s, "24", "multi-material", sx, TOP + 1.5, 2.3);
  stat(s, "17", "metal + non-metal", sx + 2.6, TOP + 1.5, 2.3);
  const strip = [["ycb_fork.jpg", "steel + plastic"], ["ycb_skillet.jpg", "Al + glass + plastic"],
    ["ycb_drill.jpg", "plastic + steel"], ["ycb_clamp.jpg", "plastic + spring"], ["ycb_mug.jpg", "plastic or enamel?"]];
  const n = strip.length, gap = 0.2, pw = (W - 2 * M - gap * (n - 1)) / n, py = TOP + 3.45, ph = 1.45;
  strip.forEach(([f, lab], i) => {
    const b = img(s, f, M + i * (pw + gap), py, pw, ph, "center", "top");
    caption(s, lab, { x: M + i * (pw + gap), y: b.y, w: pw, h: b.h });
  });
}

// ---------- 17. mmRender ----------
pres.addSection({ title: "mmRender" });
{
  const s = content("mmRender", "NEXT · MMRENDER (IVAN)", "Testing the labels in mmRender");
  const cols = [["Task", ["Per-point reflectivity", "Label → material → dB"]],
    ["Expected", ["Weaker plastic, glass", "Up to ~15 dB"]],
    ["Metric", ["Render vs MITO", "Recall / precision"]]];
  const cw = 2.55, gap = 0.25, y = TOP + 0.05, ch = 4.95;
  cols.forEach(([head, items], i) => {
    const x = M + i * (cw + gap);
    card(s, x, y, cw, ch);
    s.addText(head, { x: x + 0.25, y: y + 0.25, w: cw - 0.5, h: 0.45, fontSize: 18, bold: true, color: C.accent1,
      margin: 0, isTextBox: true });
    prompts(s, items, x + 0.25, y + 0.9, cw - 0.5, 2.5, 15);
  });
  const fx = M + 3 * (cw + gap) + 0.15, fw = W - M - fx;
  s.addShape(pres.shapes.RECTANGLE, { x: fx, y, w: fw, h: ch, fill: { color: "FFFFFF" },
    line: { color: HEX.accent5, width: 1, dashType: "dash" } });
  s.addText("mmRender output\n(before / after materials)", { x: fx, y, w: fw, h: ch, fontSize: 14, color: C.accent5,
    align: "center", valign: "middle", isTextBox: true });
}

// ---------- 18. next steps ----------
{
  const s = content("mmRender", "WRAP-UP", "Status and next steps");
  const cols = [["Done", ["Stage 2 E0–E5", "Labels, 72 objects"]], ["Next", ["Reflectivity table", "mmRender test"]],
    ["Gaps", ["Calipers", "Reconstruction impact"]]];
  const cw = 2.55, gap = 0.25, y = TOP + 0.05, ch = 4.95;
  cols.forEach(([head, items], i) => {
    const x = M + i * (cw + gap);
    card(s, x, y, cw, ch);
    s.addText(head, { x: x + 0.25, y: y + 0.25, w: cw - 0.5, h: 0.45, fontSize: 18, bold: true,
      color: i === 2 ? C.text2 : C.accent1, margin: 0, isTextBox: true });
    prompts(s, items, x + 0.25, y + 0.9, cw - 0.5, 2.5, 15);
  });
  img(s, "s2_bench.jpg", M + 3 * (cw + gap) + 0.15, y, W - M - (M + 3 * (cw + gap) + 0.15), ch, "center", "top");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
