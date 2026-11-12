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
  ..if p.granskad != "" { ([], [], [*Granskad*], p.granskad) },
)

= Syfte och resultat

Handlingen visar hur lasterna går genom trästommen ovanför bjälklaget, från taket och väggarna ned till bjälklaget, och kontrollerar stommens alla delar och stabiliseringen. Hela stommen räknas i en balkmodell (FEM): reglar, syllar, hammarband, överstycken, stolpar, takbalkar, takstolar, nock- och dalbalkar och stålband. De horisontella lasterna tas av infällda stålband i kryss i väggarna och i en del av takfallens fält och av skivorna där de räknas som skjuvskivor: utegipsen, OSB:n direkt på reglarna i de bärande innerväggarna och i gaveln 1SV och råsponten i takfallen (@skivor). Varje grupp av likadana delar kontrolleras i alla #r.last.antal_komb lastkombinationer, och tabellen visar det högsta utnyttjandet i gruppen. Nock- och dalbalkarna kontrolleras i K-01, takets anslutningar (hak, säten, takstolarnas spikplåtar) i K-03 och bjälklaget i K-05.

#table(
  columns: (1.6fr, 1.25fr, auto, 1.3fr),
  align: (left, left, right, left),
  [Grupp], [Styrande kontroll], [Utnyttjande], [Del, kombination],
  ..r.sammanf.map(s => ([#s.grupp], [#s.kontroll], [#eta(s.eta, s.ok)], liten[#s.del, #s.komb])).flatten(),
  [Takbalkarnas nedböjning], [$w_"fin" <= L slash 300$], [#eta(r.bruks.tak.eta, r.bruks.tak.ok)], liten[#r.bruks.tak.del],
  [Väggarnas överkant i vind], [$u <= H slash 300$], [#eta(r.bruks.drift.eta, r.bruks.drift.ok)], liten[#r.bruks.drift.del, #r.bruks.drift.komb],
  ..r.forankring.sammanf.map(s => ([#s.grupp], [#s.kontroll], [#eta(s.eta, s.ok)], liten[#s.del])).flatten(),
)

#if r.alla_ok [Alla delar och stålbanden klarar lasterna.] else [*Rött: delar som inte klarar lasterna* med stommen som den är i modellen.#if r.sektioner.len() > 0 [ Snitt genom dem finns i @snitt.]]

= Bärverket och balkmodellen <modell>

#figure(image("fig_modell.svg", width: 100%), caption: [Balkmodellen: #r.modell.element balkelement mellan #r.modell.noder knutpunkter, #r.modell.band_vagg stålband i väggarna och #r.modell.band_tak i takfallen (blå), upplagen på bjälklaget (svarta). Röda delar har ett utnyttjande över 100 %.])

*Modellen.* Balkmodellen är det bärande systemet ritat på systemlinjer. Varje virkesdel blir en balk längs sin fiberriktning och tvärsnittets mitt. Delar som ligger an mot varandra längs en sträcka, sida vid sida eller ovanpå varandra (reglarna i en stolpe, hammarbandet och takstolens underram, ytterbalken på diagonalen), får den största delens systemlinje och verkar tillsammans utan samverkan; last på en sådan del går till den största. Delar förbinds där deras systemlinjer möts: knutpunkten ligger på den viktigaste delen som går igenom den (syll, balk och hammarband före reglar och diagonaler, före takbalkar), och en del som slutar där förlängs längs sin axel till knutpunkten och har en led (fria böjrotationer). Knutpunkter närmare varandra längs en del än halva delens höjd är en knutpunkt, men två ställen längs en nock- eller dalbalk längre isär än så är alltid två. Varje del är rak mellan sina yttersta knutpunkter (en fot på bjälklaget räknas som en), och takstolarnas fötter och topp är en knutpunkt var, som i K-03. Nock- och dalbalkarna är limträ med stålplåtarna i full samverkan där plåtarna finns (limmade, K-01), stålbanden dragstänger som bara tar drag. Syllarna och stolparnas fötter står fast på bjälklaget; reaktionerna är lasterna till bjälklaget och förankringen.

*Takstolarna och gavlarna.* Takstolarnas ståndare och spikreglar (#r.modell.sekundara delar) ingår inte: de sitter för skivorna och fästs när taket är lagt, så att takstolen bär som en triangel av diagonaler och underram och för nockbalkens stöd och takremsan till fötterna (K-03). Gavelns överkant (hammarbandet och underramen) och takstolens överram hålls raka i sidled av gavelns och takets skivor, mellan gavelns hörn och mellan takstolens fot och topp, och skivorna för krafterna dit, som mest #r.gavel.max kN i en knutpunkt (#r.gavel.gavel, #r.gavel.komb). Det är en förutsättning (@atgarder).

#table(
  columns: (1.6fr, auto, 1.4fr, auto),
  align: (left, right, left, left),
  [Grupp], [Antal], [Tvärsnitt (mm)], [Material],
  ..r.modell.grupper.map(g => ([#g.namn], [#g.antal], [#g.dim], [#g.mat])).flatten(),
)

*Förutsättningar.* Reglarna och stolparna i väggarna och takbalkarna knäcker bara i sin styva riktning: skivorna och läkten håller dem i den veka. I ett hörn, där en vinkelrät väggs regel ligger an längs minst halva höjden (också en lätt väggs), är regeln eller stolpen stagad åt båda hållen. Fristående stolpar av flera reglar är ihopskruvade och verkar som ett tvärsnitt (som K-03). Klimatklass 1, säkerhetsklass 2 ($gamma_d$ = #r.kombination.gamma_d).

= Laster

Lasterna läggs på stommens ytor och förs till de bärande delarna: taket i rutor om 100 × 100 mm till den närmaste takbalken, takstolens ytterbalk eller nock- och dalbalken, väggarna till den närmaste delen i väggen, och den nedre delen av dörrar och glaspartier direkt till bjälklaget.

- *Egentyngd* G: delarna med #r.last.rho kg/m³, taket #r.last.g_tak kN/m² takyta (#r.last.kg_tak kg/m²: F-01 utan takbalkarna, som är delar i modellen), ytterväggarna #r.last.vagg_ytter och innerväggarna #r.last.vagg_inner kN/m² vägg.
- *Snö* (F-01, $s_k$ = #r.last.sk kN/m²): S1 med $mu$ = #r.last.mu_dal på takfallen mot dalarna och #r.last.mu_takfot mot takfoten (som K-03, på säker sida), S2 och S3 osymmetriska.
- *Vind* (F-01, $q_p$ = #r.last.qp kN/m², $h$ = #r.last.h m): formfaktorerna efter SS-EN 1991-1-4, väggarna för hela huset (7.2.2) och taken för varje huskropp som sadeltak (7.2.5). Med vinden vinkelrätt mot nockarna (x) är taken ett tak med flera skepp (7.2.7, figur 7.10 c): zonerna F, G och J bara på den första kroppen i vindens väg, och formfaktorn gånger 0,6 på läfallen bakom den första kroppen och på lovartsfallen bakom den andra, där kropparna står bakom varandra. Sadeltakets formfaktorer används också bakom dalarna (större vågrät kraft än det tråggformade takets).

*Kombinationer.* #r.last.antal_komb i brottgränstillståndet: 6.10a och 6.10b med $gamma_d$, snö och vind som huvudlast med den andra som samverkande ($psi_0$ = #r.kombination.psi0_sno respektive #r.kombination.psi0_vind) och vind med gynnsam egentyngd (lyft, förankring); #r.last.antal_bruks i bruksgränstillståndet. $k_"mod"$ = #r.kmod.G (egentyngd), #r.kmod.S (med snö) och #r.kmod.W (med vind).

= Lastvägar

== Vertikala laster till bjälklaget

Reaktionerna i upplagen är lika med lasterna (jämvikt). Stolparna bär enligt balkmodellen: karakteristiska G och S1, dimensionerande $N_"Ed"$ med snö som huvudlast jämfört med lasten som K-05 dimensionerar bjälklaget för, och det största $N_"Ed"$ i alla kombinationer (med vind som huvudlast får stolparna i stålbandens fält bandens vertikala kraft). Väggar som står under nock- och dalbalkarna bär en del av balkarnas last, som K-01 och K-05 lägger på stolparna och takstolarna. Rött: stolpar där balkmodellen ger mer än K-05.

#grid(columns: (1.35fr, 1fr), gutter: 10pt,
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right, right),
    [Stolpe], [G], [S1], [$N_"Ed"$], [K-05], [Kvot], [Max],
    ..r.stolpar.map(s => ([#s.namn], [#s.G], [#s.S], [#s.Ned], [#s.K05], [#if s.over { text(fill: rod, weight: "bold", s.kvot) } else { s.kvot }], [#s.Nmax])).flatten(),
  ),
  [
    #table(
      columns: (auto, auto, auto, auto, auto),
      align: (left, right, right, right, right),
      table.header([Takstol], [$N_"d"$], [K-03], [$H_"d"$], [K-03]),
      ..r.takstolar.map(t => ([#t.namn], [#t.N], [#t.N03], [#t.H], [#t.H03])).flatten(),
    )
    #liten[Takstolarna: tryckkraften i diagonalen och dragkraften i underramen (kN, snö som huvudlast) i balkmodellen och i K-03, där takstolen ensam bär nockbalkens stöd och takremsan till fötterna. Krafterna i stolparna i kN.]
  ],
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

= Skivverkan <skivor>

Skivorna räknas som skjuvskivor i balkmodellen: varje regelfack eller fack mellan takbalkar som skivan täcker är en skiva med hörnen i facket knutpunkter, med styvhet för skjuvvinkeln och en bärförmåga, elastisk–idealplastisk (skivan tar som mest bärförmågan, sedan tar banden och de andra skivorna resten). Antal skivor: #r.skivor.antal.utegips utegips, #r.skivor.antal.osb OSB och #r.skivor.antal.raspont råspont.

- *Utegipsen* på ytterväggarnas utsida, i facken utan öppning: skruv c/c #r.skivor.ug.s mm längs kanterna, $F_k$ = #r.skivor.ug.F_k N per skruv, styvhet #r.skivor.ug.K N/mm per meter vägg.
- *OSB direkt på reglarna* (#r.skivor.osb.produkt, spik c/c #r.skivor.osb.s mm längs kanterna och #r.skivor.osb.s_mitt mm längs mellanreglarna): i de bärande innerväggarna på båda sidor och på insidan av gaveln 1SV, som har reglar 45×145 och OSB:n och gipsen direkt på reglarna utan installationsskikt. OSB:n går i gavelns hörn fram till långsidans stomme, på hörnstolpens inre regel. $F_k$ = #r.skivor.osb.F_k N per spik (SS-EN 1995-1-1 8.2.2), $K_"ser"$ = #r.skivor.osb.K_ser N/mm, styvhet #r.skivor.osb.K N/mm per meter vägg. De andra ytterväggarnas invändiga skivor sitter på installationsskiktet och räknas inte.
- Facken bildar segment mellan öppningarna; ett segment kortare än $h slash 4$ räknas inte och ett kortare än $h slash 2$ har faktorn $c = l slash (h slash 2)$ (9.2.4.2). I 1SV, med utegips utanför och OSB innanför, räknas #r.skivor.andel av den svagare sidans bärförmåga (utegipsen; förbanden har olika förskjutningsmodul, 9.2.4.2 (5)).

== Råsponten i takfallen

*Utförande.* #r.raspont.produkt. Råsponten ligger på ströläkten 34×45 längs takbalkarna (på hårdboarden) och spikas i den, så att kraften går från brädan via spikparet till ströläkten och takbalken; ströläkten ska därför vara fäst i varje takbalk. Spikparet sitter i brädans täckande bredd $w$ = #r.raspont.w mm med avståndet $a$ = #r.raspont.a mm (20 mm från kanterna, minst $7 d$ för spik som belastas mot kanten, 8.3.1.2 tabell 8.2). Brädorna ska skarvas på ströläkt, med skarvarna förskjutna.

*Modell.* Brädorna går vinkelrätt mot takbalkarna, så skivverkan uppstår bara genom att varje bräda vrids mot takbalkarna och spikparet tar ett moment (stela brädor; Brignola, Pampanin och Podestà 2009, NZSEE Bulletin 42(3), ekv. 3 och NZSEE:s riktlinjer). Not och spont och friktionen mellan brädorna räknas inte, och inte heller fasthållningen från takplåten. Spiken $d$ = #r.raspont.d mm i brädan #r.raspont.t mm mot ströläkten #r.raspont.t2 mm: $F_"v,Rk"$ = #r.raspont.F_k N (8.6, utan linverkan), $K_"ser"$ = #r.raspont.K_ser N/mm och $K_u$ = #r.raspont.K_u N/mm (tabell 7.1). Spikparets vridstyvhet $k_r = K_u a^2 slash 2$ = #r.raspont.k_r Nm/rad och bärförmåga $M_R = F a$. Ett fack $b times L$ mellan takbalkarna har $L slash w$ spikpar, alltså skjuvstyvheten $G t = k_r slash (b w)$ = #r.raspont.Gt N/mm och bärförmågan $q = F a slash (b w)$ = #r.raspont.qRk kN/m karakteristiskt (#r.raspont.qRd kN/m dimensionerande med vind) vid $b$ = 600 mm. Takbalkarnas noder vid upplaget (hammarbandet, dalbalken eller takstolens fot) och i nocken är facket hörn; facken över takfönstren ingår inte.

*Jämförelse med stålbanden.* Takfallens skjuvstyvhet $G t$ i planet (N/mm). Banden: kryssen i fälten, en diagonal verksam, $E A (b h)^2 slash L^3$ per fält utan förskjutning i bandens ändar (som i balkmodellen; med spikarnas förskjutning blir banden vekare). FEMA 356 anger 0,35 kN/mm för enkel rak brädbeklädnad ur prov (med friktion och spikarnas fasthållning, @raspont-kanslighet).

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right),
  [Takfall], [Fack], [Banden], [Råsponten], [Andel], [FEMA 356], [Andel],
  ..r.raspont.tak.map(t => ([#t.takfall], [#t.fack], [#t.Gt_band], [#t.Gt_rasp], [#t.kvot], [#t.Gt_fema], [#t.kvot_fema])).flatten(),
)

Råsponten är alltså mycket vekare än banden och tar nästan ingenting av vindlasten: som mest #r.raspont.V_max kN i ett takfall.

=== Känslighet <raspont-kanslighet>

Väggarnas horisontella reaktion i karakteristisk vind i x (kN) och väggens högsta utnyttjande (delar och band, brottgränstillståndet), utan råsponten, med den räknade råsponten och med FEMA 356:s styvhet #r.raspont.G_d N/mm (bärförmågan som ovan):

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right, right, right),
  table.header([], table.cell(colspan: 3)[Vind +x (kN)], table.cell(colspan: 3)[Vind −x (kN)], table.cell(colspan: 3)[Utnyttjande],
    [Vägg], [utan], [räknad], [FEMA], [utan], [räknad], [FEMA], [utan], [räknad], [FEMA]),
  ..r.raspont.vaggar.map(v => ([#v.vagg], [#v.at("Rutan+x")], [#v.at("Rmed+x")], [#v.at("Rfema+x")], [#v.at("Rutan−x")], [#v.at("Rmed−x")], [#v.at("Rfema−x")], [#eta(v.eta_utan, v.ok_utan)], [#eta(v.eta_med, v.ok_med)], [#eta(v.eta_fema, v.ok_fema)])).flatten(),
)

Väggarnas reaktioner ändras med högst #r.raspont.dR kN och utnyttjandena med högst #r.raspont.deta procentenheter, också med FEMA:s styvhet: stålbanden styr takfallen och fördelningen mellan gavlarna NO och SV och 2C. Råsponten räknas med den konservativa styvheten och bärförmågan ovan.

= Kontroller

Virket (SS-EN 1995-1-1): normalkraft och böjning (6.17–6.20, med knäckning 6.23–6.24, $k_m$ = #r.kontroll.k_m), tvärkraft och vridning (6.13–6.15, $k_"cr"$ = #r.kontroll.k_cr) i varje balkelement med krafterna längs elementet, och tryck vinkelrätt fibrerna där reglar och stolpar står på syllar ($k_"c,90"$ = #r.kontroll.k_c90) och under hammarband (1,5). Varje rad är gruppens högsta utnyttjande.

#table(
  columns: (1.25fr, 1.1fr, auto, 1.25fr, 1.6fr),
  align: (left, left, right, left, left),
  [Grupp], [Kontroll], [$eta$], [Del], [Krafter],
  ..r.detalj.filter(d => d.kontroll != "Spik i bandets ände").map(d => ([#d.grupp], [#d.kontroll], [#eta(d.eta, d.ok)], liten[#d.del], liten[#if "Nc" in d [N#sub[c] #d.Nc kN ] #if "My" in d [M#sub[y] #d.My, M#sub[z] #d.Mz kNm ] #if "V" in d [V #d.V kN ] #if "N" in d and not ("Nc" in d) [N #d.N kN]  · #d.komb])).flatten(),
)

#if r.sektioner.len() > 0 [
== Delarna som inte klarar lasterna <snitt>

Snitt genom stommen där delar inte klarar lasterna, sedda från väggens utsida, med delarna ur modellen och krafterna i balkmodellen i den styrande kombinationen.

#for s in r.sektioner [
  #figure(image(s.fil, width: 100%), caption: [#s.text])
]
]

= Stålband <band>

Stålband #r.band.b × #r.band.t mm S350GD+Z275, infällda och spikade med #r.band.spik i varje del de korsar: dragkraftskapacitet $N_"t,Rd"$ = #r.band.NtRd kN (nettotvärsnittet vid hålen ⌀#r.band.d0, SS-EN 1993-1-3). Spiken i bandets ände (SS-EN 1995-1-1 8.2.3, tunn stålplåt): $F_"v,Rk"$ = #r.band.FvRk kN per spik.

#table(
  columns: (1.5fr, auto, auto, auto, 1fr),
  align: (left, right, right, right, left),
  [Band], [$N_"Ed"$ (kN)], [$F_"v,Rd"$ (kN)], [Spik per ände], [Del],
  ..r.band.rader.map(b => ([#b.grupp], [#b.N], [#b.FvRd], [#b.n], liten[#b.del])).flatten(),
)

= Förankring i bjälklaget <forankring>

Balkmodellen håller varje syllnod och stolpfot fast i bjälklaget; reaktionerna där är krafterna som förankringen ska ta. #r.forankring.n_lyft av #r.forankring.n_upplag upplag lyfter i någon kombination, som mest #r.forankring.lyft kN (#r.forankring.lyft_del, #r.forankring.lyft_komb), och den största horisontalkraften i ett upplag är #r.forankring.hor kN (#r.forankring.hor_del).

*Lastvägen.* Syllen hålls ned av betongbultarna genom den (modellen, minst en bult per syllbit, högst 300 mm från ändarna och 1 200 mm isär, \#88). Når en lodrät bult inte betongen med minst 35 mm till kanten (ytterväggarna står 30 mm utanför plattans kant, också vid plattan på marks fria kanter, där L-elementens rygg är kantisoleringen) borras den snett inåt, 45° eller 60° från lodlinjen, med snedbricka#r.forankring.sneda_text vid ytterväggarna går den snett in längs väggen förbi beslagets andra bult. Mellan bultarna bär syllen lyftet från reglarna och banden i böjning: fritt upplagd mellan två bultar och konsol utanför den yttersta. Regeln hålls i syllen av #r.forankring.skruv snett genom regelns fot. Där syllen, bultarna eller skruvarna inte räcker har modellen vinkelbeslag #r.forankring.beslag på regelns eller stolpens fria sidor längs väggen (i hörnen på den vinkelräta väggens regel), fullt utskruvade i regeln och syllen, med en eller två betongbultar genom beslagets hål och syllen ned i plattan, och där inte ens två beslag räcker ett förankringsbeslag #r.forankring.halldon_namn på regelgruppens insida. Stolpar som står direkt på plattan har beslagen på plattan, för både lyftet och sidkraften. Beslagen för upplagets lyft direkt till sina bultar; syllen bär lyftet vid de andra upplagen. En syllbit utan egna bultar (ett kort stycke mellan reglarna) hålls av beslagen på den, vars bultar eller ankare går genom syllen: de andra upplagen på biten lyfter genom dem, och på säker sida tar varje sådant beslag hela deras lyft.

Beslagen står i modellen (#r.forankring.n_beslag beslag vid #r.forankring.n_upplag_beslag upplag). Kravet räknas för varje upplag i alla kombinationer: beslag vid de upplag som lyfter mest, ett beslag, två eller två med två bultar vardera, tills syllarna, bultarna och skruvarna räcker. Kontrollen prövar modellens beslag mot lyftet och syllarna och bultarna med upplagen utan beslag.

*Bärförmågor* (vind, $k_"mod"$ #r.kmod.W):
- *Betongbulten* M#r.forankring.d med bricka #r.forankring.bricka mm: krav på produkten $N_"Rd"$ ≥ #r.forankring.NRd kN och $V_"Rd"$ ≥ #r.forankring.VRd kN i sprucken betong, också vid ytterväggarnas kantavstånd och snett borrad (IN-01). Brickans tryck mot syllen, $f_"c,90,d" A_"ef"$ (6.1.5, 30 mm längs fibrerna på var sida): #r.forankring.Rbricka kN. En sned bult bär lodrätt bärförmågan gånger cos(lutningen).
- *Bulten i syllen* i sidled (8.2.3, bulten fast i betongen som en tjock plåt, syllen 45 mm, $f_"h,k"$ = #r.forankring.fhk MPa): $F_"v,Rk"$ = #r.forankring.Fvk kN, $F_"v,Rd"$ = #r.forankring.Fvd kN per bult. Horisontalkraften i en syllbit delas på dess bultar och beslagens bultar.
- *Syllen* flatt: $M_"Rd" = f_"m,d" k_h b h^2 slash 6$ med $h$ = 45 mm och $b$ = väggens bredd.
- *Regeln i syllen*: #r.forankring.skruv, $f_"ax,k"$ 11 MPa och 40 mm gänga i syllen: #r.forankring.Rskruv kN.
- *Vinkelbeslaget* (ETA-06/0106, databladet: två beslag $R_"1,k"$ = #r.forankring.R1k kN och $R_"2/3,k"$ = #r.forankring.R23k kN, med skruv CSA5,0×40, inte spik): #r.forankring.R1 kN uppåt och #r.forankring.R23 kN i sidled per beslag ($gamma_M$ 1,35). Bulten genom beslaget får beslagets kraft gånger #r.forankring.band för beslagets bändning. Ett beslag med en lodrät bult bär #r.forankring.Rkat.at(0) kN, två #r.forankring.Rkat.at(1) kN och två med två bultar vardera #r.forankring.Rkat.at(2) kN.
- *Förankringsbeslaget* #r.forankring.halldon_namn (ETA-23/0813, databladet): $R_"1,k"$ = #r.forankring.hd_tra kN i träet med full spikning, #r.forankring.hd_stal kN i stålet och $R_"1,d"$ = #r.forankring.hd_betong kN i sprucken betong: #r.forankring.Rhd kN.

*Syllbitarna.* Böjningen och bultarnas drag av lyftet som syllen bär (vid upplagen utan beslag), och horisontalkraften per bult:

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right, right, right, right, right),
  [Vägg], [Syll], [Längd (mm)], [Bultar], [Böjning], [Bultens drag], [$H$ (kN)], [per bult (kN)], [Skjuvning], [Beslag],
  ..r.forankring.bitar.map(b => ([#b.vagg], [#b.syll], [#b.langd], [#b.bultar], [#eta(b.M, b.ok)], [#b.N], [#b.H], [#b.V], [#b.uH], [#b.beslag])).flatten(),
)

#liten[Bultarnas drag är andel av #r.forankring.Nbricka kN (betongbulten eller brickan, lodrätt för de sneda). Största drag i en bult #r.forankring.N_max kN, största skjuvning #r.forankring.V_max kN.]

#figure(image("fig_forankring.svg", width: 100%), caption: [Förankringen i plan: betongbultarna genom syllarna och modellens beslag.])

*Beslagen.* $u$ från väggens början (K-05:s system, väggens origo); kravet är beslagen som upplaget behöver, och utnyttjandet är lyftet (och för stolparna sidkraften) mot modellens beslag:

#text(size: 8pt)[#table(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, left, left, right, left),
  [Upplag], [$u$ (mm)], [Lyft (kN)], [$H$ (kN)], [I modellen], [Krav], [Utnyttjande], [Kombination],
  ..r.forankring.beslag_rader.map(b => ([#b.del], [#b.u], [#b.lyft], [#b.H], [#b.modell], [#b.krav], [#eta(b.eta, b.ok)], [#b.komb])).flatten(),
)]

= Bruksgränstillståndet

Takbalkarna: $w_"fin"$ = #r.bruks.tak.wfin mm ($w_G$ #r.bruks.tak.wG mm med krypning och $w_S$ #r.bruks.tak.wS mm) över spannet #r.bruks.tak.L mm, #r.bruks.tak.del: #eta(r.bruks.tak.eta, r.bruks.tak.ok) av $L slash 300$. Väggarnas överkant i karakteristisk vind: #r.bruks.drift.u mm vid höjden #r.bruks.drift.H mm (#r.bruks.drift.del, #r.bruks.drift.komb): #eta(r.bruks.drift.eta, r.bruks.drift.ok) av $H slash 300$.

= Förutsättningar och åtgärder <atgarder>

- Stålbanden spikas i varje del de korsar och i ändarna med spiken i @band. Syllarna, reglarna och stolparna förankras i bjälklaget enligt @forankring: betongbultarna genom syllarna, skruvarna i reglarnas fötter, vinkelbeslagen och de särskilda förankringsbeslagen.
- Skivorna som räknas som skjuvskivor (@skivor) fästs som där: utegipsen, OSB:n i de bärande innerväggarna och i gaveln 1SV (fram till hörnstolparna) och råsponten med två spikar per bräda och ströläkt, ströläkten fäst i varje takbalk. Övriga skivor monteras som vanligt; alla stagar reglarna och takbalkarna i den veka riktningen.
- Gavelns och takets skivor håller gavelns överkant och takstolens överram i sidled och för krafterna i @modell till gavelns hörn och till takplanet.
- Regeln 45×95 på innerväggen 1A:s hammarband (1A-H02) ligger an mot takbalken 1SO-T07 och för takfallets kraft i x till 1A längs lutningen (balkmodellen har dem på en systemlinje). Förbanden tar takbalkens kraft vid takfoten, ca 11 kN längs lutningen: skruv 5×90 c/c 200 ned i hammarbandet 1A-H01 och skruv 5×140 c/c 200 vågrätt genom regeln in i takbalken, förborrat, mitt i anliggningen (18 mm över takbalkens underkant, kantavstånd minst 3$d$, SS-EN 1995-1-1 tabell 8.2), $F_"v,Rd"$ ≈ 1,1 kN per skruv (8.6, k#sub[mod] 0,9), 10 skruv i varje förband.
- Takstolarnas ståndare bär inte takstolen: de fästs när taket är lagt, utan att diagonalerna vilar på dem.
#if not r.alla_ok [- Delarna i rött i avsnitt 1 och 5 ska förstärkas eller ändras i modellen, och K-04 räknas om.]
