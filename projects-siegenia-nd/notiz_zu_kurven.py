# -*- coding: utf-8 -*-
"""
Notiz_zu_Kurven.py  -  SIEGENIA Niederdielfen / NX 2412 / NX Open Python
=====================================================
Wandelt Hinweise (Notes) des Arbeitsteils in echte Kurven (Linien) um.
Schrift: Einstrich-Schrift (Hershey Simplex, aehnlich NX blockfont) -
geeignet fuer Zeichnung, Referenzsets und Laser/Gravur.

Ablauf
  1. KOPIE des Teils oeffnen (z.B. oelkanne_neu.prt) und als Arbeitsteil setzen.
     Nicht direkt im G:\\CAD\\ugsshare-... arbeiten.
  2. Optional: Hinweise vorselektieren (Filter "Hinweis"). Ohne Auswahl werden
     ALLE Hinweise des Arbeitsteils verarbeitet.
  3. Datei > Ausfuehren > NX Open... > dieses Skript.
  4. Listing Window lesen, Ergebnis optisch gegen die Hinweise pruefen.
     Danach Hinweise loeschen (oder Lauf mit DELETE_NOTES = True auf frischer Kopie).

Annahme: Die Hinweise liegen in der XY-Ebene des WCS (bei der Oelkanne: absolutes XY).
Bei anderer Lage vorher WCS in die Textebene legen.
Nicht in Produktion getestet - erst DRY_RUN = True laufen lassen.
"""
import json, math, re

# ---------------- Konfiguration ----------------
DRY_RUN      = False   # True: nur auslesen/protokollieren, nichts erzeugen
DELETE_NOTES = False   # True: Hinweise nach erfolgreicher Umwandlung loeschen
ZIEL_LAYER   = None    # None = aktueller Arbeitslayer, sonst z.B. 1
ZIEL_FARBE   = None    # None = Standardfarbe, sonst NX-Farbnummer
REFSET_NAME  = None    # z.B. "MODELL": Kurven zusaetzlich in dieses Referenzset
DEFAULT_SIZE = 2.5     # Fallback-Schrifthoehe [mm], falls NX keine Textinfo liefert
FIT_LENGTH   = True    # Textbreite an NX-Textbox anpassen (erhaelt Luecken/Abstaende)
ZEILENABSTAND = 1.6    # bei mehrzeiligen Hinweisen, Faktor auf Schrifthoehe

