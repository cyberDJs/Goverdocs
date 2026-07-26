---
id: PRODUCT-MODE-GOVERDOCS
type: product-decision-execution-operating-mode
title: Product, Decision and Execution Operating Mode
status: proposed
owner: GOVERDOCS
created: 2026-07-26
updated: 2026-07-26
version: 0.1.1
canonical: true
managed_by: mixed
write_policy: approval-required
supersedes: null
superseded_by: null
related:
  - CONST-FRAMEWORK-GOVERDOCS
  - ADR-0004
  - WB-0003
  - REV-0003
  - PROJECT-STATE-GOVERDOCS
source_refs:
  - SESSION-2026-07-26-01
last_verified: null
review_due: 2026-08-15
---

# PRODUCT, DECISION AND EXECUTION OPERATING MODE

## 0. Normativní hranice

Tento dokument je `PROPOSED` operating mode podřízený:

1. `WORLD_CLASS_SOFTWARE_DEVOPS_OPERATING_MODE.md`,
2. `GOVERDOCS_CONSTITUTIONAL_FRAMEWORK.md`.

Řídí produktové, rozhodovací, realizační a adopční otázky. Technickou
implementaci, bezpečnost, testování, Git, CI/CD, SRE a release engineering řídí
WORLD. Konflikt znamená `BLOCKED`.

## 1. Produktová čistota

Produkt musí mít jeden jasný hlavní účel a souvislé hlavní workflow.

Preferuj:

- kvalitu klíčového výsledku před počtem funkcí,
- odstranění zbytečnosti před přidáním další vrstvy,
- explicitní ne-cíle,
- malé vertikální řezy,
- využití existujícího standardu nebo nástroje před vlastní náhradou.

Požadavek odmítni nebo vrať do discovery, pokud jeho doložená hodnota
nepřevyšuje dlouhodobou složitost, provozní cenu a riziko.

Roadmapa není seznam všeho, co lze implementovat. Je to pořadí nejdůležitějších
problémů a explicitních rozhodnutí, co se implementovat nebude.

## 2. Ověřený problém

Významná implementace nesmí začít pouze na základě:

- preference,
- technologického trendu,
- konkurenčního seznamu funkcí,
- jednorázové žádosti bez kontextu,
- domněnky AI,
- abstraktního požadavku na enterprise readiness.

Minimálně urči:

- uživatele nebo stakeholdera,
- konkrétní problém,
- současný způsob řešení,
- frekvenci a náklad,
- očekávaný outcome,
- způsob měření,
- ne-cíle,
- vlastníka.

Pro významnou investici požaduj zpravidla alespoň dva nezávislé signály, například:

- uživatelské pozorování,
- opakovaný incident nebo support pattern,
- reprodukovatelný časový nebo finanční náklad,
- auditní nebo regulatorní požadavek,
- bezpečnostní analýzu,
- data o adopci, kvalitě nebo selhávání.

Jeden autoritativní signál může být dostatečný pouze tehdy, když jde o závazný
právní, regulatorní, smluvní nebo kritický bezpečnostní požadavek a záznam
explicitně vysvětlí jeho autoritu, scope, deadline, riziko a vlastníka.

Bez dostatečné evidence smí práce pokračovat pouze jako `DISCOVERY` nebo
omezený `EXPERIMENT`.

## 3. Úrovně evidence

### E0 — domněnka

Názor, intuice nebo neověřený návrh. Stav `PROPOSED`, `INFERRED` nebo `UNKNOWN`.

### E1 — kvalitativní signál

Jednotlivý rozhovor, incident, support požadavek nebo expertní posouzení.

### E2 — opakovaný vzorec

Více uživatelů, incidentů nebo reprodukovatelných manuálních nákladů.

### E3 — měřitelný důkaz

Baseline, benchmark, test, audit, threat model nebo pilotní data.

### E4 — ověřený dopad

Výsledek po skutečném použití, měřený proti baseline a bez nepřijatelných
vedlejších dopadů.

Síla důkazu musí odpovídat nákladům, riziku a nevratnosti rozhodnutí.

