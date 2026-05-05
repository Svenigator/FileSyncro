# Bugs

## Open
- [ ] [HIGH] Sync überschreibt neuere Datei — Beim Sync wird die neuere Zieldatei durch eine ältere Quelldatei überschrieben
- [ ] [MED] Fehlende Fehlerausgabe — Bei fehlenden Berechtigungen wird kein verständlicher Fehler ausgegeben

## In Progress
- [ ] [LOW] Log-Datei wächst unbegrenzt — Kein Log-Rotation-Mechanismus vorhanden

## Fixed
- [x] [HIGH] Absturz bei leerem Verzeichnis — NullPointerException wenn Quellverzeichnis leer ist
