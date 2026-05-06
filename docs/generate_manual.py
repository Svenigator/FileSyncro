#!/usr/bin/env python3
"""Generates FileSyncro_Manual.pdf with UI mockup screenshots."""
from __future__ import annotations
import io
from pathlib import Path
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

# ─── palette (CustomTkinter dark mode) ────────────────────────────────────
BG       = (30, 30, 30)
FRAME    = (54, 54, 54)
BLUE     = (31, 106, 165)
BLUE2    = (55, 130, 195)
GRAY_BTN = (82, 82, 82)
TEXT     = (215, 215, 215)
GRAY     = (138, 138, 138)
ENTRY    = (52, 54, 56)
GREEN    = (88, 196, 114)
RED      = (206, 76, 76)
ORANGE   = (224, 152, 48)
WHITE    = (255, 255, 255)

_FONTS = {
    False: "C:/Windows/Fonts/arial.ttf",
    True:  "C:/Windows/Fonts/arialbd.ttf",
}

def _f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(_FONTS[bold], size)
    except OSError:
        return ImageFont.load_default(size=size)

# ─── low-level drawing helpers ─────────────────────────────────────────────
def rr(d: ImageDraw.ImageDraw, xy, r: int, fill, outline=None, ow: int = 1):
    d.rounded_rectangle(list(xy), radius=r, fill=fill, outline=outline, width=ow)

