"""
AI boom dashboard (Streamlit): how much AI investment adds to the economy, whether it
can last, where it is heading, and what it is doing to the labor market.

Pages
  1. Real economy      NIPA investment lines (Tables 5.3.5/5.3.6), contributions to real GDP
                       growth, Fed-style buildout proxy net of computer imports, data center and
                       power construction (Census C30), semiconductor output, productivity
  2. Firm level        Hyperscaler capex vs operating cash flow, capex guidance, bond issuance
  3. Financial markets AI stocks (daily moves), IG credit spreads, hyperscaler spreads and
                       ratings, token prices
  4. Leading signals   Nvidia, TSMC, Korean chip exports, memory prices, AI-lab revenue,
                       token volume, business AI adoption
  5. Compute prices    GPU rental prices by chip: B300 record (Compute Desk), Silicon Data
                       neocloud/hyperscaler indices, Ornn daily index (live, public API)
  6. Labor market      Young-worker and tech unemployment/employment, software postings,
                       AI-attributed job cuts

Live data: FRED (BEA, Census, Fed, BLS, ICE BofA, Indeed), Our World in Data (data center
construction), Ornn GPU rental index (public API, trailing 3 months), Financial Modeling Prep if you add a key (otherwise Yahoo Finance via yfinance).
Figures without a free feed live in ai_boom_reference.py, each with its source.

Run:   py -m streamlit run ai_boom_dashboard.py
Needs: pip install streamlit altair pandas requests yfinance
"""

import io
import itertools
import os
import re
import time
from datetime import date

import altair as alt
import pandas as pd
import requests
import streamlit as st

import ai_boom_reference as ref
import store

# ---------------------------------------------------------------------------
# Series definitions (FRED IDs)
# ---------------------------------------------------------------------------
# NIPA Table 5.3.5 (nominal, $B SAAR) - the AI-proxy investment lines
NIPA_NOMINAL = {
    "A679RC1Q027SBEA": "Info-processing equipment + software",
    "Y034RC1Q027SBEA": "Info-processing equipment",
    "B935RC1Q027SBEA": "Computers & peripherals",
    "B985RC1Q027SBEA": "Software",
    "Y006RC1Q027SBEA": "R&D",
}
# NIPA Table 5.3.1 (real, % change at annual rate)
NIPA_REAL_GROWTH = {
    "A679RL1Q225SBEA": "Info-processing equipment + software",
    "Y034RL1Q225SBEA": "Info-processing equipment",
    "B935RL1Q225SBEA": "Computers & peripherals",
    "B985RL1Q225SBEA": "Software",
    "Y006RL1Q225SBEA": "R&D",
}
# NIPA Table 1.5.2-style contributions to % change in real GDP (pp at annual rate)
NIPA_CONTRIB = {
    "Y034RY2Q224SBEA": "Info-processing equipment",
    "B935RY2Q224SBEA": "Computers & peripherals",
    "B985RY2Q224SBEA": "Software",
    "Y006RY2Q224SBEA": "R&D",
}
# Real (chained 2017 $) levels used for the import offset and the year-over-year proxy
NIPA_REAL_LEVELS = {
    "B935RX1Q020SBEA": "Computers & peripherals (real)",
    "B985RX1Q020SBEA": "Software (real)",
    "Y006RX1Q020SBEA": "R&D (real)",
    "B852RX1Q020SBEA": "Imports: computers, peripherals & parts (real)",
    "B850RX1Q020SBEA": "Exports: computers, peripherals & parts (real)",
    "GDPC1": "Real GDP",
}
TRADE_NOMINAL = {
    "B852RC1Q027SBEA": "Imports: computers, peripherals & parts",
    "B850RC1Q027SBEA": "Exports: computers, peripherals & parts",
    "GDP": "Nominal GDP",
}
GDP_GROWTH = {"A191RL1Q225SBEA": "Real GDP growth"}
# Real nonresidential fixed investment and its three parts: BEA chain-type quantity indexes (2017=100,
# back to 1947; FRED's chained-dollar levels only start in 2007) and nominal levels for spending shares
NONRES_QTY = {
    "A008RA3Q086SBEA": "Nonresidential fixed investment",
    "B009RA3Q086SBEA": "Structures",
    "Y033RA3Q086SBEA": "Equipment",
    "Y001RA3Q086SBEA": "Intellectual property products",
}
NONRES_NOM = {
    "B009RC1Q027SBEA": "Structures (nominal)",
    "Y033RC1Q027SBEA": "Equipment (nominal)",
    "Y001RC1Q027SBEA": "Intellectual property products (nominal)",
}
NONRES_IDS = tuple([*NONRES_QTY, *NONRES_NOM])
RESIDUAL = "Chain-weighting residual"
MONTHLY_REAL = {
    "PRPWRCONS": "Private power construction",            # Census C30, $M SAAR
    "IPG3344S": "Industrial production: semiconductors",  # Fed G.17, 2017=100
}
PRODUCTIVITY = {"PRS85006092": "Nonfarm business labor productivity"}
REAL_ECON_IDS = tuple(dict.fromkeys([*NIPA_NOMINAL, *NIPA_REAL_GROWTH, *NIPA_CONTRIB, *NIPA_REAL_LEVELS,
                                     *TRADE_NOMINAL, *GDP_GROWTH, *MONTHLY_REAL, *PRODUCTIVITY]))

CREDIT = {
    "BAMLC0A2CAA": "AA corporate OAS",
    "BAMLC0A4CBBB": "BBB corporate OAS",
    "BAMLH0A0HYM2": "High-yield OAS",
}
TREASURY = {   # constant-maturity Treasury yields, % (for each bond's spread over Treasuries)
    "DGS1": 1, "DGS2": 2, "DGS3": 3, "DGS5": 5, "DGS7": 7, "DGS10": 10, "DGS20": 20, "DGS30": 30,
}
LABOR = {
    "UNRATE": "Unemployment rate",
    "LNS14024887": "Unemployment rate, age 16-24",
    "CES6054150001": "Computer systems design employment",
    "CES5051800001": "Data processing & hosting employment",
    "USINFO": "Information sector employment",
    "IHLIDXUSTPSOFTDEVE": "Software development postings (Indeed)",
}
SERIES_NAMES = {**NIPA_NOMINAL, **{k: v + " (real growth)" for k, v in NIPA_REAL_GROWTH.items()},
                **{k: v + " (contribution)" for k, v in NIPA_CONTRIB.items()}, **NIPA_REAL_LEVELS,
                **TRADE_NOMINAL, **GDP_GROWTH, **MONTHLY_REAL, **PRODUCTIVITY, **CREDIT, **LABOR,
                **{k: f"{v}-year Treasury yield" for k, v in TREASURY.items()},
                **{k: v + " (real index)" for k, v in NONRES_QTY.items()}, **NONRES_NOM}

# The AI trade by segment (edit freely: each segment becomes an equal-weight basket)
AI_SEGMENTS = {
    "Chips": {"NVDA": "Nvidia", "AVGO": "Broadcom", "AMD": "AMD", "TSM": "TSMC", "MU": "Micron",
              "MRVL": "Marvell", "ARM": "Arm"},
    "Chip equipment": {"ASML": "ASML", "AMAT": "Applied Materials", "LRCX": "Lam Research", "KLAC": "KLA"},
    "Hyperscalers": {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta", "ORCL": "Oracle"},
    "Neoclouds": {"CRWV": "CoreWeave", "NBIS": "Nebius"},
    "Networking & servers": {"ANET": "Arista Networks", "DELL": "Dell", "SMCI": "Supermicro"},
    "Power & cooling": {"VRT": "Vertiv", "ETN": "Eaton", "GEV": "GE Vernova", "CEG": "Constellation Energy",
                        "VST": "Vistra"},
    "Software": {"PLTR": "Palantir", "NOW": "ServiceNow", "CRM": "Salesforce", "SNOW": "Snowflake",
                 "DDOG": "Datadog", "ADBE": "Adobe"},
}
SEGMENT_OF = {t: seg for seg, m in AI_SEGMENTS.items() for t in m}
AI_TICKERS = {t: n for m in AI_SEGMENTS.values() for t, n in m.items()}
DEFAULT_SEGMENTS = ["Chips", "Hyperscalers", "Software"]
# Index funds that track pieces of the AI trade (benchmarks; never averaged with the stocks)
AI_ETFS = {
    "QQQ": "Nasdaq-100 (Invesco QQQ)",
    "AIVC": "Bloomberg AI Value Chain Equal Weight (Amplify AIVC)",
    "SMH": "Semiconductors (VanEck SMH)",
    "SOXX": "Semiconductors (iShares SOXX)",
    "IGV": "Software (iShares IGV)",
    "AIQ": "AI & Technology (Global X AIQ)",
    "CHAT": "Generative AI & Tech (Roundhill CHAT)",
    "GRID": "Smart grid infrastructure (First Trust GRID)",
}
DEFAULT_ETFS = ["QQQ", "AIVC", "SMH", "IGV"]
BENCHMARKS = set(AI_ETFS) | {"SPY", "VOO", "IVV", "DIA", "IWM", "^IXIC", "^GSPC", "^NDX"}
BASKET = "Equal-weight AI basket"
HYPERSCALERS = {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta", "ORCL": "Oracle"}
# Firms tracked on the Firm level page: hyperscalers plus the debt-funded neoclouds
CAPEX_FIRMS = {**HYPERSCALERS, "CRWV": "CoreWeave", "NBIS": "Nebius"}

# Chart colours: same validated palette as the jobs dashboard
BLUE = "#2a78d6"
ORANGE = "#eb6834"
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8c6bd1", "#3fb7c9", "#a0785a",
               "#7a7974", "#c2b035", "#d65c5c", "#5c8f3a", "#b05fa8"]
MA_COLOR = "#7a7974"
GOOD = "#0ca30c"
BAD = "#d03b3b"
LABEL_INK = "#898781"
GRID = "#8987814d"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
FRED_API = "https://api.stlouisfed.org/fred/series/observations"
OWID_DC_CSV = "https://ourworldindata.org/grapher/monthly-spending-data-center-us.csv"
FMP_BASE = "https://financialmodelingprep.com/stable"
ORNN_API = "https://api.ornnai.com/api"
ORNN_GPUS = {"B200": "B200", "H200": "H200", "H100": "H100 SXM", "A100": "A100 SXM4"}
GPU_COLORS = {"B300": "#2a78d6", "B200": "#eb6834", "H200": "#1baf7a", "H100": "#eda100", "A100": "#8c6bd1"}
BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"),
    "Accept": "text/csv,text/plain,application/json,*/*",
}


