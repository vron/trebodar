#let r = json("resultat.json")
#let p = r.projekt
#let o = r.objekt

#set document(title: p.objekt, author: p.upprattad)
#set page(
  paper: "a4",
  margin: (x: 18mm, top: 20mm, bottom: 16mm),
  header: context [
    #set text(8pt)
    #grid(columns: (1fr, auto), p.namn, [#p.dokument rev #p.revision · Sida #counter(page).display() av #counter(page).final().first()])
    #v(-2pt)
    #line(length: 100%, stroke: 0.4pt)
  ],
)
#set text(font: "Carlito", size: 9.5pt, lang: "sv")
#set par(justify: false, leading: 0.55em, spacing: 0.75em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  v(5pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#show heading.where(level: 2): it => block(above: 8pt, below: 4pt, text(size: 9.5pt, weight: "bold")[#counter(heading).display() #h(3pt) #it.body])
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 3pt, bottom: 3pt, it)
#let liten(body) = text(size: 8.5pt, body)

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Översikt inför tekniskt samråd], [*Upprättad*], p.upprattad,
  ..if p.granskad != "" { ([], [], [*Granskad*], p.granskad) },
)

= Syfte

Handlingen anger de gemensamma förutsättningarna för konstruktionen: regelverk, klasser och laster. Detaljhandlingarna i avsnitt 5 bygger på dessa och redovisar respektive del av konstruktionen.
// Avsnitt 5 listar handlingarna som lämnas in till tekniskt samråd. Serierna och numreringen står i registret, indata.toml ([[serie]]).

= Objekt

