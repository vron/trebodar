#let r = json("resultat.json")
#let p = r.projekt
#let t = r.t
#let tab = r.tab

#set document(title: p.objekt, author: p.upprattad)
#set page(
  paper: "a4",
  margin: (x: 17mm, top: 18mm, bottom: 14mm),
  header: context [
    #set text(8pt)
    #grid(columns: (1fr, auto), p.namn, [#p.dokument rev #p.revision · Sida #counter(page).display() av #counter(page).final().first()])
    #v(-2pt)
    #line(length: 100%, stroke: 0.4pt)
  ],
)
#set text(font: "Carlito", size: 9pt, lang: "sv")
#set par(justify: false, leading: 0.5em, spacing: 0.65em)
#set heading(numbering: "1.1", supplement: [avsnitt])
#show heading.where(level: 1): it => {
  v(2pt)
  block(below: 4pt, text(size: 10.5pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#show heading.where(level: 2): it => {
  block(above: 6pt, below: 3pt, text(size: 9.5pt, weight: "bold")[#counter(heading).display() #h(3pt) #it.body])
}
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 3.5pt, y: 1.8pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 2pt, bottom: 2pt, it)
#show figure.caption: set text(size: 8pt)
#set figure(gap: 3pt)
#set list(spacing: 0.5em)
#set enum(spacing: 0.5em)
#let liten(body) = text(size: 8pt, body)
#let rader(rows) = rows.flatten().map(x => eval(x, mode: "markup"))

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 3.5pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Värmeförluster per byggdel, köldbryggor, mark i 3D och energibehov över året], [*Upprättad*], p.upprattad,
  [*Underlag*], p.underlag, [*Status*], [Eget underlag, ingår inte i handlingarna till tekniskt samråd],
)

= Syfte och sammanfattning

Utredningen visar var värmen lämnar huset och hur mycket energi huset behöver under ett år på platsen, så som huset är utformat i modellen, när huset används #t.narvaro_text. Jämförelserna i @kansl är räkneexempel. Huset värms bara med golvvärmen i mellanbjälklaget: källaren får ingen egen värme utan värms av bjälklaget ovanför. Inne hålls minst #t.T_inne °C. Bergvärmepumpens värmefaktor räknas timme för timme.

Byggdelarna och skarvarna räknas i detalj i två dimensioner, marken med källaren, bottenplattan, plattan på mark och mellanbjälklaget i tre dimensioner, och huset som helhet stationärt och timme för timme med väderdata för platsen 2014–2023. Alla verktyg är kontrollerade mot analytiska lösningar och standarder (@kontroller).

#table(
  columns: (1fr, auto, auto),
  align: (left, right, left),
  [Resultat (grundfallet)], [Värde], [Jämförelse],
  ..rader(tab.sammanfattning),
)

