# CLAUDE.md — Patricia Vega Portfolio Dashboard
## Operational Knowledge Base · Last updated: July 11, 2026

This file is read-first at the start of every session. It contains the authoritative operational knowledge for this workspace. **Before doing any work, read this file completely.**

---

## 1. What This Workspace Is

An active portfolio analysis and monitoring system for Patricia's 31-stock watchlist, consisting of:
- An interactive HTML dashboard (`stock_dashboard.html`) with live prices, entry targets, statuses, and full stock analyses
- Automated scheduled tasks for pre-market briefings, market-close checks, and macro reactions
- A persistent parameters file (`investment_parameters.json`) as the single source of truth for all valuation inputs
- A briefings archive with daily markdown files and Word documents

---

## 2. File Structure — Exact Paths

```
/Users/pvegamacbookair/Claude Cowork/       ← WORKSPACE ROOT
├── CLAUDE.md                                ← THIS FILE (read first) — now pushed to GitHub on every price check
├── stock_dashboard.html                     ← Main dashboard (31 stocks)
├── investment_parameters.json               ← Valuation parameters (authoritative) — now pushed to GitHub too
├── Position_Tracker.md                      ← Patricia's personal tranche/exit tracker (added Jul 9, 2026) — NEVER pushed to GitHub (see §4B)
├── index.html                               ← GitHub Pages redirect
├── export_stocks.js                         ← Generates stocks.json/csv/stocks_full.json from the dashboard (added Jul 11, 2026, see §4B)
├── stocks.json / stocks.csv                 ← Lean, formula-friendly export (ticker/price/targets/scores) — auto-generated, don't hand-edit
├── stocks_full.json                         ← Full per-stock narrative export (summary/macroContext/redFlags/verdict/etc.) — auto-generated, don't hand-edit
├── Briefings/                               ← ⚠️ Capital B, NOT "BRIEFINGS"
│   ├── append_briefing.py                   ← Helper: saves briefing to dashboard + .md
│   ├── YYYY-MM-DD-premarket.md              ← Pre-market briefing files
│   ├── YYYY-MM-DD-market-close.md           ← Market-close briefing files
│   └── *.docx                               ← Word document reports
├── Q2_2026_Quarterly_Report.txt             ← Reference
├── github_push.py                           ← GitHub sync utility — also runs export_stocks.js before staging (see §4B)
└── github_setup.sh                          ← GitHub setup script
```

**⚠️ CRITICAL PATH NOTES:**
- The briefings folder is `Briefings/` — capital B only. On macOS (case-insensitive) `BRIEFINGS/` and `Briefings/` resolve to the same folder, but in the Linux bash sandbox they are DIFFERENT. Always use `Briefings/` exactly.
- The append_briefing.py path used in Python: `sys.path.insert(0, '/Users/pvegamacbookair/Claude Cowork/Briefings')`
- In the bash sandbox, the workspace mounts at: `/sessions/<id>/mnt/Claude Cowork/`

**`Position_Tracker.md` (added Jul 9, 2026):** A simple markdown file, separate from the dashboard, that tracks Patricia's actual open tranches for positions she's personally exiting or calibrating — entry price, share count, status (OPEN/CLOSED), exit target (e.g. a GTC limit price), and the technical/macro rationale behind that target. This is distinct from `stock_dashboard.html`'s `entryTarget`/`status` fields, which reflect the general valuation framework (T1/T2/Bear Floor) for all 31 holdings, not Patricia's specific cost basis or personal exit plans. Both `premarket-price-check` and `market-close-price-check` read this file (PART 1C — lightweight, no dashboard mutation) and flag in the briefing when a tracked ticker's price has reached or is within ~1% of its exit target. Update this file manually (or ask Claude to update it) whenever a tranche is opened, closed, or a target changes — it will silently go stale otherwise, the same way `MACRO_CALENDAR` did.

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

## 4B. External Data Exports — for Claude for Excel / other tools (added July 11, 2026)

**Why this exists:** Patricia is building a short-term-lens investment dashboard in Excel (same watchlist, reframed around short-term signals — RSI/MACD/SMA, range trades like the NVDA/MSFT mini-tranche strategy) and wants Claude for Excel to be able to see this dashboard's data to assess what's reusable. Claude for Excel cannot browse the filesystem — per Anthropic's docs it "can only access the workbook you have open in Excel," plus Connectors and native Excel web-import formulas (WEBSERVICE/IMPORTDATA/IMPORTXML/etc.). Since `stock_dashboard.html` is already public on GitHub Pages (`PVega007/stock-dashboard`, confirmed public repo), the fix is exporting clean data to that same repo that Excel can fetch by URL — no GitHub connector/auth needed for read access since the repo is public.

**Three export files, all auto-generated by `export_stocks.js` — never hand-edit them:**

| File | Purpose | Raw URL |
|---|---|---|
| `stocks.json` | Lean, tabular: ticker/name/sector/status/price/entryTarget (+ parsed t1_floor/t1_ceiling/t2_ceiling)/analystTarget/marketCap/PE/scores. Best for Excel formulas (WEBSERVICE/IMPORTDATA) since it's small. | `https://raw.githubusercontent.com/PVega007/stock-dashboard/main/stocks.json` |
| `stocks.csv` | Same lean data as stocks.json, CSV form — easiest single-formula pull into a range via `IMPORTDATA`. | `https://raw.githubusercontent.com/PVega007/stock-dashboard/main/stocks.csv` |
| `stocks_full.json` | Full per-stock narrative: `summary`, `steps.macroContext/priceAction/business/financial/management/governance/valuation/catalysts`, `redFlags`, `verdict` (or `steps.s11`), `scores`, PE data. ~200KB — too large for a single Excel cell via WEBSERVICE, meant for an LLM (Claude for Excel via a connector, or pasted/read directly) to reason over, not for spreadsheet formulas to parse. | `https://raw.githubusercontent.com/PVega007/stock-dashboard/main/stocks_full.json` |

**How they get generated and published:** `export_stocks.js` reads `stock_dashboard.html` directly (executes its own `const STOCKS = [...]` / `const PE_DATA = {...}` statements in a Node `vm` sandbox rather than regex-parsing them — regex broke on nested brackets/quotes in `redFlags` and note strings; see Lessons Learned below). `github_push.py` now calls `node export_stocks.js` before staging, then also pushes `investment_parameters.json` and `CLAUDE.md` (previously untracked/unpushed despite being referenced as public) alongside the usual `index.html`/`stock_dashboard.html`. This means **every scheduled `premarket-price-check` / `market-close-price-check` run refreshes and republishes all three export files automatically** — no separate step needed in those task prompts beyond the existing PART 6 GitHub push call.

