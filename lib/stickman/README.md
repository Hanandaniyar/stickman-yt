# Pustaka Stickman (untuk Udun)

Karakter tetap channel **Economic for adults**. Dipakai di setiap adegan agar gaya konsisten.

## Gaya
- Garis hitam `#111` tebal 8, kepala bulat dengan mata titik.
- Latar: ilustrasi flat-vector lembut dari `lib/backgrounds/` sesuai tempat cerita (lihat *Latar & kamera*). `#FAF7F0` hanya warna dasar halaman.
- Aksen hijau `#1F9D55` untuk angka/kata penting (`class="sm-accent"`), merah `#D64545` untuk hal negatif (`sm-negative`).
- Judul: `class="sm-title"` (Montserrat 900).

## Cara memakai di adegan `scenes/sNN.html`
Root komposisi sudah memuat GSAP, `assets/stickman/stickman.js`, `stickman.css`, dan `assets/backgrounds/backgrounds.js`. Contoh minimal di bawah; untuk adegan lengkap dengan latar dan kamera lihat *Latar & kamera*. Adegan cukup memanggil `window.Stickman`.

```html
<template>
  <style>
    #root { position: absolute; inset: 0; }
    #s03-guy { left: 700px; top: 330px; }
    #s03-coin { left: 1150px; top: 380px; }
  </style>
  <div id="root" data-composition-id="s03" data-width="1920" data-height="1080">
    <div id="s03-guy" class="clip sm-figure" data-start="0" data-duration="6"></div>
    <div id="s03-coin" class="clip sm-prop" data-start="1" data-duration="5"></div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    const guy = Stickman.mount(document.getElementById("s03-guy"), { pose: "stand", scale: 1.4 });
    Stickman.breathe(tl, guy, 0, 6);
    Stickman.pose(tl, guy, "point", 0.8);
    const coin = Stickman.prop(document.getElementById("s03-coin"), "coin", { size: 140 });
    tl.fromTo(coin, { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(2)" }, 1);
    window.__timelines["s03"] = tl;
  </script>
</template>
```

Aturan: id elemen diawali id adegan (`s03-…`), id komposisi dan kunci `__timelines` sama dengan id adegan, isi di dalam `<template>`, pakai `fromTo` (bukan `from`), tanpa `Math.random`, `Date.now`, atau `repeat: -1`.

## API
| Fungsi | Kegunaan |
|---|---|
| `Stickman.mount(el, {pose, scale, color})` | Gambar stickman di dalam `el`. `scale` 1 = tinggi ±400px. |
| `Stickman.pose(tl, fig, nama, detik, durasi=0.27, {mirror, ease})` | Ganti pose. Wajah ikut berubah (senang, sedih, kaget, datar). |
| `Stickman.breathe(tl, fig, dari, sampai)` | Gerak napas halus. Pakai di setiap adegan agar karakter "hidup". |
| `Stickman.walk(tl, fig, x0, x1, detik, durasi, {run, end})` | Berjalan/berlari horizontal (px), lalu berhenti dengan pose `end`. |
| `Stickman.prop(el, tipe, {size})` | Gambar properti. |

**Pose:** stand, point, think, shrug, celebrate, sad, walk, run, sit, explain, shocked, hold-sign.

**Properti:** coin, money-stack, house, car, credit-card, bank, chart-up, chart-down, lightbulb, atom, chip, phone, clock, question-mark, arrow.

Butuh pose atau properti baru? Tambahkan ke `poses.json` **dan** blok `/*POSES*/` di `stickman.js` (harus identik), lalu jalankan `uv run pytest tests/test_stickman_lib.py`. Untuk grafik, judul animasi, atau transisi, cari dulu di registry HyperFrames (`/hyperframes-registry`) sebelum membuat sendiri.

## Latar & kamera
`lib/backgrounds/` berisi 16 latar SVG 1920×1080 (digambar sendiri, tanpa teks/merek, kontras rendah):

| Tempat | Nama |
|---|---|
| Kota | `street`, `city-skyline`, `highway` |
| Belanja | `store-checkout`, `supermarket`, `car-dealership` |
| Rumah | `kitchen`, `living-room` |
| Kerja/uang | `office`, `bank-hall`, `factory`, `data-center`, `classroom` |
| Alam | `park` |
| Netral | `paper-grid` (grafik/angka), `studio` (konsep abstrak) |

Lembar kontak: `lib/backgrounds/contact-sheet.jpg`. Semua latar punya **garis lantai di y=840** dan 200 px bawah polos (subtitle). Lapisan `base` (diam), `far`, `mid`, `near` (paralaks). Latar baru dibuat lewat `tools/make_backgrounds.py`.

`sty build` hanya menyalin latar yang disebut adegan (`Stickman.background(el, "nama")` atau `<img src="assets/backgrounds/nama.svg">`) dan memuat `assets/backgrounds/backgrounds.js` secara sinkron di `<head>`. `sty check` menolak nama yang tidak ada.

