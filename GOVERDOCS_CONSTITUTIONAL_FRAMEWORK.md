---
id: CONST-FRAMEWORK-GOVERDOCS
type: governance-constitution-framework
title: GOVERDOCS Constitutional Framework
status: active
owner: GOVERDOCS
created: 2026-07-26
updated: 2026-08-17
version: 1.0.1
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - PRODUCT-MODE-GOVERDOCS
  - ADR-0004
  - WB-0003
  - REV-0003
  - GOV-0001
source_refs:
  - SESSION-2026-07-26-01
  - SESSION-2026-07-26-02
  - GITHUB-MAIN-b002135d4ce532c451bf6eee9cd9c8782431ee92
  - GITHUB-RELEASE-v0.1.0@018d8b7d5f5ab12f537991fe565b9dae4af3b0d9
last_verified: 2026-08-17
review_due: 2026-09-17
---

# GOVERDOCS CONSTITUTIONAL FRAMEWORK

## 0. Normativní stav

Tento dokument je `ACTIVE` koordinační rámec. Doplňuje, ale nemění ani
nenahrazuje soubor `WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md`.

Rámec byl přijat pro `warn-only` režim po odděleně schválené implementaci,
commitu a pushi a po úspěšném CI nad přesným SHA
`6236a8cae777063811b41ae00fb36f819f8468e7`. Aktivní stav neznamená tag, release, deployment, adopci ani
ověřený produktový dopad.

## 1. Hlavní operační invariant

Nejsilnější vývojový model spojuje Jobsovu produktovou čistotu, unixovou
jednoduchost, DevOps automatizaci, SRE spolehlivost, bezpečnostní princip nulové
důvěry a úplnou auditovatelnost celého životního cyklu systému — nejen jeho Git
historie.

Každá změna musí být jednoduchá, účelná, automatizovaná, bezpečná, měřitelná,
vratná a důkazně ověřitelná.

Pokud změna některou relevantní vlastnost nesplňuje, musí být:

- zjednodušena,
- doplněna o chybějící kontrolu nebo důkaz,
- schválena jako přesně omezená a časově ohraničená výjimka,
- nebo označena jako `BLOCKED`.

Automatizace smí automatizovat opakovatelné kontroly, validaci, build, testy,
sběr evidence, regeneraci odvozených artefaktů a ověření rollbacku.

Automatizace nesmí převzít rozhodovací autoritu, schválit vlastní výstup ani
obejít approval gate.

## 2. Pořadí autority

Při konfliktu platí:

1. systémová, bezpečnostní a právní pravidla platformy,
2. `WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md`,
3. explicitní aktuální zadání v mezích vyšších pravidel,
4. tento koordinační rámec,
5. aplikovatelný operating mode a strojově čitelné governance policies,
6. schválené ADR, bezpečnostní pravidla a release pravidla,
7. ostatní projektová dokumentace,
8. předpoklady a preference.

Nevyřešený konflikt znamená `BLOCKED`. Konflikt se nesmí řešit výběrem
pohodlnějšího pravidla. Vyžaduje contradiction review, rozhodovací záznam a
opravu canonical zdroje.

Povýšení tohoto rámce nad WORLD vyžaduje samostatnou změnu WORLD, nový checksum,
ADR, plnou verifikaci a samostatná schválení. Tento návrh takové povýšení
neprovádí.

## 3. Povinný slovník pravdivosti

- `PROPOSED` — návrh bez schválení a bez důkazu implementace.
- `APPROVED` — explicitně schválený rozsah; neznamená implementaci.
- `IMPLEMENTED` — změna existuje v přesně určeném prostředí.
- `VERIFIED` — tvrzení je doloženo konkrétním reprodukovatelným důkazem.
- `INFERRED` — závěr je odvozen, ale nebyl přímo ověřen.
- `UNKNOWN` — nejsou dostatečné podklady.
- `BLOCKED` — bezpečné pokračování není možné.
- `PARTIALLY VERIFIED` — část je ověřena a část zůstává neověřená.

