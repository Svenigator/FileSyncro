# FileSyncro

Peer-to-Peer Datei-Synchronisation für Veranstaltungen. Verteilt Präsentationen und Videos automatisch auf alle Laptops im lokalen Netzwerk — kein USB-Stick, kein manuelles Kopieren.

## Voraussetzungen

Keine Installation erforderlich. Einfach die Executable starten.

- **Windows:** `FileSyncro.exe` herunterladen und starten
- **macOS:** `FileSyncro.app` herunterladen, Rechtsklick → "Öffnen" (nur beim ersten Start nötig)

Die aktuellen Builds findest du unter [Actions → Artifacts](../../actions).

---

## Benutzung

### 1. App starten

Starte FileSyncro auf allen Laptops im gleichen Netzwerk (WLAN oder LAN).

### 2. Sync-Ordner wählen

Klicke auf `...` und wähle den Ordner, in dem deine Präsentationen und Videos liegen sollen. Dieser Ordner wird auf allen Geräten synchronisiert.

### 3. Geräte verbinden

Andere FileSyncro-Instanzen im Netzwerk werden **automatisch erkannt** und erscheinen in der Geräteliste (grüner Punkt = erreichbar).

Falls ein Gerät nicht automatisch erscheint: IP-Adresse manuell eingeben und auf "Hinzufügen" klicken.

### 4. Dateien synchronisieren

**Automatisch:** Kopiere eine Datei in den Sync-Ordner — sie wird sofort auf alle verbundenen Geräte übertragen.

**Manuell:** Klicke auf "Jetzt synchronisieren" um alle Unterschiede abzugleichen.

### Konflikt

Wenn dieselbe Datei auf zwei Geräten gleichzeitig geändert wurde, erscheint ein Dialog:

```
Konflikt: vortrag.pptx
  Lokal:  15:32 Uhr
  Remote: 15:34 Uhr  (MacBook-Thomas)

  [Lokale Version behalten]  [Remote übernehmen]
```

### Datei löschen

Wenn du eine Datei löschst, fragt FileSyncro:

```
vortrag_alt.pptx wurde gelöscht.
Auf allen Geräten löschen oder nur lokal?

  [Nur lokal]  [Alle Geräte]
```

---

## Entwicklung

### Setup

```bash
git clone https://github.com/Svenigator/FileSyncro.git
cd FileSyncro
pip install -r requirements.txt -r requirements-dev.txt
```

### App starten

```bash
python -m src.main
```

### Tests

```bash
pytest -v
```

### Build

```bash
pip install pyinstaller
python build.py
```

Erzeugt `dist/FileSyncro.exe` (Windows) oder `dist/FileSyncro.app` (macOS).

---

## Tech Stack

| Komponente | Technologie |
|---|---|
| GUI | customtkinter |
| HTTP-Sync | aiohttp |
| Datei-Watching | watchdog |
| Netzwerk-Discovery | zeroconf (mDNS) |
| Build | PyInstaller |

---

## Funktionsweise

Jede FileSyncro-Instanz ist ein gleichwertiger **Peer** — es gibt keinen zentralen Server. Jedes Gerät läuft gleichzeitig als Sender und Empfänger auf Port **5757**.

Geräte finden sich gegenseitig automatisch via **mDNS** (`_filesyncro._tcp.local.`). Dateien werden per **HTTP PUT** übertragen und anhand ihres Timestamps auf Konflikte geprüft.