# ---------------------------------------------------------------------------
# Data: FRED
# ---------------------------------------------------------------------------
def _get(url, params, headers=None, tries=3, timeout=(10, 90)):
    """GET with retries and a longer read timeout (FRED can be slow to respond)."""
    last_err = None
    for attempt in range(tries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise last_err


def parse_fred_csv(text: str) -> pd.DataFrame:
    """Parse a fredgraph.csv response into a long frame: date, series, value."""
    df = pd.read_csv(io.StringIO(text), na_values=".")
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"])
    long = df.melt(id_vars="date", var_name="series", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long.dropna(subset=["value"])


def _one_via_api(sid, start, api_key):
    resp = _get(FRED_API, {"series_id": sid, "api_key": api_key, "file_type": "json",
                           "observation_start": start})
    obs = pd.DataFrame(resp.json()["observations"])[["date", "value"]]
    obs["date"] = pd.to_datetime(obs["date"])
    obs["value"] = pd.to_numeric(obs["value"], errors="coerce")
    obs["series"] = sid
    return obs.dropna(subset=["value"])


FRED_FLOOR = "2010-01-01"     # every FRED group is saved from here (or earlier if a page asks for it)
PRICE_FLOOR = "2014-12-01"    # prices are saved from here (the "Show data from" slider starts at 2015)


def _stored(name: str, fetch, spinner: str, label: str = ""):
    """Saved copy from ai-capex\\data, or download (with a spinner) if it's older than the last 5 pm ET."""
    if store.fresh(name):
        return store.get(name, fetch, label)
    with st.spinner(spinner):
        return store.get(name, fetch, label)


def load_series(ids: tuple, start: str, api_key: str = "") -> tuple:
    """(long frame from `start`, failed IDs). The whole history from FRED_FLOOR is saved on disk and
    refreshed once a day, so moving the "Show data from" slider never downloads anything."""
    fetch_start = min(start, FRED_FLOOR)
    name = "fred_" + store.key(tuple(sorted(ids)), fetch_start)
    df, failed = _stored(name, lambda: _topup_series(name, ids, fetch_start, api_key),
                         "Updating data from FRED (once a day)...", label=",".join(ids)[:200])
    return df[df["date"] >= pd.Timestamp(start)], failed


FRED_RECENT_YEARS = 3     # each daily top-up re-reads this much, so recent revisions are picked up
FRED_FULL_DAYS = 30       # and the whole history is re-read once a month, for BEA's annual and comprehensive revisions


def _topup_series(name: str, ids: tuple, fetch_start: str, api_key: str):
    """First time (or once a month): the whole history. Otherwise only the last FRED_RECENT_YEARS, merged into
    the saved copy; series that fail to download keep their saved values."""
    old = store.load(name) if store.exists(name) else None
    full_at = store.meta(name).get("full_at")
    stale = (not full_at or
             (store.now_et() - pd.Timestamp(full_at).to_pydatetime()).days >= FRED_FULL_DAYS)
    if old is None or stale:
        df, failed = _download_series(ids, fetch_start, api_key)
        return store.WithMeta((df, failed), full_at=store.now_et().isoformat(timespec="seconds"))
    recent = max(fetch_start, f"{date.today().year - FRED_RECENT_YEARS}-01-01")
    new, _ = _download_series(ids, recent, api_key)       # raises if nothing came back: the old copy is kept
    odf = old[0]
    got = set(new["series"])
    odf = odf.assign(date=pd.to_datetime(odf["date"]))
    new = new.assign(date=pd.to_datetime(new["date"]))
    merged = pd.concat([odf[~odf["series"].isin(got) | (odf["date"] < pd.Timestamp(recent))], new],
                       ignore_index=True).sort_values(["series", "date"]).reset_index(drop=True)
    return merged, [s for s in ids if s not in set(merged["series"])]


def _download_series(ids: tuple, start: str, api_key: str = "") -> tuple:
    """Returns (long frame, list of series that failed). A bad or discontinued ID
    doesn't take the others down with it."""
    frames, failed = [], []
    if api_key:
        for sid in ids:
            try:
                frames.append(_one_via_api(sid, start, api_key))
            except Exception:
                failed.append(sid)
    else:
        try:  # one keyless request for everything
            resp = _get(FRED_CSV, {"id": ",".join(ids), "cosd": start}, headers=BROWSER_HEADERS, tries=2)
            frames.append(parse_fred_csv(resp.text))
        except Exception:  # fall back to one request per series
            for sid in ids:
                try:
                    resp = _get(FRED_CSV, {"id": sid, "cosd": start}, headers=BROWSER_HEADERS, tries=2)
                    frames.append(parse_fred_csv(resp.text))
                except Exception:
                    failed.append(sid)
    if not frames:
        raise RuntimeError("No FRED series could be downloaded.")
    out = pd.concat(frames, ignore_index=True)
    failed += [s for s in ids if s not in set(out["series"]) and s not in failed]
    out["name"] = out["series"].map(SERIES_NAMES).fillna(out["series"])
    return out, failed


def fred_or_stop(ids, start):
    try:
        df, failed = load_series(tuple(ids), start, fred_key)
    except Exception as e:
        msg = str(e).replace(fred_key, "***") if fred_key else str(e)
        st.error(f"Couldn't download data from FRED: {msg}")
        if not fred_key:
            st.info("FRED's keyless download is sometimes slow or blocks scripts. Add a free FRED API "
                    "key in the sidebar (fred.stlouisfed.org → My Account → API Keys).")
        st.stop()
    if failed:
        st.caption(f"⚠️ Not available from FRED right now: {', '.join(failed)}")
    return df


def ser(df: pd.DataFrame, sid: str) -> pd.Series:
    """One series as a date-indexed Series (empty if missing)."""
    s = df[df["series"] == sid].sort_values("date")
    return pd.Series(s["value"].values, index=pd.DatetimeIndex(s["date"]), name=sid)


# ---------------------------------------------------------------------------
# Data: Our World in Data (data center construction)
# ---------------------------------------------------------------------------
def _download_data_centers() -> pd.DataFrame:
    resp = _get(OWID_DC_CSV, {"v": 1, "csvType": "full", "useColumnShortNames": "false"},
                headers=BROWSER_HEADERS, tries=2, timeout=(10, 30))
    d = pd.read_csv(io.StringIO(resp.text))
    d = d[d["Entity"] == "United States"]
    val_col = [c for c in d.columns if c not in ("Entity", "Code", "Month", "Year", "Day")][0]
    out = pd.DataFrame({"date": pd.to_datetime(d["Month"].astype(str).str[:7] + "-01"),
                        "value": pd.to_numeric(d[val_col], errors="coerce") / 1e9})
    return out.dropna().sort_values("date")


def load_data_centers() -> tuple:
    """Monthly private data center construction, $B constant 2021 dollars, not seasonally adjusted.
    Saved on disk and refreshed once a day; falls back to the snapshot in ai_boom_reference.py."""
    try:
        return _stored("owid_data_centers", _download_data_centers,
                       "Updating data center construction (once a day)..."), "live"
    except Exception:
        snap = pd.DataFrame(ref.DC_SNAPSHOT, columns=["month", "value"])
        snap["date"] = pd.to_datetime(snap["month"] + "-01")
        return snap[["date", "value"]], "snapshot"


# ---------------------------------------------------------------------------
# Data: stock prices and cash flows (FMP if a key is set, else Yahoo Finance)
# ---------------------------------------------------------------------------
FMP_DOWN = {"why": ""}   # set when FMP refuses (rate limit or plan); later calls skip FMP straight to Yahoo


def _fmp(path, params, key):
    if FMP_DOWN["why"]:
        raise RuntimeError(f"FMP skipped: {FMP_DOWN['why']}")
    try:
        resp = _get(f"{FMP_BASE}/{path}", {**params, "apikey": key}, tries=1, timeout=(10, 30))
    except requests.HTTPError as e:
        code = getattr(e.response, "status_code", None)
        if code in (401, 402, 403, 429):
            FMP_DOWN["why"] = f"HTTP {code}"     # don't wait on FMP again for the other tickers
        raise RuntimeError(f"FMP HTTP {code}") from None
    data = resp.json()
    if isinstance(data, dict) and ("Error Message" in data or "error" in data):
        raise RuntimeError(str(data)[:200])
    return data


def load_prices(tickers: tuple, start: str, fmp_key: str = "") -> tuple:
    """Daily closes from `start` for `tickers`: (frame, {symbol: source}, failed). All segment stocks and
    benchmark funds are saved together on disk; any other ticker is saved on its own. Refreshed once a day
    after the close."""
    base = tuple(dict.fromkeys(list(AI_TICKERS) + list(AI_ETFS)))
    nb = "prices_base_" + store.key(base)
    parts = [_stored(nb, lambda: _topup_prices(nb, base, fmp_key),
                     "Updating stock prices (once a day, after the close)...")]
    for t in tickers:
        if t not in base:
            nt = "prices_" + re.sub(r"[^A-Za-z0-9]", "_", t)
            parts.append(_stored(nt, lambda t=t, nt=nt: _topup_prices(nt, (t,), fmp_key), f"Updating {t} prices..."))
    frames = [p[0] for p in parts if not p[0].empty]
    src = {k: v for p in parts for k, v in p[1].items()}
    px = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["date", "symbol", "close"])
    px = px[px["symbol"].isin(tickers) & (px["date"] >= pd.Timestamp(start))]
    return px, {k: v for k, v in src.items() if k in tickers}, [t for t in tickers if t not in set(px["symbol"])]


PRICE_OVERLAP_DAYS = 7     # each top-up re-reads the last week, to catch late corrections
ADJUST_TOLERANCE = 0.005   # a saved close that moved more than 0.5% means a split or dividend re-adjusted history


def _topup_prices(name: str, tickers: tuple, fmp_key: str = "") -> tuple:
    """First time: full history from PRICE_FLOOR. After that, only from a week before the last saved day,
    added to the saved copy. A ticker whose overlapping closes changed (a split or dividend re-adjusts past
    prices), that is new, or whose data is more than a month old gets its full history again."""
    empty = pd.DataFrame(columns=["date", "symbol", "close"])
    old = store.load(name) if store.exists(name) else None
    if old is None or old[0].empty:
        return _download_prices(tickers, PRICE_FLOOR, fmp_key)
    opx, osrc, _ = old
    opx = opx.assign(date=pd.to_datetime(opx["date"]))
    new_dates = lambda f: f.assign(date=pd.to_datetime(f["date"])) if not f.empty else f  # noqa: E731
    last = opx.groupby("symbol")["date"].max()
    newest = last.max()
    current = [t for t in tickers if t in last.index and last[t] >= newest - pd.Timedelta(days=30)]
    redo = [t for t in tickers if t not in current]
    if current:
        start = min(last[current]) - pd.Timedelta(days=PRICE_OVERLAP_DAYS)
        new, nsrc, _ = _download_prices(tuple(current), start.strftime("%Y-%m-%d"), fmp_key)
        new = new_dates(new)
    else:
        start, new, nsrc = newest, empty, {}
    if current and new.empty:
        raise RuntimeError("no new prices came back")          # keep the saved copy as it is
    for t in current:
        ov = new[new["symbol"] == t].merge(opx[opx["symbol"] == t], on=["date", "symbol"], suffixes=("", "_old"))
        if len(ov) and ((ov["close"] / ov["close_old"] - 1).abs().max() > ADJUST_TOLERANCE):
            redo.append(t)
    full, fsrc, _ = _download_prices(tuple(redo), PRICE_FLOOR, fmp_key) if redo else (empty, {}, [])
    full = new_dates(full)
    missing_new = [t for t in current if t not in set(new["symbol"]) and t not in redo]
    keep = opx[(opx["symbol"].isin(missing_new))                                      # no new data: keep all
               | (opx["symbol"].isin(current) & ~opx["symbol"].isin(redo + missing_new) & (opx["date"] < start))
               | (opx["symbol"].isin(redo) & ~opx["symbol"].isin(set(full["symbol"])))]  # full re-read failed
    parts = [f for f in (keep, new[~new["symbol"].isin(redo)], full) if not f.empty]
    out = pd.concat(parts, ignore_index=True) if parts else empty.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.drop_duplicates(["symbol", "date"], keep="last").sort_values(["symbol", "date"]).reset_index(drop=True)
    src = {**osrc, **nsrc, **fsrc}
    return out, {t: v for t, v in src.items() if t in set(out["symbol"])}, [t for t in tickers if t not in set(out["symbol"])]


def _download_prices(tickers: tuple, start: str, fmp_key: str = "") -> tuple:
    """Daily closes, long frame: date, symbol, close. Returns (frame, {symbol: source}, failed)."""
    FMP_DOWN["why"] = ""          # give FMP one fresh try per download
    frames, src, todo = [], {}, list(tickers)
    if fmp_key:
        for t in tickers:
            try:
                rows = _fmp("historical-price-eod/light", {"symbol": t, "from": start}, fmp_key)
                d = pd.DataFrame(rows)
                if d.empty:
                    continue
                frames.append(pd.DataFrame({"date": pd.to_datetime(d["date"]), "symbol": t,
                                            "close": pd.to_numeric(d["price"], errors="coerce")}))
                src[t] = "FMP"
                todo.remove(t)
            except Exception:
                pass  # plan limits on some symbols: try Yahoo below
    if todo:
        try:
            import yfinance as yf
            data = yf.download(todo, start=start, auto_adjust=True, progress=False,
                               group_by="ticker", threads=True)
            for t in list(todo):
                try:
                    close = data[t]["Close"] if isinstance(data.columns, pd.MultiIndex) else data["Close"]
                except KeyError:
                    continue
                close = close.dropna()
                if close.empty:
                    continue
                idx = pd.to_datetime(close.index)
                if idx.tz is not None:
                    idx = idx.tz_convert(None)
                frames.append(pd.DataFrame({"date": idx, "symbol": t, "close": close.values}))
                src[t] = "Yahoo Finance"
                todo.remove(t)
        except Exception:
            pass
    if not frames:
        return pd.DataFrame(columns=["date", "symbol", "close"]), src, todo
    return pd.concat(frames, ignore_index=True).dropna(), src, todo


def load_cash_flows(tickers: tuple, fmp_key: str = "") -> tuple:
    """Quarterly cash flows, saved on disk and refreshed once a day."""
    return _stored("cashflows_" + store.key(tickers), lambda: _download_cash_flows(tickers, fmp_key),
                   "Updating cash-flow statements (once a day)...")


def _download_cash_flows(tickers: tuple, fmp_key: str = "") -> tuple:
    """Quarterly capex, operating cash flow, free cash flow, net debt issued ($B)."""
    FMP_DOWN["why"] = ""          # give FMP one fresh try per download
    rows, src = [], {}
    for t in tickers:
        got = False
        if fmp_key:
            try:
                data = _fmp("cash-flow-statement", {"symbol": t, "period": "quarter", "limit": 5}, fmp_key)
                for r in data:
                    rows.append({"symbol": t, "quarter": pd.to_datetime(r["date"]),
                                 "capex": -float(r.get("capitalExpenditure") or 0) / 1e9,
                                 "ocf": float(r.get("operatingCashFlow") or 0) / 1e9,
                                 "fcf": float(r.get("freeCashFlow") or 0) / 1e9,
                                 "debt": float(r.get("netDebtIssuance") or 0) / 1e9})
                got = bool(data)
                if got:
                    src[t] = "FMP"
            except Exception:
                got = False
        if not got:
            try:
                import yfinance as yf
                cf = yf.Ticker(t).quarterly_cashflow
                for q in cf.columns:
                    c = cf[q]
                    capex = -float(c.get("Capital Expenditure", float("nan")))
                    ocf = float(c.get("Operating Cash Flow", float("nan")))
                    rows.append({"symbol": t, "quarter": pd.to_datetime(q), "capex": capex / 1e9,
                                 "ocf": ocf / 1e9, "fcf": (ocf - capex) / 1e9,
                                 "debt": float(c.get("Net Issuance Payments Of Debt", float("nan"))) / 1e9})
                src[t] = "Yahoo Finance"
            except Exception:
                pass
    d = pd.DataFrame(rows, columns=["symbol", "quarter", "capex", "ocf", "fcf", "debt"])
    d = d.dropna(subset=["capex", "ocf"]).drop_duplicates(["symbol", "quarter"])
    d["company"] = d["symbol"].map(CAPEX_FIRMS)
    return d.sort_values(["symbol", "quarter"]), src


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------
def quarterly_contributions(df: pd.DataFrame, trade_weight: float, include_rd: bool) -> pd.DataFrame:
    """Official BEA contributions (pp at annual rate) for the AI-proxy lines, plus a computed
    offset for net imports of computers, peripherals and parts:
        contribution = lagged nominal share of GDP x real growth at annual rate
    (BEA does not publish this end-use trade contribution on FRED)."""
    comp = ser(df, "B935RY2Q224SBEA")
    parts = {
        "Computers & peripherals": comp,
        "Other info-processing equipment": ser(df, "Y034RY2Q224SBEA") - comp,
        "Software": ser(df, "B985RY2Q224SBEA"),
    }
    if include_rd:
        parts["R&D"] = ser(df, "Y006RY2Q224SBEA")
    gdp_nom = ser(df, "GDP")
    for sid_real, sid_nom, sign, label in [("B852RX1Q020SBEA", "B852RC1Q027SBEA", -1, "imp"),
                                           ("B850RX1Q020SBEA", "B850RC1Q027SBEA", 1, "exp")]:
        real, nom = ser(df, sid_real), ser(df, sid_nom)
        growth = ((real / real.shift(1)) ** 4 - 1) * 100
        share = (nom / gdp_nom).shift(1)
        parts[label] = sign * share * growth * trade_weight
    if "imp" in parts and "exp" in parts:
        parts["Net imports of computers & parts"] = parts.pop("imp").add(parts.pop("exp"), fill_value=0)
    out = pd.DataFrame(parts).dropna(how="all")
    out.index.name = "date"
    return out


def yoy_buildout_proxy(df: pd.DataFrame, dc: pd.DataFrame, trade_weight: float) -> pd.DataFrame:
    """Fed-style AI buildout proxy, contribution to year-over-year real GDP growth (pp):
    software + computers & peripherals + data centers + power facilities - net imports of
    computers, peripherals & parts. Each term = nominal share of GDP four quarters earlier x
    real growth over four quarters. Data centers use OWID's constant-dollar series; power
    construction is only available in nominal terms, so its growth includes price changes."""
    gdp_nom = ser(df, "GDP")
    terms = {}
    for label, real_id, nom_id in [("Software", "B985RX1Q020SBEA", "B985RC1Q027SBEA"),
                                   ("Computers & peripherals", "B935RX1Q020SBEA", "B935RC1Q027SBEA")]:
        real, nom = ser(df, real_id), ser(df, nom_id)
        terms[label] = (real / real.shift(4) - 1) * (nom / gdp_nom).shift(4) * 100
    # Structures: quarterly averages of monthly series, at annual rates
    if not dc.empty:
        q = dc.set_index("date")["value"].resample("QS").agg(["mean", "count"])
        dcq = (q["mean"] * 12).where(q["count"] == 3)
        terms["Data centers"] = (dcq - dcq.shift(4)) / gdp_nom.shift(4) * 100
    pw = ser(df, "PRPWRCONS")
    if not pw.empty:
        q = pw.resample("QS").agg(["mean", "count"])
        pwq = (q["mean"] / 1000).where(q["count"] == 3)
        terms["Power facilities"] = (pwq - pwq.shift(4)) / gdp_nom.shift(4) * 100
    imp_r, imp_n = ser(df, "B852RX1Q020SBEA"), ser(df, "B852RC1Q027SBEA")
    exp_r, exp_n = ser(df, "B850RX1Q020SBEA"), ser(df, "B850RC1Q027SBEA")
    net = (-(imp_r / imp_r.shift(4) - 1) * (imp_n / gdp_nom).shift(4)
           + (exp_r / exp_r.shift(4) - 1) * (exp_n / gdp_nom).shift(4)) * 100 * trade_weight
    terms["Net imports of computers & parts"] = net
    out = pd.DataFrame(terms)
    out = out[out.notna().sum(axis=1) >= 3]
    out.index.name = "date"
    return out


def nonres_breakdown(df: pd.DataFrame, measure: str) -> tuple:
    """Real growth of nonresidential fixed investment and of structures, equipment and IPP, plus each
    part's contribution to the total's growth (pp):
        contribution = part's share of nominal nonresidential spending in the base period x its real growth
    The residual makes the parts add up exactly to BEA's total (chain weighting isn't exactly additive)."""
    q = {name: ser(df, sid) for sid, name in NONRES_QTY.items()}
    nom = pd.DataFrame({name.replace(" (nominal)", ""): ser(df, sid) for sid, name in NONRES_NOM.items()})
    lag = 4 if measure.startswith("Year") else 1
    if measure.startswith("Year"):
        growth = {k: (v / v.shift(4) - 1) * 100 for k, v in q.items()}
    else:
        growth = {k: ((v / v.shift(1)) ** 4 - 1) * 100 for k, v in q.items()}
    shares = nom.div(nom.sum(axis=1), axis=0).shift(lag)
    parts = pd.DataFrame({k: shares[k] * growth[k] for k in nom.columns})
    total = growth["Nonresidential fixed investment"]
    parts[RESIDUAL] = total - parts.sum(axis=1, min_count=3)
    parts.index.name = "date"
    return growth, parts.dropna(how="all"), total


SP_SCALE = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-",
            "CCC+", "CCC", "CCC-"]
MOODYS_SCALE = ["Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3", "B1", "B2",
                "B3", "Caa1", "Caa2", "Caa3"]


def notches_above_junk(sp: str, moodys: str = "—"):
    """Steps above the junk line: BBB-/Baa3 = 0, AAA/Aaa = 9, junk ratings negative."""
    for rating, scale in ((sp, SP_SCALE), (moodys, MOODYS_SCALE)):
        if rating in scale:
            return 9 - scale.index(rating)
    return None


