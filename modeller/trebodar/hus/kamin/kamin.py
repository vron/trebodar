"""Kaminen (#145): Rais 600:2 (glas framtill och på en sida) i en murad, putsad och kalkad skorsten i allrummets hörn
mellan väggarna 2C och 2B, från golvet till innertaket, och en isolerad skorsten rakt upp genom taket.

Två lägen att jämföra (rum.KAMIN_LAGE, miljövariabeln TREBODAR_KAMIN):

- A (förvalt): baksidan mot 2C och den slutna sidan mot 2B. Fronten med det stora glaset är vänd mot rummet och
  matbordet (söderut, +y) och sidoglaset västerut längs 2C (−x): glaset på höger sida sett framifrån.
- B: baksidan mot 2B och den slutna sidan mot 2C. Fronten är vänd västerut längs 2C (−x) och sidoglaset mot rummet
  och matbordet (söderut, +y): glaset på vänster sida sett framifrån.

Måtten nedan är i skorstenens eget system: p från sidoväggens gips längs baksidans vägg och q från baksidans vägg ut i
rummet (rum.kamin_plan lägger dem i plan).

Insatsen (Rais 600:2, installationsmanualen): 699 × 610 × 402 (bredd, höjd, djup), frontram 705 × 627 (antagen som
för 600:3, 6 mm bredare än kroppen), rökstos Ø150 överst, 188 mm bakom fronten, underkanten 450 över golvet (golvet
till dörrens underkant minst 300). Den står på två stöd av kalciumsilikat, i liv med skorstenens front och med
glassidan i liv med skorstenens fria sida. Ramens kant står SIDA_FRI från sidoväggens gips (manualen: brännbart vid
dörrens sida minst 350); i läge B 410, så att skorstenen går fri från takbalken i y 6 550.

Skorstenen (rum.KAMINMUR): mot väggarnas gips (manualen: 0 mm till brännbar vägg bakom med skivorna nedan), 502 djup
(insatsen, 50 luft och 50 kalciumsilikat). Baksidan, väggsidan och fronten är 50 mm kalciumsilikat (Skamotec 225) och
den fria sidan under insatsen lättbetong 100, ovanför den kalciumsilikat 50. Utsidan är kalkputs 10 på nät, kalkad i
Jotun 1563 Mørk strandsand, ända upp till innertaket. Hålet för insatsen är 2 mm större än ramen runt om (minst
615 × 704 × 375), eftersom stålet utvidgar sig. Konvektionsöppningar i den fria sidan (inte i fronten): 255 cm² under
och 510 cm² över insatsen (minst 250 och 500), och 50 mm över den övre en obrännbar skiva av kalciumsilikat 50
(manualen); innertaket är minst 500 över öppningen och 1 000 över dörrens överkant. Golvet är betong
(mellanbjälklaget), så golvplåt behövs inte. Möbler minst 950 framför dörren och från sidoglaset.

Den isolerade skorstenen, Ø150/Ø250 rostfri (en CE-märkt systemskorsten med 50 mm deklarerat avstånd till brännbart,
G50), går ända ned till stosen (manualen) och rakt upp, utan böjar: genom skivan över konvektionsöppningen, inne i den
murade skorstenen, genom innertaket, isoleringen och taket mellan takbalkarna (minst 50 mm till trä) och upp till
800 mm över mittre huskroppens nock (manualen: minst 80 cm över nocken och minst 3 m från insatsens överkant). Den
kommer upp på takfallet 2NV nära dalen DB2 och blir därför hög över taket. I läge A står den i en fyrkantig
inklädnad av takets plåt, 560 × 560, med avtäckning och mynningen strax över den; i läge B står den för nära dalen
för inklädnaden (rändalen går 300 mm ut från dallinjen) och är rund med krage. Hålen genom innertaket, isoleringen och
taket skärs i hus.py.

Förbränningsluften utifrån (Rais AirSystem, Ø100 under insatsen) är inte dragen (#145).
"""
from __future__ import annotations

