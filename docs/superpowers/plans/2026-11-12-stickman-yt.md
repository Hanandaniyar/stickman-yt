# Tim Agent Channel Stickman — Rencana Implementasi (cloud + HyperFrames)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun repo GitHub private berisi pipeline produksi video stickman. Handur, Udin, Udan, Udun, dan Udon bekerja di sesi Claude Code cloud yang dikendalikan dari iPad. Suara, render, upload ke channel **Economic for adults**, dan notifikasi Telegram berjalan di GitHub Actions.

**Architecture:** Agent menulis file episode (topik, naskah, narasi per adegan, fragmen HTML per adegan), lalu meminta tahap berikutnya dengan mengubah `request` di `status.json` dan push ke `main`. Workflow `pipeline.yml` membaca permintaan itu dan menjalankan CLI Python `sty`. CLI ini membungkus `npx hyperframes` untuk TTS Kokoro, transkripsi, lint, dan render, lalu menyusun komposisi dari fragmen dan timing, mengunggah ke YouTube, dan mengirim Telegram. Hasil kecil (timing, still, status) di-commit balik ke repo; video disimpan di GitHub Release `ep-NNN`.

**Tech Stack:** Python 3.12 + uv, pytest; HyperFrames CLI + skill core (Node 22+, FFmpeg, Chrome headless); GitHub Actions `ubuntu-latest`; google-api-python-client + google-auth; Telegram Bot API lewat `urllib`.

**Spec:** `docs/superpowers/specs/2026-11-11-stickman-yt-design.md`

## Global Constraints

