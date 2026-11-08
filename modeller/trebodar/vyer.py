"""Vyer för rendering (Blender) och webbvisaren: kamera och mål i husets koordinater (mm), objektiv och dagsljus.

Dagsljuset anges som (månad, dag, klocka, väder) och räknas fram för platsen (skelett.PLATS) med
modellering/dagsljus.py: solens riktning, färg och styrka och himlen. Väder: "sol", "halvklart", "lätt mulet",
"mulet".

Inomhusbilderna (INNE) har standardiserade namn I01–I30, <nummer>-<rum>-<vy>-<objektiv>, och två objektiv: "öga"
(40 mm, i ögonhöjd 1,60 m: bildvinkeln och perspektivet som när man står i rummet) och "vid" (20 mm på 1,45 m, som
vanliga vidvinkelbilder av rum). Kameran hålls vågrät, så att lodräta linjer blir lodräta (objektivförskjutning i
höjdled i stället för att luta kameran). Ritningen över kamerornas lägen: `./mod kameraplan` (renderingar/).
`dolj`: delar av sökvägar som inte visas.
"""
from __future__ import annotations

import math
import tomllib
from pathlib import Path

from trebodar import skelett as S
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT

ROT = Path(__file__).resolve().parents[2]
OBJEKTIV = {"öga": {"lins": 40.0, "hojd": 1600.0}, "vid": {"lins": 20.0, "hojd": 1450.0}}
# källarens tändgrupper (hus/installationer/el/rum/kallare.py), tända i bilderna av källaren: källaren är mörk med
# sina små fönster
KALLAREN = {f"KA-T{i}": 1.0 for i in range(1, 9)}
INNE_LJUS = (4, 20, "14:00", "sol")       # standardljuset för inomhusbilderna: april, eftermiddag, sol från SSV
# ljusserierna (webbplatsens växel i bildvisaren): A är varje vys eget ljus, de andra samma tid och väder för alla
# vyer, ute och inne (rendera.sh --ljusserie B, bilderna i renderingar/B/); "tand": "alla" tänder hela
# elinstallationen; "utan" är vyerna (eller början av namnen) som inte renderas i serien
LJUSSERIER = {
    "A": {"namn": "Bildens eget ljus"},
    "B": {"namn": "April, kväll, mest sol", "ljus": (4, 28, "18:30", "halvklart")},
    "C": {"namn": "Oktober, förmiddag, mulet", "ljus": (10, 6, "10:00", "mulet")},
    # D på julafton kl. 22 med fullmånen 43° upp i östsydost, som lyser upp landskapet; utan närbilderna av fasaderna
    # och taket, som är svarta i mörker, och stommen, som är byggskedet
    "D": {"namn": "December, kväll, klar himmel", "ljus": (12, 24, "22:00", "klart"), "tand": "alla",
          "utan": ("detalj-falu", "detalj-fasad", "detalj-takflakt", "detalj-sten", "detalj-tak", "detalj-takhuv",
                   "stomme")},
}
Z_KALLARE = S.Z_BOTTENPLATTA