from shapely.geometry import box as plan_box

from modellering import Del, Form, Kapad, Material, Montage, Placering, box, cylinder

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.ror import ror
from trebodar.hus.invandigt.skikt import SKIVOR_T, innertak_vid, upp_till_taket
from trebodar.hus.rum import KAMIN_HORN, KAMIN_LAGE, KAMIN_MATT, kamin_plan
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT
from trebodar.material import GLAS, KALCIUMSILIKAT, KALKPUTS, KAMIN, LATTBETONG, ROSTFRITT, TAKPLAT

LAGE = KAMIN_LAGE
GLASSIDA = {"A": "höger", "B": "vänster"}[LAGE]           # sidoglaset sett framifrån
# insatsen (Rais 600:2, installationsmanualen)
KROPP = (699.0, 392.0, 610.0)               # bredd, djup bakom ramen, höjd
RAM = (705.0, 627.0, 10.0)                  # frontram: bredd, höjd, tjocklek (bredden antagen)
GLAS_H = 470.0                              # glasens höjd (antagen)
RAM_SLUTEN, RAM_HORN = 57.0, 30.0           # ramens bredd vid den slutna sidan och i glashörnet (antagna)
SIDOGLAS = (40.0, 290.0)                    # sidoglaset: från ramens baksida och längd bakåt (antaget)
STOS_D, STOS_FRAN_FRONT, STOS_H = 150.0, 188.0, 40.0
VAGG_T = 5.0                                # kroppens plåt
Z_INSATS = 450.0                            # kroppens underkant över golvet
SPEL = 2.0                                  # runt ramen i hålet
# skorstenen (i p och q)
BREDD, DJUP = KAMIN_MATT
SIDA_FRI = BREDD - RAM[0]                   # ramens kant från sidoväggens gips (Rais: brännbart vid dörrens sida 350)
PUTS, MUR, KS_T = 10.0, 100.0, 50.0         # kalkputs, lättbetong, kalciumsilikat
BAK = KS_T                                  # baksidan mot väggen: kalciumsilikat 50 (Rais: mot brännbar vägg)
LUFT_BAK = 50.0                             # luften mellan insatsen och baksidan (Rais: 50)
P_MITT = SIDA_FRI + RAM[0] / 2              # insatsens mitt
P_FRI, Q_FRONT = BREDD - PUTS, DJUP - PUTS  # den fria sidans och frontens utsida under putsen
# konvektionsöppningarna i den fria sidan (inte i fronten): längd längs sidan och höjd, under och över insatsen
KONV_UNDER, KONV_OVER = (300.0, 85.0), (300.0, 170.0)    # 255 och 510 cm² (minst 250 och 500)
Z_KONV_UNDER = 250.0
Q_KONV = 100.0                              # öppningarnas bakre kant från baksidans vägg
H_KASSE = 1900.0                            # skivan över den övre konvektionsöppningen, överkant
STOD_B = 60.0
STOD_IN = 60.0                              # stöden så långt in från sidorna: luften från den nedre öppningen
Z_SIDA = 1071.0                             # den fria sidans murverk upp hit (hålets överkant); ovanför kalciumsilikat
# den isolerade skorstenen
SKORSTEN_D, SKORSTEN_INRE = 250.0, 150.0
FRI = 50.0                                  # avstånd till brännbart vid genomföringen
OVER_NOCK = 800.0                           # mynningen över mittre huskroppens nock (Rais: minst 800)
RANDAL = 300.0                              # rändalen så långt ut från dallinjen (tak/dalar.py)
# inklädnaden över taket: fyrkantig, av takets plåt på en obrännbar stomme kring den runda skorstenen
KLADSEL = 560.0                             # yttermått
KLADSEL_FRI = 100.0                         # minst så långt från rändalen
KRONA_UT, KRONA_T = 25.0, 20.0              # avtäckningen: utsprång runt om och höjd
MYNNING_OVER = 100.0                        # rökkanalens mynning över avtäckningen


