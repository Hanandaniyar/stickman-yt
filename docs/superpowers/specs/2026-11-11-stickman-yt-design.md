# Desain: Tim Agent Channel YouTube Stickman

Tanggal: 2026-11-11 · Lokasi proyek: `~/Desktop/stickman-yt`

## 1. Maksud dan alasan

Pemilik ingin penghasilan dari YouTube.

Yang dibangun: tim agent pribadi di Claude Code yang memproduksi video YouTube
**animasi stickman** berbahasa Inggris untuk **penonton Amerika**. Topiknya
ilmu pengetahuan, terutama **keuangan, teknologi, sains, dan fisika**.
Animasinya **sederhana tapi khas** (gaya yang dikenali sebagai milik channel ini).

**Narator netral (keputusan pemilik).** Stickman menjelaskan sebagai karakter.
Video **tidak boleh** berisi cerita atau urusan pribadi pemilik.
Pembeda channel datang dari kualitas penjelasan dan gaya visual.

**Strategi topik: utamakan CPM tinggi (keputusan pemilik).** Udin meriset
sendiri topik yang menarik bagi penonton Amerika, dengan prioritas niche yang
bayaran iklannya tinggi. Hasil riset awal (2026-11-12, dari blog alat kreator
seperti vidIQ dan OutlierKit; angkanya kasar dan saling berbeda):
- **Keuangan pribadi dan investasi**: paling tinggi, RPM sekitar $10–35.
  Contoh: pajak, 401(k)/IRA, credit score, utang, inflasi, perumahan, cara
  kerja pasar.
- **Teknologi, AI, dan software**: RPM sekitar $10–25.
- **Sains dan edukasi**: RPM median sekitar $10. Lebih rendah, tapi
  jangkauannya luas.
- Kuartal 4 (Okt–Des) CPM 30–50% lebih tinggi dari kuartal 1.

Jadi porsi utama channel ada di keuangan dan teknologi. Sains dan fisika
dipakai sebagai daya tarik atau sudut pandang ("ilmu di balik uang/teknologi")
atau sebagai episode selingan. Udin memberi skor setiap usulan topik dengan
kriteria: perkiraan tingkat CPM, minat pencarian, kecocokan dengan format
stickman, dan keamanan iklan (advertiser-friendly).

TikTok/Shopee affiliate dikerjakan pemilik di tempat lain dan **di luar
lingkup** desain ini.

## 2. Tujuan, bukan-tujuan, anti-tujuan

**Tujuan**
- Pemilik cukup memberi perintah ke satu agent, **Handur**. Handur mengatur
  seluruh proses dari ide sampai video terunggah ke YouTube.
- Pemilik hanya dilibatkan di tiga titik keputusan: **memilih topik,
  menyetujui naskah, menyetujui video akhir sebelum upload**.
- Setiap hasil diperiksa Handur sebelum lanjut ke tahap berikutnya.
- Progres dikirim ke Telegram pemilik (satu arah, hanya notifikasi).
- Upload ke YouTube otomatis lewat YouTube Data API.
- Seluruh perangkat gratis dan berjalan di Mac pemilik.

**Bukan tujuan (untuk versi ini)**
- Konten TikTok/Shopee affiliate.
- Produksi tanpa persetujuan pemilik sama sekali (otomatis penuh).
- Membalas atau memberi perintah lewat Telegram (hanya kirim kabar).
- Membaca komentar atau analitik YouTube.

**Anti-tujuan (gagal walaupun secara teknis berjalan)**
- Channel ditolak monetisasinya atau diturunkan jangkauannya karena kebijakan
  YouTube "inauthentic / mass-produced content". Video harus terasa dibuat
  dengan sengaja: naskah tajam, sudut pandang jelas, visual tiap episode
  benar-benar mengikuti isi naskah, bukan template yang hanya diganti teks.
- Kesalahan fakta, terutama soal keuangan dan fisika.
- Konten keuangan yang terdengar seperti saran investasi pribadi.
- Gaya yang meniru channel stickman terkenal tertentu.

## 3. Batasan

