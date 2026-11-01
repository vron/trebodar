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
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 3.5pt, y: 1.8pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: it => pad(top: 2pt, bottom: 2pt, it)
#show figure.caption: set text(size: 8pt)
#set figure(gap: 3pt)
#set list(spacing: 0.5em)
#set enum(spacing: 0.5em)
#let liten(body) = text(size: 8pt, body)
#let s = r.sam
#let k = r.kl
#let fl = r.fl
#let S = r.S
#let R = r.rek

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

Luftspalten mellan råsponten och vindskivan (hård träfiberskiva) går obruten från takfot till takfot över nockar och dalar, som längst #r.g.vag_max m. Här bedöms om den ventileras tillräckligt, vad takfönstren, eventuella gavelöppningar, vindskivan och badrummet betyder och om en oventilerad spalt räcker. Måttet är mögelindex M (VTT) på råspontens undersida: målet är M < 1 (ingen påväxt), och ASHRAE 160 godtar M ≤ 3.

*Beslut och utförande*
+ Plåten: zink-magnesium utan organisk beläggning. Den låga emissiviteten avgör; målad plåt skulle ge M #S.malad.M.
+ Spalten: #R.spalt mm fri höjd efter toleranser, också över nock- och dalbalkarna.
+ Omluftning vid varje takfönster: uppehåll i ströläkten, minst #R.omluft mm och gärna 600 mm fritt per läktlinje ovanför och under fönstret (@fig-omluft).
+ Inga öppningar i gavlarna. Alla takfötter öppna med insektsnät.
+ Dalbalkarnas överkant i takplanens skärning, inte i takbalkarnas överkant; K-03 och modell-todo punkt 7 ändras.
+ Vindskiva med deklarerat Sd, gärna högst ca 0,3 m. Intello Plus, helt lufttät, också över badrummet.
+ Står huset tomt på vintern: håll hellre 15 än 10 °C inne.

