# OATHDO

**OATHDO** je deterministický dokumentační governor pro projekty řízené lidmi i AI agenty. Propojuje změny v repozitáři s dokumentací, rozhodnutími, schváleními a auditní evidencí, které mají změnu doprovázet.

!!! important "Prezentační vrstva"
    Tento web je odvozená prezentační vrstva. Kanonickým zdrojem pravdy jsou soubory a Git historie repozitáře OATHDO. Build webu nemění canonical governance obsah a není automaticky publikován.

!!! note "CLI kompatibilita"
    Produktový a repozitářový název je OATHDO. Python package a CLI v aktuální kompatibilní řadě stále používají jméno `goverdocs`.

## Co systém poskytuje

- deterministickou klasifikaci změn,
- rozhodovací matici a plán dokumentačních operací,
- validaci metadata, vztahů, supersession a lokálních odkazů,
- registry, relationship graph a auditní receipts,
- explicitní approval a authority hranice,
- exact-head GitHub governance enforcement,
- reprodukovatelné distribuční artefakty.

## Bezpečnostní hranice

OATHDO v0.1 neobsahuje autonomní canonical writer. LLM může navrhnout text, ale nesmí schválit vlastní canonical zápis ani nahradit požadovanou lidskou authority.

## Aktuální governance milestone

R11 multi-actor authority model je canonical a fail-closed negativní enforcement je live ověřen. Finální stav `FULLY VERIFIED` vyžaduje ještě pozitivní live critical proof se dvěma rozdílnými non-author authority aktéry.

Pokračuj na [rychlý start](getting-started.md) nebo na vysvětlení [governance modelu](governance-model.md).