`APPROVED` neznamená `IMPLEMENTED`. `IMPLEMENTED` neznamená `VERIFIED`.
`VERIFIED` neznamená automaticky `RELEASED`, `DEPLOYED`, `ADOPTED` ani
`SUCCESSFUL`.

Pojem `COMPLETE` se nesmí použít bez důkazu splnění všech relevantních
produktových, technických, bezpečnostních, provozních a adopčních kritérií.

## 4. Nulová důvěra

Nevěř automaticky:

- uživatelskému vstupu,
- lokálnímu prostředí,
- síti,
- CI metadatům,
- externímu API,
- pluginu,
- dependency,
- artefaktu,
- dokumentaci,
- AI výstupu,
- předchozímu schválení,
- deklarovanému release nebo deploymentu.

Na každé trust boundary ověř podle relevance:

- identitu,
- autentizaci,
- autorizaci,
- minimální oprávnění,
- integritu,
- původ,
- čerstvost,
- rozsah,
- auditní stopu,
- revokaci,
- bezpečný failure mode.

Git commit dokazuje obsah Git historie. Nedokazuje automaticky build, artefakt,
release, deployment, runtime stav, adopci ani produktový dopad.

## 5. Úplný evidenční řetězec

Podle rozsahu musí být dohledatelný řetězec:

```text
ověřený problém
→ discovery evidence
→ rozhodnutí
→ schválený scope
→ implementace
→ testy
→ commit
→ CI nad přesným commitem
→ artefakt a checksum
→ SBOM a provenance
→ tag
→ release
→ deployment
→ ověřená runtime verze
→ health, SLO a telemetry
→ incidenty
→ adopce
→ měřený dopad
→ post-implementation review
```

Nevztahující se článek musí mít explicitní odůvodnění. `N/A` nesmí sloužit k
obejití důkazu.

Odvozený registr, index nebo dashboard není canonical důkaz, pokud nelze
jednoznačně dohledat jeho zdroj a integritu.

<a id="approval-gates"></a>

## 6. Samostatné approval gates

Samostatné schválení je vyžadováno podle relevance pro:

1. produktový záměr,
2. rozhodnutí nebo architekturu,
3. implementaci,
4. canonical dokumentační změnu,
5. commit,
6. push,
7. merge,
8. tag,
9. release,
10. deployment,
11. destruktivní migraci,
12. změnu licence,
13. veřejné API,
14. bezpečnostní výjimku a risk acceptance.

Schválení jedné brány automaticky neschvaluje další. Mlčení není schválení.
Schválení musí být přiřaditelné, auditovatelné, omezené na konkrétní scope a
platné pro konkrétní stav.

Tato sekce je jediným canonical zdrojem seznamu approval gates. Strojově
čitelné policies na ni smějí odkazovat, ale nesmějí udržovat paralelní seznam.

## 7. Operating modes

### Engineering operating mode

`WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md` zůstává nejvyšším projektovým
technickým standardem a určuje architekturu, implementaci, testování, Git,
DevOps, SRE, bezpečnost, release engineering a technickou důkazní disciplínu.

### Product, decision and execution operating mode

`PRODUCT_DECISION_EXECUTION_OPERATING_MODE.md` řídí ověření problému,
produktovou čistotu, discovery, evidence, rozhodování, prioritizaci, adopci a
měření dopadu. Nesmí přepisovat technické nebo bezpečnostní požadavky WORLD.

### Machine-readable change gate

`policies/CHANGE_GATE_10_OF_10.yaml` je jediný canonical zdroj dimenzí změnové
brány. Markdown dokumenty nesmí udržovat paralelní kopii jejího seznamu.

## 8. Změnová brána 10/10

Označení `10/10` znamená pouze:

- všech deset dimenzí definovaných canonical YAML politikou bylo posouzeno,
- každá relevantní dimenze má konkrétní důkaz,
- žádná blocking dimenze není neověřená,
- rozsah a prostředí jsou přesně určeny.

Neznamená absolutní dokonalost, nulové riziko ani univerzální vhodnost.

Každý report musí uvést počet `VERIFIED`, počet schválených `N/A`, počet
`BLOCKED`, deklarovaný scope, prostředí a odkazy na evidence. Samotné číslo bez
těchto údajů není platný výsledek brány.

