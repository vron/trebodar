"""Badrummets inredning (ärende #52) på lägena i hus/badrum.py.

- **Badrumsbänken** längs 1NO: fyra lika breda dörrar av fräst ask 22 med det linsformade greppet på tre skåp med
  stomme av björkplywood 20 som köksskåpen (koksskap.py), en, två och en dörr, på en sparklist av ask som följer
  golvets fall; bänkskivan Bricmate Jura 12 som i köket, med tvättstället av porslin undermonterat mitt under fönstret
  1NO-F1 och blandaren bakom det. Skåpen står på golvets högsta punkt under bänken. Tvättstället står i det mittre
  skåpet, som har reglar fram och bak i stället för tak; vattenlåset och rören står i det (tappvattnet och avloppet).
- **Badkaret** fristående och ovalt av mineralkomposit, förenklat som en avsmalnande ellips med karet urtaget, och en
  golvstående blandare med handdusch vid änden mot 1A.
- **WC:n** golvstående med S-lås, förenklad: fot och skål, sits och lock och cistern, med baksidan mot L9.
- **Duschen**: två glasdörrar 8 mm i nischens öppning, hängda i väggprofiler på 1B och L11 och utåtgående, och på 1C
  en termostatblandare med stång, takdusch och handdusch.
- **Skåpet** i nischen mellan L10 och L19: stomme av björkplywood med hyllor och två höga dörrar av fräst ask i L9:s
  yta; ovanför skåpet är nischen öppen upp till innertaket.
- **Spegeln** på 1NO till höger om fönstret och **handdukstorken** (elektrisk) på 1A.

Delarna heter BA- och sedan BANK (skåpen BANK1–BANK3 med -SIDA-V osv. som köksskåpen, -DORR1 och -DORR2),
BANK-SKIVA, BANK-SPARK, TVATTSTALL, TVATTSTALL-BLANDARE, BADKAR, BADKAR-BLANDARE, WC- (FOT, SITS, LOCK, CISTERN),
DUSCH- (DORR-V, DORR-O, PROFIL-V, PROFIL-O, BLANDARE, STANG, TAKDUSCH, HANDDUSCH), SKAP- (stommen, HYLLA1–4, DORR1–2,
SPARK), SPEGEL och HANDDUKSTORK-.
"""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, box, cylinder, polyeder, prisma, svep

from trebodar.byggdelar.virke import fmt
from trebodar.hus import badrum as B
from trebodar.material import (ASK, BADKARSMATERIAL, BANKSKIVA, BJORKPLYWOOD, DUSCHGLAS, KROM, PORSLIN, SPEGEL)

from . import koksskap as K

BANK_T, UTSTICK, BAK = B.BANKSKIVA_T, 15.0, 13.0   # bänkskivan, dess utstick utanför dörrarna och stommen från väggen
SOCKEL, SPARK_IN, SPARK_T = 100.0, 50.0, 16.0
REGEL = 40.0                                # reglarna fram och bak under tvättstället
SKAP_DORRAR = (1, 2, 1)                     # bänkens skåp: dörrar per skåp, alla dörrar lika breda
GODS = B.TVATTSTALL_GODS                    # tvättställets och badkarets gods (förenklat)
PROFIL = (20.0, 30.0)                       # duschdörrarnas väggprofil: från väggen, längs dörrarnas linje
SKAP_DJUP = 700.0                           # skåpets stomme
N_HYLLOR = 4
GREPP_Z = 1050.0                            # de höga dörrarnas grepp över golvet


def _dorrar(m: Montage, kod: str, bredd: float, z0: float, z1: float, n: int, grepp_z: float | None = None) -> None:
    """n dörrar av fräst ask över skåpets bredd, SPEL emellan och mot grannarna (i skåpets system, y −22..0)."""
    b = (bredd - (n + 1) * K.SPEL) / n
    for i in range(n):
        x0 = K.SPEL + i * (b + K.SPEL)
        m.lagg(Del(f"Dörr ask fräst {fmt(K.FRONT_T)} {fmt(b)}×{fmt(z1 - z0)}", K.front(x0, x0 + b, z0, z1, grepp_z),
                   ASK), Placering(), f"{kod}-DORR{i + 1}")


