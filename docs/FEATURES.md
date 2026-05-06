# Features

## Backlog
- [ ] Peer-to-Peer Sync — Dateien direkt zwischen Rechnern im lokalen Netzwerk übertragen (kein zentraler Server)
- [ ] Auto-Discovery — andere FileSyncro-Instanzen im Netzwerk automatisch via mDNS/zeroconf finden
- [ ] Manuelle IP-Eingabe — Geräte alternativ per IP-Adresse manuell hinzufügen
- [ ] Datei-Watching — Änderungen im Sync-Ordner automatisch erkennen und sofort synchronisieren (watchdog, 500ms Debounce)
- [ ] Manueller Sync — Button zum sofortigen Abgleich aller Dateien mit allen verbundenen Geräten
- [ ] Konflikt-Erkennung — bei gleichzeitiger Änderung derselben Datei Dialog anzeigen, Nutzer entscheidet welche Version bleibt
- [ ] Lösch-Bestätigung — bei Dateilöschung fragen ob nur lokal oder auf allen Geräten gelöscht werden soll
- [ ] Fortschrittsanzeige — Fortschrittsbalken pro Datei bei großen Übertragungen (z.B. Videos)
- [ ] Fehlerbehandlung — Retry bei fehlgeschlagener Übertragung, Statusanzeige pro Gerät (erreichbar/nicht erreichbar)
- [ ] GUI — grafische Oberfläche mit Geräteliste, Aktivitätslog, Sync-Ordner-Auswahl und Dialogen
- [ ] Windows-Build — standalone FileSyncro.exe ohne Installationserfordernis
- [ ] macOS-Build — standalone FileSyncro.app ohne Installationserfordernis

- [ ] Web-Interface — optionale Browser-Oberfläche (aiohttp + HTML) auf Port 5757, damit iPads und andere Geräte ohne App den Sync-Status einsehen, Dateien hochladen und einen Sync anstoßen können
- [ ] GitHub Release — automatisches Release bei neuem Tag, damit Builds dauerhaft als Download verfügbar sind (nicht nur 90 Tage als Artefakt)
- [ ] Peer-Erreichbarkeit prüfen — "Aktualisieren"-Button in der Geräteliste, der alle Peers per HTTP-Ping anpingt und den Status (erreichbar/nicht erreichbar) sofort aktualisiert; nicht antwortende Geräte werden automatisch entfernt
- [ ] Einzelne Datei manuell pushen — Rechtsklick auf eine Datei im Sync-Ordner (oder Auswahl im Log) zum gezielten Übertragen an einen oder alle Peers; nützlich wenn eine automatische Übertragung fehlgeschlagen ist
- [ ] Peer-Auswahl per Checkbox — Checkbox neben jedem Gerät in der Liste; nur angehakte Geräte nehmen am automatischen Sync und am manuellen Sync-Button teil

## In Progress

## Done
- [x] Projektstruktur — Grundlegende Verzeichnis- und Dateistruktur angelegt