# Hershey Simplex (futural), public domain. Format: zeichen -> [vorschub, [[x,y,x,y,...], ...]]
# Einheiten: Grundlinie y=0, Versalhoehe 21.
GLYPHS = json.loads(r'''{" ":[16,[]],"!":[10,[[5,21,5,7],[5,2,4,1,5,0,6,1,5,2]]],"\"":[16,[[4,21,4,14],[12,21,12,14]]],"#":[21,[[11,25,4,-7],[17,25,10,-7],[4,12,18,12],[3,6,17,6]]],"$":[20,[[8,25,8,-4],[12,25,12,-4],[17,18,15,20,12,21,8,21,5,20,3,18,3,16,4,14,5,13,7,12,13,10,15,9,16,8,17,6,17,3,15,1,12,0,8,0,5,1,3,3]]],"%":[24,[[21,21,3,0],[8,21,10,19,10,17,9,15,7,14,5,14,3,16,3,18,4,20,6,21,8,21,10,20,13,19,16,19,19,20,21,21],[17,7,15,6,14,4,14,2,16,0,18,0,20,1,21,3,21,5,19,7,17,7]]],"&":[26,[[23,12,23,13,22,14,21,14,20,13,19,11,17,6,15,3,13,1,11,0,7,0,5,1,4,2,3,4,3,6,4,8,5,9,12,13,13,14,14,16,14,18,13,20,11,21,9,20,8,18,8,16,9,13,11,10,16,3,18,1,20,0,22,0,23,1,23,2]]],"'":[10,[[5,19,4,20,5,21,6,20,6,18,5,16,4,15]]],"(":[14,[[11,25,9,23,7,20,5,16,4,11,4,7,5,2,7,-2,9,-5,11,-7]]],")":[14,[[3,25,5,23,7,20,9,16,10,11,10,7,9,2,7,-2,5,-5,3,-7]]],"*":[16,[[8,15,8,3],[3,12,13,6],[13,12,3,6]]],"+":[26,[[13,18,13,0],[4,9,22,9]]],",":[8,[[5,4,4,3,3,4,4,5,5,4,5,2,3,0]]],"-":[26,[[4,9,22,9]]],".":[8,[[4,5,3,4,4,3,5,4,4,5]]],"/":[22,[[20,25,2,-7]]],"0":[20,[[9,21,6,20,4,17,3,12,3,9,4,4,6,1,9,0,11,0,14,1,16,4,17,9,17,12,16,17,14,20,11,21,9,21]]],"1":[20,[[6,17,8,18,11,21,11,0]]],"2":[20,[[4,16,4,17,5,19,6,20,8,21,12,21,14,20,15,19,16,17,16,15,15,13,13,10,3,0,17,0]]],"3":[20,[[5,21,16,21,10,13,13,13,15,12,16,11,17,8,17,6,16,3,14,1,11,0,8,0,5,1,4,2,3,4]]],"4":[20,[[13,21,3,7,18,7],[13,21,13,0]]],"5":[20,[[15,21,5,21,4,12,5,13,8,14,11,14,14,13,16,11,17,8,17,6,16,3,14,1,11,0,8,0,5,1,4,2,3,4]]],"6":[20,[[16,18,15,20,12,21,10,21,7,20,5,17,4,12,4,7,5,3,7,1,10,0,11,0,14,1,16,3,17,6,17,7,16,10,14,12,11,13,10,13,7,12,5,10,4,7]]],"7":[20,[[17,21,7,0],[3,21,17,21]]],"8":[20,[[8,21,5,20,4,18,4,16,5,14,7,13,11,12,14,11,16,9,17,7,17,4,16,2,15,1,12,0,8,0,5,1,4,2,3,4,3,7,4,9,6,11,9,12,13,13,15,14,16,16,16,18,15,20,12,21,8,21]]],"9":[20,[[16,14,15,11,13,9,10,8,9,8,6,9,4,11,3,14,3,15,4,18,6,20,9,21,10,21,13,20,15,18,16,14,16,9,15,4,13,1,10,0,8,0,5,1,4,3]]],":":[8,[[4,12,3,11,4,10,5,11,4,12],[4,5,3,4,4,3,5,4,4,5]]],";":[8,[[4,12,3,11,4,10,5,11,4,12],[5,4,4,3,3,4,4,5,5,4,5,2,3,0]]],"<":[24,[[20,18,4,9,20,0]]],"=":[26,[[4,12,22,12],[4,6,22,6]]],">":[24,[[4,18,20,9,4,0]]],"?":[18,[[3,16,3,17,4,19,5,20,7,21,11,21,13,20,14,19,15,17,15,15,14,13,13,12,9,10,9,7],[9,2,8,1,9,0,10,1,9,2]]],"@":[27,[[18,13,17,15,15,16,12,16,10,15,9,14,8,11,8,8,9,6,11,5,14,5,16,6,17,8],[12,16,10,14,9,11,9,8,10,6,11,5],[18,16,17,8,17,6,19,5,21,5,23,7,24,10,24,12,23,15,22,17,20,19,18,20,15,21,12,21,9,20,7,19,5,17,4,15,3,12,3,9,4,6,5,4,7,2,9,1,12,0,15,0,18,1,20,2,21,3],[19,16,18,8,18,6,19,5]]],"A":[18,[[9,21,1,0],[9,21,17,0],[4,7,14,7]]],"B":[21,[[4,21,4,0],[4,21,13,21,16,20,17,19,18,17,18,15,17,13,16,12,13,11],[4,11,13,11,16,10,17,9,18,7,18,4,17,2,16,1,13,0,4,0]]],"C":[21,[[18,16,17,18,15,20,13,21,9,21,7,20,5,18,4,16,3,13,3,8,4,5,5,3,7,1,9,0,13,0,15,1,17,3,18,5]]],"D":[21,[[4,21,4,0],[4,21,11,21,14,20,16,18,17,16,18,13,18,8,17,5,16,3,14,1,11,0,4,0]]],"E":[19,[[4,21,4,0],[4,21,17,21],[4,11,12,11],[4,0,17,0]]],"F":[18,[[4,21,4,0],[4,21,17,21],[4,11,12,11]]],"G":[21,[[18,16,17,18,15,20,13,21,9,21,7,20,5,18,4,16,3,13,3,8,4,5,5,3,7,1,9,0,13,0,15,1,17,3,18,5,18,8],[13,8,18,8]]],"H":[22,[[4,21,4,0],[18,21,18,0],[4,11,18,11]]],"I":[8,[[4,21,4,0]]],"J":[16,[[12,21,12,5,11,2,10,1,8,0,6,0,4,1,3,2,2,5,2,7]]],"K":[21,[[4,21,4,0],[18,21,4,7],[9,12,18,0]]],"L":[17,[[4,21,4,0],[4,0,16,0]]],"M":[24,[[4,21,4,0],[4,21,12,0],[20,21,12,0],[20,21,20,0]]],"N":[22,[[4,21,4,0],[4,21,18,0],[18,21,18,0]]],"O":[22,[[9,21,7,20,5,18,4,16,3,13,3,8,4,5,5,3,7,1,9,0,13,0,15,1,17,3,18,5,19,8,19,13,18,16,17,18,15,20,13,21,9,21]]],"P":[21,[[4,21,4,0],[4,21,13,21,16,20,17,19,18,17,18,14,17,12,16,11,13,10,4,10]]],"Q":[22,[[9,21,7,20,5,18,4,16,3,13,3,8,4,5,5,3,7,1,9,0,13,0,15,1,17,3,18,5,19,8,19,13,18,16,17,18,15,20,13,21,9,21],[12,4,18,-2]]],"R":[21,[[4,21,4,0],[4,21,13,21,16,20,17,19,18,17,18,15,17,13,16,12,13,11,4,11],[11,11,18,0]]],"S":[20,[[17,18,15,20,12,21,8,21,5,20,3,18,3,16,4,14,5,13,7,12,13,10,15,9,16,8,17,6,17,3,15,1,12,0,8,0,5,1,3,3]]],"T":[16,[[8,21,8,0],[1,21,15,21]]],"U":[22,[[4,21,4,6,5,3,7,1,10,0,12,0,15,1,17,3,18,6,18,21]]],"V":[18,[[1,21,9,0],[17,21,9,0]]],"W":[24,[[2,21,7,0],[12,21,7,0],[12,21,17,0],[22,21,17,0]]],"X":[20,[[3,21,17,0],[17,21,3,0]]],"Y":[18,[[1,21,9,11,9,0],[17,21,9,11]]],"Z":[20,[[17,21,3,0],[3,21,17,21],[3,0,17,0]]],"[":[14,[[4,25,4,-7],[5,25,5,-7],[4,25,11,25],[4,-7,11,-7]]],"\\":[14,[[0,21,14,-3]]],"]":[14,[[9,25,9,-7],[10,25,10,-7],[3,25,10,25],[3,-7,10,-7]]],"^":[16,[[8,23,0,9],[8,23,16,9]]],"_":[18,[[0,-7,18,-7]]],"`":[8,[[5,16,3,14,3,12,4,11,5,12,4,13,3,12]]],"a":[19,[[15,14,15,0],[15,11,13,13,11,14,8,14,6,13,4,11,3,8,3,6,4,3,6,1,8,0,11,0,13,1,15,3]]],"b":[19,[[4,21,4,0],[4,11,6,13,8,14,11,14,13,13,15,11,16,8,16,6,15,3,13,1,11,0,8,0,6,1,4,3]]],"c":[18,[[15,11,13,13,11,14,8,14,6,13,4,11,3,8,3,6,4,3,6,1,8,0,11,0,13,1,15,3]]],"d":[19,[[15,21,15,0],[15,11,13,13,11,14,8,14,6,13,4,11,3,8,3,6,4,3,6,1,8,0,11,0,13,1,15,3]]],"e":[18,[[3,8,15,8,15,10,14,12,13,13,11,14,8,14,6,13,4,11,3,8,3,6,4,3,6,1,8,0,11,0,13,1,15,3]]],"f":[12,[[10,21,8,21,6,20,5,17,5,0],[2,14,9,14]]],"g":[19,[[15,14,15,-2,14,-5,13,-6,11,-7,8,-7,6,-6],[15,11,13,13,11,14,8,14,6,13,4,11,3,8,3,6,4,3,6,1,8,0,11,0,13,1,15,3]]],"h":[19,[[4,21,4,0],[4,10,7,13,9,14,12,14,14,13,15,10,15,0]]],"i":[8,[[3,21,4,20,5,21,4,22,3,21],[4,14,4,0]]],"j":[10,[[5,21,6,20,7,21,6,22,5,21],[6,14,6,-3,5,-6,3,-7,1,-7]]],"k":[17,[[4,21,4,0],[14,14,4,4],[8,8,15,0]]],"l":[8,[[4,21,4,0]]],"m":[30,[[4,14,4,0],[4,10,7,13,9,14,12,14,14,13,15,10,15,0],[15,10,18,13,20,14,23,14,25,13,26,10,26,0]]],"n":[19,[[4,14,4,0],[4,10,7,13,9,14,12,14,14,13,15,10,15,0]]],"o":[19,[[8,14,6,13,4,11,3,8,3,6,4,3,6,1,8,0,11,0,13,1,15,3,16,6,16,8,15,11,13,13,11,14,8,14]]],"p":[19,[[4,14,4,-7],[4,11,6,13,8,14,11,14,13,13,15,11,16,8,16,6,15,3,13,1,11,0,8,0,6,1,4,3]]],"q":[19,[[15,14,15,-7],[15,11,13,13,11,14,8,14,6,13,4,11,3,8,3,6,4,3,6,1,8,0,11,0,13,1,15,3]]],"r":[13,[[4,14,4,0],[4,8,5,11,7,13,9,14,12,14]]],"s":[17,[[14,11,13,13,10,14,7,14,4,13,3,11,4,9,6,8,11,7,13,6,14,4,14,3,13,1,10,0,7,0,4,1,3,3]]],"t":[12,[[5,21,5,4,6,1,8,0,10,0],[2,14,9,14]]],"u":[19,[[4,14,4,4,5,1,7,0,10,0,12,1,15,4],[15,14,15,0]]],"v":[16,[[2,14,8,0],[14,14,8,0]]],"w":[22,[[3,14,7,0],[11,14,7,0],[11,14,15,0],[19,14,15,0]]],"x":[17,[[3,14,14,0],[14,14,3,0]]],"y":[16,[[2,14,8,0],[14,14,8,0,6,-4,4,-6,2,-7,1,-7]]],"z":[17,[[14,14,3,0],[3,14,14,14],[3,0,14,0]]],"{":[14,[[9,25,7,24,6,23,5,21,5,19,6,17,7,16,8,14,8,12,6,10],[7,24,6,22,6,20,7,18,8,17,9,15,9,13,8,11,4,9,8,7,9,5,9,3,8,1,7,0,6,-2,6,-4,7,-6],[6,8,8,6,8,4,7,2,6,1,5,-1,5,-3,6,-5,7,-6,9,-7]]],"|":[8,[[4,25,4,-7]]],"}":[14,[[5,25,7,24,8,23,9,21,9,19,8,17,7,16,6,14,6,12,8,10],[7,24,8,22,8,20,7,18,6,17,5,15,5,13,6,11,10,9,6,7,5,5,5,3,6,1,7,0,8,-2,8,-4,7,-6],[8,8,6,6,6,4,7,2,8,1,9,-1,9,-3,8,-5,7,-6,5,-7]]],"~":[24,[[3,6,3,8,4,11,6,12,8,12,10,11,14,8,16,7,18,7,20,8,21,10],[3,8,4,10,6,11,8,11,10,10,14,7,16,6,18,6,20,7,21,10,21,12]]],"\u007f":[16,[[0,21,0,0,1,0,1,21,2,21,2,0,3,0,3,21,4,21,4,0,5,0,5,21,6,21,6,0,7,0,7,21,8,21,8,0,9,0,9,21,10,21,10,0,11,0,11,21,12,21,12,0,13,0,13,21,14,21,14,0,15,0,15,21,16,21,16,0]]]}''')
CAP = 21.0


