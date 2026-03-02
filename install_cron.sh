#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
CRON_EXPR="0 * * * *"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/cron.log"

mkdir -p "$LOG_DIR"

JOB="$CRON_EXPR cd $PROJECT_DIR && $PYTHON_BIN scrape_polymarket.py >> $LOG_FILE 2>&1"

( crontab -l 2>/dev/null | grep -v 'scrape_polymarket.py' ; echo "$JOB" ) | crontab -

echo "Installed cron job:"
echo "$JOB"
