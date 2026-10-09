// The DGLRM talk deck, From Bed Rest to Mars: co-author placeholders, technical half and backup slides.
// Numbers from results/ on feat/report; the example on slide 3 is the cached answer for the
// row the report's own example figure uses (median LLM error).
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
// applyTheme comes from the pptx skill used to build this deck; set APPLY_THEME to its path.
const { applyTheme } = require(process.env.APPLY_THEME || "./apply_theme.js");

const OUT = process.argv[2] || "bed-rest-to-mars-talk.pptx";
const EX = JSON.parse(fs.readFileSync(path.join(__dirname, "example.json"), "utf8"));
const LOGO = path.join(__dirname, "dglrm_logo_schrift2_ret.png"); // 558 x 150 px
const LOGO_RATIO = 150 / 558;
const ART = (f) => path.join(__dirname, f); // title-bg.png, stripe.png, dot-earth.png, dot-mars.png (made by art.py)

const THEME = {
  name: "Bed Rest to Mars academic",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    // From the title: deep-space navy, Mars rust, Earth blue; cool greys for lines, grids and panels
    dk1: "1B2533", lt1: "FFFFFF", dk2: "0B2545", lt2: "F0F3F7",
    accent1: "C1440E", accent2: "2F6690", accent3: "5D6B7B",
    accent4: "B8C4D1", accent5: "98A6B5", accent6: "E2E7ED",
    hlink: "2F6690", folHlink: "5D6B7B",
  },
};
const HEX = THEME.colors;
const MONO = "Courier New";

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  pres.title = "From Bed Rest to Mars: Development of a Literature-Derived Machine Learning Framework for Predicting Lower-Limb Muscle Atrophy in Spaceflight Analogues";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "Content",
    background: { color: C.background1 },
    objects: [
      { image: { path: ART("stripe.png"), x: 0, y: 0, w: 13.333, h: 0.09, altText: "Gradient stripe, Earth blue to Mars red" } },
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.8,
          fontFace: THEME.headFontFace, fontSize: 28, bold: true, color: C.text2, align: "left", valign: "middle", margin: 0 }, text: "" } },
      { image: { path: LOGO, x: 0.6, y: 6.93, w: 1.25, h: 1.25 * LOGO_RATIO, altText: "DGLRM logo" } },
      { text: { text: "From Bed Rest to Mars  |  64. Jahrestagung der DGLRM", options: { x: 2.0, y: 6.95, w: 5, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 6.95, w: 0.5, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
  });

  pres.defineSlideMaster({ title: "Title", background: { path: ART("title-bg.png") }, objects: [] });

  const SECTIONS = [
    ["Intro and motivation", "Why predict muscle loss; from bed rest to Mars"],
    ["Literature research", "Range of studies; search and screening"],
    ["Data extraction and database", "Dataset contents; loss per muscle group"],
    ["ML framework", "Testing on unseen campaigns"],
    ["Models and results", "Models, results, LLM robustness and validity checks"],
    ["Conclusion", "Findings, limitations, further work"],
  ];
  const PART = (i) => (i < 3 ? "Part 1" : "Part 2");

  // Progress tracker, bottom-right corner: one dot per agenda section, the current one larger.
  function tracker(s, cur) {
    const x0 = 9.95, step = 0.38, cy = 7.1, de = 0.22, dm = 0.24;
    const xe = x0 - 0.4, xm = x0 + step * 5 + 0.38;
    s.addShape(pres.shapes.LINE, { x: xe, y: cy, w: xm - xe, h: 0, line: { color: HEX.accent5, width: 0.75, dashType: "dash" }, objectName: "Tracker line" });
    s.addImage({ path: ART("dot-earth.png"), x: xe - de / 2, y: cy - de / 2, w: de, h: de, altText: "Earth" });
    s.addImage({ path: ART("dot-mars.png"), x: xm - dm / 2, y: cy - dm / 2, w: dm, h: dm, altText: "Mars" });
    for (let i = 0; i < 6; i++) {
      const d = i === cur ? 0.24 : 0.13;
      s.addShape(pres.shapes.OVAL, { x: x0 + i * step - d / 2, y: cy - d / 2, w: d, h: d,
        fill: { color: i === cur ? C.accent1 : i < cur ? C.text2 : C.background1 },
        line: { color: i === cur ? HEX.accent1 : i < cur ? HEX.dk2 : HEX.accent5, width: 0.75 },
        objectName: `Tracker ${i + 1} ${SECTIONS[i][0]}` });
    }
    s.addText(`${cur + 1}  ${SECTIONS[cur][0]}`, { x: 5.9, y: 6.95, w: 3.3, h: 0.3, fontSize: 10, bold: true,
      color: C.accent1, align: "right", margin: 0, isTextBox: true });
  }

  let currentSection = null;
  const add = (sec, master = "Content") => {
    const part = sec === undefined ? "Opening" : PART(sec);
    if (part !== currentSection) { pres.addSection({ title: part }); currentSection = part; }
    const s = pres.addSlide({ masterName: master, sectionTitle: part });
    if (sec !== undefined) tracker(s, sec);
    return s;
  };

  // Placeholder slide for the co-author's half: title, dashed frame, suggested points from the report.
  function placeholder(sec, title, hints, figure) {
    const s = add(sec);
    s.addText(title, { placeholder: "title" });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.35, w: 12.1, h: 5.3, fill: { color: C.background1 },
      line: { color: HEX.accent5, width: 1, dashType: "dash" }, objectName: "Placeholder frame" });
    text(s, [
      { text: "PLACEHOLDER: content by Niloufar", options: { bold: true, fontSize: 14, color: C.accent3, breakLine: true } },
      { text: "Suggested points from the final report:", options: { italic: true, fontSize: 14, color: C.accent3, breakLine: true, paraSpaceAfter: 6 } },
      ...bullets(hints, 16).map((r, i) => (figure && i === hints.length - 1 ? { ...r, options: { ...r.options, breakLine: true } } : r)),
      ...(figure ? [{ text: "Possible figure: " + figure, options: { italic: true, fontSize: 14, color: C.accent3 } }] : []),
    ], { x: 0.9, y: 1.6, w: 11.5, h: 4.9 });
    s.addNotes("Placeholder for the co-author's slide. The suggested points are from the final report on branch feat/report; replace them with the final content.");
    return s;
  }

  const text = (s, t, o) => s.addText(t, { margin: 0, isTextBox: true, color: C.text1, valign: "top", ...o });
  const box = (s, o, name) => s.addShape(pres.shapes.RECTANGLE, {
    fill: { color: C.background1 }, line: { color: HEX.accent5, width: 1 }, objectName: name, ...o });
  const arrow = (s, x, y, w, name) => s.addShape(pres.shapes.LINE, { x, y, w, h: 0,
    line: { color: HEX.dk1, width: 1.25, endArrowType: "triangle" }, objectName: name });
  const bullets = (items, size = 16) => items.map((it, i) => {
    const [t, lvl] = Array.isArray(it) ? it : [it, 0];
    return { text: t, options: { bullet: lvl ? { indent: 18 } : true, indentLevel: lvl, fontSize: lvl ? size - 2 : size,
      breakLine: i < items.length - 1, paraSpaceAfter: lvl ? 2 : 4 } };
  });

  const axis = {
    catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent3,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
    titleFontFace: "+mn-lt", valAxisTitleFontFace: "+mn-lt",
    catAxisLabelFontSize: 14, valAxisLabelFontSize: 12, dataLabelFontSize: 13,
    valGridLine: { color: HEX.accent6, size: 0.75 }, catGridLine: { style: "none" },
    catAxisLineColor: HEX.accent5, valAxisLineShow: false,
    showLegend: false, showTitle: true, titleFontSize: 13, titleColor: HEX.dk1, titleBold: true,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelColor: HEX.dk1,
    barDir: "bar", barGapWidthPct: 50,
  };

  // Tier-2 numbers (model_comparison.csv, tabpfn_comparison.csv) and the LLM's
  // (forecast_comparison.csv). Bottom-to-top order for horizontal bars.
  const ml = [
    ["Gradient boosting", 3.34, 0.30], ["Ridge", 3.28, 0.27], ["SVR", 3.28, 0.36],
    ["TabPFN", 3.22, 0.39], ["Random forest", 3.18, 0.34], ["Duration curve", 3.16, 0.14],
  ];
  let nFig = 0, nTab = 0;
  const FIG = (t) => `Figure ${++nFig}. ${t}`, TAB = (t) => `Table ${++nTab}. ${t}`;
  const color = (n, llm) => (n === "Duration curve" ? HEX.dk2 : n === "LLM prediction" ? HEX.accent1 : HEX.accent4);

  // ---------- Title (Intro) ----------
  {
    const s = add(undefined, "Title");
    s.addImage({ path: LOGO, x: 0.9, y: 0.6, w: 3.2, h: 3.2 * LOGO_RATIO, altText: "DGLRM logo" });
    text(s, [
      { text: "From Bed Rest to Mars:", options: { fontSize: 44, breakLine: true } },
      { text: "Development of a Literature-Derived Machine Learning Framework for Predicting Lower-Limb Muscle Atrophy in Spaceflight Analogues", options: { fontSize: 22, color: "F2D0A9" } },
    ], { x: 0.9, y: 1.5, w: 8.6, h: 2.9, fontFace: THEME.headFontFace, bold: true, color: "FFFFFF", valign: "bottom", paraSpaceAfter: 8 });
    text(s, [
      { text: "Niloufar Ahmadymarzdashty", options: {} }, { text: "1", options: { superscript: true } },
      { text: ",  Milad Bahari Qaragoz", options: {} }, { text: "2", options: { superscript: true } },
    ], { x: 0.9, y: 4.7, w: 8.6, h: 0.4, fontSize: 18, color: "FFFFFF" });
    text(s, [
      { text: "1", options: { superscript: true } }, { text: " Independent researcher", options: { breakLine: true } },
      { text: "2", options: { superscript: true } }, { text: " Master's candidate, Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)", options: {} },
    ], { x: 0.9, y: 5.15, w: 8.6, h: 0.6, fontSize: 14, color: "B7C3D3" });
    text(s, "64. Jahrestagung der DGLRM", { x: 0.9, y: 5.9, w: 8.6, h: 0.4, fontSize: 16, bold: true, color: "F2D0A9" });
    s.addNotes("Intro (Niloufar). Placeholder: add the opening sentence.");
  }

  // ---------- Agenda ----------
  {
    const s = add(undefined);
    s.addText("Agenda", { placeholder: "title" });
    const xs = [0, 1, 2, 3, 4, 5].map((i) => 1.45 + i * 2.08), cy = 3.75, d = 0.7;
    s.addShape(pres.shapes.LINE, { x: 0.75, y: cy, w: 12.55 - 0.75, h: 0, line: { color: HEX.accent5, width: 1.5, dashType: "dash" }, objectName: "Agenda line" });
    s.addImage({ path: ART("dot-earth.png"), x: 0.5, y: cy - 0.23, w: 0.46, h: 0.46, altText: "Earth" });
    s.addImage({ path: ART("dot-mars.png"), x: 12.33, y: cy - 0.26, w: 0.52, h: 0.52, altText: "Mars" });
    // part brackets
    [[0, 2, "Part 1: background and data", "Niloufar Ahmadymarzdashty"], [3, 5, "Part 2: modelling and prediction", "Milad Bahari Qaragoz"]].forEach(([a, b, label, who], k) => {
      const x = xs[a] - 0.35, w = xs[b] - xs[a] + 0.7, y = 2.3;
      s.addShape(pres.shapes.LINE, { x, y: y + 0.8, w, h: 0, line: { color: HEX.dk2, width: 1 }, objectName: `Part ${k + 1} bracket` });
      s.addShape(pres.shapes.LINE, { x, y: y + 0.8, w: 0, h: 0.15, line: { color: HEX.dk2, width: 1 }, objectName: `Part ${k + 1} bracket left` });
      s.addShape(pres.shapes.LINE, { x: x + w, y: y + 0.8, w: 0, h: 0.15, line: { color: HEX.dk2, width: 1 }, objectName: `Part ${k + 1} bracket right` });
      text(s, [{ text: label, options: { bold: true, color: C.text2, breakLine: true } }, { text: who, options: { color: C.accent3, fontSize: 14 } }],
        { x, y, w, h: 0.7, fontSize: 16, align: "center", valign: "bottom" });
    });
    SECTIONS.forEach(([name, desc], i) => {
      s.addShape(pres.shapes.OVAL, { x: xs[i] - d / 2, y: cy - d / 2, w: d, h: d, fill: { color: i < 3 ? C.text2 : C.accent1 },
        line: { type: "none" }, objectName: `Agenda ${i + 1}` });
      text(s, String(i + 1), { x: xs[i] - d / 2, y: cy - d / 2, w: d, h: d, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle" });
      text(s, [{ text: name, options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } }, { text: desc, options: { fontSize: 14 } }],
        { x: xs[i] - 0.98, y: cy + 0.6, w: 1.96, h: 1.6, align: "center" });
    });
    text(s, "The marker in the bottom-right corner of each slide shows where we are.", { x: 0.6, y: 6.3, w: 12.1, h: 0.35, fontSize: 13, italic: true, color: C.accent3 });
    s.addNotes("Agenda. Part 1 (Niloufar): why this matters and why bed rest, how we searched the literature, and what the dataset contains, including which muscles lose most. Part 2 (Milad): how we tested the models, the models and their results with the validity checks of the LLM, and the conclusion.");
  }

  // ---------- Co-author's half: placeholders ----------
  // ---------- Motivation (slide 3) ----------
  {
    const s = add(0);
    s.addText("Motivation: predicting lower-limb muscle atrophy", { placeholder: "title" });
    text(s, [
      { text: "Why is this important?", options: { bold: true, fontSize: 20, color: C.text2, breakLine: true, paraSpaceAfter: 8 } },
      ...bullets([
        "Prevention: identify risk early and leave time to intervene",
        "Countermeasures: match exercise and nutrition to the predicted risk",
        "Vulnerable muscles: show which muscles need closer monitoring",
        "Function: less muscle loss helps preserve strength and power",
        "Mission planning: estimate muscle loss on long missions with limited exercise equipment",
      ], 17).map((r) => ({ ...r, options: { ...r.options, paraSpaceAfter: 10 } })),
    ], { x: 0.6, y: 1.35, w: 6.6, h: 4.6, valign: "top" });

    // right panel: unloading and what it does to a muscle
    const px = 7.55, pw = 5.18;
    s.addShape(pres.shapes.RECTANGLE, { x: px, y: 1.35, w: pw, h: 5.35, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Illustration panel" });
    text(s, FIG("Unloading shrinks leg muscles"), { x: px + 0.25, y: 1.5, w: pw - 0.5, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
    // bed tilted head-down (head at the right, lower end), person lying on it
    s.addShape(pres.shapes.RECTANGLE, { x: 8.0, y: 2.6, w: 4.3, h: 0.14, rotate: 6, fill: { color: C.accent3 }, line: { type: "none" }, objectName: "Bed" });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.6, y: 2.29, w: 2.85, h: 0.36, rotate: 6, rectRadius: 0.15, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Body" });
    s.addShape(pres.shapes.OVAL, { x: 11.45, y: 2.37, w: 0.42, h: 0.42, fill: { color: C.text2 }, line: { type: "none" }, objectName: "Head" });
    text(s, "Weeks to months in bed; legs carry no body weight", { x: px + 0.25, y: 3.05, w: pw - 0.5, h: 0.3, fontSize: 12, italic: true, color: C.accent3 });

    // muscle cross-sections drawn to scale: area −15.8% (calf, control groups, day 60)
    const d0 = 1.9, d1 = d0 * Math.sqrt(1 - 0.158), cy = 4.6, bone = 0.42;
    const sec = (cx, d, name) => {
      s.addShape(pres.shapes.OVAL, { x: cx - d / 2, y: cy - d / 2, w: d, h: d, fill: { color: C.accent1, transparency: 25 }, line: { color: HEX.accent1, width: 1 }, objectName: name });
      s.addShape(pres.shapes.OVAL, { x: cx - bone / 2 - 0.2, y: cy - bone / 2 + 0.15, w: bone, h: bone, fill: { color: C.background1 }, line: { color: HEX.accent5, width: 1 }, objectName: name + " bone" });
    };
    sec(8.85, d0, "Muscle before");
    s.addShape(pres.shapes.LINE, { x: 9.95, y: cy, w: 0.6, h: 0, line: { color: HEX.dk1, width: 1.25, endArrowType: "triangle" }, objectName: "Arrow" });
    sec(11.55, d1, "Muscle after");
    // dashed outline: original size, so the lost tissue is visible
    s.addShape(pres.shapes.OVAL, { x: 11.55 - d0 / 2, y: cy - d0 / 2, w: d0, h: d0, fill: { type: "none" }, line: { color: HEX.dk1, width: 1, dashType: "dash" }, objectName: "Original outline" });
    text(s, "Before bed rest", { x: 7.85, y: 5.65, w: 2.0, h: 0.3, fontSize: 13, align: "center", bold: true });
    text(s, "After unloading", { x: 10.55, y: 5.65, w: 2.0, h: 0.3, fontSize: 13, align: "center", bold: true, color: C.accent1 });
    text(s, "Schematic calf cross-section; dashed line = size before unloading.", { x: px + 0.25, y: 6.05, w: pw - 0.5, h: 0.5, fontSize: 11, italic: true, color: C.accent3 });

    s.addNotes(
      "Opening of part 1 (Niloufar), about forty-five seconds.\n\n" +
      "Muscle atrophy, especially in the legs, is one of the main problems of long-duration spaceflight. " +
      "Our question, in the title, is whether the amount of atrophy can be predicted.\n\n" +
      "Why it matters: a prediction lets crews and planners act early, match exercise and nutrition to the expected loss, focus monitoring on the muscles that lose most, protect strength and function, and plan long missions where exercise equipment is limited.\n\n" +
      "On the right is the ground model we rely on: volunteers lie in bed tilted six degrees head-down for weeks to months. " +
      "The circles show a calf cross-section before and after unloading; how much each muscle loses comes later, in the muscle section."
    );
  }
  // ---------- Why from bed rest to Mars? (slide 4) ----------
  {
    const s = add(0);
    s.addText("From bed rest to Mars: analogue and application", { placeholder: "title" });
    const head = (t, before = 0) => ({ text: t, options: { bold: true, fontSize: 19, color: C.text2, breakLine: true, paraSpaceBefore: before, paraSpaceAfter: 3 } });
    const last = (rows) => rows.map((r, i, a) => (i === a.length - 1 ? { ...r, options: { ...r.options, breakLine: true } } : r));
    text(s, [
      head("Bed rest: the ground analogue"),
      ...last(bullets([
        "Spaceflight data on muscle are scarce",
        "Head-down bed rest unloads the legs under controlled conditions",
      ], 16)),
      head("Mars: the long-term application", 18),
      ...bullets([
        "No early return in an emergency: the crew depends on its own fitness",
      ], 16),
    ], { x: 0.6, y: 1.3, w: 6.1, h: 3.85 });

    // right: Moon mission vs Mars mission
    const gx = 7.1, gw = 5.63;
    s.addShape(pres.shapes.RECTANGLE, { x: gx, y: 1.3, w: gw, h: 3.85, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Mission panel" });
    text(s, FIG("Moon mission vs Mars mission"), { x: gx + 0.2, y: 1.4, w: gw - 0.4, h: 0.3, fontSize: 14, bold: true, color: C.text2 });
    // schematic: distances from Earth
    const ey = 2.3;
    const body = (cx, d, col, name, label) => {
      s.addShape(pres.shapes.OVAL, { x: cx - d / 2, y: ey - d / 2, w: d, h: d, fill: { color: col }, line: { type: "none" }, objectName: name });
      s.addImage({ path: path.join(__dirname, `planet-${name.toLowerCase()}.png`), x: cx - d / 2, y: ey - d / 2, w: d, h: d, altText: name + " (photo map, semi-transparent)" });
      text(s, label, { x: cx - 0.6, y: ey + 0.36, w: 1.2, h: 0.25, fontSize: 11, bold: true, align: "center" });
    };
    const dash = (x1, x2, lab, name) => {
      s.addShape(pres.shapes.LINE, { x: x1, y: ey, w: x2 - x1, h: 0, line: { color: HEX.accent3, width: 1, dashType: "dash", endArrowType: "triangle" }, objectName: name });
      text(s, lab, { x: x1, y: ey - 0.32, w: x2 - x1, h: 0.25, fontSize: 11, italic: true, align: "center", color: C.text2 });
    };
    body(7.6, 0.6, HEX.dk2, "Earth", "Earth");
    body(8.75, 0.3, HEX.accent4, "Moon", "Moon");
    body(12.2, 0.5, HEX.accent1, "Mars", "Mars");
    dash(7.93, 8.58, "3 days", "Route to Moon");
    dash(8.95, 11.93, "about 6 months, one way", "Route to Mars");

    // timelines on one day scale (0 to 900 days)
    const bx = 9.0, bw = 3.5, perDay = bw / 900, X = (d) => bx + d * perDay;
    const rowY = [3.05, 3.8];
    text(s, [
      { text: "Moon mission", options: { bold: true, fontSize: 13, breakLine: true } },
      { text: "about 12 days", options: { fontSize: 10.5, italic: true, color: C.accent3 } },
    ], { x: gx + 0.2, y: rowY[0], w: 1.85, h: 0.55 });
    s.addShape(pres.shapes.RECTANGLE, { x: X(0), y: rowY[0] + 0.1, w: 12 * perDay, h: 0.32, fill: { color: HEX.accent3 }, line: { type: "none" }, objectName: "Moon mission bar" });
    text(s, "◄ the whole mission (Apollo 17)", { x: X(12) + 0.06, y: rowY[0] + 0.1, w: 2.6, h: 0.32, fontSize: 10.5, italic: true, valign: "middle", color: C.accent3 });
    text(s, [
      { text: "Mars mission", options: { bold: true, fontSize: 13, breakLine: true } },
      { text: "about 2.5 years", options: { fontSize: 10.5, italic: true, color: C.accent3 } },
    ], { x: gx + 0.2, y: rowY[1], w: 1.85, h: 0.55 });
    [["to Mars", 0, 180, 0], ["on Mars, about 500 days", 180, 680, 45], ["home", 680, 860, 0]].forEach(([lab, d0, d1, tr], i) => {
      s.addShape(pres.shapes.RECTANGLE, { x: X(d0), y: rowY[1] + 0.1, w: (d1 - d0) * perDay, h: 0.32, fill: { color: HEX.accent1, transparency: tr }, line: { color: HEX.lt1, width: 1 }, objectName: "Mars " + lab });
      text(s, lab, { x: X(d0), y: rowY[1] + 0.1, w: (d1 - d0) * perDay, h: 0.32, fontSize: 10, bold: true, align: "center", valign: "middle", color: i === 1 ? C.text1 : C.background1 });
    });
    // arrival marker
    s.addShape(pres.shapes.LINE, { x: X(180), y: rowY[1] + 0.45, w: 0, h: 0.2, line: { color: HEX.dk1, width: 1, beginArrowType: "triangle" }, objectName: "Arrival marker" });
    text(s, "arrival: 6 months weightless, then surface work", { x: X(180) - 0.6, y: rowY[1] + 0.67, w: 4.1, h: 0.25, fontSize: 10.5, italic: true, align: "left", color: C.text2 });
    // axis in years
    const ay = 4.85;
    s.addShape(pres.shapes.LINE, { x: bx, y: ay, w: bw, h: 0, line: { color: HEX.accent3, width: 0.75 }, objectName: "Time axis" });
    [[0, "0"], [365, "1 year"], [730, "2 years"]].forEach(([d, l]) => {
      s.addShape(pres.shapes.LINE, { x: X(d), y: ay, w: 0, h: 0.06, line: { color: HEX.accent3, width: 0.75 }, objectName: "Tick " + l });
      text(s, l, { x: X(d) - 0.4, y: ay + 0.06, w: 0.8, h: 0.2, fontSize: 10, align: "center", color: C.accent3 });
    });

    // bottom: from prediction to readiness
    const fy = 5.45, fh = 0.75, fw = 2.65;
    const fx = [0.6, 3.75, 6.9, 10.05];
    const steps = [
      ["Bed-rest studies", "ground analogue", false],
      ["Atrophy prediction", "this work", false],
      ["Strength and power assessment", "", true],
      ["Operational readiness on arrival", "", true],
    ];
    steps.forEach(([t, sub, future], i) => {
      s.addShape(pres.shapes.RECTANGLE, { x: fx[i], y: fy, w: fw, h: fh,
        fill: { color: i === 1 ? HEX.dk2 : HEX.lt1 }, line: { color: i === 1 ? HEX.dk2 : HEX.accent5, width: 1, dashType: future ? "dash" : "solid" }, objectName: "Step " + (i + 1) });
      text(s, sub ? [
        { text: t, options: { bold: true, fontSize: 14, breakLine: true } },
        { text: sub, options: { fontSize: 11, italic: true } },
      ] : [{ text: t, options: { bold: true, fontSize: 14 } }], { x: fx[i] + 0.1, y: fy, w: fw - 0.2, h: fh, align: "center", valign: "middle", color: i === 1 ? C.background1 : C.text1 });
    });
    arrow(s, fx[0] + fw + 0.05, fy + fh / 2, fx[1] - fx[0] - fw - 0.1, "Arrow 1");
    text(s, "+", { x: fx[1] + fw, y: fy, w: fx[2] - fx[1] - fw, h: fh, fontSize: 24, bold: true, align: "center", valign: "middle", color: C.text2 });
    arrow(s, fx[2] + fw + 0.05, fy + fh / 2, fx[3] - fx[2] - fw - 0.1, "Arrow 3");
    text(s, FIG("From bed-rest data to crew readiness"), { x: 0.6, y: fy + fh + 0.07, w: 6.0, h: 0.25, fontSize: 11, bold: true, color: C.text2 });
    text(s, "Dashed: future use, which needs validation with spaceflight data", { x: 6.9, y: fy + fh + 0.07, w: 5.8, h: 0.25, fontSize: 11, italic: true, color: C.accent3 });

    s.addNotes(
      "Part 1 (Niloufar), about forty-five seconds.\n\n" +
      "Direct spaceflight data on muscle are scarce, so we use head-down bed rest, the standard ground analogue: volunteers lie tilted six degrees head-down and their legs carry no weight, under controlled conditions. " +
      "Bed rest is not the same as spaceflight, but it is a sound starting point to build and test prediction models.\n\n" +
      "Mars in our title stands for the long-term application. The panel compares the two missions on one time scale. " +
      "A Moon mission lasted about twelve days, and the crew could be home in three. " +
      "A Mars mission takes about two and a half years: six months to get there, about five hundred days on the surface, six months back. " +
      "There is no early return in an emergency, and after six months in weightlessness the crew must leave the spacecraft and work on the surface. " +
      "Mission figures: Apollo 17, and NASA's Mars Design Reference Architecture 5.0.\n\n" +
      "The bottom row is the idea: atrophy prediction, together with strength and power testing, could one day help keep the crew ready for work on arrival. " +
      "The dashed steps are future use, and applying the model on a real mission needs validation with spaceflight data first."
    );
  }
  // ---------- What range did we study? (slide 5) ----------
  {
    const s = add(1);
    s.addText("Range of unloading durations and studies", { placeholder: "title" });

    // top: range in the abstract vs range in the final dataset, on one day scale
    const bx = 3.6, bw = 8.4, X = (d) => bx + d / 180 * bw;
    text(s, FIG("Unloading range in the abstract and in the final dataset"), { x: 0.6, y: 1.22, w: 12.1, h: 0.32, fontSize: 14, bold: true, color: C.text2 });
    const ranges = [
      { lab: "Abstract", sub: "15 bed-rest studies", segs: [[14, 119, HEX.accent4]], note: "14 to 119 days" },
      { lab: "Final dataset", sub: "52 studies", segs: [[5, 119, HEX.dk2], [119, 180, HEX.accent1]], note: "5 to 180 days" },
    ];
    ranges.forEach((r, i) => {
      const y = 1.62 + i * 0.62;
      text(s, [
        { text: r.lab, options: { bold: true, fontSize: 15, breakLine: true, color: C.text2 } },
        { text: r.sub, options: { fontSize: 12, color: C.accent3 } },
      ], { x: 0.6, y, w: 2.9, h: 0.6, valign: "middle" });
      r.segs.forEach(([d0, d1, col], k) => {
        s.addShape(pres.shapes.RECTANGLE, { x: X(d0), y: y + 0.12, w: X(d1) - X(d0), h: 0.36, fill: { color: col }, line: { type: "none" }, objectName: `${r.lab} ${d0}-${d1}` });
      });
      text(s, String(r.segs[0][0]), { x: X(r.segs[0][0]) - 0.45, y: y + 0.12, w: 0.4, h: 0.36, fontSize: 12, align: "right", valign: "middle", bold: true });
      text(s, String(r.segs[r.segs.length - 1][1]), { x: X(r.segs[r.segs.length - 1][1]) + 0.07, y: y + 0.12, w: 0.5, h: 0.36, fontSize: 12, valign: "middle", bold: true });
      if (i === 1) {
        text(s, "bed rest", { x: X(5), y: y + 0.12, w: X(119) - X(5), h: 0.36, fontSize: 12, bold: true, align: "center", valign: "middle", color: C.background1 });
        text(s, "spaceflight", { x: X(119), y: y + 0.12, w: X(180) - X(119), h: 0.36, fontSize: 12, bold: true, align: "center", valign: "middle", color: C.background1 });
      }
    });
    // shared day axis
    const ay = 2.92;
    s.addShape(pres.shapes.LINE, { x: X(0), y: ay, w: bw, h: 0, line: { color: HEX.accent3, width: 0.75 }, objectName: "Day axis" });
    [0, 30, 60, 90, 119, 150, 180].forEach((d) => {
      s.addShape(pres.shapes.LINE, { x: X(d), y: ay, w: 0, h: 0.06, line: { color: HEX.accent3, width: 0.75 }, objectName: "Tick " + d });
      text(s, String(d), { x: X(d) - 0.3, y: ay + 0.07, w: 0.6, h: 0.22, fontSize: 10, align: "center", color: C.accent3 });
    });
    text(s, "Days of unloading", { x: 0.6, y: ay - 0.02, w: 2.8, h: 0.3, fontSize: 11, align: "right", color: C.accent3 });

    // bottom: studies per year, coloured by how long the unloading lasted
    const bands = [["5 to 14 days", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2, 2, 0, 1, 2, 0, 2, 2, 1, 2, 3, 3]], ["15 to 30 days", [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1]], ["31 to 60 days", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 2, 1, 0, 1, 1, 1]], ["61 to 119 days", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1]], ["180 days (spaceflight)", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]]];
    // keep only years in which at least one study was published
    const keep = bands[0][1].map((_, i) => i).filter((i) => bands.some(([, v]) => v[i] > 0));
    const years = keep.map((i) => String(1992 + i));
    // chart frame chosen so the plot area spans the same x range as the day scale above (bx to bx + bw)
    const cx = 3.0, cw = 9.4;
    text(s, FIG("Studies published per year, by length of unloading"), { x: bx, y: 3.3, w: bw, h: 0.35, fontSize: 14, bold: true, color: C.text2 });
    text(s, "Years without studies omitted", { x: bx, y: 3.62, w: bw, h: 0.25, fontSize: 11, italic: true, color: C.accent3 });
    const cols = ["D3DCE6", "9AB0C7", "5B80A5", HEX.dk2, HEX.accent1];
    text(s, "Length of unloading", { x: 0.6, y: 4.2, w: 2.4, h: 0.3, fontSize: 13, bold: true, color: C.text2 });
    [...bands].reverse().forEach(([name], k) => {
      const ly = 4.6 + k * 0.36, ci = bands.length - 1 - k;
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: ly + 0.06, w: 0.22, h: 0.18, fill: { color: cols[ci] }, line: { type: "none" }, objectName: "Legend " + name });
      text(s, name, { x: 0.9, y: ly, w: 2.1, h: 0.3, fontSize: 12, valign: "middle" });
    });
    s.addChart(pres.charts.BAR, bands.map(([name, values]) => ({ name, labels: years, values: keep.map((i) => values[i]) })), {
      x: cx, y: 3.9, w: cw, h: 2.95, barDir: "col", barGrouping: "stacked", barGapWidthPct: 35,
      layout: { x: (bx - cx) / cw, y: 0.04, w: bw / cw, h: 0.82 },
      chartColors: cols,
      catAxisLabelColor: HEX.accent3, valAxisLabelColor: HEX.accent3, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
      catAxisLabelRotate: 0, catAxisLineColor: HEX.accent5, catGridLine: { style: "none" },
      valAxisMinVal: 0, valAxisMaxVal: 7, valAxisMajorUnit: 1, valAxisLineShow: false, valGridLine: { color: HEX.accent6, size: 0.75 },
      showValAxisTitle: false, showTitle: false, showLegend: false,
    });

    s.addNotes(
      "Part 1 (Niloufar), about forty-five seconds.\n\n" +
      "When we submitted the abstract, our dataset held 15 bed-rest studies, covering 14 to 119 days of unloading. " +
      "After submission we extended it. The final dataset has 52 studies, published from 1992 to 2026, and covers 5 to 180 days. " +
      "The orange part of the lower bar is not bed rest: the stretch beyond 119 days comes from spaceflight, where three studies measured crews after about 180 days.\n\n" +
      "The chart below shows how many of these studies were published each year, and the colours show how long the unloading lasted. " +
      "Most of the literature is recent: 37 of the 52 studies are from 2016 or later. Short studies of up to two weeks are the most common; long campaigns of two to four months are rarer."
    );
  }
  // ---------- How did we build the dataset? (slide 6) ----------
  {
    const s = add(1);
    s.addText("Literature search and study selection", { placeholder: "title" });
    const bw = 2.1, step = 2.45, by = 2.5, bh = 1.45, xs = [0, 1, 2, 3, 4].map((i) => 0.6 + i * step);
    const flow = [
      ["Identification", "5,741", "records found", "PubMed, Scopus, Web of Science, NASA reports; 10 from other sources"],
      ["Screening", "3,600", "records after removing duplicates", ""],
      ["Full text", "84", "full texts sought", ""],
      ["Included", "52", "studies", ""],
      ["Final dataset", "36", "campaigns", "742 rows; papers on the same cohort merged"],
    ];
    flow.forEach(([phase, n, lab, sub], i) => {
      const last = i === 4, x = xs[i];
      text(s, phase.toUpperCase(), { x, y: by - 0.35, w: bw, h: 0.25, fontSize: 10.5, bold: true, align: "center", color: last ? C.accent1 : C.accent3, charSpacing: 1 });
      s.addShape(pres.shapes.RECTANGLE, { x, y: by, w: bw, h: bh, fill: { color: last ? HEX.dk2 : HEX.lt1 }, line: { color: last ? HEX.dk2 : HEX.accent5, width: 1 }, objectName: "Step " + phase });
      const tc = last ? C.background1 : C.text1;
      text(s, [
        { text: n, options: { fontSize: 26, bold: true, fontFace: THEME.headFontFace, color: last ? C.background1 : C.text2, breakLine: true } },
        { text: lab, options: { fontSize: 13, color: tc, breakLine: !!sub } },
        ...(sub ? [{ text: sub, options: { fontSize: 10.5, italic: true, color: last ? C.background1 : C.accent3 } }] : []),
      ], { x: x + 0.1, y: by + 0.08, w: bw - 0.2, h: bh - 0.16, align: "center", valign: "middle" });
      if (i < 4) arrow(s, x + bw + 0.04, by + bh / 2, step - bw - 0.08, "Flow arrow " + (i + 1));
    });

    // what was removed between steps
    const notes = [
      "2,141 duplicates removed",
      "2,493 excluded, mostly no unloading model or no muscle outcome\n1,023 not screened in time",
      "19 report muscle results only as charts, without a baseline value\n4 full texts not available\n11 excluded at full text",
    ];
    notes.forEach((t, i) => {
      const cx = xs[i] + bw + (step - bw) / 2;
      s.addShape(pres.shapes.LINE, { x: cx, y: by + bh / 2 + 0.05, w: 0, h: 1.05, line: { color: HEX.accent5, width: 0.75, dashType: "dash", endArrowType: "triangle" }, objectName: "Removed " + (i + 1) });
      text(s, t, { x: cx - 1.1, y: by + bh / 2 + 1.15, w: 2.2, h: 1.5, fontSize: 11, align: "center", color: C.accent3 });
    });

    text(s, FIG("Flow of records, in the style of PRISMA 2020. Full-text counts as recorded; they are still being reconciled with the dataset."), { x: 0.6, y: 6.35, w: 12.1, h: 0.3, fontSize: 11, italic: true, color: C.accent3 });

    s.addNotes(
      "Part 1 (Niloufar), about one minute.\n\n" +
      "We searched four databases, PubMed, Scopus, Web of Science and NASA's technical reports, and added older work we had collected before the search, nine studies from before 2013 and one campaign from NASA's open bed-rest data. In total, 5,741 records. " +
      "After removing duplicates, 3,600 records remained. 2,493 were excluded, mostly because they did not use an unloading model or did not measure muscle, and 1,023 could not be screened in the time we had, so they did not go further.\n\n" +
      "We sought 84 full texts. The main loss at this step: 19 studies show their muscle results only as charts, without a baseline value, so we could not extract them; 4 full texts were not available and 11 were excluded. " +
      "These full-text counts are as recorded in our screening log and are still being reconciled with the dataset, so do not claim they add up exactly. " +
      "52 studies were included.\n\n" +
      "Several papers often report the same bed-rest campaign, so we merged papers on the same cohort. The final dataset has 36 independent campaigns and 742 rows."
    );
  }
  // ---------- What does the dataset look like? (slide 7) ----------
  {
    const s = add(2);
    s.addText("Dataset composition", { placeholder: "title" });

    // bottom: two tables side by side
    const hdr = (t, align = "left") => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 }, align } });
    const cell = (t, align = "left", bold = false) => ({ text: t, options: { align, bold } });
    const tOpts = { fontSize: 13, fontFace: THEME.bodyFontFace, color: HEX.dk1, valign: "middle", rowH: 0.4,
      border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: HEX.accent6 }, { type: "none" }], margin: [0.03, 0.1, 0.03, 0.1] };
    text(s, TAB("Final dataset at a glance"), { x: 0.6, y: 1.45, w: 5.9, h: 0.32, fontSize: 15, bold: true, color: C.text2 });
    s.addTable([
      [hdr("Feature"), hdr("n", "right")],
      [cell("Muscles or muscle groups"), cell("51", "right", true)],
      [cell("Rows: control / countermeasure"), cell("470 / 272", "right", true)],
      [cell("Rows: during bed rest / recovery"), cell("478 / 264", "right", true)],
    ], { x: 0.6, y: 1.9, w: 5.9, colW: [4.1, 1.8], ...tOpts, rowH: 0.5 });
    text(s, [
      { text: "742 observations are not 742 independent participants: ", options: { bold: true } },
      { text: "one campaign gives rows for several muscles, groups and scan days." },
    ], { x: 0.6, y: 5.3, w: 12.1, h: 0.7, fontSize: 14 });

    text(s, TAB("Imaging method and size measure"), { x: 7.0, y: 1.45, w: 5.73, h: 0.32, fontSize: 15, bold: true, color: C.text2 });
    s.addTable([
      [hdr("Method"), hdr("n", "right"), hdr("Size measure"), hdr("n", "right")],
      [cell("MRI"), cell("655", "right", true), cell("Volume"), cell("594", "right", true)],
      [cell("DXA"), cell("37", "right", true), cell("Cross-sectional area"), cell("100", "right", true)],
      [cell("CT"), cell("30", "right", true), cell("Lean mass"), cell("37", "right", true)],
      [cell("Ultrasound"), cell("20", "right", true), cell("Thickness"), cell("11", "right", true)],
      [cell("Total", "left", true), cell("742", "right", true), cell("Total", "left", true), cell("742", "right", true)],
    ], { x: 7.0, y: 1.9, w: 5.73, colW: [1.45, 0.85, 2.48, 0.95], ...tOpts, rowH: 0.5 });

    s.addNotes(
      "Part 1 (Niloufar), about one minute.\n\n" +
      "The final dataset has 742 rows. Each row is one muscle outcome: one muscle, in one group, at one scan day. " +
      "One campaign can therefore give many rows, for several muscles, time points or groups.\n\n" +
      "For each outcome we extracted the length of unloading, the day of the scan, the muscle, the participants (group size, share of women, age), whether the group had a countermeasure, the imaging method, and how muscle size was measured. " +
      "Our prediction target is the percentage change in muscle size from baseline.\n\n" +
      "Left table: 742 rows from 52 studies and 36 independent campaigns, covering 51 muscles or muscle groups; 470 rows are control groups and 272 countermeasure groups; 478 were measured during bed rest and 264 in recovery. " +
      "742 rows does not mean 742 people: one campaign gives rows for several muscles, groups and scan days.\n\n" +
      "Right table: most rows are MRI volumes. CT gives cross-sectional area, DXA gives lean mass of the leg, and ultrasound gives thickness or area."
    );
  }
  // ---------- Are all muscles affected the same? (slide 8) ----------
  {
    const s = add(2);
    s.addText("Muscle atrophy by muscle group", { placeholder: "title" });
    // day-60 estimates per muscle group: report tab_ranking (modelling subset, control groups)
    const groups = [
      ["hip-rotators", "Deep hip rotators", -1.9, "9AA5B1"],
      ["hip-adductors", "Inner thigh (hip adductors)", -5.4, "3A9CA6"],
      ["hip-extensors", "Glutes (hip extensors)", -6.1, "9C6B98"],
      ["hip-flexors", "Hip flexors", -6.8, "6A994E"],
      ["hip-abductors", "Outer hip (hip abductors)", -9.1, "7B6FC4"],
      ["knee-flexors", "Back thigh (knee flexors)", -9.8, "4F86C6"],
      ["knee-extensors", "Front thigh (knee extensors)", -10.1, HEX.dk2],
      ["dorsiflexors", "Shin (dorsiflexors)", -10.2, "E0A030"],
      ["plantar-flexors", "Calf (plantar flexors)", -15.8, HEX.accent1],
    ];
    // common saturating time course from the report (tau = 60 days), scaled to each group's day-60 value
    const shape = (t) => (1 - Math.exp(-t / 60)) / (1 - Math.exp(-1));
    const px = 1.35, pw = 6.9, py = 1.5, ph = 4.25, dMax = 120, yMin = -24;
    const X = (d) => px + d / dMax * pw, Y = (v) => py + (v / yMin) * ph;
    [0, -4, -8, -12, -16, -20, -24].forEach((v) => {
      s.addShape(pres.shapes.LINE, { x: px, y: Y(v), w: pw, h: 0, line: { color: v ? HEX.accent6 : HEX.accent3, width: 0.75 }, objectName: "Grid " + v });
      text(s, (v ? "−" + -v : "0") + "%", { x: px - 0.62, y: Y(v) - 0.11, w: 0.52, h: 0.22, fontSize: 10, align: "right", color: C.accent3 });
    });
    [0, 30, 60, 90, 120].forEach((d) => {
      text(s, String(d), { x: X(d) - 0.3, y: Y(yMin) + 0.06, w: 0.6, h: 0.22, fontSize: 10, align: "center", color: C.accent3 });
    });
    text(s, "Day of unloading", { x: px, y: Y(yMin) + 0.3, w: pw, h: 0.25, fontSize: 11, align: "center", color: C.accent3 });
    text(s, "Change in muscle size", { x: px - 0.75, y: py - 0.38, w: 2.5, h: 0.25, fontSize: 11, color: C.accent3 });
    // dashed reading line at day 60
    s.addShape(pres.shapes.LINE, { x: X(60), y: py - 0.1, w: 0, h: ph + 0.1, line: { color: HEX.dk1, width: 1, dashType: "dash" }, objectName: "Day 60 line" });
    text(s, "day 60", { x: X(60) + 0.05, y: py - 0.12, w: 0.8, h: 0.22, fontSize: 10.5, bold: true });
    // curves from day 5 to day 119 (the range of the bed-rest data)
    const days = []; for (let d = 5; d <= 119; d += 2) days.push(d); days.push(119);
    const top = Y(0), xs0 = X(5);
    groups.forEach(([key, name, v60, col]) => {
      const pts = days.map((d) => ({ x: X(d) - xs0, y: Y(v60 * shape(d)) - top }));
      const h = Math.max(...pts.map((p) => p.y));
      s.addShape(pres.shapes.CUSTOM_GEOMETRY, { x: xs0, y: top, w: X(119) - xs0, h, points: pts,
        fill: { type: "none" }, line: { color: col, width: key === "plantar-flexors" ? 3 : 2 }, objectName: name + " curve" });
      s.addShape(pres.shapes.OVAL, { x: X(60) - 0.055, y: Y(v60) - 0.055, w: 0.11, h: 0.11, fill: { color: col }, line: { color: HEX.lt1, width: 0.5 }, objectName: name + " at day 60" });
    });

    // labels: icon, name and day-60 value, in the order of the curves
    const lx = 9.0, ly0 = 1.38, lh = 0.54;
    text(s, "At day 60", { x: 11.7, y: ly0 - 0.3, w: 1.02, h: 0.25, fontSize: 10.5, bold: true, align: "right", color: C.accent3 });
    groups.forEach(([key, name, v60, col], i) => {
      const y = ly0 + i * lh, cyl = y + lh / 2;
      // leader from the curve end (day 119) to the label
      const ex = X(119), ey = Y(v60 * shape(119));
      s.addShape(pres.shapes.LINE, { x: ex + 0.03, y: Math.min(ey, cyl), w: lx - ex - 0.1, h: Math.abs(cyl - ey) || 0.001, flipV: cyl < ey,
        line: { color: col, width: 0.75 }, objectName: name + " leader" });
      s.addImage({ path: path.join(__dirname, `muscle-${key}.png`), x: lx, y: y + 0.02, w: (lh - 0.04) * 2 / 3, h: lh - 0.04, altText: name + " (highlighted on a leg outline)" });
      text(s, name, { x: lx + 0.42, y, w: 2.5, h: lh, fontSize: 12, valign: "middle", color: C.text1 });
      text(s, (v60 + "").replace("-", "−") + "%", { x: 11.9, y, w: 0.82, h: lh, fontSize: 13, bold: true, align: "right", valign: "middle", color: col });
    });

    text(s, FIG("Change in muscle size by muscle group: one shared time course (τ = 60 days) scaled to each group's day-60 estimate; control groups, days 5 to 119."),
      { x: 0.6, y: 6.45, w: 12.1, h: 0.25, fontSize: 10.5, italic: true, color: C.accent3 });

    s.addNotes(
      "Part 1 (Niloufar), about one minute.\n\n" +
      "No, muscles are not affected equally. Each line shows how much a muscle group shrinks over the days of bed rest, for groups without a countermeasure. " +
      "The dashed line reads the values at day 60.\n\n" +
      "The calf, the plantar flexors, loses most: about 16 percent at day 60, almost 6 percentage points more than the front thigh. " +
      "The shin, the front thigh and the back thigh lose about 10 percent. Hip muscles lose least.\n\n" +
      "How the lines are drawn: the day-60 values are the estimates of our meta-regression for each muscle group. The shape over time is the one curve the model fits to all muscles, " +
      "rising fast in the first weeks and levelling off; time constant 60 days. Hip rotators and outer hip rest on a single campaign each, so treat those two with care."
    );
  }

  // ---------- Slide 1: the evaluation setup ----------
  {
    const s = add(3);
    s.addText("Evaluation: leave-one-campaign-out validation", { placeholder: "title" });

    const y = 1.45, h = 2.75;
    box(s, { x: 0.6, y, w: 4.6, h }, "Input box");
    text(s, [
      { text: "Input: one measurement", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      ...bullets(["Day of bed rest when the scan was taken", "Which muscle group (9, e.g. calf, front thigh)", "Exercise group or no-exercise control",
        "How it was scanned (MRI, CT, DXA, ultrasound)", "One muscle or several combined"], 15),
    ], { x: 0.8, y: y + 0.15, w: 4.25, h: h - 0.3 });
    arrow(s, 5.25, y + h / 2, 0.5, "Arrow input to model");
    box(s, { x: 5.8, y, w: 3.4, h }, "Model box");
    text(s, [
      { text: "Model", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      ...bullets(["Duration curve: uses the number of days only (the baseline)", "4 standard ML models", "TabPFN (pretrained network)", "LLM classifier: returns a probability per range"], 15),
    ], { x: 6.0, y: y + 0.15, w: 3.05, h: h - 0.3 });
    arrow(s, 9.25, y + h / 2, 0.5, "Arrow model to output");
    box(s, { x: 9.8, y, w: 2.93, h }, "Output box");
    text(s, [
      { text: "Output", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      { text: "How much the muscle has shrunk, in % of its size before bed rest", options: { fontSize: 15, breakLine: true } },
      { text: "Average over the group of volunteers, e.g. \u221210%", options: { fontSize: 14, color: C.accent3 } },
    ], { x: 10.0, y: y + 0.15, w: 2.6, h: h - 0.3 });

    // leave-one-campaign-out strip
    const sy = 4.75, n = 32, w = 0.27, g = 0.05, held = 13;
    text(s, FIG("Testing: hold out one campaign, train on the rest, repeat 32 times"), { x: 0.6, y: 4.4, w: 10, h: 0.3, fontSize: 15, bold: true, color: C.text2 });
    for (let i = 0; i < n; i++) {
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6 + i * (w + g), y: sy, w, h: 0.27,
        fill: { color: i === held ? C.accent1 : C.accent6 }, line: { color: i === held ? HEX.accent1 : HEX.accent5, width: 0.5 },
        objectName: i === held ? "Test campaign" : `Training campaign ${i + 1}` });
    }
    text(s, [
      { text: "Grey: 31 training campaigns.  ", options: {} },
      { text: "Orange: the held-out test campaign.", options: { color: C.accent1 } },
      { text: "  Each campaign is held out once.", options: {} },
    ], { x: 0.6, y: 5.15, w: 11, h: 0.3, fontSize: 14 });
    text(s, bullets([
      "Why campaigns, not measurements: the 346 rows used for modelling come from 32 of the 36 campaigns, and rows of one campaign share volunteers.",
      "Score: average error in percentage points (pp), each campaign counted once. Predicted \u221210%, measured \u221213%: error 3 pp.",
    ], 14), { x: 0.6, y: 5.6, w: 12.1, h: 1.1 });

    s.addNotes(
      "About one minute.\n\n" +
      "Each row in our data is one measurement: a group of volunteers, one muscle, one day of bed rest. " +
      "The inputs are the day of the scan, the muscle family, whether the group did a countermeasure, how the muscle was imaged, and whether the value covers a group of muscles. " +
      "The output is the percentage change in muscle size from before bed rest.\n\n" +
      "We have 346 rows, but they come from 32 independent campaigns, because several papers report the same volunteers. " +
      "So we test by holding out one whole campaign, training on the other 31 and predicting the held-out one, 32 times. " +
      "The code checks that no campaign appears on both sides of a split.\n\n" +
      "The score is the mean absolute error in percentage points, averaged so that each campaign counts once. " +
      "Every model is compared with a duration-only curve, which uses the number of days and nothing else."
    );
  }

  // ---------- Slide 3: LLM system view ----------
  {
    const s = add(4);
    s.addText("LLM-based probabilistic classifier: input and output", { placeholder: "title" });

    // left: the request
    const lx = 0.6, ly = 1.35, lw = 5.3, lh = 4.55;
    box(s, { x: lx, y: ly, w: lw, h: lh }, "Request box");
    const k = (key, val) => [
      { text: key, options: { fontFace: MONO, fontSize: 12, bold: true, color: C.text2, breakLine: true } },
      { text: val, options: { fontSize: 13, breakLine: true } },
    ];
    text(s, [
      { text: "Request (one per measurement)", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      { text: " ", options: { fontSize: 4, breakLine: true } },
      ...k("participants", "men only, mean age 35, n = 11"),
      ...k("protocol", "head-down tilt bed rest, 21 days, control group"),
      ...k("measurement", "vastus lateralis, MRI cross-sectional area"),
      ...k("target", "day 21 of bed rest"),
      ...k("typical_curve_other_campaigns", "duration curve fitted on the other 31 campaigns"),
      ...k("observations_other_campaigns", "rows from the other 31 campaigns, most similar first, up to about 26,000 tokens"),
      ...k("question", "Which range will the change fall in? 19 options: below −30%, 2-point ranges up to +4%, +4% and above"),
    ], { x: lx + 0.2, y: ly + 0.15, w: lw - 0.4, h: lh - 0.3, paraSpaceAfter: 1 });

    // middle: the model
    arrow(s, 6.0, 3.7, 0.5, "Arrow request to LLM");
    box(s, { x: 6.55, y: 3.05, w: 1.35, h: 1.3, fill: { color: C.background2 } }, "LLM box");
    text(s, [{ text: "LLM", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      { text: "classifier", options: { bold: true, fontSize: 14, color: C.text2, breakLine: true } },
      { text: "fixed version", options: { fontSize: 11, color: C.accent3 } }],
      { x: 6.55, y: 3.05, w: 1.35, h: 1.3, align: "center", valign: "middle" });
    arrow(s, 7.95, 3.7, 0.5, "Arrow LLM to answer");
    text(s, "Not a chat model: it is built for classification and returns only a probability for each listed option, never free text.", {
      x: 6.0, y: 4.45, w: 2.45, h: 1.3, fontSize: 11, italic: true, align: "center", color: C.accent3 });

    // right: the answer, as returned for this row
    const idx = EX.reps.map((r, i) => i).filter((i) => EX.reps[i] >= -19 && EX.reps[i] <= 3);
    const cats = idx.map((i) => String(EX.reps[i]).replace("-", "−"));
    s.addChart(pres.charts.BAR, [
      { name: "LLM", labels: cats, values: idx.map((i) => EX.llm[i]) },
      { name: "Duration curve", labels: cats, values: idx.map((i) => +EX.curve[i].toFixed(3)) },
    ], {
      x: 8.5, y: 1.35, w: 4.3, h: 3.4, barDir: "col", barGapWidthPct: 30,
      chartColors: [HEX.accent1, HEX.accent4],
      catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent3,
      catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt", legendFontFace: "+mn-lt",
      catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, legendFontSize: 11,
      valGridLine: { color: HEX.accent6, size: 0.75 }, catGridLine: { style: "none" },
      catAxisLabelFrequency: 2, valAxisMinVal: 0, valAxisMaxVal: 0.7, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0",
      showTitle: true, title: FIG("Probability per range"), titleFontSize: 13, titleColor: HEX.dk1, titleBold: true,
      showLegend: true, legendPos: "b",
      showCatAxisTitle: true, catAxisTitle: "Change in muscle size (%, centre of each 2-point range)", catAxisTitleFontSize: 10, catAxisTitleColor: HEX.accent3,
      objectName: "Example answer chart",
    });
    text(s, bullets([
      "Our code averages the range midpoints, weighted by probability (open ends count as −31% and +5%): −6.6%",
      "Measured: −9.4%, an error of 2.8 pp, a typical row",
    ], 13), { x: 8.6, y: 4.85, w: 4.15, h: 1.2 });

    text(s, [
      { text: "Never sent (checked on every request): ", options: { bold: true } },
      { text: "the held-out campaign's measurements, and any paper, author or campaign name. All 430 answers are saved, so every result can be rebuilt without calling the model again." },
    ], { x: 0.6, y: 6.25, w: 12.1, h: 0.6, fontSize: 13 });

    s.addNotes(
      "About a minute and a half.\n\n" +
      "The ML models only saw coded columns. Here we gave each measurement, written out in words, to a newly released language model built for probabilistic classification. " +
      "It is not a chat model that writes text: you give it a described situation and a fixed list of options, and it returns a probability for each option, nothing else.\n\n" +
      "On the left is a real request from our cache. It describes the volunteers, the protocol, the muscle and how it was scanned, and the day. " +
      "It also contains the duration curve fitted on the other 31 campaigns and as many rows from those campaigns as fit, most similar first. " +
      "The question asks which of 19 ranges the change will fall in.\n\n" +
      "On the right is what came back for this row: a probability for each range. We never ask the model for a number. Our code turns the probabilities into a prediction, here minus 6.6 percent against an observed minus 9.4. " +
      "We chose this row because its error is the model's median error.\n\n" +
      "The request never contains the held-out campaign's own data or any name that could identify a paper, and the code checks that on every request. " +
      "Every answer is cached, so all our numbers can be rebuilt without calling the model again."
    );
  }

  // ---------- Slide 4: same comparison with the LLM ----------
  {
    const s = add(4);
    s.addText("Model comparison on held-out campaigns", { placeholder: "title" });
    const rows = [...ml.slice(0, 5), ["Duration curve", 3.16, 0.14], ["LLM prediction", 2.71, 0.43]];
    const names = rows.map((r) => r[0]);
    s.addChart(pres.charts.BAR, [{ name: "MAE", labels: names, values: rows.map((r) => r[1]) }], {
      x: 0.5, y: 1.3, w: 6.2, h: 3.75, ...axis, title: FIG("Error, pp (lower = better)"),
      chartColors: names.map((n) => color(n)), valAxisMinVal: 0, valAxisMaxVal: 4, valAxisMajorUnit: 1, objectName: "MAE chart with LLM",
    });
    s.addChart(pres.charts.BAR, [{ name: "R2", labels: names, values: rows.map((r) => r[2]) }], {
      x: 6.9, y: 1.3, w: 5.9, h: 3.75, ...axis, title: FIG("R² (higher = better)"),
      chartColors: names.map((n) => color(n)), valAxisMinVal: 0, valAxisMaxVal: 0.5, valAxisMajorUnit: 0.1,
      valAxisLabelFormatCode: "0.0", objectName: "R2 chart with LLM",
    });
    text(s, bullets([
      "ML models explain more of the differences (R² 0.27 to 0.39), but none has lower error than the curve.",
      "LLM vs curve, scored the same way: 2.71 vs 3.13 pp, so 0.42 pp smaller; closer in 20 of 32 campaigns.",
      "95% confidence interval of that difference: 0.13 to 0.73 pp. The whole range is above zero, so it is unlikely to be luck.",
    ], 14), { x: 0.6, y: 5.12, w: 12.1, h: 1.4 });
    text(s, "The curve shows 3.13 pp here, not 3.16, because the comparison scores it exactly as it scores the LLM.", {
      x: 0.6, y: 6.55, w: 12.1, h: 0.3, fontSize: 11, italic: true, color: C.accent3 });

    s.addNotes(
      "About a minute and a half.\n\n" +
      "We compared four standard models, ridge regression, random forest, support vector regression and gradient boosting, tuned inside each training fold, and later TabPFN, a neural network pretrained for small tables. " +
      "On the left is the error on the held-out campaign. The duration curve scores 3.16 percentage points and the best ML model, the random forest, 3.18: none of them is lower than the curve. " +
      "On the right, the ML models explain two to three times more variance, because they learn that the calf loses more than the hip. Most of the error left is a shift that applies to a whole campaign, from its scanner, its volunteers or its protocol, and none of our columns describes it. " +
      "We had committed in advance to report this result whichever way it came out.\n\n" +
      "The language model is at the bottom. Its error is 2.71 percentage points, the lowest of all models, and it explains the most variance, 0.43.\n\n" +
      "Compared with the curve on the same rows and scored the same way, the error falls from 3.13 to 2.71, a gain of 0.42 points. The 95 percent confidence interval runs from 0.13 to 0.73, so even the most pessimistic estimate is an improvement. " +
      "It is closer than the curve in 20 of the 32 campaigns. No other method has a gain whose interval stays above zero.\n\n" +
      "If asked about a target: we had set a 15 percent improvement target. The error improvement is 13.3 percent and the probabilistic score improvement 17.7 percent."
    );
  }

  // ---------- Slide 5: validity checks ----------
  {
    const s = add(4);
    s.addText("Robustness and validity checks of the LLM prediction", { placeholder: "title" });
    text(s, "Gain = how much smaller the LLM's error is than the curve's, in pp (full result: 0.42). Each check and its pass rule were fixed before running it.", {
      x: 0.6, y: 1.2, w: 12.1, h: 0.35, fontSize: 13, italic: true, color: C.accent3 });

    const col = (x, groups) => text(s, groups.flatMap(([h, items], gi) => [
      { text: h, options: { bold: true, fontSize: 16, color: C.text2, breakLine: true, paraSpaceBefore: gi ? 10 : 0 } },
      ...bullets(items, 14).map((r, i) => (i === items.length - 1 && gi === groups.length - 1
        ? { ...r, options: { ...r.options, breakLine: false } } : { ...r, options: { ...r.options, breakLine: true } })),
    ]), { x, y: 1.75, w: 5.85, h: 3.2 });

    col(0.6, [
      ["Does it recognise a known campaign?", [
        "Everything identifying a campaign removed: gain still 0.30 pp, interval above zero",
        "Asked to choose the campaign's name from a list of options: right 19% of the time, where guessing gives 8%",
      ]],
      ["Does it use the other campaigns' data?", [
        "Their values shuffled: worse than the curve (gain −1.25 pp)",
        "None of their data given: error 5.85 vs 3.13 pp",
      ]],
    ]);
    col(6.85, [
      ["Is it sensitive to presentation?", [
        "Other campaigns' rows in a different order: error changes 3%",
        "Answer ranges moved by 1 point: error changes 1%",
      ]],
      ["Is it reproducible?", [
        "20 identical requests resent: predictions differ by 0.17 pp on average, well below the 0.42 pp gain",
      ]],
    ]);

    text(s, [
      { text: "Limitations of this result", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      ...bullets([
        "Added after the ML result was known; not in the original plan",
        "Overconfident ranges: its 80% ranges hold the measured value 62% of the time, so we report only its single-number prediction",
        "Given a campaign's own earlier scans, it does not use them",
      ], 14),
    ], { x: 0.6, y: 5.0, w: 12.1, h: 1.6 });

    s.addNotes(
      "About a minute and a quarter.\n\n" +
      "We wrote down each check and its pass rule, and committed them to the repository, before running it.\n\n" +
      "Language models have read many papers, so the model might recognise a published campaign and recall its result. " +
      "With every identifying detail removed, the gain is 0.30 points and its interval stays above zero. " +
      "When we asked the model to choose the campaign's name from a list of options, it was right 19 percent of the time, where guessing gives 8 percent. If asked: of the three campaigns behind most of the gain, it named only one.\n\n" +
      "When we shuffle the other campaigns' values, the gain turns into a loss of 1.25 points, and with no reference data the error rises to 5.85. The gain comes from reading those data.\n\n" +
      "Reordering the rows or shifting the range edges changes the error by 1 to 3 percent. Repeating 20 requests moves the predictions by 0.17 points on average, well under the 0.42 gain.\n\n" +
      "Three limitations: we added this model after the ML result; its 80 percent ranges contain the truth only 62 percent of the time, so we quote only point predictions; and when given a campaign's own earlier scans, it does not use them."
    );
  }

  // ---------- Slide 6: conclusions ----------
  {
    const s = add(5);
    s.addText("Conclusions, limitations and further work", { placeholder: "title" });
    // upper half: conclusions and limitations side by side; lower half: further work
    const head = (t) => ({ text: t, options: { bold: true, fontSize: 20, color: C.text2, breakLine: true, paraSpaceAfter: 8 } });
    text(s, [head("Conclusions"), ...bullets([
      "ML models do not beat a duration-only curve (3.18 vs 3.16 pp)",
      "The LLM classifier lowers the error to 2.71 pp (curve 3.13 pp)",
    ], 18)], { x: 0.6, y: 1.4, w: 5.8, h: 2.6 });
    text(s, [head("Limitations"), ...bullets([
      "32 independent campaigns, mostly young men",
      "No bed-rest data beyond day 119",
      "Group averages, not individual astronauts",
      "Bed rest is not spaceflight",
    ], 18)], { x: 6.9, y: 1.4, w: 5.8, h: 2.6 });
    s.addShape(pres.shapes.LINE, { x: 0.6, y: 4.2, w: 12.1, h: 0, line: { color: HEX.accent5, width: 0.75 }, objectName: "Divider" });
    text(s, [head("Further work"), ...bullets([
      "Muscle-specific modelling: estimate each muscle's susceptibility and combine it with baseline volumes into total lower-limb volume loss",
      "Individual and functional prediction: participant-level data over time, linked to strength and function",
      "Validation on independent campaigns and spaceflight data before any personal risk-assessment tool",
    ], 16)], { x: 0.6, y: 4.4, w: 12.1, h: 2.3 });
    s.addNotes(
      "About thirty seconds.\n\n" +
      "With 32 independent campaigns, standard ML models and TabPFN do not beat a curve that only knows the number of days. " +
      "An LLM-based probabilistic classifier that reads each campaign's description and the other campaigns' data reduces the error from 3.13 to 2.71 points. " +
      "The main limitation is the small sample of 32 campaigns, mostly young men, with no bed-rest data beyond day 119. " +
      "Stress this: every row is a group average, so the model predicts the average loss of a group of volunteers. It cannot yet predict the risk for an individual astronaut.\n\n" +
      "Further work has three steps. First, estimate how susceptible each muscle is relative to a reference muscle, and combine those coefficients with baseline muscle volumes to estimate total lower-limb volume loss; " +
      "the dataset has 30 group time points where three or more muscles were scanned together, across 14 campaigns, so this can be tested. " +
      "Second, move from group averages to individuals with participant-level data over time, and link muscle loss to strength and function. " +
      "Third, validate on independent campaigns and on spaceflight data before building any personal risk-assessment tool. These are plans, not results."
    );
  }

  // ---------- Outro ----------
  {
    const s = add(undefined, "Title");
    s.background = { path: ART("outro-bg.png") };
    s.addImage({ path: LOGO, x: 0.9, y: 0.6, w: 3.2, h: 3.2 * LOGO_RATIO, altText: "DGLRM logo" });
    text(s, [
      { text: "Thank you for listening", options: { fontSize: 46, breakLine: true } },
      { text: "Questions are welcome", options: { fontSize: 26, color: "F2D0A9" } },
    ], { x: 0.9, y: 2.1, w: 9.8, h: 1.9, fontFace: THEME.headFontFace, bold: true, color: "FFFFFF", valign: "bottom", paraSpaceAfter: 10 });
    text(s, "From Bed Rest to Mars  |  64. Jahrestagung der DGLRM", { x: 0.9, y: 4.3, w: 8.4, h: 0.4, fontSize: 16, bold: true, color: "F2D0A9" });
    s.addNotes("Close (Milad). Thank the audience and invite questions. The backup slides that follow answer the questions we expect: part 1 on slides 17 to 19, data and search on 15 and 16, part 2 on 20 to 22.");
  }

  // ---------- Backup slides ----------
  function backup(title, qs, notes, foot) {
    pres.addSection({ title: "Backup" });
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Backup" });
    s.addText(title, { placeholder: "title" });
    s.addText("BACKUP", { x: 10.7, y: 6.95, w: 1.3, h: 0.3, fontSize: 10, bold: true, color: C.accent3, align: "right", margin: 0, isTextBox: true });
    const w = 5.9, h = 2.6, xs = [0.6, 6.8], ys = [1.3, 4.05];
    qs.forEach(([q, items], i) => {
      const x = xs[i % 2], y = ys[Math.floor(i / 2)];
      text(s, [
        { text: q, options: { bold: true, fontSize: 15, color: C.text2, breakLine: true, paraSpaceAfter: 4 } },
        ...bullets(items, 14),
      ], { x, y, w, h });
    });
    if (foot) text(s, foot, { x: 0.6, y: 6.6, w: 10, h: 0.3, fontSize: 11, italic: true, color: C.accent3 });
    s.addNotes(notes);
  }

  backup("Backup: dataset coverage and limitations", [
    ["Did you miss studies?", [
      "Four sources searched from 2013 on, plus 10 older or open-data studies (sources and queries on the next slide)",
      "Not covered: Embase (no access); 1,023 records not yet screened (screening backup)",
    ]],
    ["One campaign dominates the data", [
      "MEDES 90-day: 40% of all rows, a quarter of the modelling data",
      "Scoring gives each campaign one vote; the re-run without it is still to do",
    ]],
    ["Can MRI, CT, DXA and ultrasound be mixed?", [
      "Each method gets its own term: DXA and ultrasound thickness show 5 to 6 pp less loss than CT; MRI volume is within 0.5 pp",
      "The MRI-only re-run is still to do",
    ]],
    ["How reliable is the extraction?", [
      "Every value is traced to its paper and page, table or figure",
      "674 of 742 rows high confidence; 19 read off figures; no independent second extraction",
    ]],
  ], "Backup. Be direct that the three must-show sensitivity analyses (composite-first, without MEDES, MRI only) have not been run yet. Only the weighting check has, and it changed little.");

  // ---------- Backup: search strategy ----------
  {
    pres.addSection({ title: "Backup" });
    const s = pres.addSlide({ masterName: "Content", sectionTitle: "Backup" });
    s.addText("Backup: literature search sources and query", { placeholder: "title" });
    s.addText("BACKUP", { x: 10.7, y: 6.95, w: 1.3, h: 0.3, fontSize: 10, bold: true, color: C.accent3, align: "right", margin: 0, isTextBox: true });
    const hdr = (t, align = "left") => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 }, align } });
    const c = (t, align = "left", bold = false) => ({ text: t, options: { align, bold } });
    text(s, TAB("Sources (searched 4 September 2026)"), { x: 0.6, y: 1.3, w: 5.6, h: 0.32, fontSize: 15, bold: true, color: C.text2 });
    s.addTable([
      [hdr("Source"), hdr("Records", "right")],
      [c("PubMed"), c("1,412", "right")],
      [c("Scopus"), c("1,757", "right")],
      [c("Web of Science Core Collection"), c("1,876", "right")],
      [c("NASA Technical Reports Server"), c("686", "right")],
      [c("Earlier studies and NASA open data"), c("10", "right")],
      [c("Total", "left", true), c("5,741", "right", true)],
    ], { x: 0.6, y: 1.7, w: 5.6, colW: [4.3, 1.3], fontSize: 13, fontFace: THEME.bodyFontFace, color: HEX.dk1, valign: "middle", rowH: 0.38,
      border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: HEX.accent6 }, { type: "none" }], margin: [0.03, 0.1, 0.03, 0.1] });
    text(s, bullets([
      "Journal databases: publications from 2013 onwards",
      "Older work enters through studies we held before the search (9) and one NASA open-data campaign",
      "NASA reports: five short keyword queries, e.g. \"bed rest\" \"muscle volume\"",
      "Not searched: Embase (no institutional access), Cochrane CENTRAL, trial registries, citation chasing",
    ], 13), { x: 0.6, y: 4.5, w: 5.6, h: 2.2 });

    // right: query structure and one string verbatim
    text(s, FIG("Query: two required blocks"), { x: 6.6, y: 1.3, w: 6.1, h: 0.32, fontSize: 15, bold: true, color: C.text2 });
    const blocks = [
      ["Unloading model", "bed rest, head-down tilt, dry immersion, limb suspension, simulated microgravity, disuse"],
      ["Muscle outcome", "atrophy, muscle volume, mass, size, cross-sectional area, lean mass, thickness, main leg muscles"],
      ["Excluded", "rat, mouse, rodent, hindlimb"],
    ];
    const bw = 1.75, gap = 0.425;
    blocks.forEach(([h, t], i) => {
      const x = 6.6 + i * (bw + gap);
      s.addShape(pres.shapes.RECTANGLE, { x, y: 1.72, w: bw, h: 1.6, fill: { color: i === 2 ? C.background2 : HEX.lt1 }, line: { color: HEX.accent5, width: 1, dashType: i === 2 ? "dash" : "solid" }, objectName: "Block " + h });
      text(s, [
        { text: h, options: { bold: true, fontSize: 12, color: C.text2, breakLine: true } },
        { text: t, options: { fontSize: 10.5 } },
      ], { x: x + 0.08, y: 1.78, w: bw - 0.16, h: 1.5, align: "center", valign: "middle" });
      if (i < 2) text(s, i === 0 ? "AND" : "NOT", { x: x + bw, y: 1.72, w: gap, h: 1.6, fontSize: 11, bold: true, align: "center", valign: "middle", color: C.accent1 });
    });
    text(s, "Web of Science string, verbatim", { x: 6.6, y: 3.5, w: 6.1, h: 0.25, fontSize: 11, bold: true, color: C.accent3 });
    s.addShape(pres.shapes.RECTANGLE, { x: 6.6, y: 3.78, w: 6.13, h: 2.45, fill: { color: C.background2 }, line: { type: "none" }, objectName: "Query panel" });
    text(s, [
      'TS=(("bed rest" OR bedrest OR "head-down tilt" OR "head down bed rest" OR HDBR',
      '  OR antiorthostatic OR hypokinesia OR hypodynamia OR "dry immersion"',
      '  OR "limb suspension" OR ULLS OR "simulated microgravity"',
      '  OR "microgravity analog*" OR "spaceflight analog*" OR "mechanical unloading"',
      '  OR "muscle unloading" OR disuse)',
      ' AND',
      ' (atroph* OR "muscle volume" OR "muscle mass" OR "muscle size"',
      '  OR "cross-sectional area" OR PCSA OR "lean mass" OR "muscle thickness"',
      '  OR "muscle wasting" OR deconditioning OR soleus OR gastrocnemius',
      '  OR "triceps surae" OR quadriceps OR "vastus lateralis" OR "knee extensor"))',
      'NOT TS=(rat OR rats OR mice OR mouse OR rodent OR hindlimb OR "hind limb")',
    ].map((l, i, a) => ({ text: l, options: { breakLine: i < a.length - 1 } })),
      { x: 6.72, y: 3.88, w: 5.95, h: 2.3, fontFace: MONO, fontSize: 9, color: C.text1 });

    s.addNotes(
      "Backup. All four strings are in the report appendix, copied from docs/literature-review/search_log.md. " +
      "PubMed uses the same two blocks with MeSH terms and the humans filter; Scopus and Web of Science exclude animal studies in the query. " +
      "The 2013 limit is the main weakness: only two of ten known modelling papers fall inside the window, and the known-item test without the limit was not run. " +
      "Embase was not searched for lack of access; it indexes conference abstracts the other databases miss."
    );
  }

  // ---------- Referee questions on part 1 (slides 3 to 8) ----------
  backup("Backup: screening and study selection", [
    ["Why were 1,023 records not screened?", [
      "Search and screening were time-boxed to one week",
      "They are the rest of the \"maybe\" set and 80 records waiting for a full text",
      "They leave the flow at screening but are not counted as excluded",
    ]],
    ["Who screened, and was it done twice?", [
      "Eligibility criteria were written before screening began",
      "A rule-based triage sorted the records; one person then read the priority set and the top of the \"maybe\" set",
      "No second screener",
    ]],
    ["84 full texts but 52 studies: why so few?", [
      "19 give muscle results only as charts, without a baseline value",
      "4 full texts not available (one conference abstract still used); 11 excluded at full text",
      "These counts are as recorded and still being reconciled with the dataset",
    ]],
    ["Why search only from 2013?", [
      "The search was time-boxed to one week",
      "Older work enters through 9 studies we held before the search; 6 of their campaigns would otherwise be missing",
      "Both known modelling papers from after 2013 were found by all three journal databases",
    ]],
  ], "Backup, part 1 (Niloufar). The 1,023 unscreened records are shown leaving the flow at screening, next to the 2,493 exclusions. If asked, say plainly that they were not screened in time; they were not read and rejected. " +
    "If pressed on the full-text stage: the report's own full-text counts are still being reconciled with the final extraction (it says so in a draft note), so do not claim the full-text numbers add up exactly. " +
    "Known-item test: of the ten modelling papers we knew before the search, only two were published after 2013, and every journal database returned both. The test without the date limit was not run.");

  backup("Backup: dataset expansion and composition", [
    ["The abstract had 15 studies. Did adding 37 change the analysis after seeing data?", [
      "Eligibility criteria were fixed before screening; the dataset was frozen (14 and 19 September) before the final models",
      "The curve shape was chosen by a rule declared before fitting",
    ]],
    ["Slide 5 shows 180 days, but the model stops at day 119. Why?", [
      "The 14 spaceflight rows were measured after landing, so they leave the model with the 264 recovery rows",
      "8 of the 14 are one back muscle (lumbar multifidus)",
    ]],
    ["Mostly young men: does this apply to women and older crews?", [
      "Rows, not people: men only 567, mixed 113, women only 40 (35 of them WISE-2005), not reported 22",
      "Healthy young 692, middle-aged 8, older 42: the results describe young men",
    ]],
    ["What exactly is a row's percentage change?", [
      "Follow-up vs the same group's own baseline; negative means loss",
      "Recomputed from the printed values; where a paper prints the mean of individual changes, that value is kept and labelled",
      "Rows weighted by number of participants: only 8 of 32 campaigns report the spread of the change",
    ]],
  ], "Backup, part 1 (Niloufar). Expansion: the eligibility criteria in the report's Table 2 were written before screening; dataset version 1.0 was frozen on 14 September and 1.1 on 19 September, and every result is fitted on 1.1. " +
    "The rule for the curve: the saturating form is the headline unless another form beats it by at least 4 AIC points. " +
    "Spaceflight: the dataset keeps the spaceflight rows, flagged, but they are post-flight measurements, so the during-unloading filter removes them. " +
    "Weighting: inverse-variance weighting would need the spread of the change, which most papers do not print; the check that compares both weightings moved the duration effect by under 1 pp.");

  backup("Backup: certainty of the muscle-group curves", [
    ["Is each line fitted to its own muscle?", [
      "No. The day-60 values are fitted per muscle group (named muscles, 25 campaigns); the lines share one time course (τ = 60 days)",
      "Separate shapes cannot be estimated: six of nine groups rest on four campaigns or fewer",
    ]],
    ["Why a saturating curve?", [
      "Logarithmic, saturating and spline curves fit equally well (within 1.3 AIC points): the loss slows, but the data cannot say along which curve",
      "By day 119 the curve reaches 86% of its plateau, −17.3% (95% CI −20.9 to −13.7)",
    ]],
    ["How certain are the day-60 values?", [
      "Calf −15.8% (95% CI −18.9 to −12.7); front thigh −10.1% (−13.6 to −6.6); hip rotators −1.9% (−3.9 to 0.2)",
      "Calf vs shin, the ankle's opposing pair: 5.6 pp more loss (2.1 to 9.1), p = 0.003",
      "Hip rotators and outer hip: one campaign each",
    ]],
    ["Is the calf result an artefact of how often it is scanned?", [
      "The order holds after adjusting for duration, countermeasure group and imaging method",
      "Calf: 78 rows from 13 campaigns, the second best-covered group after the front thigh (86 rows, 22 campaigns)",
    ]],
  ], "Backup, part 1 (Niloufar). Be precise about slide 8: the coloured dots at day 60 are the model's estimates for each muscle group, with the intervals shown here. " +
    "The lines are drawn with one shared time course scaled to those values, so they show the shape the model assumes, not a separate fit per muscle. " +
    "The intervals are 95% cluster-robust, which means they account for several rows coming from the same campaign. " +
    "The calf-versus-shin contrast is reported on its own because it does not depend on which muscle is the reference.");

  backup("Backup: significance and relevance of the LLM gain", [
    ["Is 0.42 pp worth anything?", [
      "It is 13% lower error than the curve (3.13 to 2.71 pp)",
      "Small; we present it as a secondary finding",
    ]],
    ["20 of 32 campaigns is close to a coin flip", [
      "Counting wins only: p = 0.22 (sign test)*",
      "Using the size of each win: mean gain 0.42 pp, 95% CI 0.13 to 0.73",
    ]],
    ["Does it rest on a few campaigns?", [
      "3 long MRI campaigns (NASA SPRINT, Berlin BBR2-2, MEDES LTBR) give 56% of the gain; without them 0.20 pp, CI −0.01 to 0.43*",
      "Only SPRINT is recognised, and with campaign details removed the LLM still wins there (3.79 vs 5.92 pp)",
    ]],
    ["Did it read these papers in training? Was it added after the fact?", [
      "Training exposure cannot be ruled out by any test; hiding campaign details and the naming test are the strongest checks available",
      "Added after the ML result, but every check and target was committed before the first answer",
    ]],
  ], "Backup. The two starred numbers are our own calculation from results/forecast_predictions.csv, not in the report. Without the three campaigns that carry most of the gain, the interval touches zero; say so if asked.", "* Our calculation from the saved LLM predictions; not in the report.");

  backup("Backup: ML results and fairness of the comparison", [
    ["Did the ML models get a fair chance?", [
      "Tuned inside each training fold, grouped by campaign; TabPFN needs no tuning",
      "All models saw the same inputs, folds and scoring",
    ]],
    ["Why not add age, sex or countermeasure type?", [
      "32 campaigns leave room for about 3 campaign-level inputs (about 10 campaigns per input)",
      "Age and sex are fixed within a campaign (271 of the 346 modelling rows men-only), so they act as a campaign label; 100 countermeasure rows spread over 9 types",
    ]],
    ["Is the duration curve a straw man?", [
      "Ridge regression uses days, muscle and every other input: 3.28 vs 3.16 pp",
      "Knowing the muscle raises R² but not the error on a new campaign",
    ]],
    ["Would a nearest-neighbour method match the LLM?", [
      "Not tested. If the gain comes from picking similar rows, this is the next control to run",
    ]],
  ], "Backup. The honest gap here is the nearest-neighbour control: we cannot yet say whether a simple similarity method would match the LLM. The 271 men-only rows and 100 countermeasure rows are our count on the 346 modelling rows; the report gives the same point on the 425 lower-limb rows before duplicate composites were removed (347 men-only, 126 countermeasure).");

  backup("Backup: applicability to Mars mission planning", [
    ["A Mars transit is about 180 days; the data stop at 119", [
      "Only one campaign reaches 119 days",
      "A 180-day estimate is planned from the duration curve only, with an uncertainty range, labelled as an assumption",
    ]],
    ["Bed rest is not spaceflight", [
      "Only 14 spaceflight rows, 8 of them one back muscle: too few to test transfer",
    ]],
    ["Which countermeasure works? What about individuals?", [
      "Countermeasure groups lose 3.7 pp less (95% CI 1.5 to 5.9), all types pooled",
      "Every row is a group average; nothing about individual risk",
    ]],
    ["Can anyone reproduce an LLM result?", [
      "Fixed model version; all 430 answers saved, so every number rebuilds without the model",
      "Identical requests differ by 0.17 pp on average",
    ]],
  ], "Backup. The supported planning statements, within 5 to 119 days and for groups: most loss happens in the first weeks, calf muscles need protecting first, and countermeasure groups lose less.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
