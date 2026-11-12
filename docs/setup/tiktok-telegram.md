# Perintah TikTok dari Telegram (Mac)

Handur menerima perintah dari bot Telegram yang sama (bot laporan YouTube),
lewat fitur Channels Claude Code. Mac harus nyala dan Claude jalan di Terminal.

Sudah terpasang: Bun, Claude Code terminal (`claude`), plugin
`telegram@claude-plugins-official`.

## 1. Izin otomatis (sekali saja)
Supaya Handur tidak berhenti menunggu izin saat kamu tidak di depan Mac,
buat file `.claude/settings.json` di folder proyek dengan isi ini:

```json
{
  "permissions": {
    "allow": [
      "mcp__plugin_telegram_telegram__reply",
      "mcp__plugin_telegram_telegram__react",
      "mcp__plugin_telegram_telegram__download_attachment",
      "mcp__plugin_telegram_telegram__edit_message",
      "Read(~/.claude/channels/telegram/inbox/**)",
      "Write(tiktok/**)",
      "Edit(tiktok/**)",
      "WebSearch",
      "WebFetch",
      "Bash(npx hyperframes lint:*)",
      "Bash(npx hyperframes render:*)",
      "Bash(npx hyperframes snapshot:*)",
      "Bash(ffprobe:*)",
      "Bash(ffmpeg:*)",
      "Bash(mkdir -p tiktok/:*)",
      "Bash(cp ~/.claude/channels/telegram/inbox/:*)",
      "Bash(ls:*)",
      "Bash(git status:*)",
      "Bash(git add tiktok/:*)",
      "Bash(git commit:*)"
    ]
  }
}
```

Yang tidak ada di daftar ini (misalnya `git push`, menghapus file) tetap
minta izin dulu.

## 2. Simpan token bot
Buka Terminal di folder proyek, jalankan `claude`, lalu ketik:

```
/telegram:configure <token dari BotFather>
```

Token disimpan di `~/.claude/channels/telegram/.env`. Jangan kirim token ke chat.

## 3. Jalankan Handur dengan Telegram
Keluar dari Claude (`/exit`), lalu:

```bash
cd ~/Desktop/stickman-yt && claude --channels plugin:telegram@claude-plugins-official
```

Biarkan jendela Terminal ini terbuka.

## 4. Pairing (sekali saja)
1. Kirim pesan apa saja ke bot di Telegram. Bot membalas dengan kode.
2. Di Terminal Claude, ketik `/telegram:access pair <kode>`.
3. Lalu `/telegram:access policy allowlist` supaya hanya akunmu yang bisa memberi perintah.

## Cara pakai
Kirim ke bot, misalnya: `Handur, bikin video TikTok produk ini <link>`, plus
foto produk (kirim **sebagai File** supaya tidak dikompres) dan contoh video
(screenshot atau penjelasan gaya). Hasil datang dengan label `🎵 TIKTOK`.

## Catatan
- Jangan jalankan workflow GitHub **Telegram setup** saat Claude Channels
  sedang jalan: keduanya membaca pesan bot dan bisa bentrok.
- Mac jangan tidur selama dipakai (System Settings → Energy / Battery).
- Channels masih research preview; perintah bisa berubah.