VYER = {
    "ute-sydost": {"kamera": [-9000, -9000, 6500], "mal": [6500, 6500, 1500], "lins": 30, "ljus": (6, 21, "09:00", "sol"),
                   "lodrat": False},
    "ute-nordvast": {"kamera": [23000, 21000, 7000], "mal": [7000, 6500, 1000], "lins": 30,
                     "ljus": (6, 21, "18:30", "sol"), "lodrat": False},
    "ute-nordost": {"kamera": [4000, -14000, 3500], "mal": [7000, 5000, 1500], "lins": 32,
                    "ljus": (6, 21, "06:30", "sol"), "lodrat": False},
    # från havets sida (sydväst och väster, ögonhöjden omkring fasadens mitt, kvällssol): som när man kommer över
    # berget från havet
    "ute-sydvast": {"kamera": [-12000, 34000, 3600], "mal": [7000, 8000, 2300], "lins": 40,
                    "ljus": (6, 21, "19:00", "sol"), "lodrat": False},
    "ute-vast": {"kamera": [26000, 34000, 1800], "mal": [7000, 8000, 2000], "lins": 40, "ljus": (6, 21, "19:00", "sol"),
                 "lodrat": False},
    # flygbilderna rakt ovanifrån med verklig norr uppåt (som flygfoton; norr i modellen är (0,751, −0,660) enligt
    # passningen mot SWEREF, sweref_passning), för att se och kommentera var saker står: tomten (omkring 150 × 85 m)
    # och omgivningen (400 × 225 m); tomten i mulet väder, så att trädens skuggor på gräsmattan inte ser ut som träd
    "flyg-tomten": {"kamera": [2500, 6800, 125000], "mal": [3251, 6140, 0], "lins": 30,
                    "ljus": (6, 21, "12:00", "mulet"), "lodrat": False},
    "flyg-omgivningen": {"kamera": [2500, 6800, 330000], "mal": [3251, 6140, 0], "lins": 30,
                         "ljus": (6, 21, "12:00", "sol"), "lodrat": False},
    "detalj-fasad": {"kamera": [6500, -4200, 1700], "mal": [8200, 0, 1500], "lins": 40, "ljus": (9, 15, "12:00", "mulet")},
    "detalj-falu": {"kamera": [-3600, 5600, 1500], "mal": [-95, 6600, 1300], "lins": 40,
                    "ljus": (9, 15, "12:00", "mulet")},
    "detalj-sten": {"kamera": [11800, -2600, -600], "mal": [12600, 900, -1100], "lins": 40,
                    "ljus": (6, 21, "09:00", "sol")},
    "detalj-tak": {"kamera": [-6000, 2500, 3200], "mal": [1500, 9500, 3000], "lins": 45, "ljus": (6, 21, "10:00", "sol"),
                   "lodrat": False},
    "detalj-spot": {"kamera": [6600, 7900, 1500], "mal": [5873, 8650, 3174], "lins": 50, "ljus": (12, 21, "18:00", "sol"),
                    "lodrat": False, "inne": True, "tand": {"AL-T1": 1.0, "AL-T2": 1.0}},
    "detalj-tubspot": {"kamera": [12350, 8750, 2350], "mal": [12725, 9600, 2850], "lins": 50,
                       "ljus": (12, 21, "18:00", "sol"), "lodrat": False, "inne": True, "tand": {"KO-T1": 1.0}},
    # pendlarna (hus/installationer/el): PH 5 över bordet, Stav över köksön, VL45 i vardagsrummet och globen i sovrummet
    "detalj-ph5": {"kamera": [5300, 6900, 1500], "mal": [6905, 8975, 1500], "lins": 35, "ljus": (12, 21, "18:00", "sol"),
                   "lodrat": False, "inne": True, "tand": {"AL-T3": 1.0, "AL-T1": 0.3, "AL-T2": 0.3}},
    "detalj-stav": {"kamera": [9500, 7800, 1500], "mal": [11385, 9140, 950], "lins": 20, "ljus": (12, 21, "18:00", "sol"),
                    "lodrat": False, "inne": True, "tand": {"KO-T3": 1.0, "KO-T1": 0.3}},
    "detalj-vl45": {"kamera": [3300, 11600, 1450], "mal": [1850, 13470, 2000], "lins": 30,
                    "ljus": (12, 21, "18:00", "sol"), "lodrat": False, "inne": True, "tand": {"VR-T3": 1.0}},
    "detalj-glob": {"kamera": [5300, 4900, 1550], "mal": [7055, 3425, 2200], "lins": 35, "ljus": (12, 21, "18:00", "sol"),
                    "lodrat": False, "inne": True, "tand": {"SV-T1": 1.0}},
    # ventilationen (hus/installationer/ventilation): källarrummets kanal och fläkt under källarens tak, kanalen upp
    # i väggen 1C (skikten dolda), takhuven och köksfläktens galler
    "detalj-kallarkanal": {"kamera": [1500, 9000, Z_KALLARE + 1400], "mal": [3700, 8220, -330], "lins": 24,
                           "ljus": (12, 21, "18:00", "sol"), "lodrat": False, "inne": True, "tand": KALLAREN},
    "detalj-1c": {"kamera": [2600, 9700, 1300], "mal": [2810, 8220, 1700], "lins": 24, "ljus": (9, 15, "12:00", "mulet"),
                  "lodrat": False, "inne": True, "dolj": ["Hus/Invändigt/Innerväggar/Innerväggarnas skikt/Skikt 1C"]},
    # köket (ärende #21): bänken längs 3NV med lådskåpen, hällen och diskhon, och ön
    "detalj-koket": {"kamera": [10700, 11900, 1550], "mal": [13300, 8700, 950], "lins": 22,
                   "ljus": (9, 15, "12:00", "mulet"), "inne": True},
    # kökets inbyggnad (ärende #20): kyl, frys och skafferi bakom en vägg till innertaket, luckan till förrådet ovanför
    "detalj-inbyggnad": {"kamera": [10150, 9900, 1550], "mal": [12000, 7300, 1650], "lins": 20,
                         "ljus": (9, 15, "12:00", "mulet"), "inne": True},
    "detalj-takhuv": {"kamera": [7800, 9800, 6600], "mal": [2810, 8220, 3700], "lins": 50,
                      "ljus": (6, 21, "10:00", "sol"), "lodrat": False},
    "detalj-takflakt": {"kamera": [17800, 7200, 5200], "mal": [13555, 9664, 3050], "lins": 50,
                        "ljus": (9, 15, "12:00", "mulet")},
    # tappvattnet (hus/installationer/vatten): fördelarskåpet på V19 med rören upp till källarens tak, värmepumpen och
    # matarledningarna i teknikrummet
    "detalj-teknikrum": {"kamera": [2250, 8050, Z_KALLARE + 1350], "mal": [4300, 8450, -750], "lins": 20,
                         "ljus": (12, 21, "18:00", "sol"), "lodrat": False, "inne": True, "tand": KALLAREN},
    "stomme": {"kamera": [-8000, -9000, 9000], "mal": [6500, 6500, 1800], "lins": 30, "ljus": (6, 21, "10:00", "sol"),
               "lodrat": False, "dolj": ["Hus/Tak/", "Hus/Fasad", "Hus/Isolering", "Hus/Invändigt",
                                         "Fönster och dörrar", "Installationer", "Mark/Sovrumsavsats", "Mark/Entréavsats",
                                         "Mark/Bänktrappa"]},
}

