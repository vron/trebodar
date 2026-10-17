#let r = json("resultat.json")
#let p = r.projekt
#let l = r.ly

#set document(title: p.objekt, author: p.upprattad)
#set page(
  paper: "a4",
  margin: (x: 18mm, top: 20mm, bottom: 14mm),
  header: context [
    #set text(8pt)
    #grid(columns: (1fr, auto), p.namn, [#p.dokument rev #p.revision · Sida #counter(page).display() av #counter(page).final().first()])
    #v(-2pt)
    #line(length: 100%, stroke: 0.4pt)
  ],
)
#set text(font: "Carlito", size: 9.5pt, lang: "sv")
#set par(justify: false, leading: 0.55em, spacing: 0.75em)
#set heading(numbering: "1")
#show heading.where(level: 1): it => {
  v(3pt)
  block(below: 5pt, text(size: 11pt, weight: "bold")[#counter(heading).display() #h(4pt) #it.body])
}
#set table(stroke: (x, y) => (top: if y == 0 { 0.6pt } else { 0.3pt + luma(170) }, bottom: 0.6pt), inset: (x: 4pt, y: 2.4pt))
#show table.cell.where(y: 0): set text(weight: "bold")
#show figure.caption: set text(size: 8.5pt)
#set figure(gap: 4pt)

// ---------------------------------------------------------------- titelblock
#table(
  columns: (auto, 1fr, auto, auto),
  stroke: 0.4pt,
  inset: 4pt,
  [*Projekt*], p.namn, [*Dokument*], [#p.dokument, rev #p.revision],
  [*Objekt*], p.objekt, [*Datum*], p.datum,
  [*Innehåll*], [Egentyngden vid lyft, avstånd mellan lyftpunkterna], [*Upprättad*], p.upprattad,
  [*Underlag*], p.underlag, [*Status*], [Eget underlag, ingår inte i handlingarna till tekniskt samråd],
)

= Syfte och förutsättningar

Nock- och dalbalkarna (K-01) är limträ GL30c 200 × 170 med limmade och skruvade stålplåtar 200 × 10 i över- och underkant på delar av längden. Här kontrolleras att egentyngden inte skadar balkarna när de lyfts i två punkter, med stroppar i en triangel upp till kroken, och vilket avstånd mellan lyftpunkterna som behövs.

- *Egentyngd:* #l.q_plat kN/m med plåtar, #l.q_utan kN/m utan (limträ och distansreglar). Plåtarna samverkar fullt med limträet (limmade); utan plåt bär limträet ensamt.
- *Lastfaktor:* #l.gG × dynamisk faktor #l.dyn = #l.faktor på egentyngden: ryck, inbromsning och ojämn hantering, långt över ett långsamt kranlyft (1,1–1,3).
- *Bärförmåga:* limträ $f_"m,d" = k_"mod" k_h f_"m,k" slash gamma_M$ = #l.fmd MPa ($k_"mod"$ = #l.kmod momentan last, $k_h$ = #l.kh), stål $f_"yd"$ = #l.fyd MPa. Stropparnas tryck i balken mellan lyftpunkterna ingår.
- *Krav:* utnyttjandet högst #l.mal med faktorerna ovan, alltså dubbel marginal mot brott. Avståndet har itererats i steg om #l.steg mm för varje balk och avrundats uppåt till #l.avrunda mm, så att samma avstånd gäller alla balkar.

= Lyft i två punkter, s = #l.s mm

#figure(image("fig_lyft.svg", width: 82%), caption: [Den styrande balken med plåtarna (grå), tyngdpunkten och lyftpunkterna, stroppar i #l.vinkel° mot balken.])

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right, right, right),
  [Balk], [L (mm)], [Vikt (kN)], [Tyngdp. x], [Lyftpunkter x], [Stropp (kN)], [$M_d$ (kNm)], [$sigma_"trä"$ (MPa)], [Utnyttj.], [$w_k$ (mm)],
  ..r.balkar.map(b => (b.namn, b.L, b.W, b.xc, [#b.x1 och #b.x2], b.F, b.Md, b.s_tra, b.u, b.w)).flatten(),
)
#text(size: 8.5pt)[x från balkens ände x = 0 enligt R-01. Stropp: kraften i varje stropp vid #l.vinkel°, karakteristisk. $M_d$, $sigma_"trä"$ och utnyttjandet med faktorn #l.faktor. $w_k$: största nedböjning av egentyngden, karakteristisk.]

= Resultat och anvisning

- Med lyftpunkterna #l.s mm isär, symmetriskt kring tyngdpunkten, är utnyttjandet högst #r.umax (#r.styr). Lyftets moment och tvärkraft i delarna med plåt är högst #r.andel_M och #r.andel_V av K-01:s dimensionerande, så plåtarna, limmet och skruvarna klarar lyftet med god marginal.
- *Tyngdpunkten ligger inte mitt på balken*, eftersom plåtarna sitter på delar av längden. Märk tyngdpunkten och lyftpunkterna på varje balk enligt tabellen. Punkterna får gärna ligga längre isär än #l.s mm men inte närmare.
- Stropparna ska ha minst #l.vinkel° mot balken, alltså vara minst #l.s mm långa var. Mjuka stroppar (rundslinga) runt balken med kantskydd mot plåtarnas kanter. Lyft först när limmet har härdat enligt K-01.