- **Tidak berjalan di laptop pemilik** (keputusan pemilik 2026-11-12: Mac
  Intel lama). Kerja dilakukan di cloud: agent di Claude Code cloud yang
  dikendalikan dari iPad, sementara suara, render, dan upload berjalan di
  GitHub Actions. Pemilik sudah punya akun GitHub; proyek disimpan di repo
  **private**. Setup awal (Telegram, Google Cloud, GitHub Secrets) dibuat bisa
  dilakukan dari iPad.
  - Agent bekerja di sesi Claude Code cloud pada repo itu, lalu commit dan
    push ke `main`.
  - Satu workflow GitHub Actions menjalankan suara, render, upload, dan
    notifikasi. Workflow dipicu oleh perubahan `status.json`.
  - Video final disimpan sebagai aset GitHub Release per episode (bukan di
    git). Preview dikirim ke Telegram supaya bisa ditonton di iPad.
  - Rahasia disimpan di GitHub Secrets.
  - Kuota gratis Actions untuk repo private: 2.000 menit/bulan.
- Semua alat gratis. Narasi pakai TTS lokal (Kokoro), bukan layanan berbayar.
- Agent berbicara ke pemilik dalam **bahasa Indonesia**. Konten video
  (naskah, judul, deskripsi) dalam **bahasa Inggris Amerika**.
- Batasan Claude Code: **subagent tidak bisa memanggil subagent lain**. Karena
  itu Handur tidak boleh berupa subagent. Handur harus berjalan di sesi utama
  (lihat bagian 5).
- YouTube Data API: proyek Google Cloud yang belum lolos audit hanya bisa
  mengunggah sebagai **private**. Kuota harian ±10.000 unit, dan satu upload
  memakan ±1.600 unit (±6 upload/hari).
- Rahasia (token Telegram, chat ID, client ID/secret dan refresh token
  YouTube) disimpan di **GitHub Secrets**, tidak pernah ditulis di chat, log,
  atau git. `.env` lokal hanya untuk pengujian dan masuk `.gitignore`.

## 4. Pendekatan yang dipertimbangkan

**Tingkat otomatisasi**
- A. Bot sebagai asisten, pemilik jadi sutradara (memilih topik dan menyetujui
  naskah). Kualitas terjaga dan aman dari kebijakan YouTube.
- B. Hampir otomatis, pemilik hanya menyetujui video jadi. Lebih cepat, tapi
  video cenderung seragam.
- C. Otomatis penuh. Ditolak karena inilah pola yang ditekan YouTube.
- **Dipilih: A di awal, bergeser ke B** setelah gaya dan topik yang berhasil
  ditemukan (sekitar 10–20 video).

**Peran Handur**
- 1. Pemeriksa saja: pemilik memanggil tiap agent sendiri, Handur hanya menilai.
- 2. Bos yang mengatur tim: pemilik bicara ke Handur, Handur menyuruh agent
  lain, memeriksa, dan meminta revisi.
- **Dipilih pemilik: 2.**

**Mesin animasi**
- Remotion (React): karakter stickman dibuat sekali sebagai komponen SVG
  dengan pustaka pose. Skill resmi `remotion-dev/skills` ±6,8 ribu bintang.
- Manim (Python): unggul untuk rumus dan grafik, tapi kaku untuk karakter.
- **HyperFrames** (`heygen-com/hyperframes`, ±82,7 ribu bintang, Apache-2.0):
  video dari HTML/CSS/animasi yang bisa di-seek, dirancang khusus untuk agent
  AI. Isinya 9 skill dan ±450 komponen siap pakai (grafik, subtitle, transisi,
  judul). TTS Kokoro dan transkripsi lokal sudah ada di CLI-nya
  (`npx hyperframes tts`, `npx hyperframes transcribe`).
- **Dipilih pemilik (2026-11-12): HyperFrames.** Karakter stickman dibuat
  sendiri sebagai SVG/HTML yang dipakai ulang; grafik, subtitle, dan
  transisi diambil dari registry HyperFrames.
- **Hanya fitur gratis dan lokal.** Tidak memakai fitur Pro/HeyGen
  (`/style-sampling`, `/reverse-any-video`, Voice Turbo, kredit, `cloud render`).
  Suara memakai `npx hyperframes tts` (Kokoro lokal), timing memakai
  `npx hyperframes transcribe`, dan musik diambil dari file lokal
  (YouTube Audio Library). Telemetri/feedback HyperFrames dimatikan.
  Kebutuhan: Node 22+, FFmpeg, Chrome headless.

**Upload**
- YouTube Data API: resmi, stabil, tapi video private sampai audit lolos.
- Otomasi browser ke YouTube Studio: ditolak karena mudah rusak dan berisiko
  melanggar ketentuan YouTube.
