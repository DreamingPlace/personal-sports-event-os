# Personal Sports Event OS
<!-- impeccable:product-schema 1 -->

## Platform
web

Tauri 2 macOS desktop host (not a hosted website). Desktop-first, offline, one project folder per workspace.

## Stack
User-specified: Tauri 2 / Rust transport / React / TypeScript / Vite / frozen Python sidecar. Existing ApplicationService owns all business state, calculations, approval, validation and snapshots. Kernel architecture remains frozen.

## Audience
赛事运营、票务、商业运营和项目统筹人员。Local professional productivity, not a general dashboard.

## Primary Jobs
Create/open project → select capabilities → enter facts → find errors → calculate scenarios → record outside approval → compare → freeze snapshot → reopen later.

## Character
professional; dense but calm; precise; reliable; desktop-first; data-oriented.

## NOT
marketing website; consumer app; analytics dashboard wall; AI chat app; cute SaaS; crypto dashboard; neon developer toy.

## Confirmed Constraints
Synthetic data only. No AI, ticketing platform, cloud, central project database, real company data, automated approval, pricing decisions or raw SQLite/JSON edits from React. Installed app must not require Python/venv/pip. Existing 180 backend tests must remain intact.

## Accessibility & Inclusion
Keyboard-first editing, visible focus, labels, accessible dialogs, textual status, error location, reduced motion. Target 1440×900 and 1280×800, establish tested minimum. No tooltip-only information.

## Evidence on Hand
README, V1_1_ARCHITECTURE, V1_1_1_HARDENING, docs/ARCHITECTURE, BUSINESS_RULES and DATA_DICTIONARY read. Baseline bd99376568d007b13e81e99d939afe2b72cde835 verified clean; 180/180 actual tests passed before desktop changes.

## Open Decisions / Working Assumptions
User confirmed Chinese UI with original module IDs, versions and technical field names. No product facts are inferred from brand references. App is local ad-hoc signed development distribution, not App Store/notarized production delivery.