*Det viktigaste:*
- *Ventilationen* är den största enskilda förlusten när huset används (#t.vent_andel % vid 0 °C): frånluften, #t.q_franluft l/s, går ut utan värmeåtervinning. Det är #t.q_m2 l/s per m² Atemp, mindre än BBR:s 0,35. Huset används bara #t.narvaro_text, och resten av veckan går frånluften ned till #t.tomt_flode l/s per m² (#t.q_tom l/s). Under året blir den i medel #t.q_medel l/s och #t.vent_ar_andel % av förlusterna.
- *Väggarna* har U = #t.U_vagg_medel W/m²K i medel (#t.U_vagg_spann): 95 mm mineralull mellan reglar, där virket i medel är #t.f_tra_medel % av regelfacken, och #t.inst_text. BBR:s riktvärde är 0,18.#t.inst_fukt Ångbromsen är fuktadaptiv (Intello Plus), och U-03 anger för taket att installationsskiktet innanför den inte isoleras; samma fråga gäller väggarna och bör stämmas av med leverantörens anvisningar innan väggarnas installationsskikt isoleras.
- *Taket* har U = #t.U_tak W/m²K: 170 mm träfiber mellan takbalkarna och #t.tak_text (U-03). BBR:s riktvärde är 0,13. Med mineralull också där blev golvvärmen #t.tak_ar MWh mindre om året (@kansl), men då låg #t.tak_innanfor % av takets värmemotstånd innanför ångbromsen.
- *Gavelspetsarna* ovanför hammarbandet (#t.A_gavel m², sex gavlar) har mineralull i gavelstolarnas fack: U = #t.U_gavel W/m²K.
- *Källarens golv* förlorar ungefär dubbelt så mycket som 300 mm cellplast ensam skulle ge: kantbalkarna, balkarna under innerväggarna och plintarna står på 100 mm, och bottenplattan är gjuten ihop med källarväggarnas kärna, som bara har 100 mm cellplast utanför (@mark).
- *Mellanbjälklagets kanter*: genom de 30 mm cellplast utanför betongens kant går #t.kant_noll W vid 0 °C ute, #t.kant_noll_andel % av förlusterna, och #t.kant_ar kWh under året (#t.kant_ar_andel %). #t.kant_varme_andel % av det kommer direkt från golvvärmen (@kanter).
- *Källaren blir varmare än plan 1*: #t.Tb_noll °C vid 0 °C ute. Bjälklaget har ingen isolering under sig, så #t.ned_andel % av golvvärmen går ned i källaren. Den varma luften stiger genom trapphålet. Med 21 °C på plan 1 blir källaren #t.Tb21_noll °C vid 0 °C ute, #t.Tb21_min15 °C vid −15 °C och #t.Tb21_ar °C i medel över året (@kallare).
- *Solen* genom fönstren ger #t.sol_tot kWh om året. Av det sparar #t.sol_nytta kWh golvvärme (#t.sol_andel %); resten kommer när huset redan är varmt nog.
- *Bergvärmepumpen* ger en årsvärmefaktor på #t.SCOP för golvvärmen: framledningen behöver högst #t.T_fram_max °C. Köpt el blir #t.E kWh/år.
- *Um* = #t.Um W/m²K mot BBR:s #t.Um_krav för småhus. Primärenergitalet blir #t.EP_ben kWh/m² Atemp och år (BEN, 21 °C) mot kravet #t.EP_krav, tack vare bergvärmepumpen.
- *Kostnaden* för elen till värme, varmvatten, fläktar och pumpar blir #t.kostnad kr om året med de senaste årens elpriser (@kostnad).

= Metod

#figure(image("fig_skarvar.svg", width: 100%), caption: [Temperaturen i fyra av skarvarna vid 0 °C ute och #t.T_inne °C på plan 1 (stationärt, grundfallet: golvvärmens plan #t.Th_noll °C, källaren #t.Tb_noll °C). Linjerna visar varje grad och materialens gränser. a) och b) med hela detaljen, c) och d) med takets och väggens skikt homogeniserade.]) <fig-skarvar>

Beräkningen går i fyra steg. Varje steg kontrolleras för sig (@kontroller).

+ *Byggdelarna* (@byggdelar). Väggar och tak räknas i ett tvådimensionellt snitt vinkelrätt mot reglarna med finita volymer (cell 1 mm). Virkesandelen i regelfacken är mätt i modellen per vägg och per takfall, som virkets volym mot virkets och isoleringens. Snittet ska ligga mellan SS-EN ISO 6946:s övre och undre gräns. Fönstren räknas enligt SS-EN ISO 10077-1.
+ *Köldbryggorna* (@skarvar). Skarvarna räknas i tvådimensionella snitt enligt SS-EN ISO 10211 med invändiga mått, som Um i BBR (cell #t.h_2d mm). Där skarven når marken eller bjälklaget räknas den två gånger: med hela detaljen och så som 3D-modellen ser den. Skillnaden är skarvens tillskott.
+ *Marken, källaren och mellanbjälklaget i 3D* (@mark). Finita volymer på ett rätvinkligt nät med #t.N3d celler (#t.h_3d mm vid väggarna och kanterna). Nätet når #t.mark_ut m ut från huset och #t.mark_djup m ned. Golvvärmen är ett plan i rörens nivå med golvvärmens medeltemperatur.
+ *Huset* (@stationart, @ar). Alla delar sätts ihop till ett nät av värmekonduktanser mellan fem omgivningar: ute, markytan, källaren, plan 1 och golvvärmen. Ventilation, infiltration och luftutbytet i trapphålet kommer till. Nätet räknas stationärt och timme för timme under tio år.

Alla omgivningar kopplas linjärt, så varje del räknas en gång per omgivning med 1 K där och 0 K i de andra. Det ger kopplingskoefficienterna enligt SS-EN ISO 10211, som sedan kan sättas ihop för vilka temperaturer som helst. Ytmotstånden följer SS-EN ISO 6946:
- 0,13 m²K/W mot väggar och 0,10 uppåt mot taket;
- 0,17 nedåt, under bjälklaget och mot källargolvet;
- 0,04 utvändigt;
- golvvärmens yta 1/10,8 enligt SS-EN 1264.

Bakom fasadens och takets luftspalter räknas skikten utanför spalten inte. Spalten får då samma ytmotstånd som insidan (0,13 och 0,10).

= Byggdelarna <byggdelar>

#table(
  columns: (auto, 1fr, auto, auto, auto, auto, auto),
  align: (left, left, right, right, right, right, right),
  [Vägg], [Uppbyggnad], [A (m²)], [Virke (%)], [U 2D], [ISO 6946], [Gränser],
  ..rader(tab.vaggar),
)
#liten[A är den invändiga arean utan fönster och dörrar men med gavelspetsen (ångbromsens area i modellen). Virke är andelen virke i regelfacken mellan syll och hammarband, mätt i modellen. U 2D är snittet med finita volymer och ISO 6946 kombinerade metoden; gränserna är ISO 6946:s undre och övre. Gavelspetsarna har sitt eget U nedan. 2SV:s fält är små bitar bredvid skjutdörren; där antas 30 % virke.]

#table(
  columns: (4.2cm, auto, auto, 1fr),
  align: (left, right, right, left),
  [Byggdel], [U (W/m²K)], [Area (m²)], [Uppbyggnad och underlag],
  ..rader(tab.byggdelar),
)

Fönstren är VELFAC 200 ENERGY med isolerruta 3-glas 48 mm. VELFAC anger Uw ned till 0,80 för referensfönstret 1 230 × 1 480. Med Ug = #t.Ug (antaget) och ψg = #t.psi_g ger det Uf = #t.Uf W/m²K för ram och båge med siktlinjen 54 mm. Husets fönster är mindre än referensfönstret, så ramen tar en större del: Uw = #t.Uw_spann W/m²K. Ytterdörrarna och takfönstren är inte valda; deras U är antagna typvärden.

= Köldbryggorna <skarvar>

#table(
  columns: (1fr, auto, auto, auto, 1fr),
  align: (left, right, right, right, left),
  [Skarv], [ψ (W/mK)], [l (m)], [ψ·l (W/K)], [Snitt],
  ..rader(tab.skarvar),
)
#liten[Invändiga mått. Mellanbjälklagets kant över källarväggen och vid plattan på mark har fyra omgivningar. ψ redovisas mot ute med golvvärmen (ψ#sub[he]) och rummet (ψ#sub[ie]). Kanten mot källaren ingår i 3D-modellen, och kopplingarna mellan inre omgivningar påverkar inte förlusten. Uppskattade värden saknar snitt; de är typvärden.]