- **Dipilih: YouTube Data API.** Selama belum lolos audit, video diunggah
  private lengkap dengan metadata, lalu pemilik mempublikasikannya dengan satu
  klik. Audit diajukan paralel. Setelah lolos, video langsung dijadwalkan
  publik tanpa mengubah kode (cukup ganti pengaturan).

**Suara narasi**
- **Dipilih: Kokoro TTS** (open-source, Apache 2.0, lokal). ElevenLabs bisa
  menggantikannya nanti; rancang pembuatan suara agar mesinnya bisa ditukar.

## 5. Tim dan alur kerja (keputusan pemilik)

| Nama | Peran | Bentuk di Claude Code |
|---|---|---|
| **Handur** | Bos: mengatur alur, memeriksa kualitas dan kelayakan setiap hasil, mencari cacat di naskah, storyboard, dan video | Perilaku sesi utama (skill proyek `/handur` + `CLAUDE.md`) |
| **Udin** | Periset topik | Subagent `.claude/agents/udin.md` |
| **Udan** | Penulis naskah | Subagent `.claude/agents/udan.md` |
| **Udun** | Sutradara visual: storyboard, suara, animasi, render | Subagent `.claude/agents/udun.md` |
| **Udon** | Penerbit: judul, deskripsi, tag, thumbnail, upload | Subagent `.claude/agents/udon.md` |

Pemakaian: pemilik membuka folder proyek di Claude Code lalu menulis, misalnya,
"Handur, buat video tentang kenapa inflasi bikin kita makin miskin", atau
"Handur, carikan topik minggu ini".

**Alur satu episode**
1. **Udin** meriset dan memberi ±5 usulan topik. Tiap topik berisi judul
   kerja, sudut pandang unik, alasan penonton Amerika peduli, fakta kunci, dan
   sumber. → Handur memeriksa → **pemilik memilih** (titik keputusan 1).
   Jika pemilik sudah memberi topik, Udin tetap meriset fakta dan sumbernya.
2. **Udan** menulis naskah narasi bahasa Inggris, 5–10 menit (±750–1.500 kata):
   hook kuat di 15 detik pertama, alur jelas, analogi sehari-hari, nada santai,
   cerdas, dan sedikit lucu, ditutup dengan kesimpulan. Setiap klaim fakta
   ditandai beserta sumbernya. → Handur memeriksa → **pemilik menyetujui
   naskah** (titik keputusan 2).
3. **Udun** memecah naskah jadi storyboard per adegan (potongan narasi, pose
   dan aksi stickman, properti, teks di layar, grafik/rumus, perkiraan durasi),
   lalu membuat narasi suara (Kokoro), mengambil timing per kata (Whisper),
   dan merender video di Remotion, lengkap dengan subtitle dan musik latar.
   Handur memeriksa storyboard sebelum render, dan memeriksa video setelah render.
4. **Udon** menyiapkan judul, deskripsi (termasuk sumber dan disclaimer
   "not financial advice" untuk topik keuangan), tag, dan thumbnail (render
   still dari Remotion dengan karakter yang sama). → Handur memeriksa →
   **pemilik menyetujui video akhir** (titik keputusan 3) → Udon mengunggah.

**Aturan pemeriksaan Handur**
- Setiap pemeriksaan menghasilkan **LOLOS** atau **REVISI** dengan daftar cacat
  yang spesifik. Hasilnya disimpan di folder episode.
- Yang diperiksa: akurasi fakta dan sumber, kekuatan hook, kejelasan
  penjelasan, keaslian (tidak template-is, tidak meniru channel lain),
  kepatuhan kebijakan YouTube, kesesuaian visual dengan narasi, sinkron
  suara–gambar–subtitle, cacat teknis (frame kosong, teks terpotong,
  audio terpotong, durasi).
- Maksimal **2 putaran revisi** per tahap. Jika masih belum lolos, Handur
  berhenti dan bertanya ke pemilik.

**Notifikasi Telegram**
Skrip `scripts/notify` mengirim pesan singkat ke Telegram pemilik setiap
tahap selesai, setiap putusan Handur, dan setiap kali pemilik perlu mengambil
keputusan. Format: emoji, nama agent, lalu satu kalimat. Contoh:
"👑 Handur: naskah ❌ revisi, hook terlalu lambat". Pesan dikirim oleh GitHub
Actions: agent menulis baris `notify: …` di pesan commit, lalu workflow
meneruskannya. Dengan cara ini sesi cloud tidak perlu akses langsung ke
Telegram. `TELEGRAM_CHAT_ID` didapat lewat workflow setup sekali jalan
setelah pemilik mengirim pesan ke bot. Jika token kosong atau Telegram gagal,
proses produksi **tidak boleh berhenti**; cukup catat peringatan.

