# Code-First Power BI Report Design: Research Learnings

Purpose: the living knowledge base for our blog and POC on a code-first Power BI report design workflow: Excalidraw wireframe, agent-generated HTML/SVG canvas background, HTML visual prototyping via HTML/SVG-returning DAX measures against the live semantic model, production rebuild in Deneb (Vega-Lite), then estate-scale automation through a centralized design language. Compiled 2026-07-02 from 7 research agents plus 5 adversarial fact-check verdicts. Update this file as POC results land.

---

## TL;DR: Top learnings

- **The export "killer feature" claim survived fact-checking but must be reworded.** Certification buys exactly two documented things: rendering in export to PDF/PowerPoint and in subscription emails. The Export data command (Excel/CSV) is a Power BI host feature governed by report and tenant settings, not by certification, and no primary source guarantees it for Deneb. The POC must demonstrate it with screenshots. See Section 3.
- **The HTML Content visual's export failure is structural, and that is confirmed.** Its data view contains only the HTML string measure plus granularity columns, so any data export yields markup, not rows. Separately, the uncertified standard edition renders blank or as an error symbol in PDF/PPT exports and subscription emails. A certified "HTML Content (lite)" edition exists and does render in exports.
- **Deneb is current at 1.9.1 (March 2026), MIT licensed, free, Microsoft certified, and its docs moved to [deneb.guide](https://deneb.guide/).** Deneb 1.8+ runs Vega-Lite 6.x, so agent-generated specs must pin the v6 schema; Deneb 1.9 removed `__identity__`/`__key__` in favor of `__row__`, breaking older templates.
- **Deneb ships a first-party [PBIR Implementation Guide](https://deneb.guide/docs/pbir-guide)** written explicitly for programmatic and LLM generation of Deneb visuals inside PBIR files (visual GUID, stringified `jsonSpec`, D-suffix numeric literals). This is the single most important find for the automation thesis.
- **SVG-from-DAX is now a first-party Microsoft pattern.** The [card visual docs](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-card) ship copy-paste TMDL measures with `dataCategory: ImageUrl` returning SVG data URIs. SVG measures render in six core visuals. DAX measure strings can reach roughly 2.1 million characters; the famous 32,766-character truncation applies to columns only.
- **Canvas backgrounds: render to PNG at exact page pixel size (default 1280x720), set Image fit to Fit and transparency to 0%.** Raw SVG canvas backgrounds have an unresolved clipping bug. Wallpaper (the outspace layer) is documented as excluded from PDF export, so all chrome goes on the canvas background.
- **PBIR became the default report format (Service January 2026, Desktop March 2026) with GA planned Q3 2026,** conversion is one-way, and every file has a public JSON schema. Microsoft explicitly documents batch script edits as a supported scenario. Do not call PBIR "GA" yet.
- **Microsoft's official AI surface leaves our exact niche open.** The Power BI MCP servers cover semantic models only, Copilot cannot use custom visuals or make styling changes, and the June 8, 2026 agent skills explicitly scope out Deneb visuals and SVG measures.
- **Closest prior art is Kurt Buhler at SQLBI** (Excalidraw wireframe to Deneb spec, March 2025; Figma wireframe to Claude Code subagents to deployed report, September 2025). Nobody has published agent-generated HTML/SVG canvas backgrounds or the deliberate HTML-prototype-then-Deneb-production split with export as the migration trigger. That assembled pipeline is our novelty claim; agent report-building per se is not novel.
- **Deneb interactivity works but is mechanically specific:** cross-filtering is an opt-in visual property that injects a `__selected__` field (not Vega-Lite selections), the signal-driven API is Vega only, and cross-filter/tooltips/context menu all require marks that map 1:1 to untransformed dataset rows. Rule: aggregate in DAX, never in the spec.
- **Key numbers:** Deneb dataset default 10,000 rows (Override Row Limit fetches 10k batches); export caps 150,000 rows .xlsx, 30,000 rows .csv, 500,000 rows live-connection .xlsx; Desktop exports summarized CSV only; the embedded JS `exportData` API excludes custom visuals entirely.
- **The design language has four distribution channels:** report theme JSON (colors, fonts, one shared default background, `pbiColor` schemes), Deneb JSON templates with `usermeta` in git, DAX UDF libraries (DaxLib.SVG on daxlib.org), and PBIR `page.json` edits for anything page-specific.

---

## 1. Deneb and Vega-Lite (versions, certification, limits, licensing)

### Versions and timeline
- Current release: **1.9.1** ([GitHub release 2026-03-31](https://github.com/deneb-viz/deneb/releases); AppSource deployment lags roughly 1 to 2 weeks, docs list 2026-04-08). 1.9.1's only change was reverting a focus-mode regression from 1.9.0.
- Docs moved: deneb-viz.github.io now 301-redirects to **[deneb.guide](https://deneb.guide/)**. Cite deneb.guide in the blog.
- Bundled library history ([changelog](https://deneb.guide/docs/changelog)): 1.7.0 (Jul 2024) = Vega 5.30.0 / Vega-Lite 5.19.0; 1.8.0 (Jul 2025) = Vega 6.1.2 / VL 6.1.0; 1.8.2 (Oct 2025) = Vega 6.2.0 / VL 6.4.1; 1.9 (Mar 2026) is a performance release.
- **Deneb 1.9 highlights** ([release blog](https://deneb.guide/blog/1-9-release)): 15 to 40 percent faster visual initialization, 200 to 300 percent faster dataset processing, React 19.2, `pbiColorOrdinal`/`pbiColorLinear`/`pbiColorDivergent` auto-interpolation, and a **breaking change**: `__identity__`/`__key__` dataset fields removed in favor of `__row__`. Older community templates using those fields need migration.
- Deneb 1.8 removed the "Edit Specification Field Mapping" feature (use Monaco find/replace when renaming model fields referenced in specs).
- **Agent implication:** LLMs trained mostly on Vega-Lite 5 examples. Pin `$schema` to Vega-Lite v6 and validate specs before deployment.

### Certification and builds
- Deneb is **Microsoft certified** on AppSource (publisher Coacervo Limited, Daniel Marsh-Patrick). Per [deneb.guide](https://deneb.guide/): "Deneb is certified by Microsoft, meaning that it doesn't access external services or resources and can be exported to PDF or displayed in emails."
- Every GitHub release also offers an **uncertified standalone .pbiviz** with remote URL/data/image loading enabled ([release notes](https://github.com/deneb-viz/deneb/releases/tag/1.9.1.0)). Governance guidance: stick to the AppSource build.
- Certification is re-checked on every version submission ([Certified Power BI visuals, Microsoft Learn](https://learn.microsoft.com/power-bi/developer/visuals/power-bi-custom-visuals-certified)).

### Data limits and performance
- Default dataset cap: **10,000 rows**. The format pane's Data Limit Options > **Override Row Limit** fetches additional data in 10,000-row batches, "subject to resource limits and entirely up to Power BI" ([Dataset docs](https://deneb.guide/docs/dataset)). In PBIR this is `objects.dataLimit.override` (boolean). The Power BI platform dataview cap is 30,000 rows unless the visual windows for more.
- [Performance guidance](https://deneb.guide/docs/performance): SVG is the default renderer; **canvas is recommended for large or uncertain data volumes**. Consolidate marks, bring only needed columns/measures, disable Auto-Apply while editing heavy specs. Render mode is exposed in PBIR as `renderMode` ("svg" default).

### Licensing
- **MIT, entirely free, no paid tier, no license keys** ([repo](https://github.com/deneb-viz/deneb)). Self-funded plus sponsorship. No procurement blocker.

### Templates and the design language
- First-class template workflow (Generate JSON Template, Ctrl+Alt+E) with schema-validated `usermeta` (build, metaVersion=1, provider, dataset placeholders, author info) designed for reuse and source control ([Templates docs](https://deneb.guide/docs/templates)). Templates in git are the distributable design system.
- Template download from the visual rides the tenant "Allow downloads from custom visuals" setting (the file download API, `ExportContent` privilege in [capabilities.json](https://github.com/deneb-viz/deneb/blob/master/capabilities.json)).
- Watch [issue #472](https://github.com/deneb-viz/deneb/issues/472): a v2 template format is an open design issue that could change the `usermeta` contract.

### PBIR Implementation Guide (the automation blueprint)
- First-party guide for authoring Deneb visuals as code in PBIP/PBIR ([PBIR Implementation Guide](https://deneb.guide/docs/pbir-guide)), explicitly aimed at people "using an LLM or other tool to help generate report content."
- Key facts: visual GUID `deneb7E15AEF80B9E4D4F8E12924291ECE89A`; spec lives in `visual.objects.vega[0].properties.jsonSpec` (stringified exactly once); plus `jsonConfig`, `provider` ('vegaLite'), `renderMode`, `enableSelection`/`enableHighlight`/`enableTooltips`, `objects.dataLimit.override`. Gotchas: numeric literals need the `D` suffix, text values single-quoted inside the JSON string, booleans as string literals, all wrapped in `expr.Literal.Value`. Field bindings in `visual.query.queryState.dataset.projections`.

### Vega vs Vega-Lite
- Current Deneb docs do not editorialize; the recommendation comes from the Vega project itself: use Vega-Lite as the primary tool and drop to Vega for advanced cases ([Vega-Lite homepage](https://vega.github.io/vega-lite/)). Deneb's [worked example](https://deneb.guide/docs/simple-example) uses Vega-Lite.
- Caveat for expectations: David Bacci's flagship [Deneb-Showcase](https://github.com/PBI-David/Deneb-Showcase) (~979 stars) is roughly 27 Vega vs 3 Vega-Lite examples, and the advanced cross-filtering API (`pbiCrossFilterApply()`/`pbiCrossFilterClear()`, added 1.7) is Vega only. Vega-Lite covers our core-visual replacements fine, but do not imply Bacci-tier showpieces are Vega-Lite recipes.

### Interactivity recipes (for the Deneb rebuild step)
- **Cross-filtering** ([docs](https://deneb.guide/docs/1.7/interactivity-selection)): opt-in via "Expose cross-filtering values for dataset rows". Deneb injects `__selected__` with three states (on/off/neutral); the spec encodes it visually, e.g. opacity 0.3 when "off". Data Point Limit default 50, range 1 to 250. Marks must preserve untransformed row context.
- **Cross-highlighting** ([docs](https://deneb.guide/docs/1.2/interactivity-highlight)): opt-in "Expose Cross-Highlight Values for Measures"; injects `[measure]__highlight`, `__highlightStatus`, `__highlightComparator` per measure. Canonical pattern: two-layer bar (dimmed base + full-opacity highlight layer). Ready template: [Compact Bar Chart with Cross-Highlight and Cross-Filter](https://github.com/PowerBI-tips/Deneb-Templates).
- **Tooltips** ([docs](https://deneb.guide/docs/interactivity-tooltips)): Power BI tooltip handler on by default; `"tooltip": true` on a mark; report page tooltips served when the datum matches. **Context menu** ([docs](https://deneb.guide/docs/interactivity-context-menu)): drillthrough resolves only when the right-clicked mark represents a single untransformed row.
- **Theme integration** ([Schemes docs](https://deneb.guide/docs/1.7/schemes)): `pbiColorNominal`/`pbiColorOrdinal`/`pbiColorLinear`/`pbiColorDivergent` runtime schemes plus `pbiColor(0)` and named sentiment colors ('negative', 'neutral', 'positive'). Also `pbiFormatAutoUnit` and the `pbiContainer` signal. The agent should emit `pbiColor()` references instead of hard-coded hex so one theme.json restyles the estate.
- Known caveat ([issue #535](https://github.com/deneb-viz/deneb/issues/535)): external cross-filtering filters Deneb's dataset but does not update `__selected__`.

---

## 2. HTML/SVG DAX measures and the HTML Content visual

### The HTML Content visual (two editions)
- Two separate AppSource products by Daniel Marsh-Patrick (same author as Deneb), both MIT ([editions doc](https://html-content.com/docs/visual-editions), [GitHub v1.6.0, Apr 2025](https://github.com/dm-p/powerbi-visuals-html-content)):
  - **Standard**: broadest HTML/CSS/SVG surface, remote images, web fonts, iframes. **Not certified**: renders blank/error in PDF/PPT exports and subscription emails, and dies under the "Add and use certified visuals only" tenant setting.
  - **[HTML Content (lite)](https://marketplace.microsoft.com/en-us/product/power-bi-visuals/coacervolimited1596856650797.htmlcontent_certified?tab=Overview)**: certified. Sanitizes every value ([sanitization doc](https://html-content.com/docs/sanitization)); no `<script>`, `<iframe>`, `<object>`, no external URLs. Docs recommend lite-first, upgrade only if the sanitizer rejects something.
- Sandbox limitations ([limitations doc](https://html-content.com/docs/limitations)): no cookies/localStorage, no popups, iframes need CORS in Service and don't render in Desktop, no externally hosted JS.
- **Interactivity caveat:** tooltips, cross-filtering, and drillthrough (added in [1.4, Aug 2023](https://coacervo.co/html-content-1-4)) require rows in the Granularity data role. **A single-measure HTML-blob design cannot cross-filter.** Interaction design must be proven in the Deneb rebuild, not the HTML prototype. State this honestly in the blog.

### SVG-from-DAX: now a first-party pattern
- Microsoft's [card visual walkthrough](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-card) (ms.date 2026-04-09) ships complete TMDL measures with `dataCategory: ImageUrl` returning URL-encoded SVG data URIs for callout images, category header backgrounds, and hero images (an IBCS-style variance bar). The (new) card visual went **GA November 2025**.
- Encoding conventions from Microsoft's own examples: `%3C` for `<`, `%23` for `#` in hex colors, `%25` for `%`, `%2B` for `+`, single quotes for SVG attributes (DAX strings use double quotes). An unencoded `#` silently truncates rendering.
- Canonical community tutorial: [SQLBI, Kurt Buhler, Sep 2024](https://www.sqlbi.com/articles/creating-custom-visuals-in-power-bi-with-dax/) (table, matrix, new card, Figma-to-DAX workflow, maintenance warnings).
- **Renders in six core visuals**: table, matrix, new card, button slicer, list slicer, image ([Leszkiewicz, Nov 24 2025](https://www.powerofbi.org/2025/11/24/responsive-svg-charts-in-power-bi-core-visuals/)), who also demonstrates responsive SVG via `<foreignObject>` carrying CSS variables and media queries.
- Matrix/table cell images are clamped to the Image size format settings, 8 to 512 px ([matrix format settings](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-matrix-visual-format-settings)).

### Size limits (get this right)
- **Columns / Power Query: 32,766 characters, silent truncation. DAX measures: roughly 2.1 million characters.** ([Chris Webb: max text length](https://blog.crossjoin.co.uk/2019/05/17/maximum-length-text-value-power-bi/), [storing large images](https://blog.crossjoin.co.uk/2019/05/19/storing-large-images-in-power-bi-datasets/)). Generated SVG belongs in measures, not columns. Large assets can be chunked across rows and reassembled with CONCATENATEX.
- A flat "32k limit for SVG measures" is wrong; drafts repeating it must be corrected.

### The 2025 tooling wave (design-language enabler)
- **DAX user-defined functions** (preview Sep 2025) plus the **[DAX Lib registry](https://www.sqlbi.com/blog/marco/2025/12/12/introducing-dax-lib-the-app-store-for-dax-user-defined-functions/)** (launched Dec 12, 2025, 30+ libraries).
- **[DaxLib.SVG](https://daxlib.org/package/daxlib.svg/)** (Jake Duddy, MIT, [docs](https://evaluationcontext.github.io/daxlib.svg/)): nine chart types (Bars, Line, Area, ProgressBar, Pill, Boxplot, Jitter, Heatmap, Violin) as composable DAX UDFs rendering via ImageUrl data URIs. David Bacci's [PBI-Core-Visuals-SVG-HTML](https://github.com/PBI-David/PBI-Core-Visuals-SVG-HTML) shows the same UDF pattern.
- Implication: instead of regenerating raw SVG strings per report, the agent can emit or adopt a shared UDF library deployed estate-wide via TMDL.
- **Honest boundary correction:** "HTML/SVG measures for static chrome only" undersells the post-Nov-2025 state. Microsoft's own docs show data-driven SVG (progress bars, variance bars, status states) as a production pattern. The real boundary is **interactivity and clean data export**, not "static only."
- No primary source exists for an SVG preview inside DAX query view or Tabular Editor; do not claim an in-tooling preview loop.

---

## 3. The export decision rule (verified)

This is the heart of the blog's argument. Five claims went through adversarial fact-checking. Two came back PARTIALLY_TRUE and their corrections are load-bearing.

### Claim 1: "Deneb is certified, therefore users can export its data to Excel/CSV"
**Verdict: PARTIALLY_TRUE.**

**Corrected statement (use this wording):** Deneb is a Microsoft-certified custom visual, but certification is not what enables data export, and Microsoft does not guarantee Export data for any custom visual. Certification grants exactly two documented capabilities: rendering in **export to PDF/PowerPoint** and in **subscription emails**. The **Export data** command is a standard Power BI host feature governed by the report-level Export data setting, tenant admin settings (which override report settings), and permissions (underlying data additionally needs Build permission and tables with unique keys). Deneb plausibly supports it because it binds real model fields through a standard Values data role, but this must be demonstrated empirically in the POC, not cited as a Deneb feature.

Key evidence:
- [deneb.guide](https://deneb.guide/): certification statement mentions PDF export and emails only. No Deneb doc page mentions Export data.
- [Certified Power BI visuals, Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/developer/visuals/power-bi-custom-visuals-certified): benefits listed are PowerPoint export and subscription emails.
- [Export data from a Power BI visualization](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-export-data): export availability is governed by settings and permissions; "Some custom visuals or specific visual configurations don't support data export."
- **Documentation history finding:** until at least October 2024 that same Microsoft page flatly said "Power BI custom visuals and R visuals are not currently supported" for data export; the line was removed in the 2026 rewrite ([archived doc at commit 6b0dd0e](https://github.com/MicrosoftDocs/powerbi-docs/blob/6b0dd0e32debca04b051f91d769326e8f40673f4/powerbi-docs/visuals/power-bi-visualization-export-data.md)). Microsoft never documented certification as enabling data export.
- Scope caveat: in embedded scenarios the [JS exportData API](https://learn.microsoft.com/javascript/api/overview/powerbi/export-data) states "Custom and R visuals, aren't supported." State the claim as **service UI behavior** only.
- Row caps: 150,000 rows .xlsx (matrix "Data with current layout" counts data intersections), 30,000 rows .csv, 500,000 rows live-connection .xlsx, DirectQuery 16 MB. Desktop exports summarized .csv only.

### Claim 2: "The HTML Content visual cannot meaningfully export its underlying data"
**Verdict: CONFIRMED.**

Precise statement: the failure is **structural**, not a documented prohibition. The visual's data roles are content (the HTML string), sampling/granularity, and tooltips ([capabilities.json](https://raw.githubusercontent.com/dm-p/powerbi-visuals-html-content/main/capabilities.json), [data roles doc](https://html-content.com/docs/data-roles)). The numeric series a DAX-generated HTML chart renders exists only inside the markup string, so a summarized export yields raw markup plus grain columns. No community thread demonstrates a working Excel export ([Fabric Community example](https://community.fabric.microsoft.com/t5/Desktop/Rendering-HTML-in-Power-BI-table-visualization/td-p/2590568)). Additionally, the standard edition is uncertified and exports blank to PDF/PPT ([editions](https://html-content.com/docs/visual-editions), [wontfix issue #109](https://github.com/dm-p/powerbi-visuals-html-content)); the certified lite edition fixes export rendering but has the same HTML-string data view, so data export is equally meaningless there.

### Claim 3: "A DAX measure returning an SVG data URI with the ImageUrl data category renders in core visuals"
**Verdict: CONFIRMED.**

Microsoft's [card visual walkthrough](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-card) ships exactly this TMDL. [Display images in a table/matrix/slicer](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-images-tables) confirms Image URL data category and SVG as a supported format. Constraints worth quoting: 32,766-char column truncation vs ~2.1M-char measures ([Chris Webb](https://blog.crossjoin.co.uk/2019/05/19/storing-large-images-in-power-bi-datasets/)), URL-encoding rules (`%23` for `#`), matrix image size clamp of 8 to 512 px, six-visual render list ([powerofbi.org](https://www.powerofbi.org/2025/11/24/responsive-svg-charts-in-power-bi-core-visuals/)).

### Claim 4: "A background image exported at exact page pixel size maps 1:1 to the canvas via Canvas background + Fit"
**Verdict: CONFIRMED.**

The Canvas background dropdown targets the report page ([Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-visual-elements-for-reports)); the theme schema's scaling enum is exactly Normal, Fit, Fill ([official theme JSON schema](https://github.com/microsoft/powerbi-desktop-samples/blob/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.118.json)); with an image at exactly the page size (default 1280x720), Fit is the identity transform so background landmarks align with visual x/y coordinates ([Collaboris guide](https://www.collaboris.com/creating-report-backgrounds-for-power-bi/), [DaTaxan generator](https://dataxan.com/free-power-bi-canvas-background-download-free-power-bi-background-image/), [Lukas Reese templates](https://lukasreese.com/power-bi-dashboard-background-templates/)). Two gotchas: default page transparency is **100%**, so set it to 0% or the image is invisible; and the most common community mistake is choosing Fill instead of Fit.

### Claim 5: "Deneb participates in Power BI interactivity, configured via Vega-Lite selections/signals"
**Verdict: PARTIALLY_TRUE.**

**Corrected statement (use this wording):** Deneb visuals participate fully in Power BI interactivity, but NOT via Vega-Lite selections. Inbound cross-filtering needs no setting (the dataset just gets filtered, though `__selected__` is not updated by external selections per [issue #535](https://github.com/deneb-viz/deneb/issues/535)). Outbound cross-filtering is enabled by a Deneb visual property (disabled by default); Deneb resolves clicked marks itself and exposes the auto-generated `__selected__` field, which the spec uses only for conditional encoding ([Cross-Filtering docs](https://deneb.guide/docs/interactivity-selection)). The signal-driven advanced mode (`pbiCrossFilterApply()`/`pbiCrossFilterClear()`, added 1.7.0) is **Vega only**, not Vega-Lite ([Advanced Cross-Filtering](https://deneb.guide/docs/interactivity-selection-advanced)). Cross-highlighting is opt-in per measure ([docs](https://deneb.guide/docs/interactivity-highlight)). Power BI tooltips (handler on by default, [docs](https://deneb.guide/docs/interactivity-tooltips)) and the right-click context menu with drillthrough ([docs](https://deneb.guide/docs/interactivity-context-menu)) are supported, limited to marks representing a single untransformed dataset row.

### The resulting decision rule (blog wording)
1. Prototype anything code-first in the HTML Content visual (lite where possible) with HTML/SVG DAX measures against the live model. Fast, but interactivity and export cannot be validated there.
2. Any visual whose data users must export, or that must survive PDF/PPT export, subscription emails, or a certified-only tenant, gets rebuilt in Deneb (certified, real field bindings).
3. Static and data-driven chrome (KPI cards, status pills, timestamps) stays as SVG ImageUrl measures in **native** visuals (new card, table, slicers): native visuals are untouched by certification rules entirely.
4. Never place chrome in wallpaper (dropped from PDF export); canvas background only.
5. Disclose the boundaries: Desktop exports CSV only, embedded exportData excludes custom visuals, admin tenant settings override everything.

Why certification gates export rendering at all: certified visuals must implement the rendering events API, which tells the export engine when the visual finished drawing ([Rendering events, Microsoft Learn](https://learn.microsoft.com/power-bi/developer/visuals/event-service)).

Governance map (do not conflate the three export paths):
- **Export data** (visual menu): report setting Export data (none / summarized / summarized + underlying) plus tenant Export to Excel / Export to .csv settings ([admin controls](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-export-data#admin-and-designer-controls-for-exporting), [tenant settings](https://learn.microsoft.com/fabric/admin/service-admin-portal-export-sharing)). Admin settings win on conflict.
- **Export to PDF/PPT and subscriptions**: certification-gated rendering ([end-user PDF](https://learn.microsoft.com/power-bi/collaborate-share/end-user-pdf), [exportToFile](https://learn.microsoft.com/power-bi/developer/embedded/export-to)).
- **Custom visual file downloads** (Deneb templates, .tmplt): tenant setting "Allow downloads from custom visuals", **disabled by default**, separate from Export and sharing settings ([organizational visuals](https://learn.microsoft.com/fabric/admin/organizational-visuals), [file download API](https://learn.microsoft.com/power-bi/developer/visuals/file-download-api)).
- Tenant kill switch: "Add and use certified visuals only" blocks uncertified visuals from rendering at all; the organizational store is the escape hatch.

---

## 4. Canvas backgrounds and wireframing

### Official behavior
- Two surfaces ([Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-visual-elements-for-reports)): **Canvas background** (the page, foreground) and **Wallpaper** (outspace, furthest back). Defaults: page white at 100% transparency, wallpaper white at 0%. Above 50% page transparency an edit-mode-only dotted boundary appears.
- **Export to PDF does not include wallpaper** (documented caveat). All generated chrome goes on the canvas background.
- Page sizes ([display settings](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-report-display-settings)): default 1280x720 (16:9); presets 1920x1080, 2560x1440, 3840x2160; fully custom pixel dimensions; default page size settable in theme JSON. No official DPI concept anywhere; everything is raw pixels.
- **PBIR mechanics** ([projects-report](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [page schema v2.1.0](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition/page)): background = `objects.background`, wallpaper = `objects.outspace` in page.json; image scaling enum Normal, Fit, Fill, Tile; image referenced via ResourcePackageItem (PackageName 'RegisteredResources', PackageType 1), physical file in `StaticResources/RegisteredResources/`, registered in `resourcePackages` in definition/report.json; transparency is a D-suffixed literal (`"0D"`). Microsoft lists logo swaps and batch edits as supported RegisteredResources scenarios.
- **Naive-injection gotcha:** setting only the image without also setting transparency to `0D` looks like a failure because of the 100% default.
- Theme JSON can set ONE report-wide default background (`visualStyles.page.*` with base64 data URL and scaling), but **per-page targeting via theme does not work** ([SQLBI, Buhler](https://www.sqlbi.com/articles/re-using-visual-formatting-in-and-across-power-bi-reports/), [Fabric Community thread](https://community.fabric.microsoft.com/t5/Desktop/Per-page-background-image-with-JSON-theme/td-p/4147497)). Per-page = PBIR page.json edits.
- **SVG canvas-background bug:** SVG uploads clip / fail to fully render in Desktop and Service ([Fabric Community issue, May 2023, still "Investigating"](https://community.fabric.microsoft.com/t5/Issues/Canvas-background-is-with-SVG-files/idi-p/3242517)). Workflow consequence: the agent renders its HTML/SVG canvas to **PNG at exact page size** (headless browser screenshot), Fit, transparency 0%. Retest the bug in the POC.
- Sizing consensus ([Lukas Reese guide](https://lukasreese.com/2025/08/19/power-bi-background-image-guide-tool/)): exact-size PNG (1280x720 or standardize on 1920x1080); PNG over JPEG for crisp edges and transparency.

### The traditional workflow we contrast against
- **PowerPoint pattern** (the canon): slide sized to canvas, shapes for visual zones, export PNG, upload as background. Most-cited exemplar: [Guy in a Cube featuring Mara Pereira, May 11 2023](https://www.youtube.com/watch?v=pKkav_W-jiQ); also [Coeo](https://blog.coeo.com/using-powerpoint-to-create-and-standardise-your-power-bi-reports) and [DaTaxan](https://dataxan.com/insights/make-beautiful-power-bi-report-with-layouts-created-from-powerbi/). Pain points: manual re-export on every layout change, slide-size mismatch.
- **Figma pattern**: 1280x720 frame, layout blocks, export PNG ([DataBear, Mar 2026](https://databear.com/power-bi-wireframing-figma/)); free community assets ([Power BI Backgrounds](https://www.figma.com/community/file/1108563240558755576/power-bi-backgrounds), [Power BI UI Kit](https://www.figma.com/community/file/1221509435701072015/power-bi-ui-kit)); wireframing as stakeholder alignment ([BIBB, Oscar Martinez](https://bibb.pro/post/wireframing-in-power-bi/)).
- **Design rule to adopt:** never embed critical or data-driven text in the background image; data text lives in visuals/SVG measures, background carries only static chrome.
- **Generator prior art** (template-based, no agent, no PBIR automation): [Zerg00s/Power-BI-Backgrounds](https://github.com/Zerg00s/Power-BI-Backgrounds) (MIT SVG generator), [DaTaxan free generator](https://dataxan.com/free-power-bi-canvas-background-download-free-power-bi-background-image/), and [Lukas Reese's four-way comparison, Dec 2025](https://lukasreese.com/2025/12/22/four-ways-to-create-power-bi-backgrounds/) (manual vs PowerPoint vs Figma vs generator). Nobody connects generation to PBIR automation or a semantic design system. That is our gap.

---

## 5. Code-first tooling (PBIP, PBIR, TMDL, REST APIs, CLIs)

### PBIR status (get the wording exact)
- **Default everywhere, still technically preview.** New Service reports default to PBIR from January 2026; Desktop default from the March 2026 release (2.152); **GA planned Q3 2026**, when PBIR becomes the only supported format ([official transition post](https://powerbi.microsoft.com/en-us/blog/pbir-will-become-the-default-power-bi-report-format-get-ready-for-the-transition/), [projects-report](https://learn.microsoft.com/power-bi/developer/projects/projects-report#pbir-format)). Do not call PBIR GA as of July 2026.
- Conversion is **one-way** (Desktop keeps a 30-day backup). Tenant opt-out during preview: "Automatically convert and store reports in the Power BI enhanced metadata format (PBIR)".
- Limits: 1,000 pages/report, 1,000 visuals/page, 300 MB total, authoring degrades above ~500 files.
- PBIR is "a publicly documented format that supports modifications from non-Power BI applications"; every file has a [public JSON schema](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definitionProperties). Microsoft's listed scenarios include "apply a batch edit across all visuals using a script" ([enhanced report format](https://learn.microsoft.com/power-bi/developer/embedded/projects-enhanced-report-format)). This is the official license for step 5 of our workflow.

### REST APIs
- [Report getDefinition/updateDefinition](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/report-definition): PBIR is the default returned format; updateDefinition takes the definition/ folder as base64 parts. Calls are long-running operations (202 Accepted, poll). Rebinding via definition.pbir `byConnection`.
- [Semantic model definitions](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/semantic-model-definition) default to **TMDL**.

### TMDL
- TMDL view GA in Desktop September 2025 (2.147); TMDL View on the web in preview March 2026; TMDL syntax highlighting for DAX UDFs ([TMDL view](https://learn.microsoft.com/power-bi/transform-model/desktop-tmdl-view), [update archive](https://learn.microsoft.com/power-bi/fundamentals/desktop-latest-update-archive)). Our HTML/SVG measures and the shared UDF design library live here.

### Microsoft's agentic stack (June 2026, preview)
- **Power BI Agentic** ([overview](https://learn.microsoft.com/power-bi/developer/agentic/power-bi-agentic-overview), [announcement Jun 8 2026](https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/AI-Powered-Power-BI-reporting-From-design-to-deployment-with/ba-p/5190703)): agent skills via [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) (powerbi-report-authoring, report-design, report-planner, report-management; PBIR only), npm CLIs `@microsoft/powerbi-report-authoring-cli` (validate, catalog, previews) and `@microsoft/powerbi-desktop-bridge-cli` (open/reload/screenshot against a local Desktop server), plus the [Power BI Modeling MCP](https://github.com/microsoft/powerbi-modeling-mcp). Claude Code explicitly supported.
- **Crucial scope note:** the official report-authoring skill states Deneb visuals, SVG measures, and model changes are **not in scope**. Our workflow occupies exactly that gap.

### Fabric CLI and git
- [Fabric CLI](https://microsoft.github.io/fabric-cli/) (fab): GA May 2025, open source Oct 2025; v1.5 (Mar 2026) added `deploy` (fabric-cicd) and AI context files for Copilot, Claude, Cursor; latest v1.6.1 (Apr 2026). **No dedicated PBIR report export/import**: report round-trips go through REST or fabric-cicd.
- [Git integration](https://learn.microsoft.com/fabric/cicd/git-integration/source-code-format) syncs the same PBIP folder formats; once a report is PBIR in the service, git exports PBIR. PR review of visual.json diffs is the governance story.

### Community tooling (recommend / avoid)
- **Recommend:** [pbir.tools / pbir-cli](https://github.com/maxanatsko/pbir.tools) (v0.9.25 Jun 2026, beta, "built for humans, optimized for agents"; add visual / set / validate / publish); [data-goblin/power-bi-agentic-development](https://github.com/data-goblin/power-bi-agentic-development) (Kurt Buhler's Claude Code plugin marketplace incl. deneb-visuals skill and deneb-reviewer agent, the stack our POC environment runs); [semantic-link-labs ReportWrapper](https://semantic-link-labs.readthedocs.io/en/stable/sempy_labs.report.html) (requires PBIR); [PBIR-Utils](https://github.com/akhilannan/PBIR-Utils).
- **Avoid for reports:** legacy pbi-tools cannot extract report sections from PBIR PBIX ([issue #425](https://github.com/pbi-tools/pbi-tools/issues/425), open, no maintainer response). Core sempy's `update_report_from_reportjson` is PBIR-Legacy only; mixed estates need format detection.

---

## 6. Prior art and blog positioning

### What is NOT novel (name and cite these)
- **Agent-built Power BI reports:** Microsoft's own [June 8 2026 agent skills](https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/AI-Powered-Power-BI-reporting-From-design-to-deployment-with/ba-p/5190703) with an edit > validate > reload > screenshot loop; [Kurt Buhler, SQLBI Sep 2025](https://www.sqlbi.com/articles/introducing-ai-and-agentic-development-for-business-intelligence/): Claude Code subagents from a Figma wireframe to a deployed report.
- **Wireframe-first AI Deneb specs:** [Buhler, SQLBI Mar 2025](https://www.sqlbi.com/articles/using-ai-assistance-to-create-power-bi-custom-visuals/) starts with an Excalidraw wireframe, then Claude generates Vega-Lite for Deneb. His tested conclusion tempers any "10x faster" framing: AI visuals "still require significant effort, time investment, knowledge, and critical thought."
- **NL-to-PBIR generation:** [Lukas Reese's PBIR Report Builder Claude skill](https://lukasreese.com/2026/03/14/pbir-report-builder-claude-skill/) reports **85 to 90 percent first-try PBIR validity** (our quantitative baseline to beat with a validation loop); [pbi-cli](https://community.fabric.microsoft.com/t5/Power-BI-Community-Blog/pbi-cli-Gi-Claude-Code-the-Power-BI-Skills-It-Needs-Semantic/ba-p/5146283).
- **Claude + HTML measures + Deneb (chat-based):** [Mike Dion, f9finance, Jun 2026](https://www.f9finance.com/custom-power-bi-visuals-with-claude/): closest match to our HTML prototype stage, but copy-paste chat, no wireframe, no prototype-to-Deneb migration logic. His caveats to reuse: CSS renders inconsistently Desktop vs Service; Vega-Lite field names must match exactly.
- **Excalidraw + agents (reverse direction):** [Alexander Korn, Mar 2026](https://actionablereporting.com/2026/03/09/power-bi-report-prototyping-with-ai-from-35-pages-to-18-in-10-minutes/): agent turns an existing 35-page report into an Excalidraw redesign. Proves Excalidraw JSON is agent-friendly; nobody has published the forward direction.
- **Wireframe-to-PBIR as a product:** [Draft BI](https://draftbi.com/) (SaaS, 37 native visual types, PBIR + theme export). GUI tool, no agent, no HTML/Deneb stages.
- **Hand-built HTML/SVG chrome and AI Vega-Lite:** [Kerry Kolosko's galleries](https://kerrykolosko.com/category/custom-visualisations/html-content-visual/), Workout Wednesday HTML/CSS weeks (2024 w47, 2025 w44), [GPT-5 + Deneb walkthrough](https://www.dynamicwebtraining.com.au/blog/using-chatgpt-5-and-denab-for-custom-power-bi-visuals).
- **Copilot's structural limits** are our cleanest "why not Copilot" answer: custom visuals unsupported, styling/formatting changes unsupported ([Copilot report creation](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-create-reports)). MCP servers cover semantic models only ([MCP overview](https://learn.microsoft.com/en-us/power-bi/developer/mcp/mcp-servers-overview)).

### What IS novel (claim narrowly)
1. Agent-generated bespoke HTML/SVG **canvas background** as report chrome (no publication found on AI-generated canvas backgrounds).
2. The deliberate **HTML-prototype-then-Deneb-production split** with export fidelity as the explicit migration trigger.
3. **Estate-scale automation from a centralized design language** (theme JSON + Deneb templates + DAX UDF library + PBIR injection) rather than one-off report generation.
4. Positioning bonus: Microsoft's official skills exclude Deneb and SVG measures, so our pipeline is complementary, not competing; a nice narrative hook is that one developer (Daniel Marsh-Patrick) authors both the prototype host (HTML Content) and the production host (Deneb).

---

## 7. Open questions to test in the POC

Export (the load-bearing demo):
1. Does Export data appear on a Deneb visual in Desktop and Service, offering Summarized (and Underlying with Build permission), and does the exported table exactly match the Values field well? Screenshot both against the same data as a native visual.
2. Does an aggregated Vega-Lite spec export the pre-transform data view rather than what is drawn?
3. With Override Row Limit and 40k rows loaded, does Export data return all fetched rows or only the first window? Where does fetchMoreData stop on an F-SKU?
4. What exactly does Export data produce on HTML Content (standard, one-measure blob) vs HTML Content (lite, with Granularity rows) vs a table with an ImageUrl SVG measure (raw data URI as a column)? Capture for the "why we rebuild in Deneb" section.
5. Does export to PDF/PPT render Deneb correctly while uncertified HTML Content on the same page drops to an error symbol? Does browser Print behave differently (docs are silent on print)?
6. Does HTML Content (lite) actually render in PDF/PPT exports and subscription emails, letting certified static chrome skip the Deneb rebuild?
7. Does the report-level Export data setting hide the command on Deneb identically to native visuals?

Canvas background:
8. Is the SVG canvas-background clipping bug still reproducible in 2026 builds, or can we ship raw SVG and skip the PNG render step?
9. Does export to PDF/PPT include the canvas (page) background image, as opposed to wallpaper which is documented as excluded?
10. Does a 2x-resolution PNG (2560x1440 for a 1280x720 page) with Fit look sharper on high-DPI than exact-size?
11. Can the agent write the PNG into StaticResources/RegisteredResources, register it in definition/report.json, set objects.background plus transparency 0D in page.json, and survive a Desktop open-validate-save round trip?
12. Theme-level page background vs PBIR page.json background: which wins, and is precedence stable enough to build the override model on?
13. Do all four PBIR scaling values (Normal, Fit, Fill, Tile) round-trip for canvas background, given the UI shows only three?

Agent authoring loop:
14. Does the full PBIR authoring loop work end-to-end: agent writes Deneb visual.json per the PBIR Implementation Guide, Desktop renders without opening Deneb's editor? Test against Deneb 1.9.1 with pbir-cli.
15. What happens when Desktop or updateDefinition receives a schema-violating visual.json (silent fix, load failure, service 400)? Document the failure modes.
16. Do Claude-generated Vega-Lite specs validate against the VL 6.4.x schema, or do they emit VL 5 idioms needing a lint/validate step? Measure our first-try validity with the validation loop vs Reese's 85 to 90 percent no-loop baseline.
17. Does the Desktop Bridge screenshot correctly render Deneb and HTML custom visuals, enabling the agent's visual verification loop?
18. Can our Excalidraw wireframe JSON be translated automatically into the Design Brief YAML that Microsoft's powerbi-report-authoring skill consumes (complementary positioning)?

Deneb rebuild specifics:
19. How do VL 5-era community templates (Kolosko 2021 KPI cards, PowerBI-tips) behave under Deneb 1.9's VL 6 runtime; what migration should the agent automate?
20. KPI card boundary: at what point does a static SVG-measure card need to become a Deneb card (export? tooltip? cross-filter source?), and can a text-mark-only Deneb card still resolve context menus?
21. Can grand totals / subtotals be injected via DAX union rows without breaking row-context interactivity (thysvdw left this unsolved)?
22. Do pbiColorNominal/pbiColor() pick up a theme JSON swap live, enabling a single-file design-language restyle demo?
23. SVG vs canvas renderer timings at 1k / 10k / 50k rows for a concrete recommendation.

Measures and chrome:
24. At what character count do the six core visuals stop rendering a measure-generated SVG data URI, and does Desktop vs Service differ?
25. Does the foreignObject + CSS media query responsive-SVG technique survive Service sanitization in all six visuals and in PDF/PPT export?
26. Does the HTML prototype survive a "certified visuals only" tenant, and are SVG ImageUrl measures in native visuals the tenant-proof fallback?
27. Per-row SVG measure performance in a large matrix; does consolidating KPIs into one new card measurably cut load time?

Housekeeping:
28. Track [Deneb issue #472](https://github.com/deneb-viz/deneb/issues/472) (v2 template format) before publishing the versioning section; confirm which Deneb version tenants actually have when the blog ships (AppSource lag ~1 to 2 weeks).
29. Benchmark estate deployment paths on 3 to 5 reports: local PBIP + git integration vs REST updateDefinition (LRO polling) vs fab deploy / fabric-cicd vs semantic-link-labs notebook.
30. Does pbir-cli publish handle byPath-to-byConnection rebinding correctly against a workspace-hosted model?

---

## Resource directory

### Deneb and Vega-Lite
- [Deneb documentation](https://deneb.guide/): primary source for certification, dataset, performance, templates, changelog. Cite this, not the old GitHub Pages URL.
- [Deneb Change Log](https://deneb.guide/docs/changelog): canonical version history including bundled Vega/Vega-Lite per release.
- [PBIR Implementation Guide](https://deneb.guide/docs/pbir-guide): first-party spec for programmatically generating Deneb visuals in PBIR; the automation blueprint.
- [Dataset docs](https://deneb.guide/docs/dataset): 10,000-row default and Override Row Limit, quoted exactly.
- [Performance Considerations](https://deneb.guide/docs/performance): official SVG vs canvas guidance.
- [Templates docs](https://deneb.guide/docs/templates): usermeta schema, the versioning mechanism for the design language.
- [Cross-Filtering](https://deneb.guide/docs/interactivity-selection), [Cross-Highlighting](https://deneb.guide/docs/interactivity-highlight), [Tooltips](https://deneb.guide/docs/interactivity-tooltips), [Context Menu](https://deneb.guide/docs/interactivity-context-menu), [Theme Schemes](https://deneb.guide/docs/1.7/schemes): the interactivity and theming recipe pages.
- [deneb-viz/deneb releases](https://github.com/deneb-viz/deneb/releases): dates, certified vs standalone builds.
- [Vega-Lite homepage](https://vega.github.io/vega-lite/): official VL-first, Vega-escape-hatch guidance.
- [Deneb on AppSource](https://marketplace.microsoft.com/en-us/product/power-bi-visuals/coacervolimited1596856650797.deneb): install source; verify the certified badge manually (page blocks automated fetch).

### Deneb galleries and templates
- [Davide Bacci Deneb-Showcase](https://github.com/PBI-David/Deneb-Showcase): the flagship gallery (~979 stars, mostly Vega); Deneb's ceiling.
- [PowerBI-tips Deneb-Templates](https://github.com/PowerBI-tips/Deneb-Templates): 60 importable templates including Conditional KPI Cards and the cross-highlight + cross-filter bar.
- [vegaviz (CodeWithBehnam)](https://github.com/CodeWithBehnam/vegaviz): 269+ specs with Deneb usermeta targeting Deneb 1.9 / VL 6; the most automation-friendly gallery.
- [Kerry Kolosko Deneb templates](https://kerrykolosko.com/portfolio-category/deneb-templates/) and [Conditional KPI Cards](https://kerrykolosko.com/conditional-kpi-cards-with-deneb/): worked KPI card recipe.
- [thysvdw: The one with the matrix](https://thysvdw.github.io/posts/matrix/) and [Stories of Data: better matrix](https://www.storiesofdata.com/portfolio/building-a-better-matrix-visual-with-deneb-in-power-bi): matrix recipes and their honest limits.
- [PBI Queryous series](https://medium.com/@pbiqueryous/power-bi-a-series-in-deneb-vega-lite-data-visualisation-6ebf88c23845): beginner-to-intermediate Vega-Lite tutorials.
- [Deneb community resources index](https://deneb.guide/community/resources): the official jumping-off page.

### HTML Content and SVG measures
- [HTML Content docs](https://html-content.com/): editions, [sanitization](https://html-content.com/docs/sanitization), [limitations](https://html-content.com/docs/limitations), [data roles](https://html-content.com/docs/data-roles); primary source for the prototype host.
- [HTML Content 1.4 features (Coacervo)](https://coacervo.co/html-content-1-4): the Granularity-role dependency for interactivity.
- [Microsoft Learn: card visual SVG TMDL walkthrough](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-card): first-party SVG-from-DAX proof.
- [Microsoft Learn: images in table/matrix/slicer](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-images-tables): ImageUrl data category and supported formats.
- [SQLBI: Creating custom visuals with DAX (Buhler)](https://www.sqlbi.com/articles/creating-custom-visuals-in-power-bi-with-dax/): canonical SVG-measure tutorial.
- [DaxLib.SVG](https://daxlib.org/package/daxlib.svg/) and [docs](https://evaluationcontext.github.io/daxlib.svg/); [SQLBI: Introducing DAX Lib](https://www.sqlbi.com/blog/marco/2025/12/12/introducing-dax-lib-the-app-store-for-dax-user-defined-functions/): the UDF design-language ecosystem.
- [Responsive SVG in core visuals (Leszkiewicz)](https://www.powerofbi.org/2025/11/24/responsive-svg-charts-in-power-bi-core-visuals/): six-visual list and foreignObject technique.
- [Chris Webb: max text length](https://blog.crossjoin.co.uk/2019/05/17/maximum-length-text-value-power-bi/) and [storing large images](https://blog.crossjoin.co.uk/2019/05/19/storing-large-images-in-power-bi-datasets/): the 32,766 vs ~2.1M character facts.
- [David Bacci: PBI-Core-Visuals-SVG-HTML](https://github.com/PBI-David/PBI-Core-Visuals-SVG-HTML): advanced chrome examples closest to our agent-generated chrome.

### Export rules and governance
- [Export data from a Power BI visualization](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-export-data): row caps, summarized vs underlying, admin/designer hierarchy, custom-visual caveat.
- [Certified Power BI visuals](https://learn.microsoft.com/power-bi/developer/visuals/power-bi-custom-visuals-certified): what certification actually grants.
- [Export reports to PDF](https://learn.microsoft.com/power-bi/collaborate-share/end-user-pdf) and [exportToFile API](https://learn.microsoft.com/power-bi/developer/embedded/export-to): uncertified visuals render error symbols.
- [Embedded exportData JS API](https://learn.microsoft.com/javascript/api/overview/powerbi/export-data): custom visuals excluded programmatically.
- [Export and sharing tenant settings](https://learn.microsoft.com/fabric/admin/service-admin-portal-export-sharing) and [organizational visuals admin](https://learn.microsoft.com/fabric/admin/organizational-visuals): every switch that gates export, plus certified-only and downloads-from-custom-visuals.
- [File download API](https://learn.microsoft.com/power-bi/developer/visuals/file-download-api): the separate visual-initiated download path (Deneb templates).
- [Rendering events API](https://learn.microsoft.com/power-bi/developer/visuals/event-service): the mechanical why behind certification-gated export rendering.
- [Report settings (Export data)](https://learn.microsoft.com/power-bi/create-reports/power-bi-report-settings): the per-report designer control.
- [Archived pre-2026 export doc](https://github.com/MicrosoftDocs/powerbi-docs/blob/6b0dd0e32debca04b051f91d769326e8f40673f4/powerbi-docs/visuals/power-bi-visualization-export-data.md): proof the "custom visuals not supported" line existed until the 2026 rewrite.

### Canvas backgrounds and wireframing
- [Visual elements for reports](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-visual-elements-for-reports): canvas vs wallpaper, defaults, PDF wallpaper caveat.
- [Page size and settings](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-report-display-settings): 1280x720 default, presets to 4K.
- [Report theme JSON schema](https://github.com/microsoft/powerbi-desktop-samples/blob/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.118.json): the Normal/Fit/Fill scaling enum.
- [SVG background bug thread](https://community.fabric.microsoft.com/t5/Issues/Canvas-background-is-with-SVG-files/idi-p/3242517) and [per-page theme background thread](https://community.fabric.microsoft.com/t5/Desktop/Per-page-background-image-with-JSON-theme/td-p/4147497): the two community findings that shape our render pipeline.
- [SQLBI: re-using visual formatting (Buhler)](https://www.sqlbi.com/articles/re-using-visual-formatting-in-and-across-power-bi-reports/): themes as design-language carriers.
- [Guy in a Cube + Mara Pereira](https://www.youtube.com/watch?v=pKkav_W-jiQ), [Coeo PowerPoint workflow](https://blog.coeo.com/using-powerpoint-to-create-and-standardise-your-power-bi-reports), [DataBear Figma workflow](https://databear.com/power-bi-wireframing-figma/), [BIBB wireframing](https://bibb.pro/post/wireframing-in-power-bi/): the traditional canon we contrast against.
- [Lukas Reese: background image guide](https://lukasreese.com/2025/08/19/power-bi-background-image-guide-tool/) and [four ways compared](https://lukasreese.com/2025/12/22/four-ways-to-create-power-bi-backgrounds/); [Zerg00s generator](https://github.com/Zerg00s/Power-BI-Backgrounds); [DaTaxan generator](https://dataxan.com/free-power-bi-canvas-background-download-free-power-bi-background-image/): sizing consensus and generator prior art.
- [Figma: Power BI Backgrounds](https://www.figma.com/community/file/1108563240558755576/power-bi-backgrounds) and [Power BI UI Kit](https://www.figma.com/community/file/1221509435701072015/power-bi-ui-kit): design-tool status quo.

### Code-first tooling
- [PBIP report folder / PBIR reference](https://learn.microsoft.com/power-bi/developer/projects/projects-report): the canonical PBIR page.
- [PBIR transition announcement](https://powerbi.microsoft.com/en-us/blog/pbir-will-become-the-default-power-bi-report-format-get-ready-for-the-transition/): rollout timeline to cite verbatim.
- [microsoft/json-schemas report schemas](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definitionProperties): the externally editable contract.
- [Fabric REST report definition](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/report-definition) and [semantic model definition](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/semantic-model-definition): payload shapes for the deployment leg.
- [TMDL view](https://learn.microsoft.com/power-bi/transform-model/desktop-tmdl-view): the model-layer authoring surface.
- [Power BI Agentic overview](https://learn.microsoft.com/power-bi/developer/agentic/power-bi-agentic-overview) and [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric): the first-party agent stack and its scope exclusions.
- [Fabric CLI](https://microsoft.github.io/fabric-cli/) and [GA post](https://blog.fabric.microsoft.com/en-US/blog/fabric-cli-is-now-generally-available-explore-and-automate-microsoft-fabric-from-your-terminal/): ops leg.
- [Git integration source format](https://learn.microsoft.com/fabric/cicd/git-integration/source-code-format): what syncs and how.
- [pbir.tools](https://github.com/maxanatsko/pbir.tools), [power-bi-agentic-development](https://github.com/data-goblin/power-bi-agentic-development), [semantic-link-labs report docs](https://semantic-link-labs.readthedocs.io/en/stable/sempy_labs.report.html), [PBIR-Utils](https://github.com/akhilannan/PBIR-Utils): the community toolbelt.
- [pbi-tools issue #425](https://github.com/pbi-tools/pbi-tools/issues/425): why not pbi-tools for reports.
- [Data Goblins: programmatically modify reports](https://data-goblins.com/power-bi/programmatically-modify-reports): best community tutorial for the estate step.

### Prior art and positioning
- [SQLBI: AI assistance for custom visuals (Mar 2025)](https://www.sqlbi.com/articles/using-ai-assistance-to-create-power-bi-custom-visuals/) and [AI and agentic development for BI (Sep 2025)](https://www.sqlbi.com/articles/introducing-ai-and-agentic-development-for-business-intelligence/): the closest prior art to name and differentiate from.
- [Agent skills announcement (Jun 8 2026)](https://community.fabric.microsoft.com/t5/Power-BI-Updates-Blog/AI-Powered-Power-BI-reporting-From-design-to-deployment-with/ba-p/5190703): official prior art with our niche excluded.
- [Lukas Reese: PBIR code-first](https://lukasreese.com/2026/03/14/pbir-code-first-power-bi/) and [PBIR Report Builder skill](https://lukasreese.com/2026/03/14/pbir-report-builder-claude-skill/): the 85 to 90 percent baseline.
- [f9finance: Claude custom visuals](https://www.f9finance.com/custom-power-bi-visuals-with-claude/): chat-based HTML/Deneb prior art.
- [Alexander Korn: report-to-Excalidraw](https://actionablereporting.com/2026/03/09/power-bi-report-prototyping-with-ai-from-35-pages-to-18-in-10-minutes/): the reverse direction.
- [Draft BI](https://draftbi.com/): commercial wireframe-to-PBIR product.
- [Copilot report creation limits](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-create-reports) and [MCP servers overview](https://learn.microsoft.com/en-us/power-bi/developer/mcp/mcp-servers-overview): the "why not just use Copilot" citations.
- [Dynamic Web Training: GPT-5 + Deneb](https://www.dynamicwebtraining.com.au/blog/using-chatgpt-5-and-denab-for-custom-power-bi-visuals) and [Workout Wednesday 2024 w47](https://www.workout-wednesday.com/2024-week-47-power-bi-html-css/): tool-agnostic community baseline.
