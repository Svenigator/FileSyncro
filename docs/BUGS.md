# Bugs

## Open

## In Progress

## Fixed
- [x] [HIGH] Sync überschreibt neuere Datei — SyncServer auto-rejects incoming files where `local_ts > remote_ts + 1.0`, returning 409 `outdated` without invoking the conflict dialog.
- [x] [MED] Gerät bleibt nach Programmende in der Liste — Periodic 30s ping removes non-responding peers automatically; on-demand Refresh button available for immediate check.
- [x] [MED] Fehlende Fehlerausgabe bei fehlenden Berechtigungen — `_handle_put` catches `PermissionError` and returns HTTP 403 with the error message.
- [x] [LOW] Log-Datei wächst unbegrenzt — In-memory activity log capped at 500 lines; oldest lines removed automatically.
- [x] [MED] Öffnen-Button verschwindet bei langem Pfad — Button packed with `side="right"` before the label so it stays anchored regardless of path length.
- [x] [HIGH] Lösch-Dialog erscheint auf allen Geräten — `suppress_delete` pattern prevents watchdog from re-triggering after a remote-initiated deletion.
- [x] [HIGH] Absturz bei leerem Verzeichnis — NullPointerException wenn Quellverzeichnis leer ist.