def _xy(p: float, q: float) -> tuple[float, float]:
    x, y, _, _ = kamin_plan(p, p, q, q)
    return x, y


def _lada(p0: float, p1: float, q0: float, q1: float, z0: float, z1: float) -> Form:
    x0, y0, x1, y1 = kamin_plan(p0, p1, q0, q1)
    return box(x0, x1, y0, y1, z0, z1)


def _upp(p0: float, p1: float, q0: float, q1: float, z0: float = 0.0) -> Form:
    """Lådan från z0 upp till innertaket."""
    return upp_till_taket(plan_box(*kamin_plan(p0, p1, q0, q1)), z0)


X_SK, Y_SK = _xy(P_MITT, DJUP - STOS_FRAN_FRONT)             # rökstosen och skorstenen rakt upp
DAL = S.BALKAR["DB2"]
MED_KLADSEL = X_SK + KLADSEL / 2 + KLADSEL_FRI <= DAL.x - RANDAL

assert abs(KAMIN_HORN[0] - (S.INNERVAGGAR["2B"].origo[0] - S.INNERVAGGAR["2B"].tjocklek - SKIVOR_T)) < 0.5, \
    "hörnet i 2B:s gips mot allrummet"
assert abs(KAMIN_HORN[1] - (S.INNERVAGGAR["2C"].origo[1] + S.INNERVAGGAR["2C"].tjocklek + SKIVOR_T)) < 0.5, \
    "hörnet i 2C:s gips mot allrummet"
assert SIDA_FRI >= 350.0, "Rais: brännbart vid dörrens sida minst 350"
assert abs(DJUP - (BAK + LUFT_BAK + KROPP[1] + RAM[2])) < 0.5, "skorstenen så grund som insatsen tillåter"
assert KAMIN_HORN[1] + (BREDD if LAGE == "B" else DJUP) < S.INNERVAGGAR["2B"].origo[1] + S.INNERVAGGAR["2B"].langd, \
    "skorstenen slutar före 2B:s ände"
_R = SKORSTEN_D / 2 + FRI
assert all(Y_SK + _R <= y or y + S.TAKBALK_B <= Y_SK - _R for y in FALT["2NV"].y), "50 mm från skorstenen till takbalkarna"
assert Y_SK - _R >= S.INNERVAGGAR["2C"].origo[1] + S.INNERVAGGAR["2C"].tjocklek, "50 mm till takstolen 2C"
assert S.HUSKROPPAR[2].nock + S.BALK_B / 2 <= X_SK - _R and X_SK + _R <= DAL.x - S.BALK_B / 2, \
    "50 mm till nockbalken NB3 och dalbalken DB2"


def _z_skikt(x: float, w: float) -> float:
    """Takets skikt w (vinkelrätt över takbalkarnas överkant) vid x i mittre huskroppen, på båda sidor om nocken."""
    t = S.TAKFALL["2SO"] if x <= S.HUSKROPPAR[2].nock else S.TAKFALL["2NV"]
    return t.z_overkant(x) + w / S.COS


def _z_tak(x: float) -> float:
    """Takplåtens överkant vid x."""
    return _z_skikt(x, L.PLAT[1])


def _z_mynning() -> float:
    """Rökkanalens mynning."""
    return _z_tak(S.HUSKROPPAR[2].nock) + OVER_NOCK


def _z_kladsel() -> float:
    """Inklädnadens överkant."""
    return _z_mynning() - MYNNING_OVER - KRONA_T


def skorstenens_lada() -> tuple[float, float, float, float]:
    """Det som står på taket i plan (inklädnaden, eller skorstenen med kragen): x0, y0, x1, y1."""
    r = KLADSEL / 2 if MED_KLADSEL else SKORSTEN_D / 2 + FRI
    return X_SK - r, Y_SK - r, X_SK + r, Y_SK + r


