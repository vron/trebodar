#let r = json("resultat.json")
#let p = r.projekt

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

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Rivning av befintligt fritidshus och nybyggnad], [*Upprättad*], p.upprattad,
  ..if p.granskad != "" { ([], [], [*Granskad*], p.granskad) },
)

= Omfattning och förutsättningar

Planen anger vilket avfall rivningen och nybyggnaden på #p.fastighet (ärende #p.arende) ger upphov till och hur det tas om hand. Den är underlag till kontrollplanen enligt plan- och bygglagen 10 kap. 6 § och följer avfallsförordningen (2020:614) 3 kap. Avsnitt 2 gäller rivningen och avsnitt 3 nybyggnaden.

*Platsen.* Tomten är öppen mot havet i väster och utsatt för vind. Längs fastigheten går en gångstig ned till havet och badplatsen. Området är av riksintresse för naturvård och friluftsliv och omfattas av hushållningsbestämmelserna för obruten kust. Lätt avfall som blåser bort hamnar snabbt i naturen och i havet. Hanteringen nedan är utformad för att förhindra det.

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [Roll], [Namn], [Ansvar],
  ..r.ansvar.map(a => if a.namn == "" { (table.cell(colspan: 2)[#a.roll], [#a.uppgift]) } else { ([#a.roll], [#a.namn], [#a.uppgift]) }).flatten(),
)

Avfallet lämnas till #p.mottagare, eller till annan mottagare med tillstånd för avfallsslaget.

= Rivning

== Underlag

Materialinventeringen (#p.inventering) hör till lovbeslutet och redovisar förekomst och uppskattade mängder av avfall i det befintliga huset: fritidshus i ett plan med mindre källare, byggt omkring 1950 och påbyggt 1980, byggnadsarea 63 m². Ingen asbest har påträffats. Hanteringen på plats preciseras nedan.

== Före rivning

Byggherren tömmer huset och tar själv bort fönster och dörrar, el- och VVS-installationer, inredning, hängrännor och stuprör, takstege, takpannor och takpapp. Fönster, dörrar, takpannor, kök, sanitetsporslin och vitvaror som kan användas igen säljs, sparas eller skänks bort. Övrigt sorteras enligt tabellen nedan och lämnas till återvinningscentral. Luftvärmepumpen flyttas till attefallshuset på tomten. Stommen bedöms inte kunna återanvändas, eftersom huset är i dåligt skick.

== Sortering och behandling

#table(
  columns: (auto, 1.5fr, 1.1fr, 1fr),
  align: (left, left, left, left),
  [Avfall], [Förekomst], [På plats], [Behandling],
  ..r.rivning.map(x => ([#x.avfall], [#x.forekomst], [#x.plats], [#x.behandling])).flatten(),
)

== Dispens från utsortering på plats

Avfallsförordningen 3 kap. 19 § kräver utsortering på plats. För trä och plast i byggnadsdelar med isolering begärs dispens enligt 3 kap. 33 §, så att delarna kan lämnas hela och sorteras hos en mottagare med tillstånd för blandat bygg- och rivningsavfall. Dispensen avser rivningen, planerad till #p.rivning_tid.

- *Bättre miljömässigt resultat.* Sortering på plats bryter ned isolering, plast och papp i lätta bitar som på den vindutsatta platsen sprids till naturen, havet och badplatsen.
- *Jämförbart återvinningsresultat.* Träet energiåtervinns och isoleringen deponeras, oavsett var sorteringen sker.
- *Liten omfattning.* Huset har en byggnadsarea på 63 m² och lite isolering.

= Nybyggnad

== Sortering på plats

Byggavfallet sorteras på plats i de avfallsslag som avfallsförordningen 3 kap. 19 § kräver, och farligt avfall hålls skilt från annat avfall. Behållarnas storlek anpassas efter skedet.

#table(
  columns: (auto, 1.3fr, 1fr, 1fr),
  align: (left, left, left, left),
  [Avfallsslag], [Avfall], [Behållare], [Behandling],
  ..r.nybygge.map(x => ([#x.fraktion], [#x.avfall], [#x.behallare], [#x.behandling])).flatten(),
)

== Vind

Lätt avfall, som plast, förpackningar och isoleringsspill, samlas i slutna säckar eller behållare med lock, eller inomhus när källaren är byggd. Behållarna töms innan de blir överfulla, och löst spill plockas upp löpande.

== Jord- och bergmassor

Sprängsten och schaktmassor som inte används på tomten transporteras bort av markentreprenören för återanvändning.

== Överblivet material

Överblivet byggmaterial i hela förpackningar eller längder sparas till senare skeden eller lämnas tillbaka till leverantören.
