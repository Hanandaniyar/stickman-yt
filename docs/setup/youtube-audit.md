# Pengajuan audit YouTube API (draf jawaban)

Formulir: https://support.google.com/youtube/contact/yt_api_form
Pilih: **"I would like to request an audit of my API client"** (atau *Audit and Quota Extension*).
Isi dan kirim sendiri dengan akun **(email pemilik)**. Jawaban di bawah boleh disalin apa adanya.

## Data dasar
| Kolom | Isi |
|---|---|
| Nama / email kontak | (namamu) / (email pemilik) |
| Nama organisasi | Economic for adults (individual creator) |
| Website / homepage | https://hanandaniyar.github.io/handur-yt-legal/ |
| Privacy policy | https://hanandaniyar.github.io/handur-yt-legal/privacy.html |
| Terms of service | https://hanandaniyar.github.io/handur-yt-legal/terms.html |
| Google Cloud project ID | `handur-yt` |
| Project number | lihat Google Cloud Console → Dashboard proyek **handur-yt** → *Project number* |
| API client / OAuth client ID | Client ID yang dipakai sekarang (`…apps.googleusercontent.com`, dari file JSON) |
| Channel YouTube | https://www.youtube.com/@Economicforadults (channel ID `UCiL8FAJlsTQMUDF6j-ZZ5vA`) |
| API yang dipakai | YouTube Data API v3 |
| Kuota yang diminta | Tidak perlu tambahan (default 10.000 unit/hari cukup) |

## Deskripsi penggunaan (salin ke kolom "Describe your use case")

> Handur YT is a private, single-user tool used only by me, the owner of the YouTube channel
> "Economic for adults" (UCiL8FAJlsTQMUDF6j-ZZ5vA). I produce original educational stickman-animation
> videos about personal finance and economics. After I personally review and approve each finished
> video, my automated job (GitHub Actions) calls the YouTube Data API v3 to:
> - upload the video to my own channel (videos.insert),
> - set its title, description, tags and privacy status / scheduled publish time,
> - set the custom thumbnail (thumbnails.set),
> - read my own channel name to confirm the connection (channels.list, mine=true).
>
> The app is not offered to other users and never accesses any other account's data. OAuth credentials
> are stored only as encrypted secrets in my private GitHub repository. No user data is stored, sold or
> shared. I am requesting the audit so that videos uploaded through the API are no longer restricted to
> private mode, so I can schedule my own approved videos to go public.

## Kalau diminta bukti/screencast
- Screenshot layar persetujuan OAuth "Handur Yt" dengan dua izin YouTube.
- Screenshot atau rekaman layar YouTube Studio yang menampilkan video yang diunggah lewat API (misalnya episode 001, https://youtu.be/v0n1roVz3jU).
- Jangan tampilkan client secret, refresh token, atau isi file JSON di screenshot.

## Setelah disetujui
Beri tahu Handur. Ubah `config.json`:
```json
"upload_privacy": "public",
"publish_at_hour_et": 9
```
Dengan ini, setiap video dijadwalkan tayang pukul 09.00 waktu New York keesokan harinya.
