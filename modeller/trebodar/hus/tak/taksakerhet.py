"""Taksäkerheten (BBR 8:24, #125): tillträdet till skorstenen för sotning och snörasskydden över ytterdörrarna.

Tillträdet går från altanen: lös stege mot takfallet 2SO vid gaveln 2SV, där dalen DB4 slutar (glidskydd för stegen),
längs dalen och uppför en takstege från dalen till skorstenens norra sida (på den västra står förbränningsluftens
huv). Sotaren står på stegen bredvid skorstenen: ingen gångbrygga och ingen arbetsplattform (byggherrens val, #125).
Snörasskydd, två rör på konsoler, sitter över ytterdörrarna som står under en takfot.

Allt fästs i plåtens falsar med falsfästen, utan hål i plåten: fästskenorna och konsolerna står på falsarna
(takytor.falsar). Delarna är förenklade (fyrkantsrör), med systemets yttermått.
"""
from __future__ import annotations

from modellering import Del, Form, Kapad, Montage, Placering, box

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.kamin import kamin
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT
from trebodar.material import STAL_VFZ

from .takytor import REGIONER, falsar

TAKFALL = "2SO"                  # tillträdet går på mittre huskroppens takfall mot dalen DB4
STEGE_FRAN_DAL = 350.0           # takstegens nedre ände från dallinjen, i plan (ovanför rändalen)
STEGE_FORBI = 300.0              # takstegens övre ände så långt upp längs skorstenens sida, i plan
KONSOL_B = 40.0                  # konsolernas bredd (på falsen)
KONSOL_CC = 1100.0               # största avstånd mellan konsolerna längs snörasskydden
STEGE_B, STEGE_PROFIL = 400.0, 30.0  # takstegen: bredd och sidostyckenas profil
STEG_CC = 300.0                  # stegens delning längs takfallet
GLIDSKYDD = (500.0, 60.0, 40.0)  # glidskyddet för lös stege: längd längs takfallet, bredd, höjd
SNORAS_FRAN_TAKFOT = 600.0       # snörasskyddet från takbalkarnas ände, längs takfallet
SNORAS_UT = 500.0                # snörasskyddet så långt förbi dörrens sidor
SNORAS_ROR, SNORAS_H = 32.0, (60.0, 130.0)   # rörens mått och höjd över falsen (två rör)
SNORAS_DORRAR = ("1SO-D1", "2SO-D1", "3SO-D1", "1NV-D1")    # ytterdörrarna under en takfot


def _falsar(kod: str) -> list[float]:
    return falsar(kod, FALT[kod].fonster)


def _z(kod: str, x: float, w: float) -> float:
    return L.z_skikt(S.TAKFALL[kod], x, w)


def _langs(kod: str, x0: float, x1: float, y0: float, y1: float, w0: float, w1: float) -> Form:
    """Lådan x0–x1, y0–y1 mellan takets skikt w0 och w1 (parallell med takplanet)."""
    t = S.TAKFALL[kod]
    xa, xb = sorted((x0, x1))
    z0, z1 = min(_z(kod, xa, w0), _z(kod, xb, w0)) - 5.0, max(_z(kod, xa, w1), _z(kod, xb, w1)) + 5.0
    xm = (xa + xb) / 2
    n = t.riktning * S.TAN
    return Kapad(Kapad(box(xa, xb, y0, y1, z0, z1), (xm, y0, _z(kod, xm, w0)), (n, 0.0, -1.0)),
                 (xm, y0, _z(kod, xm, w1)), (-n, 0.0, 1.0))


def _konsoler(falsar: list[float], y0: float, y1: float) -> list[float]:
    """Falsarna som bär mellan y0 och y1: den första och den sista och så många emellan att avståndet inte blir
    större än KONSOL_CC."""
    inom = [y for y in falsar if y0 <= y <= y1]
    if len(inom) < 2:
        raise ValueError(f"för få falsar mellan y {y0:.0f} och {y1:.0f}")
    ut = [inom[0]]
    for a, b in zip(inom, inom[1:]):
        if b - ut[-1] > KONSOL_CC:
            ut.append(a)
    if ut[-1] != inom[-1]:
        ut.append(inom[-1])
    return sorted(set(ut))


