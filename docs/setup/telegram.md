# Setup Telegram (bisa dari iPad)

Tujuannya: setiap kemajuan Handur dan tim masuk ke Telegram-mu, termasuk preview video.

1. **Buat bot.** Di Telegram, buka **@BotFather**, kirim `/newbot`, lalu ikuti
   petunjuknya (nama bebas, misalnya "Handur Report"). BotFather memberi
   **token**. Token ini rahasia, jangan dikirim ke chat mana pun.
2. **Simpan token di GitHub.** Buka repo di github.com → **Settings** →
   **Secrets and variables** → **Actions** → **New repository secret**.
   - Name: `TELEGRAM_BOT_TOKEN`
   - Secret: tempel token dari BotFather
3. **Kirim pesan ke bot-mu**, misalnya "halo". Ini perlu supaya bot tahu ke
   mana harus mengirim laporan.
4. **Ambil chat ID.** Di repo → tab **Actions** → **Telegram setup** →
   **Run workflow**. Setelah selesai, buka job-nya, lalu langkah
   **Cari chat ID**. Angka yang tercetak adalah chat ID-mu.
5. **Simpan chat ID.** Buat secret baru:
   - Name: `TELEGRAM_CHAT_ID`
   - Secret: angka dari langkah 4
6. **Tes.** Buat commit apa saja yang pesannya berisi baris
   `notify: 🧪 tes`. Pesan "🧪 tes" akan masuk ke Telegram.

Kalau Telegram belum di-setup atau sedang gangguan, produksi video tetap
berjalan. Hanya laporannya yang tidak terkirim.
