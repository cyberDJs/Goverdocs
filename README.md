<div align="center">

# GOVERDOCS

### Deterministická governance technické dokumentace

**Rozpoznej dopad změny. Naplánuj řízenou aktualizaci. Ověř pravidla. Zachovej auditní stopu.**

[![Quality](https://github.com/nulleimy/Goverdocs/actions/workflows/quality.yml/badge.svg?branch=main)](https://github.com/nulleimy/Goverdocs/actions/workflows/quality.yml)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)
[![License](https://img.shields.io/badge/License-Apache--2.0-2ea44f)](LICENSE)
[![Status](https://img.shields.io/badge/Status-release%20candidate-f0ad4e)](PROJECT_STATE.md)

</div>

---

## Co je GOVERDOCS?

GOVERDOCS je open-source Python CLI a governance framework, který propojuje
změny v projektu s dokumentací, rozhodnutími, schváleními a auditními důkazy,
které mají danou změnu doprovázet.

Místo spoléhání na to, že si někdo později vzpomene aktualizovat architekturu,
ADR, bezpečnostní dokumentaci nebo projektový stav, GOVERDOCS:

- klasifikuje dopad změněných souborů a Git diffu,
- použije deterministickou rozhodovací matici,
- připraví plán dokumentačních operací,
- ověří metadata, vztahy a lokální odkazy,
- vynutí schválení tam, kde je vyžadováno,
- regeneruje odvozené registry a graf vztahů,
- zaznamená výsledek validace nebo health checku jako auditní receipt.

> [!IMPORTANT]
> LLM může navrhovat text, ale nesmí schválit vlastní canonical zápis.
> GOVERDOCS v0.1 nemá AI runtime ani autonomní příkaz `apply`.

## Proč GOVERDOCS existuje

Technická dokumentace obvykle nestárne proto, že chybí Markdown. Stárne proto,
že změna kódu, infrastruktury nebo procesu není systematicky propojena s tím,
co musí být zdokumentováno a schváleno.

| Bez governance vrstvy | S GOVERDOCS |
|---|---|
| Dopad změny zůstává v hlavě autora | Dopad změny je deterministicky klasifikován |
| Dokumentace se aktualizuje nahodile | Rozhodovací matice určí požadované operace |
| Bezpečnostní změna může uniknout review | Kritická pravidla vyžadují explicitní schválení |
| ADR lze tiše přepsat | Přijatá rozhodnutí se supersedují, ne přepisují |
| Nelze doložit výsledek kontroly | Validace a health mohou vytvořit auditní receipt |
| Registry se rozcházejí s dokumenty | Odvozené registry lze deterministicky regenerovat |

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
Validation
      │
      ▼
Human approval
      │
      ▼
Future controlled writer
      │
      ▼
Registry · Relationship graph · Audit receipt
```

Aktuální verze končí před controlled writerem. Umí číst, klasifikovat,
plánovat, validovat a regenerovat odvozené artefakty, ale sama nepřepisuje
canonical obsah.

## Co umí dnes

| Schopnost | Stav | Účel |
|---|---:|---|
| Inicializace projektu | Dostupné | Vytvoří základní governance strukturu |
| Dokumentový registr | Dostupné | Eviduje dokumenty, metadata a jejich stav |
| Klasifikace změn | Dostupné | Rozpozná dokumentační dopad změněných souborů nebo diffu |
| Rozhodovací matice | Dostupné | Mapuje události na řízené dokumentační operace |
| Plán operací | Dostupné | Vypíše cíle, pravidla a požadované schválení |
| Metadata a link validation | Dostupné | Kontroluje kontrakty, vztahy, supersession a lokální odkazy |
| Relationship graph | Dostupné | Zachycuje vazby mezi řízenými dokumenty |
| Auditní receipts | Dostupné | Ukládá výsledek `validate` a `health` |
| Deterministický rebuild | Dostupné | Regeneruje index a manifesty bez závislosti na wall-clock čase |
| Reprodukovatelné balíky | Dostupné | Ověřuje canonical sdist, wheel, licence a runtime závislosti |
| AI writer | Neimplementováno | Budoucí draftovací vrstva |
| Autonomní canonical write | Zakázáno | `apply` v0.1 záměrně neexistuje |

## Rychlý start

### Požadavky

- Python 3.11, 3.12 nebo 3.13,
- Git,
- POSIX shell pro lokální bootstrap.

### Instalace z repozitáře

```bash
git clone https://github.com/nulleimy/Goverdocs.git
cd Goverdocs

./scripts/bootstrap_local.sh

.venv/bin/goverdocs --version
.venv/bin/goverdocs health --root .
```

Očekávaný základní výstup:

```text
goverdocs 0.1.0

PROJECT=GOVERDOCS
DOCUMENTS=<count>
ISSUES=0
STATUS=PASS
```

## Základní pracovní postup

```bash
# 1. Prohlédni registry projektu.
.venv/bin/goverdocs inspect --root .

# 2. Klasifikuj změny v posledním commitu.
.venv/bin/goverdocs classify --root . --diff HEAD~1..HEAD

# 3. Připrav plán dokumentačních operací.
.venv/bin/goverdocs plan --root . --diff HEAD~1..HEAD

# 4. Ověř governance kontrakty a vytvoř receipt.
.venv/bin/goverdocs validate --root . --receipt

# 5. Zkontroluj souhrnný stav.
.venv/bin/goverdocs health --root . --receipt
```

Příkazy `classify`, `plan`, `validate` a `health` canonical dokumentaci
autonomně nemění.

## Praktický příklad: změna autentizace

```bash
.venv/bin/goverdocs classify \
  --root . \
  --changed-file src/auth/token.py

.venv/bin/goverdocs plan \
  --root . \
  --changed-file src/auth/token.py
```

Zjednodušený výstup:

```text
DOCUMENTATION EVENTS
security_boundary_change                 confidence=0.92
  - matched path: src/auth/token.py

PLANNED ACTIONS
UPDATE           PROJECT_STATE.md                         [DOC-EVT-016 | APPROVAL]
CREATE           docs/decisions/security/ADR-*.md         [DOC-EVT-016 | APPROVAL]
CREATE           docs/reviews/REV-*.md                    [DOC-EVT-016 | APPROVAL]
UPDATE_OR_CREATE docs/security/SEC-*.md                   [DOC-EVT-016 | APPROVAL]

RESULT
Canonical write: BLOCKED — approval required
```

GOVERDOCS tím neprovede změnu dokumentace. Vytvoří vysvětlitelný plán, který
ukazuje, co má být aktualizováno a kde je nutné lidské schválení.

## CLI přehled

| Příkaz | Účel | Důležité volby |
|---|---|---|
| `goverdocs init [target]` | Inicializuje governance strukturu | `--project-name`, `--force` |
| `goverdocs inspect` | Vypíše dokumentový registr | `--root`, `--json` |
| `goverdocs classify` | Klasifikuje změněné soubory a diff | `--diff`, `--changed-file`, `--diff-text-file`, `--json` |
| `goverdocs plan` | Připraví operace podle rozhodovací matice | `--diff`, `--changed-file`, `--diff-text-file`, `--json` |
| `goverdocs validate` | Ověří governance kontrakty | `--root`, `--json`, `--receipt` |
| `goverdocs rebuild-index` | Regeneruje index a manifesty | `--root` |
| `goverdocs health` | Vrátí souhrnný stav projektu | `--root`, `--receipt` |

Úplnou nápovědu zobrazíš pomocí:

```bash
.venv/bin/goverdocs --help
.venv/bin/goverdocs plan --help
```

## Architektura

```text
Git diff / changed files
          │
          ▼
Classifier ──→ Decision Matrix ──→ Planner
          │
          ▼
Validator ──→ Approval Gate ──→ future controlled writer
          │
          ▼
Documentation Index
Document Registry
Relationship Graph
Status Summary
Audit Receipts
```

Hlavní komponenty:

- **Classifier** převádí změněné cesty a sémantické signály na události.
- **Decision Matrix** obsahuje 45 pravidel s akcemi, prioritou a approval policy.
- **Planner** převádí události na vysvětlitelné operace.
- **Validator** kontroluje metadata, vztahy, supersession a lokální odkazy.
- **Registry builder** vytváří deterministické odvozené artefakty.
- **Receipts** zachovávají auditovatelný výsledek validace a health checku.

Podrobnější systémový kontext je v
[`ARCH-0001`](docs/architecture/ARCH-0001-system-context.md).

## Autorita a bezpečnostní hranice

GOVERDOCS používá explicitní model autority:

1. Projektový filesystem je canonical zdroj.
2. Chat, ZIP a exporty jsou snapshoty, nikoli autorita.
3. Povolené operace určuje deterministická policy.
4. LLM může vytvořit draft, ale nemůže schválit vlastní canonical zápis.
5. Přijatá rozhodnutí se supersedují, nikdy tiše nepřepisují.
6. Selhání validace blokuje canonical write.
7. Lokální Markdown odkazy nesmí opustit kořen projektu.

Write policy rozlišuje:

| Třída | Význam |
|---|---|
| `automatic` | Strukturovaný a měnitelný projektový stav |
| `append-only` | Chronologický registr; oprava vzniká novým záznamem |
| `approval-required` | Draft lze připravit, canonical zápis schvaluje vlastník |
| `immutable` | Přijatý důkaz nebo incidentní záznam se nemění |
| `generated` | Odvozený výstup se přestavuje z canonical zdrojů |

Viz
[`Documentation Automation Governance`](docs/governance/GOV-DOCUMENTATION-AUTOMATION.md)
a
[`Documentation Trust Boundaries`](docs/security/SEC-0001-trust-boundaries.md).

## Generované governance artefakty

Příkaz:

```bash
.venv/bin/goverdocs rebuild-index --root .
```

regeneruje:

```text
DOCUMENTATION_INDEX.md
manifests/DOCUMENT_REGISTRY.yaml
manifests/RELATIONSHIP_GRAPH.json
manifests/DOCUMENT_STATUS_SUMMARY.json
```

Výstupy jsou deterministické a jejich `generated_at` je odvozen z metadata
řízených dokumentů, ne z okamžiku spuštění příkazu.

## Mapa repozitáře

```text
automation/             Policies a rozhodovací matice
docs/architecture/      Systémový kontext a architektonické modely
docs/decisions/         ADR a významná rozhodnutí
docs/epics/             Aktivní a historické epiky
docs/governance/        Normativní governance pravidla
docs/operations/        Provozní postupy
docs/reviews/           Review a readiness evidence
docs/security/          Trust boundaries a bezpečnostní pravidla
docs/work-blocks/       Řízené implementační jednotky
manifests/              Registry, grafy a souhrny
project-memory/         Kontext, aktivní práce, rozhodnutí a session log
schemas/                JSON Schema kontrakty
scripts/                Bootstrap a release verification
src/goverdocs/          Python CLI a governance jádro
tests/                  Unit a regresní testy
```

## Release integrita

Release pipeline ověřuje artefakty bez jejich automatického publikování:

```text
source
  → Ruff + mypy + pytest
  → documentation validation + health
  → repeated sdist/wheel build
  → raw sdist payload comparison
  → canonical archive metadata
  → byte-for-byte artifact comparison
  → twine strict metadata check
  → clean wheel installation
  → pip check
  → runtime dependency inventory
  → retained CI artifacts
```

Implementaci obsahují:

- [`.github/workflows/quality.yml`](.github/workflows/quality.yml),
- [`scripts/verify_distribution.py`](scripts/verify_distribution.py),
- [`tests/test_release_packaging.py`](tests/test_release_packaging.py).

<details>
<summary>Ruční kontrola release artefaktů</summary>

```bash
python -m pip install '.[release]'

export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"

python -m build --outdir dist-a
python -m build --outdir dist-b

python scripts/verify_distribution.py compare-sdist-payload \
  --left dist-a/goverdocs-0.1.0.tar.gz \
  --right dist-b/goverdocs-0.1.0.tar.gz

for sdist in \
  dist-a/goverdocs-0.1.0.tar.gz \
  dist-b/goverdocs-0.1.0.tar.gz
do
  python scripts/verify_distribution.py canonicalize-sdist \
    --path "$sdist" \
    --epoch "$SOURCE_DATE_EPOCH"
done

python scripts/verify_distribution.py compare \
  --left dist-a \
  --right dist-b

python -m twine check --strict dist-a/*
python scripts/verify_distribution.py artifacts \
  --dist-dir dist-a \
  --manifest dist-a/ARTIFACT_MANIFEST.json
```

</details>

Tagování, GitHub release a případná publikace balíku jsou samostatné operace,
které vyžadují explicitní schválení.

## Stav projektu

| Oblast | Aktuální stav |
|---|---|
| Verze | `0.1.0` |
| Fáze | Release candidate hardening |
| Python | 3.11, 3.12, 3.13 |
| Licence | Apache-2.0 |
| Klasifikace a plánování | Implementováno |
| Validation a health | Implementováno |
| Auditní receipts | Implementováno |
| Deterministické registry | Implementováno |
| Reprodukovatelné distribuce | Implementováno |
| AI writer | Neimplementováno |
| Controlled canonical writer | Neimplementováno |
| Autonomní `apply` | Záměrně nedostupné |

Aktuální exit criteria a ověřený stav jsou vedeny v
[`PROJECT_STATE.md`](PROJECT_STATE.md).

## Dokumentace

| Dokument | Účel |
|---|---|
| [`WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md`](WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md) | Kanonická technická ústava |
| [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) | Generovaný katalog řízených dokumentů |
| [`PROJECT_STATE.md`](PROJECT_STATE.md) | Aktuální stav a release exit criteria |
| [`ARCH-0001`](docs/architecture/ARCH-0001-system-context.md) | Systémový kontext a hranice komponent |
| [`GOV-0001`](docs/governance/GOV-DOCUMENTATION-AUTOMATION.md) | Autorita, write classes a governance pravidla |
| [`SEC-0001`](docs/security/SEC-0001-trust-boundaries.md) | Trust boundaries a bezpečnostní omezení |
| [`ADR-0001`](docs/decisions/architecture/ADR-0001-deterministic-governor-first.md) | Rozhodnutí začít deterministickým governorem |
| [`ADR-0002`](docs/decisions/governance/ADR-0002-apache-2-license.md) | Rozhodnutí o Apache-2.0 |
| [`CHANGELOG.md`](CHANGELOG.md) | Historie významných změn |

## Normativní technická ústava

Soubor
[`WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md`](WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md)
je kanonická technická ústava projektu.

Jeho integrita je deklarována v
[`manifests/GOVERNANCE_ARTIFACTS.yaml`](manifests/GOVERNANCE_ARTIFACTS.yaml)
a ověřována regresním testem. Změna ústavy vyžaduje explicitní governance
change control a aktualizaci kanonického checksumu.

## Licence

GOVERDOCS je licencován pod
[Apache License 2.0](LICENSE) (`Apache-2.0`).

Licenční rozhodnutí dokumentuje
[`ADR-0002`](docs/decisions/governance/ADR-0002-apache-2-license.md).

## Zpětná vazba

Chybu, nejasnost nebo návrh změny lze zaznamenat v
[GitHub Issues](https://github.com/nulleimy/Goverdocs/issues).

---

<div align="center">

**Dokumentace jako řízený systém: deterministická, auditovatelná a pod lidskou kontrolou.**

</div>
