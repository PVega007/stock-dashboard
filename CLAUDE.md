# CLAUDE.md — Patricia Vega Portfolio Dashboard
## Operational Knowledge Base · Last updated: June 23, 2026 (evening)

This file is read-first at the start of every session. It contains the authoritative operational knowledge for this workspace. **Before doing any work, read this file completely.**

---

## 1. What This Workspace Is

An active portfolio analysis and monitoring system for Patricia's 35-stock watchlist, consisting of:
- An interactive HTML dashboard (`stock_dashboard.html`) with live prices, entry targets, statuses, and full stock analyses
- Automated scheduled tasks for pre-market briefings, market-close checks, and macro reactions
- A persistent parameters file (`investment_parameters.json`) as the single source of truth for all valuation inputs
- A briefings archive with daily markdown files and Word documents

---

## 2. File Structure — Exact Paths

```
/Users/pvegamacbookair/Claude Cowork/       ← WORKSPACE ROOT
├── CLAUDE.md                                ← THIS FILE (read first)
├── stock_dashboard.html                     ← Main dashboard (35 stocks)
├── investment_parameters.json               ← Valuation parameters (authoritative)
├── index.html                               ← GitHub Pages redirect
├── Briefings/                               ← ⚠️ Capital B, NOT "BRIEFINGS"
│   ├── append_briefing.py                   ← Helper: saves briefing to dashboard + .md
│   ├── YYYY-MM-DD-premarket.md              ← Pre-market briefing files
│   ├── YYYY-MM-DD-market-close.md           ← Market-close briefing files
│   └── *.docx                               ← Word document reports
├── Q2_2026_Quarterly_Report.txt             ← Reference
├── github_push.py                           ← GitHub sync utility
└── github_setup.sh                          ← GitHub setup script
```

**⚠️ CRITICAL PATH NOTES:**
- The briefings folder is `Briefings/` — capital B only. On macOS (case-insensitive) `BRIEFINGS/` and `Briefings/` resolve to the same folder, but in the Linux bash sandbox they are DIFFERENT. Always use `Briefings/` exactly.
- The append_briefing.py path used in Python: `sys.path.insert(0, '/Users/pvegamacbookair/Claude Cowork/Briefings')`
- In the bash sandbox, the workspace mounts at: `/sessions/<id>/mnt/Claude Cowork/`

---

## 3. FMP (Financial Modeling Prep) MCP Connector

**Plan level: Starter**

### ✅ Endpoints that WORK on Starter plan

| Use case | Tool | Endpoint | Notes |
|---|---|---|---|
| Pre-market / after-hours price | `quote` | `aftermarket-quote` | Call **individually** per ticker (e.g. `symbol: "NVDA"`) |
| Regular quote | `quote` | `quote` | Individual calls only |
| Earnings calendar | `calendar` | `earnings-calendar` | Works fine |
| Stock news | `news` | `search-stock-news` | Works fine |
| General news | `news` | `general-news` | Works fine |
| Analyst estimates | `analyst` | various | Works fine |
| Company info | `company` | various | Works fine |
| Financial statements | `statements` | various | Works fine |

### ❌ Endpoints that FAIL on Starter plan (require Premium+)

| Tool | Endpoint | Error |
|---|---|---|
| `quote` | `batch-aftermarket-quote` | Premium required |
| `quote` | `batch-quote` | Premium required |
| `quote` | `batch-quote-short` | Premium required |
| `indexes` | `all-index-quotes` | Ultimate required |
| `indexes` | most index endpoints | Ultimate required |

### ⚠️ Key FMP Operational Rules