def bond_spreads(tsy: pd.DataFrame) -> pd.DataFrame:
    """ref.AI_BONDS as a frame, with years to maturity and, where a market yield is known, the spread over
    the Treasury curve (FRED constant-maturity yields, interpolated to the bond's maturity, capped at 30y)
    on the date of the bond's price."""
    cols = ["Issuer", "Group", "Instrument", "Rate", "Type", "Coupon", "mat", "Maturity", "Amount", "Secured",
            "Price", "Yield %", "asof", "source"]
    b = pd.DataFrame(ref.AI_BONDS, columns=cols)
    b["mat"] = pd.to_datetime(b["mat"], errors="coerce")
    b["asof"] = pd.to_datetime(b["asof"], errors="coerce")
    wide = (tsy.pivot_table(index="date", columns="series", values="value").sort_index().ffill()
            if not tsy.empty else pd.DataFrame())
    tenors = sorted((y, sid) for sid, y in TREASURY.items() if sid in wide)
    tsy_y, spread = [], []
    for _, r in b.iterrows():
        ytm, asof, mat = r["Yield %"], r["asof"], r["mat"]
        if ytm is None or pd.isna(ytm) or pd.isna(asof) or pd.isna(mat) or not tenors:
            tsy_y.append(None); spread.append(None); continue
        row = wide[wide.index <= asof]
        if row.empty:
            tsy_y.append(None); spread.append(None); continue
        row = row.iloc[-1]
        yrs = min(30.0, max(1.0, (mat - asof).days / 365.25))
        xs = [t for t, _ in tenors]; ys = [float(row[sid]) for _, sid in tenors]
        curve = pd.Series(ys, index=[float(x) for x in xs])
        ty = float(curve.reindex(sorted(set(curve.index) | {yrs})).interpolate(method="index")[yrs])
        tsy_y.append(ty); spread.append((float(ytm) - ty) * 100)
    b["Treasury %"] = tsy_y
    b["Spread, bp"] = spread
    b["Years"] = ((b["mat"] - pd.Timestamp.today()).dt.days / 365.25).round(1)
    b["Secured"] = b["Secured"].map({True: "Secured", False: "Unsecured"})
    b["Priced"] = b["asof"].dt.strftime("%b %d, %Y").fillna("—")
    return b


def yoy(s: pd.Series, periods: int) -> pd.Series:
    return s.pct_change(periods, fill_method=None) * 100


# ---------------------------------------------------------------------------
# Charts (same look as the jobs dashboard)
# ---------------------------------------------------------------------------
def time_axis(d: pd.DataFrame, col="date"):
    months = 0
    if not d.empty:
        lo, hi = d[col].min(), d[col].max()
        months = (hi.year - lo.year) * 12 + hi.month - lo.month
    if months <= 40:
        label_expr = ("month(datum.value) == 0 ? timeFormat(datum.value, '%b %Y') "
                      ": timeFormat(datum.value, '%b')")
        tick = {"interval": "month", "step": 3 if months > 18 else 1}
    else:
        label_expr = "month(datum.value) == 0 ? timeFormat(datum.value, '%Y') : ''"
        tick = {"interval": "month", "step": 3}
    return alt.X(f"{col}:T", title=None, axis=alt.Axis(
        grid=False, ticks=True, tickSize=5, tickColor=LABEL_INK, domain=True, domainColor=LABEL_INK,
        tickCount=tick, labelExpr=label_expr, labelOverlap="greedy", labelAngle=0))


def axis_cfg(chart):
    return chart.configure_axis(
        grid=False, domain=False, tickColor=GRID, labelFontSize=11, titleFontSize=11
    ).configure_view(stroke=None)


def line_chart(d: pd.DataFrame, fmt=",.1f", y_title=None, height=300, colors=None, zero=False,
               log=False, ref_y=None, ref_label=None, legend=True, end_labels=True, dashed=None,
               date_fmt="%b %d, %Y"):
    """Long frame with date, Series, value. Shared hover rule with every series in the tooltip,
    bold end-of-line labels."""
    d = d.dropna(subset=["value"]).copy()
    if d.empty:
        return None
    names = list(dict.fromkeys(d["Series"]))
    colors = colors or CATEGORICAL[: len(names)]
    color = alt.Color("Series:N", scale=alt.Scale(domain=names, range=colors), sort=names,
                      legend=alt.Legend(title=None, orient="top", labelLimit=320) if legend and len(names) > 1 else None)
    yscale = alt.Scale(type="log") if log else alt.Scale(zero=zero)
    x = time_axis(d)
    y = alt.Y("value:Q", title=y_title, scale=yscale, axis=alt.Axis(format=fmt.replace("+", "")))
    lines = alt.Chart(d).mark_line(strokeWidth=2).encode(x=x, y=y, color=color)
    if dashed:
        lines = lines.encode(strokeDash=alt.condition(
            alt.FieldOneOfPredicate(field="Series", oneOf=dashed), alt.value([3, 3]), alt.value([1, 0])))
    hover = alt.selection_point(fields=["date"], nearest=True, on="pointerover", clear="pointerout", empty=False)
    wide = d.pivot_table(index="date", columns="Series", values="value").reset_index()
    safe = {n: f"s{i}" for i, n in enumerate(names)}
    wide = wide.rename(columns=safe)
    tips = [alt.Tooltip("date:T", format=date_fmt, title="Date")] + [
        alt.Tooltip(f"{safe[n]}:Q", format=fmt, title=n) for n in names if safe[n] in wide]
    rule = alt.Chart(wide).mark_rule(color=LABEL_INK).encode(
        x="date:T", opacity=alt.condition(hover, alt.value(1), alt.value(0)), tooltip=tips).add_params(hover)
    pts = alt.Chart(d).mark_point(size=50, filled=True).encode(
        x="date:T", y=alt.Y("value:Q", scale=yscale), color=alt.Color("Series:N", scale=alt.Scale(domain=names, range=colors), legend=None),
        opacity=alt.condition(hover, alt.value(1), alt.value(0)))
    layers = [lines, pts, rule]
    if end_labels:
        last = d.sort_values("date").groupby("Series").tail(1)
        layers.append(alt.Chart(last).mark_text(align="left", dx=6, fontSize=12, fontWeight="bold").encode(
            x="date:T", y=alt.Y("value:Q", scale=yscale), text=alt.Text("value:Q", format=fmt),
            color=alt.Color("Series:N", scale=alt.Scale(domain=names, range=colors), legend=None)))
    if ref_y is not None:
        layers.insert(0, alt.Chart(pd.DataFrame({"y": [ref_y], "t": [ref_label or ""]})).mark_rule(
            color=LABEL_INK, strokeDash=[4, 3]).encode(y="y:Q"))
    return axis_cfg(alt.layer(*layers).properties(height=height, padding={"right": 56}))


def bar_time(d: pd.DataFrame, fmt="+,.1f", y_title=None, height=260, color=None, sign_colors=True,
             date_fmt="%b %Y", label_last=True):
    """Time bars from a frame with date, value (blue up / orange down)."""
    d = d.dropna(subset=["value"])
    if d.empty:
        return None
    enc_color = (alt.condition(alt.datum.value >= 0, alt.value(BLUE), alt.value(ORANGE))
                 if sign_colors else alt.value(color or BLUE))
    base = alt.Chart(d).encode(x=time_axis(d), y=alt.Y("value:Q", title=y_title,
                                                      axis=alt.Axis(format=fmt.replace("+", ""))))
    bars = base.mark_bar(opacity=0.9).encode(color=enc_color, tooltip=[
        alt.Tooltip("date:T", format=date_fmt, title="Period"), alt.Tooltip("value:Q", format=fmt, title="Value")])
    layers = [alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=LABEL_INK).encode(y="y:Q"), bars]
    if label_last:
        last = d.sort_values("date").tail(1)
        layers.append(alt.Chart(last).mark_text(align="right", dy=-6, fontSize=12, fontWeight="bold",
                                                color=LABEL_INK).encode(
            x="date:T", y="value:Q", text=alt.Text("value:Q", format=fmt)))
    return axis_cfg(alt.layer(*layers).properties(height=height))


def stacked_contrib(parts: pd.DataFrame, total: pd.Series = None, total_name="Total", fmt="+.2f",
                    height=360, date_fmt="%Y Q%q", net_name="Net, pp", y_title="Percentage points"):
    """Stacked bars for components (positive and negative stack separately), a black net line
    across components and optional dots for a total (e.g. real GDP growth)."""
    long = parts.reset_index().melt(id_vars="date", var_name="Component", value_name="value").dropna()
    if long.empty:
        return None
    comps = list(parts.columns)
    colors = CATEGORICAL[: len(comps)]
    if "Net imports of computers & parts" in comps:
        colors[comps.index("Net imports of computers & parts")] = BAD
    if RESIDUAL in comps:
        colors[comps.index(RESIDUAL)] = "#c9c7c0"
    n = parts.index.nunique()
    bar_size = max(1.5, min(14.0, 760 / max(n, 1)))
    color = alt.Color("Component:N", scale=alt.Scale(domain=comps, range=colors), sort=comps,
                      legend=alt.Legend(title=None, orient="top", columns=3, labelLimit=320))
    bars = alt.Chart(long).mark_bar(opacity=0.9, size=bar_size).encode(
        x=time_axis(long), y=alt.Y("sum(value):Q", stack="zero", title=y_title),
        color=color, order=alt.Order("Component:N"),
        tooltip=[alt.Tooltip("date:T", format=date_fmt, title="Quarter"), "Component:N",
                 alt.Tooltip("value:Q", format=fmt, title="pp")])
    net = parts.sum(axis=1, min_count=1).rename("value").reset_index()
    net_line = alt.Chart(net).mark_line(color="#3b3a37", strokeWidth=2 if n <= 60 else 1.5,
                                        point=alt.OverlayMarkDef(color="#3b3a37", size=30) if n <= 60 else False
                                        ).encode(x="date:T", y="value:Q", tooltip=[
            alt.Tooltip("date:T", format=date_fmt, title="Quarter"), alt.Tooltip("value:Q", format=fmt, title=net_name)])
    layers = [alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=LABEL_INK).encode(y="y:Q"), bars, net_line]
    if total is not None:
        t = total.rename("value").reset_index()
        t = t[t["date"].isin(parts.index)]
        layers.append(alt.Chart(t).mark_point(shape="diamond", size=70, filled=True, color=ORANGE).encode(
            x="date:T", y="value:Q", tooltip=[alt.Tooltip("date:T", format=date_fmt, title="Quarter"),
                                              alt.Tooltip("value:Q", format=fmt, title=total_name)]))
    return axis_cfg(alt.layer(*layers).properties(height=height))


def grouped_bars(d: pd.DataFrame, cat: str, group: str, value: str, groups: list, colors: list,
                 fmt=",.0f", x_title=None, height=None, sort=None):
    """Horizontal grouped bars with value labels (like 'Where the jobs came from')."""
    cats = sort or list(dict.fromkeys(d[cat]))
    rank = {g: i for i, g in enumerate(groups)}
    d = d.assign(_rank=d[group].map(rank))
    y = alt.Y(f"{cat}:N", sort=cats, title=None, axis=alt.Axis(labelLimit=260))
    bars = alt.Chart(d).mark_bar(cornerRadiusEnd=4).encode(
        y=y, yOffset=alt.YOffset("_rank:O"), x=alt.X(f"{value}:Q", title=x_title,
                                                    scale=alt.Scale(domain=[0, d[value].max() * 1.15])),
        color=alt.Color(f"{group}:N", scale=alt.Scale(domain=groups, range=colors),
                        legend=alt.Legend(title=None, orient="top")),
        tooltip=[f"{cat}:N", f"{group}:N", alt.Tooltip(f"{value}:Q", format=fmt)])
    labels = alt.Chart(d).mark_text(align="left", dx=4, fontSize=11, color=LABEL_INK).encode(
        y=y, yOffset=alt.YOffset("_rank:O"), x=f"{value}:Q", text=alt.Text(f"{value}:Q", format=fmt))
    return axis_cfg((bars + labels).properties(height=height or 26 * len(cats) * len(groups) + 40))


def cat_bars(d: pd.DataFrame, cat: str, value: str, fmt=",.0f", y_title=None, height=260, color=BLUE,
             ref_y=None, ref_label=None, highlight_last=False):
    """Vertical bars over categories, value labels on top."""
    cats = list(d[cat])
    enc_color = alt.value(color)
    if highlight_last:
        d = d.assign(_last=[i == len(d) - 1 for i in range(len(d))])
        enc_color = alt.condition(alt.datum._last, alt.value(color), alt.value(MA_COLOR))
    x = alt.X(f"{cat}:N", sort=cats, title=None, axis=alt.Axis(labelAngle=0, labelLimit=140))
    top = max(d[value].max(), ref_y or 0) * 1.15
    bars = alt.Chart(d).mark_bar(cornerRadiusEnd=4, size=34).encode(
        x=x, y=alt.Y(f"{value}:Q", title=y_title, scale=alt.Scale(domain=[0, top]),
                     axis=alt.Axis(format=fmt.replace("+", ""))),
        color=enc_color, tooltip=[f"{cat}:N", alt.Tooltip(f"{value}:Q", format=fmt)])
    labels = alt.Chart(d).mark_text(dy=-8, fontSize=11, color=LABEL_INK).encode(
        x=x, y=f"{value}:Q", text=alt.Text(f"{value}:Q", format=fmt))
    layers = [bars, labels]
    if ref_y is not None:
        r = pd.DataFrame({"y": [ref_y], "label": [ref_label or ""]})
        layers.append(alt.Chart(r).mark_rule(color=BAD, strokeDash=[4, 3]).encode(y="y:Q"))
        layers.append(alt.Chart(r).mark_text(align="left", x=4, dy=-7, fontSize=11, color=BAD).encode(
            y="y:Q", text="label:N"))
    return axis_cfg(alt.layer(*layers).properties(height=height))


def return_heatmap(d: pd.DataFrame, names: dict, sessions=20):
    """Daily % change grid: one row per stock, one column per session, green up / red down."""
    dates = sorted(d["date"].unique())[-sessions:]
    d = d[d["date"].isin(dates)].dropna(subset=["ret"]).copy()
    d["Stock"] = d["symbol"].map(names).fillna(d["symbol"])
    d["day"] = d["date"].dt.strftime("%b %d")
    order = [pd.Timestamp(x).strftime("%b %d") for x in dates]
    rows = [names.get(s, s) for s in dict.fromkeys(d["symbol"])]
    lim = max(3.0, float(d["ret"].abs().quantile(0.95)))
    base = alt.Chart(d).encode(
        x=alt.X("day:O", sort=order, title=None, axis=alt.Axis(labelAngle=-45, labelFontSize=10)),
        y=alt.Y("Stock:N", sort=rows, title=None))
    rect = base.mark_rect(cornerRadius=3).encode(
        color=alt.Color("ret:Q", scale=alt.Scale(domain=[-lim, 0, lim], range=[BAD, "#f2f1ee", GOOD]),
                        legend=alt.Legend(title="% day", orient="right", format="+.0f")),
        tooltip=["Stock:N", alt.Tooltip("date:T", format="%a %b %d, %Y", title="Session"),
                 alt.Tooltip("ret:Q", format="+.2f", title="Change %"),
                 alt.Tooltip("close:Q", format=",.2f", title="Close")])
    text = base.mark_text(fontSize=10).encode(
        text=alt.Text("ret:Q", format="+.1f"),
        color=alt.condition(f"abs(datum.ret) > {lim * 0.6:.2f}", alt.value("white"), alt.value("#3b3a37")))
    return axis_cfg((rect + text).properties(height=30 * len(rows) + 50))


_NUMLIKE = re.compile(r"^\s*[~≈<>]?[$+\-−]?\$?[\d.,]+")


def _numeric_columns(df: pd.DataFrame) -> list:
    """Columns that hold numbers: numeric dtypes, plus text columns whose values all look like numbers
    (e.g. "~90", "65–70", "$1.2B"); dashes and blanks don't count against a column."""
    out = []
    for c in df.columns:
        col = df[c]
        if pd.api.types.is_bool_dtype(col):
            continue
        if pd.api.types.is_numeric_dtype(col):
            out.append(c)
            continue
        vals = [str(v) for v in col.dropna() if str(v).strip() not in ("", "—", "-", "n/a")]
        if vals and all(_NUMLIKE.match(v) for v in vals):
            out.append(c)
    return out


