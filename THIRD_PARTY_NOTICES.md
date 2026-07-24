# Third-Party Tooling Notices

This document records the external projects selected for the first GOVERDOCS
open-source governance toolchain integration. These tools provide presentation,
authoring conventions or evidence. They do not replace GOVERDOCS as the
canonical governance authority.

| Project | Pinned version or revision | Licence | Use in GOVERDOCS | Distribution boundary |
|---|---|---|---|---|
| MkDocs | `1.6.1` | BSD-2-Clause | Static documentation build engine | Optional `docs` extra; not installed by the runtime wheel |
| Material for MkDocs | `9.7.7` | MIT | Documentation portal theme | Optional `docs` extra; build-only; review by 2026-10-01 |
| MADR | conceptual template from `adr/madr` | MIT OR CC0-1.0 | Inspiration for the original GOVERDOCS ADR template | No MADR runtime code or verbatim template is packaged |
| REUSE tool | `6.2.0` | Mixed upstream licensing; tool code primarily GPL-3.0-or-later | CI/development compliance check against REUSE Specification 3.3 | Optional `compliance` extra; not installed in runtime smoke environment |
| OpenSSF Scorecard Action | `v2.4.3` / `4eaacf0543bb3f2c246792bd56e8cdeffafb205a` | Apache-2.0 | Read-only repository and supply-chain assessment | GitHub Actions only; SARIF evidence |

## Adoption constraints

- All Python tooling is exactly pinned in `pyproject.toml`.
- All GitHub Actions are pinned to full commit SHAs.
- The documentation portal is built with `--strict` but is not automatically deployed.
- REUSE is a compliance tool and does not become a GOVERDOCS runtime dependency.
- OpenSSF Scorecard runs in a separate restricted workflow.
- Material for MkDocs must be re-evaluated by `2026-10-01` because its current major line is in maintenance mode.
- Any replacement of the documentation engine or security workflow requires a separately reviewed change.

## Canonical upstream references

- MkDocs: <https://www.mkdocs.org/>
- Material for MkDocs: <https://squidfunk.github.io/mkdocs-material/>
- MADR: <https://github.com/adr/madr>
- REUSE: <https://reuse.software/>
- OpenSSF Scorecard: <https://github.com/ossf/scorecard-action>