# ---------------- reine Geometrie (ohne NX testbar) ----------------
def _clean(text):
    """NX-Steuercodes wie <$s>, <F2>, <C1.5> entfernen."""
    return re.sub(r"<[^<>]{1,12}>", "", text)


def layout_strokes(lines):
    """Polylinien in Glyph-Einheiten fuer eine Liste von Textzeilen."""
    strokes = []
    for j, line in enumerate(lines):
        x = 0.0
        y0 = -j * CAP * ZEILENABSTAND
        for ch in _clean(line):
            adv, glyph = GLYPHS.get(ch) or GLYPHS["?"]
            for s in glyph:
                strokes.append([(x + s[i], y0 + s[i + 1]) for i in range(0, len(s), 2)])
            x += adv
    return strokes


def bbox(strokes):
    xs = [p[0] for s in strokes for p in s]
    ys = [p[1] for s in strokes for p in s]
    return min(xs), min(ys), max(xs), max(ys)


def place(strokes, center, u, v, sx, sy, nlines=1):
    """Glyph-Einheiten -> 3D. center = Mitte der NX-Textbox, u = Leserichtung, v = Oben.
    Horizontal: Mitte der Tinte. Vertikal: Mitte zwischen Grundlinie und Versalhoehe
    (so wie NX die Textbox bildet) - Unterlaengen wie bei '/' verschieben nichts."""
    x0, _, x1, _ = bbox(strokes)
    cx = (x0 + x1) / 2.0
    cy = (CAP - (nlines - 1) * CAP * ZEILENABSTAND) / 2.0
    out = []
    for s in strokes:
        pts = []
        for (x, y) in s:
            a, b = (x - cx) * sx, (y - cy) * sy
            pts.append(tuple(center[k] + u[k] * a + v[k] * b for k in range(3)))
        out.append(pts)
    return out


