#let r = json("resultat.json")
#let p = r.projekt
#let farg = ("att välja": rgb("#a8530c"), "vald": luma(25), "offert": rgb("#1f4e8c"), "beställd": rgb("#1f4e8c"),
  "levererad": rgb("#2d6a31"), "monterad": rgb("#2d6a31"))
#let grå = luma(105)

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
#show link: set text(fill: rgb("#1f4e8c"))

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Specialprodukterna: val, beställning och leverans], [*Upprättad*], p.upprattad,
  ..if p.granskad != "" { ([], [], [*Granskad*], p.granskad) },
)

= Omfattning

Listan omfattar husets specialprodukter: det som väljs, beställs eller tillverkas för sig, som vitvaror, fönster och dörrar, kaminen, armaturerna och specialtillverkat stål och limträ. Vanligt material, som virke, skivor, isolering, armering, kabel och rör, ingår inte; det framgår av handlingarna och modellen.

Antalet och id:na kommer ur husets 3D-modell: produkten är märkt där den skapas i modellen, så att listan följer modellen när den ändras. Id är instansens namn i modellen, som på ritningarna (fönstret 3NV-F4, armaturen KO-L05). En produkt som inte är modellerad anger sin omfattning. Listan har #r.produkter specialprodukter med #r.instanser instanser i modellen (avsnitt 4).

#table(
  columns: (auto, 1fr),
  [Status], [Betydelse],
  ..r.status.map(s => (text(fill: farg.at(s.namn), s.namn), [#s.text])).flatten(),
)

*Ansvarig* är rollen som ser till att produkten väljs och beställs: #r.roller.join(", ", last: " och "). *Skede* är när produkten ska finnas på bygget senast: #r.skeden.join(", ", last: " och "), i byggets ordning. Ärendena (\#) finns på GitHub.

= Översikt

Produkterna per skede och status.

#table(
  columns: (1fr, ..r.status.map(_ => auto), auto),
  align: (left, ..r.status.map(_ => center), center),
  [Skede], ..r.status.map(s => text(fill: farg.at(s.namn), s.namn)), [Summa],
  ..r.oversikt.map(o => ([#o.skede], ..o.antal.map(n => if n > 0 [#n] else [–]), [#o.summa])).flatten(),
  [*Summa*], ..r.summa.map(n => [*#n*]), [*#r.produkter*],
)

= Produkter

#set table(inset: (x: 4pt, y: 3pt))
#for g in r.grupper [
  #block(breakable: false)[
  == #g.namn
  #set text(size: 9pt)
  #table(
    columns: (1fr, 1.7cm, 1.5cm, 2.8cm, 2.6cm),
    align: (left, left, left, left, left),
    table.header([Produkt], [Antal], [Status], [Ansvarig], [Skede]),
    ..g.produkter.map(x => (
      [
        #text(size: 7pt, fill: grå, x.kod) \
        #x.namn
        #if x.vald != "" [\ #emph(x.vald)]
        #if x.detaljer.len() + x.arenden.len() > 0 [
          \ #text(size: 7.5pt, fill: grå)[#x.detaljer.join(" · ") #for a in x.arenden [#link(a.url)[\##a.nr] ]]
        ]
      ],
      [#x.antal], text(fill: farg.at(x.status), x.status), [#x.ansvarig], [#x.skede],
    )).flatten(),
  )
  ]
]

= Instanserna i modellen

Modellens instanser av varje produkt, efter typ (modellens beskrivning), med id.

#table(
  columns: (auto, 1.25fr, auto, 1fr),
  align: (left, left, center, left),
  table.header([Produkt], [Typ i modellen], [Antal], [Id]),
  ..r.grupper.map(g => g.produkter.filter(x => x.varianter.len() > 0).map(x => x.varianter.enumerate().map(((i, v)) => (
    if i == 0 { text(size: 8pt, x.kod) } else [], text(size: 8pt, v.typ), text(size: 8pt, str(v.antal)),
    text(size: 7.5pt, v.id),
  )).flatten()).flatten()).flatten(),
)
