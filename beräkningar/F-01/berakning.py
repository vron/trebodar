"""
F-01: förutsättningar, referenser och laster.

    python berakning.py            -> F-01_forutsattningar.pdf

Läser indata.toml, räknar takets egenvikt, snölast och vindens hastighetstryck och sätter ihop
PDF via Typst (mall.typ). Kräver: pip install typst
"""
import json
import math
import tomllib
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).parent
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))


def fmt(x, n=2):
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    s = f"{abs(q):,.{n}f}".replace(",", " ").replace(".", ",")
    return ("−" if q < 0 else "") + s


# ------------------------------------------------------------------ egenvikter
tak = IN["tak"]
kg_tak = sum(t["kg"] for t in tak)
g_tak = kg_tak * 9.81 / 1000                       # kN/m² takyta
a = math.radians(IN["sno"]["alfa"])
g_tak_h = g_tak / math.cos(a)                      # kN/m² horisontell projektion
bj = IN["bjalklag"]
g_bj = bj["tjocklek"] / 1000 * bj["tunghet"]

# ------------------------------------------------------------------ snö, SS-EN 1991-1-3 tabell 5.2
sn = IN["sno"]
alfa = sn["alfa"]
mu1 = 0.8 if alfa <= 30 else 0.8 * (60 - alfa) / 30
mu2 = 0.8 + 0.8 * alfa / 30 if alfa <= 30 else 1.6   # flerspannstak, ᾱ = α
s1 = mu1 * sn["Ce"] * sn["Ct"] * sn["sk"]
s2 = mu2 * sn["Ce"] * sn["Ct"] * sn["sk"]

# ------------------------------------------------------------------ vind, SS-EN 1991-1-4 kap. 4
v = IN["vind"]
kr = 0.19 * (v["z0"] / v["z0_II"]) ** 0.07
cr = kr * math.log(v["z"] / v["z0"])
Iv = 1 / math.log(v["z"] / v["z0"])                 # kI = 1, c0 = 1
qb = 0.5 * v["rho"] * v["vb"] ** 2 / 1000
qp = (1 + 7 * Iv) * 0.5 * v["rho"] * (cr * v["vb"]) ** 2 / 1000
ce = qp / qb

print(f"tak {kg_tak:.1f} kg/m² = {g_tak:.3f} kN/m² takyta ({g_tak_h:.3f} horisontellt)")
print(f"snö μ1 {mu1:.2f} s {s1:.2f}, μ2 {mu2:.2f} s {s2:.2f}")
print(f"vind kr {kr:.4f} cr {cr:.3f} Iv {Iv:.3f} qb {qb:.3f} qp {qp:.3f} ce {ce:.2f}")

R = {
    "projekt": IN["projekt"], "objekt": IN["objekt"], "klasser": IN["klasser"],
    "tak": [dict(skikt=t["skikt"], kg=fmt(t["kg"], 1)) for t in tak],
    "kg_tak": fmt(kg_tak, 1), "g_tak": fmt(g_tak, 2), "g_tak_h": fmt(g_tak_h, 2),
    "bj": dict(t=bj["tjocklek"], gamma=fmt(bj["tunghet"], 0), g=fmt(g_bj, 2), golv=fmt(bj["golv"], 1)),
    "nyttig": {k: fmt(x, 1) for k, x in IN["nyttig"].items()},
    "sno": dict(sk=fmt(sn["sk"], 1), Ce=fmt(sn["Ce"], 1), Ct=fmt(sn["Ct"], 1), alfa=alfa,
                mu1=fmt(mu1, 1), mu2=fmt(mu2, 1), s1=fmt(s1, 2), s2=fmt(s2, 2)),
    "vind": dict(vb=v["vb"], z0=fmt(v["z0"], 3), z=fmt(v["z"], 1), kr=fmt(kr, 3), cr=fmt(cr, 2),
                 Iv=fmt(Iv, 3), qb=fmt(qb, 2), qp=fmt(qp, 2), ce=fmt(ce, 2)),
    "handlingar": IN["handling"], "nedb": IN["nedbojning"],
}
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

import typst  # noqa: E402
pdf = HERE / f"{IN['projekt']['dokument']}_forutsattningar.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(HERE.parent / ".fonts")])
print(pdf.name)
