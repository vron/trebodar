// Ritningsmall A3 liggande för Trebodar, i samma stil som beräkningsrapporterna (Carlito, tunna linjer, ljusa fyllningar).
//
// Bladet beskrivs av en JSON-fil som ett Python-skript skriver (ritningsmall/ritning.py): ritningshuvud, revisioner,
// högerkolumn med anvisningar, teckenförklaring och tabeller, samt vyer med element i namngivna lager, i pappersmått
// (mm, y nedåt från vyns övre vänstra hörn). Skalan sätts i Python, så att 1 mm på papperet = skala mm i verkligheten.
// Ram, ritningshuvud, linjetyper och färger finns bara här, och gäller alla ritningar.
//
//   typst compile --root <repo> --input blad=<sökväg till JSON från roten> [--input dolj=lager1,lager2] ritning.typ ut.pdf

#let B = json(sys.inputs.at("blad"))
#let DOLJ = sys.inputs.at("dolj", default: "").split(",").filter(x => x != "")

// ------------------------------------------------------------------ format och färger
#let BLAD = (b: 420, h: 297)                        // A3 liggande
#let RAM = (v: 20, o: 10, h: 10, n: 10)            // marginaler: vänster (inbindning), övre, höger, nedre
#let KOL = 84                                      // högerkolumnens bredd
#let INK = rgb("#1e1e1e")
#let GRA = rgb("#6b6b6b")
#let LJUS = rgb("#9a9a9a")
#let UK = rgb("#2c4a6e")
#let OK = rgb("#b5463a")
#let ZON = rgb("#c0504d")
#let FYLL = (
  betong: rgb("#ecebe7"), mark: rgb("#f4ecdc"), leca: rgb("#b9b3a9"), isol: rgb("#f7f3df"), stal: rgb("#5a5f66"),
  eps: rgb("#f3f6fa"), eps2: rgb("#dde6f0"), vit: white, svart: INK, zon: rgb("#f6e3df"), hal: white,
  jord: tiling(size: (2.2mm, 2.2mm))[#place(line(start: (0%, 100%), end: (100%, 0%), stroke: 0.15mm + rgb("#a89a7c")))],
  grus: tiling(size: (1.6mm, 1.6mm))[#place(dx: 0.5mm, dy: 0.5mm, circle(radius: 0.18mm, fill: rgb("#8f8a80")))],
  papp: rgb("#7d7466"),
)
#let STIL = (
  kontur: (thickness: 0.5mm, paint: INK, cap: "butt", join: "miter"),
  grov: (thickness: 0.7mm, paint: INK, cap: "butt"),
  normal: (thickness: 0.35mm, paint: INK, cap: "butt"),
  tunn: (thickness: 0.18mm, paint: INK, cap: "butt"),
  fin: (thickness: 0.13mm, paint: GRA, cap: "butt"),
  dold: (thickness: 0.25mm, paint: GRA, dash: (2mm, 1mm), cap: "butt"),
  axel: (thickness: 0.18mm, paint: GRA, dash: "dash-dotted", cap: "butt"),
  matt: (thickness: 0.13mm, paint: INK, cap: "butt"),
  hjalp: (thickness: 0.13mm, paint: LJUS, cap: "butt"),
  uk: (thickness: 0.6mm, paint: UK, cap: "round"),
  uk_tunn: (thickness: 0.25mm, paint: UK, cap: "round"),
  ok: (thickness: 0.6mm, paint: OK, cap: "round"),
  ok_tunn: (thickness: 0.25mm, paint: OK, cap: "round"),
  zon: (thickness: 0.18mm, paint: ZON, cap: "butt"),
  zon_kant: (thickness: 0.3mm, paint: ZON, dash: (1.5mm, 0.8mm), cap: "butt"),
  fordelning: (thickness: 0.18mm, paint: INK, cap: "butt"),
  snitt: (thickness: 0.7mm, paint: INK, cap: "butt"),
  stal: (thickness: 0.35mm, paint: FYLL.stal, cap: "butt"),
)
#let st(n) = if n == none or n == "" { none } else { stroke(STIL.at(n)) }
#let fy(n) = if n == none or n == "" { none } else if n.starts-with("#") { rgb(n) } else { FYLL.at(n) }
#let FARG = (ink: INK, gra: GRA, uk: UK, ok: OK, zon: ZON, vit: white)

#set document(title: B.huvud.nummer + " " + B.huvud.titel.join(", "), author: B.huvud.upprattad)
#set page(width: BLAD.b * 1mm, height: BLAD.h * 1mm, margin: 0mm)
#set text(font: "Carlito", size: 7.5pt, lang: "sv", fill: INK)
#set par(leading: 0.42em, spacing: 0.6em, justify: false)

// ------------------------------------------------------------------ element (pappersmått i mm)
#let P(p) = (p.at(0) * 1mm, p.at(1) * 1mm)

