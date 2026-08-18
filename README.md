<div align="center">

# OATHDO

### Deterministická governance technické dokumentace

**Rozpoznej dopad změny. Naplánuj řízenou aktualizaci. Ověř pravidla. Zachovej auditní stopu.**

[![Quality](https://github.com/nulleimy/OATHDO/actions/workflows/quality.yml/badge.svg?branch=main)](https://github.com/nulleimy/OATHDO/actions/workflows/quality.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/nulleimy/OATHDO/badge)](https://scorecard.dev/viewer/?uri=github.com/nulleimy/OATHDO)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)
[![License](https://img.shields.io/badge/License-Apache--2.0-2ea44f)](LICENSE)

</div>

---

## Co je OATHDO?

**OATHDO** je open-source governance framework pro technickou dokumentaci a změnové řízení. Propojuje změny v repozitáři s dokumentací, rozhodnutími, schváleními a auditní evidencí, které mají změnu doprovázet.

Jeho deterministické jádro:

- klasifikuje dopad změněných souborů a Git diffu,
- používá verzovanou rozhodovací matici,
- připravuje vysvětlitelný plán dokumentačních operací,
- ověřuje metadata, vztahy, supersession a lokální odkazy,
- vynucuje schválení tam, kde je vyžadováno,
- publikuje GitHub governance gate,
- zachovává auditovatelnou stopu rozhodnutí a důkazů.

> [!NOTE]
> Produktový a repozitářový název je **OATHDO**. Python package a CLI zůstávají v aktuální kompatibilní řadě pojmenované `goverdocs`; jejich případný rename je samostatná breaking-change migrace.

## Aktuální stav

| Vrstva | Stav |
|---|---|
| Deterministická klasifikace a decision matrix | ✅ dostupné |
| Dokumentový registr a relationship graph | ✅ dostupné |
| Validation / health / audit receipts | ✅ dostupné |
| Reprodukovatelný package build | ✅ CI ověřováno |
| GitHub required governance gate | ✅ server-side enforcement |
| Exact PR + HEAD approval binding | ✅ aktivní |
| Revocation semantics | ✅ aktivní |
| Multi-actor authority model | ✅ canonical |
| Anti-self-approval / separation of duties | ✅ live fail-closed ověřeno |
| Finální pozitivní 2-actor critical quorum proof | 🔶 probíhá |
| Autonomní canonical writer | ⛔ záměrně mimo aktuální release |

**R11 se nepovažuje za FULLY VERIFIED, dokud neprojde pozitivní live critical proof se dvěma rozdílnými non-author authority aktéry.**

## Authority model

Pro kritické změny OATHDO používá explicitní role a capability model:

```text
project-owner
  └─ approve:critical-owner

independent-reviewer
  └─ approve:critical-independent

critical change
  ├─ min. 2 distinct actors
  ├─ min. 2 distinct roles
  └─ PR author approval se do quorum nepočítá
```

Aktuálně role-bound identity:

```text
nulleimy     → project-owner
setarchitect → independent-reviewer
```

## Operační model

```text
Project change
      │
      ▼
Change classification
      │
      ▼
Decision matrix
      │
      ▼
Operation plan
      │
      ▼
Validation + evidence
      │
      ▼
Exact-head authority approval
      │
      ▼
GOVERDOCS Governance Gate
      │
      ▼
GitHub server enforcement
```

Název required status checku **`GOVERDOCS Governance Gate`** je zatím zachován jako kompatibilní technický context identifier. Jeho případný rename musí být proveden jako samostatná koordinovaná migrace workflow + rulesetu, aby nevznikla ochranná mezera.

## Rychlý start

### Požadavky

- Python 3.11, 3.12 nebo 3.13,
- Git,
- POSIX shell pro lokální bootstrap.

```bash
git clone https://github.com/nulleimy/OATHDO.git
cd OATHDO

./scripts/bootstrap_local.sh

.venv/bin/goverdocs --version
.venv/bin/goverdocs health --root .
```

Základní workflow:

```bash
.venv/bin/goverdocs inspect --root .
.venv/bin/goverdocs classify --root . --diff HEAD~1..HEAD
.venv/bin/goverdocs plan --root . --diff HEAD~1..HEAD
.venv/bin/goverdocs validate --root . --receipt
.venv/bin/goverdocs health --root . --receipt
```

## Architektura

```text
Git diff / changed files
          │
          ▼
Classifier ──→ Decision Matrix ──→ Planner
          │
          ▼
Validator ──→ Approval Verification ──→ Authority Policy
          │                                  │
          └──────────────→ Gate Report ←─────┘
                               │
                               ▼
                    GitHub Required Check
                               │
                               ▼
                    Repository Ruleset
```

## Roadmapa

### R11 — Governance Authority / Multi-Actor Trust

- [x] explicit authority model,
- [x] role capabilities,
- [x] actor binding,
- [x] anti-self-approval,
- [x] separation of duties,
- [x] fail-closed solo-actor proof,
- [x] `setarchitect` enrollment jako `independent-reviewer`,
- [ ] neutral-author critical proof,
- [ ] exact-head approval `nulleimy`,
- [ ] exact-head approval `setarchitect`,
- [ ] required governance gate PASS,
- [ ] server-side exact-head merge,
- [ ] post-merge Quality + CodeQL,
- [ ] R11 = FULLY VERIFIED.

### Následující produktová vrstva

Po uzavření R11 má smysl pokračovat v tomto pořadí:

1. **Authority hardening** — stabilní enrollment lifecycle, audit identity bindingu a provozní recovery.
2. **Controlled writer boundary** — explicitně autorizovaný canonical write bez přeskakování governance gate.
3. **Operation proof / immutable evidence** — doložitelný vztah intent → authority → execution → post-state.
4. **Runtime adapters** — bezpečné napojení na externí vývojové a AI runtime systémy.
5. **Release hardening** — stabilní veřejné kontrakty, migration policy a compatibility guarantees.

## Bezpečnostní principy

- fail closed,
- exact-subject approval,
- žádné self-approval pro critical změny,
- žádné oslabení rulesetu kvůli testu,
- žádný fabricated authority actor,
- historie a evidence se neinterpretují jako aktuální autorita bez ověření,
- LLM může připravit návrh, ale nesmí samo vytvořit platnou lidskou authority.

## Dokumentace

- [`PROJECT_STATE.md`](PROJECT_STATE.md) — stav projektu,
- [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) — dokumentový index,
- [`docs/governance/`](docs/governance/) — governance model a evidence,
- [`docs/architecture/`](docs/architecture/) — systémová architektura,
- [`policies/`](policies/) — policy a enforcement kontrakty,
- [`site-docs/`](site-docs/) — zdroj dokumentačního portálu.

## Licence

Apache-2.0. Viz [`LICENSE`](LICENSE).