#table(
  columns: (auto, 1fr),
  align: (left, left),
  stroke: (x, y) => (bottom: 0.3pt + luma(170)),
  [Fastighet], o.fastighet,
  [Adress], o.adress,
  [Ärende], [#o.arende. #o.lov],
  [Byggherre], o.byggherre,
  [Kontrollansvarig], o.ka,
  [Byggnad], [Fritidshus i tre förskjutna byggnadskroppar med källare. Byggnadsarea #o.bya m², bruttoarea #o.bta m²],
  [Läge], [Kustläge. Färdigt golv #o.fg (#o.koordinater)],   // som situationsplanen 200 rev 02: FG +8,5, SWEREF 99 12 00, RH2000
)

*Bärande system.* Byggnadskropparna har sadeltak med takvinkel #r.sno.alfa° och ligger bredvid varandra med dalar mellan.

- *Tak:* bandtäckt zink-magnesiumplåt på underlagspapp och råspont, med en ventilerad luftspalt mot isoleringen. Takbalkar 45×170 C24 c/c 600 spänner mellan nock- och dalbalkar av limträ med stålplåtar. I gavlarna och i husets mitt bärs nockbalkarna av triangulerade takstolar.
- *Väggar:* regelstomme 45×95 C24 med skivor på båda sidor och installationsskikt 45 invändigt. Gavlarna 1SV och 2SV har reglar 45×145, 1SV med OSB och gips direkt på reglarna. Stålband i kryss i väggarna och i en del av takfallens fält stabiliserar huset mot horisontella laster. Nock- och dalbalkarnas stöd bärs av stolpar av sammansatta reglar och limträ.
  // Gaveln 1SV saknar installationsskikt och installationer. Karmreglarna vid gavlarnas fönster mot NO och vid 3SV är dubbla.
  // Skjuvskivor tillsammans med stålbanden (K-04): utegipsen, OSB:n direkt på reglarna i de bärande innerväggarna och i
  // gaveln 1SV och råsponten i takfallen. Huvudstolpen LN1_3 med strävor på båda sidor står under nockbalk 1 (K-03).
- *Bjälklag:* platsgjuten armerad betongplatta, #r.bj.t mm, över källaren.
- *Källare och grund:* väggar av Sundolitt Kub 350-150. Inne i källaren bärs bjälklaget av rör VKR 80×80×4 i stål, svetsade på fotplåtar som är ingjutna i bottenplattans plintar och med topplåtar ingjutna i bjälklaget. Bottenplatta L400 på makadam på sprängt berg. Där södra huskroppen saknar källare ligger mellanbjälklaget som platta på mark på 350 mm cellplast.
  // Kub 350-150: armerad betongkärna 150 mm i kvarsittande form av cellplast, 100 mm på var sida (K-06). Vid P7 två rör
  // tätt intill varandra (K-05). L400: 100 mm betong på 300 mm cellplast, kantbalkar i L-element, balkar under
  // innerväggarna och plintar under rören (K-06). Plattan på mark: L-element 500, 150 mm platta på 350 mm cellplast
  // (K-06, AR-02). "Södra" efter verklig nordriktning (situationsplanen), inte modellens nominella (norr = lågt y).

= Regelverk och klasser

Ansökan om lov kom in före den 1 juli 2026. Byggherren tillämpar därför de äldre reglerna, BBR och EKS, i sin helhet enligt övergångsbestämmelserna till Boverkets byggregler.
// De nya reglerna (BFS 2024:5 m.fl.) gäller från den 1 juli 2025; de äldre får tillämpas när ansökan om lov kom in före
// den 1 juli 2026 (Boverkets konsekvensutredning till BFS 2024:14). Lovet: BYGG.2025.2278, beslut 2026-02-18.

// Referenserna kontrollerade 2026-11-28: EKS 12 = BFS 2011:10 med ändringar t.o.m. BFS 2022:4 (Boverket); standarderna
// är de som detaljhandlingarna hänvisar till (K-01–K-06, R-05: VKR-rören efter SS-EN 10219).
#table(
  columns: (1.25fr, 1fr),
  align: (left, left),
  [Regel], [Omfattning],
  [PBL (2010:900), PBF (2011:338)], [Plan- och bygglagen och -förordningen],
  [EKS 12, BFS 2011:10 med ändringar t.o.m. BFS 2022:4], [Bärförmåga, stadga och beständighet, nationella val till eurokoderna],
  [BBR, BFS 2011:6 med ändringar], [Övriga tekniska egenskapskrav],
  [SS-EN 1990, SS-EN 1991-1-1, -1-3, -1-4, -1-5, -1-6], [Grundläggande dimensionering och laster, även under byggskedet],
  [SS-EN 1992-1-1, -1-2, SS-EN 1992-4], [Betong, även vid brand, och infästningar i betong],
  [SS-EN 1993-1-1, -1-3, -1-8], [Stål, tunnplåt (stålbanden) och förband],
  [SS-EN 1995-1-1, SS-EN 1996-1-1, SS-EN 1997-1], [Trä, murverk och geoteknik],
  [SS-EN 14081-1, SS-EN 14080, SS-EN 10025-2, SS-EN 10219, SS-EN 206], [Konstruktionsvirke, limträ, konstruktionsstål, kallformade konstruktionsrör och betong],
  [SS-EN 1090-2], [Utförande av stålkonstruktioner],
)

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [Klass], [Val], [Gäller],
  // Säkerhetsklass 2 får väljas för små byggnader med högst två plan där få personer vistas mer än tillfälligt, t.ex.
  // en- och tvåbostadshus (Boverket, val av säkerhetsklass). EXC2 räcker för statiskt belastade stålkonstruktioner (EKS,
  // allmänt råd med tabell C.1 i SS-EN 1993-1-1/A1).
  [Säkerhetsklass], [#r.klasser.sakerhetsklass, $gamma_d$ = #str(r.klasser.gamma_d).replace(".", ",")], [Hela den bärande stommen (EKS avd. A 13 §)],
  [Avsedd livslängd], [#r.klasser.livslangd år], [Kategori 4, SS-EN 1990 tabell 2.1],
  [Klimatklass], [1], [Trä inom klimatskärmen. Huset hålls uppvärmt året runt],
  [], [2], [Trä på klimatskärmens kalla sida, till exempel råspont och läkt],
  [Utförandeklass stål], [EXC2], [SS-EN 1090-2],
)

= Laster

Karakteristiska värden. Lastkombinationer enligt SS-EN 1990 med EKS.
// Brottgränstillstånd: ekvation 6.10a och 6.10b med gamma_d; bruksgränstillstånd: karakteristisk och kvasipermanent kombination.

== Egenvikt

#block(breakable: false, grid(
  columns: (1fr, 1fr),
  column-gutter: 14pt,
  table(
    columns: (1fr, auto),
    align: (left, right),
    [Tak, per m² takyta], [kg/m²],
    ..r.tak.filter(t => t.kg != "0,0").map(t => ([#t.skikt], [#t.kg])).flatten(),   // skikt utan vikt (ångbromsen) visas inte
    [*Summa*], [*#r.kg_tak*],
  ),
  [
    #table(
      columns: (1fr, auto),
      align: (left, right),
      [Byggnadsdel], [kN/m²],
      [Tak, per m² takyta], [*#r.g_tak*],
      [Tak, per m² horisontell yta], [#r.g_tak_h],
      [Betongbjälklag #r.bj.t mm, #r.bj.gamma kN/m³], [#r.bj.g],
      [Golvuppbyggnad], [#r.bj.golv],
    )
    // Golvuppbyggnaden täcker trägolv 20 mm (ca 0,15 kN/m²) och klinker i våtrum. Tunghet för betong enligt SS-EN 1991-1-1
    // tabell A.1. Isoleringens densitet enligt tillverkaren. Stålbalkar och stolpar räknas med sin verkliga vikt i
    // detaljhandlingarna.
  ],
))

== Variabla laster

#table(
  columns: (auto, auto, auto, auto, auto, 1fr),
  align: (left, right, right, right, right, left),
  [Last], [Värde], [$psi_0$], [$psi_1$], [$psi_2$], [Underlag],
  [Nyttig last, bjälklag kat. A], [$q_k$ = #r.nyttig.qk kN/m²], [0,7], [0,5], [0,3], [EKS tabell C-1. $Q_k$ = #r.nyttig.Qk kN],
  [Lätta mellanväggar], [#r.nyttig.vagg kN/m²], [], [], [], [På säker sida mot 0,5 kN/m² för väggar på högst 1,0 kN/m, SS-EN 1991-1-1 6.3.1.2(8). Tyngre väggar som linjelast],
  [Snö, grundvärde], [$s_k$ = #r.sno.sk kN/m²], [0,6], [0,3], [0,1], [EKS, Tanums kommun. $C_e$ = $C_t$ = 1,0],
  [Snö, takfall], [#r.sno.s1 kN/m²], [], [], [], [$mu_1$ = #r.sno.mu1, sadeltak #r.sno.alfa°, SS-EN 1991-1-3 5.3.3],
  [Snö, vid dalarna], [#r.sno.s2 kN/m²], [], [], [], [$mu_2$ = #r.sno.mu2, flerspannstak, SS-EN 1991-1-3 5.3.4],
  [Vind, hastighetstryck], [$q_p$ = #r.vind.qp kN/m²], [0,3], [0,2], [0], [$v_b$ = #r.vind.vb m/s (EKS, Tanum), terrängtyp 0],
  [Temperatur], [], [0,6], [0,5], [0], [SS-EN 1991-1-5. Stål–trä-balkarna, se K-01 och K-02],
  [Jordtryck], [], [], [], [], [Källarväggar, se K-06],
)

// Vind: terrängtyp 0, z0 = 0,003 m, referenshöjden z = nockens höjd över marken (5,6 m). q_p = (1 + 2 k_p I_v)·½ρ(c_r v_b)²
// enligt EKS avd. C kap. 1.1.4 7 § i stället för uttryck 4.8 i SS-EN 1991-1-4, k_p = 3,0; c_0 = 1 (topografin ökar inte
// vinden, SS-EN 1991-1-4 4.3.3). Värdena (k_r, c_r, I_v, q_b, c_e) räknas i berakning.py. Formfaktorerna i varje detaljhandling.

== Bruksgränstillstånd

Gränsvärden för nedböjning. EKS anger inga värden, så de bestäms för projektet inom standardernas rekommendationer.

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [Byggnadsdel], [Krav], [Underlag],
  [Tak: nock-, dal- och takbalkar], [$w_"fin"$ ≤ $L$/#r.nedb.tak], [SS-EN 1995-1-1 tabell 7.2, strängaste värdet i intervallet $L$/150–$L$/300],
  [Betongbjälklag], [≤ $L$/#r.nedb.bjalklag], [Kvasipermanent last, SS-EN 1992-1-1 7.4.1(4)],
)

= Handlingar till tekniskt samråd

== Uppdaterade revisioner av bygglovsdokument

Bygglovsritningar som har reviderats efter beslutet (D32, 2026-02-18). Ändringarna är små och lämnas in till kommunen.

#table(
  columns: (12mm, 1fr, 10mm, 20mm, 1.2fr),
  align: (left, left, left, left, left),
  [Nr], [Ritning], [Rev], [Datum], [Ändring],
  ..r.bygglov.map(h => ([#h.nr], [#h.namn], [#h.rev], [#h.datum], [#h.andring])).flatten(),
)

== Konstruktionshandlingar

#table(
  columns: (12mm, 1fr, 16mm),
  align: (left, left, left),
  [Nr], [Handling], [Status],
  ..r.handlingar.map(h => ([#h.nr], [#h.namn], [#h.status])).flatten(),
)

// Avsnittet om numreringen (serierna, samråd ja/nej) är borttaget ur pdf:en; registret är indata.toml ([[serie]]),
// som webbplatsens handlingsförteckning läser.