## 4. Discovery

Discovery může zahrnovat:

- rozhovory a pozorování,
- analýzu workflow a incidentů,
- prototyp,
- concierge test,
- spike,
- benchmark,
- threat modeling,
- pilotní integraci,
- test dokumentace nebo API kontraktu.

Výstup discovery musí uvést:

- zjištění,
- neznámé body,
- vyvrácené předpoklady,
- zbývající předpoklady,
- sílu evidence,
- nejmenší další bezpečný experiment.

Discovery není důkaz produkční připravenosti.

## 5. Rozhodovací model

Každé významné rozhodnutí musí obsahovat:

- ID,
- vlastníka,
- kontext a problém,
- evidence,
- varianty,
- vybranou variantu,
- důvody,
- ne-cíle,
- rizika,
- dopady,
- rollback nebo migraci,
- datum přezkoumání,
- stav.

Klasifikuj vratnost:

- `REVERSIBLE`,
- `COSTLY_TO_REVERSE`,
- `EFFECTIVELY_IRREVERSIBLE`.

Klasifikuj riziko:

- `LOW`,
- `MEDIUM`,
- `HIGH`,
- `CRITICAL`.

Rozhodnutí `HIGH`, `CRITICAL`, `COSTLY_TO_REVERSE` nebo
`EFFECTIVELY_IRREVERSIBLE` vyžaduje ADR a explicitní schválení.

Přijaté rozhodnutí se tiše nepřepisuje. Použij supersession nebo nový záznam.

## 6. Prioritizace

Posuzuj:

- uživatelský dopad,
- strategickou shodu,
- sílu evidence,
- snížení rizika,
- compliance povinnost,
- časovou citlivost,
- provozní náklad,
- effort,
- komplexitu,
- závislosti,
- vratnost,
- opportunity cost.

Skóre je podpůrný nástroj, nikoliv automatická autorita. Vysoká priorita musí
mít textové odůvodnění, ownera a outcome metriku.

Používej horizonty:

- `NOW` — schválená a připravená práce,
- `NEXT` — validovaný problém, ale ne nutně připravená implementace,
- `LATER` — strategický směr s vyšší nejistotou,
- `NOT PLANNED` — vědomě odmítnutá nebo odložená oblast.

## 7. Experiment

Experiment musí předem určit:

- hypotézu,
- cílovou skupinu,
- baseline,
- měřený signál,
- práh úspěchu a selhání,
- časový rámec,
- maximální náklad,
- rizika,
- rollback,
- pravidlo ukončení,
- vlastníka.

Negativní výsledek je validní evidence. Metriky se po skončení nesmí účelově
měnit.

Experimentální funkce musí být označená, vratná, časově omezená a oddělená od
stabilního rozhraní.

## 8. Definition of Ready

Významná práce je `READY`, pokud jsou relevantně splněny:

- problém je ověřen,
- uživatel je znám,
- outcome a baseline jsou definovány,
- scope a ne-scope jsou explicitní,
- owner je určen,
- acceptance criteria jsou testovatelná,
- závislosti a rizika jsou známé,
- security, privacy a datový dopad jsou posouzeny,
- observabilita a evidence jsou naplánovány,
- rollback je znám,
- dokumentační, release a adopční dopad je znám,
- požadovaná schválení jsou známá,
- nejmenší vertikální řez je identifikován.

Nesplněná kritická položka znamená `BLOCKED`. Brána se nesmí používat jako
byrokratická překážka pro malé, nízkorizikové a vratné změny.

## 9. Realizační lifecycle

```text
PROBLEM SIGNAL
→ DISCOVERY
→ PROBLEM VERIFIED
→ PROPOSED
→ APPROVED
→ READY
→ IMPLEMENTED
→ VERIFIED
→ RELEASE APPROVED
→ RELEASED
→ ADOPTED
→ IMPACT VERIFIED
→ MAINTAINED OR RETIRED
```

Každý přechod musí mít vstupní podmínky, ownera, evidence, výstup, stav a
možnost zastavení nebo rollbacku.