Köldbryggorna står för #t.skarv_H W/K, #t.skarv_andel % av transmissionsförlusterna. Störst är mellanbjälklagets kant (#t.kant_H W/K); fönstrens anslutning ger #t.fonster_H W/K.

- *Mellanbjälklagets kant:* betongen med golvvärmen går ut till 30 mm från stommens utsida, och där finns bara 30 mm cellplast. Vid #t.Th_noll °C i golvvärmens plan och 0 °C ute leder kanten över källarväggen #t.kant_W W/m direkt ut.
- *Fönstren:* ψ = #t.psi_fonster W/mK. Karmen sitter 20 mm innanför panelen med 15 mm drevning mot karmreglarna. I snittet ersätts karmen av ett block, med λ = #t.lam_karm W/mK bestämt så att fönstret ensamt ger precis Uf och Ug; skarvens ψ är det som väggen och inbyggnaden lägger till.
- *Virket vid öppningar och hörn* (karmreglar och hörnstolpar) ingår i väggarnas virkesandel och därmed i väggarnas U. Det ritas därför inte för sig i snitten.
- *Nock och dal:* snitten följer modellen. Takets isolering går fram till balkarna ovanför upplagsreglarna, och stålplåtarna finns på en del av balkarnas längd.

== Mellanbjälklagets kanter <kanter>