def angle_to_rad(a):
    """UF liefert je nach Funktion Grad oder Bogenmass - heuristisch erkennen."""
    if a is None:
        return 0.0
    a = float(a)
    if abs(a) > 2 * math.pi + 1e-6:
        return math.radians(a)
    if abs(a - round(a)) > 1e-6:      # nicht-ganzzahlig und klein -> Bogenmass
        return a
    return math.radians(a)            # 0, 1, 2 ... als Grad interpretieren


# ---------------- NX-Teil ----------------
def _ask_textinfo(uf, tag):
    """UF_DRF_ask_draft_aid_text_info -> dict mit size/angle/origin/length/height."""
    try:
        r = uf.Drf.AskDraftAidTextInfo(tag)
    except Exception as e:
        return None, "Fehler: %s" % e
    infos = r[1] if isinstance(r, tuple) and len(r) == 2 else r
    try:
        ti = infos[0]
    except Exception:
        return None, "leer/unerwartet: %r" % (r,)

    def g(*names):
        for n in names:
            if hasattr(ti, n):
                return getattr(ti, n)
        return None
    return {"size": g("size", "Size"), "angle": g("angle", "Angle"),
            "origin": g("origin", "Origin"), "length": g("length", "Length"),
            "height": g("height", "Height")}, None


