# Začínáme

## Požadavky

- Python 3.11 až 3.13,
- Git,
- POSIX shell pro bootstrap skript.

## Instalace

```bash
git clone https://github.com/nulleimy/OATHDO.git
cd OATHDO
./scripts/bootstrap_local.sh
```

## CLI kompatibilita

Produktový a repozitářový název je **OATHDO**. Python package a CLI v aktuální kompatibilní řadě stále používají jméno `goverdocs`.

## První kontrola

```bash
.venv/bin/goverdocs --version
.venv/bin/goverdocs inspect --root .
.venv/bin/goverdocs validate --root .
.venv/bin/goverdocs health --root .
```

## Analýza změny

```bash
.venv/bin/goverdocs classify --root . --diff HEAD~1..HEAD
.venv/bin/goverdocs plan --root . --diff HEAD~1..HEAD
```

Tyto příkazy analyzují a plánují. Canonical dokumentaci autonomně nemění.

## Lokální build dokumentačního portálu

```bash
python -m pip install -e '.[docs]'
mkdocs build --strict
```

Výstup vznikne v ignorovaném adresáři `site/`. Publikace je samostatná, explicitně schvalovaná operace.
