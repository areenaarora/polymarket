# polymarket

Hourly scraper for Polymarket categories:
- World Events
- Tech

For each category, captures top 20 markets ranked by **24h volume**.

## Captured fields
- `time`
- `category`
- `market_id`
- `slug`
- `question`
- `volume24hr_usd`
- `volume_total_usd`
- `end_date`
- `options` and `results_pct`

## Output files
Under `data/`:
- `snapshots_long.csv` → append-only history (one row per market per run)
- `snapshots_wide.csv` → one row per market, each run adds new timestamped columns (volume/results)
- `latest.json` → latest run dump for quick inspection
- `.last_signature.txt` → last material-data signature used to skip no-op writes

If Polymarket data is unchanged vs previous run, the scraper now skips writes to avoid noisy commits.

## Setup
```bash
cd ~/dev/polymarket
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scrape_polymarket.py
```

## Scheduler (Primary)
Primary scheduler is **GitHub Actions** (`.github/workflows/polymarket-hourly.yml`) running hourly.

## Optional local fallback (cron)
Only use local cron if you want a machine-local backup runner.
```bash
cd ~/dev/polymarket
./install_cron.sh
```

This installs:
```cron
0 * * * * cd ~/dev/polymarket && python3 scrape_polymarket.py >> ~/dev/polymarket/logs/cron.log 2>&1
```

## Verify local cron (optional)
```bash
crontab -l | grep scrape_polymarket.py
tail -f ~/dev/polymarket/logs/cron.log
```
