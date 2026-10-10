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
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 3pt, bottom: 3pt, it)
#show figure.caption: set text(size: 8.5pt)
#set figure(gap: 4pt)
#let liten(body) = text(size: 8.5pt, body)
#let s = r.s
#let b = r.bas

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Transient värmeledning i 2D och fuktbedömning], [*Upprättad*], p.upprattad,
  [*Underlag*], p.underlag, [*Status*], [Eget underlag, ingår inte i handlingarna till tekniskt samråd],
)

= Syfte

Bottenplattan i källaren har golvvärme från #r.dr.fran till #r.dr.till och ingen golvvärme på sommaren. Fukt i marken under plattan vandrar mot kallare ställen. När plattan är varmare än marken under cellplasten går ångflödet nedåt, och plattan och cellplasten hålls torra. På våren, när golvvärmen stängs av, är marken under huset varm efter vintern. Då kan flödet vända. Här beräknas temperaturen i plattan och i marken under hela året i en tvådimensionell sektion genom källaren, med antaganden på säker sida, och fuktsäkerheten bedöms. Utförandet är L300 enligt K-06, med L400 som jämförelse.

= Sektion och uppbyggnad

#figure(image("fig_sektion.svg", width: 100%), caption: [Sektion A–A med beräkningsmodellens geometri. Koordinater som i K-05. z räknas från bottenplattans överkant.])

Sektion A–A ligger vid y = #s.y mm, tvärs husets största bredd, #s.B mm mellan ytterliven på #s.vv och #s.vo. Väggarnas och rörens lägen och markytans nivå, +#s.mark_v m utanför #s.vv och +#s.mark_o m utanför #s.vo, är tagna ur modellen. Sektionen går genom plintarna #s.plintar. Uppbyggnaden är K-06:s:
- 100 mm platta på #s.t_eps mm cellplast S100 i två skikt, med åldringsbeständig plastfolie mellan skikten;
- kantbalkar #s.h_balk mm i L-element, och plintar med samma höjd, båda på 100 mm S200;
- Lecaväggar 100 + 150 + 100 som står i ett urtag i kantbalken;
- makadam på berg.

Modellen är tvådimensionell. Huset blir då oändligt långt, och plintarna blir balkar längs hela huset. Båda delarna ger varmare mark under plattan än i verkligheten. Källaren är ungefär 14 × 12 m, så värmen leds bort åt alla fyra sidor, och plintarna är bara 0,6–1,2 m stora.