- Tidak ada kerja produksi di laptop pemilik. Semua yang dijalankan otomatis berjalan di GitHub Actions atau sesi Claude Code cloud. Laptop di sesi ini hanya dipakai untuk menulis kode dan menjalankan test unit.
- Hanya fitur HyperFrames yang gratis dan lokal. **Dilarang:** `auth login`, HeyGen, `media-use generate`, Voice Turbo, `cloud render`, `lambda`, `cloudrun`, `/style-sampling`, `/reverse-any-video`, dan `feedback`. Set env `HYPERFRAMES_TELEMETRY=0` (atau padanannya menurut `--help`) di setiap pemanggilan.
- Suara memakai `npx hyperframes tts` (Kokoro), transkripsi memakai `npx hyperframes transcribe`, dan musik diambil dari file di `assets/music/`.
- Rahasia hanya ada di GitHub Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`. Rahasia tidak pernah dicetak ke log; gunakan `::add-mask::` jika perlu.
- Agent berbicara ke pemilik dalam bahasa Indonesia. Isi video dalam bahasa Inggris Amerika. Narator netral, tanpa cerita atau urusan pribadi pemilik.
- Video 1920×1080, 30 fps. Naskah 750–1.500 kata. Upload default `private`. Maksimal 2 putaran revisi.
- Kegagalan Telegram tidak pernah menggagalkan job.
- Nama agent: `handur`, `udin`, `udan`, `udun`, `udon`. Channel: `@Economicforadults`.

## Review Focus

1. **Telegram belum di-setup atau API gagal**: langkah notify mencetak peringatan dan job tetap sukses. Diuji di Task 2.
2. **Angka dan simbol di narasi** (`$1,500`, `7%`, `401(k)`, `2026`): dinormalisasi sebelum TTS. Diuji di Task 5.
3. **Workflow memicu dirinya sendiri, atau dua permintaan bertabrakan**: commit balik dari Actions memakai `GITHUB_TOKEN` (tidak memicu workflow lagi), `concurrency` per episode, dan `request` dikosongkan setelah diproses. Diuji di Task 3 dan Task 7.
4. **Refresh token YouTube kedaluwarsa** (consent screen masih mode *Testing*, sehingga token kedaluwarsa dalam 7 hari) **atau kuota habis**: pesan bahasa Indonesia yang jelas lewat Telegram, dan stage tidak menjadi `done`. Diuji di Task 8; panduan setup mewajibkan mode *In production*.
5. **Video preview lebih dari 50 MB** (batas bot Telegram): preview 480p dengan bitrate rendah. Jika masih terlalu besar, kirim tautan Release saja. Diuji di Task 6.

---

## Struktur file

```
stickman-yt/
├── CLAUDE.md                        konteks proyek + "Handur, …" → skill handur   (Task 9)
├── config.json                                                                  (Task 1)
├── pyproject.toml, uv.lock
├── sty/  __init__.py cli.py config.py notify.py episode.py textnorm.py
│         voice.py build.py render.py upload.py ci.py
├── tests/
├── lib/stickman/                    karakter stickman (SVG + pose + animasi)     (Task 4)
│   ├── stickman.js  stickman.css  poses.json  thumbnail.html  demo/index.html
├── assets/music/                    musik bebas royalti (pemilik)
├── .claude/agents/{udin,udan,udun,udon}.md                                      (Task 9)
├── .claude/skills/handur/{SKILL.md,rubric.md}                                   (Task 9)
├── .claude/skills/hyperframes*/     skill core HyperFrames (diinstal)            (Task 4)
├── .github/workflows/ test.yml pipeline.yml telegram-setup.yml                  (Task 1, 7, 2)
├── docs/setup/ telegram.md youtube.md ipad.md                                   (Task 2, 8, 9)
└── episodes/NNN-slug/
    ├── status.json  01-topics.md  02-script.md  narration.json
    ├── scenes/sNN.html              fragmen HTML per adegan (Udun)
    ├── timing.json                  hasil CI
    ├── stills/*.png                 hasil CI, untuk diperiksa Handur
    ├── 04-metadata.json  thumbnail.txt
    ├── reviews/
    └── (tidak di-commit) audio/ build/ final.mp4 preview.mp4
```

**Kontrak data:**

- `config.json`: `{"approve_topic": true, "approve_script": true, "approve_final": true, "max_revision_rounds": 2, "upload_privacy": "private", "publish_at_hour_et": null, "voice": "am_michael", "voice_speed": 1.0, "scene_gap_s": 0.25, "music_volume": 0.08}`
- `status.json`: `{"episode": "001-slug", "stage": "topics", "request": null, "approvals": {"topic": false, "script": false, "final": false}, "reviews": [{"stage": str, "round": int, "verdict": "LOLOS"|"REVISI", "file": str}], "release_url": null, "youtube_id": null, "last_error": null, "updated_at": ISO8601}`
  - `stage` ∈ `topics, script, scenes, rendered, metadata, approved, done`.
  - `request` ∈ `null, "render", "upload"`.
- `narration.json`: `{"scenes": [{"id": "s01", "text": str}], "music": "assets/music/<file>"|null}`. Id berformat `s\d{2}`, unik, berurutan. Setiap id punya `scenes/<id>.html`.
- Fragmen `scenes/sNN.html`: satu elemen root `<section data-scene="sNN">`. Animasi relatif terhadap awal adegan (detik 0) mengikuti kontrak animasi seekable dari skill `/hyperframes`. Fragmen boleh memakai `lib/stickman` dan blok registry HyperFrames.
- `timing.json`: `{"duration": float, "scenes": [{"id", "start", "end"}], "words": [{"w", "start", "end"}]}`
- `04-metadata.json`: `{"title": str ≤100, "description": str ≤5000, "tags": [str], "category_id": "27"}`. `thumbnail.txt` berisi teks thumbnail ≤ 5 kata.

---

### Task 1: Kerangka repo, config, CI test

**Files:**
- Create: `pyproject.toml`, `sty/__init__.py`, `sty/config.py`, `sty/cli.py`, `config.json`, `tests/test_config.py`, `.github/workflows/test.yml`
- Modify: `.gitignore` (tambah `.venv/`, `node_modules/`, `episodes/*/audio/`, `episodes/*/build/`, `*.mp4`, `.hyperframes/`)

**Interfaces:**
- Produces: `PROJECT_ROOT: Path`; `load_config(root: Path = PROJECT_ROOT) -> dict` (default di atas digabung dengan file; key tak dikenal → `ValueError` yang menyebut key-nya); `main(argv=None) -> int` dengan pola `register(subparsers)` per modul.

- [ ] **Step 1:** Pasang uv lokal (`curl -LsSf https://astral.sh/uv/install.sh | sh`), lalu `git init -b main`, `uv init --package --name sty --python 3.12`, `uv add --dev pytest`.
- [ ] **Step 2: Test gagal** `tests/test_config.py`: `test_defaults_when_file_missing` (`max_revision_rounds == 2`, `upload_privacy == "private"`), `test_file_overrides`, `test_unknown_key_rejected` (pesan memuat nama key).
- [ ] **Step 3:** `uv run pytest -v` → FAIL. **Step 4:** Implementasi + `config.json`. **Step 5:** PASS, dan `uv run sty --help` exit 0.
- [ ] **Step 6:** `test.yml`: on push/PR → `astral-sh/setup-uv` → `uv run pytest -q`.
- [ ] **Step 7:** Commit `feat: repo skeleton, config, CI tests` (`.env` tidak ter-stage).

### Task 2: Notifikasi Telegram

**Files:**
- Create: `sty/notify.py`, `tests/test_notify.py`, `.github/workflows/telegram-setup.yml`, `docs/setup/telegram.md`
- Modify: `sty/cli.py`

**Interfaces:**
- Produces:
  - `notify(text: str) -> bool`: membaca env `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID`. Jika salah satu kosong, langsung `False` tanpa request. Tidak pernah melempar exception. Timeout 10 detik.
  - `notify_video(path: Path, caption: str) -> bool`: memanggil `sendVideo`. Jika file > 49 MB, mengembalikan `False` tanpa request.
  - `extract_notify_lines(commit_message: str) -> list[str]`: mengambil setiap baris yang diawali `notify:` lalu men-trim prefiksnya.
  - `find_chat_id(token: str) -> str | None`: `getUpdates`, mengambil `chat.id` dari pesan terakhir.
  - CLI: `sty notify "<teks>"`, `sty notify-commit` (membaca `git log -1 --format=%B`), `sty find-chat-id`. Ketiganya selalu exit 0, dan tidak ada output yang memuat token.
- `telegram-setup.yml` (`workflow_dispatch`): menjalankan `sty find-chat-id` lalu mencetak hanya chat ID. Chat ID bukan rahasia berbahaya; pemilik menyalinnya ke secret `TELEGRAM_CHAT_ID`.

- [ ] **Step 1: Test gagal** (mock `urllib.request.urlopen`): `test_missing_env_returns_false_without_request`, `test_network_error_returns_false`, `test_extract_notify_lines` (`"feat: x\n\nnotify: 👑 Handur: naskah lolos\nnotify: ✍️ Udan: selesai"` → 2 baris tanpa prefiks), `test_video_too_big_skipped` (file 50 MB → `False`, urlopen tidak dipanggil), `test_token_not_in_output(capsys)`.
- [ ] **Step 2:** FAIL → **Step 3:** implementasi → **Step 4:** PASS.
- [ ] **Step 5:** `docs/setup/telegram.md` (bahasa Indonesia, bisa dari iPad):
  1. @BotFather → `/newbot`.
  2. Di GitHub: repo → Settings → Secrets and variables → Actions → `TELEGRAM_BOT_TOKEN`.
  3. Kirim pesan ke bot.
  4. Actions → "Telegram setup" → Run → salin chat ID ke secret `TELEGRAM_CHAT_ID`.
- [ ] **Step 6:** Commit `feat: telegram notifications`.

### Task 3: Episode, status, dan permintaan tahap

**Files:**
- Create: `sty/episode.py`, `sty/ci.py`, `tests/test_episode.py`, `tests/test_ci.py`
- Modify: `sty/cli.py`

**Interfaces:**
- Produces (`episode.py`):
  - `create_episode(slug: str, root) -> Path`: nomor 3 digit berikutnya; slug dinormalisasi ke `a-z0-9-`; membuat `reviews/` dan `scenes/`; menulis `status.json` dengan stage `topics`.
  - `episode_dir(ref: str, root) -> Path`: menerima `"1"`, `"001"`, atau `"001-slug"`.
  - `load_status(ep)`, `save_status(ep, status)` (atomik, mengisi `updated_at`).
  - `set_stage(ep, stage)`: stage tak dikenal → `ValueError`.
  - `record_review(ep, stage, verdict, notes_md) -> int`, `revision_rounds(ep, stage) -> int`.
  - `approve(ep, which: Literal["topic","script","final"])`: `final` juga mengubah stage ke `approved`.
  - `request(ep, what: Literal["render","upload"])`:
    - `render` butuh `narration.json` valid; error validasi disebut per adegan, misalnya `"s03: scenes/s03.html tidak ada"`.
    - `upload` butuh `approvals.final` dan `release_url`; jika belum ada → `PermissionError` dengan pesan `butuh persetujuan akhir`.
  - `validate_narration(ep) -> list[str]`: memeriksa id unik dan berurutan, teks tidak kosong, fragmen ada, root `data-scene` cocok, dan musik ada jika diisi.
  - CLI: `sty new|status|review|stage|approve|request|check`.
- Produces (`ci.py`): `pending_requests(root) -> list[tuple[Path, str]]` (semua episode dengan `request` tidak null); `clear_request(ep, error: str | None)` (mengosongkan `request` dan mengisi `last_error`). CLI `sty ci-pending` mencetak JSON `[{"episode": "...", "request": "render"}]` untuk dipakai sebagai matrix workflow.

- [ ] **Step 1: Test gagal:** `test_numbering`, `test_slug_normalized` (`"Why Inflation?!"` → `001-why-inflation`), `test_review_rounds`, `test_invalid_stage`, `test_episode_ref_lookup`, `test_request_render_requires_valid_narration` (fragmen hilang → error yang menyebut `s03`), `test_request_upload_requires_final_approval`, `test_pending_requests_lists_only_requested`, `test_clear_request_records_error`.
- [ ] **Step 2:** FAIL → **Step 3:** implementasi → **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat: episodes, status, stage requests`.

### Task 4: Karakter stickman untuk HyperFrames dan skill core

**Files:**
- Create: `lib/stickman/stickman.js`, `lib/stickman/stickman.css`, `lib/stickman/poses.json`, `lib/stickman/thumbnail.html`, `lib/stickman/demo/index.html`, `lib/stickman/README.md`, `package.json` (pin `hyperframes` ke versi persis terbaru yang dirilis minimal 2 minggu lalu)
- Install: skill core HyperFrames ke `.claude/skills/` lewat `npx hyperframes skills update`. Hapus `/style-sampling` dan `/reverse-any-video` jika ikut terpasang, karena keduanya fitur Pro.

**Interfaces:**
- Baca dulu skill `/hyperframes` dan `/hyperframes-registry` untuk kontrak komposisi dan animasi seekable. Semua yang ditulis di sini harus mengikuti kontrak itu.
- Produces:
  - `poses.json`: pose `stand, point, think, shrug, celebrate, sad, walk, run, sit, explain, shocked, hold-sign`, masing-masing berisi sudut sendi (`head, torso, armL_upper, armL_lower, armR_upper, armR_lower, legL_upper, legL_lower, legR_upper, legR_lower`).
  - `stickman.js` mengekspor `createStickman(el, {pose, scale, color})` dan `animatePose(tl, figure, toPose, at, duration=0.27)` untuk timeline seekable.
  - Properti SVG: `coin, money-stack, house, car, credit-card, bank, chart-up, chart-down, lightbulb, atom, chip, phone, clock, question-mark, arrow` lewat `createProp(el, type, {x, y, scale})`.
  - Gaya: latar `#FAF7F0`, garis hitam 8px, kepala bulat, aksen hijau `#1F9D55`, merah `#D64545`, font judul Montserrat Bold. Stickman "bernafas" (bob 2px, 2 detik).
  - `thumbnail.html`: 1280×720, dibaca dengan query `?text=…&pose=…`.
- `lib/stickman/README.md` adalah panduan singkat untuk Udun: cara mengimpor, daftar pose dan properti, dan contoh fragmen adegan.

- [ ] **Step 1: Test gagal** `tests/test_stickman_lib.py`: `poses.json` memuat 12 pose dan setiap pose punya 10 sendi bernilai angka; `stickman.js` memuat semua nama properti di atas.
- [ ] **Step 2:** FAIL → **Step 3:** implementasi.
- [ ] **Step 4:** `npx hyperframes lint lib/stickman/demo` (atau perintah cek setara menurut `/hyperframes-cli`) → tanpa error. Render demo 5 detik dengan `--quality draft`, lalu lihat 3 frame. Stickman harus berganti pose dengan mulus dan teks terbaca.
- [ ] **Step 5:** PASS → Commit `feat: stickman character library and hyperframes skills`.

### Task 5: Suara narasi dan timing

**Files:**
- Create: `sty/textnorm.py`, `sty/voice.py`, `tests/test_textnorm.py`, `tests/test_voice.py`
- Modify: `sty/cli.py`, `pyproject.toml` (`num2words`, `soundfile`, `numpy`)

**Interfaces:**
- Consumes: `narration.json`, `load_config()` (`voice`, `voice_speed`, `scene_gap_s`).
- Produces:
  - `normalize_for_tts(text) -> str`.
  - `synthesize_episode(ep, *, force=False, run=subprocess.run) -> dict`:
    1. Untuk setiap adegan: `npx hyperframes tts` dengan teks yang sudah dinormalisasi, voice, dan speed → `audio/<id>.wav`. Opsi persisnya lihat `--help`. Adegan yang wav-nya sudah ada dilewati, kecuali `force`.
    2. Gabungkan semua wav dengan jeda `scene_gap_s` → `audio/narration.wav`.
    3. Hitung `start`/`end` dari jumlah sampel.
    4. Jalankan `npx hyperframes transcribe` pada setiap wav, lalu geser waktu katanya.
    5. Tulis `timing.json`.
  - CLI `sty voice <ep> [--force]`.

- [ ] **Step 1: Test gagal `test_textnorm.py`:**
  - `"$1,500"` → `"one thousand five hundred dollars"`
  - `"7%"` → `"seven percent"`
  - `"401(k)"` → `"four oh one k"`
  - `"in 2026"` → `"in twenty twenty-six"`
  - `"$3.5 trillion"` → `"three point five trillion dollars"`
  - `"AI & crypto"` → `"AI and crypto"`
- [ ] **Step 2: Test gagal `test_voice.py`** dengan `run` palsu yang menulis wav diam 1,0 detik dan JSON transkrip palsu:
  - `test_scene_timing`: 3 adegan → `scenes[1].start == 1.25` dan `duration == 3.5`.
  - `test_resume_skips_existing`: TTS dipanggil 2 kali.
  - `test_force_regenerates`: 3 kali.
  - `test_words_offset`.
  - `test_normalized_text_passed_to_tts`.
  - `test_tts_failure_names_scene`: `RuntimeError` yang memuat `s02`.
- [ ] **Step 3:** FAIL → **Step 4:** implementasi → **Step 5:** PASS.
- [ ] **Step 6:** Commit `feat: narration via hyperframes tts and word timing`.

### Task 6: Menyusun komposisi, render, still, preview, thumbnail

**Files:**
- Create: `sty/build.py`, `sty/render.py`, `tests/test_build.py`, `tests/test_render.py`
- Modify: `sty/cli.py`

**Interfaces:**
- Consumes: `timing.json`, `scenes/*.html`, `narration.json.music`, `lib/stickman`, `thumbnail.txt`, `load_config()["music_volume"]`.
- Produces:
  - `build_composition(ep) -> Path`: menulis `build/index.html`. Isinya kerangka komposisi HyperFrames 1920×1080/30fps berdurasi `timing.duration + 1.0`. Setiap fragmen ditempatkan pada `start`-nya dengan durasi `end - start`. Komposisi juga memuat track audio `narration.wav`, musik pada `music_volume` jika ada, subtitle 2 baris dari `words` (blok captions registry HyperFrames, kata aktif berwarna `#1F9D55`), dan `lib/stickman` yang disalin ke `build/`. Atribut-atribut persisnya mengikuti kontrak `/hyperframes`.
  - `render_episode(ep, run=subprocess.run) -> Path`:
    1. `npx hyperframes lint` (atau setaranya) pada `build/`.
    2. `render --quality delivery -o final.mp4`.
    3. Pastikan durasi `ffprobe` = durasi komposisi ±0,5 detik.
  - `make_stills(ep, run) -> list[Path]`: 5 frame (1 detik, 25%, 50%, 75%, dan 1 detik sebelum akhir) → `stills/`.
  - `make_preview(ep, run) -> Path | None`: ffmpeg 854×480, `-crf 32`, audio 64k. Jika hasilnya > 49 MB → `None`.
  - `make_thumbnail(ep, run) -> Path`: merender `thumbnail.html` dengan teks dari `thumbnail.txt` → `thumbnail.png`.
  - CLI `sty build|render|stills|preview|thumbnail <ep>`.

- [ ] **Step 1: Test gagal `test_build.py`:**
  - `test_scenes_placed_at_timing_start`: fragmen `s02` muncul dengan start `1.25`.
  - `test_music_optional`.
  - `test_missing_timing_message`: pesannya memuat `jalankan sty voice dulu`.
  - `test_fragment_scene_id_mismatch_rejected`.
- [ ] **Step 2: Test gagal `test_render.py`** (`run` palsu):
  - `test_lint_runs_before_render`.
  - `test_duration_mismatch_raises`.
  - `test_render_failure_includes_stderr_tail`: memuat 20 baris terakhir stderr.
  - `test_preview_too_big_returns_none`.
- [ ] **Step 3:** FAIL → **Step 4:** implementasi → **Step 5:** PASS.
- [ ] **Step 6:** Commit `feat: compose, render, stills, preview, thumbnail`.

### Task 7: Workflow pipeline GitHub Actions

**Files:**
- Create: `.github/workflows/pipeline.yml`, `tests/test_workflow.py`

**Interfaces:**
- Consumes: `sty ci-pending`, `sty voice|build|render|stills|preview|thumbnail|upload|notify-commit|notify`, `clear_request`.
- Produces: `pipeline.yml` berisi tiga job.
  - **Pemicu:** `push` ke `main` (paths `episodes/**`, plus semua commit untuk notify) dan `workflow_dispatch`. `permissions: contents: write`.
  - **Job `notify`:** `sty notify-commit` pada setiap push.
  - **Job `plan`:** `sty ci-pending` → output matrix.
  - **Job `work`** (matrix per episode, `concurrency: ep-${{ matrix.episode }}`, `timeout-minutes: 120`):
    1. setup-node 22, setup-uv, `apt-get install ffmpeg`, `npx hyperframes browser ensure`. Cache npm dan model Kokoro di `~/.cache`.
    2. Jika `render`: `sty voice` → `build` → `render` → `stills` → `thumbnail` → `preview`.
    3. Buat atau perbarui Release `ep-NNN` (`gh release create/upload --clobber`) berisi `final.mp4` dan `thumbnail.png`, lalu isi `release_url`.
    4. Set stage `rendered`, commit `timing.json`, `stills/`, `thumbnail.png`, dan `status.json`, lalu push (`GITHUB_TOKEN`, sehingga tidak memicu ulang).
    5. `notify_video(preview)`, atau jika gagal kirim teks + tautan Release.
    6. Jika `upload`: unduh `final.mp4` dari Release → `sty upload` → commit status.
    7. Jika ada error: `clear_request(ep, error)`, commit, lalu `sty notify "❌ <ep>: <ringkasan error>"`. Job tetap berstatus gagal agar terlihat di tab Actions.
  - Env setiap step: `HYPERFRAMES_TELEMETRY=0`. Secrets dipetakan ke env hanya di step yang membutuhkannya.

- [ ] **Step 1: Test gagal `tests/test_workflow.py`** (parse YAML dengan `pyyaml`):
  - `test_work_has_concurrency_per_episode`.
  - `test_permissions_contents_write`.
  - `test_secrets_only_in_needed_steps`: `YT_REFRESH_TOKEN` hanya muncul di step upload.
  - `test_no_forbidden_hyperframes_commands`: tidak ada `cloud render`, `auth login`, `lambda`, `cloudrun`, `generate`, atau `feedback` di semua workflow.
- [ ] **Step 2:** FAIL → **Step 3:** tulis workflow → **Step 4:** PASS. Jalankan `actionlint` lewat `npx`/docker jika tersedia; jika tidak, cukup parse YAML.
- [ ] **Step 5:** Commit `feat: github actions production pipeline`.

### Task 8: Upload YouTube dan panduan setup Google

**Files:**
- Create: `sty/upload.py`, `tests/test_upload.py`, `docs/setup/youtube.md`
- Modify: `sty/cli.py`, `pyproject.toml` (`google-api-python-client`, `google-auth`)

**Interfaces:**
- Consumes: `04-metadata.json`, `final.mp4`, `thumbnail.png`, `load_config()` (`upload_privacy`, `publish_at_hour_et`), `notify`, fungsi status.
- Produces:
  - `credentials_from_env() -> Credentials`: dari `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, dengan token URI Google dan scope `youtube.upload` + `youtube`.
  - `upload_episode(ep, video: Path, service=None) -> str`:
    1. Tolak jika `approvals.final` false.
    2. Validasi judul ≤100 karakter dan deskripsi ≤5.000 sebelum ada panggilan API.
    3. `videos.insert` resumable dengan `categoryId` 27, `selfDeclaredMadeForKids` false, dan privacy dari config. Jika `public` + `publish_at_hour_et`, kirim sebagai `private` + `publishAt` hari berikutnya pada jam itu, zona America/New_York.
    4. `thumbnails.set`; 403 hanya menjadi peringatan.
    5. Simpan `youtube_id`, set stage `done`, lalu notify `📤 Udon: "<judul>" terunggah (<privacy>) https://youtu.be/<id>`.
  - CLI `sty upload <ep> --video PATH`.

- [ ] **Step 1: Test gagal** (service palsu):
  - `test_requires_final_approval`.
  - `test_insert_body`: title, tags, `"27"`, `"private"`.
  - `test_scheduled_publish`: `publishAt` jam 09:00 ET.
  - `test_thumbnail_403_is_warning`.
  - `test_quota_error`: pesan `kuota YouTube habis, coba lagi besok`; stage bukan `done`.
  - `test_invalid_grant`: pesan memuat `refresh token kedaluwarsa` dan `docs/setup/youtube.md`.
  - `test_title_too_long`.
- [ ] **Step 2:** FAIL → **Step 3:** implementasi → **Step 4:** PASS.
- [ ] **Step 5:** `docs/setup/youtube.md` (bahasa Indonesia, bisa dari iPad):
  1. Google Cloud Console → proyek baru → aktifkan YouTube Data API v3.
  2. OAuth consent screen External, lalu **Publish app → In production**. Jika tidak, refresh token mati dalam 7 hari. Layar "unverified app" boleh dilewati untuk akun sendiri.
  3. Buat kredensial **Web application** dengan redirect `https://developers.google.com/oauthplayground`.
  4. Buka OAuth Playground → ikon gear → "Use your own OAuth credentials" → scope `youtube.upload` dan `youtube` → login dengan akun pemilik channel Economic for adults → tukar kode → salin refresh token.
  5. Simpan ke GitHub Secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
  6. Verifikasi telepon channel (untuk thumbnail kustom).
  7. Ajukan audit YouTube API Services. Setelah lolos, ubah `upload_privacy`/`publish_at_hour_et` di `config.json`.
- [ ] **Step 6:** Commit `feat: youtube upload and google setup guide`.

### Task 9: Handur, empat agent, CLAUDE.md, panduan iPad

**Files:**
- Create: `CLAUDE.md`, `.claude/agents/{udin,udan,udun,udon}.md`, `.claude/skills/handur/SKILL.md`, `.claude/skills/handur/rubric.md`, `docs/setup/ipad.md`, `tests/test_agents.py`

**Interfaces:**
- Consumes: semua CLI `sty`, `lib/stickman/README.md`, skill `/hyperframes` dan `/hyperframes-registry`.
- Produces:
  - **Udin** (`WebSearch, WebFetch, Read, Write, Bash`): `01-topics.md` berisi 5 topik. Setiap topik punya judul kerja, sudut pandang, alasan penonton AS peduli, skor 1–5 (CPM, minat pencarian, cocok stickman, aman iklan), fakta kunci, dan URL sumber. Prioritas: keuangan pribadi/investasi > teknologi/AI > sains/fisika sebagai sudut pandang.
  - **Udan** (`Read, Write, WebSearch, WebFetch`): `02-script.md` sepanjang 750–1.500 kata. Hook ±40 kata pertama. Klaim fakta ditandai `[S1]` dengan daftar sumber di akhir. Narator netral, santai, cerdas, sedikit lucu, tanpa saran investasi personal.
  - **Udun** (`Read, Write, Edit, Bash`): mengubah naskah yang disetujui menjadi `narration.json` (satu adegan = 1–3 kalimat) dan `scenes/sNN.html`. Membaca `/hyperframes` dan `/hyperframes-registry` sebelum menulis fragmen. Wajib memakai `lib/stickman`. Boleh menambah pose/properti ke `lib/stickman` asalkan test dan lint lulus. Menjalankan `sty check <ep>` lalu `sty request <ep> render`. Tidak pernah menjalankan perintah HyperFrames yang dilarang.
  - **Udon** (`Read, Write, Bash`): `04-metadata.json` dan `thumbnail.txt`. Untuk topik keuangan, deskripsi wajib memuat baris `This video is for educational purposes only and is not financial advice.` dan daftar sumber. `sty request <ep> upload` hanya dijalankan setelah persetujuan akhir pemilik dan atas perintah Handur.
  - **Semua agent:** menutup tugas dengan commit + push ke `main` yang pesannya memuat baris `notify: <emoji> <Nama>: <ringkasan>`.
  - **Skill Handur:**
    - Membaca `config.json` dan `status.json`, lalu menjalankan tahap secara berurutan lewat subagent.
    - Memeriksa setiap hasil dengan `rubric.md`, lalu mencatat lewat `sty review`.
    - Jika `REVISI`, Handur mengembalikannya ke agent yang sama. Jika ronde sudah mencapai `max_revision_rounds`, Handur bertanya ke pemilik.
    - Meminta persetujuan pemilik sesuai config, lalu mencatatnya lewat `sty approve`.
    - Setelah `sty request … render`, Handur memberi tahu pemilik bahwa render berjalan di GitHub dan hasilnya akan masuk ke Telegram. Saat dilanjutkan, Handur menjalankan `git pull`, memeriksa `stills/*.png` dan `timing.json`, lalu meminta Udon menyiapkan metadata.
    - Mendukung perintah "lanjutkan episode NNN", "carikan topik", dan "status".
    - Bahasa ke pemilik: Indonesia.
  - `rubric.md`: daftar cek per tahap sesuai spec bagian 5.
  - `CLAUDE.md` memuat:
    - Ringkasan proyek dan channel `@Economicforadults`.
    - Narator netral dan strategi CPM.
    - Aturan "hanya fitur HyperFrames gratis/lokal" dan daftar perintah terlarang.
    - Aturan push ke `main`.
    - Daftar perintah `sty`.
    - Pemicu "Handur, …" → skill handur.
  - `docs/setup/ipad.md`: buka aplikasi Claude → Code → pilih repo → buat environment cloud dengan setup script `curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync`, plus akses jaringan yang mengizinkan pencarian web dan npm → contoh perintah "Handur, carikan topik minggu ini".

- [ ] **Step 1: Test gagal `tests/test_agents.py`:**
  - `test_agent_frontmatter`: `name` = nama file, `description` tidak kosong, `tools` sesuai daftar di atas.
  - `test_handur_mentions_gates`: SKILL.md memuat `config.json`, `max_revision_rounds`, `sty review`, `sty approve`, `sty request`, dan keempat nama agent.
  - `test_udon_upload_only_after_final_approval`.
  - `test_claude_md_forbidden_commands_listed`.
  - `test_claude_md_has_channel`.
- [ ] **Step 2:** FAIL → **Step 3:** tulis file-file tersebut → **Step 4:** seluruh `uv run pytest -v` PASS.
- [ ] **Step 5:** Commit `feat: handur and agent team`.

### Task 10: Publikasi ke GitHub dan uji ujung ke ujung

**Files:** tidak ada file baru; hanya setup dan verifikasi.

- [ ] **Step 1:** Pemilik membuat repo **private** kosong (misalnya `stickman-yt`) dan memberi tahu nama akunnya. Push memakai `gh` CLI. Unduh binary resmi dari rilis `cli/cli` di GitHub ke folder sementara; login dilakukan pemilik sendiri lewat `gh auth login` di terminal. Lalu `git remote add origin … && git push -u origin main`.
- [ ] **Step 2:** Pemilik mengisi secrets mengikuti `docs/setup/telegram.md` dan `youtube.md`. Verifikasi: jalankan workflow "Telegram setup", lalu commit kosong dengan `notify: 🧪 tes` → pesan masuk di Telegram.
- [ ] **Step 3:** Pemilik menaruh 1–3 musik YouTube Audio Library di `assets/music/` (lewat web GitHub atau dari sesi cloud).
- [ ] **Step 4: Uji ujung ke ujung dari iPad:** "Handur, buat video tentang kenapa inflasi bikin tabungan menyusut". Hasil yang diharapkan:
  1. Topik bersumber diminta untuk dipilih.
  2. Naskah lolos Handur lalu disetujui pemilik.
  3. `sty request render` → Actions hijau → preview masuk ke Telegram dan `stills/` ter-commit.
  4. Handur memeriksa still.
  5. Metadata dan thumbnail siap, lalu persetujuan akhir.
  6. `sty request upload` → video **private** muncul di YouTube Studio channel Economic for adults, dan notifikasi Telegram terkirim.
- [ ] **Step 5:** Catat menit Actions yang terpakai per video di `docs/setup/ipad.md`, untuk perkiraan kuota 2.000 menit/bulan.