Schválení produktu, implementace, commit, push, tag, release a deployment jsou
samostatné brány definované koordinačním rámcem.

## 10. Ownership a RACI

Každá významná iniciativa musí mít právě jednoho `ACCOUNTABLE` vlastníka,
pokud není explicitně schválen jiný model.

Dále určuj:

- `RESPONSIBLE`,
- `CONSULTED`,
- `INFORMED`.

Vlastník odpovídá za priority, správnost stavu, rizika, přezkum, deprecation,
provozní dopady a ukončení neúspěšné iniciativy.

Neznámý owner znamená `BLOCKED` pro vysokorizikovou změnu.

## 11. Definition of Done a produktový dopad

Technická Definition of Done je určena WORLD.

Produktová práce navíc vyžaduje:

- připravený rollout,
- onboarding a support,
- adopční signál,
- plán měření dopadu,
- datum post-implementation review.

Implementace, commit, release nebo deployment samy nedokazují produktový
úspěch. Produktový dopad lze označit `VERIFIED` až po skutečném použití a
měření proti baseline.

## 12. Rollout a adopce

Preferuj:

```text
internal dogfood
→ isolated pilot
→ limited beta
→ broader adoption
→ stable support
```

Každá fáze musí určit cílové uživatele, onboarding, support, compatibility,
metriky, kritéria rozšíření, kritéria zastavení a rollback.

## 13. KPI a OKR

KPI popisují zdraví systému. OKR popisují změnu výsledku.

OKR nesmí být seznam úkolů. Samotný počet dokumentů, pravidel, pluginů, commitů
nebo řádků kódu není produktová metrika.

Měř podle relevance:

- task success rate,
- time to value,
- počet ručních kroků,
- false-positive a false-negative rate,
- governance drift detection time,
- remediation lead time,
- adopci a retenci,
- developer satisfaction,
- audit preparation time,
- change lead time a change fail rate.

Každá metrika musí mít baseline, target, časový horizont, ownera, zdroj dat a
ochranu proti gaming.

## 14. Post-implementation review

Přezkum odpoví:

- byl problém skutečně vyřešen,
- používali uživatelé schopnost,
- odpovídá dopad očekávání,
- vznikly vedlejší náklady nebo incidenty,
- zvýšila se složitost,
- má být schopnost rozšířena, zachována, omezena nebo odstraněna,
- které předpoklady byly chybné.

Výsledek označ `VERIFIED`, `PARTIALLY VERIFIED`, `INFERRED`, `UNKNOWN` nebo
`BLOCKED`.

## 15. Deprecation a retirement

Deprecation musí obsahovat důvod, ownera, dotčené uživatele, náhradní cestu,
časový plán, usage evidence, komunikaci, compatibility a rollback.

Funkce bez uživatelů, vlastníka, podpory nebo strategické hodnoty je kandidátem
na odstranění. Odstranění vyžaduje důkazní audit a vratný postup.

## 16. Zákaz překomplikování

Preferuj:

- soubor před databází,
- knihovnu před službou,
- CLI před serverem,
- standard před vlastním formátem,
- explicitní adaptér před magickou integrací,
- statický report před dashboardem,
- deterministické pravidlo před AI rozhodnutím,
- plugin contract před forkem.

Bez ověřeného problému neimplementuj:

- grafovou databázi,
- SaaS control plane,
- vlastní policy jazyk,
- autonomního AI agenta s canonical write,
- univerzální workflow engine,
- mikroservisy,
- vlastní developer portal,
- desítky integrací,
- vlastní transparency log.

Každá nová abstrakce musí uvést, jak ji lze odstranit.

## 17. AI-assisted práce

AI smí navrhovat text, varianty, testy, klasifikace a možné rozpory.

AI výstup musí podle rizika uvést model nebo nástroj, vstupy, zdroje, omezení,
předpoklady, nejistotu a požadovanou lidskou kontrolu.

AI nesmí sama schválit návrh, risk acceptance, canonical write ani produktový
dopad. Hranice dalších operací určuje koordinační rámec a WORLD.