def _stomme(m: Montage, kod: str, bredd: float, djup: float, z0: float, z1: float, oppet_tak: bool = False,
            hyllor: int = 0) -> None:
    """Skåpets stomme av björkplywood (sidor, botten, tak eller reglar, rygg och hyllor) i skåpets system: x från
    vänster sida sett framifrån, y in i skåpet, z uppåt."""
    t = K.T
    delar = [("SIDA-V", box(0.0, t, 0.0, djup, z0, z1)), ("SIDA-H", box(bredd - t, bredd, 0.0, djup, z0, z1)),
             ("BOTTEN", box(t, bredd - t, 0.0, djup, z0, z0 + t)),
             ("RYGG", box(t, bredd - t, djup - t, djup, z0 + t, z1 - t))]
    if oppet_tak:
        delar += [("TAK-F", box(t, bredd - t, 0.0, REGEL, z1 - t, z1)),
                  ("TAK-B", box(t, bredd - t, djup - t - REGEL, djup - t, z1 - t, z1))]
    else:
        delar.append(("TAK", box(t, bredd - t, 0.0, djup - t, z1 - t, z1)))
    for i in range(hyllor):
        zh = z0 + t + (z1 - z0 - 2 * t) * (i + 1) / (hyllor + 1)
        delar.append((f"HYLLA{i + 1}", box(t, bredd - t, 20.0, djup - t, zh, zh + t)))
    for namn, f in delar:
        m.lagg(Del(f"Skåpstomme björkplywood {fmt(t)}", f, BJORKPLYWOOD), Placering(), f"{kod}-{namn}")


