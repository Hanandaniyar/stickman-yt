#!/bin/zsh
# Jalankan Handur yang menerima perintah dari Telegram.
# Token bot disimpan di ~/.config/handur/telegram.env (bukan di ~/.claude/channels/telegram/.env),
# supaya sesi Claude lain tidak ikut menyalakan bot dan merebutnya.
set -a
source ~/.config/handur/telegram.env
set +a
export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
cd ~/Desktop/stickman-yt || exit 1
caffeinate -i -w $$ &
exec claude --channels plugin:telegram@claude-plugins-official
