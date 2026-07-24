# Governance model

## Tok změny

```text
Project change
  → deterministic classification
  → decision matrix
  → operation plan
  → validation
  → human approval
  → future controlled writer
  → registry, graph and audit receipt
```

Aktuální verze končí před controlled writerem.

## Autorita

1. Projektový filesystem a Git historie jsou canonical.
2. Chat, export nebo ZIP jsou pouze snapshoty.
3. Povolené operace určuje deterministická policy.
4. LLM nemůže schválit vlastní výstup.
5. Přijaté rozhodnutí se superseduje, nikoli tiše přepisuje.
6. Selhání validace blokuje canonical write.

## Write policy

| Třída | Význam |
|---|---|
| `automatic` | Strukturovaný, měnitelný projektový stav |
| `append-only` | Chronologický registr s opravami formou nových záznamů |
| `approval-required` | Canonical změnu musí schválit vlastník |
| `immutable` | Přijatý důkaz se nemění |
| `generated` | Odvozený výstup se přestavuje z canonical zdrojů |

Podrobné normativní znění zůstává v kanonických dokumentech repozitáře.
