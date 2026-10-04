# Sports Event OS Desktop design system

Single visual authority. Product needs and accessible macOS behavior win over every external skill. Mode: Operate. Design Read: a local professional event-operations workspace; calm, precise and table-led, not a marketing dashboard.

## Layout
Targets 1440×900 / 1280×800; minimum 1040×700. Native macOS window chrome. Navigation 208px, flexible main workspace; optional inline detail expands below a selected row rather than mandatory third column. Navigation can be explicitly narrowed; Quality Gate / Versions / Snapshots remain in a fixed bottom group. At narrow widths sidebar width reduces; tables scroll horizontally, never turn into cards. Main content does not scroll behind the action toolbar.

## Surface and tokens
Light working environment. Canvas #f3f4f4, sidebar #ecefef, workspace #ffffff, subtle row hover #f4f7f6, selected #e5f0eb. Ink #202b28, muted #56645e, divider #d7deda, accent #245e47; on-accent white. PASS #246043, WARNING #79530b, BLOCK #a72e35. Status always has a text label. Dark ink/accent deliberately contrast with neutral background; verify actual rendered contrast.
Spacing 4/8/12/16/24/32px. Radius: cells 2px, inputs/buttons 5px, dialogs 8px; no large rounded cards. One divider for each actual structural boundary; shadow only for modal elevation.

## Typography
System macOS sans and PingFang SC; no remote fonts. Body/control 14px, secondary 12px, heading 22px, numeric summary 28px maximum. Tabular numbers right-aligned; technical keys/IDs use monospace only where useful. Clear table headers, no giant hero. Long provenance/error text wraps.

## Core surfaces
Projects: compact recent-project rows; new/open actions, explicit path, name/id/status/version/modified/quality.
New: three steps identity → profile → modules (requires/provides shown); synthetic-only notice.
Workspace: dynamic enabled-only module navigation, Overview, Quality Gate, Versions, Snapshots, module management.
Editor: schema-driven fields, spreadsheet-like row table, inline controls. Nested objects/arrays in expandable inline detail, not per-cell modal. Row add/remove explicit; empty states explain next action. Optional/nullable fields explicit. Dates retain ISO timezone information.
Revenue: backend read-only totals, compact scenario table, stage/tier/session table tabs. Public/rights/fulfilled are separate columns. No frontend arithmetic or KPI cards.
Quality: prominent textual aggregate + Blocking/Warnings/Passed sections; passed means no reported findings, not fabricated per-rule passes. Go-to-field only when source maps to schema path.
Snapshot: persistent READ ONLY label, frozen metadata/data, no mutation controls. Diff grouped by backend module/fact/reason labels.

## Interaction and state
Tab/Shift-Tab follow DOM; Enter activates/edit-selects cell; Escape restores focus-entry value. Focus always visible. Changed cells carry a small dirty marker and text context; local number/type errors carry aria-invalid and nearby explanation. Save/submit returns authoritative DTO; APPROVED→DRAFT is backend-driven and shown calmly. Outside-approval dialog requests nonempty reference and shows exact current revision. No optimistic business approval.

Loading keeps task context; backend failure has reconnect/open guidance and Technical Details. Empty projects/rows/snapshots/diff/calculation are explained. Explicit save differentiates local editor drafts, backend working changes and persisted data. Switching project/module with unsent changes requires confirmation.

## Motion contract (Emil)
High-frequency navigation, keyboard edits, rows, numbers and selection: instant, no animation. Occasional pointer-opened dialog: opacity + translateY(4px), 160ms enter / 100ms exit, cubic-bezier(.2,.8,.2,1); communicates overlay layer. Keyboard-opened dialog: instant. Reduced motion removes movement and uses at most 60ms opacity. CSS transitions are interruptible; no animation library. No hover scale, bounce, count-up, scroll reveals, keyframes or transition:all.

## Dependencies and review
React/TypeScript/Vite + Base UI Dialog; native semantic table/inputs/select. No chart, toast or state library unless actual use requires it. One implementation → one consolidated critique/a11y/detector/motion audit → one fix batch → one polish/confirmation. Record residual UX iterations; no Kernel redesign.

## Rejected adviser defaults
GPT Taste AIDA, randomized hero, mock RNG output, mandatory GSAP, enormous spacing, background images: conflict with product and truthfulness. Adopt only contrast, layout coherence, anti-clutter and label discipline. UI Pro Max marketing generation and mobile-card conversion rejected. No external skill overwrites these decisions.
