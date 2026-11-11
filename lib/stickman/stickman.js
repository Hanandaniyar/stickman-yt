/* Stickman: karakter channel Economic for adults untuk HyperFrames.
 * Dimuat sekali di <head> komposisi root: <script src="assets/stickman/stickman.js"></script>
 * Semua gerakan adalah tween pada timeline adegan (deterministik, bisa di-seek).
 * Sudut dalam derajat: 0 = lurus ke bawah, 90 = ke kanan layar, -90 = ke kiri, 180 = ke atas.
 * Sudut lengan/kaki bawah relatif terhadap bagian atasnya. torso & head = kemiringan dari tegak.
 */
(function () {
  var POSES = /*POSES*/{
  "stand": {
    "head": 0,
    "torso": 0,
    "armL_upper": -12,
    "armL_lower": -5,
    "armR_upper": 12,
    "armR_lower": 5,
    "legL_upper": -10,
    "legL_lower": 0,
    "legR_upper": 10,
    "legR_lower": 0
  },
  "point": {
    "head": 0,
    "torso": 0,
    "armL_upper": -12,
    "armL_lower": -5,
    "armR_upper": 90,
    "armR_lower": 0,
    "legL_upper": -10,
    "legL_lower": 0,
    "legR_upper": 10,
    "legR_lower": 0
  },
  "think": {
    "head": 8,
    "torso": 0,
    "armL_upper": -40,
    "armL_lower": 80,
    "armR_upper": 30,
    "armR_lower": 130,
    "legL_upper": -10,
    "legL_lower": 0,
    "legR_upper": 10,
    "legR_lower": 0
  },
  "shrug": {
    "head": -8,
    "torso": 0,
    "armL_upper": -60,
    "armL_lower": -80,
    "armR_upper": 60,
    "armR_lower": 80,
    "legL_upper": -10,
    "legL_lower": 0,
    "legR_upper": 10,
    "legR_lower": 0
  },
  "celebrate": {
    "head": -6,
    "torso": 0,
    "armL_upper": -150,
    "armL_lower": -10,
    "armR_upper": 150,
    "armR_lower": 10,
    "legL_upper": -15,
    "legL_lower": 0,
    "legR_upper": 15,
    "legR_lower": 0
  },
  "sad": {
    "head": 25,
    "torso": 8,
    "armL_upper": -5,
    "armL_lower": 0,
    "armR_upper": 5,
    "armR_lower": 0,
    "legL_upper": -6,
    "legL_lower": 0,
    "legR_upper": 6,
    "legR_lower": 0
  },
  "walk": {
    "head": 0,
    "torso": 4,
    "armL_upper": 20,
    "armL_lower": 10,
    "armR_upper": -20,
    "armR_lower": 10,
    "legL_upper": -25,
    "legL_lower": 10,
    "legR_upper": 20,
    "legR_lower": -15
  },
  "run": {
    "head": 0,
    "torso": 12,
    "armL_upper": 45,
    "armL_lower": 70,
    "armR_upper": -40,
    "armR_lower": 60,
    "legL_upper": -40,
    "legL_lower": 50,
    "legR_upper": 35,
    "legR_lower": 10
  },
  "sit": {
    "head": 0,
    "torso": 0,
    "armL_upper": -10,
    "armL_lower": -5,
    "armR_upper": 10,
    "armR_lower": 5,
    "legL_upper": -90,
    "legL_lower": 90,
    "legR_upper": 90,
    "legR_lower": -90
  },
  "explain": {
    "head": 0,
    "torso": 0,
    "armL_upper": -45,
    "armL_lower": -60,
    "armR_upper": 45,
    "armR_lower": 60,
    "legL_upper": -10,
    "legL_lower": 0,
    "legR_upper": 10,
    "legR_lower": 0
  },
  "shocked": {
    "head": -5,
    "torso": -5,
    "armL_upper": -130,
    "armL_lower": -40,
    "armR_upper": 130,
    "armR_lower": 40,
    "legL_upper": -12,
    "legL_lower": 0,
    "legR_upper": 12,
    "legR_lower": 0
  },
  "hold-sign": {
    "head": 0,
    "torso": 0,
    "armL_upper": -160,
    "armL_lower": 30,
    "armR_upper": 160,
    "armR_lower": -30,
    "legL_upper": -10,
    "legL_lower": 0,
    "legR_upper": 10,
    "legR_lower": 0
  }
}/*END POSES*/;

  var INK = "#111111", ACCENT = "#1F9D55", NEG = "#D64545", PAPER = "#FAF7F0";
  var LEN = { torso: 95, neck: 12, head: 30, upper: 55, lower: 52, thigh: 66, shin: 64 };
  var HIP = { x: 100, y: 245 };
  var FACES = { celebrate: "smile", sad: "sad", shocked: "o", think: "flat" };
  var NS = "http://www.w3.org/2000/svg";

  function rad(d) { return (d * Math.PI) / 180; }
  function dir(a) { return { x: Math.sin(rad(a)), y: Math.cos(rad(a)) }; }
  function step(p, a, l) { var d = dir(a); return { x: p.x + d.x * l, y: p.y + d.y * l }; }
  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function copyPose(name) {
    if (!POSES[name]) throw new Error("Stickman: pose tidak dikenal: " + name);
    var o = {}; for (var k in POSES[name]) o[k] = POSES[name][k]; return o;
  }
  function mirror(p) {
    return {
      head: p.head, torso: p.torso,
      armL_upper: -p.armR_upper, armL_lower: -p.armR_lower, armR_upper: -p.armL_upper, armR_lower: -p.armL_lower,
      legL_upper: -p.legR_upper, legL_lower: -p.legR_lower, legR_upper: -p.legL_upper, legR_lower: -p.legL_lower,
    };
  }
  function facePath(kind) {
    switch (kind) {
      case "smile": return "M -11 6 Q 0 17 11 6";
      case "sad": return "M -10 13 Q 0 4 10 13";
      case "o": return "M -5 9 a 5 6 0 1 0 10 0 a 5 6 0 1 0 -10 0";
      case "flat": return "M -8 10 L 8 10";
      default: return "M -9 8 Q 0 13 9 8";
    }
  }

  function draw(fig) {
    var s = fig.state, P = fig.parts;
    var hip = { x: HIP.x, y: HIP.y };
    var neck = step(hip, 180 + s.torso, LEN.torso);
    var headC = step(neck, 180 + s.torso + s.head, LEN.neck + LEN.head);
    var shoulder = step(hip, 180 + s.torso, LEN.torso - 8);
    function limb(lineU, lineL, root, au, al, lu, ll) {
      var j = step(root, au, lu), e = step(j, au + al, ll);
      lineU.setAttribute("x1", root.x); lineU.setAttribute("y1", root.y);
      lineU.setAttribute("x2", j.x); lineU.setAttribute("y2", j.y);
      lineL.setAttribute("x1", j.x); lineL.setAttribute("y1", j.y);
      lineL.setAttribute("x2", e.x); lineL.setAttribute("y2", e.y);
    }
    P.torso.setAttribute("x1", hip.x); P.torso.setAttribute("y1", hip.y);
    P.torso.setAttribute("x2", neck.x); P.torso.setAttribute("y2", neck.y);
    limb(P.armLU, P.armLL, shoulder, s.armL_upper, s.armL_lower, LEN.upper, LEN.lower);
    limb(P.armRU, P.armRL, shoulder, s.armR_upper, s.armR_lower, LEN.upper, LEN.lower);
    limb(P.legLU, P.legLL, hip, s.legL_upper, s.legL_lower, LEN.thigh, LEN.shin);
    limb(P.legRU, P.legRL, hip, s.legR_upper, s.legR_lower, LEN.thigh, LEN.shin);
    P.head.setAttribute("transform", "translate(" + headC.x + " " + headC.y + ") rotate(" + -(s.torso + s.head) + ")");
  }

  /* Pasang stickman di dalam elemen el (biasanya div .clip). Mengembalikan objek figure. */
  function mount(el, opts) {
    opts = opts || {};
    var color = opts.color || INK, scale = opts.scale || 1, start = opts.pose || "stand";
    var svg = svgEl("svg", { viewBox: "0 0 200 400", width: 200 * scale, height: 400 * scale, overflow: "visible" });
    var body = svgEl("g", { stroke: color, "stroke-width": 8, "stroke-linecap": "round", fill: "none" });
    var parts = {};
    ["legLU", "legLL", "legRU", "legRL", "torso", "armLU", "armLL", "armRU", "armRL"].forEach(function (k) {
      parts[k] = svgEl("line", {}); body.appendChild(parts[k]);
    });
    var head = svgEl("g", {});
    head.appendChild(svgEl("circle", { r: LEN.head, fill: PAPER, stroke: color, "stroke-width": 8 }));
    head.appendChild(svgEl("circle", { cx: -10, cy: -5, r: 3.5, fill: color, stroke: "none" }));
    head.appendChild(svgEl("circle", { cx: 10, cy: -5, r: 3.5, fill: color, stroke: "none" }));
    var mouth = svgEl("path", { d: facePath(FACES[start]), stroke: color, "stroke-width": 4, fill: "none" });
    head.appendChild(mouth);
    parts.head = head; body.appendChild(head);
    svg.appendChild(body); el.appendChild(svg);
    var fig = {
      el: el, svg: svg, body: body, parts: parts, mouth: mouth, state: copyPose(start),
      startAngles: copyPose(start), startName: start, keys: [], clock: { t: 0 }, driven: 0,
    };
    draw(fig);
    return fig;
  }

  function lerpPose(a, b, k) {
    var o = {}; for (var j in a) o[j] = a[j] + (b[j] - a[j]) * k; return o;
  }

  /* Hitung pose pada waktu adegan t dari daftar keyframe (murni fungsi waktu, aman untuk seek). */
  function drawAt(fig, t) {
    var keys = fig.keys, cur = fig.startAngles, face = fig.startName;
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (t < k.at) break;
      if (t >= k.at + k.dur) { cur = k.to; face = k.name; continue; }
      var p = (t - k.at) / k.dur;
      cur = lerpPose(k.from, k.to, k.ease(p));
      face = p >= 0.5 ? k.name : face;
      break;
    }
    fig.state = cur;
    draw(fig);
    fig.mouth.setAttribute("d", facePath(FACES[face]));
  }

  /* Ganti pose mulai detik `at` selama `duration`. Mengembalikan detik selesai. */
  function pose(tl, fig, name, at, duration, opts) {
    opts = opts || {};
    duration = duration == null ? 0.27 : duration;
    var to = opts.mirror ? mirror(copyPose(name)) : copyPose(name);
    var from = fig.keys.length ? fig.keys[fig.keys.length - 1].to : fig.startAngles;
    fig.keys.push({ at: at, dur: duration, from: from, to: to, name: name, ease: gsap.parseEase(opts.ease || "back.out(1.4)") });
    fig.keys.sort(function (a, b) { return a.at - b.at; });
    var end = at + duration;
    if (end > fig.driven) {
      var driverStart = fig.driven;
      tl.fromTo(fig.clock, { t: driverStart }, {
        t: end, duration: end - driverStart, ease: "none", immediateRender: false,
        onUpdate: function () { drawAt(fig, fig.clock.t); },
      }, driverStart);
      fig.driven = end;
    }
    return end;
  }

  /* Naik-turun 2px dengan periode 2 detik, dari detik `from` sampai `to` (tanpa repeat tak hingga). */
  function breathe(tl, fig, from, to) {
    var n = Math.max(0, Math.floor((to - from) / 1));
    if (!n) return;
    tl.fromTo(fig.body, { y: 0 }, { y: -2, duration: 1, ease: "sine.inOut", yoyo: true, repeat: n - 1 }, from);
  }

  /* Berjalan dari x0 ke x1 (px, transform el) selama `duration`, kaki diayun bergantian 3x per detik. */
  function walk(tl, fig, x0, x1, at, duration, opts) {
    opts = opts || {};
    var gait = opts.run ? "run" : "walk";
    tl.fromTo(fig.el, { x: x0 }, { x: x1, duration: duration, ease: "none" }, at);
    var steps = Math.max(2, Math.round(duration * 3)), d = duration / steps;
    for (var i = 0; i < steps; i++) pose(tl, fig, gait, at + i * d, d, { mirror: i % 2 === 1, ease: "sine.inOut" });
    return pose(tl, fig, opts.end || "stand", at + duration, 0.2);
  }

  var PROPS = {
    "coin": '<circle cx="50" cy="50" r="40" fill="#F2C94C"/><circle cx="50" cy="50" r="28" fill="none"/><text x="50" y="62" font-size="36" text-anchor="middle" fill="#111" stroke="none" font-family="Montserrat" font-weight="700">$</text>',
    "money-stack": '<rect x="10" y="55" width="80" height="30" rx="4" fill="' + ACCENT + '"/><rect x="10" y="35" width="80" height="22" rx="4" fill="' + ACCENT + '"/><rect x="10" y="15" width="80" height="22" rx="4" fill="' + ACCENT + '"/><circle cx="50" cy="26" r="7" fill="none" stroke="#fff"/>',
    "house": '<path d="M12 50 L50 14 L88 50" fill="none"/><rect x="22" y="48" width="56" height="40" fill="#FFF"/><rect x="43" y="62" width="14" height="26" fill="#111"/>',
    "car": '<path d="M8 66 L14 46 L30 34 L68 34 L82 46 L92 66 Z" fill="' + NEG + '"/><circle cx="28" cy="70" r="10" fill="#111"/><circle cx="72" cy="70" r="10" fill="#111"/>',
    "credit-card": '<rect x="6" y="22" width="88" height="56" rx="8" fill="#2D6CDF"/><rect x="6" y="34" width="88" height="10" fill="#111"/><rect x="16" y="56" width="22" height="10" rx="2" fill="#F2C94C"/>',
    "bank": '<path d="M8 36 L50 10 L92 36 Z" fill="#FFF"/><rect x="18" y="40" width="10" height="38" fill="#FFF"/><rect x="45" y="40" width="10" height="38" fill="#FFF"/><rect x="72" y="40" width="10" height="38" fill="#FFF"/><rect x="8" y="80" width="84" height="10" fill="#FFF"/>',
    "chart-up": '<path d="M10 90 L10 10 M10 90 L92 90" fill="none"/><path d="M18 76 L40 56 L56 64 L84 24" fill="none" stroke="' + ACCENT + '"/><path d="M70 24 L84 24 L84 38" fill="none" stroke="' + ACCENT + '"/>',
    "chart-down": '<path d="M10 90 L10 10 M10 90 L92 90" fill="none"/><path d="M18 24 L40 44 L56 36 L84 76" fill="none" stroke="' + NEG + '"/><path d="M70 76 L84 76 L84 62" fill="none" stroke="' + NEG + '"/>',
    "lightbulb": '<path d="M50 10 C26 10 18 34 30 50 C36 58 38 64 38 72 L62 72 C62 64 64 58 70 50 C82 34 74 10 50 10 Z" fill="#F2C94C"/><path d="M40 82 L60 82 M43 90 L57 90" fill="none"/>',
    "atom": '<ellipse cx="50" cy="50" rx="42" ry="15" fill="none"/><ellipse cx="50" cy="50" rx="42" ry="15" fill="none" transform="rotate(60 50 50)"/><ellipse cx="50" cy="50" rx="42" ry="15" fill="none" transform="rotate(-60 50 50)"/><circle cx="50" cy="50" r="7" fill="' + ACCENT + '"/>',
    "chip": '<rect x="24" y="24" width="52" height="52" rx="6" fill="#333"/><rect x="38" y="38" width="24" height="24" fill="' + ACCENT + '" stroke="none"/><path d="M34 24 V12 M50 24 V12 M66 24 V12 M34 76 V88 M50 76 V88 M66 76 V88 M24 34 H12 M24 50 H12 M24 66 H12 M76 34 H88 M76 50 H88 M76 66 H88" fill="none"/>',
    "phone": '<rect x="28" y="8" width="44" height="84" rx="8" fill="#FFF"/><rect x="34" y="18" width="32" height="56" fill="#DDE6F5" stroke="none"/><circle cx="50" cy="83" r="4" fill="#111" stroke="none"/>',
    "clock": '<circle cx="50" cy="50" r="40" fill="#FFF"/><path d="M50 50 L50 24 M50 50 L68 58" fill="none"/>',
    "question-mark": '<text x="50" y="80" font-size="84" text-anchor="middle" fill="' + NEG + '" stroke="none" font-family="Montserrat" font-weight="900">?</text>',
    "arrow": '<path d="M8 50 L80 50 M60 28 L84 50 L60 72" fill="none"/>',
  };

  /* Gambar properti `type` di dalam el. opts.size dalam px (default 120). */
  function prop(el, type, opts) {
    opts = opts || {};
    if (!PROPS[type]) throw new Error("Stickman: properti tidak dikenal: " + type);
    var size = opts.size || 120;
    var svg = svgEl("svg", { viewBox: "0 0 100 100", width: size, height: size, overflow: "visible" });
    var g = svgEl("g", { stroke: INK, "stroke-width": 6, "stroke-linecap": "round", "stroke-linejoin": "round" });
    g.innerHTML = PROPS[type];
    svg.appendChild(g); el.appendChild(svg);
    return svg;
  }

  window.Stickman = {
    POSES: POSES, PROP_TYPES: Object.keys(PROPS), COLORS: { ink: INK, accent: ACCENT, negative: NEG, paper: PAPER },
    mount: mount, pose: pose, breathe: breathe, walk: walk, prop: prop,
  };
})();