## 6. Struktur folder

```
stickman-yt/
├── CLAUDE.md                 ← konteks proyek + aturan Handur
├── .claude/
│   ├── agents/udin.md, udan.md, udun.md, udon.md
│   └── skills/handur/SKILL.md
├── docs/
├── video/                    ← proyek Remotion (Stickman, pose, properti, template adegan)
├── scripts/                  ← notify, tts (Kokoro), timing (Whisper), render, upload
├── .env, .gitignore
└── episodes/
    └── 001-<slug>/
        ├── status.json       ← tahap saat ini, putusan Handur, riwayat revisi
        ├── 01-topics.md
        ├── 02-script.md
        ├── 03-storyboard.json
        ├── audio/            ← narasi + timing
        ├── render/           ← video final
        ├── 04-metadata.json, thumbnail.png
        └── reviews/          ← catatan pemeriksaan Handur
```

Episode harus bisa dilanjutkan dari tahap terakhir. Jika sesi terputus,
"Handur, lanjutkan episode 001" membaca `status.json` dan meneruskan dari sana.

## 7. Setup satu kali yang dilakukan pemilik sendiri

- Membuat bot Telegram lewat @BotFather, menyimpan token di GitHub Secrets,
  lalu mengirim satu pesan ke bot.
- Membuat proyek Google Cloud, mengaktifkan YouTube Data API v3, membuat
  kredensial OAuth, mengambil refresh token (bisa dari iPad), lalu menyimpan
  semuanya di GitHub Secrets. Builder harus menyediakan panduan langkah demi
  langkah dalam bahasa Indonesia.
- Mengajukan audit YouTube API (panduan disediakan builder).

## 7a. Keputusan desainer (bisa dikoreksi pemilik)

- **Animasi: pustaka dasar + komponen baru per episode.** `video/` berisi
  pustaka dasar (Stickman + pose, properti umum, template grafik/rumus/
  perbandingan/timeline). Storyboard JSON menyusun adegan dari pustaka itu.
  Jika satu adegan butuh visual yang belum ada, Udun **boleh menulis komponen
  React/SVG baru**. Komponen itu harus lolos `tsc` dan render uji satu frame,
  lalu disimpan ke pustaka agar bisa dipakai ulang. Alasannya: pustaka saja
  membuat visual berulang (anti-tujuan), sedangkan kode bebas per episode
  berisiko rusak. Handur memeriksa hasil render-nya, bukan kodenya.
- **Titik persetujuan bisa diatur.** Ketiga titik keputusan diatur di
  `config.json` (misalnya `"approve_topic": true`). Pergeseran ke mode B cukup
  dengan mengubah pengaturan, tanpa membangun ulang. Ini sejalan dengan
  pengaturan upload private/publik.
- **Channel dan identitas.** Pemilik **sudah punya channel YouTube**. Upload
  ditujukan ke channel itu, dan nama, logo, serta warna channel menjadi dasar
  gaya thumbnail dan karakter. Channel: **Economic for adults**
  (https://www.youtube.com/@Economicforadults). Per 2026-11-12: 67 subscriber,
  31 video, video terakhir 3 bulan lalu dengan view sangat rendah. Nama channel
  cocok dengan fokus keuangan/ekonomi. Identitas visual (warna, gaya
  thumbnail) dibangun baru bersama karakter stickman; video lama tidak
  mengikat gaya. Detail ini dicatat juga di `CLAUDE.md`.

## 8. Diserahkan ke builder

- Detail desain karakter stickman dan pustaka pose awal, dengan syarat
  sederhana, mudah dibaca di layar HP, dan konsisten di semua video.
- Pilihan suara Kokoro (pria/wanita, aksen Amerika), rasio 16:9, resolusi 1080p.
- Format persis `status.json`, storyboard JSON, dan metadata.
- Implementasi Whisper (openai-whisper, faster-whisper, atau whisper.cpp)
  dan cara instalasi dependensi.
- Sumber musik latar bebas royalti dan cara memilihnya per video.
- Cara Udin meriset tren (pencarian web; tanpa API berbayar).
