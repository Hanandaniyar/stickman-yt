# Setup upload YouTube (bisa dari iPad)

Tujuannya: GitHub Actions boleh mengunggah video ke channel **Economic for adults**
atas namamu. Cukup dilakukan sekali. Kamu butuh: akun Google pemilik channel dan
akses ke repo GitHub. Semua langkah bisa dari Safari di iPad (pakai mode "Request
Desktop Website" kalau tampilan terpotong).

## 1. Buat proyek Google Cloud dan aktifkan YouTube API
1. Buka https://console.cloud.google.com dan login dengan akun pemilik channel.
2. Buat proyek baru, misalnya `stickman-yt`.
3. Menu **APIs & Services → Library**, cari **YouTube Data API v3**, lalu **Enable**.

## 2. Atur layar persetujuan OAuth (penting!)
1. Menu **Google Auth Platform** (atau **APIs & Services → OAuth consent screen**).
2. Tipe pengguna **External**. Isi nama aplikasi (bebas) dan email-mu.
3. Di bagian **Audience**, tekan **Publish app** sehingga statusnya **In production**.

> ⚠️ Kalau dibiarkan di mode *Testing*, izin upload **kedaluwarsa setiap 7 hari**
> dan upload akan gagal dengan pesan "refresh token kedaluwarsa".
> Status *unverified* tidak masalah untuk akun sendiri. Saat login nanti akan
> muncul peringatan "Google hasn't verified this app". Pilih **Advanced →
> Go to … (unsafe)**. Itu aplikasimu sendiri.

## 3. Buat kredensial OAuth
1. **APIs & Services → Credentials → Create credentials → OAuth client ID**.
2. Application type: **Web application**.
3. Authorized redirect URIs: tambahkan `https://developers.google.com/oauthplayground`.
4. Simpan. Catat **Client ID** dan **Client secret**.

## 4. Ambil refresh token lewat OAuth Playground
1. Buka https://developers.google.com/oauthplayground.
2. Ikon gear (⚙️) kanan atas → centang **Use your own OAuth credentials** → tempel
   Client ID dan Client secret.
3. Di kotak kiri, ketik dua scope ini (pisahkan dengan spasi), lalu **Authorize APIs**:
   `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube`
4. Login dengan akun Google pemilik channel. Jika diminta memilih channel/akun brand,
   pilih **Economic for adults**.
5. Kembali di Playground, tekan **Exchange authorization code for tokens**.
6. Salin nilai **Refresh token**. Jangan kirim ke chat mana pun.

## 5. Simpan di GitHub Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**, buat tiga:

| Name | Isi |
|---|---|
| `YT_CLIENT_ID` | Client ID dari langkah 3 |
| `YT_CLIENT_SECRET` | Client secret dari langkah 3 |
| `YT_REFRESH_TOKEN` | Refresh token dari langkah 4 |

## 6. Verifikasi telepon channel (untuk thumbnail kustom)
Buka https://www.youtube.com/verify saat login sebagai channel. Tanpa ini video
tetap terunggah, tapi thumbnail kustom ditolak (bot hanya memberi peringatan).

## 7. Audit YouTube API (supaya video bisa langsung publik)
Selama proyek Google belum lolos audit, video yang diunggah lewat API **terkunci
private**. Kamu tinggal membukanya di YouTube Studio dan mengubahnya ke Public
(satu klik).

Untuk menghapus batasan ini, ajukan audit gratis lewat formulir
**YouTube API Services – Audit and Quota Extension**
(https://support.google.com/youtube/contact/yt_api_form). Jelaskan bahwa ini alat
pribadi untuk mengunggah video edukasi buatan sendiri ke channel sendiri.
Prosesnya beberapa minggu.

Setelah disetujui, ubah `config.json`:

```json
"upload_privacy": "public",
"publish_at_hour_et": 9
```

Dengan pengaturan itu, video dijadwalkan tayang pukul 09.00 waktu New York
keesokan harinya.

## Kalau ada masalah
- **"refresh token kedaluwarsa"**: pastikan langkah 2 (In production), lalu ulangi langkah 4–5.
- **"kuota YouTube habis"**: batas harian ±6 upload. Coba lagi besok.