def _convert_note(n, wp, uf, log, X, Y, neue):
    import NXOpen
    text = [t for t in n.GetText()]
    o = n.AnnotationOrigin
    anchor = (o.X, o.Y, o.Z)
    log("")
    log("Hinweis %s: %r" % (n.Tag, text))
    log("  AnnotationOrigin  : (%.3f, %.3f, %.3f)" % anchor)

    info, err_i = _ask_textinfo(uf, n.Tag)
    log("  DraftAidTextInfo  : %s" % (info if info else err_i))

    size = float(info["size"]) if info and info["size"] else DEFAULT_SIZE
    ang = angle_to_rad(info["angle"] if info else None)
    u = tuple(math.cos(ang) * X[k] + math.sin(ang) * Y[k] for k in range(3))
    v = tuple(-math.sin(ang) * X[k] + math.cos(ang) * Y[k] for k in range(3))

    # TextInfo.origin = linke untere Ecke der Textbox (im Log verifiziert:
    # origin + (length/2, height/2) == AnnotationOrigin)
    center, methode, L = anchor, "AnnotationOrigin als Mitte", None
    if info and info["origin"] is not None and info["length"] and info["height"]:
        ll = [float(c) for c in info["origin"]]
        L, H = float(info["length"]), float(info["height"])
        c = tuple(ll[k] + u[k] * L / 2.0 + v[k] * H / 2.0 for k in range(3))
        abw = math.dist(c, anchor)
        if abw <= max(L, H):
            center, methode = c, "TextInfo-Box (Abw. zu AnnotationOrigin %.3f mm)" % abw
        else:
            log("  ! TextInfo-Box unplausibel (Abstand %.1f mm) - Fallback" % abw)
            L = None
    log("  -> Hoehe %.3f mm, Winkel %.1f Grad, Position: %s" % (size, math.degrees(ang), methode))

    strokes = layout_strokes(text)
    if not strokes:
        log("  (kein darstellbarer Text)")
        return 0
    sy = size / CAP
    sx = sy
    if FIT_LENGTH and L:
        x0, _, x1, _ = bbox(strokes)
        if x1 > x0:
            fit = L / (x1 - x0)
            if 0.6 * sy <= fit <= 1.6 * sy:
                sx = fit
    if DRY_RUN:
        log("  DRY_RUN: %d Polylinien wuerden erzeugt (Breitenfaktor %.2f)" % (len(strokes), sx / sy))
        return 0

    anz = 0
    for pts in place(strokes, center, u, v, sx, sy, len(text)):
        for a, b in zip(pts[:-1], pts[1:]):
            if math.dist(a, b) < 1e-6:
                continue
            neue.append(wp.Curves.CreateLine(NXOpen.Point3d(*a), NXOpen.Point3d(*b)))
            anz += 1
    log("  %d Linien erzeugt (Breitenfaktor %.2f)" % (anz, sx / sy))
    return anz