# vyernas bildtexter på webbplatsen (inomhusbilderna får sin ur rummet och vyn); TEKNIK: bilderna av stommen och
# installationerna, en egen grupp på startsidan
TEXTER = {
    "ute-sydost": "Huset från sydost", "ute-nordvast": "Huset från nordväst", "ute-nordost": "Huset från nordost",
    "ute-sydvast": "Huset från sydväst", "ute-vast": "Huset från väster",
    "flyg-tomten": "Tomten uppifrån, norr uppåt", "flyg-omgivningen": "Omgivningen uppifrån, norr uppåt",
    "detalj-fasad": "Fasaden i järnvitriol", "detalj-falu": "Fasaden i falu rödfärg",
    "detalj-sten": "Sockeln av granit", "detalj-tak": "Taket, bandtäckt plåt med takfönster",
    "detalj-spot": "Spotlights i allrummets tak",
    "detalj-tubspot": "Spotlights i köket", "detalj-ph5": "PH 5 över matbordet", "detalj-stav": "Pendlarna över köksön",
    "detalj-vl45": "VL45 i vardagsrummet", "detalj-glob": "Glob i sovrummet",
    "detalj-kallarkanal": "Ventilationen i källaren", "detalj-1c": "Ventilationskanalen i väggen 1C",
    "detalj-takhuv": "Takhuven", "detalj-takflakt": "Köksfläktens takfläkt",
    "detalj-teknikrum": "Teknikrummet", "stomme": "Stommen",
    "detalj-inbyggnad": "Kyl, frys och skafferi i köket, förråd ovanför",
    "detalj-koket": "Köket: lådor av fräst ask och bänkskiva av granitkeramik",
}
TEKNIK = {"stomme", "detalj-spot", "detalj-tubspot", "detalj-kallarkanal", "detalj-1c", "detalj-takhuv",
          "detalj-takflakt", "detalj-teknikrum"}