**⚠️ `Position_Tracker.md` is intentionally never included in any export or push.** It contains Patricia's personal account structure (which tranches sit in her IRA vs. her husband's IRA vs. taxable accounts), specific entry prices, and wash-sale tax strategy — meaningfully more sensitive than the general 31-stock valuation framework already public in the dashboard. If Patricia ever wants the *range-trade methodology* (not the personal account/tax specifics) available to Excel too, that would need a separate, explicitly-approved, redacted export — don't infer consent from this section.

**Manual publish note:** Like all GitHub pushes, this only works from a real push context (Patricia's Mac, via the LaunchAgent or a manual `python3 github_push.py` in Terminal) — a sandboxed session's `github_push.py` call will fail on `github_token.txt` access exactly as documented in §9, and the export files just won't be picked up until the next successful push.

---

## 5. Entry Target Methodology (v3 — Hybrid, updated June 23, 2026)

**Always read `investment_parameters.json` before recalculating any entry targets.**

### What T1 and T2 Mean

**T1 range** = Buy zone. The floor (EPS × low P/E × (1 − MoS)) is the deepest discount — crossing below it triggers BUY ZONE. The ceiling (EPS × low P/E) is low-end fair value with no discount. The whole T1 range signals "good to excellent value."

**T2 range** = Optimism zone. The ceiling (EPS × high P/E × (1 − ½ MoS)) is bull-case fair value. Price above T2 ceiling triggers OVERVALUED. In the T2 range, the stock is priced for execution — hold but don't add.

Dashboard status summary:
- **BUY ZONE**: price ≤ T1 floor — maximum discount, full MoS applied, highest conviction
- **WATCH (T1 zone)**: T1 floor < price ≤ T1 ceiling — approaching low-end fair value, consider smaller tranche
- **WATCH (T2 zone)**: T1 ceiling < price ≤ T2 ceiling — fairly valued to optimistic, hold
- **OVERVALUED**: price > T2 ceiling — exceeds bull-case, consider trimming

Example — NVDA "$271–$319 | $320–$354": Below $271 = BUY ZONE (35× EPS, full 15% MoS). $271–$319 = T1 watch zone. $320–$354 = T2 watch zone. Above $354 = OVERVALUED (exceeds 42× EPS with ½ MoS).

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
| `premarket-price-check` | 7:01 AM CT, Mon–Fri | Fetch pre-market prices, update dashboard, check `Position_Tracker.md` exit targets, save briefing, auto-push GitHub |
| `market-close-price-check` | 4:00 PM CT, Mon–Fri (cron `0 16 * * 1-5`) | Fetch closing prices, update dashboard, check `Position_Tracker.md` exit targets, save briefing, auto-push GitHub |
| `weekly-portfolio-review` | 10:05 AM CT, Saturday | Macro scores + event-driven re-analysis (~30–45 min) |
| `quarterly-full-refresh` | 10 AM CT, 1st Sat of Jan/Apr/Jul/Oct | Full 12-step re-analysis all 35 stocks |
| `macro-reassessment` | Manual only | Full macro reassessment when triggered by briefings |

**GitHub auto-push** (added June 23, 2026): Both price-check tasks now automatically call `github_push.py` at the end of each run (PART 6). No manual Terminal push needed after briefings. **Note (July 7, 2026):** this explicit PART 6 call is effectively a backup — a macOS LaunchAgent (installed June 29, see Section 9 "GitHub Push" lessons) already auto-pushes independently whenever `stock_dashboard.html` is saved, from any source. If the explicit PART 6 call ever reports failure from a sandboxed session, check `git log` / `github_push.log` before concluding the push didn't happen — it usually already did.

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

## 7. The 31 Holdings

**Current as of July 11, 2026.** Grouped by category (matches dashboard category filter):

| Category | Tickers |
|---|---|
| Tech/AI | NVDA, MRVL, AVGO, MSFT, GOOGL, HPQ |
| Semiconductors | MU, WDC, SNDK, FSLR, TSM, LEU |
| Healthcare | LLY, NVO |
| Financials | BRK-B |
| Energy | FRVO, HESM, BP, SHEL |
| Utilities | CEG, NEE |
| International ETF | EWY, EWL, AVDE, FENI, SCHF |
| US ETF | VOO, XLU, IAU, REMX, SOXQ |

**Removed June 23, 2026:** AMKR, AMAT, TER, CRWV, SWKS, NXPI, QCOM, CSCO, INTC, LITE  
**Added June 23, 2026:** HESM, CEG, NEE, XLU, IAU, REMX, SOXQ  
**Removed June 29, 2026:** HON (Aerospace spin-off — too much complexity post-HONA split), AMD, HPE, CRUS, TXN, AMZN, PLAB (portfolio simplification)  
**Added June 29, 2026:** BP, SHEL (oil & gas majors — robust financials, high dividends, Energy sector diversification)  
**Added July 11, 2026:** SNDK (SanDisk — pure-play NAND flash spun off from WDC in Feb 2025; was missed when WDC was rebuilt HDD-only at the July 4 quarterly refresh, added back at Patricia's request while setting up the Claude for Excel short-term dashboard project. Uses a provisional normalized-P/E valuation — see Section 5 and § 9 Lessons Learned)

---

## 8. Current Status Snapshot (as of June 29, 2026 — market close)

| Status | Tickers |
|---|---|
| BUY ZONE | FRVO, MSFT, NVDA |
| WATCH | AVDE, BP, BRK-B, CEG, EWL, EWY, FENI, FSLR, GOOGL, HPQ, IAU, MU, NEE, NVO, SCHF, SHEL, XLU |
| OVERVALUED | AVGO, HESM, LEU, LLY, MRVL, REMX, SOXQ, TSM, VOO, WDC, SNDK (added Jul 11, 2026) |

*Status changes whenever prices are updated — check dashboard for current state. This table is a point-in-time snapshot from June 29 and has not been reconciled against every subsequent price move — SNDK's entry is current as of its July 11 addition, but treat the rest of this table as illustrative rather than live.*

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
- **Weekly task was missing save + GitHub steps** (discovered June 28, 2026): The `weekly-portfolio-review` scheduled task had no PART 5 (save_briefing) or PART 6 (GitHub push + present_files). Fixed June 28 — now mirrors the pre-market/market-close task structure. The weekly review .md file type is `WEEKLY-REVIEW`, producing filenames like `YYYY-MM-DD-weekly-review.md`.
- **Weekly task ticker list was stale**: Task prompt listed 38 old tickers (including removed stocks like LITE, INTC, AMAT, etc.) — corrected to current 35 on June 28, 2026.
- **Weekly + quarterly ticker lists went stale again after the June 29 restructuring** (discovered July 7, 2026): Both tasks still listed the pre-restructuring 35-ticker roster (AMD, HON, HPE, TXN, PLAB, CRUS, AMZN included; BP, SHEL missing). Corrected both to the current 30-ticker list. Also fixed quarterly's `s11`-format stock list — it named 6 tickers (WDC, CRUS, HPE, HPQ, HON, MSFT) but 3 of those (CRUS, HPE, HON) no longer exist in the portfolio; only **WDC, HPQ, MSFT** are still active `s11`-format stocks. **Lesson: whenever the portfolio roster changes (Section 7), grep every scheduled task prompt for the old tickers** — ticker lists are hardcoded in task text and don't update themselves.
- **The "first 10 tickers use space format" claim was wrong** (discovered July 7, 2026): Verified directly against the live dashboard — only **FSLR, AVGO, MU** (3 tickers) use `priceResearch: "$X"` (space after colon); all other 27 use `priceResearch:"$X"` (no space). This is not tied to array position and drifts as stocks are added/removed, so weekly/quarterly task prompts were updated to describe the format by ticker name instead of position, and to point at the regex (`key:\s*["\']`) that handles both automatically rather than relying on a count.
- **append_briefing.py uses Mac-side paths and cannot run from bash sandbox**: The `DASHBOARD` path is hardcoded to `/Users/pvegamacbookair/Claude Cowork/stock_dashboard.html`. When running in a manual session from the bash sandbox, update the dashboard BRIEFINGS array directly (as done June 28) rather than calling `save_briefing()` via the sandbox.
- **FMP `technicalIndicators` ignores `from`/`to` date params** (discovered June 30, 2026): The endpoint returns full historical data (~160K chars) regardless of any date filtering. The output file lands in a Mac temp path inaccessible from the bash sandbox. **Workaround for ECL**: Use the Read tool on the output file path with a small limit — the JSON is newest-first, so the first ~2,000 characters contain today's signal. Alternatively, write a Python script that opens the file and prints `json.loads(f.read())[:2]`.

### GitHub Push
- **`github_push.py` must use `--force` and token-in-URL**: Plain `git push origin main` fails when remote has diverged. Always use `git push --force https://PVega007:{token}@github.com/PVega007/stock-dashboard.git main`. The updated script handles this automatically.
- **Stale lock files**: If git crashes mid-run, `.git/index.lock` or `.git/HEAD.lock` may be left behind. The updated `github_push.py` auto-removes them on each run.
- **Sandbox cannot push to GitHub**: The Linux bash sandbox has network restrictions blocking outbound git, and it can't see `github_token.txt` even when the mounted-folder path resolves. Calling `github_push.py` from inside a sandboxed session (e.g. via `mcp__workspace__bash`, or a `subprocess` call issued from that sandbox) will reliably fail with a "No such file or directory: github_token.txt" error. **This is expected and does not mean the dashboard failed to reach GitHub** — see the LaunchAgent bullet immediately below before concluding a push failed.
- **⚠️ There are TWO independent push mechanisms — check the LaunchAgent before reporting a failure (discovered July 7, 2026):** A macOS LaunchAgent (`com.patricia.dashboard-push.plist`, installed June 29, label `com.patricia.dashboard-push`) watches `stock_dashboard.html` via `WatchPaths` and fires `python3 github_push.py` **natively on the Mac** ~30s (its `ThrottleInterval`) after any save to that file — this includes saves made through Read/Write/Edit tools or through a mounted-folder `mcp__workspace__bash` session, since those write to the real file on disk, not a sandbox-only copy. Because the LaunchAgent runs on the Mac, it *does* have access to `github_token.txt` and normally succeeds even when an explicit in-sandbox `github_push.py` call fails. **Before telling Patricia a GitHub push failed, always check both of these on the actual repo (not assumptions):**
  1. `git -C "/Users/pvegamacbookair/Claude Cowork" log --oneline -5 --date=iso --pretty=format:"%h %ad %s"` — look for a same-day "Dashboard update" commit timestamped after your edits.
  2. `tail -30 "/Users/pvegamacbookair/Claude Cowork/github_push.log"` — look for a recent `✅ GitHub Pages updated` line.

  Only report a genuine push failure if **neither** shows a successful push for today. A failed in-sandbox subprocess call, by itself, is not evidence of failure — it's expected behavior. (This exact mistake happened on July 7, 2026: a sandboxed `github_push.py` call failed on the missing token file, was reported to Patricia as "push failed, needs manual push," and it turned out the LaunchAgent had already completed three successful pushes minutes earlier. Patricia's manual run afterward correctly reported "Nothing new to commit.")
- **Restricted PATH in scheduled task environment**: The Claude app's subprocess runs with a minimal PATH that may not include Homebrew's bin directory (`/opt/homebrew/bin` on Apple Silicon, `/usr/local/bin` on Intel). Using bare `"git"` command fails silently if git was installed via Homebrew. The script now uses `find_git()` which checks `/usr/bin/git`, `/opt/homebrew/bin/git`, and `/usr/local/bin/git` explicitly — no PATH dependency.
- **Same restricted-PATH issue applies to `node`** (added July 11, 2026, when `export_stocks.js` was wired in): `github_push.py` now uses `find_node()`, checking `/opt/homebrew/bin/node`, `/usr/local/bin/node`, `/usr/bin/node` explicitly before falling back to PATH. Unlike `find_git()`, a missing node is **non-fatal** — the export step is skipped with a warning and the dashboard push still proceeds, so a node PATH issue on Patricia's Mac won't block the core dashboard/briefing publish.
- **Regex-based JS parsing breaks on nested brackets/quotes in the STOCKS array** (discovered July 11, 2026 building `export_stocks.js`): An early version tried to isolate `const STOCKS = [...]` by manually re-bracketing a substring (stripping the `const STOCKS = ` prefix, finding the last `]`, wrapping in parens) — this repeatedly hit `SyntaxError: Unexpected token ';'` because `redFlags` arrays and note strings contain their own brackets/quotes that confuse naive boundary-finding. Fix: execute the dashboard's own `const STOCKS = [...];` / `const PE_DATA = {...};` statements **verbatim** (unmodified) inside a Node `vm` sandbox context, then read the resulting variable off the sandbox object afterward. Cutting at the *next* `const <NAME> = ` marker (which is exactly where the dashboard's own source already ends the prior statement) is far more robust than trying to guess where an array/object literal closes.