def _banken() -> Montage:
    """Badrumsbänken: skåpen (x längs bänken, framsidan mot rummet åt +y), sparklisten, bänkskivan, tvättstället och
    blandaren."""
    m = Montage("Badrumsbänken", beskrivning="Tre skåp med dörrar av fräst ask, bänkskiva Bricmate Jura 12 och "
                                            "undermonterat tvättställ")
    (x0, x1), yv = B.BANK_X, B.Y_1NO
    zg = B.Z_BANK                                                # bänken står på golvets högsta punkt under den
    zs, zt = zg + SOCKEL, zg + B.BANK_Z - BANK_T                  # sockelns överkant, skåpens överkant
    y_fram = yv + B.BANK_DJUP - UTSTICK                           # dörrarnas framsida
    y_st = y_fram - K.FRONT_T                                     # stommens framkant
    djup = y_st - (yv + BAK)
    dorr = (x1 - x0) / sum(SKAP_DORRAR)                          # en dörrs del av bänken
    kanter = [x0 + dorr * sum(SKAP_DORRAR[:k]) for k in range(len(SKAP_DORRAR) + 1)]
    # tvättstället undermonterat under bänkskivan, mellan stommens reglar; blandaren bakom det
    bi, di, hi = B.TVATTSTALL
    yt1 = y_st - REGEL - 3.0                                      # tvättställets framkant (utsidan)
    yt0 = yt1 - di - 2 * GODS
    xt0, xt1 = B.X_TVATTSTALL - bi / 2 - GODS, B.X_TVATTSTALL + bi / 2 + GODS
    k_ho = next(k for k in range(len(SKAP_DORRAR)) if kanter[k] <= B.X_TVATTSTALL < kanter[k + 1])
    assert kanter[k_ho] + K.T < xt0 and xt1 < kanter[k_ho + 1] - K.T, "tvättstället i ett skåp"
    for k, n in enumerate(SKAP_DORRAR):
        kod, bredd = f"BA-BANK{k + 1}", kanter[k + 1] - kanter[k]
        s = Montage(kod, "Skåp", f"Skåp {fmt(bredd)}×{fmt(djup)}, stomme av björkplywood 20, dörrar av ask",
                    produkt="BADRUMSSKAP")
        _stomme(s, kod, bredd, djup, zs, zt, oppet_tak=k == k_ho, hyllor=0 if k == k_ho else 1)
        _dorrar(s, kod, bredd, zs, zt - K.SPEL, n)
        m.lagg(s, Placering.axlar((kanter[k + 1], y_st, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)))
    # sparklisten följer golvet under bänken
    ys = y_fram - SPARK_IN
    z0 = B.lagsta_golv(x0, x1, ys - SPARK_T, ys)
    spark = B.pa_golvet(box(x0, x1, ys - SPARK_T, ys, z0 - 1.0, zs), x0, x1, ys - SPARK_T, ys)
    m.lagg(Del(f"Sparklist ask {fmt(SPARK_T)}", spark, ASK), Placering(), "BA-BANK-SPARK")
    hal = [(xt0 + GODS, yt0 + GODS), (xt1 - GODS, yt0 + GODS), (xt1 - GODS, yt1 - GODS), (xt0 + GODS, yt1 - GODS)]
    m.lagg(Del(f"Bänkskiva Bricmate Jura {fmt(BANK_T)}",
               prisma([(x0, yv), (x1, yv), (x1, yv + B.BANK_DJUP), (x0, yv + B.BANK_DJUP)], BANK_T, [hal], z0=zt),
               BANKSKIVA, produkt="BANKSKIVA"), Placering(), "BA-BANK-SKIVA")
    ho = box(xt0, xt1, yt0, yt1, zt - hi - GODS, zt) - box(xt0 + GODS, xt1 - GODS, yt0 + GODS, yt1 - GODS,
                                                           zt - hi, zt + 1.0)
    m.lagg(Del(f"Tvättställ porslin {fmt(bi)}×{fmt(di)}, undermonterat", ho, PORSLIN, produkt="TVATTSTALL"),
           Placering(), "BA-TVATTSTALL")
    xm, yb, z = B.X_TVATTSTALL, (yv + yt0) / 2, zt + BANK_T
    pip = svep([(xm, yb, z), (xm, yb, z + 160.0), (xm, yt0 + 70.0, z + 160.0), (xm, yt0 + 70.0, z + 120.0)], 11.0,
               30.0)
    m.lagg(Del("Tvättställsblandare", pip | cylinder(25.0, 80.0, (xm, yb, z)), KROM), Placering(),
           "BA-TVATTSTALL-BLANDARE")
    return m


def _ellips(a: float, b: float, z: float, n: int, cx: float = 0.0, cy: float = 0.0) -> list[tuple[float, float, float]]:
    return [(cx + a * math.cos(2 * math.pi * i / n), cy + b * math.sin(2 * math.pi * i / n), z) for i in range(n)]


def _loft(nedre: list[tuple[float, float, float]], ovre: list[tuple[float, float, float]]) -> Form:
    """Kroppen mellan två plana ringar med lika många hörn (sidorna trianglar, så att ytorna är plana)."""
    n = len(nedre)
    ytor: list[tuple[int, ...]] = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        ytor += [(i, j, n + j), (i, n + j, n + i)]
    return polyeder(nedre + ovre, ytor)


