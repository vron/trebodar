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
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 3pt, bottom: 3pt, it)
#show figure.caption: set text(size: 8.5pt)
#set figure(gap: 4pt)
#let liten(body) = text(size: 8.5pt, body)
#let b = r.bas

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Värmeberäkning, stationär 2D], [*Upprättad*], p.upprattad,
  ..if p.granskad != "" { ([], [], [*Granskad*], p.granskad) },
)

= Syfte

Nockbalkarna består av limträ med stålplåtar i över- och underkant. Över- och underplåten får olika temperatur när det är kallt ute och varmt inne, och skillnaden ger tvång i balken. Här beräknas plåtarnas temperatur vid stationärt vintertillstånd, med värmeflödet kring nocken i två dimensioner.

= Uppbyggnad

#figure(image("fig_geometri.svg", width: 100%), caption: [Tvärsnitt genom nocken. Modellen omfattar #r.g.tak_langd mm tak, mätt längs takfallet, på var sida om balken.])

Taket har takvinkeln #r.g.takvinkel°. Isoleringens ovansida ligger i balkens överkant. Under isoleringen finns en installationsspalt med glespanel och därunder gipsskivan, vars topp ligger strax under balkens underplåt.

#table(
  columns: (1fr, auto, auto, 2fr),
  align: (left, right, right, left),
  [Skikt], [Tjocklek (mm)], [λ (W/mK)], [Underlag],
  [Stålplåt S355], [#r.g.plat_t], [#r.m.stal], [SS-EN ISO 10456, konstruktionsstål],
  [Limträ, tvärs fibrerna], [#r.g.tra_h], [#r.m.limtra], [SS-EN ISO 10456, barrträ 500 kg/m³],
  [Hård träfiberskiva], [#r.g.masonit], [#r.m.masonit], [SS-EN ISO 10456, träfiberskiva ca 800 kg/m³],
  [Träfiberisolering Hunton Nativo], [#r.g.isolering], [#r.m.isolering], [Tillverkarens deklarerade värde],
  [Isolering med takbalkar 45×170 c/c #r.m.takbalk_cc], [#r.g.isolering], [#r.lam_iso], [Viktat: #r.f_tb % trä, parallella värmevägar],
  [Installationsspalt med glespanel 45 c/c #r.m.regel_cc], [#r.g.installation], [#r.lam_inst], [Luftskikt #r.lam_luft45 W/mK, #r.f_rg % trä],
  [Gipsskiva], [#r.g.gips], [#r.m.gips], [SS-EN ISO 10456, 900 kg/m³],
)

*Luftskikt.* Stillastående luft räknas med en ekvivalent värmekonduktivitet $λ = d slash R$, där värmemotståndet $R$ enligt SS-EN ISO 6946 tabell 8 (värmeflöde uppåt) inkluderar både ledning, konvektion och strålning i skiktet: #r.luft_d.zip(r.luft_R).slice(1).map(v => [#v.at(0) mm: #v.at(1)]).join(", ") m²K/W. I fickan mellan underplåten och gipsskivans topp är skiktet tunt och växer utåt från mitten, så λ beräknas där för den lokala tjockleken.

= Randvillkor

#table(
  columns: (auto, auto, 1fr),
  align: (left, right, left),
  [Rand], [Värde], [Underlag],
  [Luft i takets luftspalt], [#r.rd.T_ute °C], [Dimensionerande vinterfall],
  [Konvektion i luftspalten], [#r.rd.h_konv W/m²K], [Långsamt luftflöde, ca 0,1 m/s],
  [Strålning mot råsponten], [#r.rd.h_r W/m²K], [$4 sigma T^3 slash (2 slash epsilon - 1)$, $epsilon$ = #r.rd.eps, råsponten vid luftens temperatur],
  [Emissivitet, alla ytor], [#r.rd.eps], [Plåtarna antas målade. Blanka eller förzinkade plåtar ger mindre temperaturskillnad, se avsnitt 5],
  [Ytterytan totalt, $h_e$], [*#r.rd.h_ute W/m²K*], [Gäller isoleringens ovansida och överplåten],
  [Rumsluft], [#r.rd.T_inne °C], [],
  [Rumssidan, $h_i$], [*#r.rd.h_inne W/m²K*], [$R_"si"$ = #r.rd.Rsi m²K/W: naturlig konvektion och strålning, låg luftrörelse vid nocken],
  [Nockens mitt och snitten i taket], [adiabatiska], [Symmetri respektive endimensionellt flöde långt från balken],
)

SS-EN ISO 6946 anger $R_"si"$ = 0,10 m²K/W för värmeflöde uppåt och 0,13 för horisontellt flöde. Det högre värdet används här, eftersom luften står stilla i nocken. Luftspalten räknas med den uppskattade konvektionen och strålningen ovan. Andra värden prövas i avsnitt 5.

= Beräkningsmodell

Halva tvärsnittet modelleras med symmetri i nockens mitt. Stationär värmeledning löses med finita element med linjära triangelelement, #r.noder noder och #r.element element, med tätare nät i plåtarna och i tunna skikt. Takbalkar och glespanel är utsmetade i sina skikt enligt tabellen ovan. Balkens skruvar och plåtens kontakt med takbalkarna i tredje dimensionen ingår inte. Kontakten mellan skikten antas vara fullständig.

*Kontroller.*
- *Nät:* med fyra gånger mindre elementytor (#r.noder2 noder) blir temperaturskillnaden mellan plåtarna #r.dT_nat2 K mot #r.dT_nat1 K.
- *Energibalans:* värmeflödet in från rummet och ut till luftspalten stämmer överens, #r.q2d W per meter nock.
- *Endimensionell jämförelse:* vid modellens ände, långt från balken, är gipsytans temperatur #r.T_yta_fe °C. Motsvarande endimensionella beräkning ger #r.T_yta_1d °C ($U$ = #r.U1 W/m²K, $R$ = #r.R1 m²K/W).

#table(
  columns: (auto, auto),
  align: (left, right),
  [Skikt, endimensionellt], [R (m²K/W)],
  ..r.skikt.map(s => ([#s.namn], [#s.R])).flatten(),
  [*Summa*], [*#r.R1*],
)

= Resultat

#figure(image("fig_falt.svg", width: 100%), caption: [Temperaturfält, grundfallet. Ute #r.rd.T_ute °C i luftspalten, inne +#r.rd.T_inne °C.])

#grid(
  columns: (1fr, auto),
  column-gutter: 10pt,
  figure(image("fig_falt_zoom.svg", width: 100%), caption: [Nocken förstorad.]),
  figure(image("fig_profil.svg", width: 62mm), caption: [Temperatur längs nockens mitt.]),
)

Balken är en köldbrygga genom isoleringen. Överplåten ligger direkt mot luftspalten och får nära uteluftens temperatur. Underplåten värms från rummet genom den tunna luftfickan och gipsskivan. Stålets höga värmeledningsförmåga gör att temperaturen i respektive plåt är i det närmaste jämn: överplåten #r.To_min till #r.To_max °C, underplåten #r.Tu_min till #r.Tu_max °C.

#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right),
  [Fall], [$h_e$], [$h_i$], [Överplåt (°C)], [Underplåt (°C)], [Skillnad (K)], [Flöde (W/m)],
  ..r.fall.map(f => ([#f.namn], [#f.h_ute], [#f.h_inne], [#f.To], [#f.Tu], [*#f.dT*], [#f.q])).flatten(),
)
#liten[$h$ i W/m²K. Medeltemperatur i respektive plåt. Flöde per meter nock, hela tvärsnittet. Ute #r.rd.T_ute °C och inne +#r.rd.T_inne °C om inget annat anges. Vid blanka plåtar gäller ε för plåtarnas ytor, och fickan under underplåten räknas som ledning och strålning mellan plåten och gipsskivan.]

= Sammanfattning

Vid #r.rd.T_ute °C ute och +#r.rd.T_inne °C inne blir överplåten #b.To °C och underplåten #b.Tu °C. Skillnaden är *#b.dT K*. Räknat från limningstemperaturen +20 °C är ändringen #b.dTo K i överplåten och #b.dTu K i underplåten. Med rimliga variationer av ytövergångarna och plåtarnas ytbehandling ligger skillnaden mellan #r.dT_min och #r.dT_max K. Plåtarnas temperatur är i det närmaste jämn över bredden.