```html
<template>
  <style>
    #root { position: absolute; inset: 0; overflow: hidden; background: #FAF7F0; }
    #s04-stage, #s04-cam { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }
    #s04-guy { left: 560px; }
    #s04-cart { position: absolute; left: 1080px; top: 600px; width: 230px; }
    #s04-title { position: absolute; left: 460px; top: 90px; width: 1000px; text-align: center; font-size: 84px; }
  </style>
  <div id="root" data-composition-id="s04" data-width="1920" data-height="1080">
    <div id="s04-stage">                 <!-- transisi masuk/keluar -->
      <div id="s04-cam">                 <!-- kamera: latar + pemain ikut zoom/geser -->
        <div id="s04-bg"></div>
        <div id="s04-guy" class="sm-figure"></div>
        <img id="s04-cart" src="assets/emoji/shopping-cart.svg" alt="">
      </div>
      <div id="s04-title" class="sm-title">Groceries <span class="sm-negative">+$40</span></div>  <!-- judul diam -->
    </div>
  </div>
  <script>
  (function () {
    const tl = gsap.timeline({ paused: true });
    const $ = (n) => document.getElementById("s04-" + n);
    const bg = Stickman.background($("bg"), "kitchen");
    Stickman.enter(tl, $("stage"), "slide-left", { at: 0 });          // + sfx whoosh di at 0
    Stickman.camera(tl, $("cam"), { preset: "push-in", duration: 5 });
    Stickman.parallax(tl, bg, { x: 80, duration: 5 });
    const guy = Stickman.mount($("guy"), { pose: "stand", scale: 1.1, ground: true });
    Stickman.breathe(tl, guy, 0, 5);
    tl.fromTo($("cart"), { scale: 0 }, { scale: 1, duration: 0.5, ease: "back.out(2)" }, 0.4);
    Stickman.exit(tl, $("stage"), "fade", { at: 4.65 });
    window.__timelines["s04"] = tl;
  })();
  </script>
</template>
```

| Fungsi | Kegunaan |
|---|---|
| `Stickman.background(el, nama, {dim})` | Pasang latar inline di `el` (butuh id, mis. `s04-bg`). Mengembalikan `{svg, base, far, mid, near}`. `dim: 0.3` meredupkan warna. |
| `Stickman.camera(tl, el, {preset, from, to, at, duration, ease})` | Zoom/geser halus (ken burns) pada pembungkus `#sNN-cam`. Preset: `push-in`, `pull-out`, `pan-left`, `pan-right`, `push-left`, `push-right`. Atau `from/to: {scale, focus}`: `focus` = x (px) yang dibawa ke tengah. Lantai tetap di y=840 berapa pun zoom-nya dan tepi latar tidak pernah terlihat (dibatasi otomatis). Boleh dipanggil berkali-kali (gerakan berurutan). |
| `Stickman.parallax(tl, bg, {x, y, at, duration})` | Geser lapisan `far`/`mid`/`near` dengan kecepatan 0,25/0,6/1 × `x` (px). Pakai bersama `pan-*`. |
| `Stickman.enter(tl, el, jenis, {at, duration})` | Transisi masuk: `fade`, `slide-left`, `slide-right`, `slide-up`, `zoom`, `wipe`, `iris`. |
| `Stickman.exit(tl, el, jenis, {at, duration})` | Kebalikannya, biasanya di 0,35 detik terakhir adegan. |
| `Stickman.mount(el, {…, ground: true})` | Tempatkan kaki stickman tepat di lantai (y=840; atau `ground: <y>`). |

Tips: pilih latar sesuai **tempat** narasi (harga mobil → `car-dealership`, tabungan → `bank-hall`, belanja → `supermarket`/`store-checkout`, AI/cloud → `data-center`, angka → `paper-grid`). Zoom wajar 1,05–1,2. Taruh pemain dan ilustrasi di dalam `#sNN-cam`, teks judul di luarnya.

## Thumbnail
`thumbnail.html` (1280×720) diisi otomatis oleh `sty thumbnail` dari `thumbnail.txt` (teks) dan pose.

## Shorts (video tegak 1080×1920)
Tulis `"format": "short"` di `narration.json`. `sty build` membuat komposisi 1080×1920 dan mengisi `window.STICKMAN_FRAME`.
- Adegan: root `data-width="1080" data-height="1920"`, wadah kamera 1080×1920.
- Latar diperbesar 2× (3840×2160) dan lantai berada di **y=1440** (`Stickman.GROUND`). `Stickman.background(el, name, {focusX})` memilih bagian latar yang dibawa ke tengah (x latar asli 0–1920, bawaan 960).
- Subtitle tampil di atas (top 300 px, maks 3 kata, 96 px). Jangan taruh teks penting di y 260–460; area bawah y > 1500 tertutup UI Shorts (judul, tombol kanan).
- Stickman Shorts sebaiknya `scale` 1.6–2.2 supaya terbaca di ponsel.