def _badkaret() -> Montage:
    """Badkaret: en avsmalnande oval (längden längs 1SO) med karet urtaget, och blandaren vid änden mot 1A."""
    m = Montage("Badkaret", beskrivning="Fristående badkar av mineralkomposit med golvstående blandare och handdusch")
    (x0, x1), (y0, y1) = B.BADKAR_X, B.BADKAR_Y
    L, W, H = B.BADKAR
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    zg = B.Z_BADKAR
    n, kant = 48, 45.0
    z0 = B.lagsta_golv(x0, x1, y0, y1) - 1.0                     # badkaret står på golvet (ställbara fötter)
    yttre = B.pa_golvet(_loft(_ellips(W / 2 - 110.0, L / 2 - 150.0, z0, n, cx, cy),
                              _ellips(W / 2, L / 2, zg + H, n, cx, cy)), x0, x1, y0, y1)
    kar = _loft(_ellips(W / 2 - 190.0, L / 2 - 330.0, zg + B.BADKAR_KAR, n, cx, cy),
                _ellips(W / 2 - kant, L / 2 - kant, zg + H + 1.0, n, cx, cy))
    m.lagg(Del(f"Badkar fristående {fmt(L)}×{fmt(W)}", yttre - kar, BADKARSMATERIAL, produkt="BADKAR"), Placering(),
           "BA-BADKAR")
    bx, by = B.BADKARSBLANDARE
    zb = B.hogsta_golv(bx - 45.0, bx + 45.0, by - 45.0, by + 45.0)
    pip = svep([(bx, by, zb), (bx, by, zb + 980.0), (bx, by - 230.0, zb + 980.0), (bx, by - 230.0, zb + 930.0)], 17.0,
               60.0)
    fot = B.pa_golvet(cylinder(45.0, 14.0, (bx, by, zb - 2.0)), bx - 45.0, bx + 45.0, by - 45.0, by + 45.0)
    hand = cylinder(16.0, 220.0, (bx + 45.0, by, zb + 560.0))
    m.lagg(Del("Badkarsblandare golvstående med handdusch", pip | fot | hand, KROM, produkt="BADKARSBLANDARE"),
           Placering(), "BA-BADKAR-BLANDARE")
    return m


