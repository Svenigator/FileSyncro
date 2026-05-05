# FileSyncro Design

**Datum:** 2026-05-05  
**Status:** Approved

---

## Problem

Bei Veranstaltungen (Tagungen, Konferenzen) laufen Präsentationen und Videos auf mehreren Laptops (Windows und macOS). Referenten liefern Dateien per USB-Stick — diese müssen manuell auf alle Rechner kopiert werden. FileSyncro eliminiert diesen manuellen Schritt durch automatische Peer-to-Peer-Synchronisation im lokalen Netzwerk.

---

## Ziel

Eine plattformübergreifende Desktop-App, die Dateien automatisch zwischen 2–10 Rechnern im selben lokalen Netzwerk synchronisiert. Keine Installation erforderlich, kein zentraler Server, kein Internet.

---

## Tech Stack

| Zweck | Library |
|---|---|
| GUI | `customtkinter` |
| HTTP-Server/-Client | `aiohttp` |
| Datei-Watching | `watchdog` |
| mDNS-Discovery | `zeroconf` |
| Packaging | `pyinstaller` |
| Sprache | Python 3.11+ |

---

## Architektur

Jede FileSyncro-Instanz ist ein gleichwertiger **Peer** — kein zentraler Server. Jeder Rechner kann Dateien senden und empfangen.

Jede Instanz besteht aus vier parallel laufenden Bausteinen:

```
┌─────────────────────────────────────────┐
│              FileSyncro App             │
│                                         │
│  ┌──────────┐     ┌──────────────────┐  │
│  │   GUI    │◄────│  Peer Manager    │  │
│  │(CustomTk)│     │(bekannte Geräte) │  │
│  └──────────┘     └────────┬─────────┘  │
│                            │            │
│  ┌──────────┐     ┌────────▼─────────┐  │
│  │  File    │────►│   Sync Server    │  │
│  │ Watcher  │     │  (HTTP Port 5757)│  │
│  │(watchdog)│     └────────┬─────────┘  │
│  └──────────┘              │            │
│  ┌─────────────────────────▼──────────┐ │
│  │     Discovery (zeroconf/mDNS)      │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Bausteine

**GUI (customtkinter)**
- Hauptfenster mit Geräteliste, Sync-Ordner-Auswahl, Aktivitätslog
- Konflikt-Dialog: zeigt beide Versionen (Timestamp, Größe), Nutzer wählt
- Lösch-Dialog: "Nur lokal" oder "Alle Geräte"
- Fortschrittsbalken für große Dateiübertragungen

**Sync Server (aiohttp)**
- HTTP-Server auf Port 5757 auf allen Interfaces
- `PUT /file` — empfängt Datei von einem Peer
- `DELETE /file` — empfängt Löschbefehl von einem Peer
- `GET /files` — gibt Liste aller lokalen Dateien mit Timestamps zurück

**File Watcher (watchdog)**
- Beobachtet den konfigurierten Sync-Ordner rekursiv
- 500ms Debounce um Doppel-Trigger beim Speichern zu vermeiden
- Bei Änderung/Neuanlage: Datei an alle Peers pushen
- Bei Löschung: Lösch-Dialog anzeigen

**Discovery (zeroconf)**
- Meldet sich unter `_filesyncro._tcp.local.` im Netzwerk an
- Entdeckt andere Instanzen automatisch
- Manuelle IP-Eingabe als Fallback (wird zur Peer-Liste hinzugefügt)

---

## GUI-Layout

```
┌─────────────────────────────────────────┐
│  FileSyncro                             │
├─────────────────────────────────────────┤
│  Sync-Ordner: [C:\Veranstaltung\  ] [...]  │
├─────────────────────────────────────────┤
│  Verbundene Geräte                      │
│  ┌─────────────────────────────────┐    │
│  │ ● MacBook-Pro-Thomas   192.168… │    │
│  │ ● WIN-PC-Bühne         192.168… │    │
│  │ ○ (manuell hinzufügen…)         │    │
│  └─────────────────────────────────┘    │
├─────────────────────────────────────────┤
│  [Jetzt synchronisieren]   Status: OK   │
│  Aktivität:                             │
│  ✓ vortrag_mueller.pptx → 2 Geräte     │
│  ✓ intro_video.mp4 → 2 Geräte          │
└─────────────────────────────────────────┘
```

---

## Sync-Logik

### Datei hinzugefügt / geändert (automatisch)
1. `watchdog` erkennt Änderung
2. 500ms Debounce
3. HTTP-PUT an alle bekannten Peers (Datei + Timestamp im Header)
4. Peer prüft:
   - Datei existiert nicht → direkt speichern
   - Gleicher Timestamp → ignorieren
   - Anderer Timestamp → Konflikt-Dialog

### Manueller Sync
1. `GET /files` von jedem Peer abrufen
2. Timestamps vergleichen
3. Fehlende oder neuere Dateien übertragen

### Datei gelöscht
1. `watchdog` erkennt Löschung
2. Dialog: "Nur lokal" oder "Alle Geräte"
3. Bei "Alle Geräte": HTTP-DELETE an alle Peers

### Neues Gerät im Netzwerk
1. mDNS meldet neuen Peer
2. Erscheint in der Geräteliste
3. Kein automatischer Full-Sync — Nutzer löst manuell aus

---

## Fehlerbehandlung

| Situation | Verhalten |
|---|---|
| Peer nicht erreichbar | Rotes Symbol in Geräteliste, Eintrag im Aktivitätslog |
| Übertragung fehlgeschlagen | Einmaliger Retry nach 3s, dann manueller Retry-Button |
| Sync-Ordner nicht gefunden | Warnung beim Start, Ordner-Auswahl öffnet sich |
| Große Datei (Video) | Fortschrittsbalken im Aktivitätslog |

---

## Packaging & Distribution

| Plattform | Output | Voraussetzung |
|---|---|---|
| Windows | `FileSyncro.exe` (single file) | Keine Installation |
| macOS | `FileSyncro.app` (App-Bundle) | Rechtsklick → Öffnen beim ersten Start (Gatekeeper) |

Zielgröße: ~50–70 MB. Erstellt mit PyInstaller aus demselben Codebase.

---

## Nicht im Scope

- Ende-zu-Ende-Verschlüsselung (Veranstaltungsnetz wird als vertrauenswürdig betrachtet)
- Versionierung / Backup alter Dateien
- Sync über Internet
- Mobile Apps