Betongen i mellanbjälklaget går ut till plattans kant. Utanför den finns 30 mm cellplast och sedan fasadens luftspalt och panel: över källarväggarna och vid plattan på mark, sammanlagt #t.l_kant m. Golvvärmens rör ligger 150 mm innanför väggarnas insida. Värmen som går ut genom kantisoleringen räknas i skarvarnas detaljerade snitt (@fig-skarvar a och b). Den kommer ur golvvärmen och, en mindre del, ur rummet och källaren.

#block(breakable: false, table(
  columns: (1fr, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right, right),
  [Kant], [l (m)], [W/m, 0 °C], [W, 0 °C], [Andel], [W, #t.dim_Te °C], [Andel], [kWh/år], [Andel],
  ..rader(tab.kant),
))
#liten[Värmen genom kantisoleringen ut till luftspalten bakom fasaden, och dess andel av husets förluster vid 0 °C och #t.dim_Te °C ute (stationärt) och under året (timsimuleringen, medel 2014–2023). #t.kant_varme_andel % kommer direkt från golvvärmen. Skarvens hela tillskott (@skarvar) är större: där ingår också värmen som går upp genom syllen och väggens nederdel och ned i källarväggens kärna.]

= Marken, källaren och mellanbjälklaget i 3D <mark>

#figure(image("fig_3d.svg", width: 100%), caption: [3D-modellen i snitt vid y = 6 000 (K-05) genom källaren och de två högra huskropparna, med temperaturen vid 0 °C ute och #t.T_inne °C på plan 1 (grundfallet). Markytan har här årsmedeltemperaturen #t.T_ar °C. Linjerna visar varje grad och materialens gränser.]) <fig-3d>

Modellen har källarväggarna (Sundolitt Kub 350-150 med gips, med cellplasten obruten runt hörnen och förbi innerväggarna) i K-05:s lägen och bottenplattan L400 enligt K-06: kantbalkar 450 × 300 och plintar under rören på 100 mm cellplast, i övrigt 300 mm. Mellanbjälklaget är 150 mm betong med trapphålet. Plattan på mark ligger på 350 mm cellplast i L-element. Fyllningen har λ = 2,0 och berget under λ = 3,5. Markytan runt huset följer modellens marknivåer per fasad. Källarens fönster och dörr räknas som vägg här och byts sedan mot sina U-värden.

#table(
  columns: (1fr, auto, auto, auto),
  align: (left, right, right, right),
  [Koppling (W/K)], [Nätet #t.h_3d mm], [Dubbelt så grovt], [Grovt, utan kantbalkar och plintar],
  ..rader(tab.koppling3d),
)
#liten[Kopplingskoefficienterna mellan omgivningarna: flödet när den ena har 1 K och de andra 0 K. Golvvärmens plan leder #t.ned_W W/K ned till källaren, mot #t.upp_W W/K upp till plan 1 (betongen under rören och ytmotståndet nedåt). Kantbalkarna och plintarna på 100 mm cellplast leder #t.bryggor_W W/K mer från källaren till marken än om cellplasten vore 300 mm överallt.]

Som kontroll är samma lösare jämförd med SS-EN ISO 13370 för en platta på mark och en uppvärmd källare med enkel form (@kontroller). Avvikelsen är #t.iso_platta % och #t.iso_kallare %. Det verkliga huset har mer: källarväggarna står till stor del över mark (#t.ovan_mark), och kantbalkarna och plintarna är köldbryggor.