#let rita(e) = {
  let t = e.t
  if t == "l" {
    // polylinje
    let pts = e.p
    place(curve(stroke: st(e.s), curve.move(P(pts.at(0))), ..pts.slice(1).map(q => curve.line(P(q)))))
  } else if t == "pg" {
    let pts = e.p
    place(curve(stroke: st(e.at("s", default: none)), fill: fy(e.at("f", default: none)),
      curve.move(P(pts.at(0))), ..pts.slice(1).map(q => curve.line(P(q))), curve.close()))
  } else if t == "c" {
    let r = e.r
    place(dx: (e.c.at(0) - r) * 1mm, dy: (e.c.at(1) - r) * 1mm,
      circle(radius: r * 1mm, stroke: st(e.at("s", default: none)), fill: fy(e.at("f", default: none))))
  } else if t == "tx" {
    context {
      let sz = e.at("sz", default: 7.5)
      let body = text(size: sz * 1pt, weight: if e.at("b", default: false) { "bold" } else { "regular" },
        fill: FARG.at(e.at("col", default: "ink")), style: if e.at("i", default: false) { "italic" } else { "normal" },
        e.txt.split("\n").join(linebreak()))
      let bx = if e.at("bg", default: false) { box(fill: white, inset: (x: 0.5pt, y: 1pt), outset: 0pt, body) } else { box(body) }
      let m = measure(bx)
      let a = e.at("a", default: "lb")
      let ax = if a.at(0) == "l" { 0pt } else if a.at(0) == "c" { m.width / 2 } else { m.width }
      let ay = if a.at(1) == "t" { 0pt } else if a.at(1) == "m" { m.height / 2 } else { m.height }
      let rot = e.at("rot", default: 0)
      place(dx: e.p.at(0) * 1mm, dy: e.p.at(1) * 1mm,
        rotate(-rot * 1deg, origin: top + left, reflow: false, move(dx: -ax, dy: -ay, bx)))
    }
  }
}

#let vy(v) = place(dx: v.x * 1mm, dy: v.y * 1mm,
  box(width: v.w * 1mm, height: v.h * 1mm, clip: v.at("klipp", default: false), {
    for l in v.lager {
      if l.namn not in DOLJ { for e in l.element { rita(e) } }
    }
  }))

// ------------------------------------------------------------------ högerkolumnen
#let rubrik(t) = block(above: 3.2mm, below: 1.4mm, text(size: 8.5pt, weight: "bold", t))

#let symbol(s) = box(width: 9mm, height: 2.6mm, {
  if s.form == "linje" {
    place(dy: 1.3mm, line(length: 9mm, stroke: st(s.stil)))
  } else if s.form == "yta" {
    place(rect(width: 9mm, height: 2.6mm, fill: fy(s.fyll), stroke: st(s.at("stil", default: "tunn"))))
  } else if s.form == "ruta" {
    place(dx: 3.2mm, dy: 0.0mm, rect(width: 2.6mm, height: 2.6mm, fill: fy(s.fyll), stroke: none))
  } else if s.form == "bubbla" {
    place(dx: 3.2mm, dy: 0mm, circle(radius: 1.3mm, stroke: 0.18mm + INK, fill: white,
      align(center + horizon, text(size: 6pt, s.at("txt", default: "")))))
  } else if s.form == "fordelning" {
    place(dy: 1.3mm, line(length: 9mm, stroke: st("fordelning")))
    place(dx: -0.5mm, dy: 0.8mm, circle(radius: 0.5mm, fill: INK))
    place(dx: 8.5mm, dy: 0.8mm, circle(radius: 0.5mm, fill: INK))
  }
})

#let kolumn_block(k) = {
  if k.typ == "rubrik" { rubrik(k.text) }
  else if k.typ == "text" {
    set text(size: k.at("sz", default: 7.2) * 1pt)
    for r in k.rader { block(above: 0mm, below: 0.9mm, r) }
  } else if k.typ == "lista" {
    set text(size: k.at("sz", default: 7.2) * 1pt)
    for (i, r) in k.rader.enumerate() {
      block(above: 0mm, below: 0.9mm, grid(columns: (3.2mm, 1fr), [#(i + 1).], r))
    }
  } else if k.typ == "symboler" {
    set text(size: 7.2pt)
    for s in k.rader {
      block(above: 0mm, below: 1.0mm, grid(columns: (11mm, 1fr), align: horizon, symbol(s), s.text))
    }
  } else if k.typ == "tabell" {
    set text(size: k.at("sz", default: 6.8) * 1pt)
    table(columns: k.at("bredd", default: k.kolumner.map(_ => 0)).map(b => if b == 0 { auto } else { b * 1fr }), stroke: (x, y) => (top: if y == 0 { 0.4pt } else { 0.2pt + luma(180) }, bottom: 0.4pt),
      inset: (x: 2pt, y: 1.6pt), align: k.at("just", default: k.kolumner.map(_ => left)).map(a => if a == "r" { right } else if a == "c" { center } else { left }),
      table.header(..k.kolumner.map(c => text(weight: "bold", c))),
      ..k.rader.flatten())
  }
}

// ------------------------------------------------------------------ ritningshuvud och revisioner
#let falt(etikett, varde, sz: 8.5pt, b: false) = block(inset: (x: 1.6mm, top: 1.2mm, bottom: 1.2mm), width: 100%, {
  text(size: 5.6pt, fill: GRA, upper(etikett))
  v(0.6mm, weak: true)
  linebreak()
  text(size: sz, weight: if b { "bold" } else { "regular" }, varde)
})

