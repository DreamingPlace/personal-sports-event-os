# UI research — 2026-10-05

Actual installed `ui-ux-pro-max-cli` Codex install: `.agents/skills/ui-ux-pro-max/` contains SKILL.md, scripts/search.py, searchable CSV data, references. Runtime search used before implementation, not a catalog stub.

|Query / actual recommendation|Relevant reason|Decision|
|---|---|---|
|desktop productivity enterprise / --design-system: Minimalism & Swiss Style, clear contrast|Quiet operational work|Adopt hierarchy, reject marketing demo/hero, scroll reveal and two-accent palette|
|project management / ux: z-index management|Result did not answer task intent|Reject; retried product domain. Productivity Tool appeared as second result: adopt functional hierarchy, reject landing conversion|
|data table keyboard / ux: horizontal table scrolling|Many named numeric columns|Adopt scroll container, sticky header, keyboard cell edit; reject card conversion|
|form UX labels / ux: associated labels + named buttons|Data accuracy and screen readers|Adopt; no placeholder-only controls|
|sidebar navigation / ux: logical tab order|Repeated module switching|Adopt enabled-only list and consistent order; no animated navigation|
|data validation error summary / ux: focusable summary and field links|Quality Gate primary workflow|Adopt; preserve expected/actual, inline local shape errors, backend source navigation only when locatable|
|status not color / ux: text + color, submission feedback|PASS/WARNING/BLOCK and approval|Adopt labels, live status, not colored dots alone|
|accessibility focus visible / ux: focus not obscured|Scrollable grids and sticky header|Adopt scroll-padding and focus outlines; do not claim AAA certification|
|enterprise tool density / ux: no results; retried dense enterprise tables / style|Actual narrow match was data-dense-dashboard|Adopt 36px rows, neutral surfaces, table density; reject KPI walls, multiple charts, indiscriminate tiny text|
|controlled form table state / React: controlled inputs, local state|Frontend temporary drafts, not SSOT|Adopt; replace local draft with authoritative DTO after submit|

Implementation selection: package.json absent before scaffold. Emil pick-ui-library explicitly consulted for accessible dialogs: use Base UI Dialog, native inputs/select/table for simple controls; no heavyweight grid, chart or motion library. CSS only for occasional dialog feedback. Data tables are primary, not charts.

Priority: user product/platform requirements > PRODUCT > DESIGN > tokens/components > these results > skill defaults > visual references. Research is evidence, not a second design authority.

Sources: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill ; https://github.com/emilkowalski/skills
