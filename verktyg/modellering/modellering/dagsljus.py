"""Dagsljus: solens läge och ljusets riktning, färg och styrka på en plats vid en viss tid och i ett visst väder, för
renderingen (sol och himmel i Blender) och för analyser (solstudier, ljus genom fönster).

    dagsljus(manad, dag, klocka, vader, plats) -> Ljus

ger solens azimut och höjd, riktningen mot solen i modellens koordinater, solens och himlens färg (linjär Rec. 709,
som Blenders scen) och belysning (lux) och strålningen (W/m²). Väder: "sol" (klart), "lätt mulet" (halvklart, solen
skymd en del av tiden och mjukare skuggor) och "mulet" (inget direkt solljus); på engelska "sunny",
"slightlyovercast" och "overcast".

Modellen:
- Solens läge: NOAA:s solkalkylator (efter Meeus), med refraktion; omkring 0,01° åren 1800–2100. Lokal tid med
  sommartid (tidszonen).
- Klart väder: solens spektrum utanför atmosfären (svartkropp 5 772 K, solarkonstanten 1 361 W/m² och avståndet till
  solen) genom atmosfären längs luftmassan (Kasten & Young 1989): Rayleighspridning, aerosoler (Ångström α, β) och
  ozon (Hartley- och Chappuisbanden). Himlens diffusa ljus som i SPCTRAL2 (Bird & Riordan 1986): Rayleigh- och
  aerosolspridning och reflexer mellan mark och himmel. Vattenånga dämpar bredbandsstrålningen (Lacis & Hansen 1974).
  Färgen ur spektrum med CIE 1931 (Wyman, Sloan & Shirley 2013) till linjär Rec. 709; belysningen med 683 lm/W.
- Moln (Kasten & Czeplak 1980): globalstrålningen G = G_klar·(1 − 0,75·(N/8)^3,4), där N är molnigheten i oktas,
  och diffusandelen går från den klara himlens till 1 som (N/8)². Det diffusa ljuset från molnen har globalljusets
  spektrum, något blåare (MOLN_BLA: vattnet i molnen dämpar det röda; mulet dagsljus är omkring 6 500 K). Mulet
  (N = 8): inget direkt solljus; himlen som CIE:s mulna standardhimmel (luminansen tre gånger högre i zenit än vid
  horisonten).

Klimatet (ozon och vattenånga per månad) är ungefärliga medelvärden för västkusten, 58–59° N.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

LUMEN_PER_WATT = 683.0
T_SOL = 5772.0                       # K, solens effektiva temperatur
SOLRADIE_AU = 6.957e8 / 1.495978707e11
L = np.arange(300.0, 4001.0, 5.0)    # våglängder [nm]
_LU = L / 1000.0                     # [µm]
_DL = 5.0

# ozon [DU] och utfällbart vatten [cm] per månad, 58–59° N (ungefärligt)
OZON = (330, 370, 390, 390, 370, 350, 330, 310, 290, 290, 300, 310)
VATTEN = (0.8, 0.8, 0.9, 1.1, 1.4, 1.8, 2.2, 2.1, 1.7, 1.4, 1.0, 0.9)
MARKALBEDO = 0.15
ANGSTROM_ALFA = 1.3
MOLN_BLA = 0.75                      # ljuset genom moln: globalljusets spektrum · (λ/555 nm)^−0,75 (ca 6 500 K mitt på dagen)


@dataclass(frozen=True)
class Plats:
    """En plats: latitud och longitud (grader), höjden över havet för modellens z = 0 (m), azimuten (grader från
    geografiska norr, medurs) för modellens +x och tidszonen."""
    lat: float
    lon: float
    hojd: float = 0.0
    azimut_x: float = 90.0
    tidszon: str = "Europe/Stockholm"

    def riktning(self, azimut: float, hojd: float) -> tuple[float, float, float]:
        """Enhetsvektorn mot en punkt på himlen (azimut och höjd i grader) i modellens koordinater."""
        v, h = math.radians(self.azimut_x - azimut), math.radians(hojd)
        return (math.cos(h) * math.cos(v), math.cos(h) * math.sin(v), math.sin(h))


@dataclass(frozen=True)
class Vader:
    namn: str
    moln: float                      # molnighet [oktas]
    beta: float                      # Ångströms turbiditet (aerosolernas optiska djup vid 1 µm)
    sol_vinkel: float                # solskivans skenbara diameter [°]: större i dis och tunna moln (mjukare skuggor)


VADER = {
    "sol": Vader("sol", 0.0, 0.05, 0.53),
    "lätt mulet": Vader("lätt mulet", 4.0, 0.12, 2.5),
    "mulet": Vader("mulet", 8.0, 0.12, 0.0),
}
_ALIAS = {"sunny": "sol", "klart": "sol", "slightlyovercast": "lätt mulet", "slightly overcast": "lätt mulet",
          "latt mulet": "lätt mulet", "halvklart": "lätt mulet", "overcast": "mulet"}


def vader(namn: str) -> Vader:
    k = namn.strip().lower().replace("_", " ")
    return VADER[_ALIAS.get(k, k)]


@dataclass(frozen=True)
class Ljus:
    """Dagsljuset: solens läge och riktning, sol och himmel (färg som linjär Rec. 709 med luminansen 1)."""
    tid: str                         # lokal tid, ISO 8601
    vader: str
    sol_azimut: float                # [°] från geografiska norr, medurs
    sol_hojd: float                  # [°] över horisonten (skenbar, med refraktion)
    riktning: tuple[float, float, float]     # mot solen, i modellens koordinater
    sol_farg: tuple[float, float, float]
    sol_lux: float                   # direkt belysning vinkelrätt mot solen
    sol_vinkel: float                # solskivans skenbara diameter [°]
    himmel_farg: tuple[float, float, float]
    himmel_lux: float                # diffus belysning på en horisontell yta
    moln: float                      # [oktas]
    beta: float
    ozon: float                      # [DU]
    dni: float                       # direkt normalstrålning [W/m²]
    dhi: float                       # diffus horisontell strålning [W/m²]
    ghi: float                       # global horisontell strålning [W/m²]
    sol_cct: float                   # solljusets färgtemperatur [K]
    himmel_cct: float

    @property
    def sol_lux_horisontell(self) -> float:
        return self.sol_lux * max(0.0, math.sin(math.radians(self.sol_hojd)))

    @property
    def global_lux(self) -> float:
        return self.sol_lux_horisontell + self.himmel_lux

    def som_dict(self) -> dict[str, object]:
        return asdict(self)


# ------------------------------------------------------------------ solens läge (NOAA)

def solposition(t: datetime, lat: float, lon: float) -> tuple[float, float, float]:
    """Solens azimut (från norr, medurs) och skenbara höjd [°] och avståndet till solen [AU] vid tiden t (med
    tidszon)."""
    u = t.astimezone(timezone.utc)
    jd = 2440587.5 + u.timestamp() / 86400.0
    T = (jd - 2451545.0) / 36525.0
    l0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0
    m = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    mr = math.radians(m)
    c = (math.sin(mr) * (1.914602 - T * (0.004817 + 0.000014 * T)) + math.sin(2 * mr) * (0.019993 - 0.000101 * T)
         + math.sin(3 * mr) * 0.000289)
    sann = l0 + c
    r = 1.000001018 * (1 - e * e) / (1 + e * math.cos(math.radians(m + c)))
    om = math.radians(125.04 - 1934.136 * T)
    lam = math.radians(sann - 0.00569 - 0.00478 * math.sin(om))
    eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60
    eps = math.radians(eps0 + 0.00256 * math.cos(om))
    dekl = math.asin(math.sin(eps) * math.sin(lam))
    y = math.tan(eps / 2) ** 2
    l0r = math.radians(l0)
    eot = 4 * math.degrees(y * math.sin(2 * l0r) - 2 * e * math.sin(mr) + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
                           - 0.5 * y * y * math.sin(4 * l0r) - 1.25 * e * e * math.sin(2 * mr))
    minuter = u.hour * 60 + u.minute + u.second / 60 + u.microsecond / 6e7
    tst = (minuter + eot + 4 * lon) % 1440
    ha = math.radians(tst / 4 - 180 if tst >= 0 else tst / 4 + 180)
    fi = math.radians(lat)
    cosz = max(-1.0, min(1.0, math.sin(fi) * math.sin(dekl) + math.cos(fi) * math.cos(dekl) * math.cos(ha)))
    z = math.acos(cosz)
    h = 90 - math.degrees(z)
    # refraktion (NOAA)
    if h > 85:
        ref = 0.0
    elif h > 5:
        th = math.tan(math.radians(h))
        ref = 58.1 / th - 0.07 / th ** 3 + 0.000086 / th ** 5
    elif h > -0.575:
        ref = 1735 + h * (-518.2 + h * (103.4 + h * (-12.79 + h * 0.711)))
    else:
        ref = -20.774 / math.tan(math.radians(h))
    h += ref / 3600
    az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(fi) - math.tan(dekl) * math.cos(fi))) + 180) \
        % 360
    return az, h, r


# ------------------------------------------------------------------ spektrum och färg

def _g(x: np.ndarray, mu: float, s1: float, s2: float) -> np.ndarray:
    return np.exp(-0.5 * ((x - mu) / np.where(x < mu, s1, s2)) ** 2)


XB = 1.056 * _g(L, 599.8, 37.9, 31.0) + 0.362 * _g(L, 442.0, 16.0, 26.7) - 0.065 * _g(L, 501.1, 20.4, 26.2)
YB = 0.821 * _g(L, 568.8, 46.9, 40.5) + 0.286 * _g(L, 530.9, 16.3, 31.1)
ZB = 1.217 * _g(L, 437.0, 11.8, 36.0) + 0.681 * _g(L, 459.0, 26.0, 13.8)
XYZ_TILL_RGB = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])


def _planck(lam_nm: np.ndarray, t: float) -> np.ndarray:
    h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23
    lam = lam_nm * 1e-9
    return 2 * h * c * c / lam ** 5 / np.expm1(h * c / (lam * k * t)) * 1e-9       # W/(m²·sr·nm)


E0 = math.pi * _planck(L, T_SOL) * SOLRADIE_AU ** 2                               # W/(m²·nm) vid 1 AU
TAU_R = 1.0 / (_LU ** 4 * (115.6406 - 1.335 / _LU ** 2))                          # Rayleigh, vid havsytan
K_O3 = 8.0 * np.exp(-(L - 300.0) / 12.4) + 0.12 * np.exp(-0.5 * ((L - 600.0) / 60.0) ** 2)   # [1/atm-cm]
OMEGA = 0.945 * np.exp(-0.095 * np.log(_LU / 0.4) ** 2)                          # aerosolernas albedo
_CS = np.where(_LU <= 0.45, (_LU + 0.55) ** 1.8, 1.0)


def fargen(e: np.ndarray) -> tuple[tuple[float, float, float], float, float]:
    """Spektrumets färg (linjär Rec. 709 med luminansen 1), belysning [lux] och färgtemperatur [K]."""
    X, Y, Z = (float(np.sum(e * b) * _DL) for b in (XB, YB, ZB))
    if Y <= 0:
        return (1.0, 1.0, 1.0), 0.0, 0.0
    rgb = np.maximum(XYZ_TILL_RGB @ np.array([X, Y, Z]) / Y, 0.0)
    # luminansen 1 i Rec. 709 (0,2126 R + 0,7152 G + 0,0722 B)
    rgb = rgb / float(rgb @ np.array([0.2126, 0.7152, 0.0722]))
    x, y = X / (X + Y + Z), Y / (X + Y + Z)
    n = (x - 0.3320) / (0.1858 - y)
    cct = 449 * n ** 3 + 3525 * n ** 2 + 6823.3 * n + 5520.33                    # McCamy
    return (float(rgb[0]), float(rgb[1]), float(rgb[2])), LUMEN_PER_WATT * Y, float(cct)


def svartkropp(kelvin: float) -> tuple[float, float, float]:
    """Glödande kropps färg vid temperaturen (t.ex. en lampa på 3 000 K) i linjär Rec. 709 med luminansen 1."""
    return fargen(_planck(L, kelvin))[0]


def _luftmassa(z_grader: float) -> float:
    return 1.0 / (math.cos(math.radians(z_grader)) + 0.50572 * (96.07995 - z_grader) ** -1.6364)


def klar_himmel(sol_hojd: float, avstand_au: float, beta: float, ozon_du: float, vatten_cm: float,
                hojd_m: float = 0.0, markalbedo: float = MARKALBEDO) -> tuple[np.ndarray, np.ndarray, float]:
    """Klar himmel: direkt normalstrålning och diffus horisontell strålning per våglängd [W/(m²·nm)] och vattenångans
    bredbandstransmission."""
    if sol_hojd <= 0.0:
        return np.zeros_like(L), np.zeros_like(L), 1.0
    z = 90.0 - sol_hojd
    cz = math.cos(math.radians(z))
    m = _luftmassa(z)
    p = math.exp(-hojd_m / 8434.5)
    o3 = ozon_du / 1000.0
    mo = (1 + 22 / 6370) / math.sqrt(cz * cz + 2 * 22 / 6370)
    tau_a = beta * _LU ** -ANGSTROM_ALFA
    e0 = E0 / avstand_au ** 2
    tr = np.exp(-m * p * TAU_R)
    ta = np.exp(-m * tau_a)
    to = np.exp(-mo * o3 * K_O3)
    dn = e0 * tr * ta * to
    taa = np.exp(-(1 - OMEGA) * tau_a * m)
    tas = np.exp(-OMEGA * tau_a * m)
    alg = math.log(1 - 0.65)
    afs = alg * (1.459 + alg * (0.1595 + alg * 0.4129))
    bfs = alg * (0.0783 + alg * (-0.3824 - alg * 0.5874))
    fs = 1 - 0.5 * math.exp((afs + bfs * cz) * cz)
    ir = e0 * cz * to * taa * (1 - tr ** 0.95) * 0.5
    ia = e0 * cz * to * taa * tr ** 1.5 * (1 - tas) * fs
    m1 = 1.8
    fs1 = 1 - 0.5 * math.exp((afs + bfs / m1) / m1)
    rs = np.exp(-m1 * o3 * K_O3) * np.exp(-(1 - OMEGA) * tau_a * m1) * (
        0.5 * (1 - np.exp(-m1 * p * TAU_R)) + (1 - fs1) * np.exp(-m1 * p * TAU_R) * (1 - np.exp(-OMEGA * tau_a * m1)))
    ig = (dn * cz + ir + ia) * rs * markalbedo / (1 - rs * markalbedo)
    dh = _CS * (ir + ia) + ig
    u = vatten_cm * m
    tw = 1 - 2.9 * u / ((1 + 141.5 * u) ** 0.635 + 5.925 * u)
    return dn, dh, tw


# ------------------------------------------------------------------ dagsljuset

def dagsljus(manad: int, dag: int, klocka: str | float, vader_: str | Vader = "sol", plats: Plats | None = None,
             ar: int = 2026) -> Ljus:
    """Dagsljuset den dag i månaden klockan (lokal tid, "HH:MM" eller timmar) i vädret, på platsen."""
    if plats is None:
        raise ValueError("platsen saknas")
    w = vader_ if isinstance(vader_, Vader) else vader(vader_)
    if isinstance(klocka, str):
        hh, _, mm = klocka.partition(":")
        timmar = int(hh) + (int(mm) if mm else 0) / 60
    else:
        timmar = float(klocka)
    t = datetime(ar, manad, dag, tzinfo=ZoneInfo(plats.tidszon)) + timedelta(hours=timmar)    # väggklockan
    az, h, r = solposition(t, plats.lat, plats.lon)
    ozon, vatten = OZON[manad - 1], VATTEN[manad - 1]
    dn, dh, tw = klar_himmel(h, r, w.beta, ozon, vatten, plats.hojd)
    sh = max(0.0, math.sin(math.radians(h)))
    sol_rgb, sol_lux, sol_cct = fargen(dn)
    _, dif_lux, _ = fargen(dh)
    # moln: globalljuset och diffusandelen (Kasten & Czeplak); det diffusa ljuset är den blå himlens del (1 − N/8) och
    # molnens, som har globalljusets spektrum
    n = min(max(w.moln, 0.0), 8.0) / 8.0
    g_klar = sol_lux * sh + dif_lux
    d0 = dif_lux / g_klar if g_klar > 0 else 1.0
    g = g_klar * (1 - 0.75 * n ** 3.4)
    d = d0 + (1 - d0) * n * n
    k_dir = ((1 - d) * g / (sol_lux * sh)) if sol_lux * sh > 0 else 0.0
    moln_lux = max(0.0, d * g - (1 - n) * dif_lux)
    moln_spektrum = (dn * sh + dh) * (L / 555.0) ** -MOLN_BLA
    _, moln_spektrum_lux, _ = fargen(moln_spektrum)
    himmel_rgb, himmel_lux, himmel_cct = fargen(
        (1 - n) * dh + moln_spektrum * (moln_lux / moln_spektrum_lux if moln_spektrum_lux > 0 else 0.0))
    dni_klar = float(np.sum(dn) * _DL) * tw
    dhi_klar = float(np.sum(dh) * _DL) * tw
    ghi_klar = dni_klar * sh + dhi_klar
    ghi = ghi_klar * (1 - 0.75 * n ** 3.4)
    dfrac = (dhi_klar / ghi_klar if ghi_klar > 0 else 1.0)
    dfrac = dfrac + (1 - dfrac) * n * n
    dhi = dfrac * ghi
    dni = (ghi - dhi) / sh if sh > 0 else 0.0
    return Ljus(tid=t.isoformat(timespec="minutes"), vader=w.namn, sol_azimut=az, sol_hojd=h,
                riktning=plats.riktning(az, h), sol_farg=sol_rgb, sol_lux=sol_lux * k_dir, sol_vinkel=w.sol_vinkel,
                himmel_farg=himmel_rgb, himmel_lux=himmel_lux,
                moln=w.moln, beta=w.beta, ozon=ozon, dni=dni, dhi=dhi, ghi=ghi, sol_cct=sol_cct, himmel_cct=himmel_cct)


# ------------------------------------------------------------------ redovisning

MANADER = ("januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober",
           "november", "december")


def _tal(v: float, d: int = 1) -> str:
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def beskrivning(lj: Ljus) -> str:
    """Ljuset i text (svenska)."""
    t = datetime.fromisoformat(lj.tid)
    off = t.utcoffset()
    utc = f"UTC+{off.total_seconds() / 3600:g}" if off is not None else ""
    rad = [f"{t.day} {MANADER[t.month - 1]} {t:%H:%M} ({utc}), {lj.vader}: solen i azimut {_tal(lj.sol_azimut)}° "
           f"och höjd {_tal(lj.sol_hojd)}°, mot modellens (x, y, z) = ({', '.join(_tal(c, 3) for c in lj.riktning)})"]
    if lj.sol_lux > 0:
        rad.append(f"  solljus {_tal(lj.sol_lux / 1000)} klx vinkelrätt ({_tal(lj.sol_lux_horisontell / 1000)} klx på "
                   f"marken), {_tal(lj.sol_cct, 0)} K, Rec. 709 ({' '.join(_tal(c, 2) for c in lj.sol_farg)}), "
                   f"solskivan {_tal(lj.sol_vinkel, 2)}°")
    rad.append(f"  himmel {_tal(lj.himmel_lux / 1000)} klx på marken, {_tal(lj.himmel_cct, 0)} K, Rec. 709 "
               f"({' '.join(_tal(c, 2) for c in lj.himmel_farg)}); molnighet {_tal(lj.moln, 0)}/8")
    rad.append(f"  global {_tal(lj.global_lux / 1000)} klx; strålning DNI {_tal(lj.dni, 0)}, DHI {_tal(lj.dhi, 0)}, "
               f"GHI {_tal(lj.ghi, 0)} W/m²")
    return "\n".join(rad)


def dygn(manad: int, dag: int, vader_: str, plats: Plats, steg_min: int = 30) -> list[Ljus]:
    """Ljuset under dagen, var steg_min minut medan solen är uppe."""
    ut = []
    for k in range(0, 24 * 60, steg_min):
        lj = dagsljus(manad, dag, f"{k // 60}:{k % 60:02d}", vader_, plats)
        if lj.sol_hojd > -0.83:
            ut.append(lj)
    return ut


def tabell(ljus: list[Ljus]) -> str:
    rad = ["tid    azimut  höjd   sol klx     K  himmel klx     K  global klx   DNI   DHI   GHI"]
    for lj in ljus:
        t = datetime.fromisoformat(lj.tid)
        rad.append(f"{t:%H:%M} {lj.sol_azimut:7.1f} {lj.sol_hojd:5.1f} {lj.sol_lux / 1000:9.1f} {lj.sol_cct:5.0f} "
                   f"{lj.himmel_lux / 1000:11.1f} {lj.himmel_cct:5.0f} {lj.global_lux / 1000:11.1f} {lj.dni:5.0f} "
                   f"{lj.dhi:5.0f} {lj.ghi:5.0f}")
    return "\n".join(rad)


def soldiagram(plats: Plats, fil: str, fasader: dict[str, float] | None = None) -> None:
    """Solens bana den 21:a varje månad (azimut och höjd, timmarna markerade) och fasadernas riktningar (azimut för
    utåtnormalen)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for m in (12, 1, 2, 3, 4, 5, 6):
        bana = [solposition(datetime(2026, m, 21, tzinfo=ZoneInfo(plats.tidszon)) + timedelta(minutes=k), plats.lat,
                            plats.lon)[:2] for k in range(0, 1440, 5)]
        a, h = zip(*[(az, hh) for az, hh in bana if hh > -1])
        par = "" if m in (6, 12) else f" (och 21 {MANADER[11 - m]})"
        ax.plot(a, h, lw=1.2, label=f"21 {MANADER[m - 1]}{par}")
        for timme in range(24):
            az, hh, _ = solposition(datetime(2026, m, 21, timme, tzinfo=ZoneInfo(plats.tidszon)), plats.lat, plats.lon)
            if hh > 0:
                ax.plot(az, hh, "k.", ms=3)
                if m == 6:
                    ax.annotate(f"{timme}", (az, hh), textcoords="offset points", xytext=(0, 4), fontsize=7,
                                ha="center")
    for namn, az in (fasader or {}).items():
        ax.axvline(az % 360, color="0.6", lw=0.8, ls="--")
        ax.text(az % 360, 1, namn, rotation=90, fontsize=8, color="0.4", ha="right", va="bottom")
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 60)
    ax.set_xticks(range(0, 361, 45), ["N", "NO", "O", "SO", "S", "SV", "V", "NV", "N"])
    ax.set_xlabel("azimut (från geografiska norr)")
    ax.set_ylabel("solhöjd (°)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_title(f"Solens bana, {plats.lat:.3f}° N {plats.lon:.3f}° O (lokal tid, timmarna vid midsommar)")
    fig.tight_layout()
    fig.savefig(fil, dpi=150)
