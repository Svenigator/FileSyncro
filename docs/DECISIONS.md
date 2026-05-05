# Architecture Decision Records

## ADR-001: Markdown als Tracker-Format
- **Datum:** 2026-05-05
- **Status:** Accepted
- **Kontext:** Für FileSyncro wird ein einfacher Weg benötigt, Features, Bugs und Entscheidungen zu verfolgen, ohne ein externes Tool einzuführen.
- **Entscheidung:** Drei Markdown-Dateien (FEATURES.md, BUGS.md, DECISIONS.md) im `docs/`-Verzeichnis dienen als leichtgewichtiger Tracker. Alles bleibt im Repository versioniert.
- **Konsequenzen:** Kein externes Tool nötig. Änderungen sind per Git nachvollziehbar. Kein automatisiertes Reporting oder Filtering möglich.

## ADR-002: Prioritäts-Präfixe in BUGS.md
- **Datum:** 2026-05-05
- **Status:** Accepted
- **Kontext:** Bugs haben unterschiedliche Dringlichkeit. Eine visuelle Priorisierung direkt im Text spart das Öffnen eines externen Tools.
- **Entscheidung:** Jeder Bug-Eintrag trägt einen Präfix: `[HIGH]`, `[MED]` oder `[LOW]`.
- **Konsequenzen:** Priorität ist auf einen Blick erkennbar. Bei Statusänderung muss nur die Checkbox geändert werden, nicht der Präfix.