1. **Never use batch quote endpoints** — they require Premium. Always loop through tickers one at a time using `aftermarket-quote` or `quote`.
2. **FRVO and LEU**: flag any move >10% for Patricia's manual review — do not auto-update.
3. **International ETFs** (EWL, AVDE, FENI, SCHF): expect zero pre-market volume — keep stored price, this is normal.
4. **Data quality check**: divergence >25% from stored price → flag and skip. Bid/ask spread >3% AND volume <500 → unreliable, keep stored price.
5. FMP `aftermarket-quote` returns `{symbol, ask, bid, aSize, bSize, volume, ...}`. Midpoint = (ask + bid) / 2.

---

## 4. Dashboard (`stock_dashboard.html`)

### Structure
The dashboard is a single self-contained HTML file. Stock data lives in a JavaScript array `const STOCKS = [...]` near the top of the file.

Each stock entry contains:
```javascript
{ ticker:"NVDA", name:"...", sector:"...", priceResearch:"$204.41", priceDate:"June 11, 2026",
  entryTarget:"$271–$319 | $320–$354", marketCap:"...", analystTarget:"...",
  status:"BUY ZONE",  // "BUY ZONE" | "WATCH" | "OVERVALUED"
  category:"Tech/AI",
  scores:{macro:X, business:X, financial:X, management:X, governance:X, valuation:X},
  ... }
```

### Updating Prices via Python (preferred method)

```python
import re

def update_price(html, ticker, new_price, new_date):
    # Update priceResearch (handles both "priceResearch:" and "priceResearch :" formats)
    pattern = (
        r'(ticker:\s*["\']' + re.escape(ticker) + r'["\']'
        r'.*?priceResearch:\s*["\'])'
        r'[^"\']*'
        r'(["\'])'
    )
    html, n = re.subn(pattern, r'\g<1>' + new_price + r'\g<2>', html, count=1, flags=re.DOTALL)
    # Also update priceDate
    pattern2 = (
        r'(ticker:\s*["\']' + re.escape(ticker) + r'["\']'
        r'.*?priceDate:\s*["\'])'
        r'[^"\']*'
        r'(["\'])'
    )
    html, _ = re.subn(pattern2, r'\g<1>' + new_date + r'\g<2>', html, count=1, flags=re.DOTALL)
    return html, n
```

### Updating Entry Targets
```python
pattern = (
    r'(ticker:\s*["\']' + re.escape(ticker) + r'["\']'
    r'.*?entryTarget:\s*["\'])'
    r'[^"\']*'
    r'(["\'])'
)
```

### Updating Status
```python
pattern = (
    r'(ticker:\s*["\']' + re.escape(ticker) + r'["\']'
    r'.*?status:\s*["\'])'
    r'[^"\']+' 
    r'(["\'])'
)
```

### Status Thresholds
- **BUY ZONE**: price ≤ T1 floor
- **WATCH**: price between T1 floor and T2 ceiling
- **OVERVALUED**: price > T2 ceiling

### P/E Column (added June 23, 2026)

A **P/E (TTM | Target)** column is displayed in the main table and detail panel, sourced from:
- `PE_DATA` JS constant embedded in the dashboard (TTM values fetched from FMP `metrics-ratios-ttm` endpoint; target ranges from `investment_parameters.json`)
- ETFs (VOO, XLU, IAU, REMX, SOXQ, EWY, EWL, AVDE, FENI, SCHF) and FRVO show "—" for TTM P/E — ratios endpoints return no data for these
- Column is sortable; stocks without a valid TTM P/E sort to the bottom (value 9999)

```javascript
// PE_DATA structure
const PE_DATA = {
  "NVDA": { ttm: "30.6×", target: "35–42×", note: "" },
  "MU":   { ttm: "48.7×", target: "22–28× norm.", note: "* TTM = peak cycle; target uses mid-cycle EPS" },
  // ... all 35 stocks
};
```

### Bear Market Defense Framework (added June 23, 2026)

**Key JS constants and functions:**

