"""Natthimlen för renderingen: stjärnorna och månen där de står på platsen vid tiden, när solen är mer än 6° under
horisonten.

    natt(tid, plats, sol_hojd) -> dict | None

- Stjärnorna: Yale Bright Star Catalogue (BSC5, Hoffleit & Warren 1991, lokalt/natthimmel/bsc5.dat, versionshanteras
  inte) till MAG_MAX, J2000 med precessionen till tiden (Meeus 21.1), som riktningar i modellens koordinater med
  magnitud och färgindex B−V. De tänds från skymningen (solen −6°) till mörker (−12°).
- Månen (Schlyter, med de största störningarna och parallaxen; omkring en bågminut): riktningen, den belysta andelen
  och belysningen på marken (fullmåne 0,25 lux, fasvinkelns ljuskurva (Allen) och atmosfärens dämpning), med NASA:s
  karta (CGI Moon Kit, LROC, public domain, lokalt/natthimmel/lroc_color_poles_2k.tif) för ytan i Blender.
- Månhimlen: månljuset spritt i atmosfären, som den klara dagshimlen med solen där månen står (dagsljus.klar_himmel),
  nedskalad med månens ljus: belysningen på en horisontell yta och färgen.

Hämta filerna med `./mod omgivning --hamta` (natthimmel.hamta).
"""
from __future__ import annotations

import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .dagsljus import OZON, VATTEN, Plats, fargen, klar_himmel, solposition, vader
from .karna import ROT

MAPP = ROT / "lokalt" / "natthimmel"
KATALOG = MAPP / "bsc5.dat"
MANKARTA = MAPP / "lroc_color_poles_2k.tif"
KALLOR = {KATALOG: "http://tdc-www.harvard.edu/catalogs/bsc5.dat.gz",
          MANKARTA: "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_2k.tif"}
MAG_MAX = 5.5                        # de svagaste stjärnorna som tas med
FULLMANE_LUX = 0.25                  # fullmånens belysning med månen i zenit, utan atmosfär


def hamta() -> list[str]:
    """Katalogen och månkartan till MAPP, om de saknas."""
    import gzip
    nya = []
    MAPP.mkdir(parents=True, exist_ok=True)
    for fil, url in KALLOR.items():
        if fil.exists():
            continue
        data = urllib.request.urlopen(url, timeout=60).read()
        fil.write_bytes(gzip.decompress(data) if url.endswith(".gz") else data)
        nya.append(fil.name)
    return nya


def tidpunkt(iso: str) -> datetime:
    """Tiden ur ISO 8601 (dagsljus.Ljus.tid)."""
    return datetime.fromisoformat(iso)


def _r(x: float) -> float:
    return math.radians(x)


def _horisont(ra: float, dec: float, lst: float, lat: float) -> tuple[float, float]:
    """Azimut (från norr, medurs) och höjd [°] ur rektascension och deklination [°] vid den lokala stjärntiden."""
    ha = _r(lst - ra)
    d, la = _r(dec), _r(lat)
    hojd = math.asin(math.sin(la) * math.sin(d) + math.cos(la) * math.cos(d) * math.cos(ha))
    az = math.atan2(-math.sin(ha) * math.cos(d), math.cos(la) * math.sin(d) - math.sin(la) * math.cos(d) * math.cos(ha))
    return math.degrees(az) % 360.0, math.degrees(hojd)


def _jd(t: datetime) -> float:
    return 2440587.5 + t.astimezone(timezone.utc).timestamp() / 86400.0


def _lst(jd: float, lon: float) -> float:
    """Lokal stjärntid [°] (GMST, Meeus 12.4)."""
    T = (jd - 2451545.0) / 36525.0
    return (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T + lon) % 360.0


def stjarnor(t: datetime, plats: Plats) -> list[list[float]]:
    """Stjärnorna över horisonten: [x, y, z, magnitud, B−V] (riktningen i modellens koordinater)."""
    if not KATALOG.exists():
        return []
    jd = _jd(t)
    ar = (jd - 2451545.0) / 365.25
    lst = _lst(jd, plats.lon)
    ut = []
    for rad in KATALOG.read_text(encoding="latin-1").splitlines():
        try:
            mag = float(rad[102:107])
            ra = (int(rad[75:77]) + int(rad[77:79]) / 60 + float(rad[79:83]) / 3600) * 15.0
            dec = (int(rad[84:86]) + int(rad[86:88]) / 60 + int(rad[88:90]) / 3600) * (-1 if rad[83] == "-" else 1)
        except ValueError:
            continue
        if mag > MAG_MAX:
            continue
        try:
            bv = float(rad[109:114])
        except ValueError:
            bv = 0.6
        # precessionen J2000 → tiden (Meeus 21.1): m = 3,075 s/år, n = 20,043″/år
        ra += ar * (46.1244 + 20.0431 * math.sin(_r(ra)) * math.tan(_r(dec))) / 3600.0
        dec += ar * 20.0431 * math.cos(_r(ra)) / 3600.0
        az, h = _horisont(ra, dec, lst, plats.lat)
        if h > -1.0:
            ut.append([*plats.riktning(az, h), mag, bv])
    return ut