def main():
    import NXOpen
    import NXOpen.UF
    import NXOpen.Annotations

    s = NXOpen.Session.GetSession()
    wp = s.Parts.Work
    uf = NXOpen.UF.UFSession.GetUFSession()
    lw = s.ListingWindow
    lw.Open()
    log = lw.WriteLine
    log("=== SIEGENIA ND: Notiz_zu_Kurven  (%s)  DRY_RUN=%s ===" % (wp.Leaf, DRY_RUN))

    # Hinweise sammeln: Vorauswahl hat Vorrang
    notes = []
    sm = NXOpen.UI.GetUI().SelectionManager
    for i in range(sm.GetNumSelectedObjects()):
        o = sm.GetSelectedTaggedObject(i)
        if hasattr(o, "GetText") and isinstance(o, NXOpen.Annotations.Annotation):
            notes.append(o)
    quelle = "Vorauswahl"
    if not notes:
        notes = [n for n in wp.Notes]
        quelle = "alle Hinweise im Arbeitsteil"
    log("Hinweise: %d (%s)" % (len(notes), quelle))
    if not notes:
        return

    # Ebene: WCS-XY
    m = wp.WCS.CoordinateSystem.Orientation.Element
    X = (m.Xx, m.Xy, m.Xz)
    Y = (m.Yx, m.Yy, m.Yz)

    mark = s.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Hinweise zu Kurven")
    neue = []
    fertig = []

    for n in notes:
        try:
            anz = _convert_note(n, wp, uf, log, X, Y, neue)
            if anz:
                fertig.append(n)
        except Exception:
            import traceback
            log("  !! Fehler bei Hinweis %s:" % n.Tag)
            for zeile in traceback.format_exc().splitlines():
                log("     " + zeile)

    if DRY_RUN or not neue:
        log("")
        log("Ende (nichts erzeugt).")
        return

    if ZIEL_LAYER is not None or ZIEL_FARBE is not None:
        dm = s.DisplayManager.NewDisplayModification()
        dm.ApplyToAllFaces = False
        if ZIEL_LAYER is not None:
            dm.NewLayer = ZIEL_LAYER
        if ZIEL_FARBE is not None:
            dm.NewColor = ZIEL_FARBE
        dm.Apply(neue)
        dm.Dispose()

    if REFSET_NAME:
        rs = [r for r in wp.GetAllReferenceSets() if r.Name.upper() == REFSET_NAME.upper()]
        if rs:
            rs[0].AddObjectsToReferenceSet(neue)
            log("Kurven zu Referenzset '%s' hinzugefuegt." % rs[0].Name)
        else:
            log("! Referenzset '%s' nicht gefunden." % REFSET_NAME)

    if DELETE_NOTES and fertig:
        s.UpdateManager.ClearErrorList()
        s.UpdateManager.AddObjectsToDeleteList(fertig)
        s.UpdateManager.DoUpdate(mark)
        log("%d Hinweise geloescht." % len(fertig))

    log("")
    log("Fertig: %d Linien aus %d Hinweisen. Rueckgaengig: 1x Strg+Z." % (len(neue), len(fertig)))


if __name__ == "__main__":
    main()