```javascript
// INVESTMENT_PARAMS — investment_parameters.json embedded as a JS constant
// (browser cannot read disk files; must be kept in sync manually if JSON changes)
const INVESTMENT_PARAMS = { holdings: { "NVDA": { low_pe:35, high_pe:42, mos:0.15, metric:"fwd_pe", bear_discount:0.30 }, ... } };

// Active regime state
let activeRegime = "BULL_MARKET";  // or "BEAR_MARKET"

// T3 Bear Floor = T1 floor × (1 − bear_discount)
function getT3BearFloor(ticker, entryTarget) { ... }

// parseT1Floor — strips commas, matches first $number in entryTarget string
function parseT1Floor(entryTarget) { ... }
```

**Bear mode UI elements:**
- `#regime-toggle-btn` — button in toolbar; toggles `activeRegime` and calls `renderTable()`
- `#regime-banner` — red banner above table, visible only in Bear mode
- Row-level highlight in `renderTable()`: when `activeRegime === 'BEAR_MARKET' && price < t3Floor`, row gets `rgba(220,38,38,0.08)` background + red left border
- `🚨 BEAR FLOOR` red pill badge appears below status badge in the status column (main table, visible at a glance)
- `bearFloorAlertHtml()` in detail panel: full CRITICAL ALIGNMENT alert with dollar and % gap when price < T3

**When INVESTMENT_PARAMS changes** (new stock, bear_discount revision, etc.), update BOTH `investment_parameters.json` AND the `INVESTMENT_PARAMS` constant in `stock_dashboard.html`. They must stay in sync.

### Bear Floor in Entry Target Column (added June 23, 2026)

The entry target cell shows a third line: `🐻 $XXX` — the T3 Bear Floor — for all stocks that have a `bear_discount` in `INVESTMENT_PARAMS`. ETFs and FRVO (no bear_discount) show nothing. Always visible regardless of regime mode.

```javascript
// In renderTable(), entry target cell:
${(() => { const t3 = getT3BearFloor(stock.ticker, stock.entryTarget); return t3 ? `<div class="bear-floor-line">🐻 $${t3.toLocaleString()}</div>` : ''; })()}
// CSS: .entry-cell .bear-floor-line { font-size:10px; color:#f87171; margin-top:3px; opacity:0.85; }
```

### Default Sort Order (added June 23, 2026)

When no column sort is active, the table defaults to: **BUY ZONE → WATCH → OVERVALUED**.

In Bear mode, stocks below their T3 Bear Floor float to the very top (above all BUY ZONE stocks), then the rest follow in status order. Any user-applied column sort or filter overrides this default.

---

## 5. Entry Target Methodology (v3 — Hybrid, updated June 23, 2026)

**Always read `investment_parameters.json` before recalculating any entry targets.**

### Formula
```
Forward EPS   = Current Price ÷ Forward P/E (consensus)
                OR analyst mid-cycle normalized EPS where noted (MU, FSLR)
                OR DCF/unit where noted (HESM)
                OR price-based support levels where noted (IAU, REMX)

T1 floor      = Forward EPS × Low P/E × (1 − MoS)            ← deep entry, full discount
T1 ceiling    = Forward EPS × Low P/E                          ← low-end fair value, no discount
T2 ceiling    = Forward EPS × High P/E × (1 − ½ MoS)         ← bull-case, half discount
Bear Floor    = T1 floor × (1 − bear_discount)                ← recession/crash scenario floor
               bear_discount: Defensive 20%, Growth/Tech 30%, Cyclical 35-40%

Dashboard format: "$T1floor–$T1ceil | $(T1ceil+1)–$T2ceil"
bearFloor field: "$XXX" (displayed separately in detail panel)
```

### Execution Confirmation Layer (NEW in v3)
Before deploying capital when price reaches T1 zone, check **2+ of 4 signals**:
1. **RSI (14-day) < 45** — confirms oversold condition aligned with entry
2. **MACD daily converging** — histogram bars shrinking or bullish cross printed
3. **Price at/below 50-day SMA** — aligns entry with institutional support
4. **Price below 9-day EMA** — confirms stock in drawdown, not a dip on uptrend