# Inomhusbilderna: (nummer, rum, vy, objektiv, kamerans läge (x, y) [, golvets z], målet (x, y, z))
_INNE = [
    ("I01", "allrum", "mot-kok", "vid", (5100, 10450), (11500, 8300, 1300)),
    ("I02", "allrum", "mot-kamin", "vid", (6900, 10500), (6900, 5900, 1350)),
    ("I03", "allrum", "mot-tradgard", "vid", (6000, 6450), (6900, 11040, 1100)),
    ("I04", "allrum", "matplats", "öga", (9900, 9600), (5000, 8800, 1200)),
    ("I05", "allrum", "mot-hall", "vid", (8800, 7200), (1500, 10200, 1300)),
    ("I06", "kok", "oversikt", "vid", (8300, 9900), (13000, 9300, 1200)),
    ("I07", "kok", "mot-allrum", "vid", (12750, 7800), (7500, 10600, 1300)),     # framför kökets inbyggnad
    ("I08", "kok", "mot-fonster", "öga", (11400, 10100), (13675, 9400, 1300)),
    ("I09", "kok", "mot-uteplats", "öga", (12600, 7900), (10900, 12445, 1100)),
    ("I10", "vardagsrum", "fran-hall", "vid", (2600, 11450), (2155, 15800, 1150)),
    ("I11", "vardagsrum", "mot-hall", "vid", (2000, 15350), (2600, 9800, 1350)),
    ("I12", "vardagsrum", "mot-altandorr", "öga", (700, 13700), (4245, 14575, 1150)),
    ("I13", "vardagsrum", "mot-golvfonster", "öga", (3700, 12300), (1900, 15835, 1100)),
    ("I14", "hall", "fran-entre", "vid", (650, 10250), (6500, 9000, 1350)),
    ("I15", "hall", "mot-entre", "vid", (3700, 9800), (-30, 10255, 1150)),
    ("I16", "badrum", "fran-dorr", "vid", (2350, 6950), (1100, 3800, 1100)),    # innanför dörren, förbi L19
    ("I17", "badrum", "mot-dorr", "vid", (450, 3950), (2900, 7300, 1300)),
    ("I18", "sovrum", "fran-dorr", "vid", (4150, 5650), (8600, 3000, 1300)),
    ("I19", "sovrum", "mot-fonster", "öga", (6100, 4800), (6300, 135, 1500)),       # framför garderoben
    ("I20", "sovrum", "mot-golvfonster", "vid", (6700, 4800), (3270, 3800, 1000)),
    ("I21", "kontor", "oversikt", "vid", (9050, 1100), (4700, 1900, 1300)),
    ("I22", "kontor", "mot-altandorr", "öga", (7200, 1300), (4565, 2520, 1150)),
    ("I23", "sovrum-litet", "fran-dorr", "vid", (10450, 2700), (13200, 1500, 1200)),
    ("I24", "kontor-litet", "fran-dorr", "vid", (11250, 3300), (13675, 3725, 1300)),
    ("I25", "gastrum", "fran-dorr", "vid", (11250, 5180), (13675, 5500, 1300)),
    ("I26", "gang", "mot-kok", "öga", (10300, 3250), (10300, 9500, 1300)),
    ("I27", "gang", "mot-sovrum", "öga", (10300, 6900), (10300, 2905, 1300)),
    ("I28", "trappa", "ned", "öga", (9360, 5470), (7700, 5470, -1500)),
    ("I29", "kallare", "oversikt", "vid", (12800, 11500, Z_KALLARE), (7000, 3500, Z_KALLARE + 1200)),
    ("I30", "kallare", "mot-trappan", "vid", (5000, 6300, Z_KALLARE), (8600, 5470, Z_KALLARE + 900)),
]

# inomhusbilder med egna inställningar: trappan ned med lutande kamera (lodräta linjer konvergerar), källarens
# belysning tänd
_INNE_EXTRA: dict[str, dict[str, object]] = {"I28": {"lodrat": False, "tand": KALLAREN},
                                             "I29": {"tand": KALLAREN}, "I30": {"tand": KALLAREN}}


def _inne() -> dict[str, dict[str, object]]:
    ut: dict[str, dict[str, object]] = {}
    for nr, rum, vy, obj, kam, mal in _INNE:
        o = OBJEKTIV[obj]
        z0 = kam[2] if len(kam) > 2 else 0.0
        ut[f"{nr}-{rum}-{vy}-{obj}"] = {"kamera": [kam[0], kam[1], z0 + o["hojd"]], "mal": list(mal), "lins": o["lins"],
                                        "ljus": INNE_LJUS, "inne": True, "rum": rum, "objektiv": obj,
                                        **_INNE_EXTRA.get(nr, {})}
    return ut


INNE = _inne()

