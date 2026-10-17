"""
R-03: betongarbetets bärande delar i 3D, ur samma källor som ritningarna: bottenplattan, källarväggarna och rören
(R-04, R-05, K-06) och mellanbjälklaget (K-05, R-06).

Koordinater i mm enligt K-05 (x, y); z = 0 i bottenplattans överkant (som R-05), mellanbjälklagets överkant
z = 2 250. snitt: kropparna klipps i planet (behåll en sida av ett lodrätt plan), så att snittytorna blir kropparnas
egna sidor.
"""
import os
import sys

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "R-05"))
import kallare as K  # noqa: E402

H, HMB = K.H_VAGG, K.H_MB                         # 2 100, 150
Z1 = H + HMB                                      # plan 1:s golv
HB, TF, HP = K.UTF["h_balk"], K.T_FOT, K.H_PLATTA # 200, 100, 100

FARG = dict(betong="#d9d6ce", karna="#b7b1a6", eps="#f1f4f7", s300="#c6d6e8", stal="#55667a")

KALLARE, BETONG = K.KALLARE, K.BETONG
KANT, INRE, PLINTAR = K.kantbalk(), K.balkar_inre(), K.plintar()
TJOCK = unary_union([KANT, INRE] + list(PLINTAR.values())).intersection(BETONG)
KONTUR, HAL, MARK = Polygon(K.G["kontur"]), Polygon(K.G["hal"]), Polygon(K.G["mark"])


def grund(s, kapa=None):
    """Bottenplattan: L-elementen (rygg och fot), cellplasten (S100 i två skikt, S300 under balkar och plintar),
    balkarna och plintarna och plattan; kapa: plattan tas bort där, så att balkarna och plintarna syns."""
    rygg = KALLARE.difference(BETONG)
    fot = KALLARE.difference(KALLARE.buffer(-K.B_L, join_style=2)).difference(rygg)
    s.prisma(rygg, -HB - TF, 0.0, FARG["s300"])
    s.prisma(fot, -HB - TF, -HB, FARG["s300"])
    s.prisma(unary_union([INRE] + list(PLINTAR.values())).difference(KANT), -HB - TF, -HB, FARG["s300"])
    falt = BETONG.difference(TJOCK)
    s.prisma(falt.intersection(KALLARE.buffer(-K.B_L, join_style=2)), -HB - TF, -HB, FARG["eps"])
    s.prisma(falt, -HB, -HP, FARG["eps"])
    s.prisma(TJOCK, -HB, -HP, FARG["betong"])
    s.prisma(BETONG if kapa is None else BETONG.difference(kapa), -HP, 0.0, FARG["betong"])


def vaggar(s):
    """Källarväggarna (Kub 350-150): kärnan och cellplasten, öppningarna, bröstningarna under fönstren."""
    s.prisma(K.KARNA, 0.0, H, FARG["karna"])
    s.prisma(K.HEL.difference(K.KARNA), 0.0, H, FARG["eps"])
    for o in K.OPPNINGAR:
        if o["z0"] <= 0:
            continue
        a, b, c = o["x0"] + K.GLIPA_SMYG, o["x1"] - K.GLIPA_SMYG, o["c"]
        hel = box(a, c - K.T_VAGG / 2, b, c + K.T_VAGG / 2)
        kar = box(a, c - K.T_KARNA / 2, b, c + K.T_KARNA / 2)
        if o["ax"] == "v":
            hel, kar = (Polygon([(y, x) for x, y in g.exterior.coords]) for g in (hel, kar))
        s.prisma(kar, 0.0, o["z0"], FARG["karna"])
        s.prisma(hel.difference(kar), 0.0, o["z0"], FARG["eps"])


def ror(s):
    """Stålrören VKR 80×80 på fotplåtar i plintarna, med topplåt under mellanbjälklaget."""
    for r in K.ROR:
        bx, by, _ = K.FOTPLAT[r["n"]]
        mx, my = r["mitt"]
        s.stang(mx - bx / 2, mx + bx / 2, my - by / 2, my + by / 2, -15.0, 3.0, FARG["stal"])
        for x, y in r["ror"]:
            s.stang(x - K.PLAT / 2, x + K.PLAT / 2, y - K.PLAT / 2, y + K.PLAT / 2, 3.0, H, FARG["stal"])


def bjalklag(s, kapa=None):
    """Mellanbjälklaget 150 med trapphålet, också plattan på mark (plan 1) på 400 mm cellplast."""
    p = KONTUR.difference(HAL)
    s.prisma(p if kapa is None else p.difference(kapa), H, Z1, FARG["betong"])
    s.prisma(MARK.buffer(-1.0, join_style=2), H - 400.0, H, FARG["eps"])
