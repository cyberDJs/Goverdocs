# GOVERDOCS

Deterministické governance jádro pro projektovou dokumentaci používanou lidmi i AI agenty.

## Princip

```text
project change
  → deterministic classification
  → decision matrix
  → operation plan
  → validation
  → approval gate
  → canonical write
  → audit receipt
```

LLM smí navrhovat obsah. **Nesmí být autoritou pro canonical zápis.**

## Normativní technická ústava

Soubor `WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md` je kanonická technická ústava projektu.

Jeho integrita je deklarována v `manifests/GOVERNANCE_ARTIFACTS.yaml` a ověřována regresním testem. Soubor se nesmí měnit bez explicitního governance change control a aktualizace kanonického checksumu.

## V0.1

- 45 pravidel rozhodovací matice,
- YAML politiky a JSON Schema,
- CLI: `init`, `inspect`, `classify`, `plan`, `validate`, `rebuild-index`, `health`,
- metadata, vztahy, supersession a local-link validation,
- dokumentový registr, relationship graph a auditní receipts,
- testy a GitHub CI,
- bez AI runtime a bez automatického canonical zápisu.

## Licence

GOVERDOCS je licencován pod Apache License 2.0 (`Apache-2.0`).
Kanonický text je v souboru [`LICENSE`](LICENSE) a rozhodnutí dokumentuje
[`ADR-0002`](docs/decisions/governance/ADR-0002-apache-2-license.md).

## Lokální instalace

```bash
cd /Users/eimyna/GOVERDOCS
./scripts/bootstrap_local.sh
```

## Analýza změn

```bash
.venv/bin/goverdocs classify --root . --changed-file src/auth/token.py
.venv/bin/goverdocs plan --root . --changed-file docs/architecture/system.md
.venv/bin/goverdocs validate --root . --receipt
```

## Bezpečnostní hranice

Příkaz `apply` záměrně neexistuje. V0.1 čte, klasifikuje, plánuje, validuje a regeneruje odvozené registry; canonical obsah autonomně nepřepisuje.

## Release verification

Release distributions are built and verified without publishing them:

```bash
python -m pip install '.[release]'
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
python -m build
python scripts/verify_distribution.py canonicalize-sdist \
  --path dist/goverdocs-0.1.0.tar.gz \
  --epoch "$SOURCE_DATE_EPOCH"
python -m twine check --strict dist/*
python scripts/verify_distribution.py artifacts \
  --dist-dir dist \
  --manifest dist/ARTIFACT_MANIFEST.json
```

CI additionally installs the wheel into a clean virtual environment, runs
`pip check`, executes the GOVERDOCS health command and records the resolved
runtime dependency inventory. Tagging and release publication are separate,
approval-gated operations.
