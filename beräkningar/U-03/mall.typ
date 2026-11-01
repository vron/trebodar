#let r = json("resultat.json")
#let p = r.projekt

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
#set heading(numbering: "1", supplement: [avsnitt])
#show heading.where(level: 1): it => {
  v(2pt)
  block(below: 4pt, text(size: 10.5pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 3.5pt, y: 2pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 2pt, bottom: 2pt, it)
#show figure.caption: set text(size: 8pt)
#set figure(gap: 3pt)
#set list(spacing: 0.5em)
#let liten(body) = text(size: 8pt, body)
#let s = r.sam
#let k = r.kl
#let fl = r.fl

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 3.5pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Luftflöde, temperatur, fukt och mögelindex timme för timme #k.period, hela taket som nätverk], [*Upprättad*], p.upprattad,
  [*Underlag*], p.underlag, [*Status*], [Eget underlag, ingår inte i handlingarna till tekniskt samråd],
)

= Syfte och slutsatser

Luftspalten mellan råsponten och den hårda träfiberskivan går obruten från takfot till takfot över nockar och dalar, som längst #r.g.vag_max m. Här bedöms om den ventileras tillräckligt, vad takfönstren, gavelöppningar, vindskivans ånggenomsläpplighet och badrummet betyder, och om en oventilerad spalt räcker.