= Ventilation och luftläckage <ventilation>

Frånluften är #t.q_franluft l/s med grundflödena enligt VL-01: köket #t.FF1 l/s, badrummet #t.FF2 l/s och källaren #t.FF3 l/s. Köksfläkten forceras 30 minuter om dagen (BEN). Uteluften kommer in genom ventilerna i fönstren på plan 1. Källarens frånluft tas därför från plan 1 genom trapphålet och för med sig värme ned i källaren.

Med källaren i Atemp är frånluften #t.q_m2 l/s per m², mindre än BBR:s 0,35 l/s per m² golvarea för bostäder (BBR 6:251), som här vore #t.q_bbr l/s. När ingen vistas i huset får flödet minskas till lägst 0,10 l/s per m² (BBR 6:251). Huset används #t.narvaro_text (#t.andel_hemma % av tiden). Resten av veckan går alla fläktarna ned i samma proportion till #t.tomt_flode l/s per m² Atemp, #t.q_tom l/s, och köksfläkten forceras inte. Under året blir frånluften i medel #t.q_medel l/s. De stationära fallen (vid 0 °C och det kallaste dygnet) räknas med huset i bruk och grundflödena. Fallen med BBR:s flöde, med grundflödena också när huset står tomt och med helårsboende redovisas i @kansl.

Lufttätheten är antagen till q#sub[50] = #t.q50 l/s·m² omslutande area, eftersom huset inte är provtryckt. Infiltrationen räknas med LBL-modellen (ASHRAE Fundamentals kap. 16) för stigkraft och vind och läggs ihop med frånluften kvadratiskt. Undertrycket gör att läckaget mest blir en del av frånluften: tillskottet är #t.q_extra l/s vid 0 °C och 4 m/s.

Genom trapphålet blandas luften när källaren är varmare än plan 1. Det räknas som ett dubbelriktat flöde genom en vågrät öppning (Epstein), halverat för trappan: #t.q_trapp l/s vid 0 °C ute.

= Stationära fall <stationart>

#figure(image("fig_forluster.svg", width: 100%), caption: [Värmeförlusterna per byggdel vid 0 °C ute (markytan #t.T_ar °C, årsmedel) och #t.T_inne °C på plan 1, utan internlast och sol. Summan, #t.Q_noll W, är golvvärmens effekt.]) <fig-forluster>

#table(
  columns: (1fr, auto, auto, auto, auto),
  align: (left, right, right, right, right),
  [Byggdel], [0 °C (W)], [Andel], [#t.dim_Te °C (W)], [Andel],
  ..rader(tab.forluster),
)
#liten[Förlusten ut ur huset genom varje byggdel. Kategorierna för källaren och mellanbjälklaget kommer ur 3D-modellens ytor. #t.dim_Te °C är den lägsta dygnsmedeltemperaturen 2014–2023 (#t.dim_dag). Markytan har då #t.dim_Tm °C, markens tröga temperatur enligt ISO 13370.]

#table(
  columns: (1fr, auto, auto),
  align: (left, right, right),
  [Golvvärmen och temperaturerna], [0 °C ute], [#t.dim_Te °C ute],
  ..rader(tab.temperaturer),
)

Golvvärmen sitter mitt i ett oisolerat bjälklag. Uppåt är det 68 mm betong och golvytan; nedåt 82 mm betong och ytmotståndet mot källarens tak. Bjälklaget leder därför nästan lika bra nedåt som uppåt per grad. Källaren värms tills den är nästan lika varm som golvvärmens plan, och då går #t.ned_andel % av golvvärmen ned. Källaren blir varmare än plan 1, och dess förluster genom väggar, golv, fönster och frånluft betalas med golvvärme.

== Källaren med 21 °C på plan 1 <kallare>

Golvvärmen sitter bara i mellanbjälklaget. Med 21 °C på plan 1 bestämmer bjälklagets temperatur hur varm källaren blir: ju kallare ute, desto varmare måste bjälklaget vara, och desto mer värme går ned i källaren. Figuren och tabellen gäller stationärt, utan sol och internlast. Markytan har markens tröga temperatur.

