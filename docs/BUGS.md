# Bugs

## Open
- [ ] [HIGH] Sync überschreibt neuere Datei — Beim Sync wird die neuere Zieldatei durch eine ältere Quelldatei überschrieben
- [ ] [MED] Fehlende Fehlerausgabe — Bei fehlenden Berechtigungen wird kein verständlicher Fehler ausgegeben

## In Progress
- [ ] [LOW] Log-Datei wächst unbegrenzt — Kein Log-Rotation-Mechanismus vorhanden

## Fixed
- [x] [HIGH] Lösch-Dialog erscheint auf allen Geräten — `suppress_delete`-Pattern verhindert, dass watchdog die remoteseitig ausgelöste Löschung als lokales Ereignis behandelt. `SyncServer` ruft `on_before_delete` vor dem Löschen auf, `FileWatcher` unterdrückt das nächste Delete-Event für diesen Pfad.
- [x] [HIGH] Absturz bei leerem Verzeichnis — NullPointerException wenn Quellverzeichnis leer ist