def html_table(data, bold_rows=(), hide_index=False, max_height=None):
    """Static table: numeric columns have right-aligned headings and values, text columns are
    left-aligned (st.dataframe can't align headings). Accepts a DataFrame or a pandas Styler.
    Colours follow the light/dark theme."""
    styler = data if hasattr(data, "to_html") and hasattr(data, "data") else data.style
    df = styler.data
    num = set(_numeric_columns(df))
    styles = [
        {"selector": "", "props": "border-collapse: collapse; width: 100%; font-size: 0.9rem;"
                                  "font-variant-numeric: tabular-nums;"},
        {"selector": "th, td", "props": f"padding: 6px 12px; border-bottom: 1px solid {GRID}; vertical-align: top;"},
        {"selector": "th.col_heading", "props": f"color: {LABEL_INK}; font-weight: 600; text-align: left;"},
        {"selector": "th.blank", "props": "text-align: left;"},
        {"selector": "th.row_heading", "props": "text-align: left; font-weight: 500;"},
        {"selector": "td", "props": "text-align: left;"},
    ]
    for i, c in enumerate(df.columns):
        if c in num:
            styles.append({"selector": f"th.col{i}, td.col{i}", "props": "text-align: right; white-space: nowrap;"})
    styler = styler.set_table_styles(styles)
    if hide_index:
        styler = styler.hide(axis="index")
    if bold_rows:
        styler = styler.apply(lambda r: ["font-weight: 700" if r.name in bold_rows else "" for _ in r], axis=1)
    box = "overflow-x: auto;" + (f" max-height: {max_height}px; overflow-y: auto;" if max_height else "")
    st.html(f'<div style="{box}">{styler.to_html()}</div>')


_DOWNLOADS = itertools.count()  # unique keys for download buttons


def chart_csv(chart, data=None) -> pd.DataFrame:
    """The data behind a chart, for the Download CSV button: explicit data if given, else the
    chart's own data frame (or the largest one among its layers)."""
    if isinstance(data, pd.DataFrame):
        return data
    frames = []
    stack = [chart]
    while stack:
        c = stack.pop()
        d = getattr(c, "data", None)
        if isinstance(d, pd.DataFrame):
            frames.append(d)
        stack.extend(getattr(c, "layer", None) or [])
        stack.extend(getattr(c, "vconcat", None) or [])
        stack.extend(getattr(c, "hconcat", None) or [])
    frames = [f for f in frames if not f.empty]
    return max(frames, key=len) if frames else pd.DataFrame()


def show(chart=None, name="chart_data", data=None):
    """Draw a chart with a 'Download CSV' button for its data underneath."""
    if chart is None:
        st.caption("No data for this chart yet.")
        return
    st.altair_chart(chart)
    try:
        csv = chart_csv(chart, data)
    except Exception:
        csv = pd.DataFrame()
    if not csv.empty:
        st.download_button("⬇ Download CSV", csv.to_csv(index=False).encode(),
                           file_name=f"{name}_{date.today():%Y-%m-%d}.csv", mime="text/csv",
                           key=f"dl_{name}_{next(_DOWNLOADS)}")


def tile(col, label, value, delta=None, help=None, delta_color="off"):
    col.metric(label, value, delta, delta_color=delta_color, help=help)


def link(src):
    name, url = src
    return f"[{name}]({url})"


def fred_link(sid):
    return f"[{sid}](https://fred.stlouisfed.org/series/{sid})"


def sources_box(fred_ids=(), refs=(), notes=()):
    with st.expander("Sources and notes"):
        if fred_ids:
            st.markdown("**FRED series:** " + " · ".join(f"{fred_link(s)} {SERIES_NAMES.get(s, '')}" for s in fred_ids))
        for r in refs:
            st.markdown("- " + link(r))
        for n in notes:
            st.markdown(f"- {n}")


def window(d: pd.DataFrame, col="date"):
    return d[d[col] >= pd.Timestamp(f"{start_year}-01-01")]


def to_long(series_map: dict) -> pd.DataFrame:
    """{label: date-indexed Series} -> long frame date, Series, value."""
    frames = [pd.DataFrame({"date": s.index, "Series": k, "value": s.values}) for k, s in series_map.items()
              if s is not None and len(s)]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["date", "Series", "value"])


def qlabel(ts) -> str:
    return f"{ts.year} Q{(ts.month - 1) // 3 + 1}"


def last_val(s: pd.Series, i=-1):
    s = s.dropna()
    return s.iloc[i] if len(s) >= abs(i) else float("nan")


# ---------------------------------------------------------------------------
# Page 1: Real economy
# ---------------------------------------------------------------------------
def real_economy_page():
    st.title("Real economy: AI investment in the national accounts")
    st.caption("BEA NIPA Tables 5.3.5 (levels), 5.3.1 (real growth) and contributions to real GDP growth, "
               "Census C30 construction, Federal Reserve G.17, BLS. Quarterly data at seasonally adjusted "
               "annual rates unless noted.")
    with st.sidebar:
        include_rd = st.checkbox("Include R&D in contributions", value=True, key="re_rd",
                                 help="The Fed's buildout proxy leaves R&D out; many trackers include it.")
        trade_w = st.slider("Weight on computer trade offset", 0.0, 1.0, 1.0, 0.05, key="re_w",
                            help="Share of computer, peripheral and parts trade treated as AI investment. "
                                 "1.0 subtracts all of it; the Fed down-weights by the capital-goods share "
                                 "of trade.")

    raw = fred_or_stop(REAL_ECON_IDS, f"{start_year - 3}-01-01")
    dc, dc_src = load_data_centers()

    gdp_g = ser(raw, "A191RL1Q225SBEA")
    broad = ser(raw, "A679RC1Q027SBEA")
    comp = ser(raw, "B935RC1Q027SBEA")
    imp_n, exp_n = ser(raw, "B852RC1Q027SBEA"), ser(raw, "B850RC1Q027SBEA")
    ip = ser(raw, "IPG3344S")
    contrib = quarterly_contributions(raw, trade_w, include_rd)
    latest_q = contrib.index.max() if not contrib.empty else gdp_g.index.max()

    # --- Headline tiles -----------------------------------------------------
    c = st.columns(6)
    tile(c[0], f"Real GDP growth, {qlabel(gdp_g.index[-1])}", f"{last_val(gdp_g):.1f}%",
         f"prior qtr {last_val(gdp_g, -2):.1f}%", help="Percent change at annual rate.")
    tile(c[1], "Info-processing equip. + software", f"${last_val(broad):,.0f}B",
         f"{last_val(yoy(broad, 4)):+.1f}% YoY", help="A679RC, nominal, annual rate.")
    tile(c[2], "Computers & peripherals", f"${last_val(comp):,.0f}B",
         f"{last_val(yoy(comp, 4)):+.1f}% YoY", help="Servers dominate the recent surge.")
    if not contrib.empty:
        net_pp = contrib.loc[latest_q].sum()
        gross_pp = contrib.loc[latest_q].drop("Net imports of computers & parts", errors="ignore").sum()
        tile(c[3], f"AI-proxy contribution, {qlabel(latest_q)}", f"{net_pp:+.2f}pp",
             f"gross {gross_pp:+.2f}pp before imports",
             help="Sum of the lines in the contributions chart below, net of computer imports.")
    dcl = dc.sort_values("date")
    dc_yoy = (dcl["value"].iloc[-1] / dcl["value"].iloc[-13] - 1) * 100 if len(dcl) > 13 else float("nan")
    tile(c[4], f"Data center construction, {dcl['date'].iloc[-1]:%b %Y}",
         f"${ref.DC_NOMINAL_LATEST['value_b_saar']:.0f}B" if dcl['date'].iloc[-1].strftime('%b %Y') == ref.DC_NOMINAL_LATEST['month']
         else f"${dcl['value'].iloc[-1] * 12:.0f}B",
         f"{dc_yoy:+.0f}% YoY (real)",
         help="Annual rate. Latest nominal SAAR from the Census release when available; "
              "YoY uses OWID's constant-dollar monthly series.")
    tile(c[5], f"Semiconductor output, {ip.index[-1]:%b %Y}", f"{last_val(ip):.1f}",
         f"{last_val(yoy(ip, 12)):+.1f}% YoY", help="Industrial production, NAICS 3344, 2017=100.")

    # --- Real nonresidential fixed investment, since 1990 -----------------------
    st.subheader("Business investment since 1990: structures, equipment and intellectual property")
    st.caption("Real private nonresidential fixed investment (BEA, inflation-adjusted) and its three parts. "
               "AI spending sits mostly in equipment (servers, chips, networking) and intellectual property "
               "(software, R&D); data center buildings are in structures.")
    nr = fred_or_stop(NONRES_IDS, "1988-01-01")
    a, b, c3 = st.columns([2, 2, 3])
    with a:
        nr_view = st.segmented_control("View", ["Lines", "Stacked contributions"], default="Lines",
                                       key="re_nr_view", label_visibility="collapsed") or "Lines"
    with b:
        opts = ["Year over year %", "Quarterly, annualized %"] + (["Index, 2017 = 100"] if nr_view == "Lines" else [])
        nr_measure = st.segmented_control("Measure", opts, default="Year over year %", key=f"re_nr_measure_{nr_view}",
                                          label_visibility="collapsed") or "Year over year %"
    with c3:
        nr_from = st.slider("From", 1990, date.today().year - 1, 1990, key="re_nr_from")
    cutoff = pd.Timestamp(f"{nr_from}-01-01")
    if nr_view == "Lines":
        if nr_measure.startswith("Index"):
            m = {name: ser(nr, sid) for sid, name in NONRES_QTY.items()}
            fmt, yt = ",.0f", "Real index, 2017 = 100"
        else:
            m, _, _ = nonres_breakdown(nr, nr_measure)
            fmt, yt = "+.1f", ("% change from a year earlier" if nr_measure.startswith("Year")
                               else "% change at annual rate")
        long = to_long(m)
        show(name="nonres_investment_lines", chart=line_chart(long[long["date"] >= cutoff], fmt=fmt, y_title=yt,
             height=360, zero=not nr_measure.startswith("Index"), colors=["#3b3a37", ORANGE, BLUE, "#1baf7a"],
             date_fmt="%Y Q%q"))
    else:
        _, parts, total = nonres_breakdown(nr, nr_measure)
        parts = parts[parts.index >= cutoff]
        show(name="nonres_investment_contributions", chart=stacked_contrib(
            parts, net_name="Nonresidential growth, %",
            y_title="Contribution to growth, pp" + (" (year over year)" if nr_measure.startswith("Year") else " (annualized)"),
            height=380))
        st.caption("Bars = each part's contribution to the growth of real nonresidential investment (its share of "
                   "spending × its real growth); they stack to the black line, total nonresidential growth. The grey "
                   "residual is the small gap left by chain weighting.")
        if not parts.empty:
            last = parts.dropna(how="all").index.max()
            cols = st.columns(4)
            tile(cols[0], f"Nonresidential growth, {qlabel(last)}", f"{total.get(last, float('nan')):+.1f}%")
            for col, k in zip(cols[1:], ["Structures", "Equipment", "Intellectual property products"]):
                tile(col, k, f"{parts.loc[last, k]:+.2f}pp")

    # --- Investment lines ----------------------------------------------------
    st.subheader("How much are businesses spending on AI-related investment?")
    st.caption("Business investment from the official GDP accounts (BEA) in the categories where AI spending "
               "shows up. The broadest line, info-processing equipment + software, contains the others: "
               "computers & servers are part of info-processing equipment. R&D is shown separately. "
               "Communication equipment is left out because it mixes networking gear with phones and broadcast gear.")
    measure = st.segmented_control("Measure", ["Level ($B)", "Year-over-year %", "Real growth, annualized %"],
                                   default="Level ($B)", key="re_measure", label_visibility="collapsed") or "Level ($B)"
    picks = st.multiselect("Lines", list(NIPA_NOMINAL.values()), default=list(NIPA_NOMINAL.values()), key="re_lines",
                           label_visibility="collapsed")
    if measure == "Level ($B)":
        m = {n: ser(raw, sid) for sid, n in NIPA_NOMINAL.items() if n in picks}
        fmt, yt = ",.0f", "$B, annual rate"
    elif measure == "Year-over-year %":
        m = {n: yoy(ser(raw, sid), 4) for sid, n in NIPA_NOMINAL.items() if n in picks}
        fmt, yt = "+.1f", "% change from a year earlier (nominal)"
    else:
        m = {n: ser(raw, sid) for sid, n in NIPA_REAL_GROWTH.items() if n in picks}
        fmt, yt = "+.1f", "% change at annual rate (real)"
    show(name="ai_investment_lines", chart=line_chart(window(to_long(m)), fmt=fmt, y_title=yt, height=340, zero=measure != "Level ($B)",
                    date_fmt="%Y Q%q"))

    # --- Contributions -------------------------------------------------------
    st.subheader("How much did AI investment add to GDP growth each quarter?")
    st.caption("Each bar is the percentage points of quarterly GDP growth (annualized) that one category added, "
               "as published by BEA. The red bar subtracts imported computer hardware, which counts as US "
               "investment but is made abroad. Black line = AI total after imports. Orange diamonds = overall GDP "
               "growth. The table's last row shows the AI total as a share of all growth.")
    cw = contrib[contrib.index >= pd.Timestamp(f"{start_year}-01-01")]
    show(name="gdp_contribution_quarterly", chart=stacked_contrib(cw, gdp_g, "Real GDP growth"))
    if not contrib.empty:
        tbl = contrib.tail(6).copy()
        tbl["Net AI proxy"] = tbl.sum(axis=1)
        tbl["Real GDP growth"] = gdp_g.reindex(tbl.index)
        tbl["AI share of growth"] = tbl["Net AI proxy"] / tbl["Real GDP growth"] * 100
        tbl.index = [qlabel(i) for i in tbl.index]
        styler = tbl.T.style.format("{:+.2f}", na_rep="—").format(
            "{:.0f}%", subset=pd.IndexSlice[["AI share of growth"], :], na_rep="—")
        html_table(styler, bold_rows=["Net AI proxy"])

    # --- Fed-style year-over-year proxy ---------------------------------------
    st.subheader("How much of the past year's GDP growth came from the AI buildout?")
    st.markdown(
        "This follows the method in a July 2026 Federal Reserve staff note. It adds up four kinds of spending "
        "that make up the AI buildout: **software**, **computers & servers**, **data center construction** and "
        "**power plant construction**. It then **subtracts imported computer hardware**: a GPU built in Taiwan "
        "counts as US investment but isn't US production, so it doesn't add to US GDP.\n\n"
        "Each bar is how many percentage points that piece added to real GDP growth over the past four quarters. "
        "The black line is the total after imports; the orange diamonds are overall GDP growth. When the line sits "
        "close to the diamonds, nearly all of the economy's growth came from the AI buildout.")
    st.caption("Compared with the quarterly chart above: this one covers a full year, so it's less jumpy; it adds "
               "data centers and power plants; and it leaves out R&D. Structures come from the Census construction "
               "survey (data centers in inflation-adjusted dollars via Our World in Data; power in current dollars).")
    proxy = yoy_buildout_proxy(raw, dc, trade_w)
    gdpc = ser(raw, "GDPC1")
    gdp_yoy = yoy(gdpc, 4)
    pw = proxy[proxy.index >= pd.Timestamp(f"{start_year}-01-01")]
    show(name="ai_buildout_share_of_gdp_growth_yoy", chart=stacked_contrib(pw, gdp_yoy, "Real GDP growth, YoY %"))
    fed = ref.FED_PROXY
    a, b, cc = st.columns(3)
    tile(a, "Fed estimate, Q1 2026 (gross)", f"{fed['q1_2026_gross_pp']:.2f}pp",
         f"computer imports −{fed['q1_2026_import_drag_pp']:.2f}pp", help=link(fed["source"]))
    tile(b, "Fed estimate, late 2025", f"{fed['late_2025_net_pp']:.2f}pp net",
         f"{fed['late_2025_gross_pp']:.2f}pp gross")
    if not proxy.empty:
        lq = proxy.dropna(how="all").index.max()
        tile(cc, f"This proxy, {qlabel(lq)}", f"{proxy.loc[lq].sum():+.2f}pp",
             f"of {gdp_yoy.get(lq, float('nan')):.1f}% real GDP growth YoY")

    # --- Structures -----------------------------------------------------------
    st.subheader("Building the data centers and power plants")
    st.caption("Spending on the buildings themselves, from the Census Bureau's monthly construction survey. The "
               "GDP categories above cover equipment and software, not buildings, so these are tracked separately.")
    l, r = st.columns(2)
    with l:
        dcw = window(dc).assign(Series="Monthly")
        roll = dc.set_index("date")["value"].rolling(12).mean()
        dcw = pd.concat([dcw, window(to_long({"12-month average": roll}))])
        show(name="data_center_construction", chart=line_chart(dcw, fmt=",.2f", y_title="$B per month, 2021 dollars", height=280,
                        colors=[BLUE, MA_COLOR], dashed=["Monthly"], date_fmt="%b %Y"))
        st.caption(f"Data center construction, not seasonally adjusted. Source: "
                   f"{'Our World in Data (live)' if dc_src == 'live' else 'snapshot in ai_boom_reference.py'}. "
                   "Excludes the servers inside.")
    with r:
        power = ser(raw, "PRPWRCONS") / 1000
        show(name="power_construction", chart=line_chart(window(to_long({"Power construction": power})), fmt=",.1f",
                        y_title="$B, annual rate", height=280, legend=False, date_fmt="%b %Y"))
        st.caption(f"Private power construction, latest {last_val(yoy(power, 12)):+.1f}% YoY. "
                   "Included in the Fed's buildout proxy.")

    # --- Trade and domestic production ---------------------------------------
    st.subheader("How much AI hardware is imported, and how much the US makes")
    l, r = st.columns(2)
    with l:
        show(name="computer_trade", chart=line_chart(window(to_long({"Imports": imp_n, "Exports": exp_n, "Net imports": imp_n - exp_n})),
                        fmt=",.0f", y_title="$B, annual rate", height=280, colors=[ORANGE, BLUE, BAD],
                        date_fmt="%Y Q%q"))
        st.caption("Trade in computers, servers and parts. Imports far exceed exports: most AI hardware is built "
                   "abroad, so that spending boosts other countries' output rather than US GDP. Net imports are "
                   "what the charts above subtract.")
    with r:
        show(name="semiconductor_production", chart=line_chart(window(to_long({"Semiconductors (NAICS 3344)": ip})), fmt=",.1f",
                        y_title="Index, 2017 = 100", height=280, legend=False, date_fmt="%b %Y"))
        st.caption("US factory output of semiconductors and other electronic components (Federal Reserve "
                   "industrial production index, 2017 = 100).")

    st.subheader("Is AI making workers more productive yet?")
    prod = ser(raw, "PRS85006092")
    show(name="labor_productivity", chart=bar_time(window(pd.DataFrame({"date": prod.index, "value": prod.values})), fmt="+.1f",
                  y_title="% change at annual rate", height=240, date_fmt="%Y Q%q"))
    st.caption("Output per hour worked in the business sector (BLS), % change at an annual rate. Productivity is "
               "the payoff the investment is supposed to deliver. So far the gains look like firms getting more from "
               "existing staff; a measure that strips out how hard people and machines are worked has barely moved.")

    st.download_button("Download real-economy series (CSV)",
                       raw.pivot_table(index="date", columns="name", values="value").reset_index().to_csv(index=False).encode(),
                       file_name=f"ai_boom_real_economy_{date.today():%Y_%m_%d}.csv", mime="text/csv")
    sources_box(REAL_ECON_IDS + NONRES_IDS, refs=[ref.DC_SOURCE, ref.DC_NOMINAL_LATEST["source"], fed["source"]], notes=[
        f"Fed figure data (gross vs net series): {fed['data_file']}",
        "Gross output and value added by industry (NAICS 3344, software publishing, data processing & hosting, "
        "computer systems design, scientific R&D) are in BEA's GDP-by-industry tables (apps.bea.gov), not on FRED.",
        "BEA's digital economy satellite account is no longer produced (last estimates 2017-2022); BEA publishes no AI satellite account.",
        "Multifactor productivity and capital services for software and IT equipment are annual BLS series (not shown).",
    ])