#figure(image("fig_kallare.svg", width: 100%), caption: [a) Golvvärmens plan och källaren mot utetemperaturen med 21 °C (heldraget) och 20 °C (streckat) på plan 1. b) Golvvärmens effekt med 21 °C på plan 1 och hur den delar sig upp till plan 1 och ned till källaren. Skillnaden är det som går direkt ut genom kanterna och till marken.]) <fig-kallare>

#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto, auto),
  align: (right, right, right, right, right, right, right, right),
  [Ute (°C)], [Golvvärmens plan (°C)], [Källaren (°C)], [Golvvärme (kW)], [Upp (kW)], [Ned (kW)], [Andel ned], [Trapphålet (l/s)],
  ..rader(tab.kallare),
)
#liten[Plan 1 21 °C, stationärt utan sol och internlast. Upp och ned: värmen från golvvärmens plan till plan 1 och till källaren. Trapphålet: luftutbytet när källaren är varmare än plan 1.]

Källaren håller sig över 21 °C hela vintern utan egen värme. Under året blir den i medel #t.Tb21_ar °C, med timvärden mellan #t.Tb21_minh och #t.Tb21_maxh °C (@fig-kallare-ar). På sommaren, när golvvärmen står, följer källaren plan 1 och marken.

= Energibehovet under året <ar>

#figure(image("fig_ar.svg", width: 100%), caption: [a) Golvvärmens värme och solen genom fönstren per månad (medel 2014–2023). b) Golvvärmen per år.]) <fig-ar>

Timsimuleringen har tre tillstånd: luften och de lätta delarna på plan 1, mellanbjälklaget och källaren med bottenplattan. Konduktanserna är husmodellens. Infiltrationen och trapphålets luftutbyte räknas om varje timme. Marken får en trög temperatur enligt den periodiska metoden i ISO 13370 (dämpning #t.eta, fördröjning #t.lag månader).

Brukarindata följer BEN tabell 2:1 för småhus:
- #t.T_inne °C inne (beställarens krav; BEN anger 21 °C, som räknas som ett fall för BBR:s primärenergital);
- hushållsel 30 kWh/m² Atemp, varav 70 % blir värme;
- personvärme 3,51 personer à 80 W i 14 h/dygn;
- huset används #t.narvaro_text (#t.andel_hemma % av tiden); då gäller hushållselen och personvärmen ovan, annars bara en grundlast på #t.grundlast W (kyl, frys och standby, uppskattat), och frånluften går ned (@ventilation). Tappvarmvattnet (BEN 20 kWh/m²) och vädringen (4 kWh/m²) räknas efter andelen av tiden som någon är hemma. BBR:s primärenergital räknas med helårsboende enligt BEN;
- solavskärmning 0,71 (gardiner och liknande).

Solen genom fönstren räknas med vädret för varje timme och fasadens riktning: direkt och diffus strålning mot varje fönster, glasets andel och g-värde (#t.g), infallsvinkeln och avskärmningen. Hälften hamnar på golvet (bjälklaget), hälften i rummets luft och lätta delar. Källarens fönster värmer källaren. Solen ger #t.sol_tot kWh om året och sparar #t.sol_nytta kWh golvvärme (#t.sol_andel %), jämfört med fallet utan sol i @kansl. Mest gör den det vår och höst; på sommaren behövs ingen värme, och på vintern är solen svag. Golvvärmen styrs mot #t.T_inne °C i rummet #t.horisont timmar framåt, högst #t.P_max kW. Över #t.T_vad °C vädras det.

#table(
  columns: (1fr, auto, auto),
  align: (left, right, right),
  [Värmebalans, medel 2014–2023], [kWh/år], [kWh/m² Atemp],
  ..rader(tab.arsbalans),
)
#liten[Förlusterna per byggdel under året, och tillskotten från sol och internlast. Summan av förlusterna är golvvärmen plus tillskotten (det som vädras bort på sommaren kommer till).]

#figure(image("fig_kallare_ar.svg", width: 100%), caption: [Källarens temperatur varje månad under 2014–2023 med 21 °C och 20 °C på plan 1: medel (linjen) och lägsta och högsta timvärde (bandet), och utetemperaturens månadsmedel.]) <fig-kallare-ar>

#figure(image("fig_temperaturer.svg", width: 100%), caption: [Dygnsmedeltemperaturen ute, i golvvärmens plan, i källaren och på plan 1 under #t.ar_vis, det år som ligger närmast medelåret.]) <fig-temp>

*Bergvärmepumpen.* Varje timme räknas värmefaktorn ur temperaturerna i kondensorn och förångaren. Kondensorn följer golvvärmens framledning, som är golvvärmeplanets temperatur plus rörens motstånd mot betongen. Förångaren följer köldbäraren, som är berggrundens temperatur minus borrhålets motstånd gånger uttaget och bergets motstånd gånger uttaget i tre tidsskalor: de senaste sex timmarna, de senaste 30 dygnen och medeluttaget under #t.driftar års drift. Verkningsgraden mot den ideala (Carnot) är anpassad till NIBE S1256-13 vid B0/W35. Golvvärmen kan gå med låg framledning, eftersom den värmer en stor yta, och det ger en hög värmefaktor. Uttaget ur berget är #t.uttag_m kWh per meter borrhål och år. Borrhålets längd bör stämmas av med borrarens dimensionering.

#table(
  columns: (1fr, auto, 1fr),
  align: (left, right, left),
  [Värmepumpen (golvvärmen)], [Värde], [Underlag],
  ..rader(tab.varmepump),
)

