# Project-local design toolchain

Installed using official repositories and project scope on 2026-10-05:
- `skills add Leonxlnx/taste-skill --skill gpt-taste --agent codex --yes` (run through pnpm dlx).
- `ui-ux-pro-max-cli` / `uipro init --ai codex`, not obsolete uipro-cli. Data/scripts/references verified and searches executed.
- Codex skill installer with explicit project --dest for emilkowalski/skills: emil-design-eng, animate, review-animations, pick-ui-library.
- `impeccable install --providers=codex --scope=project`, engine 0.1.11, skill 4.5.0. context run once; hooks status enabled, no ignores, no disabled override.
- awesome-design-md: only two remote references read, no repository clone.

Skills are available for automatic discovery on the next turn; this implementation explicitly reads their installed SKILL.md now. Impeccable init/shape run as instruction workflows, not nonexistent shell subcommands. The user's detailed approved brief supplies the product facts and direction; only unresolved UI language was asked. No repeated discovery questionnaire or five competing design systems.

Codex trust: open `/hooks` in this project and approve the installed project hook if prompted. The installer manifest exists at `.codex/hooks.json`; installation/enabled status alone does not prove native host trust. We do not edit trust records or disable the hook. Manual detector and hook-payload verification are recorded in the design audit.

External skill files are advisers, not runtime application dependencies. Do not ship their binaries in the .app.

Supplement for current CLI packaging: fetched only `src/ui-ux-pro-max/templates/` and `.claude/skills/ui-ux-pro-max/references/` from its official repository into the project skill; verified 25 files across these two directories. This is not the obsolete uipro-cli and not a catalog stub. Project-local third-party skill trees/hooks are ignored by Git (machine-local tooling); application source, lockfiles, installation instructions and design evidence are committed. Installers may prompt for project hook trust; do not approve by modifying trust configuration.
