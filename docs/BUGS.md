# Bugs

## Open
- [ ] [HIGH] Lösch-Dialog erscheint auf allen Geräten — Wenn Gerät A eine Datei löscht und "Alle Geräte" wählt, empfangen die anderen Geräte den DELETE-Befehl, watchdog erkennt die Löschung lokal und zeigt den Dialog erneut an. Die Entscheidung sollte nur auf dem auslösenden Gerät getroffen werden.
- [ ] [HIGH] Sync überschreibt neuere Datei — Beim Sync wird die neuere Zieldatei durch eine ältere Quelldatei überschrieben
- [ ] [MED] Fehlende Fehlerausgabe — Bei fehlenden Berechtigungen wird kein verständlicher Fehler ausgegeben

## In Progress
- [ ] [LOW] Log-Datei wächst unbegrenzt — Kein Log-Rotation-Mechanismus vorhanden

## Fixed
- [x] [HIGH] Absturz bei leerem Verzeichnis — NullPointerException wenn Quellverzeichnis leer ist