def _over_taket(x0: float, y0: float, x1: float, y1: float, z1: float, w: float) -> Form:
    """Lådan x0–x1, y0–y1 från takets skikt w upp till z1, på båda sidor om nocken."""
    nock = S.HUSKROPPAR[2].nock
    form: Form | None = None
    for xa, xb, tecken in ((x0, min(x1, nock), 1.0), (max(x0, nock), x1, -1.0)):
        if xb - xa < 0.01:
            continue
        xm = (xa + xb) / 2
        z0 = min(_z_skikt(xa, w), _z_skikt(xb, w)) - 5.0
        halva = Kapad(box(xa, xb, y0, y1, z0, z1), (xm, y0, _z_skikt(xm, w)), (tecken * S.TAN, 0.0, -1.0))
        form = halva if form is None else form | halva
    assert form is not None
    return form


Hal = tuple[Form, tuple[float, float, float, float, float, float], tuple[str, ...]]


def genomforingar() -> list[Hal]:
    """Hålen för skorstenen genom innertaket, isoleringen och taket (med avståndet FRI till brännbart) och, där
    inklädnaden står, i takplåten och falsarna (plåten viks upp mot den): verktyget, dess låda och montagen det skär
    (hus.py)."""
    r = SKORSTEN_D / 2 + FRI
    z0 = min(innertak_vid(X_SK + dx, Y_SK) for dx in (-r, r)) - 2.0
    z1 = _z_mynning() + 60.0
    ut: list[Hal] = [(cylinder(r, z1 - z0, (X_SK, Y_SK, z0)), (X_SK - r, Y_SK - r, z0, X_SK + r, Y_SK + r, z1),
                      ("Tak", "Isolering", "Invändigt"))]
    if MED_KLADSEL:
        x0, y0, x1, y1 = skorstenens_lada()
        zk = _z_kladsel()
        ut.append((_over_taket(x0, y0, x1, y1, zk, L.PLAT[0]),
                   (x0, y0, min(_z_skikt(x0, L.PLAT[0]), _z_skikt(x1, L.PLAT[0])) - 5.0, x1, y1, zk), ("Tak",)))
    return ut


def _halet() -> Form:
    """Hålet för insatsen genom fronten och den fria sidan."""
    zm = Z_INSATS + KROPP[2] / 2
    return _lada(SIDA_FRI - SPEL, BREDD + 1.0, DJUP - RAM[2] - KROPP[1] - SPEL, DJUP + 1.0, zm - RAM[1] / 2 - SPEL,
                 zm + RAM[1] / 2 + SPEL)


def _konvektion() -> tuple[Form, Form]:
    """Konvektionsöppningarna genom den fria sidan (murverket eller skivan, och putsen), under och över insatsen."""
    (bu, hu), (bo, ho) = KONV_UNDER, KONV_OVER
    zo = H_KASSE - KS_T - ho - 50.0
    return (_lada(P_FRI - MUR - 1.0, BREDD + 1.0, Q_KONV, Q_KONV + bu, Z_KONV_UNDER, Z_KONV_UNDER + hu),
            _lada(P_FRI - KS_T - 1.0, BREDD + 1.0, Q_KONV, Q_KONV + bo, zo, zo + ho))