#table(
  columns: (1fr, auto, auto),
  align: (left, right, left),
  [Energi och BBR 29], [Värde], [Underlag],
  ..rader(tab.energi),
)
#liten[BBR 29 (BFS 2020:4) avsnitt 9:2, småhus över 130 m² Atemp. Primärenergitalet (EP#sub[pet]) räknas så här: (E#sub[uppv]/F#sub[geo] + E#sub[tvv] + E#sub[f]) · VF#sub[el] / Atemp, med F#sub[geo] = 0,9 för Tanum och VF#sub[el] = 1,8. Avsnitt 9:2 gäller inte för bostadshus som används mindre än fyra månader om året eller under en begränsad del av året, med en energianvändning under 25 % av helårsanvändning (BBR 9:113). Huset hålls uppvärmt året runt (F-01), så kraven bör gälla.]

Kontroll med gradtimmar: förlustfaktorn #t.H_tot W/K (transmission och luften i medel över året, alla rum lika varma) gånger #t.gradtimmar kKh under #t.T_inne °C ger #t.gt_brutto MWh. Med solen och internlasten avdragna blir det #t.gt_netto MWh/år, mot simuleringens #t.Q_ar MWh. Skillnaden är rimlig: en del av tillskotten kommer när de inte behövs, och källaren är varmare än plan 1.

= Jämförelser och känslighet <kansl>

#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right),
  [Fall], [H#sub[T] (W/K)], [Um], [Effekt #t.dim_Te °C (kW)], [Golvvärme (MWh/år)], [Köpt el (MWh/år)], [Elkostnad (kr/år)], [EP#sub[pet]],
  ..rader(tab.fall),
)
#liten[Varje fall ändrar grundfallet på en punkt. Fallen är räkneexempel som visar vad som väger tyngst, inte förslag. Effekten är stationär utan internlast och sol. Elkostnaden är den rörliga (@kostnad).]

== Kostnaden för elen <kostnad>

Köpt el är elen till värmepumpen (golvvärme och varmvatten), fläktarna och pumparna; hushållselen ingår inte. Kostnaden räknas med elen per månad och månadens rörliga elpris: spotprisets medel i elområde SE3 åren #t.pris_ar, elhandlarens påslag #t.pris_paslag öre, energiskatten #t.pris_skatt öre och elnätets överföringsavgift #t.pris_nat öre per kWh, allt med moms. De fasta avgifterna ingår inte. Vägt efter när elen används blir priset #t.pris_medel öre/kWh i grundfallet.

