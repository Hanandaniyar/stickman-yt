# Rubrik pemeriksaan Handur

Putusan **LOLOS** hanya jika semua poin wajib terpenuhi. Tulis setiap cacat secara spesifik (di mana, apa, usulan perbaikan).

## Topik (`01-topics.md`)
- [ ] 5 topik (atau 1 topik yang diminta) lengkap: judul kerja, sudut pandang, alasan penonton AS peduli, skor, fakta, sumber.
- [ ] Setiap fakta punya URL sumber tepercaya; tidak ada angka tanpa sumber.
- [ ] Prioritas CPM: mayoritas keuangan pribadi/investasi atau teknologi.
- [ ] Aman iklan: tanpa politik partisan, tanpa saran investasi personal, tanpa sensasi menyesatkan.
- [ ] Bukan topik yang sudah dibuat di episode sebelumnya (cek `episodes/`).

## Naskah (`02-script.md`)
- [ ] 750–1.500 kata.
- [ ] Hook kuat di ±40 kata pertama (bukan salam pembuka).
- [ ] Penjelasan runtut dan mudah dipahami orang awam; ada analogi sehari-hari.
- [ ] Akurasi: setiap klaim fakta bertanda `[Sn]` dan cocok dengan sumbernya (buka sumber jika ragu).
- [ ] Narator netral: tidak ada cerita atau urusan pribadi pemilik.
- [ ] Bukan saran keuangan personal; risiko disebut bila relevan.
- [ ] Orisinal: tidak meniru struktur/kalimat khas channel lain; ada sudut pandang sendiri.
- [ ] Mudah diucapkan TTS: kalimat pendek, tanpa singkatan aneh.

## Adegan (`narration.json`, `scenes/*.html`) dan metadata
- [ ] `uv run sty check <ep>` → `valid`.
- [ ] Narasi per adegan = naskah yang disetujui (tanpa tanda `[Sn]`), tidak ada bagian hilang.
- [ ] Setiap adegan memakai stickman dan visualnya **menjelaskan** narasinya; variasi komposisi antar adegan (tidak template-is).
- [ ] Teks layar ≤ 6 kata, tidak bertabrakan dengan area subtitle bawah (±200 px dari bawah).
- [ ] `04-metadata.json`: judul ≤ 100 karakter dan jujur, deskripsi berisi sumber + disclaimer "not financial advice" untuk topik keuangan, 8–15 tag.
- [ ] `thumbnail.txt`: ≤ 5 kata + pose yang ada.

## Video (`stills/*.png`, `timing.json`)
- [ ] Tidak ada frame kosong, teks terpotong, elemen keluar layar, atau tumpang tindih yang tidak disengaja.
- [ ] Subtitle terbaca dan tidak menutupi visual penting.
- [ ] Durasi wajar (`timing.json.duration` ±5–10 menit); tidak ada adegan yang terlalu lama diam.
- [ ] Kebijakan YouTube: tidak terasa "mass-produced" (visual sesuai isi, tidak berulang), tidak menyesatkan.