def mane(t: datetime, plats: Plats) -> dict:
    """Månen: azimut och topocentrisk höjd [°], riktningen i modellens koordinater, belysta andelen, fasvinkeln [°],
    belysningen vinkelrätt mot månen på marken [lux] och månhimlen (_manhimlen) när månen står över horisonten."""
    d = _jd(t) - 2451543.5                                          # dagar från 2000-01-00
    N, i, w = 125.1228 - 0.0529538083 * d, 5.1454, 318.0634 + 0.1643573223 * d
    a, e, M = 60.2666, 0.0549, (115.3654 + 13.0649929509 * d) % 360.0
    ws, Ms = 282.9404 + 4.70935e-5 * d, (356.0470 + 0.9856002585 * d) % 360.0
    E = M + math.degrees(e * math.sin(_r(M)) * (1 + e * math.cos(_r(M))))
    for _ in range(5):
        E -= (E - math.degrees(e * math.sin(_r(E))) - M) / (1 - e * math.cos(_r(E)))
    x, y = a * (math.cos(_r(E)) - e), a * math.sqrt(1 - e * e) * math.sin(_r(E))
    r, v = math.hypot(x, y), math.degrees(math.atan2(y, x))
    xe = r * (math.cos(_r(N)) * math.cos(_r(v + w)) - math.sin(_r(N)) * math.sin(_r(v + w)) * math.cos(_r(i)))
    ye = r * (math.sin(_r(N)) * math.cos(_r(v + w)) + math.cos(_r(N)) * math.sin(_r(v + w)) * math.cos(_r(i)))
    ze = r * math.sin(_r(v + w)) * math.sin(_r(i))
    lon, lat = math.degrees(math.atan2(ye, xe)), math.degrees(math.atan2(ze, math.hypot(xe, ye)))
    Ls, Lm = Ms + ws, M + w + N
    D, F = Lm - Ls, Lm - N
    s = lambda q: math.sin(_r(q))                                   # noqa: E731
    lon += (-1.274 * s(M - 2 * D) + 0.658 * s(2 * D) - 0.186 * s(Ms) - 0.059 * s(2 * M - 2 * D)
            - 0.057 * s(M - 2 * D + Ms) + 0.053 * s(M + 2 * D) + 0.046 * s(2 * D - Ms) + 0.041 * s(M - Ms)
            - 0.035 * s(D) - 0.031 * s(M + Ms) - 0.015 * s(2 * F - 2 * D) + 0.011 * s(M - 4 * D))
    lat += (-0.173 * s(F - 2 * D) - 0.055 * s(M - F - 2 * D) - 0.046 * s(M + F - 2 * D) + 0.033 * s(F + 2 * D)
            + 0.017 * s(2 * M + F))
    r += -0.58 * math.cos(_r(M - 2 * D)) - 0.46 * math.cos(_r(2 * D))
    ecl = _r(23.4393 - 3.563e-7 * d)
    xg, yg, zg = math.cos(_r(lon)) * math.cos(_r(lat)), math.sin(_r(lon)) * math.cos(_r(lat)), math.sin(_r(lat))
    yq, zq = yg * math.cos(ecl) - zg * math.sin(ecl), yg * math.sin(ecl) + zg * math.cos(ecl)
    ra, dec = math.degrees(math.atan2(yq, xg)), math.degrees(math.atan2(zq, math.hypot(xg, yq)))
    az, h = _horisont(ra, dec, _lst(_jd(t), plats.lon), plats.lat)
    h -= math.degrees(math.asin(1 / r)) * math.cos(_r(h))           # parallaxen
    elong = math.degrees(math.acos(math.cos(_r(lon - Ls)) * math.cos(_r(lat))))
    fas = 180.0 - elong                                             # fasvinkeln
    luft = 1.0 / (math.sin(_r(h)) + 0.50572 * (h + 6.07995) ** -1.6364) if h > 0 else math.inf
    lux = FULLMANE_LUX * 10 ** (-0.4 * (0.026 * fas + 4e-9 * fas ** 4)) * math.exp(-0.21 * luft) / math.exp(-0.21)
    himmel_lux, himmel_farg = _manhimlen(h, t.month, lux) if h > 0 else (0.0, (1.0, 1.0, 1.0))
    return {"azimut": az, "hojd": h, "riktning": list(plats.riktning(az, h)),
            "andel": (1 - math.cos(_r(elong))) / 2, "fasvinkel": fas, "lux": lux if h > 0 else 0.0,
            "himmel_lux": himmel_lux, "himmel_farg": himmel_farg}


def _manhimlen(hojd: float, manad: int, lux: float) -> tuple[float, tuple[float, float, float]]:
    """Månhimlen i klart väder: belysningen på en horisontell yta [lux] och färgen (linjär Rec. 709, luminansen 1),
    som den klara dagshimlen med solen på månens höjd, skalad med kvoten mellan månens och solens ljus vinkelrätt mot
    dem."""
    dn, dh, _ = klar_himmel(hojd, 1.0, vader("klart").beta, OZON[manad - 1], VATTEN[manad - 1])
    _, sol_lux, _ = fargen(dn)
    farg, himmel_lux, _ = fargen(dh)
    return lux * himmel_lux / sol_lux, farg


def natt(t: datetime, plats: Plats) -> dict | None:
    """Natthimlen vid tiden (stjärnorna, deras styrka i skymningen 0–1, månen och riktningen mot solen för månens
    fas), eller None när solen är mindre än 6° under horisonten."""
    az, h, _ = solposition(t, plats.lat, plats.lon)
    if h > -6.0:
        return None
    m = mane(t, plats)
    return {"stjarnor": stjarnor(t, plats), "styrka": min(1.0, (-6.0 - h) / 6.0), "mane": m if m["hojd"] > -1.0 else None,
            "sol": list(plats.riktning(az, h)), "kartan": str(MANKARTA) if MANKARTA.exists() else None}
