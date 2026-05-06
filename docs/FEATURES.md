# Features

## Backlog
- [ ] Fortschrittsanzeige — Fortschrittsbalken pro Datei bei großen Übertragungen (z.B. Videos)
- [ ] Web-Interface — optionale Browser-Oberfläche (aiohttp + HTML) auf Port 5757, damit iPads und andere Geräte ohne App den Sync-Status einsehen, Dateien hochladen und einen Sync anstoßen können
- [ ] GitHub Release — automatisches Release bei neuem Tag, damit Builds dauerhaft als Download verfügbar sind (nicht nur 90 Tage als Artefakt)

## In Progress

## Done
- [x] Projektstruktur — Grundlegende Verzeichnis- und Dateistruktur angelegt
- [x] Peer-to-Peer Sync — Dateien direkt zwischen Rechnern im lokalen Netzwerk übertragen (kein zentraler Server)
- [x] Auto-Discovery — andere FileSyncro-Instanzen im Netzwerk automatisch via mDNS/zeroconf finden
- [x] Manuelle IP-Eingabe — Geräte alternativ per IP-Adresse manuell hinzufügen
- [x] Datei-Watching — Änderungen im Sync-Ordner automatisch erkennen und sofort synchronisieren (watchdog, 500ms Debounce)
- [x] Manueller Sync — Button zum sofortigen Abgleich aller Dateien mit allen verbundenen Geräten
- [x] Konflikt-Erkennung — bei gleichzeitiger Änderung derselben Datei Dialog anzeigen, Nutzer entscheidet welche Version bleibt
- [x] Lösch-Bestätigung — bei Dateilöschung fragen ob nur lokal oder auf allen Geräten gelöscht werden soll
- [x] Fehlerbehandlung — Retry bei fehlgeschlagener Übertragung, Statusanzeige pro Gerät (erreichbar/nicht erreichbar)
- [x] GUI — grafische Oberfläche mit Geräteliste, Aktivitätslog, Sync-Ordner-Auswahl und Dialogen
- [x] Windows-Build — standalone FileSyncro.exe ohne Installationserfordernis
- [x] macOS-Build — standalone FileSyncro.app ohne Installationserfordernis
- [x] Peer-Erreichbarkeit prüfen — Refresh-Button pingt alle Peers an, entfernt nicht erreichbare automatisch
- [x] Einzelne Datei manuell pushen — gezieltes Nachsenden einer Datei an einen oder alle Peers
- [x] Peer-Auswahl & Gruppen — Geräte Gruppen mit benutzerdefinierten Namen zuordnen, aktive Gruppe wählt Sync-Teilnehmer