### Bear Framework / Dashboard JS
- **`INVESTMENT_PARAMS` JS constant must be kept in sync with `investment_parameters.json`**: The browser cannot read files from disk. When the JSON file is updated (new stock, revised bear_discount, etc.), the embedded `INVESTMENT_PARAMS` constant in `stock_dashboard.html` must also be updated manually.
- **Bear mode alert fires only when `activeRegime === 'BEAR_MARKET'`**: Toggling Bear mode off removes all row highlights and badges — this is correct behavior. In Bull mode, the dashboard looks identical to before the feature was added.
- **`parseT1Floor()` strips commas**: entryTarget strings like `"$1,100–$1,260"` must have commas removed before regex matching. The function handles this.
- **MU status changed to WATCH** (June 23, 2026): Price $1,211.38 is above T1 ceiling ($1,100) and below T2 ceiling ($1,260) → WATCH, not BUY ZONE. Mid-cycle EPS remains ~$50 for target calculations.

### EPS Accuracy / Entry Target Sanity Check

**Standard validation — run at every quarterly refresh:**
Two independent calibration checks applied together catch different failure modes:

1. **T2 ceiling vs 52-week ATH**: flag if T2 > 130% of ATH for non-growth stocks, or > 150% for any stock. Catches EPS inputs pulled from too far in the future or P/E multiples set too aggressively. Exception: growth stocks with confirmed analyst consensus EPS (e.g. NVDA) may exceed 150% if the stock has sold off hard — check EPS first.
2. **T2 ceiling vs analyst 1-year price target**: flag if T2 > 150% of analyst consensus target. Catches cases where our bull-case ceiling is disconnected from professional fundamentals. Exceptions by design: cyclicals using mid-cycle normalized EPS (e.g. MU) will naturally exceed 150% vs near-term analyst targets — this is intentional.

