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
#set heading(numbering: "1.1", supplement: [avsnitt])
#show heading.where(level: 1): it => {
  v(4pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#show heading.where(level: 2): it => block(above: 8pt, below: 4pt, text(size: 10pt, weight: "bold")[#counter(heading).display() #h(3pt) #it.body])
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 3pt, bottom: 3pt, it)
#show figure.caption: set text(size: 8.5pt)
#set figure(gap: 4pt)
#let liten(body) = text(size: 8.5pt, body)
#let rod = rgb("#b5463a")
#let eta(u, ok) = if ok { u } else { text(fill: rod, weight: "bold", u) }

#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Konstruktionsberäkning, balkmodell (FEM) av trästommen], [*Upprättad*], p.upprattad,
  [*Underlag*], [#p.underlag], ..if p.granskad != "" { ([*Granskad*], p.granskad) } else { ([], []) },
)

= Syfte och resultat

Handlingen visar hur lasterna går genom trästommen ovanför bjälklaget, från taket och väggarna ned till bjälklaget, och kontrollerar stommens alla delar och stabiliseringen. Hela stommen räknas i en balkmodell (FEM) som byggs ur modellens bärverk: reglar, syllar, hammarband, överstycken, stolpar, takbalkar, takstolar, nock- och dalbalkar och stålband, #r.modell.delar delar. Skivorna räknas inte: de horisontella lasterna tas av infällda stålband i kryss i väggarna och i takfallen. Varje grupp av likadana delar kontrolleras i alla #r.last.antal_komb lastkombinationer, och tabellen visar det högsta utnyttjandet i gruppen, som täcker de andra delarna i den. Nock- och dalbalkarna kontrolleras i K-01, takets anslutningar (hak, säten, takstolarnas spikplåtar) i K-03 och bjälklaget i K-05.

