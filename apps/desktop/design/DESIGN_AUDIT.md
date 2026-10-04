# Desktop v0.1 — 集中审查与最终确认

Date: 2026-10-05 (Asia/Singapore). Scope: macOS professional productivity UI, not mobile/marketing. Authority: PRODUCT.md → DESIGN.md. One consolidated review/fix/final confirmation; no alternative visual redesigns. Functional test failures were corrected and rerun, not concealed as aesthetic iterations.

## Actually used
- **UI/UX Pro Max**: official current CLI Codex install; data + search.py + SKILL.md verified. Official repository references/templates supplemented because this CLI version omitted those folders. Executed required searches before implementation; adoption/rejection recorded in UI_RESEARCH.md. Applied labels, semantic tables, visible focus, status text and keyboard scrolling.
- **gpt-taste**: project `skills` installation, read implementation guidance. Applied hierarchy/spacing/anti-clutter. Rejected marketing/AIDA/hero/mandatory GSAP/randomized design claims because they conflict with this brief. No simulated tool output.
- **Emil**: read emil-design-eng, animate, pick-ui-library and review-animations; used Base UI Dialog instead of an inaccessible custom overlay. Reviewed motion against justified-frequency/easing/interruptibility/reduced-motion rules.
- **Impeccable**: project Codex provider installed, context once; init and shape instruction workflows established PRODUCT/DESIGN before UI code. Critique + audit below; focused corrections; final polish was a confirmation pass, not a new design.
- **awesome-design-md**: only Linear and Notion references, not a cloned collection. Their available documents described marketing sites: explicitly rejected hero/brand direction and adopted only neutral hierarchy/separators. No brand affiliation, logo copying or mixed visual systems.

## Impeccable critique
Primary task remains visible: project identity/version → structured facts → quality → approval → immutable history. Forms use native controls, not card-based pseudo-grids. Backend state wins over UI assumptions. Strongest friction: deeply nested schemas and raw technical labels are verbose. This is a documented UX ITERATION, not a reason to redesign Kernel.

## Audit findings / unified corrections
|Priority|Evidence|Correction|Final status|
|---|---|---|---|
|P2 a11y|axe rejected role=status directly on footer|Move live status into child span; preserve contentinfo|PASS|
|P2 a11y|Read-only horizontally scrolling table lacked keyboard focus target|Named region with tabIndex=0|PASS, axe clean|
|P2 navigation|18 enabled modules pushed Quality Gate/history below sidebar fold|Fixed utility navigation below independently scrolling modules|PASS at 1440/1280/1040 widths|
|P2 error recovery|Global error UI could sit outside modal focus scope|Embed error summary/technical details inside active wizard/approval dialog|PASS code review + shared native dialog behavior|
|P3 state|Changed cells initially only had a top-level notice|Per-cell textual dirty marker, focus-within row state|PASS|
|P3 truthful metadata|Recent-project time initially represented opening, not modification|Backend persisted-file mtime DTO|PASS|

A contrast failure captured during a dialog's translucent entering frame was isolated to test timing: the settled foreground/background passed. Test now waits for computed opacity=1 rather than disabling motion/contrast rules. No detector ignore rules or axe exclusions were added.

## Audit score (heuristic, not certification)
|Dimension|Score / 4|Boundary|
|---|---|---|
|Accessibility|3|axe zero violations on tested screens, keyboard path and dialog Escape; full VoiceOver audit not performed|
|Performance|3|No motion library/charts; ~104 KiB gzipped JS, 80-row pricing grid tested; no virtualization|
|Responsive desktop|3|1440×900, 1280×800, 1040×700 inspected; no outer horizontal overflow; mobile not a target|
|Theming|3|Neutral shared tokens, light appearance only; a few intentional status surface literals|
|Implementation integrity|4|One design system; deterministic detector zero findings; no frontend business formulas|
|Total|16 / 20|Good; residual workflow ergonomics recorded, no unbounded polish|

## Motion review — Emil
Only occasional Dialog animates: opacity + translateY(4px), custom ease-out, 160ms enter /100ms exit; existing DOM layer retains CSS-transition interruption. Keyboard-triggered dialog uses no transition. Reduced motion drops translation, opacity ≤60ms. Sidebar, rows, numeric updates, validation text and high-frequency keyboard editing are instantaneous. No hover scale, spring bounce, layout-property animation, keyframes, scroll reveals or transition:all. Purpose: distinguish the protected modal layer, not decorate routine work. Native approval dialog and Escape exercised; no claim of frame-rate benchmarking.

## Deterministic tools and hook trust
- `impeccable detect apps/desktop/src --json`: initial and final `[]`.
- Installed `.codex/hooks.json` registers PostToolUse and Stop, hook status enabled, no ignores/disable override.
- Real synthetic PostToolUse payload invoked installed hook: returned `hookSpecificOutput` and confirmed scanning App.tsx with no deterministic issues. This verifies hook implementation and manifest, **not** that this host automatically granted native project-hook trust.
- If Codex prompts, user must approve the project hook via `/hooks` once. No trust files edited, bypasses, disabling, or falsely claimed host approval. Source written through shell is still covered by the explicit final detector.

## Final polish / STOP
Native packaged app inspected through create Demo → edit → approval invalidation → release BLOCK → preview PASS → Revenue → external-reference approval → second Snapshot → diff → quit → reopen → old snapshot READ ONLY → frozen Revenue. Browser screenshots checked at all three supported sizes. Stable focus, action bar, table alignment and fixed utility navigation confirmed. No further aesthetic changes after this pass.

Known UX ITERATIONS: raw schema labels; ISO datetime entry; long approval metadata diffs; no matrix paste / column resize / virtualized grids; explicit scroll for wide tables. Local technical limits are in DESKTOP_ARCHITECTURE.md. No remaining observed P0/P1 logic defect in tested scope.