# ---------------------------------------------------------------------------
# Page 2: Firm level
# ---------------------------------------------------------------------------
def firm_page():
    st.title("Firm level: hyperscaler spending and funding")
    st.caption("Hyperscalers: Microsoft, Alphabet, Amazon, Meta, Oracle. Neoclouds (CoreWeave, Nebius) rent GPU "
               "capacity to AI labs and hyperscalers and fund most of their buildout with debt.")
    st.caption("Quarterly cash-flow statements (FMP if a key is set, otherwise Yahoo Finance), company capex "
               f"guidance and bond issuance (reference figures as of {ref.AS_OF}).")
    cf, src = load_cash_flows(tuple(CAPEX_FIRMS), fmp_key)

    c = st.columns(len(ref.FIRM_FACTS))
    for col, (label, value, detail, s) in zip(c, ref.FIRM_FACTS):
        tile(col, label, value, help=f"{detail} Source: {s[0]}")

    # --- Combined capex vs combined operating cash flow --------------------------
    st.subheader("Combined capex vs combined operating cash flow")
    if not cf.empty:
        agg = cf.assign(q=cf["quarter"].dt.to_period("Q")).groupby("q").agg(
            capex=("capex", "sum"), ocf=("ocf", "sum"), firms=("symbol", "nunique"),
            names=("company", lambda x: ", ".join(sorted(x.dropna()))))
        full = agg["firms"].max()
        agg = agg[agg["firms"] == full]  # only quarters where every firm has reported
        agg.index = agg.index.to_timestamp()
        agg.index.name = "date"
        if len(agg):
            last = agg.iloc[-1]
            c = st.columns(4)
            tile(c[0], f"Combined capex, {qlabel(agg.index[-1])}", f"${last['capex']:,.0f}B",
                 f"{(last['capex'] / agg['capex'].iloc[-5] - 1) * 100:+.0f}% YoY" if len(agg) >= 5 else None)
            tile(c[1], "Combined operating cash flow", f"${last['ocf']:,.0f}B",
                 f"{(last['ocf'] / agg['ocf'].iloc[-5] - 1) * 100:+.0f}% YoY" if len(agg) >= 5 else None)
            fcf_ = last["ocf"] - last["capex"]
            tile(c[2], "Free cash flow (OCF − capex)", f"{'−' if fcf_ < 0 else '+'}${abs(fcf_):,.0f}B", delta_color="off")
            tile(c[3], "Capex as % of operating cash flow", f"{last['capex'] / last['ocf'] * 100:.0f}%",
                 f"{agg['capex'].iloc[0] / agg['ocf'].iloc[0] * 100:.0f}% in {qlabel(agg.index[0])}",
                 delta_color="off")
            show(name="combined_capex_vs_operating_cash_flow",
                 data=agg.reset_index()[["date", "capex", "ocf"]].rename(
                     columns={"capex": "Combined capex, $B", "ocf": "Combined operating cash flow, $B"}),
                 chart=line_chart(to_long({"Combined capex": agg["capex"], "Combined operating cash flow": agg["ocf"]}),
                                  fmt="$,.0f", y_title="$B per quarter", height=320, colors=[BLUE, MA_COLOR],
                                  zero=True, date_fmt="%Y Q%q"))
            st.caption(f"Sum across {full} firms ({last['names']}). Only quarters where all of them have reported are "
                       "shown. When the blue line crosses above the grey one, the group spends more on capex than its "
                       "operations bring in, and the gap is funded with cash reserves or new debt.")
        else:
            st.caption("Not enough overlapping quarters to sum.")

    st.subheader("Capex against operating cash flow")
    if cf.empty:
        st.warning("Couldn't load cash-flow statements. Add an FMP key in the sidebar or check that yfinance is installed.")
    else:
        st.caption("$B per quarter. Capex = purchases of property and equipment (excludes finance leases, so it "
                   "runs below company-reported capex). Free cash flow = operating cash flow − capex.")
        firms = list(CAPEX_FIRMS.items())
        cols = [c for i in range(0, len(firms), 4) for c in st.columns(4)]
        for col, (sym, name) in zip(cols, firms):
            d = cf[cf["symbol"] == sym]
            with col:
                if d.empty:
                    st.markdown(f"**{name}**")
                    st.caption("Not available")
                    continue
                long = pd.concat([d.assign(Series="Capex", value=d["capex"]),
                                  d.assign(Series="Operating cash flow", value=d["ocf"])])
                long["q"] = long["quarter"].apply(qlabel)
                order = ["Capex", "Operating cash flow"]
                top = max(long["value"].max(), 0) * 1.18 or 1
                bottom = min(long["value"].min(), 0) * 1.18
                base = alt.Chart(long).encode(
                    x=alt.X("q:N", title=None, axis=alt.Axis(labelAngle=-45)),
                    xOffset=alt.XOffset("Series:N", sort=order),
                    y=alt.Y("value:Q", title=None, scale=alt.Scale(domain=[bottom, top])))
                bars = base.mark_bar(cornerRadiusEnd=3).encode(
                    color=alt.Color("Series:N", scale=alt.Scale(domain=order, range=[BLUE, MA_COLOR]),
                                    legend=alt.Legend(title=None, orient="top") if sym == "MSFT" else None),
                    tooltip=["q:N", "Series:N", alt.Tooltip("value:Q", format=",.1f", title="$B")])
                labels = base.mark_text(baseline="bottom", dy=-3, fontSize=9, color=LABEL_INK).encode(
                    text=alt.Text("value:Q", format=",.0f"))
                show(name="capex_vs_cash_flow_" + sym.lower(),
                     data=long[["q", "Series", "value"]].rename(columns={"q": "Quarter", "value": "$B"}),
                     chart=axis_cfg((bars + labels).properties(title=name, height=240)))
        latest = cf.sort_values("quarter").groupby("symbol").tail(1)
        ttm = cf.sort_values("quarter").groupby("symbol").tail(4).groupby("symbol")[["capex", "ocf", "fcf"]].sum()
        t = latest.set_index("symbol")[["company", "quarter", "capex", "ocf", "fcf", "debt"]].join(
            ttm.add_suffix(" TTM"))
        t["Capex / OCF %"] = t["capex"] / t["ocf"] * 100
        t["Source"] = t.index.map(src)
        t["quarter"] = t["quarter"].dt.strftime("%b %d, %Y")
        t = t.rename(columns={"company": "Company", "quarter": "Quarter ending", "capex": "Capex", "ocf": "Op. cash flow",
                              "fcf": "Free cash flow", "debt": "Net debt issued", "capex TTM": "Capex TTM",
                              "ocf TTM": "OCF TTM", "fcf TTM": "FCF TTM"})

        def neg_red(v):
            return f"color: {BAD}; font-weight: 600" if isinstance(v, (int, float)) and v < 0 else ""
        money = ["Capex", "Op. cash flow", "Free cash flow", "Net debt issued", "Capex TTM", "OCF TTM", "FCF TTM"]
        html_table(t.reset_index(drop=True).style.format({**{m: "${:,.1f}B" for m in money},
                                                          "Capex / OCF %": "{:.0f}%"}, na_rep="—")
                   .map(neg_red, subset=["Free cash flow", "FCF TTM"]), hide_index=True)

    l, r = st.columns(2)
    with l:
        st.subheader("2026 capex guidance kept rising")
        g = pd.DataFrame([(co, lab, v) for co, j, a, ju, _ in ref.CAPEX_GUIDANCE
                          for lab, v in [("Jan 2026", j), ("Apr 2026", a), ("Jul 2026", ju)]],
                         columns=["Company", "Guide", "Capex"])
        show(name="capex_guidance_2026", chart=grouped_bars(g, "Company", "Guide", "Capex", ["Jan 2026", "Apr 2026", "Jul 2026"],
                          ["#c9c7c0", MA_COLOR, BLUE], fmt="$,.0f", x_title="$B (midpoint of range)"))
        st.caption("Microsoft's July guide is lower only because data center leases moved from finance to "
                   "operating leases (~$190B like-for-like).")
    with r:
        st.subheader("Hyperscaler bond issuance")
        b = pd.DataFrame(ref.HYPERSCALER_BONDS, columns=["Year", "Issuance", "Share of US IG supply %"])
        show(name="hyperscaler_bond_issuance", chart=cat_bars(b, "Year", "Issuance", fmt="$,.0f", y_title="$B", height=300, highlight_last=True))
        st.caption("Alphabet, Amazon, Meta, Microsoft and Oracle. Share of US investment-grade supply: "
                   + ", ".join(f"{y} {s}%" for y, _, s in ref.HYPERSCALER_BONDS[-3:]) + ".")

    # --- 2027 outlook ----------------------------------------------------------
    st.subheader("2027 outlook")
    st.caption("No hyperscaler has given a calendar-2027 capex number yet. Bars compare each company's latest "
               "2026 guide with sell-side 2027 estimates; Oracle's bar is its own fiscal-2027 guidance "
               "(Jun 2026–May 2027).")
    c = st.columns(len(ref.CAPEX_2027_TOTALS))
    for col, (label, value, detail, s) in zip(c, ref.CAPEX_2027_TOTALS):
        tile(col, label, value, help=f"{detail} Source: {s[0]}")
    groups = ["2026 guidance (Jul)", "2027 analyst estimate", "FY27 company guidance"]
    rows = []
    for co, g26, est27, guide27, _, _ in ref.CAPEX_2027:
        for grp, v in zip(groups, [g26, est27, guide27]):
            if v is not None:
                rows.append((co, grp, v))
    g27 = pd.DataFrame(rows, columns=["Company", "Basis", "Capex"])
    l, r = st.columns([3, 2])
    with l:
        show(name="capex_outlook_2027", chart=grouped_bars(g27, "Company", "Basis", "Capex", [g for g in groups if g in set(g27["Basis"])],
                          [MA_COLOR, BLUE, ORANGE], fmt="$,.0f", x_title="$B",
                          sort=[c[0] for c in ref.CAPEX_2027]))
        est = [(co, g26, e) for co, g26, e, *_ in ref.CAPEX_2027 if g26 and e]
        if est:
            st.caption("Implied 2026→2027 growth: " + ", ".join(f"{co} {e / g - 1:+.0%}" for co, g, e in est)
                       + ". Microsoft has no public 2027 estimate in this file.")
    with r:
        said = pd.DataFrame([(co, txt) for co, *_, txt, _ in ref.CAPEX_2027], columns=["Company", "What management said"])
        html_table(said, hide_index=True)

    sources_box(refs=[ref.PLATFORMONOMICS, ref.VANGUARD_BONDS] + [f[3] for f in ref.FIRM_FACTS]
                + list(dict.fromkeys([c[5] for c in ref.CAPEX_2027] + [t[3] for t in ref.CAPEX_2027_TOTALS])),
                notes=["Cash flows: " + ", ".join(f"{k} {v}" for k, v in src.items()) if src else "Cash flows: none loaded"])