def btn(d, xy, text: str, color=BLUE, tc=WHITE, fs: int = 13, r: int = 8):
    rr(d, xy, r, fill=color)
    x0, y0, x1, y1 = xy
    f = _f(fs, bold=True)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.text((cx - tw // 2, cy - th // 2), text, fill=tc, font=f)

def lbl(d, xy, text: str, size: int = 13, color=TEXT, bold: bool = False):
    d.text(xy, text, fill=color, font=_f(size, bold))

def inp(d, xy, text: str = "", ph: str = "", size: int = 12):
    rr(d, xy, 6, fill=ENTRY, outline=(88, 88, 88), ow=1)
    x0, y0, x1, y1 = xy
    h = y1 - y0
    f = _f(size)
    content, color = (text, TEXT) if text else (ph, GRAY)
    bb = d.textbbox((0, 0), content, font=f)
    th = bb[3] - bb[1]
    d.text((x0 + 8, y0 + (h - th) // 2), content, fill=color, font=f)

def titlebar(d, W: int, title: str):
    rr(d, [0, 0, W, 36], 10, fill=(42, 42, 42))
    f = _f(14, bold=True)
    bb = d.textbbox((0, 0), title, font=f)
    tw = bb[2] - bb[0]
    d.text((W // 2 - tw // 2, 10), title, fill=WHITE, font=f)
    for i, c in enumerate([(206, 76, 76), (200, 158, 56), (88, 196, 114)]):
        cx = 16 + i * 22
        d.ellipse([cx - 6, 12, cx + 6, 24], fill=c)

def badge(d, cx: int, cy: int, text: str):
    r = 11
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE, outline=WHITE, width=2)
    f = _f(11, bold=True)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((cx - tw // 2, cy - th // 2 - 1), text, fill=WHITE, font=f)

def png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf.read()


# ─── screenshot 1: empty main window with callout badges ──────────────────
def ss_main() -> bytes:
    W, H = 560, 700
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    titlebar(d, W, "FileSyncro")

    # sync folder
    rr(d, [16, 52, W - 16, 84], 8, fill=FRAME)
    lbl(d, (24, 62), "Sync-Ordner:", size=12)
    btn(d, [W - 60, 57, W - 22, 79], "...", r=6, fs=12)
    lbl(d, (128, 62), "C:/Users/Benutzer/FileSyncro", size=11, color=GRAY)

    # group row
    lbl(d, (16, 97), "Gruppe:", size=12)
    rr(d, [72, 91, 256, 114], 8, fill=ENTRY, outline=(88, 88, 88), ow=1)
    lbl(d, (80, 97), "Alle Geräte", size=11, color=GRAY)
    d.polygon([(242, 99), (252, 99), (247, 108)], fill=GRAY)
    btn(d, [264, 91, 348, 114], "Verwalten", color=GRAY_BTN, fs=11)

    # devices
    lbl(d, (16, 128), "Verbundene Geräte", size=12, bold=True)
    rr(d, [16, 148, W - 16, 258], 10, fill=(38, 38, 38))
    lbl(d, (W // 2 - 82, 196), "Keine Geräte verbunden", size=11, color=GRAY)

    # manual row
    inp(d, [16, 270, 180, 294], ph="IP-Adresse")
    btn(d, [184, 270, 276, 294], "Hinzufügen", fs=11)
    btn(d, [280, 270, 396, 294], "Aktualisieren", color=GRAY_BTN, fs=11)

    # sync + status
    btn(d, [16, 308, 200, 334], "Jetzt synchronisieren", fs=12)
    lbl(d, (210, 316), "Status: bereit", size=12, color=GRAY)

    # log
    lbl(d, (16, 348), "Aktivität", size=12, bold=True)
    rr(d, [16, 368, W - 16, 684], 10, fill=(38, 38, 38))

    # callout badges
    badge(d, W - 24, 68,  "1")  # sync folder
    badge(d, W - 24, 102, "2")  # group
    badge(d, W - 24, 200, "3")  # device list
    badge(d, 398, 282,     "4")  # add / refresh
    badge(d, 202, 321,     "5")  # sync button
    badge(d, W - 24, 480, "6")  # log

    return png(img)


# ─── screenshot 2: main window with peers ─────────────────────────────────
def ss_peers() -> bytes:
    W, H = 560, 700
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    titlebar(d, W, "FileSyncro")

    rr(d, [16, 52, W - 16, 84], 8, fill=FRAME)
    lbl(d, (24, 62), "Sync-Ordner:", size=12)
    btn(d, [W - 60, 57, W - 22, 79], "...", r=6, fs=12)
    lbl(d, (128, 62), "C:/Users/Benutzer/FileSyncro", size=11, color=GRAY)

    lbl(d, (16, 97), "Gruppe:", size=12)
    rr(d, [72, 91, 256, 114], 8, fill=ENTRY, outline=(88, 88, 88), ow=1)
    lbl(d, (80, 97), "Bühne", size=11, color=TEXT)
    d.polygon([(242, 99), (252, 99), (247, 108)], fill=GRAY)
    btn(d, [264, 91, 348, 114], "Verwalten", color=GRAY_BTN, fs=11)

    lbl(d, (16, 128), "Verbundene Geräte", size=12, bold=True)
    rr(d, [16, 148, W - 16, 258], 10, fill=(38, 38, 38))

    # peer 1: same group – green
    rr(d, [20, 152, W - 20, 180], 6, fill=(48, 48, 48))
    d.ellipse([28, 161, 40, 173], fill=GREEN)
    lbl(d, (48, 161), "DESKTOP-ABC", size=12)
    lbl(d, (192, 162), "192.168.1.101", size=11, color=GRAY)
    rr(d, [330, 156, 450, 176], 5, fill=(36, 68, 40))
    lbl(d, (340, 158), "Bühne", size=10, color=GREEN)

    # peer 2: different group – gray
    rr(d, [20, 186, W - 20, 214], 6, fill=(48, 48, 48))
    d.ellipse([28, 195, 40, 207], fill=GRAY)
    lbl(d, (48, 195), "LAPTOP-DEF", size=12)
    lbl(d, (192, 196), "192.168.1.102", size=11, color=GRAY)
    rr(d, [330, 190, 450, 210], 5, fill=(54, 54, 54))
    lbl(d, (340, 192), "Technik", size=10, color=GRAY)

    inp(d, [16, 270, 180, 294], ph="IP-Adresse")
    btn(d, [184, 270, 276, 294], "Hinzufügen", fs=11)
    btn(d, [280, 270, 396, 294], "Aktualisieren", color=GRAY_BTN, fs=11)

    btn(d, [16, 308, 200, 334], "Jetzt synchronisieren", fs=12)
    lbl(d, (210, 316), "Status: bereit", size=12, color=GRAY)

    lbl(d, (16, 348), "Aktivität", size=12, bold=True)
    rr(d, [16, 368, W - 16, 684], 10, fill=(38, 38, 38))

    log = [
        ("+ DESKTOP-ABC (192.168.1.101) entdeckt", GREEN),
        ("+ LAPTOP-DEF (192.168.1.102) entdeckt",  GREEN),
        ("● Sync-Ziel: Gruppe Bühne",              BLUE2),
        ("✓ vortrag.pptx → 1 Gerät(e)",             TEXT),
        ("✓ Manueller Sync abgeschlossen",           TEXT),
    ]
    for i, (line, color) in enumerate(log):
        lbl(d, (24, 378 + i * 20), line, size=11, color=color)

    return png(img)


# ─── screenshot 3: group dialog ───────────────────────────────────────────
def ss_groups() -> bytes:
    W, H = 320, 360
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    titlebar(d, W, "Gruppen verwalten")
    f13b = _f(13, bold=True)
    bb = d.textbbox((0, 0), "Gruppen", font=f13b)
    tw = bb[2] - bb[0]
    d.text((W // 2 - tw // 2, 46), "Gruppen", fill=TEXT, font=f13b)

    rr(d, [12, 68, W - 12, 284], 8, fill=(38, 38, 38))
    for i, name in enumerate(["Bühne", "Technik", "Logistik"]):
        y0 = 74 + i * 36
        rr(d, [16, y0, W - 16, y0 + 28], 6, fill=FRAME)
        lbl(d, (24, y0 + 6), name, size=12)
        btn(d, [W - 52, y0 + 4, W - 20, y0 + 24], "✕", color=(138, 44, 44), fs=11, r=5)

    inp(d, [12, 294, 250, 318], ph="Neuer Name")
    btn(d, [254, 294, 308, 318], "+", fs=14, r=6)

    btn(d, [W // 2 - 60, 330, W // 2 + 60, 354], "Schließen", color=GRAY_BTN, fs=12)
    return png(img)


# ─── screenshot 4: conflict dialog ────────────────────────────────────────
def ss_conflict() -> bytes:
    W, H = 480, 222
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    titlebar(d, W, "Konflikt erkannt")

    f14b = _f(14, bold=True)
    text = "Konflikt: vortrag.pptx"
    bb = d.textbbox((0, 0), text, font=f14b)
    d.text((W // 2 - (bb[2] - bb[0]) // 2, 52), text, fill=ORANGE, font=f14b)

    lbl(d, (W // 2 - 132, 84),  "Lokal:   14:23:05 Uhr", size=12)
    lbl(d, (W // 2 - 132, 106), "Remote:  14:24:18 Uhr  (LAPTOP-DEF)", size=12)

    btn(d, [36, 148, 222, 178], "Lokale Version behalten", color=GRAY_BTN, fs=12)
    btn(d, [236, 148, 444, 178], "Remote übernehmen", color=BLUE, fs=12)
    return png(img)


# ─── screenshot 5: delete dialog ──────────────────────────────────────────
def ss_delete() -> bytes:
    W, H = 420, 182
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    titlebar(d, W, "Datei gelöscht")

    f13 = _f(13)
    for text, y, color in [
        ("vortrag.pptx wurde gelöscht.",                   52, TEXT),
        ("Auf allen Geräten löschen oder nur lokal?",       74, GRAY),
    ]:
        bb = d.textbbox((0, 0), text, font=f13)
        tw = bb[2] - bb[0]
        d.text((W // 2 - tw // 2, y), text, fill=color, font=f13)

    btn(d, [40, 118, 186, 150], "Nur lokal", color=GRAY_BTN, fs=12)
    btn(d, [210, 118, 380, 150], "Alle Geräte", color=RED, fs=12)
    return png(img)


# ─── PDF ──────────────────────────────────────────────────────────────────

class Manual(FPDF):
    F = "Arial"
    ACCENT = (31, 106, 165)

    def setup(self):
        base = "C:/Windows/Fonts/"
        # ARIALUNI has full Unicode coverage (checkmarks, arrows, etc.)
        uni = base + "ARIALUNI.ttf"
        self.add_font(self.F,       fname=uni)
        self.add_font(self.F, "B",  fname=base + "arialbd.ttf")
        self.add_font(self.F, "I",  fname=base + "ariali.ttf")
        self.add_font(self.F, "BI", fname=base + "arialbi.ttf")

    def header(self):
        pass  # no running header on content pages

    def footer(self):
        self.set_y(-15)
        self.set_font(self.F, "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"FileSyncro – Benutzerhandbuch  |  Seite {self.page_no()}", align="C")

    def h1(self, num: str, title: str):
        self.set_font(self.F, "B", 18)
        self.set_text_color(*self.ACCENT)
        label = f"{num}  {title}" if num else title
        self.cell(0, 12, label, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self.ACCENT)
        self.set_line_width(0.4)
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + 180, y)
        self.ln(6)
        self.set_text_color(0, 0, 0)

    def h2(self, title: str):
        self.ln(4)
        self.set_font(self.F, "B", 13)
        self.set_text_color(45, 45, 45)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_text_color(0, 0, 0)

    def p(self, text: str):
        self.set_font(self.F, "", 11)
        self.set_text_color(38, 38, 38)
        self.multi_cell(0, 6.5, text)
        self.ln(3)

    def callout(self, items: list[tuple[str, str]]):
        self.set_text_color(38, 38, 38)
        for num, text in items:
            self.set_font(self.F, "B", 11)
            self.set_x(self.l_margin + 2)
            self.cell(9, 7, num)
            self.set_font(self.F, "", 11)
            self.multi_cell(0, 7, text)
        self.ln(2)

    def img_c(self, data: bytes, caption: str, w: float = 130):
        pil = Image.open(io.BytesIO(data))
        x = (self.w - w) / 2
        self.image(pil, x=x, w=w)
        self.ln(1)
        self.set_font(self.F, "I", 9)
        self.set_text_color(105, 105, 105)
        self.cell(0, 5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_text_color(0, 0, 0)


def build(output: Path):
    pdf = Manual("P", "mm", "A4")
    pdf.setup()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(15, 15, 15)

    # ── Deckblatt ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(31, 106, 165)
    pdf.rect(0, 0, 210, 72, "F")
    pdf.set_y(14)
    pdf.set_font(pdf.F, "B", 40)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 16, "FileSyncro", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(pdf.F, "", 17)
    pdf.cell(0, 10, "Benutzerhandbuch", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(pdf.F, "", 11)
    pdf.cell(0, 8, "Version 1.0", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(82)
    pdf.set_text_color(55, 55, 55)
    pdf.set_font(pdf.F, "", 12)
    pdf.multi_cell(0, 7,
        "FileSyncro synchronisiert Dateien direkt zwischen Rechnern im selben "
        "Netzwerk – ohne Cloud, ohne zentralen Server. Dieses Handbuch beschreibt "
        "alle Funktionen der Anwendung.", align="C")

    # ── Inhaltsverzeichnis ─────────────────────────────────────────
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.h1("", "Inhaltsverzeichnis")
    toc = [
        ("1", "Einführung", False),
        ("2", "Benutzeroberfläche im Überblick", False),
        ("3", "Sync-Ordner konfigurieren", False),
        ("4", "Geräte verbinden", False),
        ("4.1", "Automatische Erkennung", True),
        ("4.2", "Gerät manuell hinzufügen", True),
        ("5", "Gruppen", False),
        ("5.1", "Gruppe erstellen", True),
        ("5.2", "Gruppe auswählen", True),
        ("5.3", "Gruppenverteilung im Netzwerk", True),
        ("6", "Synchronisieren", False),
        ("7", "Konflikte & Löschvorgänge", False),
        ("7.1", "Konflikt-Dialog", True),
        ("7.2", "Lösch-Dialog", True),
        ("8", "Aktivitätslog", False),
    ]
    for num, title, sub in toc:
        pdf.set_font(pdf.F, "" if sub else "B", 11 if sub else 12)
        pdf.set_text_color(65, 65, 65 if sub else 25)
        pdf.set_x(pdf.l_margin + (6 if sub else 0))
        pdf.cell(0, 8, f"  {num}   {title}", new_x="LMARGIN", new_y="NEXT")

    # ── 1. Einführung ──────────────────────────────────────────────
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    pdf.h1("1", "Einführung")
    pdf.p(
        "FileSyncro ermöglicht die automatische Synchronisierung von Dateien zwischen "
        "mehreren Rechnern im selben lokalen Netzwerk. Es ist keine Internetverbindung "
        "oder ein zentraler Server notwendig – die Geräte kommunizieren direkt miteinander."
    )
    pdf.p(
        "Hauptfunktionen:\n"
        "  •  Automatische Geräteerkennung per mDNS im lokalen Netzwerk\n"
        "  •  Sofortige Synchronisierung bei Dateiänderungen\n"
        "  •  Gruppen: Sync nur zwischen Geräten derselben Gruppe\n"
        "  •  Konflikterkennung und -lösung bei gleichzeitigen Änderungen\n"
        "  •  Manueller Sync und manuelle Geräteverwaltung\n"
        "  •  Aktivitätslog für alle Sync-Ereignisse"
    )
    pdf.p(
        "Technische Voraussetzungen:\n"
        "  •  Windows 10/11 oder macOS\n"
        "  •  Alle Geräte im selben lokalen Netzwerk (LAN oder WLAN)\n"
        "  •  Port 5757 (TCP) in der Firewall freigegeben"
    )

    # ── 2. UI-Überblick ────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("2", "Benutzeroberfläche im Überblick")
    pdf.img_c(ss_main(), "Abb. 1 – Hauptfenster (Nummerierung der Bereiche)", w=108)
    pdf.p("Das Hauptfenster gliedert sich in sechs Bereiche:")
    pdf.callout([
        ("1", "Sync-Ordner – Der überwachte Ordner. Alle Änderungen werden sofort synchronisiert."),
        ("2", "Gruppe – Aktive Synchronisationsgruppe; nur Peers dieser Gruppe werden einbezogen."),
        ("3", "Verbundene Geräte – Erreichbare Peers mit Statusanzeige (grün / grau)."),
        ("4", "Gerät hinzufügen / Aktualisieren – Manuell per IP oder Erreichbarkeit prüfen."),
        ("5", "Jetzt synchronisieren – Vollständiger Abgleich aller Dateien mit aktiven Peers."),
        ("6", "Aktivitätslog – Protokoll aller Verbindungs- und Übertragungsereignisse."),
    ])

    # ── 3. Sync-Ordner ─────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("3", "Sync-Ordner konfigurieren")
    pdf.p(
        "Beim ersten Start wird automatisch der Ordner FileSyncro im Benutzerverzeichnis "
        "angelegt und als Sync-Ordner verwendet. Der Pfad wird oben im Hauptfenster angezeigt."
    )
    pdf.h2("Ordner wechseln")
    pdf.p(
        "Klicken Sie auf \"...\" neben der Pfadanzeige, um einen anderen Ordner auszuwählen. "
        "Der neue Ordner wird sofort überwacht; vorhandene Dateien werden beim nächsten "
        "manuellen Sync mit den Peers abgeglichen."
    )
    pdf.h2("Hinweise")
    pdf.p(
        "  •  Unterordner werden rekursiv einbezogen.\n"
        "  •  Ist ein Unterordner nicht zugänglich (z. B. fehlende Berechtigungen), "
        "wird er stillschweigend übersprungen – alle anderen Dateien werden weiterhin synchronisiert.\n"
        "  •  Sehr große Dateien können je nach Netzwerkgeschwindigkeit einige Sekunden benötigen."
    )

    # ── 4. Geräte ──────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("4", "Geräte verbinden")
    pdf.h2("4.1  Automatische Erkennung")
    pdf.p(
        "FileSyncro verwendet mDNS (Zeroconf/Bonjour), um andere Instanzen im selben "
        "Netzwerk automatisch zu erkennen. Sobald ein anderes Gerät die Anwendung startet, "
        "erscheint es innerhalb weniger Sekunden in der Geräteliste."
    )
    pdf.p(
        "Der farbige Punkt zeigt den Status:\n"
        "  ●  Grün  – Gerät erreichbar\n"
        "  ●  Grau  – Gerät nicht erreichbar\n\n"
        "Nicht erreichbare Geräte werden nach drei aufeinanderfolgenden fehlgeschlagenen "
        "Verbindungsversuchen (ca. 90 Sekunden) automatisch entfernt."
    )
    pdf.img_c(ss_peers(), "Abb. 2 – Hauptfenster mit verbundenen Geräten", w=108)

    pdf.h2("4.2  Gerät manuell hinzufügen")
    pdf.p(
        "Wenn ein Gerät nicht automatisch erkannt wird (z. B. in segmentierten Netzwerken "
        "oder bei blockiertem mDNS-Dienst):\n\n"
        "1. IP-Adresse des Zielgeräts in das Eingabefeld unten links eingeben.\n"
        "2. Auf \"Hinzufügen\" klicken.\n\n"
        "Mit \"Aktualisieren\" wird die Erreichbarkeit aller bekannten Geräte sofort geprüft."
    )

    # ── 5. Gruppen ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("5", "Gruppen")
    pdf.p(
        "Gruppen ermöglichen es, die Synchronisierung auf eine bestimmte Teilmenge von "
        "Geräten zu beschränken. Ein Gerät synchronisiert ausschließlich mit Peers, "
        "die sich in derselben Gruppe befinden."
    )
    pdf.p(
        "Ist keine Gruppe aktiv (Auswahl \"Alle Geräte\"), wird mit allen erreichbaren "
        "Peers synchronisiert.\n\n"
        "Wichtig: Jedes Gerät wählt seine eigene Gruppe selbst. Es ist nicht möglich, "
        "einem anderen Gerät eine Gruppe zuzuweisen."
    )
    pdf.h2("5.1  Gruppe erstellen")
    pdf.p(
        "1. Auf \"Verwalten\" klicken.\n"
        "2. Namen eingeben und \"+\" klicken.\n"
        "3. Dialog schließen – die neue Gruppe erscheint im Dropdown."
    )
    pdf.img_c(ss_groups(), "Abb. 3 – Gruppen verwalten", w=76)

    pdf.h2("5.2  Gruppe auswählen")
    pdf.p(
        "Im Dropdown \"Gruppe:\" die gewünschte Gruppe auswählen. "
        "Der Sync wird sofort auf Peers dieser Gruppe eingeschränkt. "
        "Die Auswahl wird gespeichert und beim nächsten Start wiederhergestellt."
    )
    pdf.h2("5.3  Gruppenverteilung im Netzwerk")
    pdf.p(
        "Bekannte Gruppen werden automatisch zwischen Geräten ausgetauscht. "
        "Wenn ein anderes Gerät mit der Gruppe \"Technik\" erreichbar ist, erscheint "
        "\"Technik\" nach kurzer Zeit auch im eigenen Dropdown – ohne manuelle Eingabe."
    )

    # ── 6. Sync ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.h1("6", "Synchronisieren")
    pdf.h2("Automatischer Sync")
    pdf.p(
        "Jede Dateiänderung im Sync-Ordner wird sofort an alle aktiven Peers übertragen. "
        "FileSyncro überwacht den Ordner kontinuierlich im Hintergrund."
    )
    pdf.h2("Manueller Sync")
    pdf.p(
        "\"Jetzt synchronisieren\" vergleicht alle lokalen Dateien mit den Peers und "
        "überträgt fehlende oder veraltete Versionen. "
        "Nützlich nach einer Offline-Phase oder beim Hinzufügen eines neuen Geräts."
    )
    pdf.h2("Zeitstempel-Logik")
    pdf.p(
        "  •  Lokale Datei neuer als Remote (+1 s Toleranz) → wird übertragen\n"
        "  •  Remote-Datei neuer als lokal → Konflikt-Dialog erscheint\n"
        "  •  Remote-Datei eindeutig älter → automatisch abgelehnt (kein Dialog)\n"
        "  •  Zeitstempel gleich (±1 s) → keine Übertragung nötig"
    )

    # ── 7. Konflikte & Löschen ─────────────────────────────────────
    pdf.add_page()
    pdf.h1("7", "Konflikte & Löschvorgänge")
    pdf.h2("7.1  Konflikt-Dialog")
    pdf.p(
        "Ein Konflikt entsteht, wenn eine eingehende Datei neuer ist als die lokale Version. "
        "FileSyncro zeigt einen Dialog mit den Zeitstempeln beider Versionen."
    )
    pdf.img_c(ss_conflict(), "Abb. 4 – Konflikt-Dialog", w=118)
    pdf.p(
        "  •  \"Lokale Version behalten\" – Die eingehende Datei wird abgelehnt.\n"
        "  •  \"Remote übernehmen\" – Die lokale Datei wird durch die empfangene Version ersetzt."
    )

    pdf.h2("7.2  Lösch-Dialog")
    pdf.p(
        "Wenn eine Datei lokal gelöscht wird, erscheint folgender Dialog:"
    )
    pdf.img_c(ss_delete(), "Abb. 5 – Lösch-Dialog", w=105)
    pdf.p(
        "  •  \"Nur lokal\" – Datei wird nur auf diesem Gerät gelöscht.\n"
        "  •  \"Alle Geräte\" – Die Löschung wird an alle aktiven Peers propagiert."
    )

    # ── 8. Aktivitätslog ───────────────────────────────────────────
    pdf.add_page()
    pdf.h1("8", "Aktivitätslog")
    pdf.p(
        "Der Aktivitätslog zeigt alle relevanten Ereignisse der aktuellen Sitzung. "
        "Er ist auf 500 Zeilen begrenzt; ältere Einträge werden automatisch entfernt. "
        "Der Inhalt wird nicht gespeichert und steht nur während der Sitzung zur Verfügung."
    )
    pdf.p(
        "Bedeutung der Einträge:\n\n"
        "  +  Gerätename (IP)  –  Neues Gerät entdeckt\n"
        "  −  Gerätename  –  Gerät getrennt\n"
        "  ●  Gerätename erreichbar  –  Gerät antwortet wieder\n"
        "  ○  Gerätename nicht erreichbar  –  Gerät antwortet nicht\n"
        "  ✓  dateiname → N Gerät(e)  –  Datei erfolgreich übertragen\n"
        "  ●  Sync-Ziel: Gruppe X  –  Gruppenfilter wurde aktiviert\n"
        "  ●  Sync-Ziel: alle Geräte  –  Kein Gruppenfilter aktiv\n"
        "  ✓  Manueller Sync abgeschlossen  –  Vollständiger Abgleich beendet"
    )

    pdf.output(str(output))
    print(f"Gespeichert: {output}")


if __name__ == "__main__":
    out = Path(__file__).parent / "FileSyncro_Manual.pdf"
    build(out)