def _skorstenen(m: Montage) -> None:
    """Murverket, skivorna av kalciumsilikat, putsen, skivan över konvektionsöppningen och stöden under insatsen."""
    hal = _halet()
    konv_u, konv_o = _konvektion()
    ix0, ix1 = KS_T, P_FRI - MUR                             # insidan mellan väggsidans skiva och den fria sidan
    iu1 = P_FRI - KS_T                                       # ovanför insatsen (tunnare fri sida)
    qk = Q_FRONT - KS_T                                      # frontens insida
    delar: list[tuple[str, str, Form, Material]] = [
        ("MUR-F", "Murverk lättbetong 100, den fria sidan", _lada(ix1, P_FRI, 0.0, Q_FRONT, 0.0, Z_SIDA) - hal - konv_u,
         LATTBETONG),
        ("SIDA-F", f"Sida kalciumsilikat {KS_T:g} ovanför insatsen, den fria sidan",
         _upp(iu1, P_FRI, 0.0, Q_FRONT, Z_SIDA) - konv_o, KALCIUMSILIKAT),
        ("SIDA-V", f"Sida kalciumsilikat {KS_T:g} mot sidoväggen", _upp(0.0, ix0, 0.0, Q_FRONT), KALCIUMSILIKAT),
        ("BAK", f"Baksida kalciumsilikat {BAK:g}", _lada(ix0, ix1, 0.0, BAK, 0.0, Z_SIDA)
         | _upp(ix0, iu1, 0.0, BAK, Z_SIDA), KALCIUMSILIKAT),
        ("FRONT", f"Front kalciumsilikat {KS_T:g}", (_lada(ix0, ix1, qk, Q_FRONT, 0.0, Z_SIDA)
                                                      | _upp(ix0, iu1, qk, Q_FRONT, Z_SIDA)) - hal, KALCIUMSILIKAT),
        ("PUTS", f"Kalkputs {PUTS:g} på nät, kalkad", (_upp(0.0, BREDD, Q_FRONT, DJUP) | _upp(P_FRI, BREDD, 0.0, Q_FRONT))
         - hal - konv_u - konv_o, KALKPUTS),
    ]
    for kod, namn, form, mat in delar:
        artikel = "Skamotec 225, 50 mm" if mat is KALCIUMSILIKAT else None
        m.lagg(Del(namn, form, mat, artikel=artikel), Placering(), f"KM-{kod}")
    # skivan över den övre konvektionsöppningen, med hål för skorstenen
    skiva = _lada(ix0, iu1, BAK, qk, H_KASSE - KS_T, H_KASSE) \
        - cylinder(SKORSTEN_D / 2 + 10.0, KS_T + 2.0, (X_SK, Y_SK, H_KASSE - KS_T - 1.0))
    m.lagg(Del(f"Skiva över konvektionsöppningen, kalciumsilikat {KS_T:g}", skiva, KALCIUMSILIKAT,
               artikel="Skamotec 225, 50 mm"), Placering(), "KM-PLAT")
    q0 = DJUP - RAM[2] - KROPP[1]
    for i, p0 in enumerate((SIDA_FRI + STOD_IN, ix1 - STOD_IN - STOD_B), 1):
        m.lagg(Del(f"Stöd under insatsen, kalciumsilikat {STOD_B:g}", _lada(p0, p0 + STOD_B, q0, qk, 0.0, Z_INSATS),
                   KALCIUMSILIKAT), Placering(), f"KM-STOD{i}")


def _insatsen(m: Montage) -> None:
    b, d, h = KROPP
    p0, p1 = P_MITT - b / 2, P_MITT + b / 2
    q1 = DJUP - RAM[2]
    q0, z0 = q1 - d, Z_INSATS
    zm = z0 + h / 2
    ga, gb = zm - GLAS_H / 2, zm + GLAS_H / 2
    fran, langd = SIDOGLAS
    sidoglas = _lada(p1 - VAGG_T, p1, q1 - fran - langd, q1 - fran, ga, gb)
    kropp: Form = (_lada(p0, p1, q0, q1, z0, z0 + h)
                   - _lada(p0 + VAGG_T, p1 - VAGG_T, q0 + VAGG_T, q1 + 1.0, z0 + VAGG_T, z0 + h - VAGG_T) - sidoglas)
    namn = f"Rais 600:2 (glas framtill och på {GLASSIDA} sida)"
    m.lagg(Del("Kamininsats Rais 600:2, kropp", kropp, KAMIN, artikel=namn, produkt="KAMIN"), Placering(), "KM-INSATS")
    rb, rh, _ = RAM
    g0, g1 = SIDA_FRI + RAM_SLUTEN, BREDD - RAM_HORN
    ram = _lada(SIDA_FRI, BREDD, q1, DJUP, zm - rh / 2, zm + rh / 2) - _lada(g0, g1, q1 - 1.0, DJUP + 1.0, ga, gb)
    m.lagg(Del("Frontram Rais 600:2", ram, KAMIN), Placering(), "KM-RAM")
    m.lagg(Del("Glas Rais 600:2, framtill", _lada(g0, g1, DJUP - 4.0, DJUP, ga, gb), GLAS), Placering(), "KM-GLAS")
    m.lagg(Del("Glas Rais 600:2, sidan", sidoglas, GLAS), Placering(), "KM-GLAS-SIDA")