# ---------------------------------------------------------------------------
# Page 3: Financial markets
# ---------------------------------------------------------------------------
def markets_page():
    st.title("Financial markets: stocks and credit")
    st.caption("Daily closes from FMP (with a key) or Yahoo Finance and ICE BofA option-adjusted spreads via FRED, "
               "saved and updated once a day after the close. Single-company CDS, bond prices and ratings have no "
               "free daily feed: they are the latest published readings, each shown with its own date.")
    with st.sidebar:
        segs = st.multiselect("Segments in the stock table", list(AI_SEGMENTS), default=DEFAULT_SEGMENTS,
                              key="mk_segments")
        seg_tickers = [t for s_ in segs for t in AI_SEGMENTS[s_]]
        tickers = st.multiselect("Stocks", seg_tickers, default=seg_tickers, key=f"mk_tickers_{'_'.join(segs)}",
                                 format_func=lambda t: f"{t} · {AI_TICKERS[t]}")
        etfs = st.multiselect("Benchmark funds", list(AI_ETFS), default=DEFAULT_ETFS, key="mk_etfs",
                              format_func=lambda t: f"{t} · {AI_ETFS[t]}")
        extra = st.text_input("Other tickers (comma-separated)", key="mk_extra")
        sessions = st.slider("Sessions in daily-move grid", 10, 60, 20, 5, key="mk_sessions")
    extra_t = [t.strip().upper() for t in extra.split(",") if t.strip()]
    stocks = list(dict.fromkeys(tickers + [t for t in extra_t if t not in BENCHMARKS]))
    etfs = list(dict.fromkeys(etfs + [t for t in extra_t if t in BENCHMARKS]))
    names = {**AI_TICKERS, **AI_ETFS, **{t: t for t in extra_t if t not in AI_TICKERS and t not in AI_ETFS}}
    seg_of = {**SEGMENT_OF, **{t: "Other" for t in extra_t if t not in SEGMENT_OF}, **{t: "Fund" for t in AI_ETFS}}

    # Load every segment member (for the segment baskets) plus the chosen funds and extras
    universe = tuple(dict.fromkeys(list(AI_TICKERS) + etfs + extra_t))
    px, psrc, pfail = load_prices(universe, f"{min(start_year, date.today().year - 1)}-12-01", fmp_key)
    if px.empty:
        st.warning("Couldn't load prices. Add an FMP key in the sidebar or install yfinance.")
    else:
        px = px.sort_values(["symbol", "date"])
        px["ret"] = px.groupby("symbol")["close"].pct_change() * 100
        wide = px.pivot_table(index="date", columns="symbol", values="close").sort_index()
        win0 = pd.Timestamp(f"{start_year}-01-01")
        ytd0 = pd.Timestamp(date.today().year, 1, 1)

        def basket(members):
            """Equal-weight basket rebalanced daily (average daily return), as a price index."""
            cols = [m for m in members if m in wide]
            if not cols:
                return pd.Series(dtype=float)
            r = wide[cols].pct_change().mean(axis=1, skipna=True).fillna(0)
            return (1 + r).cumprod() * 100

        def stats(g: pd.Series) -> dict:
            g = g.dropna()
            if len(g) < 2:
                return {}
            before_ytd = g[g.index < ytd0]
            return {"1 day %": (g.iloc[-1] / g.iloc[-2] - 1) * 100,
                    "5 days %": (g.iloc[-1] / g.iloc[-6] - 1) * 100 if len(g) > 5 else None,
                    "1 month %": (g.iloc[-1] / g.iloc[-22] - 1) * 100 if len(g) > 21 else None,
                    "YTD %": (g.iloc[-1] / before_ytd.iloc[-1] - 1) * 100 if len(before_ytd) else None,
                    "From 52-wk high %": (g.iloc[-1] / g.tail(252).max() - 1) * 100}

        def pos_neg(v):
            if not isinstance(v, (int, float)) or pd.isna(v) or v == 0:
                return ""
            return f"color: {GOOD if v > 0 else BAD}; font-weight: 600"
        pcts = ["1 day %", "5 days %", "1 month %", "YTD %", "From 52-wk high %"]

        # --- The AI trade by segment ------------------------------------------
        st.subheader("The AI trade by segment")
        st.caption("Each segment is an equal-weight basket of its stocks (average daily return, rebalanced daily); "
                   "dashed lines are the benchmark funds. Segments and members are listed under Sources and notes "
                   "and can be edited at the top of ai_boom_dashboard.py.")
        seg_lines, score = {}, []
        for seg, members in AI_SEGMENTS.items():
            b = basket(members)
            if b.empty:
                continue
            seg_lines[seg] = b
            have = [m for m in members if m in wide]
            score.append({"Segment / fund": seg, "Holdings": f"{len(have)} stocks", **stats(b)})
        for e in etfs:
            if e in wide:
                seg_lines[e] = wide[e]
                score.append({"Segment / fund": f"{e} · {AI_ETFS.get(e, e)}", "Holdings": "Fund", **stats(wide[e])})
        rebased = {k: (v[v.index >= win0] / v[v.index >= win0].dropna().iloc[0] * 100)
                   for k, v in seg_lines.items() if len(v[v.index >= win0].dropna())}
        seg_names = [k for k in rebased if k in AI_SEGMENTS]
        fund_names = [k for k in rebased if k not in AI_SEGMENTS]
        colors = CATEGORICAL[: len(seg_names)] + ["#9a9890", "#c9c7c0", "#7a7974", "#b5b3ab", "#5f5e5a",
                                                  "#d6d4cc", "#8a8880", "#a8a69e"][: len(fund_names)]
        show(name="ai_segments_vs_funds", chart=line_chart(to_long({k: rebased[k] for k in seg_names + fund_names}), fmt=",.0f",
                        y_title="Index, first day in window = 100", height=420, ref_y=100, colors=colors,
                        dashed=fund_names))
        sc = pd.DataFrame(score)
        if not sc.empty:
            sc = sc.sort_values("YTD %", ascending=False, na_position="last")
            html_table(sc.style.format({p: "{:+.2f}%" for p in pcts if p in sc}, na_rep="—")
                       .map(pos_neg, subset=[p for p in pcts if p in sc]), hide_index=True)

        # --- Individual stocks ---------------------------------------------------
        st.subheader("Individual stocks")
        shown = [t for t in stocks if t in wide]
        if not shown:
            st.info("Pick at least one segment or stock in the sidebar.")
        else:
            rows = []
            for t in shown + [e for e in etfs if e in wide]:
                g = wide[t].dropna()
                rows.append({"Symbol": t, "Name": names.get(t, t), "Segment": seg_of.get(t, ""),
                             "Date": g.index[-1].strftime("%b %d"), "Close": g.iloc[-1], **stats(g),
                             "Source": psrc.get(t, "")})
            tab = pd.DataFrame(rows)

            c = st.columns(min(6, len(shown)))
            for col, (_, r) in zip(c, tab.head(6).iterrows()):
                parts = [f"{r['1 day %']:+.2f}%" if pd.notna(r.get("1 day %")) else None,
                         f"YTD {r['YTD %']:+.0f}%" if pd.notna(r.get("YTD %")) else None]
                tile(col, f"{r['Name']}, {r['Date']}", f"{r['Close']:,.2f}",
                     " · ".join(p for p in parts if p) or None, delta_color="normal")

            st.markdown(f"**Daily moves, last {sessions} sessions**")
            show(name="daily_moves", chart=return_heatmap(px[px["symbol"].isin(shown)], names, sessions))

            st.markdown("**Performance since the start of the window**")
            sel = {names.get(t, t): wide[t] for t in shown}
            if len(shown) > 1:
                sel = {BASKET: basket(shown), **sel}
            for e in etfs:
                if e in wide:
                    sel[e] = wide[e]
            reb = {k: v[v.index >= win0] / v[v.index >= win0].dropna().iloc[0] * 100
                   for k, v in sel.items() if len(v[v.index >= win0].dropna())}
            order = list(reb)
            pal = iter(CATEGORICAL * 3)
            colors = ["#3b3a37" if n == BASKET else ("#c9c7c0" if n in etfs else next(pal)) for n in order]
            show(name="stock_performance", chart=line_chart(to_long(reb), fmt=",.0f", y_title="Index, first day = 100", height=380, ref_y=100,
                            colors=colors, dashed=[e for e in etfs if e in reb]))
            st.caption(f"Black line = {BASKET.lower()} of the stocks selected. Grey dashed lines = benchmark funds.")

            if len(shown) > 1:
                avg = {"Symbol": "Average", "Name": f"Average of {len(shown)} AI stocks (equal weight)",
                       "Segment": "", "Date": "", "Close": None, "Source": "Calculated"}
                avg.update(tab[tab["Symbol"].isin(shown)][pcts].mean(numeric_only=True).to_dict())
                tab = pd.concat([tab, pd.DataFrame([avg])], ignore_index=True)

            def row_style(r):
                if r["Symbol"] == "Average":
                    return ["font-weight: 700; border-top: 2px solid #8987814d" for _ in r]
                if r["Symbol"] in etfs:
                    return ["color: #898781; font-style: italic" if c not in pcts else "" for c in r.index]
                return ["" for _ in r]
            html_table(tab.style.format({"Close": "{:,.2f}", **{p: "{:+.2f}%" for p in pcts}}, na_rep="—")
                       .map(pos_neg, subset=pcts).apply(row_style, axis=1), hide_index=True)
            st.caption("Grey italic rows = benchmark funds. Average row = simple average across the AI stocks in the "
                       "table only; funds are left out.")
        if pfail:
            st.caption(f"No prices for: {', '.join(pfail)}")
        st.download_button("Download prices (CSV)", wide.reset_index().to_csv(index=False).encode(),
                           file_name="ai_stocks_prices.csv", mime="text/csv")

    st.subheader("Credit")
    raw = fred_or_stop(tuple(CREDIT), f"{start_year - 1}-01-01")
    spreads = {CREDIT[s]: ser(raw, s) * 100 for s in CREDIT}
    c = st.columns(4)
    for col, (n, s) in zip(c, spreads.items()):
        chg = last_val(s) - s[s.index <= s.index[-1] - pd.Timedelta(days=90)].iloc[-1] if len(s) > 70 else float("nan")
        tile(col, f"{n}, {s.index[-1]:%b %d}", f"{last_val(s):.0f}bp", f"{chg:+.0f}bp vs 3 months ago",
             delta_color="inverse")
    o = ref.CDS_5Y["Oracle"]
    tile(c[3], f"Oracle 5-yr CDS, {o[2]}", f"{o[1]}bp", f"{o[0] - o[3]:+.0f}bp since start of 2026",
         delta_color="inverse", help=ref.ORACLE_CDS["note"])
    show(name="credit_spreads", chart=line_chart(window(to_long(spreads)), fmt=",.0f", y_title="Basis points over Treasuries", height=320,
                    colors=[BLUE, ORANGE, BAD]))
    st.caption("Hyperscalers sit in the AA bucket, except Oracle (BBB−). High yield shown for context.")

    # --- Bond by bond: hyperscalers, neoclouds and other AI borrowers ------------------------
    tsy, _ = load_series(tuple(TREASURY), "2025-01-01", fred_key)
    bonds = bond_spreads(tsy)
    st.markdown("**AI borrowers' bonds: latest spread over Treasuries, bond by bond**")
    grp = st.segmented_control("Borrowers", ["All", "Hyperscalers", "Neoclouds & AI"], default="All",
                               key="mk_bond_grp", label_visibility="collapsed") or "All"
    bv = bonds if grp == "All" else bonds[bonds["Group"] == grp]
    priced = bv.dropna(subset=["Spread, bp"]).copy()
    if not priced.empty:
        priced["Bond"] = (priced["Issuer"] + " " + priced["Coupon"].map(lambda c: f"{c:g}%")
                          + " " + priced["Maturity"].str[-4:])
        priced = priced.sort_values("Spread, bp", ascending=False)
        y = alt.Y("Bond:N", sort=priced["Bond"].tolist(), title=None,
                  axis=alt.Axis(labelLimit=1000, labelOverlap=False, labelFontSize=12))
        tip = ["Bond:N", "Rate:N", "Type:N", "Maturity:N", alt.Tooltip("Price:Q", format=".2f"),
               alt.Tooltip("Yield %:Q", format=".2f"), alt.Tooltip("Treasury %:Q", format=".2f", title="Treasury, same maturity %"),
               alt.Tooltip("Spread, bp:Q", format=",.0f"), "Priced:N"]
        bars = alt.Chart(priced).mark_bar(height=16).encode(
            y=y, x=alt.X("Spread, bp:Q", title="Spread over Treasuries of the same maturity, bp (on the price date)"),
            color=alt.Color("Group:N", scale=alt.Scale(domain=["Hyperscalers", "Neoclouds & AI"], range=[BLUE, ORANGE]),
                            legend=alt.Legend(title=None, orient="top")),
            tooltip=tip)
        lab = alt.Chart(priced).mark_text(align="left", dx=4, fontSize=11, color=LABEL_INK).encode(
            y=y, x="Spread, bp:Q",
            text=alt.Text("lab:N"),
        ).transform_calculate(lab="format(datum['Spread, bp'], ',.0f') + 'bp · ' + datum.Rate + ' · ' + datum.Priced")
        show(name="ai_bond_spreads", data=priced.drop(columns=["source"]),
             chart=axis_cfg((bars + lab).properties(height=30 * len(priced) + 70)))
        st.caption("Each bar is one bond: its yield to maturity minus the Treasury yield for the same maturity on the "
                   "day it was priced (FRED constant-maturity curve, interpolated; 30-year for longer bonds). Labels "
                   "show the coupon and the price date. Prices are the latest published readings (no free daily bond "
                   "feed): Big Tech and SpaceX long bonds from a TradingView screen on Oct 5, Oracle 2046 Oct 1, "
                   "CoreWeave 2032 Oct 19.")

    st.markdown("**Terms of AI-related debt: fixed vs floating, coupon, maturity, security**")
    terms = bv[["Issuer", "Instrument", "Rate", "Type", "Maturity", "Amount", "Secured", "Price", "Yield %",
                "Spread, bp", "Priced"]].copy()
    terms = terms.sort_values(["Issuer", "Type", "Maturity"])
    html_table(terms.style.format({"Price": "{:.2f}", "Yield %": "{:.2f}", "Spread, bp": "{:,.0f}"}, na_rep="—"),
               hide_index=True, max_height=480)
    st.caption("Floating = rate resets with SOFR, so the cost rises and falls with short-term rates; the margin over "
               "SOFR is the credit spread fixed at signing. Most neocloud debt is floating-rate loans secured by GPUs "
               "and customer contracts, which have no public market price. CoreWeave's unsecured bonds are the "
               "traded benchmark. Edit AI_BONDS in ai_boom_reference.py to add bonds or new prices.")

    st.markdown("**Credit ratings and 5-year CDS across the AI trade**")
    rows = []
    for co, seg, sp, md, fi, asof, note, _ in ref.RATINGS:
        latest, latest_lab, cds_date, base, base_date, _ = ref.CDS_5Y.get(co, (None, "—", None, None, None, None))
        rows.append({"Company": co, "Segment": seg, "S&P": sp, "Moody's": md, "Fitch": fi,
                     "Notches above junk": notches_above_junk(sp, md),
                     "5-yr CDS, bp": latest_lab, "CDS as of": cds_date or "—",
                     "Latest CDS news": ref.CDS_NOTES.get(co, ""),
                     "Early 2026, bp": base, "Baseline date": base_date or "—",
                     "Change, bp": (latest - base) if latest is not None and base is not None else None,
                     "Rating as of": asof, "Note": note})
    rt = pd.DataFrame(rows)
    seg_pick = st.segmented_control("Segment", ["All"] + ref.RATING_SEGMENTS, default="All", key="mk_rating_seg",
                                    label_visibility="collapsed") or "All"
    view = rt if seg_pick == "All" else rt[rt["Segment"] == seg_pick]

    # Ladder: each company's distance from the junk line (BBB-/Baa3 = 0)
    lad = view.dropna(subset=["Notches above junk"]).copy()
    if not lad.empty:
        lad["Rating"] = [sp if sp != "—" else md + " (Moody's)" for sp, md in zip(lad["S&P"], lad["Moody's"])]
        order = lad.sort_values("Notches above junk", ascending=False)["Company"].tolist()
        segs = [g for g in ref.RATING_SEGMENTS if g in set(lad["Segment"])]
        y = alt.Y("Company:N", sort=order, title=None, axis=alt.Axis(labelLimit=220))
        bars = alt.Chart(lad).mark_bar(cornerRadiusEnd=4, height=14).encode(
            y=y, x=alt.X("Notches above junk:Q", title="Notches above junk (0 = BBB-, the lowest investment grade)",
                         scale=alt.Scale(domain=[min(-5, lad["Notches above junk"].min() - 1), 10])),
            color=alt.Color("Segment:N", scale=alt.Scale(domain=ref.RATING_SEGMENTS, range=CATEGORICAL[:5]),
                            legend=alt.Legend(title=None, orient="top") if len(segs) > 1 else None),
            tooltip=["Company:N", "Segment:N", "S&P:N", "Moody's:N", "Fitch:N", "Rating as of:N", "Note:N"])
        labels = alt.Chart(lad).mark_text(align="left", dx=5, fontSize=11, fontWeight="bold", color=LABEL_INK).encode(
            y=y, x="Notches above junk:Q", text="Rating:N")
        junk = alt.Chart(pd.DataFrame({"x": [-0.5], "t": ["Junk ←"]})).mark_rule(color=BAD, strokeDash=[4, 3]).encode(x="x:Q")
        show(name="ai_credit_ratings", data=view, chart=axis_cfg((bars + labels + junk).properties(height=24 * len(lad) + 50)))

    def widen_red(v):
        if not isinstance(v, (int, float)) or pd.isna(v) or v == 0:
            return ""
        return f"color: {BAD if v > 0 else GOOD}; font-weight: 600"

    def junk_red(v):
        if not isinstance(v, (int, float)) or pd.isna(v):
            return ""
        return f"color: {BAD}; font-weight: 700" if v <= 0 else ""
    html_table(view.style.format({"Early 2026, bp": "{:.0f}", "Change, bp": "{:+.0f}", "Notches above junk": "{:.0f}"},
                                 na_rep="—")
               .map(junk_red, subset=["Notches above junk"]).map(widen_red, subset=["Change, bp"]), hide_index=True)
    st.caption("Notches above junk use S&P's rating (Moody's where S&P is missing): 0 = BBB−, the last step before "
               "junk; negative = junk. CDS = yearly cost to insure $10M of debt, in bp; red = wider since the baseline. "
               "Dealer CDS quotes aren't free, so these are the latest levels published in the press, each with its "
               "date: Oracle and CoreWeave Oct 19, 2026. Amazon, Alphabet, Meta and Nvidia hit record highs on Oct 15 "
               "but their levels weren't published, so their numbers are still late-July readings. Alphabet, Amazon and "
               "Microsoft baselines are mid-Nov 2025. Edit RATINGS and CDS_5Y in ai_boom_reference.py to update.")

    sources_box(tuple(CREDIT) + tuple(TREASURY), refs=[ref.CDS_OCT15, ref.REUTERS_SPREADS, ref.ORACLE_CDS["source"], ref.CDS_BASELINE_SOURCE]
                + list(dict.fromkeys(b[13] for b in ref.AI_BONDS))
                + list(dict.fromkeys(v[5] for v in ref.CDS_5Y.values()))
                + list(dict.fromkeys(r[7] for r in ref.RATINGS)),
                notes=[f"**{seg}:** " + ", ".join(f"{t} ({n})" for t, n in m.items()) for seg, m in AI_SEGMENTS.items()]
                + ["**Funds:** " + "; ".join(f"{t} = {n}" for t, n in AI_ETFS.items()),
                   "Bloomberg's own AI indexes (e.g. BAIVT, the AI Value Chain Equal Weight Index) need a terminal; "
                   "AIVC is the ETF that tracks BAIVT."]
                + (["Prices: " + ", ".join(sorted({f'{v}' for v in psrc.values()}))] if not px.empty else []))


