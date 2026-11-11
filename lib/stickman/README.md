# Pustaka Stickman (untuk Udun)

Karakter tetap channel **Economic for adults**. Dipakai di setiap adegan agar gaya konsisten.

## Gaya
- Latar `#FAF7F0`, garis hitam `#111` tebal 8, kepala bulat dengan mata titik.
- Aksen hijau `#1F9D55` untuk angka/kata penting (`class="sm-accent"`), merah `#D64545` untuk hal negatif (`sm-negative`).
- Judul: `class="sm-title"` (Montserrat 900).

## Cara memakai di adegan `scenes/sNN.html`
Root komposisi sudah memuat GSAP, `assets/stickman/stickman.js`, dan `stickman.css`. Adegan cukup memanggil `window.Stickman`.

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

## Thumbnail
`thumbnail.html` (1280×720) diisi otomatis oleh `sty thumbnail` dari `thumbnail.txt` (teks) dan pose.
