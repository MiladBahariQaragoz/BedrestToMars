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

const THEME = {
  name: "Bed Rest to Mars academic",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1A1A", lt1: "FFFFFF", dk2: "1F3A5F", lt2: "F4F5F7",
    accent1: "A23B2A", accent2: "1F3A5F", accent3: "6B7280",
    accent4: "A7AEB8", accent5: "9AA3AE", accent6: "E5E7EB",
    hlink: "1F3A5F", folHlink: "6B7280",
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
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.8,
          fontFace: THEME.headFontFace, fontSize: 28, bold: true, color: C.text2, align: "left", valign: "middle", margin: 0 }, text: "" } },
      { text: { text: "From Bed Rest to Mars  |  DGLRM 2026", options: { x: 0.6, y: 6.95, w: 8, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 6.95, w: 0.5, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
  });

  pres.defineSlideMaster({ title: "Title", background: { color: C.background1 }, objects: [] });

  const SECTIONS = [
    ["Motivation", "Why forecast muscle loss, and why bed rest"],
    ["Data", "Range of unloading, search and dataset"],
    ["Muscles", "Which muscles lose most"],
    ["Models", "Testing setup; ML vs the duration curve"],
    ["LLM forecast", "What it sees, results, checks"],
    ["Conclusions", "Findings, limits, next steps"],
  ];
  const PART = (i) => (i < 3 ? "Part 1" : "Part 2");

  // Progress tracker, bottom-right corner: one dot per agenda section, the current one larger.
  function tracker(s, cur) {
    const x0 = 9.95, step = 0.38, cy = 7.1;
    s.addShape(pres.shapes.LINE, { x: x0, y: cy, w: step * 5, h: 0, line: { color: HEX.accent5, width: 0.75 }, objectName: "Tracker line" });
    for (let i = 0; i < 6; i++) {
      const d = i === cur ? 0.24 : 0.13;
      s.addShape(pres.shapes.OVAL, { x: x0 + i * step - d / 2, y: cy - d / 2, w: d, h: d,
        fill: { color: i === cur ? C.accent1 : i < cur ? C.text2 : C.background1 },
        line: { color: i === cur ? HEX.accent1 : i < cur ? HEX.dk2 : HEX.accent5, width: 0.75 },
        objectName: `Tracker ${i + 1} ${SECTIONS[i][0]}` });
    }
    s.addText(`${cur + 1}  ${SECTIONS[cur][0]}`, { x: 7.3, y: 6.95, w: 2.4, h: 0.3, fontSize: 10, bold: true,
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
  const color = (n, llm) => (n === "Duration curve" ? HEX.dk2 : n === "LLM forecast" ? HEX.accent1 : HEX.accent4);

  // ---------- Title (Intro) ----------
  {
    const s = add(undefined, "Title");
    text(s, [
      { text: "From Bed Rest to Mars:", options: { fontSize: 44, breakLine: true } },
      { text: "Development of a Literature-Derived Machine Learning Framework for Predicting Lower-Limb Muscle Atrophy in Spaceflight Analogues", options: { fontSize: 28 } },
    ], { x: 0.9, y: 1.5, w: 11.5, h: 2.9, fontFace: THEME.headFontFace, bold: true, color: C.text2, valign: "bottom", paraSpaceAfter: 8 });
    text(s, [
      { text: "Niloufar Ahmadymarzdashty", options: {} }, { text: "1", options: { superscript: true } },
      { text: ",  Milad Bahari Qaragoz", options: {} }, { text: "2", options: { superscript: true } },
    ], { x: 0.9, y: 4.7, w: 11.5, h: 0.4, fontSize: 18, color: C.text1 });
    text(s, [
      { text: "1", options: { superscript: true } }, { text: " Independent researcher", options: { breakLine: true } },
      { text: "2", options: { superscript: true } }, { text: " Master's candidate, Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)", options: {} },
    ], { x: 0.9, y: 5.15, w: 11.5, h: 0.6, fontSize: 14, color: C.accent3 });
    text(s, "DGLRM 2026", { x: 0.9, y: 5.9, w: 11.5, h: 0.4, fontSize: 14, color: C.accent3 });
    s.addNotes("Intro (Niloufar). Placeholder: add the opening sentence.");
  }

  // ---------- Agenda ----------
  {
    const s = add(undefined);
    s.addText("Agenda", { placeholder: "title" });
    const xs = [0, 1, 2, 3, 4, 5].map((i) => 1.45 + i * 2.08), cy = 3.75, d = 0.7;
    s.addShape(pres.shapes.LINE, { x: xs[0], y: cy, w: xs[5] - xs[0], h: 0, line: { color: HEX.accent5, width: 1.5 }, objectName: "Agenda line" });
    // part brackets
    [[0, 2, "Part 1: background and data", "Niloufar Ahmadymarzdashty"], [3, 5, "Part 2: modelling and forecasting", "Milad Bahari Qaragoz"]].forEach(([a, b, label, who], k) => {
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
        { x: xs[i] - 0.95, y: cy + 0.6, w: 1.9, h: 1.3, align: "center" });
    });
    text(s, "The marker in the bottom-right corner of each slide shows where we are.", { x: 0.6, y: 6.1, w: 12.1, h: 0.35, fontSize: 13, italic: true, color: C.accent3 });
    s.addNotes("Agenda. Part 1 (co-author): why this matters, why bed rest, the dataset, and which muscles lose most. Part 2: how we tested models, the LLM forecast, and conclusions.");
  }

  // ---------- Co-author's half: placeholders ----------
  placeholder(0, "Why forecast muscle loss?", [
    "Unloaded muscles that hold the body up against gravity lose mass and strength",
    "A transit to Mars takes about six months; the crew must stand, move and work on arrival",
    "Countermeasures are planned before departure, so planners need to know how much of a given muscle is lost after a given number of days",
  ]);
  placeholder(0, "From bed rest to Mars: why use bed-rest data?", [
    "Spaceflight data on leg muscle size are scarce, and the groups measured are small",
    "Bed rest is the established ground model: healthy volunteers lie in bed, usually tilted 6° head-down so that body fluids shift towards the head as in orbit",
    "Three decades of campaigns at NASA, MEDES (Toulouse), Charité (Berlin), DLR (Cologne) and elsewhere",
    "Bed rest imitates weightlessness but is not the same",
  ]);
  placeholder(1, "What range of unloading did we study?", [
    "Unloading models: head-down and horizontal bed rest, dry immersion, one-leg suspension; spaceflight kept separate",
    "At least 5 days of continuous unloading; scans from day 5 to day 119",
    "Leg muscle size measured as volume, cross-sectional area, thickness or lean mass, by MRI, CT, DXA, pQCT or ultrasound",
  ]);
  placeholder(1, "How the dataset was built", [
    "Systematic search of PubMed, Scopus, Web of Science and NASA's technical reports, 2013 onwards: 5,731 records",
    "Plus 9 older studies and one campaign from NASA's open bed-rest archive",
    "Extraction form fixed before extraction: one row per study, group, muscle and scan day",
    "Papers that report the same volunteers merged into one campaign",
  ], "search flow diagram (figures/F1_corpus)");
  placeholder(1, "The final dataset", [
    "742 measurements from 52 studies (1992 to 2026) and 36 independent campaigns",
    "Mostly MRI volumes of named muscles in young men during head-down bed rest",
    "Uneven: the MEDES 90-day campaign gives 40% of rows; 15 campaigns give 5 rows or fewer",
    "Used for modelling: 346 measurements from 32 campaigns",
  ], "campaign timeline (figures/F1b_campaigns)");
  placeholder(1, "What was extracted from each study", [
    "Muscle, day of the scan, planned length of bed rest, % change from before bed rest",
    "Group: control or countermeasure, group size, sex, age",
    "Measurement: imaging method, quantity, position along the muscle",
    "Source of every value: DOI and page, table or figure",
  ]);
  placeholder(2, "Are all muscles affected the same?", [
    "No. Calf muscles (plantar flexors) lose most: −15.8% at day 60, 5.7 pp more than the front thigh",
    "Front thigh, back thigh and shin muscles lose around 10%; hip muscles least",
    "30% of the differences between measurements lie between muscles within the same study",
    "Groups with countermeasures lose 3.7 pp less than controls",
  ], "muscle ranking (figures/F3_muscles)");
  placeholder(3, "From data to forecasts", [
    "Bridge to part 2: the data show that loss depends on time and on the muscle",
    "Next question: can a model forecast the loss in a study it has never seen?",
  ]);

  // ---------- Slide 1: the evaluation setup ----------
  {
    const s = add(3);
    s.addText("Every model is tested on a study it has not seen", { placeholder: "title" });

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
      ...bullets(["Duration curve: uses the number of days only (the baseline)", "4 standard ML models", "TabPFN (pretrained network)", "LLM forecast"], 15),
    ], { x: 6.0, y: y + 0.15, w: 3.05, h: h - 0.3 });
    arrow(s, 9.25, y + h / 2, 0.5, "Arrow model to output");
    box(s, { x: 9.8, y, w: 2.93, h }, "Output box");
    text(s, [
      { text: "Output", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      { text: "How much the muscle has shrunk, in % of its size before bed rest", options: { fontSize: 15, breakLine: true } },
      { text: "Average over the group of volunteers, e.g. \u221210%", options: { fontSize: 14, color: C.accent3 } },
    ], { x: 10.0, y: y + 0.15, w: 2.6, h: h - 0.3 });

    // leave-one-study-out strip
    const sy = 4.75, n = 32, w = 0.27, g = 0.05, held = 13;
    text(s, "Testing: hold out one study, train on the rest, repeat 32 times", { x: 0.6, y: 4.4, w: 8, h: 0.3, fontSize: 15, bold: true, color: C.text2 });
    for (let i = 0; i < n; i++) {
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6 + i * (w + g), y: sy, w, h: 0.27,
        fill: { color: i === held ? C.accent1 : C.accent6 }, line: { color: i === held ? HEX.accent1 : HEX.accent5, width: 0.5 },
        objectName: i === held ? "Test study" : `Training study ${i + 1}` });
    }
    text(s, [
      { text: "Grey: 31 training studies.  ", options: {} },
      { text: "Red: the held-out test study.", options: { color: C.accent1 } },
      { text: "  Each study is held out once.", options: {} },
    ], { x: 0.6, y: 5.15, w: 11, h: 0.3, fontSize: 14 });
    text(s, bullets([
      "Why studies, not measurements: the 346 measurements come from only 32 independent studies, because several papers report the same volunteers.",
      "Score: average error in percentage points (pp). Forecast \u221210%, measured \u221213%: error 3 pp. Each study counts once.",
    ], 14), { x: 0.6, y: 5.6, w: 12.1, h: 1.1 });

    s.addNotes(
      "About one minute.\n\n" +
      "Each row in our data is one measurement: a group of volunteers, one muscle, one day of bed rest. " +
      "The inputs are the day of the scan, the muscle family, whether the group did a countermeasure, how the muscle was imaged, and whether the value covers a group of muscles. " +
      "The output is the percentage change in muscle size from before bed rest.\n\n" +
      "We have 346 rows, but they come from 32 independent studies, because several papers report the same volunteers. " +
      "So we test by holding out one whole study, training on the other 31 and predicting the held-out one, 32 times. " +
      "The code checks that no study appears on both sides of a split.\n\n" +
      "The score is the mean absolute error in percentage points, averaged so that each study counts once. " +
      "Every model is compared with a duration-only curve, which uses the number of days and nothing else."
    );
  }

  // ---------- Slide 2: ML vs the curve ----------
  {
    const s = add(3);
    s.addText("No ML model has lower error than the duration curve", { placeholder: "title" });
    const names = ml.map((r) => r[0]);
    s.addChart(pres.charts.BAR, [{ name: "MAE", labels: names, values: ml.map((r) => r[1]) }], {
      x: 0.5, y: 1.3, w: 6.2, h: 4.15, ...axis, title: "Error on held-out study (pp, lower = better)",
      chartColors: names.map((n) => color(n)), valAxisMinVal: 0, valAxisMaxVal: 4, valAxisMajorUnit: 1, objectName: "MAE chart",
    });
    s.addChart(pres.charts.BAR, [{ name: "R2", labels: names, values: ml.map((r) => r[2]) }], {
      x: 6.9, y: 1.3, w: 5.9, h: 4.15, ...axis, title: "Differences explained (R², higher = better)",
      chartColors: names.map((n) => color(n)), valAxisMinVal: 0, valAxisMaxVal: 0.5, valAxisMajorUnit: 0.1,
      valAxisLabelFormatCode: "0.0", objectName: "R2 chart",
    });
    text(s, bullets([
      "R² is the share of the differences between measurements that a model explains: 0 is none, 1 is all. The ML models explain more (0.27 to 0.39 vs 0.14) because they learn which muscles shrink more.",
      "Their error on a new study is still no lower. Most of the error left is a shift that affects a whole study (its scanner, volunteers, protocol), and none of our inputs describe it.",
    ], 14), { x: 0.6, y: 5.55, w: 12.1, h: 1.3 });

    s.addNotes(
      "About one minute.\n\n" +
      "We compared four standard models, ridge regression, random forest, support vector regression and gradient boosting, tuned inside each training fold. " +
      "We later added TabPFN, a neural network pretrained for small tables.\n\n" +
      "On the left is the error on the held-out study. The duration curve scores 3.16 percentage points and the best model, the random forest, 3.18. None of them is lower than the curve.\n\n" +
      "On the right, the ML models explain two to three times more variance. R squared is computed over all rows together, so it rewards getting the differences between muscles right, and the models do learn that the calf loses more than the hip. " +
      "The error is averaged per study, and most of what remains is a shift that applies to a whole study, from its scanner, its volunteers or its protocol. None of our columns describes that, so 32 studies give the models nothing to learn it from. " +
      "We had committed in advance to report this result whichever way it came out."
    );
  }

  // ---------- Slide 3: LLM system view ----------
  {
    const s = add(4);
    s.addText("LLM forecast: what is sent and what comes back", { placeholder: "title" });

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
      ...k("typical_curve_other_campaigns", "duration curve fitted on the other 31 studies"),
      ...k("observations_other_campaigns", "rows from the other 31 studies, most similar first, up to about 26,000 tokens"),
      ...k("question", "Which range will the change fall in? 19 options: below −30%, 2-point ranges up to +4%, +4% and above"),
      { text: "Field names as sent; \"campaign\" means study.", options: { fontSize: 11, italic: true, color: C.accent3 } },
    ], { x: lx + 0.2, y: ly + 0.15, w: lw - 0.4, h: lh - 0.3, paraSpaceAfter: 1 });

    // middle: the model
    arrow(s, 6.0, 3.7, 0.5, "Arrow request to LLM");
    box(s, { x: 6.55, y: 3.05, w: 1.35, h: 1.3, fill: { color: C.background2 } }, "LLM box");
    text(s, [{ text: "LLM", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      { text: "fixed version", options: { fontSize: 12, color: C.accent3 } }],
      { x: 6.55, y: 3.05, w: 1.35, h: 1.3, align: "center", valign: "middle" });
    arrow(s, 7.95, 3.7, 0.5, "Arrow LLM to answer");

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
      showTitle: true, title: "Answer: probability per range", titleFontSize: 13, titleColor: HEX.dk1, titleBold: true,
      showLegend: true, legendPos: "b",
      showCatAxisTitle: true, catAxisTitle: "Change in muscle size (%, centre of each 2-point range)", catAxisTitleFontSize: 10, catAxisTitleColor: HEX.accent3,
      objectName: "Example answer chart",
    });
    text(s, bullets([
      "Our code turns the probabilities into one forecast, their weighted average: −6.6%",
      "Measured: −9.4%, an error of 2.8 pp. This is a typical row: half of the LLM's errors are smaller.",
    ], 13), { x: 8.6, y: 4.85, w: 4.15, h: 1.2 });

    text(s, [
      { text: "Never sent (checked on every request): ", options: { bold: true } },
      { text: "the held-out study's measurements, and any paper, author or study name. All 430 answers are saved, so every result can be rebuilt without calling the model again." },
    ], { x: 0.6, y: 6.25, w: 12.1, h: 0.6, fontSize: 13 });

    s.addNotes(
      "About a minute and a half.\n\n" +
      "The ML models only saw coded columns. Here we gave each measurement, written out in words, to a newly released language model built for probabilistic classification. " +
      "You give it a described situation and a fixed list of options, and it returns a probability for each option.\n\n" +
      "On the left is a real request from our cache. It describes the volunteers, the protocol, the muscle and how it was scanned, and the day. " +
      "It also contains the duration curve fitted on the other 31 studies and as many rows from those studies as fit, most similar first. " +
      "The question asks which of 19 ranges the change will fall in.\n\n" +
      "On the right is what came back for this row: a probability for each range. We never ask the model for a number. Our code turns the probabilities into a forecast, here minus 6.6 percent against an observed minus 9.4. " +
      "We chose this row because its error is the model's median error.\n\n" +
      "The request never contains the held-out study's own data or any name that could identify a paper, and the code checks that on every request. " +
      "Every answer is cached, so all our numbers can be rebuilt without calling the model again."
    );
  }

  // ---------- Slide 4: same comparison with the LLM ----------
  {
    const s = add(4);
    s.addText("The LLM forecast has the lowest error of all models", { placeholder: "title" });
    const rows = [...ml.slice(0, 5), ["Duration curve", 3.16, 0.14], ["LLM forecast", 2.71, 0.43]];
    const names = rows.map((r) => r[0]);
    s.addChart(pres.charts.BAR, [{ name: "MAE", labels: names, values: rows.map((r) => r[1]) }], {
      x: 0.5, y: 1.3, w: 6.2, h: 3.95, ...axis, title: "Error on held-out study (pp, lower = better)",
      chartColors: names.map((n) => color(n)), valAxisMinVal: 0, valAxisMaxVal: 4, valAxisMajorUnit: 1, objectName: "MAE chart with LLM",
    });
    s.addChart(pres.charts.BAR, [{ name: "R2", labels: names, values: rows.map((r) => r[2]) }], {
      x: 6.9, y: 1.3, w: 5.9, h: 3.95, ...axis, title: "Differences explained (R², higher = better)",
      chartColors: names.map((n) => color(n)), valAxisMinVal: 0, valAxisMaxVal: 0.5, valAxisMajorUnit: 0.1,
      valAxisLabelFormatCode: "0.0", objectName: "R2 chart with LLM",
    });
    text(s, bullets([
      "Same measurements, scored the same way: error 2.71 vs 3.13 pp, so 0.42 pp smaller. Closer than the curve in 20 of 32 studies.",
      "95% confidence interval of that difference: 0.13 to 0.73 pp. The whole range is above zero, so it is unlikely to be luck. No other model achieves this.",
    ], 14), { x: 0.6, y: 5.35, w: 12.1, h: 1.1 });
    text(s, "The curve shows 3.13 pp here, not 3.16, because the comparison scores it exactly as it scores the LLM.", {
      x: 0.6, y: 6.55, w: 12.1, h: 0.3, fontSize: 11, italic: true, color: C.accent3 });

    s.addNotes(
      "About forty-five seconds.\n\n" +
      "These are the same two charts with the language model added at the bottom. Its error is 2.71 percentage points, the lowest of all models, and it explains the most variance, 0.43.\n\n" +
      "Compared with the curve on the same rows and scored the same way, the error falls from 3.13 to 2.71, a gain of 0.42 points. The 95 percent confidence interval runs from 0.13 to 0.73, so even the most pessimistic estimate is an improvement. " +
      "It is closer than the curve in 20 of the 32 studies. No other method has a gain whose interval stays above zero.\n\n" +
      "If asked about a target: we had set a 15 percent improvement target. The error improvement is 13.3 percent and the probabilistic score improvement 17.7 percent."
    );
  }

  // ---------- Slide 5: validity checks ----------
  {
    const s = add(4);
    s.addText("Validity checks on the LLM forecast", { placeholder: "title" });
    text(s, "Gain = how much smaller the LLM's error is than the curve's, in pp (full result: 0.42). Each check and its pass rule were fixed before running it.", {
      x: 0.6, y: 1.2, w: 12.1, h: 0.35, fontSize: 13, italic: true, color: C.accent3 });

    const col = (x, groups) => text(s, groups.flatMap(([h, items], gi) => [
      { text: h, options: { bold: true, fontSize: 16, color: C.text2, breakLine: true, paraSpaceBefore: gi ? 10 : 0 } },
      ...bullets(items, 14).map((r, i) => (i === items.length - 1 && gi === groups.length - 1
        ? { ...r, options: { ...r.options, breakLine: false } } : { ...r, options: { ...r.options, breakLine: true } })),
    ]), { x, y: 1.75, w: 5.85, h: 3.2 });

    col(0.6, [
      ["Does it recognise published studies?", [
        "Everything identifying a study removed: gain still 0.30 pp, interval above zero",
        "Asked to choose the study's name from a list of options: right 19% of the time, where guessing gives 8%",
      ]],
      ["Does it use the other studies' data?", [
        "Their values shuffled: worse than the curve (gain −1.25 pp)",
        "None of their data given: error 5.85 vs 3.13 pp",
      ]],
    ]);
    col(6.85, [
      ["Is it sensitive to presentation?", [
        "Other studies' rows in a different order: error changes 3%",
        "Answer ranges moved by 1 point: error changes 1%",
      ]],
      ["Is it reproducible?", [
        "20 identical requests resent: forecasts differ by 0.17 pp on average, well below the 0.42 pp gain",
      ]],
    ]);

    text(s, [
      { text: "Limitations of this result", options: { bold: true, fontSize: 16, color: C.text2, breakLine: true } },
      ...bullets([
        "Added after the ML result was known, so it was not part of the original plan",
        "Overconfident: when it is 80% sure the value is in a range, it is there only 62% of the time. We therefore report only its single-number forecast.",
        "When also given a study's own earlier scans, it does not make use of them",
      ], 14),
    ], { x: 0.6, y: 5.0, w: 12.1, h: 1.6 });

    s.addNotes(
      "About a minute and a quarter.\n\n" +
      "We wrote down each check and its pass rule, and committed them to the repository, before running it.\n\n" +
      "Language models have read many papers, so the model might recognise a published study and recall its result. " +
      "With every identifying detail removed, the gain is 0.30 points and its interval stays above zero. " +
      "When we asked the model to choose the study's name from a list of options, it was right 19 percent of the time, where guessing gives 8 percent. If asked: of the three studies behind most of the gain, it named only one.\n\n" +
      "When we shuffle the other studies' values, the gain turns into a loss of 1.25 points, and with no reference data the error rises to 5.85. The gain comes from reading those data.\n\n" +
      "Reordering the rows or shifting the range edges changes the error by 1 to 3 percent. Repeating 20 requests moves the forecasts by 0.17 points on average, well under the 0.42 gain.\n\n" +
      "Three limitations: we added this model after the ML result; its 80 percent ranges contain the truth only 62 percent of the time, so we quote only point forecasts; and when given a study's own earlier scans, it does not use them."
    );
  }

  // ---------- Slide 6: conclusions ----------
  {
    const s = add(5);
    s.addText("Conclusions, limitations and further work", { placeholder: "title" });
    const cols = [
      ["Conclusions", [
        "With 32 independent studies, no ML model forecasts better than a curve based on days alone (best 3.18 vs 3.16 pp error).",
        "An LLM that reads each study's description and the other studies' data cuts the error to 2.71 pp (curve 3.13 pp), and this holds under every check.",
      ]],
      ["Limitations", [
        "Only 32 independent studies",
        "No data beyond day 119",
        "Mostly young men (347 of 425 measurements)",
        "Group averages, not individual people",
        "Bed rest imitates spaceflight but is not the same",
      ]],
      ["Further work", [
        "Fix the LLM's overconfident ranges",
        "Check results without the largest study, and with MRI scans only",
        "Extend the forecast to a 180-day mission, with an uncertainty range",
      ]],
    ];
    cols.forEach(([h, items], i) => {
      const x = 0.6 + i * 4.15;
      text(s, [
        { text: h, options: { bold: true, fontSize: 20, color: C.text2, breakLine: true, paraSpaceAfter: 8 } },
        ...bullets(items, 18),
      ], { x, y: 1.45, w: 3.8, h: 5.2 });
    });
    s.addNotes(
      "About thirty seconds.\n\n" +
      "With 32 independent studies, standard ML models and TabPFN do not beat a curve that only knows the number of days. " +
      "A language model that reads each study's description and the other studies' data reduces the error from 3.13 to 2.71 points. " +
      "The limitations and next steps are on the slide; the main one is that 32 studies is a small sample.\n\n" +
      "Thank you."
    );
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

  backup("Backup: is the dataset good enough?", [
    ["Did you miss studies?", [
      "Searched PubMed, Scopus, Web of Science and NASA reports from 2013 on (5,731 records), plus 9 older studies",
      "Not covered: Embase (no access) and 1,023 records not screened in time",
    ]],
    ["One study dominates the data", [
      "MEDES 90-day: 40% of all rows, a quarter of the modelling data",
      "Scoring gives each study one vote; the re-run without it is still to do",
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

  backup("Backup: is the LLM gain real, and does it matter?", [
    ["Is 0.42 pp worth anything?", [
      "It is 13% lower error than the curve (3.13 to 2.71 pp)",
      "Small: we report it as a finding, not the headline",
    ]],
    ["20 of 32 studies is close to a coin flip", [
      "Counting wins only: p = 0.22 (sign test)*",
      "The size of the wins matters: mean gain 0.42 pp, 95% CI 0.13 to 0.73",
    ]],
    ["Does it rest on a few studies?", [
      "3 long MRI studies (NASA SPRINT, Berlin BBR2-2, MEDES LTBR) give 56% of the gain; without them 0.20 pp, CI −0.01 to 0.43*",
      "Only SPRINT is recognised, and with study details removed the LLM still wins there (3.79 vs 5.92 pp)",
    ]],
    ["Did it read these papers in training? Was it added after the fact?", [
      "Training exposure cannot be ruled out by any test; hiding study details and the naming test are the strongest checks available",
      "Added after the ML result, but every check and target was committed before the first answer",
    ]],
  ], "Backup. The two starred numbers are our own calculation from results/forecast_predictions.csv, not in the report. Without the three studies that carry most of the gain, the interval touches zero; say so if asked.", "* Our calculation from results/forecast_predictions.csv; not in the report.");

  backup("Backup: why did ML fail, and was the comparison fair?", [
    ["Did the ML models get a fair chance?", [
      "Tuned inside each training fold, grouped by study; TabPFN needs no tuning",
      "All models saw the same inputs, folds and scoring",
    ]],
    ["Why not add age, sex or countermeasure type?", [
      "32 studies leave room for about 3 study-level inputs (about 10 studies per input)",
      "Age and sex are fixed within a study (347 of 425 rows men-only), so they act as a study label; 126 countermeasure rows spread over 9 types",
    ]],
    ["Is the duration curve a straw man?", [
      "Ridge regression uses days, muscle and every other input: 3.28 vs 3.16 pp",
      "Knowing the muscle raises R² but not the error on a new study",
    ]],
    ["Would a nearest-neighbour method match the LLM?", [
      "Not tested. If the gain comes from picking similar rows, this is the obvious next control",
    ]],
  ], "Backup. The honest gap here is the nearest-neighbour control: we cannot yet say whether a simple similarity method would match the LLM.");

  backup("Backup: can this be used to plan a Mars mission?", [
    ["A Mars transit is about 180 days; the data stop at 119", [
      "Only one study reaches 119 days",
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
