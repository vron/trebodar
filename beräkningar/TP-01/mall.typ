#let r = json("resultat.json")
#let p = r.projekt
#let grå = luma(105)
#let varning = rgb("#a8530c")

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
#show heading.where(level: 2): it => block(above: 9pt, below: 4pt, text(size: 9.5pt, weight: "bold")[#counter(heading).display() #h(3pt) #it.body])
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.6pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 3pt, bottom: 3pt, it)
#show figure.caption: set text(size: 8.5pt)

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Byggets faser och steg med ansvar, organisationen], [*Upprättad*], p.upprattad,
  ..if p.granskad != "" { ([], [], [*Granskad*], p.granskad) },
)

= Omfattning

Tidsplanen visar byggets faser och steg från tekniskt samråd till slutbesked på #p.fastighet (ärende #p.arende), med ansvarig och inblandade för varje steg, och byggets organisation. Byggstart är #r.byggstart. Tiderna fram till gjutningen av mellanbjälklaget följer byggherrens etapplan och byggskedet i K-06; de senare är preliminära och stäms av på byggmötena.

Den ansvariga parten ser till att steget blir gjort i rätt tid och enligt handlingarna; de inblandade utför delar av det eller behöver vara på plats. Faserna används också i inköpslistan IN-01: varje specialprodukt ska finnas på bygget när dess fas börjar (avsnitt 4).

#figure(image("fig_oversikt.svg", width: 100%), caption: [Hela projektet. Fyllda staplar är planerade, streckade preliminära; romberna är milstolpar och det gråa uppehåll.]) <fig-oversikt>

#table(
  columns: (1fr, auto, auto, auto),
  [Milstolpe], [Fas], [Datum], [Läge],
  ..r.milstolpar.map(m => ([#m.namn], [#m.fas], [#m.tid], text(fill: if m.lage == "preliminär" { grå } else { luma(25) }, m.lage))).flatten(),
)

= Organisation

Byggherren samordnar entreprenörerna och leverantörerna. Kontrollansvarig följer kontrollplanen (KP-01).

#table(
  columns: (auto, auto, 1fr, auto),
  [Roll], [Namn], [Uppgift], [Status],
  ..r.parter.map(x => ([#x.roll], [#x.namn], text(size: 8.5pt, x.uppgift), [#x.status])).flatten(),
)

= Från byggstart till stommen

#figure(image("fig_bygget.svg", width: 100%), caption: [Rivning, grund, mellanbjälklag och stomme vecka för vecka (veckonummer överst).]) <fig-bygget>

= Faserna

#set table(inset: (x: 4pt, y: 3pt))
#for f in r.faser [
  #block(breakable: f.steg.len() > 7)[
  == #f.namn #h(1fr) #text(size: 8.5pt, weight: "regular", fill: grå)[#f.tid#if f.prel [, preliminärt]]
  #set text(size: 8.5pt)
  #table(
    columns: (3.5cm, 2.7cm, 2.2cm, 2.6cm, 1fr),
    table.header([Steg], [Tid], [Ansvarig], [Inblandade], [Anmärkning]),
    ..f.steg.map(s => (
      [#if s.milstolpe [*#s.namn*] else [#s.namn]#if s.klar [ #text(fill: grå)[(klar)]]],
      [#s.tid \ #text(size: 7.5pt, fill: grå)[#s.vecka#if s.prel [, prel.]]],
      if s.ansvarig == "" { text(fill: varning)[ej bestämt] } else [#s.ansvarig#if s.forslag [ \ #text(size: 7.5pt, fill: grå)[förslag]]],
      [#s.inblandade],
      text(size: 7.5pt, fill: luma(60), s.anm),
    )).flatten(),
  )
  #if f.produkter.len() > 0 [
    #text(size: 8pt, fill: luma(60))[*Specialprodukter (IN-01):* #f.produkter.map(x => x.namn + " (" + x.status + ")").join(", ").]
  ]
  ]
]

= Förutsättningar och marginaler

- *Starten.* Byggstarten ligger direkt efter industrisemestern, och sommargrannar kan finnas kvar den första veckan. Tidigare start är inte realistisk med tanke på sprängningen.
- *Kedjan till mellanbjälklaget* har ingen marginal: varje etapp förutsätter den föregående, och en försening tidigt flyttar hela kedjan. Två veckors försening flyttar gjutningen av mellanbjälklaget till mitten av november.
- *Parallellgångar* om tid måste tas igen, tillsammans cirka två veckor: formen kan resas medan väggarna härdar, återfyllningen behöver bara den nedgrävda delen klar och elarbetet i etapp 8 kan börja där formen redan ligger.
- *Betongen.* Återfyllning och formrivning först vid 70 % av hållfastheten, 10–14 dygn vid 5–10 °C med cement i klass N (K-06, R-06). Ingen gjutning under −5 °C; i november kan vinterbetong och isolermattor behövas.
- *Vintern.* Stommen står till våren med råspont och fullvärdig underlagspapp (U-03). Takplåten läggs när temperaturen räcker för plåten.
- *Uppehåll.* #r.uppehall.map(u => u.namn + " " + u.tid).join("; ") ingår i tiderna.
- *Ansvar.* #r.ej_bestamda steg har ännu ingen bestämd ansvarig (ej bestämt i tabellerna).