*Slutsatser*
- *Den obrutna spalten fungerar.* Luften går genom alla sex takfallen i följd, driven av vinden och av solen: de tre solvarma takfallen mot sydost samverkar och driver luften från sydost mot nordväst. Längs den långa vägen rör sig luften i median med #fl.omluft_lang_alla m/s.
- *Med zink-magnesiumplåten klarar sig råsponten.* Med #R.spalt mm och omluftning blir M som mest #S.rek.M och med #r.g.spalt mm #S.omluft.M, i båda fallen efter de extremt milda och blöta vintrarna 2019/20 och 2020/21; alla andra år ligger under 0,6. Den långa vägen är inte sämre än de korta takfallen i husets ändar, som är vanliga sadeltak (#S.omluft.M_lang mot #S.omluft.M_kort; med målad plåt #S.malad.M_lang mot #S.malad.M_kort).
- *#R.spalt mm ger marginal mot ett skyddat läge.* Vid platsens vind är #r.g.spalt och #R.spalt mm i praktiken lika (#S.omluft.M och #S.s36.M). Med halva vindtrycket blir det #S.vind05.M och #S.s36_vind05.M, med en fjärdedel #S.vind025.M och #S.s36_vind025.M. Vid svag vind förs nämligen fukt från de solvarma takfallen mot sydost med den långsamma luften och samlas i det sista takfallet mot nordväst, mest i facken bakom takfönstren.
- *Spalten ska ventileras.* Utan luftning eller helt utan vind blir M lägst i beräkningen (#S.oventilerad.M och #S.vind0.M; #S.oventilerad_vat.M med råspont på 20 % när taket stängs), eftersom ingen fuktig uteluft kommer in. Men en oventilerad spalt torkar bara inåt, långsamt och på sommaren, så vatten från läckage eller mer byggfukt torkar inte ut, och svag luftning är ogynnsam. Den luftade spalten med marginal för svag vind är det robusta valet.
- *Gavelöppningar ger ingen förbättring.* M blir #S.omluft_gavel.M mot #S.omluft.M, och den långa vägen sämre (#S.omluft_gavel.M_lang mot #S.omluft.M_lang). De släpper också in slagregn och snö, särskilt i gavlarna mot sydväst.
- *Tomt hus på vintern.* Med 10 °C inne oktober–april blir värmeförlusten, som torkar spalten, mindre: M #S.rek_tomt.M med rekommenderat utförande (#S.tomt_vinter.M med #r.g.spalt mm), med 15 °C #S.rek_tomt15.M (#S.tomt15.M). Det gäller bara de extremt milda vintrarna 2019/20 och 2020/21, övriga år under 0,7. Det är över målet men långt under ASHRAE 160:s gräns, och ju varmare huset hålls, desto bättre.

= Taket och modellen

*Taket.* Tre sadeltak, #r.g.lutning°, med nockarna längs husets längd och dalar emellan. Uppbyggnad enligt F-01 med plåt, papp och spalt enligt denna utredning: bandtäckning av zink-magnesiumbelagd plåt, blank och omålad; underlagspapp av bitumen (t.ex. T-Roof YEP 2500, ångtät); råspont 20 mm; luftspalt mellan ströläkt på takbalkarna c/c #r.g.cc; vindskiva 3 mm; Hunton Nativo 170 mm; ångbroms Hunton Intello Plus (Sd #r.in.ab); installationsskikt 45 mm; gips. Spalten har sin fria höjd även över nock- och dalbalkarna. Alla takfötter mot det fria är öppna med insektsnät, också där huskropparna är förskjutna mot varandra. Vägen genom spalten är #r.g.vagar m beroende på var i taket facket ligger (@fig-plan a). Takfönstren TF1–TF3 (K-03) bryter två fack vardera. Badrummet (planritning 201 rev 02) ligger under TF1.

*Modellen.* Hela taket delas i #r.g.remsor remsor längs husets längd, ungefär ett fack var, och varje remsa i delsträckor mellan takfötter, nockar, dalar och fönster, med #r.g.celler celler var. För varje timme #k.period beräknas:
- *luftflödet* i alla fack av vindtrycket vid takfötterna och gavelöppningarna och av den termiska stigkraften i varje takfall. Vid takfötterna används $Delta c_p$ = 0,48 cos(1,3 φ) + 0,22, där φ är vindens vinkel mot fasadens normal (Månhardt m.fl. 2021 efter Gullbrekken m.fl. 2018), i gavlarna Swami & Chandra. Vindhastigheten är ERA5 på 10 m, utan reduktion. Tryckfallet räknas med friktion i spalten, insektsnät, in- och utlopp och vändningar vid nockar och dalar. Där facken möts är flödet in lika med flödet ut;
- *temperaturerna* i plåten (sol, utstrålning mot himlen, vind), råsponten, luften och vindskivan, med värmeflödet inifrån. Zink-magnesiumytan har solabsorption #r.in.alfa och emissivitet #r.in.eps (blank zink och förzinkad plåt 0,65–0,7 respektive 0,15–0,25);
- *fukten* i råspontens yta och kärna, i vindskivan med isoleringens överdel och i luften i spalten, med diffusion inifrån genom ångbromsen, vars Sd beror på medelfuktigheten på dess båda sidor. Råsponten torkar bara nedåt, eftersom pappen är ångtät. Inneklimatet är fuktklass 2 (#r.in.fukt g/m³), badrummet fuktklass 4 (#r.in.bad g/m³), SS-EN ISO 13788;
- *mögelindex M* (VTT-modellen, furu splintved) på råspontens undersida och på vindskivan. M = 1 är begynnande påväxt som syns i mikroskop och M = 3 påväxt som syns med blotta ögat.

Klimatet är ERA5 för Resö (#k.T °C, RF #k.RF %, vind #k.U m/s i medel på 10 m). Flöde och temperatur itereras #r.g.varv gånger per timme. Kontroller: med #r.kontroll.celler celler per delsträcka blir största M #r.kontroll.M_celler i stället för #r.kontroll.M_bas och med #r.kontroll.varv iterationer #r.kontroll.M_varv. Massbalansen i varje nod stämmer inom #r.kontroll.massbalans m³/s. En oberoende kontrollmodell med egen kod, räknad med målad plåt, ger samma rangordning mellan vägarna och utförandena och samma tidsförlopp.

#figure(image("fig_plan.svg", width: 100%), caption: [Taket i plan med husets längd uppåt (sydväst uppåt, N visar norr). Färgen visar det största mögelindexet 2014–2023 på råspontens undersida i varje delsträcka. SO och NV: takfallens riktning i vänster huskropp. Väg: luftens väg från takfot till takfot. Mörka rutor: takfönster. Heldragna linjer: nockar, streckade: dalar. Pilar: gavelöppningar.]) <fig-plan>

= Resultat

#table(
  columns: (1fr, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right),
  [Fall], [M råspont], [Yta M ≥ 1 (m²)], [M vindskiva], [Luft (m/s)], [Sämst],
  ..r.tab.map(t => if t.grupp { (table.cell(colspan: 6, text(weight: "bold", style: "italic", t.namn)),) } else {
    ([#if t.namn.starts-with("*") { strong(t.namn.trim("*")) } else { t.namn }], [*#t.M*], [#t.yta1], [#t.Miso], [#t.v], [#t.var])
  }).flatten(),
)
#liten[Mögelindex: största värde 2014–2023 (för fallen med våt råspont från 1 oktober 2013) över hela taket. Yta: den del av takets #r.g.yta m² där M ≥ 1. Vindskiva: vindskivan med isoleringens överdel. Luft: luftens hastighet i spalten, median över alla timmar och fack. Sämst: takfallets riktning och vägens längd, eller fönsterfacken, där M är störst. Om inget annat anges: 30 mm spalt, omluftning 600 mm, zink-magnesiumplåt och full vind.]

#figure(image("fig_ar.svg", width: 100%), caption: [a) Största mögelindex på råspontens undersida varje år, i hela taket (heldraget) och på den 16,3 m långa vägen utanför fönsterfacken (streckat), med #r.g.spalt mm och omluftning. b) Luftens hastighet längs den långa vägen med verkligt väder och utan vind (bara sol och stigkraft). Lugnt: vind under 2 m/s; sol: global strålning över 300 W/m²; natt: ingen sol.]) <fig-ar>

*Varför skiljer sig takfallen åt när luften är densamma?* Med zink-magnesiumplåten är skillnaden liten (#S.omluft.M vid takfoten mot sydost, där uteluften oftast kommer in). Med målad plåt syns den tydligt (@fig-plan f): flödet är detsamma upp på det ena takfallet och ned på det andra, men mögelindex beror direkt på råspontens temperatur och fuktighet vid ytan, inte direkt på flödet. Takfallen mot nordväst får under november–mars ca #s.sol_NV kWh/m² sol per vinter, de mot sydost ca #s.sol_SO. Råsponten mot nordväst blir därför kallare, RF vid ytan är högre (i medel #s.rf_NV mot #s.rf_SO % under vintern), och mögelindex växer mycket snabbt med RF över ca 85 %. Med målad plåt ligger därför takfallen mot sydost på de korta vägarna mellan 1 och 2 och de mot nordväst över 3.

*Luftflödet.* Längs den långa vägen rör sig luften i median med #fl.omluft_lang_alla m/s, ca 60 omsättningar per timme (RäknaF räknar med 20). Under lugna, soliga timmar, bara ca #fl.andel_lugn_sol % av tiden, driver solen ensam luften med #fl.vind0_lang_lugn_sol m/s, i #fl.vind0_lang_mot_NV % av dem från sydost mot nordväst. På eftermiddagen kan flödet vända, när kvällssolen värmer takfallen mot nordväst. Lugna nätter rör sig luften med #fl.omluft_lang_lugn_natt m/s; helt utan vind står den nästan still (@fig-ar b).

*Vind och spalthöjd.* Med full vind ökar M något med spalten utanför fönsterfacken (36 mm #S.s36.M, 45 mm #S.s45.M), eftersom mer fuktig uteluft kommer in. Vid svag vind är det tvärtom: då kan fukt från de solvarma takfallen mot sydost, som torkar på dagen, föras med den långsamma luften och lämnas i det skuggiga sista takfallet mot nordväst, mest bakom takfönstren där omluftningen ger mindre luft. Med en fjärdedel av vindtrycket blir M #S.s25_vind025.M med 25 mm, #S.vind025.M med 30 mm, #S.s36_vind025.M med 36 mm och #S.s45_vind025.M med 45 mm. Med 25 mm blir flödet för litet bakom takfönstren redan vid full vind (#S.s25.M). Strypta takfötter (fyra gånger större tryckfall) ger #S.takfot_strypt.M vid full vind men #S.takfot_strypt_vind025.M vid en fjärdedel av vindtrycket. Rekommenderat utförande, #R.spalt mm med #R.omluft mm omluftning, ger #S.rek.M, #S.rek_vind05.M och #S.rek_vind025.M vid full, halv och en fjärdedels vindtryck.

*Plåten.* Med ny blank plåt blir M #S.zm_ny.M, med åldrad plåt (solabsorption 0,8, emissivitet 0,4) #S.zm_patina.M och med målad plåt #S.malad.M.

*Byggfukt.* Med råsponten på 20 % när taket stängs den 1 oktober blir M #S.vat.M med omluftning, #S.takfot_strypt_vat.M med strypta takfötter och #S.oventilerad_vat.M i en oventilerad spalt. Fukten torkar ut, i den oventilerade spalten inåt genom vindskivan, isoleringen och Intello Plus på sommaren. Utan omluftning torkar också fönsterfacken ut (M #S.bas_vat.M_fon).

*Takfönstren.* Utan omluftning är luften i fönsterfacken helt stilla (M #S.bas.M_fon, som i en oventilerad spalt). Med omluftning rör sig luften där med #S.omluft.v_fon m/s mot #S.omluft.v m/s i hela taket, och M blir #S.omluft.M_fon, lägre än i resten av taket. 300 mm fri längd i ströläkten ger i fönsterfacken #S.omluft300.v_fon m/s, mot #S.omluft.v_fon med 600 mm.

*Gavelöppningar och kanal längs nock och dal.* I ändfacken bakom gavelöppningarna kommer uteluften in vid dalarnas och nockarnas ändar. Om ströläkten inte går över balkarna bildas en kanal längs nocken och dalen som förbinder facken; den ger ingen förbättring (#S.omluft_samling.M), med gavelöppningar #S.omluft_samling_gavel.M. Ströläkten kan alltså gå obruten över balkarna, om den inte stänger facken.

*Inneklimatet och vindskivan.* Badrummet med fuktklass 4 ger M #S.bad.Miso_bad på vindskivan över badrummet med Intello Plus och #S.bad_sd10.Miso_bad med en ångbroms med fast Sd 10 m; råsponten påverkas inte. Fuktklass 3 i hela huset ger #S.fukt6.M. Vindskivans Sd påverkar råsponten lite (M #S.masonit006.M, #S.omluft.M och #S.masonit06.M med Sd 0,06, 0,3 och 0,6 m).

= Rekommendationer

#figure(image("fig_omluft.svg", width: 72%), caption: [Omluftning vid ett takfönster, principskiss sedd uppifrån med nocken uppåt. Mått i mm.]) <fig-omluft>

+ *Omluftning vid takfönstren* (och skorstenen om den hamnar i taket), @fig-omluft. Ovanför och under varje fönster får ströläkten på avväxlingarna och på kortlingen uppehåll, så att luften i de två brutna facken går åt sidan till grannfacken. Fri längd minst #R.omluft mm och gärna 600 mm per läktlinje inom 1 m från fönstret, i uppehåll om högst 200 mm som förskjuts mellan intilliggande linjer så att råsponten alltid bärs. Sidoöppningen blir då minst #R.omluft × #R.spalt = #R.oppning mm² per linje. Vid mycket svag vind (en fjärdedel av vindtrycket) ger #R.omluft mm M #S.rek_vind025.M i fönsterfacken och 600 mm #S.s36_vind025.M.
+ *Spalten, #R.spalt mm.* Måttet gäller fri höjd efter toleranser: ströläkten väljs så att skivornas övermått och buktning ryms. Spalten går fri över alla nock- och dalbalkar till nästa takfall. SINTEF anger 36 mm som minimum för korta takfall och mer för längre vägar, för att undvika snösmältning; den långa vägen här ligger utanför tabellen och bedöms med beräkningen.
+ *Dalbalkarna.* Dalbalkens överkant ska ligga i takplanens skärning, ca 55 mm under takbalkarnas överkant vid balkens sidor, som i husets 3D-modell, eller dalens botten byggas plan med spaltens fria höjd över balken. K-03 och modell-todo punkt 7 anger i dag överkanten i takbalkarnas överkant, vilket stänger spalten vid dalarna, och ska ändras.
+ *Takfötterna* öppnas längs alla takfötter, också vid förskjutningarna. Insektsnätet ska ha minst 60 % fri öppning och kunna rensas. Inga öppningar i gavlarna. Extra öppningar vid nockarna har inte prövats och behövs inte.
+ *Plåten* hålls blank, utan organisk beläggning eller färg: den strålar då ut lite värme mot natthimlen och kyler inte råsponten.
+ *Vindskivan* ska ha ett deklarerat Sd, gärna högst ca 0,3 m. Beräkningen påverkas lite av Sd, men en ångöppen skiva låter isoleringen torka utåt om den blir fuktig. Oljehärdad board saknar deklarerat Sd och har troligen 0,3–0,6 m. Ett tunt alternativ med dokumenterade värden är hård träfiberskiva godkänd som vindskydd under en luftspalt, t.ex. 3,2 mm enligt SINTEF TG 2245 (Sd ≤ 0,28–0,36 m).
+ *Badrummet.* Intello Plus räcker. Det som avgör är att ångbromsen är helt lufttät: tejpade skarvar, ansluten till takfönstrets ångspärrskrage och utan genomföringar, med installationerna i installationsskiktet, och att badrummet har frånluft med forcering vid dusch.
+ *Torrt vid inbyggnad.* Råspont och takbalkar torra (högst 16 %), isoleringen högst ca 10 % (Hunton), och taket skyddas mot regn under bygget. Intello Plus monteras och tejpas innan huset värms upp. Installationsskiktet isoleras inte (TG 20557).
+ *Tomt hus på vintern.* Håll hellre 15 än 10 °C inne när huset står tomt oktober–april: värmeförlusten från ett varmare hus torkar spalten.

*Osäkerheter.* VTT-modellen för furu splintved är den känsligaste klassen; gran och kärnved växer långsammare. Absolutvärdena beror på modellens val (ytskiktets tjocklek, ytans beskaffenhet) och kan skilja en faktor 2; jämförelserna mellan utförandena är säkrare. Två indata väger tyngst. Vinden: ERA5 på 10 m används direkt vid takfötterna, och fallen med mindre vind skalar bara vindtrycket, inte vindens kylning av plåten; en fjärdedel av vindtrycket motsvarar halva vindhastigheten. Plåtens emissivitet: den kan öka med patina och smuts. Fukttransporten längs den långa vägen vid svag vind beror på råspontens fuktbuffring och är inte verifierad med mätningar. Snö på taket, plåtens och råspontens värmetröghet och luftläckage inifrån ingår inte. Snö och värmetröghet minskar den nattliga avkylningen genom utstrålning, men snö kan också sätta igen näten vid takfötterna; läckage gör att ångbromsen måste vara lufttät. Perioden omfattar den extremt milda vintern 2019/20, och framtidens vintrar väntas bli mildare och blötare.

#liten[*Källor.* Uvsløkk, SINTEF 2020:00500 _Lufting av tak_ (2021). Byggforsk 525.101 (2021). SINTEF TG 20239 (tabell 3). Månhardt m.fl., _J. Phys.: Conf. Ser._ 2069 (2021) 012018. Gullbrekken m.fl., _J. Wind Eng. Ind. Aerodyn._ 175 (2018). Mundt-Petersen, SBUF 13098 (2018): flödet under råsponten så litet som möjligt men tillräckligt för att torka. Bunkholt m.fl., _J. Phys.: Conf. Ser._ 2069 (2021) 012007. Hukka & Viitanen, _Wood Sci. Technol._ 33 (1999); Ojanen m.fl. (2010). ASHRAE 160-2016. SS-EN ISO 13788. RäknaF. ETA-18/1146 (Intello Plus). SINTEF TG 2245, TG 20557. ÖNORM B 4119:2018. Swami & Chandra, ASHRAE Trans. 94 (1988). ERA5 via Open-Meteo (CC BY 4.0).]