#table(
  columns: (1.6fr, auto, 1.25fr, auto, 1.3fr),
  align: (left, right, left, right, left),
  [Grupp], [Delar], [Styrande kontroll], [Utnyttjande], [Del, kombination],
  ..r.sammanf.map(s => ([#s.grupp], [#s.antal], [#s.kontroll], [#eta(s.eta, s.ok)], liten[#s.del, #s.komb])).flatten(),
  [Takbalkarnas nedböjning], [], [$w_"fin" <= L slash 300$], [#eta(r.bruks.tak.eta, r.bruks.tak.ok)], liten[#r.bruks.tak.del],
  [Väggarnas överkant i vind], [], [$u <= H slash 300$], [#eta(r.bruks.drift.eta, r.bruks.drift.ok)], liten[#r.bruks.drift.del, #r.bruks.drift.komb],
)

#if r.alla_ok [Alla delar och stålbanden klarar lasterna.] else [*Rött: delar som inte klarar lasterna* med stommen som den är i modellen; åtgärderna redovisas i avsnitt 7.]

= Bärverket och balkmodellen

#figure(image("fig_modell.svg", width: 100%), caption: [Balkmodellen: #r.modell.element balkelement mellan #r.modell.noder knutpunkter, #r.modell.band_vagg stålband i väggarna och #r.modell.band_tak i takfallen (blå), upplagen på bjälklaget (svarta). Röda delar har ett utnyttjande över 100 %.])

*Modellen.* Modellens bärverk (`./mod barverk`, delarnas läge, tvärsnitt och material) blir balkmodellen utan handpåläggning, så att beräkningen följer modellen: varje virkesdel blir en balk längs sin fiberriktning och tvärsnittets mitt, nock- och dalbalkarna balkar av limträ med stålplåtarna i full samverkan där plåtarna finns (limmade, K-01), och stålbanden dragstänger som bara tar drag. Delar som ligger an mot varandra förbinds där deras axlar är närmast varandra: en knutpunkt i den bärande delens axel, och leder (fria böjrotationer) i ändarna på delarna som ansluter; spikplåtar och korta bitar binder ihop delarna som ligger an mot dem. Syllarna och stolparnas fötter står fast på bjälklaget (förankrade); reaktionerna är lasterna till bjälklaget och förankringen.

#table(
  columns: (1.6fr, auto, 1.4fr, auto),
  align: (left, right, left, left),
  [Grupp], [Antal], [Tvärsnitt (mm)], [Material],
  ..r.modell.grupper.map(g => ([#g.namn], [#g.antal], [#g.dim], [#g.mat])).flatten(),
)

*Förutsättningar.* Reglarna och stolparna i väggarna och takbalkarna knäcker bara i sin styva riktning: skivorna och läkten håller dem i den veka (de räknas inte för stabiliseringen). Fristående stolpar av flera reglar är ihopskruvade och verkar som ett tvärsnitt (som K-03). Klimatklass 1, säkerhetsklass 2 ($gamma_d$ = #r.kombination.gamma_d).

= Laster

Lasterna läggs på stommens ytor och förs till de bärande delarna: taket i rutor om 100 × 100 mm till den närmaste takbalken, takstolens ytterbalk eller nock- och dalbalken, väggarna till den närmaste delen i väggen.

- *Egentyngd* G: delarna med #r.last.rho kg/m³, taket #r.last.g_tak kN/m² takyta (#r.last.kg_tak kg/m²: F-01 utan takbalkarna, som är delar i modellen, och med #r.last.tillagg.at(0).skikt), ytterväggarna #r.last.vagg_ytter och innerväggarna #r.last.vagg_inner kN/m² vägg.
- *Snö* (F-01, $s_k$ = #r.last.sk kN/m²): S1 med $mu$ = #r.last.mu_dal på takfallen mot dalarna och #r.last.mu_takfot mot takfoten (som K-03, på säker sida), S2 och S3 osymmetriska.
- *Vind* (F-01, $q_p$ = #r.last.qp kN/m², $h$ = #r.last.h m): utvändiga formfaktorer på väggarna (SS-EN 1991-1-4 tabell 7.1) och taken (7.4a–b, sadeltak 30°, varje huskropp för sig), i fyra riktningar, med sug och tryck på lovartsidan och invändig vindlast $c_"pi"$ +0,2 och −0,3.

#table(
  columns: (auto, 1fr, auto, auto, auto),
  align: (left, left, right, right, right),
  [Fall], [Beskrivning], [$F_x$ (kN)], [$F_y$ (kN)], [$F_z$ (kN)],
  ..r.last.fall.map(f => ([#f.namn], liten[#f.text], [#f.F.at(0)], [#f.F.at(1)], [#f.F.at(2)])).flatten(),
)

*Kombinationer.* #r.last.antal_komb i brottgränstillståndet: 6.10a och 6.10b med $gamma_d$, snö och vind som huvudlast med den andra som samverkande ($psi_0$ = #r.kombination.psi0_sno respektive #r.kombination.psi0_vind) och vind med gynnsam egentyngd (lyft, förankring); #r.last.antal_bruks i bruksgränstillståndet. $k_"mod"$ = #r.kmod.G (egentyngd), #r.kmod.S (med snö) och #r.kmod.W (med vind).

= Lastvägar

== Vertikala laster till bjälklaget

Lasterna i lastfallen är lika med reaktionerna i upplagen (jämvikt). Stolparna under nock- och dalbalkarna bär enligt balkmodellen (karakteristiska G och S1 och dimensionerande $N_"Ed"$) jämfört med lasten som K-05 dimensionerar bjälklaget för. Väggar som står under balkarna bär en del av balkarnas last, så stolparna där får mindre än i K-05.

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  [Stolpe], [G (kN)], [S1 (kN)], [$N_"Ed"$ (kN)], [K-05 (kN)], [Kvot],
  ..r.stolpar.map(s => ([#s.namn], [#s.G], [#s.S], [#s.Ned], [#s.K05], [#if s.over { text(fill: rod, weight: "bold", s.kvot) } else { s.kvot }])).flatten(),
)

== Horisontella laster till bjälklaget

#figure(image("fig_plan.svg", width: 100%), caption: [Väggarna och stålbanden i plan: banden i väggarna (tjocka) och i takfallen (tunna) och nock- och dalbalkarna.])

Väggarnas andel av vindlasten (karakteristisk, summan av upplagens horisontella reaktioner per vägg):

#grid(columns: (1fr, 1fr), gutter: 8pt,
  ..r.riktningar.map(v => table(
    columns: (auto, auto, auto),
    align: (left, right, right),
    [Vind #v.riktning, #v.tot kN], [kN], [Andel],
    ..v.vaggar.map(w => ([#w.vagg], [#w.kN], [#w.andel])).flatten(),
  )),
)

= Kontroller

Virket (SS-EN 1995-1-1): normalkraft och böjning (6.17–6.20, med knäckning 6.23–6.24, $k_m$ = #r.kontroll.k_m), tvärkraft och vridning (6.13–6.15, $k_"cr"$ = #r.kontroll.k_cr) i varje balkelement med krafterna längs elementet, och tryck vinkelrätt fibrerna där reglar och stolpar står på syllar ($k_"c,90"$ = #r.kontroll.k_c90) och under hammarband (1,5). Varje rad är gruppens högsta utnyttjande.

#table(
  columns: (1.25fr, 1.1fr, auto, 1.25fr, 1.6fr),
  align: (left, left, right, left, left),
  [Grupp], [Kontroll], [$eta$], [Del], [Krafter],
  ..r.detalj.filter(d => d.kontroll != "Spik i bandets ände").map(d => ([#d.grupp], [#d.kontroll], [#eta(d.eta, d.ok)], liten[#d.del], liten[#if "Nc" in d [N#sub[c] #d.Nc kN ] #if "My" in d [M#sub[y] #d.My, M#sub[z] #d.Mz kNm ] #if "V" in d [V #d.V kN ] #if "N" in d and not ("Nc" in d) [N #d.N kN]  · #d.komb])).flatten(),
)

= Stålband och förankring

Stålband #r.band.b × #r.band.t mm S350GD+Z275, infällda och spikade med #r.band.spik i varje del de korsar: dragkraftskapacitet $N_"t,Rd"$ = #r.band.NtRd kN (nettotvärsnittet vid hålen ⌀#r.band.d0, SS-EN 1993-1-3). Spiken i bandets ände (SS-EN 1995-1-1 8.2.3, tunn stålplåt): $F_"v,Rk"$ = #r.band.FvRk kN per spik.

#table(
  columns: (1.5fr, auto, auto, auto, 1fr),
  align: (left, right, right, right, left),
  [Band], [$N_"Ed"$ (kN)], [$F_"v,Rd"$ (kN)], [Spik per ände], [Del],
  ..r.band.rader.map(b => ([#b.grupp], [#b.N], [#b.FvRd], [#b.n], liten[#b.del])).flatten(),
)

*Förankringen* i bjälklaget: största lyftkraft #r.forankring.lyft kN (#r.forankring.lyft_del, #r.forankring.lyft_komb) och största horisontalkraft #r.forankring.hor kN i ett upplag (#r.forankring.hor_del). Per vägg:

#table(
  columns: (auto, auto, auto),
  align: (left, right, right),
  [Vägg], [Största lyft i ett upplag (kN)], [Horisontalkraft, summa (kN)],
  ..r.forankring.vaggar.map(v => ([#v.vagg], [#v.lyft], [#v.skjuv])).flatten(),
)

= Bruksgränstillståndet

Takbalkarna: $w_"fin"$ = #r.bruks.tak.wfin mm ($w_G$ #r.bruks.tak.wG mm med krypning och $w_S$ #r.bruks.tak.wS mm) över spannet #r.bruks.tak.L mm, #r.bruks.tak.del: #eta(r.bruks.tak.eta, r.bruks.tak.ok) av $L slash 300$. Väggarnas överkant i karakteristisk vind: #r.bruks.drift.u mm vid höjden #r.bruks.drift.H mm (#r.bruks.drift.del, #r.bruks.drift.komb): #eta(r.bruks.drift.eta, r.bruks.drift.ok) av $H slash 300$.

= Förutsättningar och åtgärder

- Stålbanden spikas i varje del de korsar och i ändarna med spiken i avsnitt 5, och förankras i bjälklaget för krafterna i avsnitt 5.
- Skivorna (utegips, gips, råspont) monteras som vanligt; de stagar reglarna och takbalkarna i den veka riktningen men räknas inte för stabiliseringen.
#if not r.alla_ok [- Delarna i rött i avsnitt 1 och 5 ska förstärkas eller ändras i modellen, och K-04 räknas om.]
