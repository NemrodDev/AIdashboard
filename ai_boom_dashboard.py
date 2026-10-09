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
  5. Labor market      Young-worker and tech unemployment/employment, software postings,
                       AI-attributed job cuts

Live data: FRED (BEA, Census, Fed, BLS, ICE BofA, Indeed), Our World in Data (data center
construction), Financial Modeling Prep if you add a key (otherwise Yahoo Finance via yfinance).
Figures without a free feed live in ai_boom_reference.py, each with its source.

Run:   py -m streamlit run ai_boom_dashboard.py
Needs: pip install streamlit altair pandas requests yfinance
"""

import io
import os
import time
from datetime import date

import altair as alt
import pandas as pd
import requests
import streamlit as st

import ai_boom_reference as ref

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
                **TRADE_NOMINAL, **GDP_GROWTH, **MONTHLY_REAL, **PRODUCTIVITY, **CREDIT, **LABOR}

AI_TICKERS = {
    "NVDA": "Nvidia", "AVGO": "Broadcom", "TSM": "TSMC", "AMD": "AMD", "MU": "Micron",
    "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta", "ORCL": "Oracle",
    "CRWV": "CoreWeave", "VRT": "Vertiv", "QQQ": "Nasdaq-100 ETF",
}
DEFAULT_TICKERS = ["NVDA", "AVGO", "TSM", "MSFT", "GOOGL", "AMZN", "META", "ORCL", "QQQ"]
HYPERSCALERS = {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "META": "Meta", "ORCL": "Oracle"}

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


@st.cache_data(ttl=6 * 60 * 60, show_spinner="Downloading data from FRED...")
def load_series(ids: tuple, start: str, api_key: str = "") -> tuple:
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
@st.cache_data(ttl=12 * 60 * 60, show_spinner="Downloading data center construction...")
def load_data_centers() -> tuple:
    """Monthly private data center construction, $B constant 2021 dollars, not seasonally adjusted.
    Falls back to the snapshot in ai_boom_reference.py."""
    try:
        resp = _get(OWID_DC_CSV, {"v": 1, "csvType": "full", "useColumnShortNames": "false"},
                    headers=BROWSER_HEADERS, tries=2, timeout=(10, 30))
        d = pd.read_csv(io.StringIO(resp.text))
        d = d[d["Entity"] == "United States"]
        val_col = [c for c in d.columns if c not in ("Entity", "Code", "Month", "Year", "Day")][0]
        out = pd.DataFrame({"date": pd.to_datetime(d["Month"].astype(str).str[:7] + "-01"),
                            "value": pd.to_numeric(d[val_col], errors="coerce") / 1e9})
        return out.dropna().sort_values("date"), "live"
    except Exception:
        snap = pd.DataFrame(ref.DC_SNAPSHOT, columns=["month", "value"])
        snap["date"] = pd.to_datetime(snap["month"] + "-01")
        return snap[["date", "value"]], "snapshot"


# ---------------------------------------------------------------------------
# Data: stock prices and cash flows (FMP if a key is set, else Yahoo Finance)
# ---------------------------------------------------------------------------
def _fmp(path, params, key):
    resp = _get(f"{FMP_BASE}/{path}", {**params, "apikey": key}, tries=2, timeout=(10, 30))
    data = resp.json()
    if isinstance(data, dict) and ("Error Message" in data or "error" in data):
        raise RuntimeError(str(data)[:200])
    return data


@st.cache_data(ttl=30 * 60, show_spinner="Fetching stock prices...")
def load_prices(tickers: tuple, start: str, fmp_key: str = "") -> tuple:
    """Daily closes, long frame: date, symbol, close. Returns (frame, {symbol: source}, failed)."""
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


@st.cache_data(ttl=6 * 60 * 60, show_spinner="Fetching cash-flow statements...")
def load_cash_flows(tickers: tuple, fmp_key: str = "") -> tuple:
    """Quarterly capex, operating cash flow, free cash flow, net debt issued ($B)."""
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
    d["company"] = d["symbol"].map(HYPERSCALERS)
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
                    height=360, date_fmt="%Y Q%q"):
    """Stacked bars for components (positive and negative stack separately), a black net line
    across components and optional dots for a total (e.g. real GDP growth)."""
    long = parts.reset_index().melt(id_vars="date", var_name="Component", value_name="value").dropna()
    if long.empty:
        return None
    comps = list(parts.columns)
    colors = CATEGORICAL[: len(comps)]
    if "Net imports of computers & parts" in comps:
        colors[comps.index("Net imports of computers & parts")] = BAD
    color = alt.Color("Component:N", scale=alt.Scale(domain=comps, range=colors), sort=comps,
                      legend=alt.Legend(title=None, orient="top", columns=3, labelLimit=320))
    bars = alt.Chart(long).mark_bar(opacity=0.9, size=14).encode(
        x=time_axis(long), y=alt.Y("sum(value):Q", stack="zero", title="Percentage points"),
        color=color, order=alt.Order("Component:N"),
        tooltip=[alt.Tooltip("date:T", format=date_fmt, title="Quarter"), "Component:N",
                 alt.Tooltip("value:Q", format=fmt, title="pp")])
    net = parts.sum(axis=1, min_count=1).rename("value").reset_index()
    net_line = alt.Chart(net).mark_line(color="#3b3a37", strokeWidth=2, point=alt.OverlayMarkDef(
        color="#3b3a37", size=30)).encode(x="date:T", y="value:Q", tooltip=[
            alt.Tooltip("date:T", format=date_fmt, title="Quarter"), alt.Tooltip("value:Q", format=fmt, title="Net, pp")])
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


def show(chart):
    if chart is None:
        st.caption("No data for this chart yet.")
    else:
        st.altair_chart(chart)


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

    # --- Investment lines ----------------------------------------------------
    st.subheader("Investment series used as the AI proxy")
    st.caption("Software and R&D are intellectual property products; computers & peripherals sit inside "
               "information-processing equipment, which sits inside the broad A679RC aggregate. "
               "Communication equipment is left out: it mixes networking gear with phones and broadcast gear.")
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
    show(line_chart(window(to_long(m)), fmt=fmt, y_title=yt, height=340, zero=measure != "Level ($B)",
                    date_fmt="%Y Q%q"))

    # --- Contributions -------------------------------------------------------
    st.subheader("Contribution to real GDP growth, by quarter")
    st.caption("Bars = BEA contributions (pp at annual rate) for each line, with the import offset computed "
               "as lagged share of GDP × real growth of net imports of computers, peripherals and parts. "
               "Black line = net AI-proxy contribution. Orange diamonds = total real GDP growth.")
    cw = contrib[contrib.index >= pd.Timestamp(f"{start_year}-01-01")]
    show(stacked_contrib(cw, gdp_g, "Real GDP growth"))
    if not contrib.empty:
        tbl = contrib.tail(6).copy()
        tbl["Net AI proxy"] = tbl.sum(axis=1)
        tbl["Real GDP growth"] = gdp_g.reindex(tbl.index)
        tbl["AI share of growth"] = tbl["Net AI proxy"] / tbl["Real GDP growth"] * 100
        tbl.index = [qlabel(i) for i in tbl.index]
        st.dataframe(tbl.T.style.format("{:+.2f}", na_rep="—").format(
            "{:.0f}%", subset=pd.IndexSlice[["AI share of growth"], :], na_rep="—"))

    # --- Fed-style year-over-year proxy ---------------------------------------
    st.subheader("Buildout proxy, year over year (Federal Reserve method)")
    st.caption("Software + computers & peripherals + data centers + power facilities − net imports of computers "
               "and parts, as a contribution to real GDP growth over four quarters. Structures come from Census "
               "C30 (data centers in constant dollars via OWID; power in nominal terms).")
    proxy = yoy_buildout_proxy(raw, dc, trade_w)
    gdpc = ser(raw, "GDPC1")
    gdp_yoy = yoy(gdpc, 4)
    pw = proxy[proxy.index >= pd.Timestamp(f"{start_year}-01-01")]
    show(stacked_contrib(pw, gdp_yoy, "Real GDP growth, YoY %"))
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
    st.subheader("Structures outside the NIPA lines (Census C30)")
    l, r = st.columns(2)
    with l:
        dcw = window(dc).assign(Series="Monthly")
        roll = dc.set_index("date")["value"].rolling(12).mean()
        dcw = pd.concat([dcw, window(to_long({"12-month average": roll}))])
        show(line_chart(dcw, fmt=",.2f", y_title="$B per month, 2021 dollars", height=280,
                        colors=[BLUE, MA_COLOR], dashed=["Monthly"], date_fmt="%b %Y"))
        st.caption(f"Data center construction, not seasonally adjusted. Source: "
                   f"{'Our World in Data (live)' if dc_src == 'live' else 'snapshot in ai_boom_reference.py'}. "
                   "Excludes the servers inside.")
    with r:
        power = ser(raw, "PRPWRCONS") / 1000
        show(line_chart(window(to_long({"Power construction": power})), fmt=",.1f",
                        y_title="$B, annual rate", height=280, legend=False, date_fmt="%b %Y"))
        st.caption(f"Private power construction, latest {last_val(yoy(power, 12)):+.1f}% YoY. "
                   "Included in the Fed's buildout proxy.")

    # --- Trade and domestic production ---------------------------------------
    st.subheader("Import offset and domestic production")
    l, r = st.columns(2)
    with l:
        show(line_chart(window(to_long({"Imports": imp_n, "Exports": exp_n, "Net imports": imp_n - exp_n})),
                        fmt=",.0f", y_title="$B, annual rate", height=280, colors=[ORANGE, BLUE, BAD],
                        date_fmt="%Y Q%q"))
        st.caption("Computers, peripherals and parts (NIPA end-use goods). Used only as an offset, so imported "
                   "hardware is not counted as domestic GDP.")
    with r:
        show(line_chart(window(to_long({"Semiconductors (NAICS 3344)": ip})), fmt=",.1f",
                        y_title="Index, 2017 = 100", height=280, legend=False, date_fmt="%b %Y"))
        st.caption("Industrial production of semiconductors and other electronic components (Fed G.17).")

    st.subheader("Use and productivity")
    prod = ser(raw, "PRS85006092")
    show(bar_time(window(pd.DataFrame({"date": prod.index, "value": prod.values})), fmt="+.1f",
                  y_title="% change at annual rate", height=240, date_fmt="%Y Q%q"))
    st.caption("Nonfarm business labor productivity (BLS). Utilization-adjusted TFP has been roughly flat, "
               "so there is no clear AI productivity signal in the aggregate yet.")

    st.download_button("Download real-economy series (CSV)",
                       raw.pivot_table(index="date", columns="name", values="value").reset_index().to_csv(index=False).encode(),
                       file_name=f"ai_boom_real_economy_{date.today():%Y_%m_%d}.csv", mime="text/csv")
    sources_box(REAL_ECON_IDS, refs=[ref.DC_SOURCE, ref.DC_NOMINAL_LATEST["source"], fed["source"]], notes=[
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
    st.caption("Quarterly cash-flow statements (FMP if a key is set, otherwise Yahoo Finance), company capex "
               f"guidance and bond issuance (reference figures as of {ref.AS_OF}).")
    cf, src = load_cash_flows(tuple(HYPERSCALERS), fmp_key)

    c = st.columns(len(ref.FIRM_FACTS))
    for col, (label, value, detail, s) in zip(c, ref.FIRM_FACTS):
        tile(col, label, value, help=f"{detail} Source: {s[0]}")

    st.subheader("Capex against operating cash flow")
    if cf.empty:
        st.warning("Couldn't load cash-flow statements. Add an FMP key in the sidebar or check that yfinance is installed.")
    else:
        st.caption("$B per quarter. Capex = purchases of property and equipment (excludes finance leases, so it "
                   "runs below company-reported capex). Free cash flow = operating cash flow − capex.")
        cols = st.columns(len(HYPERSCALERS))
        for col, (sym, name) in zip(cols, HYPERSCALERS.items()):
            d = cf[cf["symbol"] == sym]
            with col:
                if d.empty:
                    st.markdown(f"**{name}**")
                    st.caption("Not available")
                    continue
                long = pd.concat([d.assign(Series="Capex", value=d["capex"]),
                                  d.assign(Series="Operating cash flow", value=d["ocf"])])
                long["q"] = long["quarter"].apply(qlabel)
                ch = alt.Chart(long).mark_bar(cornerRadiusEnd=3).encode(
                    x=alt.X("q:N", title=None, axis=alt.Axis(labelAngle=-45)),
                    xOffset="Series:N", y=alt.Y("value:Q", title=None),
                    color=alt.Color("Series:N", scale=alt.Scale(domain=["Capex", "Operating cash flow"],
                                                                range=[BLUE, MA_COLOR]),
                                    legend=alt.Legend(title=None, orient="top") if sym == "MSFT" else None),
                    tooltip=["q:N", "Series:N", alt.Tooltip("value:Q", format=",.1f", title="$B")])
                show(axis_cfg(ch.properties(title=name, height=220)))
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
        st.dataframe(t.reset_index(drop=True).style.format({**{m: "${:,.1f}B" for m in money},
                                                            "Capex / OCF %": "{:.0f}%"}, na_rep="—")
                     .map(neg_red, subset=["Free cash flow", "FCF TTM"]), hide_index=True)

    l, r = st.columns(2)
    with l:
        st.subheader("2026 capex guidance kept rising")
        g = pd.DataFrame([(co, lab, v) for co, j, a, ju, _ in ref.CAPEX_GUIDANCE
                          for lab, v in [("Jan 2026", j), ("Apr 2026", a), ("Jul 2026", ju)]],
                         columns=["Company", "Guide", "Capex"])
        show(grouped_bars(g, "Company", "Guide", "Capex", ["Jan 2026", "Apr 2026", "Jul 2026"],
                          ["#c9c7c0", MA_COLOR, BLUE], fmt="$,.0f", x_title="$B (midpoint of range)"))
        st.caption("Microsoft's July guide is lower only because data center leases moved from finance to "
                   "operating leases (~$190B like-for-like).")
    with r:
        st.subheader("Hyperscaler bond issuance")
        b = pd.DataFrame(ref.HYPERSCALER_BONDS, columns=["Year", "Issuance", "Share of US IG supply %"])
        show(cat_bars(b, "Year", "Issuance", fmt="$,.0f", y_title="$B", height=300, highlight_last=True))
        st.caption("Alphabet, Amazon, Meta, Microsoft and Oracle. Share of US investment-grade supply: "
                   + ", ".join(f"{y} {s}%" for y, _, s in ref.HYPERSCALER_BONDS[-3:]) + ".")

    sources_box(refs=[ref.PLATFORMONOMICS, ref.VANGUARD_BONDS] + [f[3] for f in ref.FIRM_FACTS],
                notes=["Cash flows: " + ", ".join(f"{k} {v}" for k, v in src.items()) if src else "Cash flows: none loaded"])


# ---------------------------------------------------------------------------
# Page 3: Financial markets
# ---------------------------------------------------------------------------
def markets_page():
    st.title("Financial markets: stocks, credit and token prices")
    st.caption("Daily closes from FMP (with a key) or Yahoo Finance; ICE BofA option-adjusted spreads via FRED; "
               f"ratings, hyperscaler spreads and token prices are reference figures as of {ref.AS_OF}.")
    with st.sidebar:
        tickers = st.multiselect("AI stocks", list(AI_TICKERS), default=DEFAULT_TICKERS, key="mk_tickers",
                                 format_func=lambda t: f"{t} · {AI_TICKERS[t]}")
        extra = st.text_input("Other tickers (comma-separated)", key="mk_extra")
        sessions = st.slider("Sessions in daily-move grid", 10, 60, 20, 5, key="mk_sessions")
    tickers = list(dict.fromkeys(tickers + [t.strip().upper() for t in extra.split(",") if t.strip()]))
    names = {t: AI_TICKERS.get(t, t) for t in tickers}

    st.subheader("AI stocks")
    px, psrc, pfail = load_prices(tuple(tickers), f"{min(start_year, date.today().year - 1)}-12-01", fmp_key)
    if px.empty:
        st.warning("Couldn't load prices. Add an FMP key in the sidebar or install yfinance.")
    else:
        px = px.sort_values(["symbol", "date"])
        px["ret"] = px.groupby("symbol")["close"].pct_change() * 100
        ytd0 = pd.Timestamp(date.today().year, 1, 1)
        rows = []
        for t, g in px.groupby("symbol"):
            g = g.set_index("date")["close"]
            base_ytd = g[g.index < ytd0]
            rows.append({"Symbol": t, "Name": names.get(t, t), "Date": g.index[-1].strftime("%b %d"),
                         "Close": g.iloc[-1], "1 day %": (g.iloc[-1] / g.iloc[-2] - 1) * 100 if len(g) > 1 else None,
                         "5 days %": (g.iloc[-1] / g.iloc[-6] - 1) * 100 if len(g) > 5 else None,
                         "1 month %": (g.iloc[-1] / g.iloc[-22] - 1) * 100 if len(g) > 21 else None,
                         "YTD %": (g.iloc[-1] / base_ytd.iloc[-1] - 1) * 100 if len(base_ytd) else None,
                         "From 52-wk high %": (g.iloc[-1] / g.tail(252).max() - 1) * 100,
                         "Source": psrc.get(t, "")})
        tab = pd.DataFrame(rows).set_index("Symbol").reindex([t for t in tickers if t in set(px["symbol"])]).reset_index()

        c = st.columns(min(6, len(tab)))
        for col, (_, r) in zip(c, tab.head(6).iterrows()):
            parts = [f"{r['1 day %']:+.2f}%" if pd.notna(r["1 day %"]) else None,
                     f"YTD {r['YTD %']:+.0f}%" if pd.notna(r["YTD %"]) else None]
            tile(col, f"{r['Name']}, {r['Date']}", f"{r['Close']:,.2f}",
                 " · ".join(p for p in parts if p) or None, delta_color="normal")

        st.markdown(f"**Daily moves, last {sessions} sessions**")
        show(return_heatmap(px, names, sessions))

        st.markdown("**Performance since the start of the window**")
        rebased = px[px["date"] >= pd.Timestamp(f"{start_year}-01-01")].copy()
        rebased["value"] = rebased.groupby("symbol")["close"].transform(lambda s: s / s.iloc[0] * 100)
        rebased["Series"] = rebased["symbol"].map(names)
        show(line_chart(rebased[["date", "Series", "value"]], fmt=",.0f", y_title="Index, first day = 100",
                        height=380, ref_y=100))

        def pos_neg(v):
            if not isinstance(v, (int, float)) or pd.isna(v) or v == 0:
                return ""
            return f"color: {GOOD if v > 0 else BAD}; font-weight: 600"
        pcts = ["1 day %", "5 days %", "1 month %", "YTD %", "From 52-wk high %"]
        st.dataframe(tab.style.format({"Close": "{:,.2f}", **{p: "{:+.2f}%" for p in pcts}}, na_rep="—")
                     .map(pos_neg, subset=pcts), hide_index=True)
        if pfail:
            st.caption(f"No prices for: {', '.join(pfail)}")
        st.download_button("Download prices (CSV)", px.pivot_table(index="date", columns="symbol", values="close")
                           .reset_index().to_csv(index=False).encode(), file_name="ai_stocks_prices.csv", mime="text/csv")

    st.subheader("Credit")
    raw = fred_or_stop(tuple(CREDIT), f"{start_year - 1}-01-01")
    spreads = {CREDIT[s]: ser(raw, s) * 100 for s in CREDIT}
    c = st.columns(4)
    for col, (n, s) in zip(c, spreads.items()):
        chg = last_val(s) - s[s.index <= s.index[-1] - pd.Timedelta(days=90)].iloc[-1] if len(s) > 70 else float("nan")
        tile(col, f"{n}, {s.index[-1]:%b %d}", f"{last_val(s):.0f}bp", f"{chg:+.0f}bp vs 3 months ago",
             delta_color="inverse")
    tile(c[3], "Oracle 5-yr CDS", f"{ref.ORACLE_CDS['latest_bp']}bp+",
         f"vs ~{ref.ORACLE_CDS['year_ago_bp']}bp a year earlier", help=ref.ORACLE_CDS["note"])
    l, r = st.columns([3, 2])
    with l:
        show(line_chart(window(to_long(spreads)), fmt=",.0f", y_title="Basis points over Treasuries", height=320,
                        colors=[BLUE, ORANGE, BAD]))
        st.caption("Hyperscalers sit in the AA bucket, except Oracle (BBB−). High yield shown for context.")
    with r:
        hs = pd.DataFrame([(b, y, v) for b, a, c2 in ref.HYPERSCALER_SPREADS for y, v in [("2025", a), ("2026", c2)]],
                          columns=["Maturity", "Year", "bp"])
        show(grouped_bars(hs, "Maturity", "Year", "bp", ["2025", "2026"], [MA_COLOR, BLUE], fmt=",.4~f",
                          x_title="Median spread, bp"))
        st.caption("Median spreads on Amazon, Alphabet, Meta and Oracle bonds, 2025 vs 2026 issues, and the "
                   "new-issue concession. 78 of 91 2026 bonds traded wider than at issue (Jul 28).")

    st.markdown("**Credit ratings**")
    rt = pd.DataFrame([r[:6] for r in ref.RATINGS], columns=["Company", "S&P", "Moody's", "Notches above junk",
                                                            "As of", "Note"])
    st.dataframe(rt.style.map(lambda v: f"color: {BAD}; font-weight: 700" if v == 0 else "",
                              subset=["Notches above junk"]), hide_index=True)

    st.subheader("Token prices")
    ti = ref.TOKEN_INDEX
    c = st.columns(4)
    tile(c[0], "Frontier token price index", f"{ti['frontier']}", f"{ti['frontier_yoy_pct']:+.0f}% YoY",
         help=f"BenchLM median flagship price, {ti['base']}.")
    tile(c[1], "Mid-tier token price index", f"{ti['mid']}", f"{ti['mid_yoy_pct']:+.1f}% YoY")
    tile(c[2], "Median API price, per 1M tokens", f"${ti['median_input']:.2f} in", f"${ti['median_output']:.2f} out")
    tile(c[3], "Price fall at fixed capability", "~40× per year", "range 9× to 900× (Epoch AI)")
    tp = pd.DataFrame(ref.TOKEN_PRICE_GPT4, columns=["date", "value", "model"])
    tp["date"] = pd.to_datetime(tp["date"])
    ch = alt.Chart(tp).mark_line(color=BLUE, strokeWidth=2, point=alt.OverlayMarkDef(color=BLUE, size=60)).encode(
        x=time_axis(tp), y=alt.Y("value:Q", scale=alt.Scale(type="log"), title="$ per 1M tokens (log scale)"),
        tooltip=[alt.Tooltip("date:T", format="%b %Y"), "model:N", alt.Tooltip("value:Q", format="$.2f")])
    lab = alt.Chart(tp).mark_text(align="left", dx=8, dy=-8, fontSize=11, color=LABEL_INK).encode(
        x="date:T", y="value:Q", text="model:N")
    show(axis_cfg((ch + lab).properties(height=280, padding={"right": 90})))
    st.caption("Cheapest model matching GPT-4 on MMLU. Flagship prices have risen over the past year even as the "
               "price of a fixed capability collapsed.")
    sources_box(tuple(CREDIT), refs=[ref.REUTERS_SPREADS, ref.ORACLE_CDS["source"], ref.EPOCH, ref.BENCHLM]
                + list(dict.fromkeys(r[6] for r in ref.RATINGS)),
                notes=["Prices: " + ", ".join(f"{k} {v}" for k, v in psrc.items())] if not px.empty else [])


# ---------------------------------------------------------------------------
# Page 4: Leading signals
# ---------------------------------------------------------------------------
def leading_page():
    st.title("Leading signals: where the boom is heading")
    st.caption("Chip supply-chain orders lead capex by a quarter or two; AI revenue and token volume test whether "
               f"the spending pays off. Reference figures as of {ref.AS_OF}.")
    nv, ts = ref.NVIDIA, ref.TSMC_MONTHLY[-1]
    c = st.columns(5)
    tile(c[0], "Nvidia next-quarter revenue guide", f"${nv['q3_guide_b']:.0f}B",
         f"Q2 ${nv['q2_fy27_rev_b']}B, {nv['q2_yoy_pct']:+d}% YoY")
    tile(c[1], f"TSMC revenue, {pd.Timestamp(ts[0] + '-01'):%b %Y}", f"NT${ts[1]:.0f}B", f"{ts[2]:+.1f}% YoY")
    tile(c[2], f"Korean chip exports, {ref.KOREA_CHIP_RECORDS[-1][0]} 2026", f"${ref.KOREA_CHIP_RECORDS[-1][1]}B",
         f"{ref.KOREA_CHIP_LATEST_YOY:+.1f}% YoY")
    tile(c[3], "DRAM contract prices, Q4 2026", ref.DRAM["q4_2026_dram_incl_hbm"], "incl. HBM (TrendForce)")
    tile(c[4], "US firms using AI", f"{ref.BTOS_AI_USE[-1][1]}%", f"from {ref.BTOS_AI_USE[1][1]}% at start of 2026")

    l, r = st.columns(2)
    with l:
        st.subheader("AI-lab revenue run-rates")
        ar = pd.DataFrame(ref.AI_REVENUE, columns=["date", "Series", "value", "note"])
        ar["date"] = pd.to_datetime(ar["date"])
        show(line_chart(ar, fmt="$,.0f", y_title="$B annualized", height=300, colors=[BLUE, ORANGE],
                        date_fmt="%b %Y"))
        st.caption("Reported run-rates are extrapolations, not audited revenue; the two labs may measure differently.")
    with r:
        st.subheader("Token volume on OpenRouter")
        orr = pd.DataFrame([(d, v) for d, v, *_ in ref.OPENROUTER], columns=["date", "value"])
        orr["date"], orr["Series"] = pd.to_datetime(orr["date"]), "Tokens per week"
        show(line_chart(orr, fmt=",.4~g", y_title="Trillion tokens per week (log)", height=300, log=True,
                        legend=False, date_fmt="%b %Y"))
        st.caption("One aggregator, not the whole market.")
    l, r = st.columns(2)
    with l:
        st.subheader("Korean chip exports keep setting records")
        k = pd.DataFrame(ref.KOREA_CHIP_RECORDS, columns=["Month", "value"])
        show(cat_bars(k, "Month", "value", fmt="$,.1f", y_title="$B per month", highlight_last=True))
        st.caption("2026 monthly records only (Jan, Apr and Jul were not records).")
    with r:
        st.subheader("TSMC monthly revenue")
        tm = pd.DataFrame(ref.TSMC_MONTHLY, columns=["Month", "value", "yoy"])
        tm["Month"] = pd.to_datetime(tm["Month"] + "-01").dt.strftime("%b %Y")
        show(cat_bars(tm, "Month", "value", fmt=",.0f", y_title="NT$ billions", highlight_last=True))
        st.caption("YoY: " + ", ".join(f"{m} {y:+.1f}%" for m, _, y in tm.itertuples(index=False)) + ".")
    st.subheader("Share of US firms using AI")
    bt = pd.DataFrame(ref.BTOS_AI_USE, columns=["date", "value"])
    bt["date"], bt["Series"] = pd.to_datetime(bt["date"]), "Firms using AI"
    show(line_chart(bt, fmt=".1f", y_title="% of firms, past two weeks", height=240, legend=False, zero=True,
                    date_fmt="%b %d, %Y"))
    st.caption("Census BTOS: used AI in any business function. The question was broadened in Nov 2025.")
    sources_box(refs=[nv["source"], ref.TSMC_SOURCE, ref.KOREA_SOURCE, ref.DRAM["source"], ref.AI_REVENUE_SOURCE,
                      ref.BTOS_SOURCE] + list(dict.fromkeys(o[3] for o in ref.OPENROUTER)))


# ---------------------------------------------------------------------------
# Page 5: Labor market
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
        show(line_chart(window(to_long({"Age 16-24": y, "All workers": u})), fmt=".1f", y_title="Percent",
                        height=280, colors=[ORANGE, BLUE], date_fmt="%b %Y"))
    with r:
        st.subheader("Software development postings")
        show(line_chart(window(to_long({"Indeed software postings": sw})), fmt=".1f", y_title="Index, Feb 2020 = 100",
                        height=280, legend=False, ref_y=100))
        st.caption("Most of the 2026 rebound is senior and AI-titled roles (Indeed Hiring Lab).")

    st.subheader("Tech employment, year over year")
    st.caption("% change from 12 months earlier, payroll survey.")
    show(line_chart(window(to_long({"Computer systems design": yoy(csd, 12), "Data processing & hosting": yoy(dp, 12),
                                    "Information sector": yoy(info, 12)})), fmt="+.1f", y_title="% YoY", height=300,
                    zero=True, date_fmt="%b %Y"))

    l, r = st.columns(2)
    with l:
        st.subheader("Announced job cuts citing AI")
        cuts = pd.DataFrame(ref.AI_JOB_CUTS_YTD, columns=["Month", "value"])
        show(cat_bars(cuts, "Month", "value", fmt=",.0f", y_title="2026 year to date", height=280,
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
    if st.button("Refresh data"):
        st.cache_data.clear()
    st.divider()
    st.header("Settings")
    start_year = st.slider("Show data from", 2015, date.today().year, 2022, key="start_year",
                           help="Charts start in January of this year.")

pages = st.navigation([
    st.Page(real_economy_page, title="Real economy", url_path="real-economy", default=True),
    st.Page(firm_page, title="Firm level", url_path="firms"),
    st.Page(markets_page, title="Financial markets", url_path="markets"),
    st.Page(leading_page, title="Leading signals", url_path="leading"),
    st.Page(labor_page, title="Labor market", url_path="labor"),
])
pages.run()