#table(
  columns: (auto, auto, auto, 1fr),
  align: (left, right, right, left),
  [Material], [λ (W/mK)], [ρc (MJ/m³K)], [Underlag],
  [Betong], [#r.mat.betong.lam], [#r.mat.betong.rc], [SS-EN ISO 10456, 2 300 kg/m³],
  [Cellplast S100, S200], [#r.mat.cellplast.lam], [#r.mat.cellplast.rc], [Deklarerat 0,033–0,036. Högre värde för fuktig miljö under plattan],
  [Leca, blockets skal], [#r.mat.leca.lam], [#r.mat.leca.rc], [Lättklinkerbetong 650 kg/m³, fuktig],
  [Makadam], [#r.mat.makadam.lam], [#r.mat.makadam.rc], [Dränerad. Lågt värde],
  [Fyllning och mark], [#r.mat.mark.lam], [#r.mat.mark.rc], [SS-EN ISO 13370 tabell 7, sand och grus. Huset står på berg (3,5), se @kansl],
)
#liten[Hög λ i cellplasten och låg λ i marken leder mer värme ner i marken på vintern och håller kvar den. Båda ger varmare mark under plattan och ligger på säker sida.]

= Randvillkor och drift

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [Rand], [Värde], [Underlag],
  [Markyta och uteluft], [#r.kl.Tm ± #r.kl.A °C], [Sinus över året, varmast #r.kl.dag (+#r.kl.Tmax °C). Luftens årsmedel vid kusten är ungefär 8 °C och julimedlet ungefär 17 °C (SMHI 1991–2020). Markytan antas varmare och med större amplitud. Det ger varmare mark],
  [Utsidan, $R_"se"$], [#r.kl.Rse m²K/W], [Markytan och väggen ovan mark],
  [Golvvärme, #r.dr.fran–#r.dr.till], [#r.dr.T_gv °C], [Fast temperatur i slingornas nivå, #s.gv_z mm under överkant, från #s.gv_kant mm innanför väggarna. Högt antaget],
  [Källaren, vinter], [#r.dr.Tv °C], [],
  [Källaren, maj–september], [#r.dr.Ts °C], [Ingen golvvärme. Lågt antaget. Plattan får nära rummets temperatur],
  [Rumssidan, $R_"si"$], [#r.dr.Rsi_g / #r.dr.Rsi_v m²K/W], [Golv med värmeflöde nedåt, respektive vägg (SS-EN ISO 6946)],
  [Marken], [#s.ut_m m], [#s.utbredning husbredder åt sidorna och nedåt, med adiabatiska ränder (SS-EN ISO 10211)],
)
#liten[Golvvärmen stängs av och slås på från en dag till nästa. En gradvis övergång ger mindre temperaturskillnad.]

= Beräkningsmodell

Värmeledningen löses med finita volymer på ett rektangulärt nät med #r.nat.celler celler. Cellerna är #r.nat.h mm i plattan, cellplasten, väggarna och marken närmast och växer utåt. Tidssteget är #r.nat.steg h (implicit Euler). Källarens luft och uteluften är randvillkor.

Resultatet gäller det periodiska tillståndet, alltså det tillstånd som marken når efter många år med samma drift. Marken under huset är då som varmast, vilket ligger på säker sida jämfört med de första åren. Tillståndet bestäms direkt som det starttillstånd som ett års beräkning återför till sig självt (GMRES, #r.nat.it iterationer). Efter ett år avviker temperaturen mindre än $10^(#r.nat.exp)$ K från starten.

*Kontroller.* Tabellen visar minsta temperaturskillnad över cellplasten (avsnitt 5) med finare nät, kortare tidssteg och större markområde. Värmebalansen över året stämmer inom #r.Q.fel %. Golvvärmen ger #r.Q.gv kWh per år och meter hus. Av detta går #r.Q.rum kWh till rummet och #r.Q.ute kWh genom marken ut till markytan.

#table(
  columns: (1fr, auto, auto, auto),
  align: (left, right, right, right),
  [Kontroll], [Platta i fält (K)], [Plint (K)], [Kantbalk (K)],
  ..r.kontroll.map(k => ([#k.namn], [#k.falt], [#k.plint], [#k.kant])).flatten(),
)

= Fuktkriterier

Marken under cellplasten antas ha RF 100 %. Ånga diffunderar från varmt till kallt. Temperaturskillnaden över cellplasten, $Delta T$, räknas mellan betongens underkant och marken (makadamen) direkt under cellplasten. I fält är det 200 mm cellplast och plastfolie. Under plintar och kantbalkar är det 100 mm och ingen folie.

+ *Årsmedel:* $Delta T$ > 0 i medel över året, så att fukten i netto går nedåt.
+ *Varje dygn:* $Delta T$ > 0 hela året. Plattan är då alltid varmare än marken.
+ *Om kriterium 2 inte uppfylls:* kondensen under perioden med omvänd gradient ska vara försumbar och torka ut under året. Den räknas dygnsvis med Glaser: ånga från marken genom cellplasten ($mu$ = #r.fukt.mu, halva värdet i SS-EN ISO 10456) till plastfolien. Den räknas också till betongen som om folien saknades. Uttorkningen sker bara nedåt. Som jämförelse tillåter DIN 4108-3 #r.fukt.M_ref g/m² kondens mot ett skikt som inte suger vatten.

= Resultat

#figure(image("fig_ar.svg", width: 100%), caption: [Grundfallet under året. a) Temperaturer i fält där $Delta T$ är minst. b) $Delta T$ där den är minst för plattan i fält, plintarna och kantbalkarna. Skuggat: golvvärme.])

Med golvvärme är $Delta T$ i medel #r.sam.v_falt K i fält, #r.sam.v_plint K under plintarna och #r.sam.v_kant K under kantbalkarna. När golvvärmen stängs av den 1 maj sjunker plattan på några dygn till rummets temperatur. Marken under husets mitt är då #b.falt.Tg °C och svalnar långsamt. I mitten av huset och under plintarna blir $Delta T$ därför negativ under #r.bas_n dygn, som lägst #b.falt.dT K den #b.falt.dag. Vid kanterna kyls marken av utomhusklimatet. Där är $Delta T$ som minst #b.kant.dT K, i början av september när markytan är som varmast.

#figure(image("fig_falt.svg", width: 100%), caption: [Temperaturfält i grundfallet. Isotermer med 2 K avstånd i a och b, 0,5 K i c och d. I c är marken under plattan och plintarna varmare än betongen.])

#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right),
  [Grundfall], [min $Delta T$ (K)], [Datum], [x (m)], [Betong (°C)], [Mark (°C)], [Dygn < 0], [Årsmedel (K)],
  ..("falt", "plint", "kant").map(t => {
    let v = b.at(t)
    ([#v.namn], [*#v.dT*], [#v.dag], [#v.x], [#v.Ts], [#v.Tg], [#v.n_neg], [#v.medel])
  }).flatten(),
)
#liten[Minsta värde över året och över alla lägen av respektive slag. Dygn < 0 och årsmedel gäller det sämsta läget. Temperaturskillnaden mellan plastfolien och marken är som lägst #r.bas_folie.dT K. Kondensen blir som mest #r.bas_folie.M g/m² mot folien och #b.falt.M g/m² mot plattan om folien saknades.]

== Känslighet <kansl>

Varje fall ändrar ett eller två av grundfallets antaganden. Minsta $Delta T$ över året, antal dygn med $Delta T$ < 0 i det sämsta läget och största kondensmängd enligt kriterium 3.

#table(
  columns: (1fr, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  [Fall], [Fält (K)], [Plint (K)], [Kantbalk (K)], [Dygn < 0], [Kondens (g/m²)],
  ..r.fall.map(f => ([#f.namn], [#f.falt], [#f.plint], [#f.kant], [#f.n_neg], [#f.M])).flatten(),
)

= Bedömning

#let mn(n) = r.sam.min.at(n)
- *Kriterium 1* uppfylls med god marginal i alla fall. $Delta T$ är i årsmedel minst #r.sam.medel K, så fukten går i netto nedåt.
- *Kriterium 2* uppfylls inte i grundfallet. Där är plattan i mitten av huset och plintarna kallare än marken under några veckor i maj. Kriteriet uppfylls, med lägsta $Delta T$ inom parentes:
  - om källaren hålls vid 18 °C på sommaren (#mn("Källaren 18 °C på sommaren") K) eller vid 20 °C (#mn("Källaren 20 °C på sommaren") K);
  - med husets verkliga grund, berg, även med en källare på 16 °C (#mn("Berg under huset, λ = 3,5") K).
- *Kriterium 3* uppfylls. Under perioden med omvänd gradient samlas som mest #r.sam.M_max g/m² i något av fallen. Det är försumbart mot #r.fukt.M_ref g/m², och fukten torkar ut inom #r.sam.M_dygn dygn, långt före nästa vår. Under plattan finns bara cellplast och betong, som inte tar skada av så lite fukt.
- *L400* höjer det lägsta värdet i fält från #b.falt.dT till #r.sam.L400 K, men perioden med omvänd gradient finns kvar. Det som avgör är källarens temperatur på sommaren, inte cellplastens tjocklek.

*Slutsats.* Bottenplattan L300 är fuktsäker utan golvvärme på sommaren. Det gäller även med de samlade antagandena på säker sida: tvådimensionellt hus, plintar som balkar, varm mark, högt ställd golvvärme och en sval källare. Med golvvärmens golvgivare på lägst 20 °C även sommartid är plattan dessutom varmare än marken hela året, med minst #mn("Källaren 20 °C på sommaren") K, under samma antaganden. Golvvärmen går då bara när källaren annars skulle bli kallare.

Byggfukten i plattan torkar bara uppåt, eftersom plastfolien ligger under. Den ingår inte här, och RF i betongen mäts innan golvet läggs.