Výsledky:

- `10/10 — VERIFIED FOR DECLARED SCOPE`,
- `1–9/10 — PARTIALLY VERIFIED`,
- kritická chybějící dimenze — `BLOCKED`.

## 9. AI hranice

AI smí navrhovat, vysvětlovat, sumarizovat, hledat rozpory a připravovat drafty.

AI nesmí sama:

- schválit vlastní návrh,
- označit neověřený stav jako `VERIFIED`,
- obejít deterministická pravidla,
- provést canonical write, commit, push, merge, tag, release nebo deployment bez
  samostatného schválení,
- změnit scope bez upozornění,
- vydávat pravděpodobnost za důkaz.

Deterministické pravidlo a explicitní lidská autorita mají přednost před
generativním doporučením.

## 10. Výjimky

Výjimka musí obsahovat:

- stabilní ID,
- vlastníka,
- přesné pravidlo,
- důvod,
- riziko,
- kompenzační opatření,
- scope,
- datum expirace,
- review date,
- schválení.

Výjimka bez vlastníka, rozsahu nebo expirace je `BLOCKED`, pokud nejde o
explicitně schválené trvalé rozhodnutí.

## 11. Governance změn rámce

Změna tohoto rámce, operating mode nebo 10/10 policy musí být:

- verzovaná,
- auditovatelná,
- otestovaná,
- checksumově identifikovatelná,
- opatřená ADR nebo změnovým záznamem,
- vratná nebo migrovatelná,
- samostatně schválená pro implementaci, commit, push, tag a release.

Ruční změna distribuované kopie není změnou canonical standardu.

## 12. Povinný finální stavový blok

Každý významný produktový nebo technický výstup musí skončit:

```text
STATUS:
PROBLEM:
EVIDENCE:
DECISION:
VERIFIED:
NOT VERIFIED:
APPROVALS:
CHANGED:
IMPACT:
RISKS:
NEXT SAFE STEP:
```

Tento rozšířený blok doplňuje minimální blok vyžadovaný WORLD. Při konfliktu
platí WORLD.

## 13. Acceptance evidence

Aktivace `1.0.0` je omezena na `warn-only` governance scope a je doložena:

- exact-SHA commit: `6236a8cae777063811b41ae00fb36f819f8468e7`,
- quality run `30191576044`: Python 3.11, 3.12 a 3.13, Ruff, mypy, pytest,
  dokumentační validace a health, reprodukovatelné sdist/wheel buildy, metadata,
  clean-install audit, MkDocs a REUSE — vše `success`,
- OpenSSF Scorecard run `30191576042` — `success`, včetně SARIF a Code
  Scanning uploadu,
- package artifact `8628731800` SHA-256 `dcbcb253584d86bedc53f145f5461bb1283a6382b0f405cc5cc853cf9b4ce2ab`,
- documentation artifact `8628731425` SHA-256 `0ec8927f162e5191727833d5df8daeb0113c577f8e24a50a1dd1b78209429874`,
- SARIF artifact `8628727141` SHA-256 `ea7a2f955989d7c6ce2df137c8a18e0cf311ef717740d180507a7e0ea7ebac93`,
- nezměněný WORLD SHA-256 `ed44c6147049887d941b7497f1bce3b817f22b6ae00a5136a27365a2f688d918`.

Tag, release, deployment, adopce a produktový dopad nejsou součástí tohoto
přijetí a zůstávají samostatnými approval gates nebo následnými důkazy.

## 14. Revalidation — 2026-08-17

The normative framework remains valid without supersession. The original
`1.0.0` acceptance evidence above remains historical evidence for its bounded
`warn-only` scope and is not rewritten by this review.

Current GitHub revalidation was performed against canonical
`main@b002135d4ce532c451bf6eee9cd9c8782431ee92`. A later separately governed
release `v0.1.0` exists and targets
`018d8b7d5f5ab12f537991fe565b9dae4af3b0d9`. That release is subsequent
evidence under its own approval gate and does not retroactively change the
original framework activation scope.

This revalidation makes no claim about current local Git state, deployment,
adoption or verified product impact. Next review is due `2026-09-17`.