#let huvud(H) = {
  let ln = 0.3pt + INK
  set text(size: 8pt)
  table(columns: (1fr, 1fr, 1fr), stroke: ln, inset: 0pt,
    table.cell(colspan: 3, falt("Projekt", H.projekt, b: true)),
    table.cell(colspan: 3, falt("Fastighet", H.fastighet)),
    table.cell(colspan: 3, falt("Innehåll", H.titel.join(linebreak()), sz: 10pt, b: true)),
    falt("Skala", H.skala), falt("Format", "A3"), falt("Datum", H.datum),
    falt("Upprättad", H.upprattad), falt("Granskad", H.at("granskad", default: "–")), falt("Underlag", H.underlag),
    table.cell(colspan: 2, falt("Status", H.status, b: true)), falt("Revision", H.rev, sz: 12pt, b: true),
    table.cell(colspan: 3, block(inset: (x: 1.6mm, y: 1.6mm), width: 100%, {
      text(size: 5.6pt, fill: GRA, upper("Ritningsnummer"))
      linebreak()
      v(0.6mm)
      align(right, text(size: 22pt, weight: "bold", H.nummer))
    })),
  )
}

#let revisioner(R) = {
  set text(size: 6.8pt)
  table(columns: (6mm, 1fr, 16mm, 9mm), stroke: (x, y) => (top: if y == 0 { 0.3pt } else { 0.2pt + luma(180) }, bottom: 0.3pt),
    inset: (x: 1.4pt, y: 1.4pt),
    table.header(text(weight: "bold")[Rev], text(weight: "bold")[Avser], text(weight: "bold")[Datum], text(weight: "bold")[Sign]),
    ..R.map(r => (r.rev, r.avser, r.datum, r.sign)).flatten())
}

// ------------------------------------------------------------------ bladet
#let ramx0 = RAM.v
#let ramy0 = RAM.o
#let ramb = BLAD.b - RAM.v - RAM.h
#let ramh = BLAD.h - RAM.o - RAM.n
#let kolx = BLAD.b - RAM.h - KOL

// ram och kolumnlinje
#place(dx: ramx0 * 1mm, dy: ramy0 * 1mm, rect(width: ramb * 1mm, height: ramh * 1mm, stroke: 0.7mm + INK))
#place(dx: kolx * 1mm, dy: ramy0 * 1mm, line(angle: 90deg, length: ramh * 1mm, stroke: 0.35mm + INK))
// centreringsmärken
#for (x, y, a) in ((BLAD.b / 2, 0, 90deg), (BLAD.b / 2, BLAD.h - RAM.n, 90deg), (5, BLAD.h / 2, 0deg), (BLAD.b - RAM.h, BLAD.h / 2, 0deg)) {
  place(dx: x * 1mm, dy: y * 1mm, line(angle: a, length: (if a == 90deg { RAM.n } else { if x < 10 { 15 } else { RAM.h } }) * 1mm, stroke: 0.35mm + INK))
}

// vyer
#for v in B.vyer { vy(v) }
// fristående block på ritytan (t.ex. stålförteckning): {x, y, w, block: [kolumnblock]}
#for f in B.at("block", default: ()) {
  place(dx: f.x * 1mm, dy: f.y * 1mm, block(width: f.w * 1mm, { for k in f.innehall { kolumn_block(k) } }))
}

// högerkolumnen: innehåll uppifrån, revisioner och ritningshuvud nedifrån
#place(dx: (kolx + 2.5) * 1mm, dy: (ramy0 + 1) * 1mm, block(width: (KOL - 5) * 1mm, {
  for k in B.kolumn { kolumn_block(k) }
}))
#place(dx: kolx * 1mm, dy: (ramy0 + ramh) * 1mm, place(bottom + left, block(width: KOL * 1mm, {
  block(inset: (x: 2.5mm, bottom: 1.5mm), revisioner(B.revisioner))
  huvud(B.huvud)
})))
// liten text i nedre kanten: fil och skala
#place(dx: ramx0 * 1mm, dy: (BLAD.h - RAM.n + 2.2) * 1mm,
  text(size: 5.5pt, fill: GRA, [#B.huvud.nummer · #B.huvud.skala vid utskrift på A3 · Mått i mm om inte annat anges]))