**2+ signals** → HIGH CONVICTION — scale up tranche size  
**0–1 signals** → deploy minimum tranche only, wait for confirmation

### Calculation Helper
```python
def calc(eps, lo, hi, mos):
    t1_floor  = round(eps * lo * (1 - mos))
    t1_ceil   = round(eps * lo)
    t2_ceil   = round(eps * hi * (1 - mos / 2))
    return t1_floor, t1_ceil, t2_ceil

def bear_floor(t1_floor, bear_discount):
    return round(t1_floor * (1 - bear_discount))

def fmt(v):
    return f"${v:,}" if v >= 1000 else f"${v}"
```

### Special Cases
| Ticker | Metric | Note |
|---|---|---|
| MU | Normalized P/E (22–28×) | Use mid-cycle EPS ~$50, NOT peak forward EPS (~$103) |
| FRVO | EV/PPA backlog (1.5–2.0×) | Applied to backlog/share $26.77. Pre-revenue |
| WDC | EV/EBITDA (14–18×) | Forward EPS used as proxy since EBITDA/share unavailable |
| FSLR | Normalized P/E (14–18×) | Policy-sensitive; use mid-cycle EPS |
| HESM | P/DCF (11–14×) | Applied to distributable cash flow/unit ~$2.90. Not GAAP EPS |
| IAU | Price-based support | T1: $61–68 (52-wk low area), T2: $69–88. No P/E |
| REMX | Price-based support | T1: $42–60 (near 52-wk low), T2: $61–88. Hyper-cyclical |

### All P/E Ranges, MoS, bear_discount — see `investment_parameters.json`
The JSON file is the authoritative source. Do not use any other source for these values. Always read it before running calculations.

---

## 6. Scheduled Tasks

All tasks are configured in the Claude app. Task IDs are exact — use these when calling `update_scheduled_task`.

| Task ID | Schedule | Purpose |
|---|---|---|
| `premarket-price-check` | 7:01 AM CT, Mon–Fri | Fetch pre-market prices, update dashboard, save briefing, auto-push GitHub |
| `market-close-price-check` | 3:39 PM CT, Mon–Fri | Fetch closing prices, update dashboard, save briefing, auto-push GitHub |
| `weekly-portfolio-review` | 10:05 AM CT, Saturday | Macro scores + event-driven re-analysis (~30–45 min) |
| `quarterly-full-refresh` | 10 AM CT, 1st Sat of Jan/Apr/Jul/Oct | Full 12-step re-analysis all 35 stocks |
| `macro-reassessment` | Manual only | Full macro reassessment when triggered by briefings |

**GitHub auto-push** (added June 23, 2026): Both price-check tasks now automatically call `github_push.py` at the end of each run (PART 6). No manual Terminal push needed after briefings.

**One-time macro reaction tasks** are created ad hoc when major data releases are scheduled (CPI, PCE, GDP, FOMC, etc.). These fire 30 min after the release time and are automatically disabled after running.

### Briefing Save Procedure (used in all price-check tasks)
```python
import sys
sys.path.insert(0, '/Users/pvegamacbookair/Claude Cowork/Briefings')
from append_briefing import save_briefing

save_briefing(briefing_dict, content_md)
# Saves to: dashboard Briefings tab + /Users/pvegamacbookair/Claude Cowork/Briefings/YYYY-MM-DD-[type].md
```

**⚠️ MANDATORY AFTER EVERY BRIEFING:** After calling `save_briefing`, always call `mcp__cowork__present_files` with the saved .md file path so Patricia gets a downloadable card in chat. Example:
```python
# After save_briefing completes:
filepath = "/Users/pvegamacbookair/Claude Cowork/Briefings/YYYY-MM-DD-market-close.md"
# Then present_files(filepath) in the response
```
This applies to ALL briefing types: pre-market, market-close, weekly review, and ad-hoc.