def montage() -> Montage:
    m = Montage("Kamin", beskrivning=f"Rais 600:2 i en murad, putsad och kalkad skorsten i allrummets hörn mellan 2C "
                                     f"och 2B, från golvet till innertaket, med isolerad skorsten rakt upp genom "
                                     f"taket (läge {LAGE}, #145)")
    _insatsen(m)
    _skorstenen(m)
    # rökstosen och den isolerade skorstenen från stosen
    zt = Z_INSATS + KROPP[2]
    m.lagg(Del(f"Rökstos Ø{STOS_D:g}", ror((X_SK, Y_SK, zt), (X_SK, Y_SK, zt + STOS_H), STOS_D, 3.0), KAMIN),
           Placering(), "KM-STOS")
    z_topp = _z_mynning()
    langd = z_topp - zt - STOS_H
    m.lagg(Del(f"Isolerad skorsten Ø{SKORSTEN_INRE:g}/Ø{SKORSTEN_D:g} L={langd:.0f}",
               ror((X_SK, Y_SK, zt + STOS_H), (X_SK, Y_SK, z_topp), SKORSTEN_D, (SKORSTEN_D - SKORSTEN_INRE) / 2),
               ROSTFRITT, produkt="SKORSTEN"), Placering(), "KM-SKORSTEN")
    m.lagg(Del("Regnhuv", cylinder(SKORSTEN_D / 2 + FRI, 40.0, (X_SK, Y_SK, z_topp)), ROSTFRITT), Placering(), "KM-HUV")
    r = SKORSTEN_D / 2 + FRI
    za, zb = min(_z_tak(X_SK - r), _z_tak(X_SK + r)) - 80.0, max(_z_tak(X_SK - r), _z_tak(X_SK + r)) + 100.0
    k = (_z_tak(X_SK + 100.0) - _z_tak(X_SK)) / 100.0                   # takets lutning
    krage = Kapad(ror((X_SK, Y_SK, za), (X_SK, Y_SK, zb), 2 * r, FRI), (X_SK, Y_SK, _z_tak(X_SK) - 40.0), (k, 0.0, -1.0))
    m.lagg(Del("Takgenomföring, krage", krage, ROSTFRITT), Placering(), "KM-KRAGE")      # från 40 under takets yta
    if MED_KLADSEL:
        # inklädnaden över taket: plåt på obrännbar stomme, från underlagspappen (plåten viks upp mot den) till
        # avtäckningen
        x0, y0, x1, y1 = skorstenens_lada()
        zk = _z_kladsel()
        t_pl = L.PLAT_T
        skal = (_over_taket(x0, y0, x1, y1, zk, L.PLAT[0])
                - _over_taket(x0 + t_pl, y0 + t_pl, x1 - t_pl, y1 - t_pl, zk + 1.0, L.PLAT[0] - 50.0))
        m.lagg(Del(f"Skorstenens inklädnad {KLADSEL:g}×{KLADSEL:g}, bandplåt som taket på obrännbar stomme", skal,
                   TAKPLAT, produkt="SKORSTEN"), Placering(), "KM-KLADSEL")
        krona = (box(x0 - KRONA_UT, x1 + KRONA_UT, y0 - KRONA_UT, y1 + KRONA_UT, zk, zk + KRONA_T)
                 - cylinder(SKORSTEN_D / 2, KRONA_T + 2.0, (X_SK, Y_SK, zk - 1.0)))
        m.lagg(Del("Skorstenens avtäckning, plåt med fall utåt", krona, TAKPLAT), Placering(), "KM-KRONA")
    return m
