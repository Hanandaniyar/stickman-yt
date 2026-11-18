# Proyek: tim produksi video stickman — channel Economic for adults

Channel: **Economic for adults** — https://www.youtube.com/@Economicforadults
Video penjelas animasi stickman berbahasa **Inggris Amerika** untuk penonton AS, fokus keuangan pribadi/investasi dan teknologi (CPM tinggi), sains/fisika sebagai sudut pandang.

## Cara kerja
- Pemilik memberi perintah lewat **"Handur, …"** → jalankan skill **handur** (`.claude/skills/handur/SKILL.md`). Handur mengatur subagent **udin**, **udan**, **udun**, **udon**, dan **asa** (QC video TikTok affiliate) di `.claude/agents/`. Alur TikTok (lokal, lewat Telegram): bagian *Mode TikTok* di skill handur.
- Bicara ke pemilik dalam **bahasa Indonesia**. Isi video, judul, deskripsi dalam bahasa Inggris.
- Narator **netral**: jangan pernah memasukkan cerita atau urusan pribadi pemilik.
- Suara, render, dan upload **tidak** dijalankan di sesi ini: semuanya berjalan di GitHub Actions (`.github/workflows/pipeline.yml`) saat `status.json` berisi `request`. Commit dan push ke `main`; jika sesi cloud hanya boleh push ke branch `claude/…`, push ke branch itu (pipeline juga berjalan di sana).
- Baris `notify: <pesan>` di pesan commit diteruskan ke Telegram pemilik.

## Perintah `uv run sty …`
| Perintah | Fungsi |
|---|---|
| `new <slug>` | buat episode baru |
| `status [ep]` | status semua/satu episode |
| `stage <ep> <stage>` | pindah tahap (topics, script, scenes, rendered, metadata, approved, done) |
| `review <ep> <stage> LOLOS\|REVISI --notes-file F` | catat putusan Handur |
| `approve <ep> topic\|script\|final` | catat persetujuan pemilik |
| `check <ep>` | validasi narration.json + adegan |
| `request <ep> render\|upload` | minta GitHub Actions bekerja (lalu commit + push) |
| `notify "<teks>"` | kirim Telegram (butuh secrets; biasanya lewat baris `notify:` di commit) |

## Aturan HyperFrames
Hanya fitur gratis dan lokal. **Dilarang**: `auth login`, `cloud render`, `lambda`, `cloudrun`, `media-use generate`, Voice Turbo/HeyGen, `/style-sampling`, `/reverse-any-video`, `feedback`, `publish`. Telemetri mati (`HYPERFRAMES_NO_TELEMETRY=1`).

Karakter dan gaya: `lib/stickman/README.md`. Kontrak komposisi: skill `/hyperframes`.

## Pengembangan
`uv run pytest -q` harus hijau sebelum commit perubahan kode.