**Interpretation guide:**
- Flag on both checks → likely a real EPS or P/E error → fix immediately
- Flag on ATH only → check whether EPS is confirmed by analyst consensus; if yes, the ATH comparison is a false positive (stock has sold off)
- Flag on analyst target only → may be thesis disagreement (we're more optimistic than consensus) or near-term pessimism on a cyclical — monitor, revisit at quarterly
- LLY corrected June 23 (high_pe 50→35): ATH-implied P/E was ~34.5×; 50× was set during peak GLP-1 hype, not current competitive reality

- **52-week high vs T2 ceiling is a useful sanity check**: T2 ceiling >125% of 52-week high is a flag worth investigating — it usually means the EPS input was pulled from too far in the future or is simply wrong.
- **NVDA's T2 ceiling above ATH is NOT an error**: NVDA EPS $9.11 is within FY2027 analyst consensus ($8.96–$9.34). The stock has sold off from where the targets were set. T2 ceiling above 52-wk high is correct for a deep-correction scenario.
- **HPQ used EPS $4.26 instead of actual $3.00 consensus**: Source of error was using a too-optimistic forward EPS. Always cross-check implied EPS (back-calculate from T1 floor) against company guidance.
- **LLY used EPS $43.44 instead of FY2026 consensus ~$37**: Likely pulled from 2028+ projections. Use NTM forward EPS, not multi-year-out forecasts, unless explicitly documented.
- **FSLR "mid-cycle" must not be confused with peak-cycle**: 2026 consensus $17–18 is appropriate; the original $25 EPS represented analyst high-end peak estimates, not mid-cycle.
- **VOO index P/E methodology is inherently unstable**: Using price/current-P/E to derive EPS and then applying a different P/E produces circular results. Switched to price-support approach (52-week low + % corrections from ATH).

### Narrative Logic Anti-Patterns

These are logic inversions that produce misleading prose even when the status label is correct.

**The BUY ZONE direction rule:** BUY ZONE means the price has already FALLEN into or below entry territory. Language must reflect that.
- ✅ "price has fallen X% below T1 floor $Y — entry territory reached"
- ✅ "MSFT at $373 is 22% below T1 floor $476, deep in the buy zone"
- ❌ "price still needs to recover to reach entry territory" (backwards — that's OVERVALUED language)
- ❌ "wait for pullback to buy" (for a BUY ZONE stock — it has already pulled back)

**The OVERVALUED direction rule:** OVERVALUED means price has risen above T2 ceiling. Wait for it to fall, not rise.
- ✅ "above T2 ceiling — wait for pullback to $X–$Y entry zone"
- ❌ "entry confirmed" (for an OVERVALUED stock)

**The WATCH zone rule:** Be specific about which zone (T1 vs T2):
- WATCH in T1 zone (price between T1 floor and T1 ceiling): approaching fair value, consider small tranche
- WATCH in T2 zone (price between T1 ceiling and T2 ceiling): fairly valued to optimistic, hold but don't add

**Root cause discovered June 28, 2026:** Weekly briefing prose for MSFT (BUY ZONE) wrote "price still has significant recovery needed to reach entry territory" — the opposite of correct. This was stale narrative language written when MSFT was OVERVALUED, never updated when status changed to BUY ZONE.

**Where this QC is embedded:**
- All briefing tasks (pre-market, market-close, weekly, quarterly): NARRATIVE QC checklist in PART 4 / STEP 5 output section
- Applies to all prose: briefing text, movers commentary, status change notes

---

### BP and SHEL Valuation Notes

- **BP**: GAAP EPS is near-zero (impairments). Use underlying/normalized EPS ~$3.50 for P/E calc. FCF/share ~$4.41 TTM as cross-check. Never use GAAP EPS for BP entry target calculations.
- **SHEL**: EPS is clean and consistent ($5.06–$6.02 over 3 years). Use normalized mid-cycle ~$6.00. EPS is in USD (NYSE ADR).
- Both are ADRs — international stocks with GBP/USD currency translation built into the ADR price. No additional conversion needed.
- Both use `metric:"normalized_pe"` in INVESTMENT_PARAMS and investment_parameters.json.

---

### Steps Format vs Verdict Format (s11 vs verdict field)

Six stocks use `steps:{s0:..., s11:...}` format instead of a standalone `verdict:` field: **WDC, CRUS, HPE, HPQ, HON, MSFT**.

The verdict/status QC audit script only matches `verdict:` — it misses `s11:` stocks entirely. The correct combined audit checks both.

**Updated QC script covering all 35 stocks:**

```python
import re

with open('/Users/pvegamacbookair/Claude Cowork/stock_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

stocks_start = html.find('const STOCKS = [')
stocks_end = html.find('const FRAMEWORK_STEPS')
stocks_html = html[stocks_start:stocks_end]

entry_starts = [m.start() for m in re.finditer(r'\{\s*ticker\s*:\s*["\']', stocks_html)]
entry_starts.append(len(stocks_html))

mismatches = []
checked = 0
for i, start in enumerate(entry_starts[:-1]):
    end = entry_starts[i+1]
    entry = stocks_html[start:end]
    ticker_m = re.search(r'ticker\s*:\s*["\'](\w[\w-]*)["\']', entry)
    if not ticker_m or 'sector' not in entry[:200]:
        continue
    ticker = ticker_m.group(1)
    status_m = re.search(r'status\s*:\s*["\']([^"\']+)["\']', entry)
    if not status_m:
        continue
    status = status_m.group(1)
    # Check both verdict: and s11: formats
    verdict_m = re.search(r'(?:verdict|s11)\s*:\s*["\']([^"\']{0,80})', entry)
    if not verdict_m:
        continue
    verdict_open = verdict_m.group(1).lstrip('VERDICT: ')
    checked += 1
    if not verdict_open.startswith(status):
        mismatches.append((ticker, status, verdict_open))

if mismatches:
    print(f"❌ {len(mismatches)} mismatches:")
    for t, s, v in mismatches:
        print(f"  {t}: status='{s}' | opens: '{v[:70]}'")
else:
    print(f"✅ All {checked} stocks clean.")
```

**June 28, 2026:** HPE, HPQ, HON had s11 mismatches (missed by first audit). Fixed. MSFT s11 label was correct but had stale price references ($411.76, $588 ceiling) — updated to current ($372.97, $610 T2 ceiling).

**Dashboard JS bug (June 28, 2026):** The `buildDetailHtml()` function uses `const st = stock.steps || stock`, so for steps-format stocks `st = stock.steps`. The verdict render line `verdictBoxHtml(stock.status, st.verdict)` was reading `stock.steps.verdict` (undefined) instead of `stock.steps.s11`. Fixed to: `verdictBoxHtml(stock.status, st.verdict || st.s11 || '')`. This affected all 6 steps-format stocks (WDC, CRUS, HPE, HPQ, HON, MSFT) — they all showed "undefined" in the Verdict panel.

---

### Dashboard Consistency / QC

**Verdict/Status rule (critical):** Every stock's `verdict` field (or `s11` for steps-format stocks) must open with the same status keyword as its `status` field — exactly `BUY ZONE`, `WATCH`, or `OVERVALUED`. A verdict that says "WATCH — …" while `status:"BUY ZONE"` is a contradiction visible to Patricia in the detail panel.

**Root cause:** Verdicts are written at a point in time and become stale when prices move the stock across a status boundary. The `status` field is updated programmatically; the `verdict` text is not.

**When this happens:** Any time a stock's status changes (price update crosses T1 floor or T2 ceiling), the verdict opening must also be updated.

**Standard audit script** (run after any session that changes status fields, and as part of quarterly refresh QC gate):

```python
import re

with open('/Users/pvegamacbookair/Claude Cowork/stock_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

pat = r'ticker:\s*["\'](\w[\w-]*)["\'].*?status:\s*["\']([^"\']+)["\'].*?verdict:\s*["\']([^"\']{0,80})'
matches = re.findall(pat, html, re.DOTALL)

mismatches = []
for ticker, status, verdict_open in matches:
    if not verdict_open.startswith(status):
        mismatches.append((ticker, status, verdict_open))

if mismatches:
    print(f"❌ {len(mismatches)} verdict/status mismatches:")
    for t, s, v in mismatches:
        print(f"  {t}: status='{s}' | verdict opens: '{v[:70]}'")
else:
    print(f"✅ All {len(matches)} verdict labels match status — clean.")
```

**Fix format:** Replace the verdict's opening label + first price sentence with: `"[STATUS] — at $[price], [ticker] is [brief current context, e.g. 'in the T2 zone ($X–$Y)' or 'above T2 ceiling $X']. [rest of existing narrative]"`

**Where QC is embedded:**
- `quarterly-full-refresh`: STEP 3B — full audit of all 35 stocks, required before STEP 4
- `weekly-portfolio-review`: PART 2B — scoped to stocks updated that run only

**June 28, 2026:** 12 stocks had verdict/status mismatches corrected (FSLR, PLAB, AVGO, TXN, TSM, LEU, LLY, BRK-B, GOOGL, AMZN, VOO, REMX). All 35 stocks now pass the audit.

**Stale narrative field rule (found July 11, 2026 — deeper than verdict/status):** The verdict/status check above only catches a mismatched opening keyword. It does NOT catch a subtler problem: a stock's `valuation`, `entry`, `bullCase`, `bearCase`, `financial`, and `summary` fields can each independently go stale after a stock re-rates hard, even while `verdict` itself opens with the correct status keyword and passes the audit above.

**What happened to MU:** Micron ran up roughly 10x over the course of 2026 (HBM supercycle). `priceResearch`, `entryTarget`, `status`, and `verdict` were all kept current through that run. But five other fields — `summary`, `financial`, `valuation`, `entry`, `bullCase`, `bearCase` — were never rewritten and still referenced a pre-rally price/EPS scale from when MU traded in the $75–150 range: `valuation` modeled a "trough" at $450–675 using a 15x multiple on $30–45 EPS, `entry` said "entry may be justified at $75–85," `bullCase` capped upside at "$150+," `bearCase` floored the stock at "$60–80." Every one of these numbers was 5–10x below the then-current `entryTarget` grid ($880–$1,100–$1,260) and `verdict` text, an internal contradiction fully visible to Patricia (and to Claude for Excel, which caught it independently on July 11, 2026 while reviewing the GitHub export for a separate project) in the detail panel. Root cause: these fields get written once during a full 12-step re-analysis and then are only touched again during another full re-analysis (quarterly refresh) or an ad hoc reason to open that specific stock's block — unlike `priceResearch`/`status`/`verdict`, nothing in the daily/weekly pipeline ever rewrites them, so a stock that re-rates fast between quarterly refreshes can carry stale scenario pricing in these fields indefinitely.

**Fix applied (July 11, 2026):** Rewrote all five MU fields to reference the current v3 grid ($880 T1 floor / $1,100 T1 ceiling / $1,260 T2 ceiling) and the $528 Bear Floor instead of the stale ad hoc 15x-multiple trough math, while preserving the legitimate analytical point (through-cycle EPS risk, 2022–2023 precedent) each field was making.

**Stale-narrative scan** (heuristic — flags $ ranges or "$X+" figures inside `valuation`/`entry`/`bullCase`/`bearCase`/`summary` that are less than half the stock's Bear Floor, or half its T1 floor if no bear_discount is set; expect some false positives on legitimate forward-EPS or per-unit figures like NVDA's "$50-100B TAM" or CEG's "$70-80/MWh" — eyeball each hit before editing):

```python
import re, json

with open('/Users/pvegamacbookair/Claude Cowork/stock_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()
with open('/Users/pvegamacbookair/Claude Cowork/investment_parameters.json', 'r', encoding='utf-8') as f:
    params = json.load(f)['holdings']

stocks_start = html.find('const STOCKS = [')
stocks_end = html.find('const FRAMEWORK_STEPS')
stocks_html = html[stocks_start:stocks_end]
entry_starts = [m.start() for m in re.finditer(r'\{\s*ticker\s*:\s*["\']', stocks_html)]
entry_starts.append(len(stocks_html))

def parse_money(s): return float(s.replace('$','').replace(',',''))
range_pat = re.compile(r'\$([\d,]+(?:\.\d+)?)\s*[–—-]\s*\$?([\d,]+(?:\.\d+)?)')
single_pat = re.compile(r'\$([\d,]+(?:\.\d+)?)\+')

seen, flags = set(), []
for i, start in enumerate(entry_starts[:-1]):
    end = entry_starts[i+1]
    entry = stocks_html[start:end]
    ticker_m = re.search(r'ticker\s*:\s*["\'](\w[\w-]*)["\']', entry)
    if not ticker_m or 'sector' not in entry[:200]: continue
    ticker = ticker_m.group(1)
    et_m = re.search(r'entryTarget:\s*["\']([^"\']+)', entry)
    if not et_m or ticker in seen: continue
    seen.add(ticker)
    nums = re.findall(r'\$([\d,]+)', et_m.group(1))
    if len(nums) < 3: continue
    t1f = parse_money('$'+nums[0])
    bear_discount = params.get(ticker, {}).get('bear_discount')
    ref = round(t1f*(1-bear_discount)) if bear_discount else t1f
    for field in ['valuation', 'entry', 'bullCase', 'bearCase', 'summary']:
        fm = re.search(rf'{field}\s*:\s*["\']((?:[^"\\]|\\.)*)["\']', entry)
        if not fm: continue
        text = fm.group(1)
        for m in range_pat.finditer(text):
            lo, hi = parse_money('$'+m.group(1)), parse_money('$'+m.group(2))
            if lo >= 10 and hi < ref*0.5:
                flags.append((ticker, field, f"${lo:.0f}-${hi:.0f}"))
        for m in single_pat.finditer(text):
            v = parse_money('$'+m.group(1))
            if v < ref*0.5:
                flags.append((ticker, field, f"${v:.0f}+"))

for t, field, val in flags:
    print(f"{t} [{field}]: {val} — check against T1 floor/Bear Floor")
```

Run this at every quarterly refresh (in addition to, not instead of, the verdict/status check above) — any stock that re-rates 3x+ between quarterly refreshes is a candidate for this exact drift.

### Authoritative Sources Hierarchy

Always prefer sources in this order. Briefings must cite source + date for every market-moving claim.

**Tier 1 — Official/Primary (highest authority — use first for macro data):**
- **bls.gov**: CPI, PPI, JOLTS, Unemployment — always use for labor/inflation data
- **bea.gov**: GDP, PCE, Personal Income — always use for growth/spending data
- **federalreserve.gov**: FOMC decisions, minutes, economic projections, Beige Book
- **ismworld.org**: ISM Manufacturing PMI, ISM Services PMI, and their Employment/Prices/New Orders sub-indices — added July 7, 2026 after the June ISM Services Employment Index (released Jul 6) was initially missed. Use for all ISM data, not a media summary.
- **SEC EDGAR (sec.gov)**: 10-K, 10-Q, 8-K, proxy filings — primary for company disclosures
- **Company Investor Relations pages**: Earnings press releases, official guidance

**Tier 2 — High reliability (default for market and company data):**
- **FMP MCP connector**: Real-time prices, analyst consensus, earnings, financial statements, news
- **stockanalysis.com**: Clean quarterly/annual financials
- **FMP earningsTranscript**: CEO/CFO direct statements from earnings calls
- **WSJ, Financial Times, Reuters, Bloomberg**: Tier-1 financial journalism — always verify date ✓

**Tier 3 — Use with caution (verify date; distinguish news from opinion):**
- CNBC, TheStreet, Benzinga, MarketWatch, Seeking Alpha

**Rules enforced in all tasks:**
1. Macro data (CPI, PCE, GDP, FOMC): cite the primary .gov/Fed source, not a media summary of it
2. Analyst targets: use FMP `price-target-consensus`; note analyst count (4-analyst consensus ≠ 56-analyst consensus)
3. Never use a source without a confirmed publication date for any market-moving claim
4. Web search results without a confirmed date: label as "[date unverified — treat with caution]"
5. Do not use GuruFocus, Simply Wall St, or similar for P/E ranges — they use different methodologies than ours
6. **Breaking / "happening today" claims sourced from a single live-blog-style headline must be corroborated by a second independent source before being stated as confirmed fact** (added July 7, 2026 — see Lessons Learned). If only one source can be found, label it "[single-source — treat with caution]" and describe the specific claim rather than presenting it as a confirmed fact/date.
7. **Every scan (daily, weekly, quarterly, reassessment) must include a generic "economic data released today/this week [date]" catch-all WebSearch query**, not just the pre-named theme queries (Fed, tariffs, oil, etc.) — named-theme-only queries miss releases outside the pre-picked topics. `MACRO_CALENDAR` in the dashboard is manually maintained and goes stale between weekly refreshes, so it cannot be the only detection mechanism.
8. **Given the portfolio's concentration in AI/semiconductors (NVDA, MRVL, AVGO, TSM, MU, WDC, SOXQ — 7 of 30 holdings), every scan must also include a dedicated AI/semiconductor competitive-landscape query** (competitor moves, export controls, China chip self-sufficiency — e.g. Samsung, SK Hynix, ASML, Huawei, DeepSeek, OpenAI). Ticker-specific FMP news search only catches stories tied to dashboard tickers directly; structural industry news about non-dashboard entities (e.g. a competitor or a private company) needs its own search.

### Research / Scan Coverage Gaps (discovered July 7, 2026)

Patricia flagged that the day's briefings had missed relevant news despite a full pre-market scan and macro reassessment. Root-cause review found three distinct gaps, all fixed the same day:

- **`MACRO_CALENDAR` is a static, hand-maintained array and had zero entries past June 30, 2026.** Every task's "check today's calendar" step reads only from that array, so any release in July was structurally invisible regardless of how good the WebSearch step was — this is why the July 2 jobs report and July 6 ISM Services report weren't flagged. Fix: `weekly-portfolio-review` PART 3 now researches the next 2-3 weeks of confirmed releases (BLS/ISM/Fed schedules) and *writes* new entries into `MACRO_CALENDAR`, not just reads it — the array should now never drift more than ~1 week stale, assuming the weekly task runs on schedule. Backfilled July 2 (jobs report), July 6 (ISM Services incl. Employment Index), July 14 (CPI), and July 29 (FOMC) as of July 7, 2026.
- **WebSearch queries in every task were narrow, pre-named themes** (Fed decision, tariffs, oil price, dollar index, etc.) with no generic catch-all — a release outside the pre-picked topics (like ISM Services) simply wasn't searched for. Fix: added a mandatory `"economic data released today/this week [date]"` query to all 5 tasks (see Authoritative Sources Hierarchy, Rule 7).
- **News scanning was ticker-driven only** (FMP `search-stock-news` against the 30 dashboard tickers) — this missed the DeepSeek-developing-its-own-AI-chip story (Reuters, Jul 7) entirely, since DeepSeek isn't a dashboard ticker, even though it's structurally relevant to the whole AI/semi complex (NVDA, MRVL, AVGO, TSM, MU). Fix: added a mandatory AI/semiconductor competitive-landscape WebSearch query to all 5 tasks (see Rule 8).
- **Single-source "happening today" claims were stated as fact without corroboration**: the July 7 pre-market briefing said SK Hynix "made its Nasdaq ADR debut today," sourced from a single 247wallst live-blog headline ("...11 minutes ago"). The actual listing is July 10 (confirmed via CNBC/Fortune/Bloomberg). Fix: added Rule 6 — breaking claims from a single live-blog-style source must be corroborated by a second source before being stated as confirmed fact, otherwise label `"[single-source — treat with caution]"`.

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
| github_push.py updated: find_git() added to fix restricted PATH in scheduled task environment | June 26, 2026 |
| ECL activated in both pre-market and market-close task prompts (FMP technicalIndicators confirmed on Starter plan) | June 26, 2026 |
| ⚠️ FMP technicalIndicators ignores from/to date params — returns full history (~160K chars), exceeds context limit. Workaround: Read output file first 2,000 chars (newest-first) or use Python to slice file | June 30, 2026 |
| Scheduled tasks updated: auto GitHub push + downloadable briefing card after every run | June 23, 2026 |
| Market close briefing run: global AI selloff, MU -13.2%, 3 status changes | June 23, 2026 |
| Status changes (close): MU→WATCH, LEU→OVERVALUED, VOO→WATCH | June 23, 2026 |
| EPS audit: 4 stocks corrected (HPQ, LLY, FSLR, VOO) | June 23, 2026 |
| HPQ entry corrected: EPS $4.26→$3.00; "$30–$45"→"$21–$31"; BUY ZONE→WATCH | June 23, 2026 |
| LLY entry corrected: EPS $43.44→$37; "$923–$2,008"→"$786–$1,711"; stays WATCH | June 23, 2026 |
| LLY high_pe revised: 50×→35× (ATH-implied ~34.5×; GLP-1 competition); target "$786–$1,199" | June 23, 2026 |
| FSLR entry corrected: EPS $24.91→$18 mid-cycle; "$286–$408"→"$207–$295"; BUY ZONE→WATCH | June 23, 2026 |
| VOO methodology: index_pe→price_support; "$590–$876"→"$545–$640"; WATCH→OVERVALUED | June 23, 2026 |
| NVDA confirmed correct: $9.11 EPS within FY2027 consensus $8.96–$9.34; no change | June 23, 2026 |
| PCE May 2026 + GDP Q1 Final released | June 25, 2026 |
| PCE all-items 4.1% YoY (3-year high, in-line); GDP Q1 final +2.1% (beat); no rate cut signal | June 25, 2026 |
| MU Q3 FY2026 blowout: EPS $25.11 vs $21.39 est, rev $41.46B vs $35.84B; HBM booked through 2027 | June 24, 2026 |
| WDC -13.2%: Fox Advisors downgrade + 6% share dilution (convertible note exchange) | June 26, 2026 |
| LLY WATCH → OVERVALUED: Medicare GLP-1 Bridge (July 1, ~20M patients $50/mo) + EMA Jaypirca CLL + Leerink PT $1,232 | June 26, 2026 |
| CRUS OVERVALUED → WATCH: semi sector selloff pulled price below T2 ceiling $152 | June 26, 2026 |
| MU macro score raised 3 → 4: Q3 FY2026 confirms HBM supercycle as structural | June 28, 2026 |
| weekly-portfolio-review task fixed: PART 5 (save_briefing) + PART 6 (GitHub push + present_files) added; ticker list corrected 38→35 | June 28, 2026 |
| Verdict/status consistency audit run: 12 mismatches found and fixed (FSLR, PLAB, AVGO, TXN, TSM, LEU, LLY, BRK-B, GOOGL, AMZN, VOO, REMX) | June 28, 2026 |
| QC gate added to quarterly-full-refresh (STEP 3B) and weekly-portfolio-review (PART 2B) | June 28, 2026 |
| quarterly-full-refresh task updated: ticker list corrected 38→35, v3 methodology referenced, save_briefing + GitHub push added (STEP 6–7) | June 28, 2026 |
| s11-format stocks (WDC, CRUS, HPE, HPQ, HON, MSFT) discovered — missed by first QC audit; HPE/HPQ/HON s11 mismatches fixed | June 28, 2026 |
| MSFT s11 stale price refs updated ($411.76→$372.97, $588 ceiling→$610); narrative logic QC added to all 4 tasks | June 28, 2026 |
| Authoritative sources hierarchy documented in CLAUDE.md and embedded in all task prompts | June 28, 2026 |
| Dashboard JS bug fixed: `verdictBoxHtml(stock.status, st.verdict)` → `st.verdict \|\| st.s11 \|\| ''`; all 6 steps-format stocks were rendering "undefined" in Verdict panel | June 28, 2026 |
| Full 35-stock audit run: all clean ✅ | June 28, 2026 |
| macOS LaunchAgent installed: auto-pushes stock_dashboard.html to GitHub on every save (no manual Terminal step needed) | June 29, 2026 |
| FMP connector set to "Always allow" — no more per-session approval prompts | June 29, 2026 |
| Portfolio restructured 35 → 30: removed HON (spin-off complexity), AMD, HPE, CRUS, TXN, AMZN, PLAB | June 29, 2026 |
| Added BP ($37.35) and SHEL ($76.89): integrated oil & gas majors, both WATCH. Energy category now has 4 stocks | June 29, 2026 |
| BP methodology: Normalized P/E 8–12×, underlying EPS ~$3.50, MoS 20%, bear_discount 35%. T1: $22–$28, T2: $29–$38, Bear: $14 | June 29, 2026 |
| SHEL methodology: Normalized P/E 10–16×, mid-cycle EPS ~$6.00, MoS 15%, bear_discount 30%. T1: $51–$60, T2: $61–$89, Bear: $36 | June 29, 2026 |
| HESM verdict updated: WATCH → OVERVALUED (price $38.30 crossed T2 ceiling $38) | June 29, 2026 |
| QC audit run: all 30 stocks clean ✅ | June 29, 2026 |
| WDC dashboard updated: price $651.88, market cap $225B, analyst consensus target $533/$575 (Bear/Bull); Cantor Fitzgerald PT $900; ⚠️ entry targets flagged as stale (set for pre-SanDisk-spin combined NAND+HDD business); full HDD-only recalculation deferred to July 5 quarterly refresh | June 29, 2026 |
| Scheduled tasks updated: premarket-price-check and market-close-price-check ticker lists corrected 35→30 (added BP, SHEL; removed HON, AMD, HPE, CRUS, TXN, AMZN, PLAB); quarterly-full-refresh description updated to 30 stocks | June 29, 2026 |
| Next quarterly full refresh | First Saturday of July 2026 |
| Upcoming: JOLTS | June 30, 2026 |
| Pre-market briefing run: global memory-chip selloff (Samsung earnings) + Iran missile strikes on tankers in Strait of Hormuz — 🔴 REASSESS NOW; SOXQ OVERVALUED→WATCH, BP WATCH→OVERVALUED | July 7, 2026 |
| GitHub push confusion resolved + documented: confirmed the June 29 LaunchAgent auto-pushes independently of any in-sandbox `github_push.py` call; added explicit "check git log / github_push.log before reporting a push failure" lesson to CLAUDE.md Section 9 and to the GitHub-push step of all 4 relevant scheduled tasks (premarket-price-check, market-close-price-check, weekly-portfolio-review, quarterly-full-refresh) | July 7, 2026 |
| weekly-portfolio-review + quarterly-full-refresh cleaned up: ticker lists corrected 35→30 (removed AMD/HON/HPE/TXN/PLAB/CRUS/AMZN, added BP/SHEL); quarterly's s11-format list corrected to WDC/HPQ/MSFT only (CRUS/HPE/HON removed); "first 10 tickers use space format" claim corrected to the verified actual split (FSLR, AVGO, MU only) | July 7, 2026 |
| Research/scan coverage gaps found + fixed: MACRO_CALENDAR was stale past June 30 (now has a weekly auto-refresh step + backfilled through Jul 29 FOMC); added mandatory "economic data today/this week" catch-all + AI/semiconductor competitive-landscape queries to all 5 scheduled tasks; added single-source corroboration rule after a 247wallst live-blog headline caused an incorrect "SK Hynix debuts today" claim (actual listing: Jul 10); ismworld.org added to Tier 1 sources | July 7, 2026 |
| Macro reassessment run (US-Iran ceasefire declared "over," oil spiked, AI/semi selloff deepened): no macro score changes (read as escalation of an already-flagged tail risk, not new fundamentals); 5 macroContext narratives updated (AVGO, MU, EWY, BP, SHEL) | July 8, 2026 |
| `Position_Tracker.md` created — tracks Patricia's personal open tranches and exit targets, separate from the dashboard's general valuation framework; `premarket-price-check` and `market-close-price-check` updated with a lightweight PART 1C step that flags when a tracked ticker's price reaches or nears its exit target. First tracked position: AVGO tranche (entry $422.91) — GTC limit sell set at $410.75 | July 9, 2026 |
| External data exports added (`export_stocks.js` → `stocks.json`/`stocks.csv`/`stocks_full.json`) for Claude for Excel to pull from the public GitHub repo — built for Patricia's short-term-lens Excel dashboard project; wired into `github_push.py` (auto-regenerates before every push) and both price-check scheduled tasks; `investment_parameters.json` and `CLAUDE.md` also now pushed publicly for the first time (were tracked/referenced but never actually staged). `Position_Tracker.md` explicitly excluded — contains account/tax detail not approved for public export. See § 4B. | July 11, 2026 |
| SNDK added as 31st holding (see § 7); MU's `summary`/`financial`/`valuation`/`entry`/`bullCase`/`bearCase` fields found and fixed — carried pre-rally (~10x ago) price/EPS scenario numbers ($75–85 entry, $450–675 trough, $150+ bull, $60–80 bear) despite `entryTarget`/`status`/`verdict` all being current; caught by Claude for Excel independently while reviewing the GitHub export for the short-term dashboard project. New stale-narrative scan added to § "Dashboard Consistency / QC" — checks fields the verdict/status audit doesn't reach. | July 11, 2026 |

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