#table(
  columns: (1fr, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  [Inne, hela tiden], [Golvvärme (MWh/år)], [Köpt el (kWh/år)], [Kostnad (kr/år)], [Dyraste månaden (kr)], [Källaren, medel (°C)],
  ..rader(tab.kostnad),
)
#liten[Samma hus och användning (#t.narvaro_text), bara innetemperaturen ändrad. U-03 avråder från mindre än 15 °C inne när huset står tomt på vintern: värmen från huset håller takets luftspalt torr.]

#block(breakable: false, width: 62%, table(
  columns: (1fr, auto, auto, auto, auto),
  align: (left, right, right, right, right),
  [Månad], [Spotpris (öre/kWh)], [Rörligt pris (öre/kWh)], [Köpt el (kWh)], [Kostnad (kr)],
  ..rader(tab.elpris),
))
#liten[Grundfallet per månad, med spotpriset och hela det rörliga priset med moms.]

= Kontroller <kontroller>

#table(
  columns: (1fr, auto, auto, auto),
  align: (left, right, right, right),
  [Kontroll], [Beräkning], [Jämförelse], [Avvikelse],
  ..rader(tab.kontroller),
)
#liten[Energibalansen är noll inom avrundningen i alla lösningar (största restterm #t.balans W/K). Nätkontrollen: skarvarna med halva cellstorleken och 3D-modellen med dubbla.]

= Antaganden och osäkerheter

- *Installationsskiktet* har 45 mm mineralull mellan läkten i ytterväggarna men ingen isolering i taket (modellen, U-03). Utan mineralullen i väggarna blir förlusten #t.inst_extra W större vid 0 °C och golvvärmen #t.inst_ar MWh större under året; med mineralull också i taket blir förlusten #t.tak_extra W mindre och golvvärmen #t.tak_ar MWh mindre (@kansl).
- *Gavelspetsarna* har mineralull i gavelstolarnas fack, lika djupt som väggens stomme. Utan den blir förlusten där #t.gavel_extra W större vid 0 °C (@kansl).
- *Takets area* är den invändiga, från ytterväggens insida till nockens eller dalens mittlinje (#t.A_tak m² utan takfönstren); nockens och dalens ψ räknas från samma linjer.
- *Bergvärmepumpen*: värmefaktorn är anpassad till NIBE:s 5,06 vid B0/W35 och räknas för varje timme, med ett minsta temperaturlyft på 28 K (antaget), så att den inte blir högre än ca 7,4. Delast och start och stopp ingår inte. Berggrundens temperatur (#t.T_berg °C) och borrhålets motstånd är typvärden, och bergets avkylning räknas för #t.driftar års drift med en linjekälla. Varmvattnets årsvärmefaktor 3,0 är ett typvärde; varmvattenberedarens förluster när huset står tomt ingår inte.
- *Materialdata*:
  - mineralullen är inte vald; λ = 0,037 antas;
  - fönstrens Ug och ψ#sub[g] är typvärden; Uf är anpassat till VELFAC:s Uw 0,80;
  - ytterdörrarna (U 1,0) och takfönstren (U 1,1 och ψ 0,10) är antagna.
- *Lufttätheten* q#sub[50] = 0,6 är antagen. Huset är inte provtryckt.
- *Uppskattade skarvar* utan snitt: gavelns takkant (ψ 0,05) och källarens fönster och dörr (ψ 0,05). Tillsammans står de för #t.uppsk_W W/K av #t.H_T_kort W/K.
- *Klimatet* är ERA5 för platsen 2014–2023 (U-03), inte ett normalår enligt SMHI. Åren varierar med #t.Q_spann MWh.
- *Marken*: fyllning och berg med typvärden, och markytan nära huset förenklad ur modellens marknivåer. Dynamiken i marken räknas med ISO 13370:s periodiska metod, inte i 3D över tiden.
- *Golvvärmen* är ett plan med jämn temperatur i rörens nivå. Rörens motstånd mot betongen läggs till i värmepumpens framledning.
- *Brukarindata* enligt BEN gäller för ett permanent bebott småhus. Ett fritidshus med mindre internlast och varmvatten redovisas i @kansl.