# ---------------------------------------------------------------------------
# Page 4: Leading signals
# ---------------------------------------------------------------------------
def leading_page():
    st.title("Leading signals: where the boom is heading")
    st.caption("Chip supply-chain orders lead capex by a quarter or two; AI revenue, token volume and token prices "
               f"test whether the spending pays off. Reference figures as of {ref.AS_OF}.")
    nv, ts = ref.NVIDIA, ref.TSMC_MONTHLY[-1]
    c = st.columns(5)
    tile(c[0], "Nvidia next-quarter revenue guide", f"${nv['q3_guide_b']:.0f}B",
         f"Q2 ${nv['q2_fy27_rev_b']}B, {nv['q2_yoy_pct']:+d}% YoY")
    tile(c[1], f"TSMC revenue, {pd.Timestamp(ts[0] + '-01'):%b %Y}", f"NT${ts[1]:.0f}B", f"{ts[2]:+.1f}% YoY")
    tile(c[2], f"Korean chip exports, {ref.KOREA_CHIP_RECORDS[-1][0]} 2026", f"${ref.KOREA_CHIP_RECORDS[-1][1]}B",
         f"{ref.KOREA_CHIP_LATEST_YOY:+.1f}% YoY")
    tile(c[3], "DRAM contract prices, Q4 2026", ref.DRAM["q4_2026_dram_incl_hbm"], "incl. HBM (TrendForce)")
    tile(c[4], "US firms using AI", f"{ref.BTOS_AI_USE[-1][1]}%", f"from {ref.BTOS_AI_USE[1][1]}% at start of 2026")

    # --- AI revenue vs capex ----------------------------------------------------
    st.subheader("Is AI revenue keeping up with the capex?")
    st.caption("Hyperscalers don't report AI revenue as a separate line, so the closest reported measure is their "
               "cloud businesses (AWS, Google Cloud, Microsoft Cloud), where AI demand is booked. Capex = cash "
               "purchases of property & equipment (excludes finance leases). Meta has no cloud business: its AI "
               "returns come through advertising.")
    q_dates = sorted(ref.CLOUD_REVENUE)
    rows = []
    for d in q_dates:
        for seg, rev in ref.CLOUD_REVENUE[d].items():
            co = ref.CLOUD_OF[seg]
            cap = ref.CAPEX_QUARTERLY[d][co]
            rows.append({"date": pd.Timestamp(d), "Quarter": qlabel(pd.Timestamp(d)), "Company": co, "Cloud unit": seg,
                         "Cloud revenue": rev, "Capex": cap, "Capex / cloud revenue %": cap / rev * 100})
    rc = pd.DataFrame(rows)
    latest_q = rc["date"].max()
    c = st.columns(4)
    for col, (seg, g) in zip(c, rc.groupby("Cloud unit", sort=False)):
        g = g.sort_values("date")
        tile(col, f"{g['Company'].iloc[-1]} capex ÷ {seg} revenue, {g['Quarter'].iloc[-1]}",
             f"{g['Capex / cloud revenue %'].iloc[-1]:.0f}%",
             f"{g['Capex / cloud revenue %'].iloc[-1] - g['Capex / cloud revenue %'].iloc[0]:+.0f}pp vs {g['Quarter'].iloc[0]}",
             delta_color="inverse", help="Above 100% = spending more on capex each quarter than the cloud unit brings in.")
    tot = rc[rc["date"] == latest_q]
    meta_cap = ref.CAPEX_QUARTERLY[q_dates[-1]]["Meta"]
    tile(c[3], f"All three, {qlabel(latest_q)}", f"{tot['Capex'].sum() / tot['Cloud revenue'].sum() * 100:.0f}%",
         f"{(tot['Capex'].sum() + meta_cap) / tot['Cloud revenue'].sum() * 100:.0f}% incl. Meta's capex", delta_color="off")

    cols = st.columns(3)
    for col, (seg, g) in zip(cols, rc.groupby("Cloud unit", sort=False)):
        with col:
            long = pd.concat([g.assign(Series="Capex", value=g["Capex"]),
                              g.assign(Series=f"{seg} revenue", value=g["Cloud revenue"])])
            names_ = ["Capex", f"{seg} revenue"]
            base = alt.Chart(long).encode(
                x=alt.X("Quarter:N", title=None, sort=[qlabel(pd.Timestamp(d)) for d in q_dates],
                        axis=alt.Axis(labelAngle=0, labelFontSize=10)),
                xOffset=alt.XOffset("Series:N", sort=names_),
                y=alt.Y("value:Q", title="$B per quarter", scale=alt.Scale(domain=[0, long["value"].max() * 1.18])))
            bars = base.mark_bar(cornerRadiusEnd=3).encode(
                color=alt.Color("Series:N", scale=alt.Scale(domain=names_, range=[ORANGE, BLUE]),
                                legend=alt.Legend(title=None, orient="top")),
                tooltip=["Quarter:N", "Series:N", alt.Tooltip("value:Q", format="$,.1f", title="$B")])
            labels = base.mark_text(baseline="bottom", dy=-3, fontSize=9, color=LABEL_INK).encode(
                text=alt.Text("value:Q", format=",.0f"))
            show(name=f"capex_vs_{seg.lower().replace(' ', '_')}_revenue", data=g.drop(columns=["date"]),
                 chart=axis_cfg((bars + labels).properties(title=f"{g['Company'].iloc[0]}: capex vs {seg}", height=250)))

    # Annualized snapshot: the revenue AI demand produces vs what is being spent
    latest_rr = {}
    for d, co, v, _note in sorted(ref.AI_REVENUE):  # latest run-rate per lab
        latest_rr[co] = v
    lab_rr = sum(latest_rr.values())
    capex_guide_mid = sum(jul for _co, _jan, _apr, jul, _n in ref.CAPEX_GUIDANCE)
    ms = [x for x in ref.AI_DISCLOSURES if x[1] == "Microsoft" and "estimate" not in x[2]][-1]
    ms_q = max(d for d in q_dates if d <= ms[0]) if any(d <= ms[0] for d in q_dates) else q_dates[0]
    snap = pd.DataFrame([
        (f"Big-3 cloud revenue vs big-4 capex ({qlabel(latest_q)} × 4)", "Revenue", tot["Cloud revenue"].sum() * 4),
        (f"Big-3 cloud revenue vs big-4 capex ({qlabel(latest_q)} × 4)", "Capex",
         (tot["Capex"].sum() + meta_cap) * 4),
        (f"Microsoft AI run-rate vs its capex ({qlabel(pd.Timestamp(ms_q))} × 4)", "Revenue", ms[3]),
        (f"Microsoft AI run-rate vs its capex ({qlabel(pd.Timestamp(ms_q))} × 4)", "Capex",
         ref.CAPEX_QUARTERLY[ms_q]["Microsoft"] * 4),
        ("Anthropic + OpenAI run-rate vs big-4 2026 capex guidance", "Revenue", lab_rr),
        ("Anthropic + OpenAI run-rate vs big-4 2026 capex guidance", "Capex", capex_guide_mid),
    ], columns=["Comparison", "Measure", "Annualized $B"])
    st.markdown("**Annualized: AI-driven revenue vs capex**")
    show(name="ai_revenue_vs_capex_annualized", chart=grouped_bars(
        snap, "Comparison", "Measure", "Annualized $B", ["Revenue", "Capex"], [BLUE, ORANGE], fmt="$,.0f",
        x_title="$B per year", height=230))
    st.caption("Cloud revenue includes non-AI services, so it overstates AI revenue; Microsoft's AI run-rate is the only "
               "explicit hyperscaler AI figure. AI-lab revenue is end demand that hyperscalers partly capture as cloud "
               "spending. Capex is front-loaded: assets bought now earn revenue over several years, so the ratio "
               "should fall if demand keeps up. Contracted backlog points that way: Google Cloud's rose to "
               f"${ref.CLOUD_BACKLOG[-1][2]}B in {ref.CLOUD_BACKLOG[-1][1]}.")
    disc = pd.DataFrame([(pd.Timestamp(d).strftime("%b %Y"), co, lab, v, note) for d, co, lab, v, note, _ in ref.AI_DISCLOSURES],
                        columns=["Date", "Company", "Disclosure", "Run-rate, $B", "Note"])
    html_table(disc, hide_index=True)

    l, r = st.columns(2)
    with l:
        st.subheader("AI-lab revenue run-rates")
        ar = pd.DataFrame(ref.AI_REVENUE, columns=["date", "Series", "value", "note"])
        ar["date"] = pd.to_datetime(ar["date"])
        show(name="ai_lab_revenue", chart=line_chart(ar, fmt="$,.0f", y_title="$B annualized", height=300, colors=[BLUE, ORANGE],
                        date_fmt="%b %Y"))
        st.caption("Reported run-rates are extrapolations, not audited revenue; the two labs may measure differently.")
    with r:
        st.subheader("Token volume on OpenRouter")
        orr = pd.DataFrame([(d, v) for d, v, *_ in ref.OPENROUTER], columns=["date", "value"])
        orr["date"], orr["Series"] = pd.to_datetime(orr["date"]), "Tokens per week"
        show(name="openrouter_tokens", chart=line_chart(orr, fmt=",.4~g", y_title="Trillion tokens per week (log)", height=300, log=True,
                        legend=False, date_fmt="%b %Y"))
        st.caption("One aggregator, not the whole market.")
    l, r = st.columns(2)
    with l:
        st.subheader("Korean chip exports keep setting records")
        k = pd.DataFrame(ref.KOREA_CHIP_RECORDS, columns=["Month", "value"])
        show(name="korea_chip_exports", chart=cat_bars(k, "Month", "value", fmt="$,.1f", y_title="$B per month", highlight_last=True))
        st.caption("2026 monthly records only (Jan, Apr and Jul were not records).")
    with r:
        st.subheader("TSMC monthly revenue")
        tm = pd.DataFrame(ref.TSMC_MONTHLY, columns=["Month", "value", "yoy"])
        tm["Month"] = pd.to_datetime(tm["Month"] + "-01").dt.strftime("%b %Y")
        show(name="tsmc_monthly_revenue", chart=cat_bars(tm, "Month", "value", fmt=",.0f", y_title="NT$ billions", highlight_last=True))
        st.caption("YoY: " + ", ".join(f"{m} {y:+.1f}%" for m, _, y in tm.itertuples(index=False)) + ".")
    st.subheader("Share of US firms using AI")
    bt = pd.DataFrame(ref.BTOS_AI_USE, columns=["date", "value"])
    bt["date"], bt["Series"] = pd.to_datetime(bt["date"]), "Firms using AI"
    show(name="btos_ai_use", chart=line_chart(bt, fmt=".1f", y_title="% of firms, past two weeks", height=240, legend=False, zero=True,
                    date_fmt="%b %d, %Y"))
    st.caption("Census BTOS: used AI in any business function. The question was broadened in Nov 2025.")
    st.subheader("Token prices")
    ti = ref.TOKEN_INDEX
    c = st.columns(4)
    tile(c[0], "Frontier token price index", f"{ti['frontier']}", f"{ti['frontier_yoy_pct']:+.0f}% YoY",
         help=f"BenchLM median flagship price, {ti['base']}.")
    tile(c[1], "Mid-tier token price index", f"{ti['mid']}", f"{ti['mid_yoy_pct']:+.1f}% YoY")
    tile(c[2], "Median API price, per 1M tokens", f"${ti['median_input']:.2f} in", f"${ti['median_output']:.2f} out")
    tile(c[3], "Price fall at fixed capability", "~40× per year", "range 9× to 900× (Epoch AI)")
    st.markdown("**Silicon Data LLM Token Expenditure Index (SDLLMTK)**")
    sd = pd.DataFrame([(d, v, n) for d, v, n, _ in ref.SDLLMTK], columns=["date", "value", "note"])
    sd["date"] = pd.to_datetime(sd["date"])
    peak = sd.loc[sd["value"].idxmax()]
    c = st.columns(3)
    tile(c[0], f"SDLLMTK, {sd['date'].iloc[-1]:%b %d, %Y}", f"${sd['value'].iloc[-1]:.2f}",
         f"{sd['value'].iloc[-1] / peak['value'] - 1:+.0%} vs {peak['date']:%b} peak", delta_color="inverse",
         help="Usage-weighted blended price per 1M tokens across 20+ actively used models.")
    tile(c[1], f"Peak, {peak['date']:%b %Y}", f"${peak['value']:.2f}")
    tile(c[2], "Since launch (Dec 2025)", f"{sd['value'].iloc[-1] / sd['value'].iloc[0] - 1:+.0%}")
    sd_line = alt.Chart(sd).mark_line(color=BLUE, strokeWidth=2, point=alt.OverlayMarkDef(color=BLUE, size=60)).encode(
        x=time_axis(sd), y=alt.Y("value:Q", title="$ per 1M tokens", scale=alt.Scale(zero=True)),
        tooltip=[alt.Tooltip("date:T", format="%b %d, %Y", title="Date"),
                 alt.Tooltip("value:Q", format="$.2f", title="SDLLMTK"), alt.Tooltip("note:N", title="Reading")])
    sd_lab = alt.Chart(sd).mark_text(dy=-12, fontSize=11, fontWeight="bold", color=LABEL_INK).encode(
        x="date:T", y="value:Q", text=alt.Text("value:Q", format="$.2f"))
    show(name="silicon_data_token_index", chart=axis_cfg((sd_line + sd_lab).properties(height=260)))
    st.caption("Points are the dated readings reported publicly (the daily series is on Bloomberg and the Silicon "
               "Data portal); lines connect them, so they don't show day-to-day moves. Because the index is "
               "expenditure-weighted, it also falls when usage shifts to cheaper models.")

    st.markdown("**Price of a fixed capability**")
    tp = pd.DataFrame(ref.TOKEN_PRICE_GPT4, columns=["date", "value", "model"])
    tp["date"] = pd.to_datetime(tp["date"])
    ch = alt.Chart(tp).mark_line(color=BLUE, strokeWidth=2, point=alt.OverlayMarkDef(color=BLUE, size=60)).encode(
        x=time_axis(tp), y=alt.Y("value:Q", scale=alt.Scale(type="log"), title="$ per 1M tokens (log scale)"),
        tooltip=[alt.Tooltip("date:T", format="%b %Y"), "model:N", alt.Tooltip("value:Q", format="$.2f")])
    lab = alt.Chart(tp).mark_text(align="left", dx=8, dy=-8, fontSize=11, color=LABEL_INK).encode(
        x="date:T", y="value:Q", text="model:N")
    show(name="token_price_gpt4_level", chart=axis_cfg((ch + lab).properties(height=280, padding={"right": 90})))
    st.caption("Cheapest model matching GPT-4 on MMLU. Flagship prices have risen over the past year even as the "
               "price of a fixed capability collapsed.")
    sources_box(refs=[nv["source"], ref.TSMC_SOURCE, ref.KOREA_SOURCE, ref.DRAM["source"], ref.AI_REVENUE_SOURCE,
                      ref.BTOS_SOURCE] + list(dict.fromkeys(o[3] for o in ref.OPENROUTER))
                + ref.CLOUD_SOURCES + [ref.CAPEX_SOURCE] + list(dict.fromkeys(x[5] for x in ref.AI_DISCLOSURES))
                + list(dict.fromkeys(x[3] for x in ref.SDLLMTK)) + [ref.EPOCH, ref.BENCHLM])


# ---------------------------------------------------------------------------
# Page 5: Compute prices
# ---------------------------------------------------------------------------
def load_ornn() -> tuple:
    """Daily Ornn index (saved on disk, refreshed once a day after 5 pm ET). Returns (frame, error or "")."""
    try:
        return _stored("ornn_gpu_index", _download_ornn, "Updating the GPU rental index (once a day)...")
    except Exception as e:  # nothing saved yet and the API is down: the page falls back to saved readings
        return pd.DataFrame(columns=["gpu", "date", "value"]), str(e)