# rummens namn i kameraplanen (`./mod kameraplan`): namnet och läget (x, y), plan 1 eller källaren (k)
RUMSNAMN = {
    "allrum": ("Allrum", (6900, 8700)), "kok": ("Kök", (12000, 10400)), "vardagsrum": ("Vardagsrum", (2200, 13400)),
    "hall": ("Hall", (1100, 9300)), "badrum": ("Badrum", (1250, 5500)), "sovrum": ("Sovrum", (5900, 4300)),
    "kontor": ("Kontor", (6300, 1100)), "sovrum-litet": ("Sovrum, litet", (12300, 1850)),
    "kontor-litet": ("Kontor, litet", (12400, 3750)), "gastrum": ("Gästrum", (12400, 5650)),
    "gang": ("Gång", (10250, 4600)), "trappa": ("Trappa", (8350, 5470)), "kallare": ("Källare", (7000, 7800, "k")),
}
# fler rum för ljusplanernas statistik (som RUMSNAMN; ljusplanerna delar en öppen planlösning mellan namnen efter
# närmaste namn, så namnen står så att gränserna hamnar vid väggarna): källarens rum, med samma namn som golvvärmens
# zoner; tvättstugan (hallen och rummet vid V3 väster om KL8) och teknikrummet är en öppen yta, liksom trapphallen och
# rummen söder om V4–V6 (källarrummet i RUMSNAMN)
LJUSPLANENS_RUM = {
    "kallare-hall": ("Tvättstugan, hallen", (3000, 6550, "k")),
    "kallare-tvatt": ("Tvättstugan vid V3", (1150, 8350, "k")), "kallare-teknik": ("Teknikrum", (3000, 8750, "k")),
    "kallare-ksv": ("Rum norr om hallen", (1500, 4800, "k")), "kallare-ksm": ("Rum öster om KL2", (3650, 4800, "k")),
    "kallare-trapphall": ("Trapphall", (7000, 6400, "k")), "kallare": ("Rummen söder om V4–V6", (7000, 8630, "k")),
    "kallare-ks": ("Rum norr om trapphallen", (6800, 2700, "k")), "kallare-ko": ("Stora rummet", (11600, 7000, "k")),
}


# marken runt modellens terräng (renderingen): från terrängens kant till omgivningens höjder (geodata, annars z_bas)
OMGIVNING = {"mitt": [7000.0, 8000.0], "z_bas": -1600.0, "terrang": "Mark/"}
# omgivningen ur öppna geodata (`./mod omgivning --hamta`): radien och cellen (m), mappen (versionshanteras inte)
# och tillgångarna (Poly Havens texturer och modeller, CC0, `./mod omgivning --hamta`)
GEODATA = {
    "mapp": "lokalt/omgivning", "radie": 2300.0, "cell": 5.0, "tillgangar": "lokalt/polyhaven",
    # det som saknas i OpenStreetMap eller inte stämmer (ärende #26, efter flygfoton och inmätningen), i modellens mm:
    # byggnader (hörnen, höjden [m], valfritt platt tak och färger), skog (täta träd i olika höjd), inmätta träd som
    # inte finns och tallar som saknas
    "byggnader": [
        # grannhuset i norr (nybygge): väggen mot tomten inmätt (punkterna hus vid x 21,4–21,9), djupet ur flygfotot;
        # mycket mörkgrått med svartmålat plåttak (ärende #79)
        {"horn": [(21600, -12800), (29000, -12800), (29000, 6200), (21600, 6200)], "hojd": 6.5,
         "farg": "#2b2c2e", "takfarg": "#151617"},
        # grannhuset i sydost (flygfotot): två delar med platta tak
        {"horn": [(-35300, 11950), (-46600, 5400), (-50100, 11900), (-38700, 18400)], "hojd": 6.0, "tak": "platt",
         "farg": "#e8e4da", "takfarg": "#3a3c3e"},
        {"horn": [(-36700, 20100), (-45600, 14800), (-48400, 20200), (-39400, 25300)], "hojd": 3.5, "tak": "platt",
         "farg": "#e8e4da", "takfarg": "#3a3c3e"},
    ],
    "skog": [
        # mellan tomten och stranden i västsydväst
        [(29900, 49000), (23900, 56500), (22600, 72200), (26500, 91900), (34500, 110400), (44500, 122600),
         (53700, 125400), (59800, 117900), (61000, 102200), (57100, 82400), (49100, 64000), (39200, 51700)],
        # söder om tomten
        [(-10900, 35400), (-19600, 29100), (-29600, 27600), (-38300, 31500), (-43200, 39500), (-43000, 49600),
         (-37900, 59100), (-29200, 65400), (-19200, 66800), (-10500, 63000), (-5600, 55000), (-5800, 44800)],
    ],
    # bädden framför altanen (ärende #77): i verkligheten 50–70 cm hög, med låg växtlighet och de inmätta stenarna:
    # hörnen, höjden över marken runt [m] och släntens bredd [m]; buskar bredvid den
    "baddar": [{"horn": [(11980, 18050), (9980, 18530), (9590, 20300), (12770, 22330), (15060, 22280),
                         (15300, 20180), (13620, 18670)], "hojd": 0.6, "slant": 0.9}],
    "buskar": [(8900, 20500), (9400, 18200), (12500, 23050), (15500, 22800), (16000, 20000)],
    # öster om huset; de två väster om huset, vid gaveln mot grannhuset i norr
    "utan_trad": [(800, -6500), (2400, -300), (16950, 12950), (20260, 11680)],
    # öster om huset bortom de inmätta tallarna, i sydost och i sydväst
    "nya_trad": [(-20660, -13170), (-14940, 9820), (-17060, 5580), (-21900, 6290), (-19980, 11040),
                 (4670, 40540), (320, 38890), (170, 43840), (-3440, 41550)],
}