def _wc() -> Montage:
    """WC:n med baksidan mot L9 (lokalt x ut i rummet, y längs väggen, z från golvet)."""
    m = Montage("WC", beskrivning="Golvstående WC med S-lås, sits och lock, cistern", produkt="WC")
    b, d, h = B.WC
    ram = (B.X_L9 - d, B.X_L9, B.WC_Y - b / 2, B.WC_Y + b / 2)
    zg = B.hogsta_golv(*ram)
    pl = Placering.axlar((B.X_L9, B.WC_Y, zg), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    bak = 180.0

    def d_form(x_bak: float, smal: float) -> list[tuple[float, float]]:
        r = b / 2 - smal
        pkt = [(x_bak, -r), (bak, -r)]
        pkt += [(bak + (d - bak) * math.sin(math.pi * i / 24), -r * math.cos(math.pi * i / 24)) for i in range(1, 24)]
        return pkt + [(bak, r), (x_bak, r)]
    for namn, kontur, z0, z1 in (("FOT", d_form(20.0, 40.0), 0.0, 220.0), ("SKAL", d_form(20.0, 0.0), 220.0, 400.0),
                                 ("SITS", d_form(bak - 20.0, 0.0), 400.0, 418.0),
                                 ("LOCK", d_form(bak - 10.0, 3.0), 418.0, 438.0)):
        f: Form = prisma(kontur, z1 - z0, z0=z0)
        if namn == "FOT":                                       # foten följer golvets fall
            f = B.pa_golvet(prisma(kontur, z1 - z0 + 10.0, z0=-10.0).placerad(pl), *ram)
            m.lagg(Del("WC fot", f, PORSLIN), Placering(), "BA-WC-FOT")
            continue
        m.lagg(Del(f"WC {namn.lower()}", f, PORSLIN), pl, f"BA-WC-{namn}")
    r, xc, yc = 40.0, bak - 20.0, b / 2 - 10.0                  # cisternen med rundade hörn mot rummet
    hornen = [(xc - r + r * math.cos(math.pi / 2 * i / 8), sy * (yc - r + r * math.sin(math.pi / 2 * i / 8)))
              for sy in (-1.0, 1.0) for i in (range(8, -1, -1) if sy < 0 else range(9))]
    cistern = [(0.0, -yc)] + sorted((q for q in hornen if q[1] < 0), key=lambda q: q[1]) + \
        sorted((q for q in hornen if q[1] > 0), key=lambda q: q[1]) + [(0.0, yc)]
    m.lagg(Del("WC cistern", prisma(cistern, h - 438.0, z0=438.0), PORSLIN), pl, "BA-WC-CISTERN")
    return m


def _duschen() -> Montage:
    """Duschens två glasdörrar i nischens öppning (stängda) med väggprofilerna, och duschsetet på 1C."""
    m = Montage("Duschen", beskrivning="Två glasdörrar 8 mm i nischen, termostatblandare med takdusch och handdusch")
    p, q = PROFIL
    z0 = B.Z_DUSCH + B.DUSCHDORR_SPEL
    z1 = z0 + B.DUSCHDORR_H
    t, y = B.DUSCHDORR_T, B.Y_DUSCH
    xa, xb = B.X_1B + p, B.X_L11 - p
    xm = (xa + xb) / 2
    for namn, (a, c) in (("V", (xa + 2.0, xm - 2.0)), ("O", (xm + 2.0, xb - 2.0))):
        m.lagg(Del(f"Duschdörr härdat glas {fmt(t)} {fmt(c - a)}×{fmt(z1 - z0)}",
                   box(a, c, y - t / 2, y + t / 2, z0, z1), DUSCHGLAS, produkt="DUSCHDORRAR"), Placering(),
               f"BA-DUSCH-DORR-{namn}")
        xh = c - 60.0 if namn == "V" else a + 60.0
        handtag = svep([(xh, y - t / 2, z0 + 900.0), (xh, y - 45.0, z0 + 900.0), (xh, y - 45.0, z0 + 1300.0),
                        (xh, y - t / 2, z0 + 1300.0)], 8.0, 20.0)
        m.lagg(Del("Duschdörrens handtag", handtag, KROM), Placering(),
               f"BA-DUSCH-HANDTAG-{namn}")
    for namn, (a, c) in (("V", (B.X_1B, xa)), ("O", (xb, B.X_L11))):
        m.lagg(Del("Duschdörrarnas väggprofil", box(a, c, y - q / 2, y + q / 2, z0, z1), KROM), Placering(),
               f"BA-DUSCH-PROFIL-{namn}")
    # duschsetet på 1C: blandaren 60 mm ut från kaklet, stången upp till armen och takduschen ut i duschen
    ds = Montage("Duschset", beskrivning="Termostatblandare med stång, takdusch och handdusch", produkt="DUSCHSET")
    xd, yd = B.X_DUSCHBLANDARE, B.Y_1C - 60.0
    zg = B.golvniva(xd, yd)
    zb, zt = zg + B.Z_DUSCHBLANDARE, zg + B.Z_TAKDUSCH
    ds.lagg(Del("Termostatblandare dusch", svep([(xd - 160.0, yd, zb), (xd + 160.0, yd, zb)], 30.0, 0.0), KROM),
            Placering(), "BA-DUSCH-BLANDARE")
    arm = 350.0
    ds.lagg(Del("Duschstång med arm", svep([(xd, yd, zb + 30.0), (xd, yd, zt + 120.0), (xd, yd - arm, zt + 120.0),
                                         (xd, yd - arm, zt + 12.0)], 12.0, 40.0), KROM),
            Placering(), "BA-DUSCH-STANG")
    ds.lagg(Del("Takdusch Ø250", cylinder(125.0, 12.0, (xd, yd - arm, zt)), KROM), Placering(), "BA-DUSCH-TAKDUSCH")
    ds.lagg(Del("Handdusch", cylinder(18.0, 240.0, (xd + 30.0, yd, zb + 330.0)), KROM), Placering(),
            "BA-DUSCH-HANDDUSCH")
    m.lagg(ds)
    return m


def _skapet() -> Montage:
    """Skåpet i nischen: dörrarna i L9:s yta, stommen in mot L11 (lokalt x från vänster sida, vid L19, y in i skåpet
    åt +x)."""
    m = Montage("Skåpet", beskrivning="Inbyggt skåp med hyllor och två höga dörrar av fräst ask i nischen vid L10")
    (x0, x1), (y0, y1) = B.SKAP_X, B.SKAP_Y
    zg = B.hogsta_golv(x0, x1, y0, y1)
    zs, zt = zg + SOCKEL, zg + B.SKAP_Z
    bredd = y1 - y0 - 2 * K.SPEL
    pl = Placering.axlar((x0 + K.FRONT_T, y1 - K.SPEL, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
    s = Montage("BA-SKAP", "Skåp", f"Skåp {fmt(bredd)}×{fmt(SKAP_DJUP)}, stomme av björkplywood 20, dörrar av ask",
                produkt="BADRUMSSKAP")
    _stomme(s, "BA-SKAP", bredd, SKAP_DJUP, zs, zt, hyllor=N_HYLLOR)
    _dorrar(s, "BA-SKAP", bredd, zs, zt, 2, zg + GREPP_Z)
    m.lagg(s, pl)
    xs, ya, yb = x0 + SPARK_IN, y0 + K.SPEL, y1 - K.SPEL
    z0 = B.lagsta_golv(xs, xs + SPARK_T, ya, yb)
    spark = B.pa_golvet(box(xs, xs + SPARK_T, ya, yb, z0 - 1.0, zs), xs, xs + SPARK_T, ya, yb)
    m.lagg(Del(f"Sparklist ask {fmt(SPARK_T)}", spark, ASK), Placering(), "BA-SKAP-SPARK")
    return m


def _spegeln() -> Del:
    x0, x1, z0, z1 = B.SPEGEL
    zg = B.Z_BANK
    return Del(f"Spegel {fmt(x1 - x0)}×{fmt(z1 - z0)}, limmad på kaklet",
               box(x0, x1, B.Y_1NO, B.Y_1NO + 6.0, zg + z0, zg + z1), SPEGEL, produkt="SPEGEL")


def _handdukstorken() -> Montage:
    """Elektrisk handdukstork på 1A: två lodräta rör och stegar emellan, 60 mm från kaklet."""
    m = Montage("Handdukstorken", beskrivning="Elektrisk handdukstork, krom", produkt="HANDDUKSTORK")
    x0, x1, z0, z1 = B.HANDDUKSTORK
    y = B.Y_1A - 60.0
    zg = B.golvniva((x0 + x1) / 2, y)
    r_sida, r_steg = 15.0, 11.0
    for namn, x in (("V", x0 + r_sida), ("O", x1 - r_sida)):
        m.lagg(Del(f"Handdukstork rör Ø{fmt(2 * r_sida)}", cylinder(r_sida, z1 - z0, (x, y, zg + z0)), KROM),
               Placering(), f"BA-HANDDUKSTORK-{namn}")
        for i, zf in enumerate((z0 + 100.0, z1 - 100.0)):
            m.lagg(Del("Handdukstork fäste", svep([(x, y + r_sida, zg + zf), (x, B.Y_1A, zg + zf)], 8.0, 0.0), KROM),
                   Placering(), f"BA-HANDDUKSTORK-{namn}-FASTE{i + 1}")
    n = int((z1 - z0 - 60.0) // 85.0)
    for i in range(n):
        zs = zg + z0 + 40.0 + i * (z1 - z0 - 80.0) / (n - 1)
        m.lagg(Del(f"Handdukstork steg Ø{fmt(2 * r_steg)}", svep([(x0 + 2 * r_sida, y, zs), (x1 - 2 * r_sida, y, zs)],
                                                              r_steg, 0.0), KROM),
               Placering(), f"BA-HANDDUKSTORK-STEG{i + 1:02d}")
    return m


def montage() -> Montage:
    m = Montage("Badrum", beskrivning="Badrumsbänken med tvättstället, badkaret, WC:n, duschen, skåpet, spegeln och "
                                      "handdukstorken (ärende #52)")
    m.lagg(_banken())
    m.lagg(_badkaret())
    m.lagg(_wc())
    m.lagg(_duschen())
    m.lagg(_skapet())
    m.lagg(_spegeln(), Placering(), "BA-SPEGEL")
    m.lagg(_handdukstorken())
    return m
