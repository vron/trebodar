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

Handlingen anger de gemensamma förutsättningarna för konstruktionen: objektet, regelverk, klasser och laster. Detaljhandlingarna i avsnitt 5 bygger på dessa och redovisar respektive del av konstruktionen.

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
  [Byggnad], [Fritidshus i 1½ plan med källare, byggnadsarea #o.bya m², bruttoarea #o.bta m²],
  [Läge], [Kustläge, öppet mot havet i väster. Färdigt golv #o.fg (#o.koordinater)],
)

*Bärande system.* Huset består av tre förskjutna byggnadskroppar med sadeltak, takvinkel #r.sno.alfa°, som ligger bredvid varandra med dalar mellan.

- *Tak:* bandtäckt plåt på råspont. Takbalkar 45×170 C24 c/c 600 spänner mellan nock- och dalbalkar av limträ med stålplåtar (K-01). I gavlarna och i husets mitt bärs nockbalkarna av triangulerade takstolar.
- *Väggar:* regelstomme 45×95 C24 med skivor på båda sidor. Skivverkan stabiliserar huset mot horisontella laster. Nock- och dalbalkarnas stöd bärs av stolpar av sammansatta reglar.
- *Bjälklag:* platsgjuten armerad betongplatta, #r.bj.t mm, över källaren.
- *Källare och grund:* ytterväggar av armerade Leca-block 350 mm, återfyllda till högst 2 m. Innerväggar 45×120 C24 och pelare 140×140 GL30h. Bottenplatta av betong på dränerande grus på sprängd berggrund.

= Regelverk och klasser

Ansökan om lov kom in före den 1 juli 2026. Byggherren tillämpar därför de äldre reglerna, BBR och EKS, i sin helhet enligt övergångsbestämmelserna till Boverkets byggregler som gäller från den 1 juli 2025.

#table(
  columns: (1.25fr, 1fr),
  align: (left, left),
  [Regel], [Omfattning],
  [PBL (2010:900), PBF (2011:338)], [Plan- och bygglagen och -förordningen],
  [EKS 12, BFS 2011:10 med ändringar t.o.m. BFS 2022:4], [Bärförmåga, stadga och beständighet, nationella val till eurokoderna],
  [BBR, BFS 2011:6 med ändringar], [Övriga tekniska egenskapskrav],
  [SS-EN 1990, SS-EN 1991-1-1, -1-3, -1-4, -1-5], [Grundläggande dimensionering och laster],
  [SS-EN 1992-1-1, SS-EN 1993-1-1, SS-EN 1995-1-1, SS-EN 1996-1-1, SS-EN 1997-1], [Betong, stål, trä, murverk och geoteknik],
  [SS-EN 14081-1, SS-EN 14080, SS-EN 10025-2, SS-EN 206], [Konstruktionsvirke, limträ, konstruktionsstål och betong],
  [SS-EN 1090-2], [Utförande av stålkonstruktioner],
)

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [Klass], [Val], [Gäller],
  [Säkerhetsklass], [#r.klasser.sakerhetsklass, $gamma_d$ = #str(r.klasser.gamma_d).replace(".", ",")], [Hela den bärande stommen (EKS avd. A 13 §)],
  [Avsedd livslängd], [#r.klasser.livslangd år], [Kategori 4, SS-EN 1990 tabell 2.1],
  [Klimatklass], [1], [Trä inom klimatskärmen. Huset hålls uppvärmt året runt],
  [], [2], [Trä på klimatskärmens kalla sida, till exempel råspont och läkt],
  [Utförandeklass stål], [EXC2], [SS-EN 1090-2],
)

= Laster

Karakteristiska värden. Lastkombinationer enligt SS-EN 1990 med EKS: ekvation 6.10a och 6.10b med $gamma_d$ i brottgränstillstånd, karakteristisk och kvasipermanent kombination i bruksgränstillstånd. Detaljhandlingarna får använda förenklingar som ligger på säker sida.

== Egenvikt

#block(breakable: false, grid(
  columns: (1fr, 1fr),
  column-gutter: 14pt,
  table(
    columns: (1fr, auto),
    align: (left, right),
    [Tak, per m² takyta], [kg/m²],
    ..r.tak.map(t => ([#t.skikt], [#t.kg])).flatten(),
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
      [Golvuppbyggnad och ytskikt], [#r.bj.golv],
    )
    #liten[Tunghet för betong enligt SS-EN 1991-1-1 tabell A.1. Isoleringens densitet enligt tillverkaren. Stålbalkar och stolpar räknas med sin verkliga vikt i detaljhandlingarna.]
  ],
))

== Variabla laster

#table(
  columns: (auto, auto, auto, auto, auto, 1fr),
  align: (left, right, right, right, right, left),
  [Last], [Värde], [$psi_0$], [$psi_1$], [$psi_2$], [Underlag],
  [Nyttig last, bjälklag kat. A], [$q_k$ = #r.nyttig.qk kN/m²], [0,7], [0,5], [0,3], [EKS tabell C-1. $Q_k$ = #r.nyttig.Qk kN],
  [Lätta mellanväggar], [#r.nyttig.vagg kN/m²], [], [], [], [Egentyngd högst 1,0 kN/m vägg, SS-EN 1991-1-1 6.3.1.2(8). Tyngre väggar som linjelast],
  [Snö, grundvärde], [$s_k$ = #r.sno.sk kN/m²], [0,6], [0,3], [0,1], [EKS, Tanums kommun. $C_e$ = $C_t$ = 1,0],
  [Snö, takfall], [#r.sno.s1 kN/m²], [], [], [], [$mu_1$ = #r.sno.mu1, sadeltak #r.sno.alfa°, SS-EN 1991-1-3 5.3.3],
  [Snö, vid dalarna], [#r.sno.s2 kN/m²], [], [], [], [$mu_2$ = #r.sno.mu2, flerspannstak, SS-EN 1991-1-3 5.3.4],
  [Vind, hastighetstryck], [$q_p$ = #r.vind.qp kN/m²], [0,3], [0,2], [0], [$v_b$ = #r.vind.vb m/s (EKS, Tanum), terrängtyp 0, $z$ = #r.vind.z m],
  [Temperatur], [], [0,6], [0,5], [0], [SS-EN 1991-1-5. Stål–trä-balkarna, se K-01 och K-02],
  [Jordtryck], [], [], [], [], [Källarväggar, återfyllning högst 2 m med dränerande material, se K-06],
)

*Vind.* Terrängtyp 0 med $z_0$ = #r.vind.z0 m: $k_r$ = #r.vind.kr, $c_r$ = #r.vind.cr, $I_v$ = #r.vind.Iv. Med $q_b$ = #r.vind.qb kN/m² blir $q_p = (1 + 7 I_v) dot 1/2 rho (c_r v_b)^2$ = #r.vind.qp kN/m² ($c_e$ = #r.vind.ce). Formfaktorer för tak och väggar tas fram i respektive detaljhandling.

= Handlingar till tekniskt samråd

Handlingarna motsvarar det som kallelsen till tekniskt samråd begär. Konstruktionsritningarna R-01 och R-02 hänvisar till beräkningarna K-01 till K-06.

#table(
  columns: (auto, 1fr, auto, 1.3fr),
  align: (left, left, left, left),
  [Nr], [Handling], [Status], [Kommentar],
  ..r.handlingar.map(h => ([#h.nr], [#h.namn], [#h.status], [#h.kommentar])).flatten(),
)
