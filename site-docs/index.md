# GOVERDOCS

GOVERDOCS je deterministický dokumentační governor pro projekty řízené lidmi
i AI agenty. Propojuje změny v repozitáři s dokumentací, rozhodnutími,
schváleními a auditní evidencí, které mají změnu doprovázet.

!!! important "Prezentační vrstva"
    Tento web je odvozená prezentační vrstva. Kanonickým zdrojem pravdy jsou
    soubory a Git historie repozitáře GOVERDOCS. Build webu nemění canonical
    governance obsah a není automaticky publikován.

## Co systém poskytuje

- deterministickou klasifikaci změn,
- rozhodovací matici a plán dokumentačních operací,
- validaci metadata, vztahů, supersession a lokálních odkazů,
- registry, relationship graph a auditní receipts,
- explicitní approval hranice,
- reprodukovatelné distribuční artefakty.

## Bezpečnostní hranice

GOVERDOCS v0.1 neobsahuje AI writer ani autonomní příkaz `apply`. LLM může
navrhnout text, ale nesmí schválit vlastní canonical zápis.

Pokračuj na [rychlý start](getting-started.md) nebo na vysvětlení
[governance modelu](governance-model.md).