def sweref_passning() -> tuple[object, float]:
    """Modellens koordinater ↔ SWEREF 99 12 00 ur fasadens hörn F1–F12 (AR-02:s utsättningsdata): mellanbjälklagets
    kontur 95 mm utanför (regel 30 och beklädnad 65), med början i hörnet x = 13 905, y = 905 och sedan medurs."""
    from shapely.geometry import Polygon
    from shapely.geometry.polygon import orient

    from modellering.geodata import passa
    ar02 = tomllib.loads((ROT / "beräkningar" / "AR-02" / "indata.toml").read_text(encoding="utf-8"))
    c = list(orient(Polygon(S.KONTUR).buffer(95.0, join_style=2), -1).exterior.coords)[:-1]
    i = min(range(len(c)), key=lambda k: math.dist(c[k], (2e4, 0.0)))
    return passa(c[i:] + c[:i], [tuple(p) for p in ar02["koordinater"]["hornen"]])

# delar som inte tas med i webbvisaren (stora nät) och i renderingen (osynliga, i betongen)
WEBB_UTOM = ["Golvvärme"]
RENDER_UTOM = ["Golvvärme", "Hus/Armering"]

PORTAL_INNE = 200.0        # portalen i fönstret så långt in från stommens utsida (i rummet, framför insidans skikt)


def portaler() -> list[dict[str, object]]:
    """Ljusportaler i fönster, glasdörrar och takfönster (Cycles samplar himlen genom dem): rektangeln i öppningen,
    normalen in i huset (mm)."""
    ut: list[dict[str, object]] = []
    for kod, lst in OPPNINGAR.items():
        v = S.VAGGAR[kod]
        for o in lst:
            if o.typ == "ytterdörr":
                continue
            w = PORTAL_INNE if o.z1 > 0 else K.CELL + K.KARNA + 100.0     # källarens fönster: genom källarväggen
            um = (o.u0 + o.u1) / 2
            ut.append({"namn": o.kod, "mitt": [v.origo[0] + v.u[0] * um + v.w[0] * w,
                                               v.origo[1] + v.u[1] * um + v.w[1] * w, (o.z0 + o.z1) / 2],
                       "normal": [v.w[0], v.w[1], 0.0], "upp": [0.0, 0.0, 1.0], "bredd": o.u1 - o.u0,
                       "hojd": o.z1 - o.z0})
    for f in FALT.values():
        t = S.TAKFALL[f.kod]
        for fo in f.fonster:
            xm = (fo.x_ned + fo.x_upp) / 2
            s, c = math.sin(math.radians(S.TAKVINKEL)), math.cos(math.radians(S.TAKVINKEL))
            ut.append({"namn": fo.kod, "mitt": [xm, (fo.y0 + fo.y1) / 2, t.z_underkant(xm) - 150.0],
                       "normal": [t.riktning * s, 0.0, -c], "upp": [t.riktning * c, 0.0, s], "bredd": fo.y1 - fo.y0,
                       "hojd": (fo.x_upp - fo.x_ned) / c})
    return ut