def _download_ornn() -> tuple:
    """Daily Ornn index for each GPU on the public API (no key; trailing 3 months).
    Returns (long frame gpu/date/value, error message or "")."""
    frames, errs = [], []
    for chip, name in ORNN_GPUS.items():
        try:
            r = requests.get(f"{ORNN_API}/gpu/{requests.utils.quote(name)}/index-history",
                             headers=BROWSER_HEADERS, timeout=(10, 30))
            r.raise_for_status()
            rows = r.json().get("data") or []
            d = pd.DataFrame(rows)
            if d.empty or not {"timestamp", "index_value"} <= set(d.columns):
                raise ValueError("empty response")
            d = pd.DataFrame({"gpu": chip,
                              "date": pd.to_datetime(d["timestamp"], utc=True).dt.tz_localize(None).dt.normalize(),
                              "value": pd.to_numeric(d["index_value"], errors="coerce")}).dropna()
            frames.append(d.groupby(["gpu", "date"], as_index=False)["value"].last())
        except Exception as e:  # network, rate limit, schema change
            errs.append(f"{chip}: {e}")
    if not frames:
        raise RuntimeError("; ".join(errs) or "no data")   # keep the last saved copy instead
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["gpu", "date"]), "; ".join(errs)


def compute_page():
    st.title("Compute prices: what it costs to rent an AI chip")
    st.caption("On-demand rental price per GPU-hour. Rising prices mean demand is outrunning new supply; falling "
               "prices on older chips would be the first sign of a glut. Indices differ in method (Silicon Data "
               "standardizes a blend of rentals, Ornn publishes a daily settle, Compute Desk uses verified US "
               "neocloud transactions), so compare trends within a source rather than levels across them. "
               f"Reference readings as of {ref.COMPUTE_AS_OF}.")
    latest = pd.DataFrame(ref.GPU_RENTAL_LATEST, columns=["Chip", "Generation", "Launched", "Neocloud",
                                                          "7-day %", "Hyperscaler", "Ornn", "Note"])
    desk = pd.DataFrame(ref.DESK_B300, columns=["date", "value", "note"])
    desk["date"] = pd.to_datetime(desk["date"])
    live, err = load_ornn()

    # Ornn: live where the API answered, saved points for the rest and for the earlier history.
    saved = pd.DataFrame([(g, d, v) for g, d, v, _, _ in ref.ORNN_HISTORY], columns=["gpu", "date", "value"])
    saved["date"] = pd.to_datetime(saved["date"])
    if not live.empty:
        cut = live.groupby("gpu")["date"].min()
        saved = saved[saved.apply(lambda r: r["gpu"] not in cut or r["date"] < cut[r["gpu"]], axis=1)]
    ornn = pd.concat([saved, live], ignore_index=True).sort_values(["gpu", "date"])
    ornn_last = ornn.groupby("gpu").tail(1).set_index("gpu")
    if not live.empty:
        for chip, row in ornn_last.iterrows():
            latest.loc[latest["Chip"] == chip, "Ornn"] = round(float(row["value"]), 2)

    def ornn_chg(chip, days):
        """Change over `days`; if no reading lies within 5 days of that, say which date it's measured from."""
        s = ornn[ornn["gpu"] == chip].set_index("date")["value"]
        target = s.index[-1] - pd.Timedelta(days=days) if len(s) else None
        past = s[s.index <= target] if len(s) else s
        if past.empty:
            return None
        chg = s.iloc[-1] / past.iloc[-1] - 1
        near = (target - past.index[-1]).days <= 5
        return f"{chg:+.1%} in {days} days" if near else f"{chg:+.1%} since {past.index[-1]:%b %d}"

    c = st.columns(4)
    lo, hi = desk.iloc[0], desk.iloc[-1]
    tile(c[0], f"B300 (Compute Desk), {hi['date']:%b %d}", f"${hi['value']:.2f}",
         f"{hi['value'] / lo['value'] - 1:+.0%} vs {lo['date']:%b %Y} low",
         help="Record high after 17 straight daily gains, per the DESKB300 Bloomberg chart.")
    for col, chip in zip(c[1:3], ["B200", "H200"]):
        if chip in ornn_last.index:
            tile(col, f"{chip} (Ornn), {ornn_last.loc[chip, 'date']:%b %d}", f"${ornn_last.loc[chip, 'value']:.2f}",
                 ornn_chg(chip, 30))
    h = latest.set_index("Chip").loc["H100"]
    tile(c[3], "H100 (Silicon Data neocloud)", f"${h['Neocloud']:.2f}", f"{h['7-day %']:+.1f}% in 7 days",
         help=f"Hyperscalers: ${h['Hyperscaler']:.2f}/hr.")
    if err and live.empty:
        st.caption("Couldn't reach Ornn's live API, so Ornn figures are the saved readings.")

    st.subheader("Nvidia chips: newest rents at a record, every generation rising")
    nv_order = ["B300", "B200", "H200", "H100", "A100"]          # newest to oldest
    nv = pd.concat([desk[["date", "value"]].assign(Series="B300 (Compute Desk)")]
                   + [ornn[ornn["gpu"] == g][["date", "value"]].assign(Series=f"{g} (Ornn)") for g in nv_order[1:]],
                   ignore_index=True)
    names = [n for n in [f"{g} ({'Compute Desk' if g == 'B300' else 'Ornn'})" for g in nv_order] if n in set(nv["Series"])]
    show(name="nvidia_rental_prices", chart=line_chart(nv, fmt="$.2f", y_title="$ per GPU-hour", height=380,
                                                        colors=[GPU_COLORS[n.split()[0]] for n in names]))
    st.caption("Each line is one Nvidia chip, newest (B300, Blackwell Ultra) to oldest (A100, 2020). B300 is Compute "
               "Desk's DESKB300 index (Bloomberg), from verified US neocloud transactions: the Nov 3, 2025 low and the "
               "Oct 14, 2026 record are stated on its chart, the points between are read off it and approximate. The other "
               "chips are Ornn's daily index, which starts in July on the free API (B200 has two spring readings via "
               "Tomasz Tunguz), so their lines begin later. The two sources measure differently: compare each line's "
               "trend rather than B300's level against the others. Silicon Data's standardized B300 index is $"
               + f"{latest.set_index('Chip').loc['B300', 'Neocloud']:.2f}. AMD's MI300X isn't tracked daily; see the table.")

    st.subheader("Every generation costs more to rent")
    bars = latest.melt(id_vars="Chip", value_vars=["Neocloud", "Ornn"], var_name="Index", value_name="value").dropna()
    bars["Index"] = bars["Index"].replace({"Neocloud": "Silicon Data neocloud"})
    show(name="gpu_rental_by_chip", chart=grouped_bars(
        bars, cat="Chip", group="Index", value="value", groups=["Silicon Data neocloud", "Ornn"],
        colors=[BLUE, ORANGE], fmt="$.2f", x_title="$ per GPU-hour", sort=list(latest["Chip"])))
    st.caption("Newest chip at the top. Ornn doesn't cover B300 or MI300X. New to these chips? See "
               "\"What these chips are\" under the table below.")

    st.subheader("Rental prices, newest to oldest chip")
    tbl = latest.copy()
    money = lambda v: "—" if pd.isna(v) else f"${v:.2f}"
    for col_ in ["Neocloud", "Hyperscaler", "Ornn"]:
        tbl[col_] = tbl[col_].map(money)
    tbl["7-day %"] = tbl["7-day %"].map(lambda v: "—" if pd.isna(v) else f"{v:+.1f}%")
    tbl = tbl.rename(columns={"Neocloud": "Silicon Data neocloud", "Hyperscaler": "Silicon Data hyperscaler",
                              "7-day %": "SD 7-day"})
    html_table(tbl, hide_index=True)
    st.download_button("⬇ Download CSV", latest.to_csv(index=False).encode(),
                       file_name=f"gpu_rental_latest_{date.today():%Y-%m-%d}.csv", mime="text/csv",
                       key="dl_gpu_rental_latest")

    st.markdown("**What these chips are**")
    guide = pd.DataFrame(ref.CHIP_GUIDE, columns=["Chip", "Maker", "Generation", "Announced", "Shipping in volume",
                                                  "Memory", "What it is"])
    html_table(guide, hide_index=True)
    st.caption("A GPU (graphics processing unit) is the chip that trains and runs AI models; companies rent them by "
               "the hour from clouds rather than buying them outright. Nvidia names each generation after a scientist "
               "(Ampere 2020, Hopper 2022, Blackwell 2024), and newer generations are faster, so each one rents for "
               "more. Memory (HBM) decides how big a model fits on one chip, so more memory = bigger models. "
               "**Neocloud** = specialist GPU renters such as CoreWeave, Nebius and Lambda; **hyperscaler** = Amazon, "
               "Microsoft, Google and Oracle, which charge more but bundle in their other cloud services. A **GPU-hour** "
               "is one chip rented for one hour; a large AI training run uses tens of thousands of chips for weeks.")
    sources_box(refs=[ref.COMPUTE_DESK, ref.CRYPTOBRIEFING, ref.SILICON_INDEX, ref.SILICON_B300, ref.ORNN,
                      ref.ORNN_B200, ref.ORNN_H200, ref.TUNGUZ],
                notes=["Live: Ornn public API (api.ornnai.com, no key) for B200, H200, H100 SXM and A100 SXM4. "
                       "Saved once a day with the rest of the data. Everything else is in ai_boom_reference.py; update GPU_RENTAL_LATEST and DESK_B300 there.",
                       "Silicon Data's full daily history and the Compute Desk series are on Bloomberg "
                       "(SDH100RT, SDA100RT, SDB200RT, DESKB300 Index) or by subscription."])




# ---------------------------------------------------------------------------
# Page 6: Labor market
# ---------------------------------------------------------------------------
def labor_page():
    st.title("Labor market impact")
    st.caption("Where AI should show up first: young and entry-level workers, tech and software jobs, and the "
               "split of output between workers and capital. BLS and Indeed via FRED; Challenger and New York Fed "
               f"as reference figures ({ref.AS_OF}).")
    raw = fred_or_stop(tuple(LABOR), f"{start_year - 2}-01-01")
    u, y, csd, dp, info, sw = (ser(raw, s) for s in LABOR)
    c = st.columns(6)
    tile(c[0], f"Unemployment rate, {u.index[-1]:%b %Y}", f"{last_val(u):.1f}%",
         f"{last_val(u) - last_val(u, -2):+.1f}pp", delta_color="inverse")
    tile(c[1], "Unemployment, age 16-24", f"{last_val(y):.1f}%", f"{last_val(y) - last_val(y, -13):+.1f}pp YoY",
         delta_color="inverse")
    g = ref.NYFED_GRADS
    tile(c[2], f"Recent grads (22-27), {g['month']}", f"{g['rate']}%", f"all workers {g['all_workers']}%",
         help="New York Fed, bachelor's degree or higher.")
    tile(c[3], "Computer systems design jobs", f"{last_val(csd):,.0f}k", f"{last_val(yoy(csd, 12)):+.1f}% YoY",
         delta_color="normal")
    tile(c[4], "Software postings (Indeed)", f"{last_val(sw):.1f}", f"{last_val(sw) - 100:+.1f} vs Feb 2020",
         help="Index, Feb 1, 2020 = 100.", delta_color="normal")
    tile(c[5], "Job cuts citing AI, 2026 YTD", f"{ref.AI_JOB_CUTS_YTD[-1][1]:,}",
         f"2025 total {ref.AI_JOB_CUTS_2025:,}", help="Challenger, through August.")

    l, r = st.columns(2)
    with l:
        st.subheader("Unemployment: young workers vs all")
        show(name="unemployment_young_vs_all", chart=line_chart(window(to_long({"Age 16-24": y, "All workers": u})), fmt=".1f", y_title="Percent",
                        height=280, colors=[ORANGE, BLUE], date_fmt="%b %Y"))
    with r:
        st.subheader("Software development postings")
        show(name="software_postings", chart=line_chart(window(to_long({"Indeed software postings": sw})), fmt=".1f", y_title="Index, Feb 2020 = 100",
                        height=280, legend=False, ref_y=100))
        st.caption("Most of the 2026 rebound is senior and AI-titled roles (Indeed Hiring Lab).")

    st.subheader("Tech employment, year over year")
    st.caption("% change from 12 months earlier, payroll survey.")
    show(name="tech_employment_yoy", chart=line_chart(window(to_long({"Computer systems design": yoy(csd, 12), "Data processing & hosting": yoy(dp, 12),
                                    "Information sector": yoy(info, 12)})), fmt="+.1f", y_title="% YoY", height=300,
                    zero=True, date_fmt="%b %Y"))

    l, r = st.columns(2)
    with l:
        st.subheader("Announced job cuts citing AI")
        cuts = pd.DataFrame(ref.AI_JOB_CUTS_YTD, columns=["Month", "value"])
        show(name="ai_job_cuts", chart=cat_bars(cuts, "Month", "value", fmt=",.0f", y_title="2026 year to date", height=280,
                      ref_y=ref.AI_JOB_CUTS_2025, ref_label=f"All of 2025: {ref.AI_JOB_CUTS_2025:,}"))
        st.caption(f"Tech-sector cuts through August: {ref.TECH_JOB_CUTS_YTD_AUG['value']:,} "
                   f"({ref.TECH_JOB_CUTS_YTD_AUG['yoy_pct']:+d}% YoY). AI-cited share of all cuts ≈ 22%.")
    with r:
        st.subheader("Who gets the output")
        ls = ref.LABOR_SHARE
        tile(st, f"Labor share of output, {ls['quarter']}", f"{ls['value']}%", ls["note"])
        st.caption("Productivity is rising faster than pay; so far the gains are flowing to capital.")
    st.download_button("Download labor series (CSV)",
                       raw.pivot_table(index="date", columns="name", values="value").reset_index().to_csv(index=False).encode(),
                       file_name="ai_boom_labor.csv", mime="text/csv")
    sources_box(tuple(LABOR), refs=[g["source"], ref.CHALLENGER, ref.LABOR_SHARE["source"]],
                notes=[f"New York Fed college labor market page: {g['page']}"])


# ---------------------------------------------------------------------------
# App entry point: shared sidebar + page navigation
# ---------------------------------------------------------------------------
def _server_key(name: str) -> str:
    """Key from an environment variable or Streamlit secrets (for hosted deployments)."""
    key = os.environ.get(name, "")
    if not key:
        try:
            key = st.secrets.get(name, "")
        except Exception:
            key = ""
    return str(key).strip()


st.set_page_config(page_title="AI Boom Dashboard", layout="wide")

with st.sidebar:
    srv_fred, srv_fmp = _server_key("FRED_API_KEY"), _server_key("FMP_API_KEY")
    fred_key = st.text_input("FRED API key (optional)", type="password", key="fred_key",
                             placeholder="Using the saved key" if srv_fred else "Paste your key",
                             help="Free from fred.stlouisfed.org → My Account → API Keys. Or set FRED_API_KEY.").strip() or srv_fred
    fmp_key = st.text_input("FMP API key (optional)", type="password", key="fmp_key",
                            placeholder="Using the saved key" if srv_fmp else "Paste your key",
                            help="Financial Modeling Prep, for stock prices and cash flows. Without it (or for "
                                 "symbols your plan doesn't cover) the app uses Yahoo Finance. Or set FMP_API_KEY.").strip() or srv_fmp
    if st.button("Refresh data", help="Download everything again now. Otherwise data updates once a day "
                                      "after 5 pm ET (the first visit after that downloads only what's new)."):
        store.forget_all()
        st.cache_data.clear()
    _lr = store.last_refresh()
    st.caption((f"Data saved {_lr:%a %b %d, %I:%M %p} ET" if _lr else "No data saved yet")
               + f" · next update after {store.next_cutoff():%a %b %d}, 5 pm ET")
    st.divider()
    st.header("Settings")
    start_year = st.slider("Show data from", 2015, date.today().year, 2022, key="start_year",
                           help="Charts start in January of this year.")

pages = st.navigation([
    st.Page(real_economy_page, title="Real economy", url_path="real-economy", default=True),
    st.Page(firm_page, title="Firm level", url_path="firms"),
    st.Page(markets_page, title="Financial markets", url_path="markets"),
    st.Page(leading_page, title="Leading signals", url_path="leading"),
    st.Page(compute_page, title="Compute prices", url_path="compute"),
    st.Page(labor_page, title="Labor market", url_path="labor"),
])
pages.run()