#let S = r.S
- *Den obrutna spalten fungerar.* Luften går genom alla sex takfallen i följd, driven av vinden och av solen: när de tre takfallen mot sydost värms och de mot nordväst inte gör det, driver alla takfall luften åt samma håll. Längs den 16,3 m långa vägen rör sig luften i median med #fl.omluft_lang_alla m/s. Lugna soliga timmar driver solen ensam #fl.vind0_lang_lugn_sol m/s.
- *Med zink-magnesiumplåten klarar sig råspontens undersida.* Mögelindex ligger under 1 i hela taket alla tio åren, också efter den extremt milda och blöta vintern 2019/20: som mest #S.omluft.M2 vid takfoten mot sydost på de korta vägarna och #S.omluft.M_lang på den långa vägen (@fig-plan, @fig-ar). Den metalliska ytan strålar lite mot natthimlen, så plåten och råsponten kyls mindre på klara nätter. Med målad plåt hade mögelindex blivit #S.malad.M. Plåten ska alltså inte målas.
- *Den långa sammanhängande vägen är inget problem vid platsens vind, men en något större spalt ger marginal.* Med halva vindtrycket blir M #S.vind05.M2. Är läget mycket skyddat, en fjärdedel av vindtrycket, kan fukt från de solvarma takfallen mot sydost föras med den långsamma luften och samlas i det sista takfallet mot nordväst (M #S.vind025.M med #r.g.spalt mm). Med 36 mm fri höjd blir det #S.s36_vind025.M, och vid full vind #S.s36.M2.
- *Bygg inga gavelöppningar.* De ändrar mögelindex lite (#S.omluft_gavel.M2 mot #S.omluft.M2) men släpper in slagregn och snö, särskilt i gavlarna mot sydväst.
- *Takfönstren bryter facken.* Utan omluftning står luften helt still i de två facken vid varje fönster, ända till takfoten på andra sidan. Mögelindex blir där lågt, och byggfukt torkar ut inåt, men läckage vid fönstren kan inte torka ut. Uppehåll i ströläkten ovanför och under fönstren ger flödet tillbaka, som Byggforsk och ÖNORM B 4119 kräver (@fig-omluft).
- *Vindskivan och badrummet.* Vindskivan bör vara ångöppen (Sd högst ca 0,3 m). Intello Plus räcker också över badrummet. Står huset tomt och svalt på vintern blir mögelindex #S.tomt_vinter.M2 (avsnitt 3).

= Taket och modellen

*Taket.* Tre sadeltak, #r.g.lutning°, med nockarna längs husets längd och dalar emellan. Uppbyggnad (F-01): bandtäckning av zink-magnesiumbelagd plåt (silvergrå), underlagspapp av bitumen (t.ex. T-Roof YEP 2500, ångtät), råspont 20 mm, luftspalt #r.g.spalt mm effektiv höjd mellan ströläkt på takbalkarna c/c #r.g.cc, hård träfiberskiva 3 mm, Hunton Nativo 170 mm, ångbroms Hunton Intello Plus (Sd #r.in.ab), installationsskikt 45 mm och gips. Spalten och kanalen över nock- och dalbalkarna är minst #r.g.spalt mm. Alla takfötter mot det fria är öppna med insektsnät, också vid förskjutningarna. Vägen genom spalten är #r.g.vagar m beroende på var i taket facket ligger (@fig-plan a). Takfönstren TF1–TF3 (K-03) bryter två fack vardera. Badrummet (planritning 201 rev 02) ligger under TF1.

*Modellen.* Hela taket delas i #r.g.remsor remsor längs husets längd, ungefär ett fack var, och varje remsa i takfall mellan takfötter, nockar, dalar och fönster, med #r.g.celler celler per takfall. För varje timme #k.period beräknas:
- *luftflödet* i alla fack av vindtrycket vid takfötterna och gavelöppningarna och av den termiska stigkraften i varje takfall. Vid takfötterna används $Delta c_p$ = 0,48 cos(1,3 φ) + 0,22 (Månhardt m.fl. 2021 efter Gullbrekken m.fl. 2018), i gavlarna Swami & Chandra. Tryckfallet räknas med friktion i spalten, insektsnät, in- och utlopp och vändningar vid nockar och dalar. Där facken möts är flödet in lika med flödet ut;
- *temperaturerna* i plåten (sol, utstrålning mot himlen, vind), råsponten, luften och träfiberskivan, med värmeflödet inifrån. Den metalliska zink-magnesiumytan har solabsorption #r.in.alfa och låg emissivitet, #r.in.eps (blank zink och förzinkad plåt 0,65–0,7 respektive 0,15–0,25);
- *råsponten* torkar bara nedåt, mot spalten, eftersom underlagspappen är ångtät;
- *fukten* i råspontens yta och kärna, i träfiberskivan med isoleringens överdel och i luften i spalten, med diffusion inifrån genom ångbromsen. Ångbromsens Sd följer fuktigheten över den. Inneklimatet är fuktklass 2 (#r.in.fukt g/m³), badrummet fuktklass 4 (#r.in.bad g/m³);
- *mögelindex M* (VTT-modellen, furu splintved) på råspontens undersida och på träfiberskivan. M < 1 betyder ingen påväxt, M = 1 begynnande påväxt som syns i mikroskop och M = 3 påväxt som syns med blotta ögat.

Klimatet är ERA5 för Resö (#k.T °C, RF #k.RF %, vind #k.U m/s i medel på 10 m). Flöde och temperatur itereras #r.g.varv gånger per timme. Kontroller: med #r.kontroll.celler celler per takfall blir största M #r.kontroll.M_celler (#r.kontroll.M_bas) och med #r.kontroll.varv iterationer #r.kontroll.M_varv. Massbalansen i varje nod stämmer inom #r.kontroll.massbalans m³/s. En oberoende kontrollmodell med egen kod ger samma rangordning mellan vägarna och utförandena och samma tidsförlopp, med upp till hälften så höga värden på de korta vägarna.

#figure(image("fig_plan.svg", width: 100%), caption: [Taket i plan med husets längd uppåt. Färgen visar det största mögelindexet 2014–2023 på råspontens undersida i varje takfall. Mörka rutor: takfönster. Heldragna linjer: nockar, streckade: dalar. Pilar: gavelöppningar. Blått band: kanal längs nock och dal över balkarna. e) som b men med målad plåt (emissivitet 0,9).]) <fig-plan>

= Resultat

#table(
  columns: (1fr, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  [Fall], [M råspont], [Yta M ≥ 1 (m²)], [M skiva], [Luft (m/s)], [Sämst],
  ..r.tab.map(t => ([#t.namn], [*#t.M*], [#t.yta1], [#t.Miso], [#t.v], [#t.var])).flatten(),
)
#liten[Mögelindex: största värde 2014–2023 (för fallen med våt råspont från 1 oktober 2013) över hela taket. Yta: den del av takets #r.g.yta m² där M ≥ 1. Skiva: träfiberskivan med isoleringens överdel. Luft: luftens hastighet i spalten, median över alla timmar och fack. Sämst: takfallets riktning och vägens längd där M är störst.]

#figure(image("fig_ar.svg", width: 100%), caption: [a) Största mögelindex på råspontens undersida varje år, korta vägar (heldraget) och den 16,3 m långa vägen (streckat), med omluftning vid fönstren: zink-magnesiumplåt med olika vindtryck, oventilerat och, som jämförelse, målad plåt. b) Luftens hastighet längs den långa vägen med vind och sol och med bara sol och stigkraft. Lugnt: vind under 2 m/s; sol: global strålning över 300 W/m².]) <fig-ar>

*Varför skiljer två takfall med samma luft?* Flödet är detsamma upp på det ena takfallet och ned på det andra, men mögelindex beror på råspontens temperatur och fuktighet vid ytan, inte på flödet. Takfallen mot nordväst får under november–mars ca #s.sol_NV kWh/m² sol per vinter, de mot sydost ca #s.sol_SO. Råsponten mot nordväst blir därför kallare, och RF vid ytan är i medel #s.rf_NV % under vintern mot #s.rf_SO % mot sydost. Mögelindex växer mycket snabbt med RF över ca 85 %, så några procentenheter gör stor skillnad; med målad plåt ligger takfallen mot sydost mellan 1 och 2 och de mot nordväst över 3 (@fig-plan e). Längs vägen värms luften av värmeförlusten genom isoleringen, så den är kallast och fuktigast i förhållande till råsponten där den kommer in. Luften går oftast från sydost mot nordväst (sydostlig vind och solen). Därför är det värst vid takfoten mot sydost och högst upp mot nordväst, strax efter nocken. Den solvarma råsponten mot sydost skyddar snarare det nedströms takfallet: utan fuktutbyte där blir det mot nordväst något sämre.

*Luftflödet.* Längs den långa vägen rör sig luften i median med #fl.omluft_lang_alla m/s, ca 60 omsättningar per timme (RäknaF räknar med 20). Vind från sydost eller nordväst ger 0,4–0,5 m/s, vind längs nockarna, som är vanligast, ca 0,2 m/s. Lugna soliga timmar driver solen ensam #fl.vind0_lang_lugn_sol m/s, i #fl.vind0_lang_mot_NV % av dem från sydost mot nordväst. På eftermiddagen kan flödet vända, när kvällssolen värmer takfallen mot nordväst, och på natten står luften nästan still utan vind (@fig-ar b).

*Takytan, vinden och spalthöjden.* Mögelindex beror mest på hur mycket plåten kyls mot natthimlen. Med zink-magnesiumplåten (emissivitet #r.in.eps) blir det som mest #S.omluft.M2, med ny blank plåt #S.zm_ny.M2, med åldrad plåt #S.zm_patina.M2 och med målad plåt #S.malad.M2 (@fig-plan e). Med halva vindtrycket blir det #S.vind05.M2 och med en fjärdedel #S.vind025.M2. Då samlas fukt i det sista takfallet mot nordväst på den långa vägen: de solvarma takfallen mot sydost torkar på dagen, och luften, som då går långsamt, lämnar fukten i det skuggiga takfallet längst bort. Utan fuktutbyte i takfallen mot sydost försvinner effekten i beräkningen. Vid platsens vind späds fukten i stället ut med uteluft. En större spalt ger mer luft vid svag vind: vid en fjärdedel av vindtrycket blir M #S.s25_vind025.M med 25 mm, #S.vind025.M med 30 mm, #S.s36_vind025.M med 36 mm och #S.s45_vind025.M med 45 mm. Vid full vind ger både mindre och större spalt något högre värden (25 mm #S.s25.M2, 36 mm #S.s36.M2, 45 mm #S.s45.M2), eftersom mer uteluft kommer in vid takfoten. Strypta takfötter ger #S.takfot_strypt.M2 vid full vind men, liksom en mindre spalt, mindre luft när det blåser lite. Står huset tomt på vintern med 10 °C inne blir värmeförlusten, som annars torkar spalten, mindre: M #S.tomt_vinter.M2.

*Byggfukt.* Med råsponten på 20 % när taket stängs den 1 oktober blir M #S.vat.M med omluftning, #S.takfot_strypt_vat.M med strypta takfötter och #S.oventilerad_vat.M i en oventilerad spalt. Fukten torkar ut, i den oventilerade spalten inåt genom vindskivan, isoleringen och Intello Plus på sommaren. Utan omluftning torkar också fönsterfacken ut (M #S.bas_vat.M_fon). En oventilerad spalt saknar ändå marginal mot läckage, och enligt kontrollberäkningen blir den känslig om råsponten är våtare än 20 % när taket stängs.

*Takfönstren.* Utan omluftning är luften i fönsterfacken helt stilla och M #S.bas.M_fon, som i en oventilerad spalt. Med omluftning rör sig luften där med #S.omluft.v_fon m/s, mot #S.omluft.v m/s i hela taket, och M blir #S.omluft.M_fon, som i resten av taket. 300 mm fri längd i ströläkten ger nästan samma flöde (#S.omluft300.v_fon m/s) som 600 mm.

*Gavelöppningar.* I ändfacken bakom öppningarna kommer uteluften in vid dalarnas och nockarnas ändar. Mögelindex blir #S.omluft_gavel.M2 med öppningar, #S.omluft.M2 utan, och #S.gavel_vind05.M2 mot #S.vind05.M2 med halva vindtrycket. Med kanal längs nockar och dalar blir det #S.omluft_samling_gavel.M2, med bara kanalen #S.omluft_samling.M2.

= Rekommendationer

#figure(image("fig_omluft.svg", width: 72%), caption: [Omluftning vid ett takfönster, principskiss sedd uppifrån med nocken uppåt. Mått i mm.]) <fig-omluft>

+ *Omluftning vid takfönstren* (och skorstenen om den hamnar i taket), @fig-omluft. Ovanför och under varje fönster får ströläkten på avväxlingarna och på kortlingen uppehåll, så att luften i de två brutna facken går åt sidan till grannfacken. Fri längd minst 300 mm per läktlinje inom 1 m från fönstret, i uppehåll om högst 150–200 mm som förskjuts mellan intilliggande linjer så att råsponten alltid bärs. Sidoöppningen blir då minst 300 × #r.g.spalt mm = 9 000 mm² per linje; i beräkningen ger det nästan samma flöde i fönsterfacken som 600 mm.
+ *Spalten, helst 36 mm.* Vid platsens vind räcker #r.g.spalt mm fri höjd (M #S.omluft.M2, med 36 mm #S.s36.M2). Är läget mer skyddat än vädermodellen visar, ger #r.g.spalt mm M #S.vind025.M men 36 mm #S.s36_vind025.M vid en fjärdedel av vindtrycket, och 36 mm är också SINTEF:s praktiska minimum. Måttet gäller fri höjd efter toleranser: ströläkten väljs så att skivornas övermått och buktning ryms. Spalten går fri över alla nock- och dalbalkar till nästa takfall. Vid dalarna ska balkens överkant ligga i takplanens skärning, som i modellen, eller dalens botten byggas plan med minst #r.g.spalt mm fritt över balken. Om ströläkten läggs över balkarna får den inte stänga facken.
+ *Takfötterna* öppnas längs alla fasader, också vid förskjutningarna. Insektsnätet ska ha minst 60 % fri öppning och kunna rensas. Inga öppningar i gavlarna och inga extra öppningar vid nockarna.
+ *Vindskivan* ska vara ångöppen och ha ett deklarerat Sd, högst ca 0,3 m. Skivans Sd påverkar råsponten lite (M #S.masonit006.M, #S.omluft.M och #S.masonit06.M med Sd 0,06, 0,3 och 0,6 m). En öppnare skiva låter isoleringen torka utåt; dess överdel får något mer fukt men ligger långt under 1 (M #S.masonit006.Miso). Oljehärdad board saknar deklarerat Sd och har troligen 0,3–0,6 m. Ett tunt alternativ med dokumenterade värden är hård träfiberskiva godkänd som vindskydd under en luftspalt, t.ex. 3,2 mm enligt SINTEF TG 2245 (Sd ≤ 0,28–0,36 m).
+ *Badrummet.* Intello Plus räcker också där. Med fuktklass 4 blir mögelindex på träfiberskivan över badrummet #S.bad.Miso_bad, mot #S.omluft.Miso i resten av taket, och #S.bad_sd10.Miso_bad med en ångbroms med fast Sd 10 m. Råsponten påverkas inte. Det som avgör är att ångbromsen är helt lufttät: tejpade skarvar, ansluten till takfönstrets ångspärrskrage och utan genomföringar, med installationerna i installationsskiktet, och att badrummet har frånluft med forcering vid dusch.
+ *Takytan.* Den metalliska zink-magnesiumytan strålar lite mot natthimlen, så plåten och råsponten kyls mindre på klara nätter än under en målad plåt. Det är den viktigaste enskilda faktorn: med målad plåt (emissivitet 0,9) blir mögelindex #S.malad.M i stället för #S.omluft.M. Plåten ska därför inte målas eller beläggas. Åldrad, mörkare plåt (solabsorption 0,8, emissivitet 0,4) ger #S.zm_patina.M och ny blank plåt #S.zm_ny.M.
+ *Torrt vid inbyggnad.* Råspont och takbalkar torra (högst 16–18 %), isoleringen högst ca 10 % (Hunton), och taket skyddas mot regn under bygget. Intello Plus monteras och tejpas innan huset värms upp och kopplas lufttätt till takfönstrens ångspärrskragar och till alla genomföringar. Installationsskiktet isoleras inte (TG 20557).

*Osäkerheter.* VTT-modellen för furu splintved är den känsligaste klassen; gran och kärnved växer långsammare. M < 1 är ett strängt krav för en yta som ventileras med uteluft: ASHRAE 160 godtar M ≤ 3, och en skyddad furuyta i uteluften på platsen når enligt kontrollberäkningen M 4–6 varje år. Absolutvärdena beror på modellens val (ytskiktets tjocklek, ytans beskaffenhet) och kan skilja en faktor 2; jämförelserna mellan utförandena är säkrare. Den viktigaste osäkra indatan är plåtens emissivitet: zink-magnesium har låg emissivitet som ny, men den kan öka med patina och smuts (emissivitet 0,4 ger #S.zm_patina.M2, målad yta #S.malad.M2). Fukttransporten längs den långa vägen vid svag vind beror på råspontens fuktbuffring och är inte verifierad med mätningar. Vinden är ERA5 för en ruta på ca 10 × 10 km; ett skyddat läge ger mindre luft, vilket med #r.g.spalt mm spalt kan ge högre mögelindex i det sista takfallet mot nordväst (avsnitt 3). Snö på taket, plåtens och råspontens värmetröghet och luftläckage inifrån ingår inte. Snö och värmetröghet minskar utstrålningens nattliga avkylning och ligger alltså på säker sida; läckage gör det inte, och ångbromsen måste därför vara lufttät. Tio år med den extremt milda vintern 2019/20 är med, och framtidens vintrar väntas bli mildare och blötare. Siffrorna är bäst som jämförelse mellan utförandena.

#liten[*Källor.* Uvsløkk, SINTEF 2020:00500 _Lufting av tak_ (2021). Byggforsk 525.101 (2021). Månhardt m.fl., _J. Phys.: Conf. Ser._ 2069 (2021) 012018. Gullbrekken m.fl., _J. Wind Eng. Ind. Aerodyn._ 175 (2018). Mundt-Petersen, SBUF 13098 (2018). Bunkholt m.fl., _J. Phys.: Conf. Ser._ 2069 (2021) 012007. Hukka & Viitanen, _Wood Sci. Technol._ 33 (1999); Ojanen m.fl. (2010). ETA-18/1146 (Intello Plus). SINTEF TG 2245 (Huntonit Luftespalte), TG 20557. ÖNORM B 4119:2018. Swami & Chandra, ASHRAE Trans. 94 (1988). ERA5 via Open-Meteo (CC BY 4.0).]
