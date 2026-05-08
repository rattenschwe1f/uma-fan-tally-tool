# uma-tally-tool

Daily Uma Musume circle quota reports as Discord-ready PNGs. The app fetches
circle data from [uma.moe](https://uma.moe), calculates monthly fan progress,
renders a ranked 30-row report, and posts it to Discord through a webhook.

## Examples

Dark mode, numbers layout:

![Dark mode numbers report](<docs/sample dark number.png>)

Dark mode, progress bars:

![Dark mode bar report](<docs/sample dark bar.png>)

## Features

- Fully hosted GitHub Actions flow for daily Discord posting.
- Uses GitHub repository Variables and Secrets; no committed `.env` is needed.
- Supports one club or many clubs from one scalable `CLUBS_JSON` secret.
- Fetches circle members and monthly fan totals from `uma.moe`.
- Uses one `MONTHLY_QUOTA`; daily pace is derived from the current month length.
- Supports `numbers` and `bar` quota layouts.
- Always renders 30 rank slots.
- Sorts members by fans gained this month.
- Shows rank movement compared with the previous recorded day.
- Optional columns for daily average, pace badge, needed/day, low days, and latest day gain.
- Optional `PIN_LEADER` mode keeps the leader first when uma.moe provides `leader_name`.
- Optional `HIGHLIGHT_LEADER` mode adds a small leader tag in the rank column.
- Strict or prorated quota handling for mid-month joiners.

## Use This Template

1. Click **Use this template** on GitHub.
2. Create your own repository from it. (i recommend making it private)
3. Go to **Settings -> Secrets and variables -> Actions**.
4. Add the Variables and Secrets listed below.
5. Open the **Actions** tab, enable workflows if GitHub asks, and run
   **Post daily club report** once with **Run workflow**.

The included workflow runs automatically at `15:10 UTC` every day except the
first of the month, where it runs at `09:10 UTC`.

## GitHub Variables

For one club, add these under
**Settings -> Secrets and variables -> Actions -> Variables**.

For multiple clubs, put per-club settings in the `CLUBS_JSON` Secret instead.
Variables here become defaults that every club can share.

| variable | required | example | description |
| --- | --- | --- | --- |
| `CIRCLE_ID` | one club only | `123456789` | Numeric uma.moe circle id. |
| `MONTHLY_QUOTA` | no | `60000000` | Monthly fan target per member. |
| `FONT` | no | `uma` | `uma` or `mplus`. |
| `LOW_DAY_THRESHOLD` | no | `500000` | Daily gain below this counts in `Days < N`. |
| `JOINER_QUOTA` | no | `strict` | `strict` or `prorated` for mid-month joiners. |
| `TALLY` | no | `complete` | `complete` ignores the in-progress game day; `live` includes it. |
| `EXPECTED_FANS_STYLE` | no | `bar` | `numbers` or `bar`. |
| `SHOW_DAILY_AVG` | no | `true` | Show/hide `Daily Avg`. |
| `SHOW_ON_PACE` | no | `true` | Show/hide the `Done`/`Yes`/`No` pace badge. |
| `SHOW_NEEDED_PER_DAY` | no | `true` | Show/hide `Needed/Day`. |
| `SHOW_DAYS_BELOW_THRESHOLD` | no | `true` | Show/hide `Days < N`. |
| `SHOW_LATEST_DAY` | no | `true` | Show/hide the latest `Day X` gain. |
| `PIN_LEADER` | no | `false` | Pin the leader first when `leader_name` is available. |
| `HIGHLIGHT_LEADER` | no | `false` | Show a small leader tag in the rank column. |
| `SAVE_OUTPUT` | no | `false` | Keep a local PNG in the Actions runner. Usually leave `false`. |
| `OUTPUT_DIR` | no | `out` | Folder used if `SAVE_OUTPUT=true`. |
| `CLUB_LOGO` | no | `icons/Gold_City/chr_icon_1040_901040_01.png` | Local logo path in the repo. |
| `LOGO_URL` | no | `https://chronogenesis.net/images/chara_icon/...png` | Optional logo URL downloaded during the run. |

Boolean settings accept `true/false`, `yes/no`, `on/off`, or `show/hide`.

Copy variable names:

```text
CIRCLE_ID
MONTHLY_QUOTA
FONT
LOW_DAY_THRESHOLD
JOINER_QUOTA
TALLY
EXPECTED_FANS_STYLE
SHOW_DAILY_AVG
SHOW_ON_PACE
SHOW_NEEDED_PER_DAY
SHOW_DAYS_BELOW_THRESHOLD
SHOW_LATEST_DAY
PIN_LEADER
HIGHLIGHT_LEADER
SAVE_OUTPUT
OUTPUT_DIR
CLUB_LOGO
LOGO_URL
```

## GitHub Secrets

Add these under
**Settings -> Secrets and variables -> Actions -> Secrets**.

| secret | required | description |
| --- | --- | --- |
| `UMA_API_KEY` | yes | API key sent to uma.moe as `X-API-Key`. |
| `DISCORD_WEBHOOK` | one club only | Discord webhook URL used to post the rendered report. |
| `CLUBS_JSON` | multiple clubs only | JSON array of club configs, including each club's webhook. |

To get your uma.moe API key, make an account on uma.moe, open **Settings**,
and generate an API key there.

Copy secret names:

```text
UMA_API_KEY
DISCORD_WEBHOOK
CLUBS_JSON
```

## Multiple Clubs

For multiple clubs, create one Secret named `CLUBS_JSON`. Because this includes
Discord webhook URLs, store it as a Secret, not a Variable.

Example:

```json
[
  {
    "name": "Club One",
    "circle_id": "123456789",
    "discord_webhook": "https://discord.com/api/webhooks/...",
    "monthly_quota": "45000000",
    "expected_fans_style": "bar",
    "logo_url": "https://chronogenesis.net/images/chara_icon/...png"
  },
  {
    "name": "Club Two",
    "circle_id": "987654321",
    "discord_webhook": "https://discord.com/api/webhooks/...",
    "monthly_quota": "60000000",
    "expected_fans_style": "numbers",
    "club_logo": "icons/Gold_City/chr_icon_1040_901040_01.png"
  }
]
```

Add another object to the array for each additional club. Any omitted setting
falls back to the repository Variable default, then to the app default.

Supported per-club keys:

```text
name
circle_id
discord_webhook
monthly_quota
low_day_threshold
font
joiner_quota
tally
expected_fans_style
show_daily_avg
show_on_pace
show_needed_per_day
show_days_below_threshold
show_latest_day
pin_leader
pin leader
highlight_leader
save_output
output_dir
club_logo
logo_url
uma_api_key
```

Most setups should use one shared `UMA_API_KEY` Secret and put only
club-specific values in `CLUBS_JSON`.

## Local Development

Install from source:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

For local test runs, either export environment variables or create your own
ignored `.env` file from `src/uma_tally_tool/config.example.env`.

```bash
python -m uma_tally_tool --env .env
```

If `DISCORD_WEBHOOK` is set, the report is posted to Discord. If it is blank,
the app saves a PNG to `OUTPUT_DIR` so local test runs still produce something
you can inspect.

## CLI Overrides

Every setting can be overridden from the command line:

| flag | overrides |
| --- | --- |
| `--env PATH` | path to a local `.env` |
| `--circle-id N` | `CIRCLE_ID` |
| `--monthly-quota N` | `MONTHLY_QUOTA` |
| `--threshold N` | `LOW_DAY_THRESHOLD` |
| `--font {uma,mplus}` | `FONT` |
| `--joiner-quota {strict,prorated}` | `JOINER_QUOTA` |
| `--tally {live,complete}` | `TALLY` |
| `--expected-fans-style {numbers,bar}` | `EXPECTED_FANS_STYLE` |
| `--show-daily-avg` / `--hide-daily-avg` | `SHOW_DAILY_AVG` |
| `--show-on-pace` / `--hide-on-pace` | `SHOW_ON_PACE` |
| `--show-needed-per-day` / `--hide-needed-per-day` | `SHOW_NEEDED_PER_DAY` |
| `--show-days-below-threshold` / `--hide-days-below-threshold` | `SHOW_DAYS_BELOW_THRESHOLD` |
| `--show-latest-day` / `--hide-latest-day` | `SHOW_LATEST_DAY` |
| `--pin-leader` / `--no-pin-leader` | `PIN_LEADER` |
| `--highlight-leader` / `--no-highlight-leader` | `HIGHLIGHT_LEADER` |
| `--out DIR` | `OUTPUT_DIR` |
| `--save-output` / `--no-save-output` | `SAVE_OUTPUT` |
| `--logo PATH` | `CLUB_LOGO` |
| `--uma-api-key KEY` | `UMA_API_KEY` |
| `--discord-webhook URL` | `DISCORD_WEBHOOK` |

## Report Columns

- `#`: current rank by monthly fans gained, plus movement from yesterday.
- `Trainer`: member name from uma.moe.
- `Expected`: expected progress by the cutoff day in `numbers` mode.
- `Total Fans`: monthly fans gained so far in `numbers` mode.
- `Monthly Progress`: progress bar in `bar` mode, filled blue when on pace and red when behind.
- `Daily Avg`: average fans per day.
- `On Pace?`: `Done`, `Yes`, or `No`.
- `Behind By`: how far behind expected pace the member is.
- `Needed/Day`: average fans needed per remaining day to hit monthly quota.
- `Days < N`: count of days below `LOW_DAY_THRESHOLD`.
- `Day X`: fan gain on the latest snapshotted day.

## Development

```bash
pip install -e ".[dev]"
pytest -m "not network"
python -m uma_tally_tool --env .env
```

The GitHub Actions workflow uses the same package code through:

```bash
python -m uma_tally_tool.batch
```

That batch runner reads `CLUBS_JSON` when present, or falls back to the
single-club `CIRCLE_ID` and `DISCORD_WEBHOOK` settings.

## Notes

- Source API: `https://uma.moe/api/v4/circles?circle_id=...`
- API authentication is sent with the `X-API-Key` header from `UMA_API_KEY`.
- Game days roll at `15:00 UTC`.
- `TALLY=complete` trims the in-progress game day.
- `TALLY=live` includes the in-progress game day.
- Members with no recorded fans this month are filtered out as inactive.
- `JOINER_QUOTA=prorated` scales mid-month joiners to their days in club.

# credit
my good friend turtle who built the base this was built upon after yoinking my idea from me xdd