---

## 7. The 35 Holdings

**Current as of June 23, 2026.** Grouped by category (matches dashboard category filter):

| Category | Tickers |
|---|---|
| Tech/AI | NVDA, AMD, MRVL, AVGO, MSFT, GOOGL, AMZN, HON, HPE, HPQ |
| Semiconductors | MU, WDC, TXN, FSLR, PLAB, CRUS, TSM, LEU |
| Healthcare | LLY, NVO |
| Financials | BRK-B |
| Energy | FRVO, HESM |
| Utilities | CEG, NEE |
| International ETF | EWY, EWL, AVDE, FENI, SCHF |
| US ETF | VOO, XLU, IAU, REMX, SOXQ |

**Removed June 23, 2026:** AMKR, AMAT, TER, CRWV, SWKS, NXPI, QCOM, CSCO, INTC, LITE  
**Added June 23, 2026:** HESM, CEG, NEE, XLU, IAU, REMX, SOXQ

---

## 8. Current Status Snapshot (as of June 23, 2026 — market close)

| Status | Tickers |
|---|---|
| BUY ZONE | FRVO, FSLR, HPQ, MSFT, NVDA, PLAB |
| WATCH | AMZN, AVDE, BRK-B, CEG, EWL, EWY, FENI, GOOGL, HESM, HON, IAU, LLY, MU, NEE, NVO, SCHF, VOO, XLU |
| OVERVALUED | AMD, AVGO, CRUS, HPE, LEU, MRVL, REMX, SOXQ, TXN, TSM, WDC |

*Status changes whenever prices are updated — check dashboard for current state.*

---

## 9. Lessons Learned (Prevent Rework)

These are mistakes that have actually occurred — read carefully.

### Formula / Calculation
- **T2 ceiling requires ½ MoS discount**: `EPS × High P/E × (1 − ½ MoS)`. A prior session omitted this, producing ranges that were too wide.
- **MU uses normalized EPS ~$50, not forward EPS ~$103**: Micron is highly cyclical. Peak forward EPS produces unrealistic entry targets. Always use mid-cycle normalized.
- **HESM uses P/DCF, not EPS**: It's an MLP — use distributable cash flow per unit (~$2.90), with Low 11×/High 14×/MoS 12%.
- **IAU and REMX use price-based support levels, not P/E**: Hard asset ETFs — T1/T2 zones derived from 52-week lows and 200-day SMA, not earnings multiples.
- **P/E ranges are "deserved" multiples, not current market multiples**: They represent what the business deserves based on quality/moat/growth. Never replace these with current market forward P/E from GuruFocus or elsewhere.
- **Always read `investment_parameters.json` first** before any entry target recalculation. Context compaction has caused P/E range drift twice.
- **v3 adds Bear Floor and Execution Confirmation Layer**: Bear Floor = T1 floor × (1 − bear_discount). Execution layer = RSI/MACD/SMA signals checked before deploying capital in T1 zone.

### File / Folder Operations
- **Briefings folder is `Briefings/`** (capital B, lowercase rest). macOS is case-insensitive so both work in Finder, but the Linux bash sandbox is case-sensitive. Always write `Briefings/` exactly.
- **Never use `batch-aftermarket-quote`** — requires Premium FMP plan. Use individual `aftermarket-quote` calls looping through tickers one at a time.
- **Dashboard has two price field formats**: some entries use `priceResearch:"$X"` (no space after colon) and others use `priceResearch: "$X"` (space). The regex pattern handles both.

### GitHub Push
- **`github_push.py` must use `--force` and token-in-URL**: Plain `git push origin main` fails when remote has diverged. Always use `git push --force https://PVega007:{token}@github.com/PVega007/stock-dashboard.git main`. The updated script handles this automatically.
- **Stale lock files**: If git crashes mid-run, `.git/index.lock` or `.git/HEAD.lock` may be left behind. The updated `github_push.py` auto-removes them on each run.
- **Sandbox cannot push to GitHub**: The Linux bash sandbox has network restrictions blocking outbound git. The `github_push.py` script must be called via `subprocess` from the scheduled task (which runs on the Mac) — never run it directly from the bash tool.

