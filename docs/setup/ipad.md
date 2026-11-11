# Mengendalikan tim dari iPad

Semua kerja berjalan di cloud. iPad hanya untuk memberi perintah dan menyetujui.

## Sekali di awal
1. Pastikan repo ini sudah ada di GitHub (private) dan secrets sudah diisi
   (`docs/setup/telegram.md`, `docs/setup/youtube.md`).
2. Taruh 1–3 musik dari **YouTube Audio Library** (studio.youtube.com → Audio
   library, pilih yang tidak butuh atribusi) di folder `assets/music/` repo.
   Bisa lewat github.com → **Add file → Upload files**.
3. Buka aplikasi **Claude** di iPad → **Code** → hubungkan GitHub → pilih repo ini.
4. Buat **environment** cloud:
   - Setup script:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh && ~/.local/bin/uv sync
     ```
   - Akses jaringan: izinkan pencarian web dan registry paket (npm, PyPI), plus github.com.

## Sehari-hari
Mulai sesi baru di repo itu, lalu ketik misalnya:

- `Handur, carikan topik minggu ini`
- `Handur, buat video tentang kenapa inflasi bikin tabungan menyusut`
- `Handur, lanjutkan episode 001`
- `Handur, status`

Handur akan bertanya saat kamu perlu memilih topik, menyetujui naskah, dan
menyetujui video akhir. Preview video masuk ke Telegram saat render selesai.

## Kuota GitHub Actions
Repo private mendapat 2.000 menit gratis per bulan. Catat di sini menit yang
terpakai per video setelah uji coba pertama:

| Episode | Durasi video | Menit Actions |
|---|---|---|
| | | |