def _tilltrade() -> Montage:
    m = Montage("Tillträde till skorstenen", "TS", "Glidskydd för lös stege vid gaveln 2SV och takstege från dalen DB4 "
                "upp till skorstenen (BBR 8:24)", produkt="TAKSAKERHET")
    kod = TAKFALL
    t = S.TAKFALL[kod]
    assert t.riktning > 0
    falsarna = _falsar(kod)
    rs = REGIONER[kod]
    x_dal = max(r.nedre.x for r in rs)                  # dallinjen (takfoten vid gaveln 2NO ligger längre ut)
    y_gavel = max(r.y1 for r in rs)
    kx0, _, _, ky1 = kamin.kladselns_lada()
    wf = L.FALS[1]
    # takstegen norr om skorstenen, mellan två falsar: fästskenor tvärs över falsarna, sidostycken och steg
    pk = [y for y in falsarna if ky1 + 30.0 <= y][:2]
    if len(pk) < 2 or pk[1] - pk[0] < STEGE_B + 40.0:
        raise ValueError("takstegen ryms inte mellan två falsar norr om skorstenen")
    y_st = (pk[0] + pk[1]) / 2
    sx0, sx1 = x_dal + STEGE_FRAN_DAL, kx0 + STEGE_FORBI
    sy0, sy1 = y_st - STEGE_B / 2, y_st + STEGE_B / 2
    p = STEGE_PROFIL
    n_skenor = max(2, int((sx1 - sx0) / S.COS // 1000.0) + 1)
    for i in range(n_skenor):
        x = sx0 + 60.0 + i * (sx1 - sx0 - 120.0) / (n_skenor - 1)
        m.lagg(Del("Fästskena för takstege, falsfästen", _langs(kod, x - 20.0, x + 20.0, pk[0] - 30.0, pk[1] + 30.0, wf,
                                                                 wf + 20.0), STAL_VFZ), Placering(), f"TS-SKENA{i + 1}")
    stege: Form = (_langs(kod, sx0, sx1, sy0, sy0 + p, wf + 20.0, wf + 20.0 + p)
                   | _langs(kod, sx0, sx1, sy1 - p, sy1, wf + 20.0, wf + 20.0 + p))
    n_steg = int((sx1 - sx0) / S.COS // STEG_CC)
    for i in range(n_steg):
        x = sx0 + (i + 0.5) * (sx1 - sx0) / n_steg
        stege = stege | _langs(kod, x - 15.0, x + 15.0, sy0 + p, sy1 - p, wf + 20.0, wf + 20.0 + p)
    m.lagg(Del(f"Takstege {STEGE_B:g} L={(sx1 - sx0) / S.COS:.0f}", stege, STAL_VFZ), Placering(), "TS-STEGE")
    # glidskyddet för den lösa stegen från altanen: på falsen närmast gaveln 2SV, ovanför rändalen
    gl, gb, gh = GLIDSKYDD
    yg = max(y for y in falsarna if y < y_gavel - 150.0)
    m.lagg(Del("Glidskydd för lös stege, falsfäste", _langs(kod, sx0, sx0 + gl, yg - gb / 2, yg + gb / 2, wf, wf + gh),
               STAL_VFZ), Placering(), "TS-GLID")
    return m


def _snorasskydd() -> Montage:
    m = Montage("Snörasskydd", "SN", "Snörasskydd, två rör på konsoler i falsarna, över ytterdörrarna under takfot "
                "(BBR 8:2434)", produkt="SNORASSKYDD")
    dorrar = {o.kod: o for v in OPPNINGAR.values() for o in v}
    for kod_d in SNORAS_DORRAR:
        o = dorrar[kod_d]
        v = S.YTTERVAGGAR[o.vagg]
        ya, yb = sorted(v.origo[1] + v.u[1] * u for u in (o.u0, o.u1))
        kod = o.vagg
        t = S.TAKFALL[kod]
        rs = [r for r in REGIONER[kod] if r.nedre.x == FALT[kod].takfot]
        y_min, y_max = min(r.y0 for r in rs), max(r.y1 for r in rs)
        kons = _konsoler(_falsar(kod), max(ya - SNORAS_UT - 300.0, y_min + 100.0), min(yb + SNORAS_UT + 300.0, y_max - 100.0))
        y0, y1 = kons[0] - 150.0, kons[-1] + 150.0
        x0 = t.x_takfot + t.riktning * SNORAS_FRAN_TAKFOT * S.COS
        x1 = x0 + t.riktning * 100.0
        wf = L.FALS[1]
        d = SNORAS_ROR
        ror: Form | None = None
        for h in SNORAS_H:
            r_ = _langs(kod, x0 + t.riktning * 30.0, x0 + t.riktning * (30.0 + d), y0, y1, wf + h, wf + h + d)
            ror = r_ if ror is None else ror | r_
        assert ror is not None
        m.lagg(Del(f"Snörasskydd, två rör L={y1 - y0:.0f}", ror, STAL_VFZ), Placering(), f"SN-{kod_d}")
        for i, y in enumerate(kons, 1):
            m.lagg(Del("Konsol för snörasskydd, falsfäste",
                       _langs(kod, x0, x1, y - KONSOL_B / 2, y + KONSOL_B / 2, wf, wf + SNORAS_H[1] + d + 10.0)
                       - _langs(kod, x0 + t.riktning * 30.0, x0 + t.riktning * (30.0 + d), y - KONSOL_B, y + KONSOL_B,
                                wf + SNORAS_H[0], wf + SNORAS_H[0] + d)
                       - _langs(kod, x0 + t.riktning * 30.0, x0 + t.riktning * (30.0 + d), y - KONSOL_B, y + KONSOL_B,
                                wf + SNORAS_H[1], wf + SNORAS_H[1] + d), STAL_VFZ), Placering(),
                   f"SN-{kod_d}-K{i}")
    return m


def montage() -> Montage:
    m = Montage("Taksäkerhet", beskrivning="Tillträdet till skorstenen och snörasskydden (BBR 8:24, #125)")
    m.lagg(_tilltrade())
    m.lagg(_snorasskydd())
    return m
