#!/bin/zsh
# Startet den Tageslauf auf dem Mac. Wird von launchd aufgerufen (com.connorsbot.daily.plist).
# caffeinate -i verhindert, dass der Mac schläft, während der Bot bis kurz vor Schluss wartet.
set -euo pipefail
REPO="$HOME/hello-world"
set -a; source "$HOME/connors-bot.env"; set +a   # Einstellungen (Vorlage: ../connors-bot.env.example)
cd "$REPO"
exec /usr/bin/caffeinate -i "$HOME/venv-connors/bin/python" -m connors_bot.main --mode "${CB_MODE:-paper}" --wait
