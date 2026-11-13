# Upload draft ke TikTok (Content Posting API)

Tujuan: setelah video jadi, Handur mengirimnya ke **kotak masuk TikTok** kamu
sebagai draft. Kamu buka TikTok, pasang keranjang kuning, tempel caption, posting.
Keranjang kuning tidak bisa dipasang lewat API, jadi langkah terakhir tetap manual.

Mulai dengan **sandbox**: mode uji coba TikTok tanpa review, untuk maksimal 10 akun
penguji (cukup akunmu sendiri). Belum pasti `video.upload` jalan penuh di sandbox;
kalau tidak, ajukan review aplikasi (langkah 7).

## Status
Sandbox aktif, login berhasil, upload draft sudah dites (13 Nov 2026).
Perintah: `uv run sty tiktok-login` (sekali, atau jika kedaluwarsa),
`uv run sty tiktok-upload <video>`, `uv run sty tiktok-status <publish_id>`.
Token tersimpan di `~/.config/handur/tiktok_token.json` (tidak di repo).

## 1. Akun developer
Buka https://developers.tiktok.com → **Log in** dengan akun TikTok kamu →
setujui Developer Terms. (Kamu sendiri yang membuat akun ini.)

## 2. Buat aplikasi
**Manage apps → Connect an app**. Isi:
- Nama: misalnya `Handur Uploader`
- Kategori: Utilities / Productivity
- Ikon dan deskripsi singkat: "Mengirim video buatan saya ke draft TikTok saya."

## 3. Tambah produk
Di halaman aplikasi → **Add products**:
- **Login Kit**
- **Content Posting API**: aktifkan **Upload** (draft). Direct Post tidak perlu.

## 4. Scope
Centang `user.info.basic` dan `video.upload`.

## 5. Sandbox
Tab **Sandbox → Create sandbox**. Di **Target users**, tambahkan akun TikTok
kamu (akun tempat jualan affiliate). Akun itu harus login dan menyetujui
Developer Terms.

## 6. Kirim ke Handur (jangan lewat chat)
Catat **Client key** dan **Client secret** dari sandbox. Simpan sendiri ke file
`.env` proyek:

```
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
```

Lalu bilang ke Claude "TikTok app siap". Langkah login (redirect URI, izin akun)
dan skrip upload dibuat setelah itu.

## 7. Jika sandbox tidak cukup
**Submit for review** di halaman aplikasi. TikTok biasanya meminta URL kebijakan
privasi/ketentuan dan video demo. Proses bisa beberapa hari.

Sumber: [Upload content](https://developers.tiktok.com/doc/content-posting-api-get-started-upload-content),
[Sandbox](https://developers.tiktok.com/doc/add-a-sandbox).
