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

## Setup
```bash
cd ~/dev/polymarket
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scrape_polymarket.py
```

## Install hourly cron
The project uses GitHub Actions to run the scraper automatically every hour using a scheduled workflow.
```bash
cd ~/dev/polymarket
./install_cron.sh
```

This installs:
```cron
0 * * * * cd ~/dev/polymarket && python3 scrape_polymarket.py >> ~/dev/polymarket/logs/cron.log 2>&1
```

## Verify cron
```bash
crontab -l | grep scrape_polymarket.py
tail -f ~/dev/polymarket/logs/cron.log
```