### Bear Framework / Dashboard JS
- **`INVESTMENT_PARAMS` JS constant must be kept in sync with `investment_parameters.json`**: The browser cannot read files from disk. When the JSON file is updated (new stock, revised bear_discount, etc.), the embedded `INVESTMENT_PARAMS` constant in `stock_dashboard.html` must also be updated manually.
- **Bear mode alert fires only when `activeRegime === 'BEAR_MARKET'`**: Toggling Bear mode off removes all row highlights and badges — this is correct behavior. In Bull mode, the dashboard looks identical to before the feature was added.
- **`parseT1Floor()` strips commas**: entryTarget strings like `"$1,100–$1,260"` must have commas removed before regex matching. The function handles this.
- **MU status changed to WATCH** (June 23, 2026): Price $1,211.38 is above T1 ceiling ($1,100) and below T2 ceiling ($1,260) → WATCH, not BUY ZONE. Mid-cycle EPS remains ~$50 for target calculations.

### Context Compaction
- **`investment_parameters.json` is the remedy for financial parameter drift**: Any time entry targets need recalculation, read this file first. It contains all agreed P/E ranges, MoS values, and metric types.
- **`CLAUDE.md` (this file) is the remedy for operational knowledge drift**: Folder paths, FMP endpoints, task IDs, and procedural notes live here.
- **Both files must be updated when anything changes** — they are only useful if kept current.

---

## 10. Key Reference Dates

| Event | Date |
|---|---|
| Dashboard project started | ~May 2026 |
| investment_parameters.json created | June 11, 2026 |
| Entry targets recalculated (v2, correct formula) | June 11, 2026 |
| CLAUDE.md created | June 12, 2026 |
| v3 Hybrid Methodology adopted | June 23, 2026 |
| Portfolio restructured: 38 → 35 stocks | June 23, 2026 |
| Gemini technical analysis integrated (T3 Bear Floor + Confirmation Layer) | June 23, 2026 |
| PE_DATA + P/E column added to dashboard | June 23, 2026 |
| INVESTMENT_PARAMS embedded in dashboard JS | June 23, 2026 |
| Bear Market regime toggle + T3 Bear Floor alerts added | June 23, 2026 |
| 🚨 BEAR FLOOR row badge + row highlight added to main table | June 23, 2026 |
| MU status corrected: BUY ZONE → WATCH ($1,211.38 > T1 ceiling $1,100) | June 23, 2026 |
| Bear floor line added to Entry Target column (always visible) | June 23, 2026 |
| Default sort order added: BUY ZONE → WATCH → OVERVALUED; bear alerts float to top | June 23, 2026 |
| github_push.py updated: --force, token-in-URL, auto lock cleanup | June 23, 2026 |
| Scheduled tasks updated: auto GitHub push + downloadable briefing card after every run | June 23, 2026 |
| Market close briefing run: global AI selloff, MU -13.2%, 3 status changes | June 23, 2026 |
| Status changes (close): MU→WATCH, LEU→OVERVALUED, VOO→WATCH | June 23, 2026 |
| Next quarterly full refresh | First Saturday of July 2026 |
| Upcoming: PCE + GDP Final | June 25, 2026 |
| Upcoming: JOLTS | June 30, 2026 |

---

## 11. How to Update This File

Update CLAUDE.md whenever:
- A new stock is added to the dashboard
- A scheduled task is created, modified, or deleted
- A folder is renamed or created
- An FMP endpoint behavior changes
- A new operational lesson is learned
- Entry target methodology changes (also update `investment_parameters.json`)

**This file + `investment_parameters.json` together represent the complete state of the project's operational and financial knowledge.**
