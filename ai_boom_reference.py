"""
Reference figures for the AI boom dashboard that have no free live feed
(company guidance, press-reported ratings, survey releases, AI-lab run-rates...).

Every entry carries its own source. Update the numbers here when new releases
come out; the dashboard reads this module on every run.

Compiled: October 8, 2026.
"""

AS_OF = "Oct 8, 2026"

# ---------------------------------------------------------------------------
# Data center construction (Census C30 survey, via Our World in Data).
# Fallback when the OWID download is unavailable. Monthly, NOT seasonally
# adjusted, billions of constant 2021 dollars (OWID deflates with BLS PPIs).
# ---------------------------------------------------------------------------
DC_SOURCE = ("Census Bureau C30 via Our World in Data (constant 2021 $)",
             "https://ourworldindata.org/grapher/monthly-spending-data-center-us")
DC_SNAPSHOT = [
    ("2022-01", 0.758), ("2022-02", 0.698), ("2022-03", 0.783), ("2022-04", 0.835),
    ("2022-05", 0.844), ("2022-06", 0.852), ("2022-07", 0.857), ("2022-08", 0.897),
    ("2022-09", 0.982), ("2022-10", 0.809), ("2022-11", 0.841), ("2022-12", 0.868),
    ("2023-01", 0.932), ("2023-02", 1.028), ("2023-03", 1.091), ("2023-04", 1.134),
    ("2023-05", 1.157), ("2023-06", 1.194), ("2023-07", 1.288), ("2023-08", 1.372),
    ("2023-09", 1.405), ("2023-10", 1.508), ("2023-11", 1.464), ("2023-12", 1.486),
    ("2024-01", 1.588), ("2024-02", 1.641), ("2024-03", 1.850), ("2024-04", 1.781),
    ("2024-05", 2.065), ("2024-06", 2.266), ("2024-07", 2.351), ("2024-08", 2.436),
    ("2024-09", 2.475), ("2024-10", 2.549), ("2024-11", 2.521), ("2024-12", 2.735),
    ("2025-01", 2.709), ("2025-02", 2.677), ("2025-03", 2.847), ("2025-04", 3.338),
    ("2025-05", 3.098), ("2025-06", 3.019), ("2025-07", 3.082), ("2025-08", 3.229),
    ("2025-09", 3.319), ("2025-10", 3.370), ("2025-11", 3.189), ("2025-12", 3.306),
    ("2026-01", 3.269), ("2026-02", 3.266), ("2026-03", 3.495), ("2026-04", 3.797),
    ("2026-05", 4.105), ("2026-06", 4.552), ("2026-07", 4.915), ("2026-08", 5.371),
]
DC_NOMINAL_LATEST = {
    "value_b_saar": 84.95, "month": "Aug 2026", "yoy_pct": 73.2,
    "source": ("Census Bureau construction spending (Oct 1, 2026), via iRecruit",
               "https://www.irecruit.co/insights/us-data-center-construction-spending-jumps"),
}

# ---------------------------------------------------------------------------
# Fed FEDS Note, "The AI Buildout and the Economy" (Soto, Thieu & Allen, Jul 17, 2026)
# ---------------------------------------------------------------------------
FED_PROXY = {
    "q1_2026_gross_pp": 0.73,
    "q1_2026_import_drag_pp": 0.45,
    "late_2025_gross_pp": 0.75,
    "late_2025_net_pp": 0.14,
    "components": "software, computers & peripheral equipment, data centers, power facilities, "
                  "less down-weighted net exports of computers, peripherals & parts",
    "source": ("Federal Reserve FEDS Note (Jul 17, 2026)",
               "https://www.federalreserve.gov/econres/notes/feds-notes/the-ai-buildout-and-the-economy-publicly-available-data-to-assess-ais-impact-20260717.html"),
    "data_file": "https://www.federalreserve.gov/econres/notes/feds-notes/feds-ai-buildout-figure-data.xlsx",
}

# ---------------------------------------------------------------------------
# Firm level
# ---------------------------------------------------------------------------
PLATFORMONOMICS = ("Platformonomics, Follow the CAPEX: Q2 2026 Scoreboard (Jul 31, 2026)",
                   "https://platformonomics.com/2026/07/follow-the-capex-q2-2026-scoreboard/")

# 2026 full-year capex guidance, $B (midpoint of ranges), by guidance date
CAPEX_GUIDANCE = [
    # company, Jan 2026, Apr 2026, Jul 2026, note
    ("Amazon", 200, 200, 220, ""),
    ("Alphabet", 180, 185, 200, ""),
    ("Microsoft", 140, 190, 175, "Jan is an estimate; Jul is lower only because data center leases "
                                 "moved from finance to operating leases (~$190B like-for-like)."),
    ("Meta", 125, 135, 137.5, ""),
]
CAPEX_Q2_2026 = {"total_b": 172, "qoq_pct": 29, "yoy_pct": 77, "h1_b": 305, "source": PLATFORMONOMICS}

# 2027 outlook. No hyperscaler has given a calendar-2027 capex number yet; what each said on
# its Q2 2026 call, plus sell-side estimates. $B. None = no figure available.
CITI_2027 = ("Citi estimates via BigGo Finance (Jul 16, 2026)",
             "https://finance.biggo.com/news/a9ad937b-2486-448b-935f-09511f331f7a")
ORACLE_FY27 = ("S&P / Oracle FY27 guidance, via PPC Land (Jul 2026)",
               "https://ppc.land/s-p-cuts-oracle-to-bbb-as-ai-buildout-widens-cash-deficit-to-42bn/")
MSFT_Q2 = ("The Star, 'Microsoft sees strong cash flow, lower capex' (Jul 31, 2026)",
           "https://www.thestar.com.my/business/business-news/2026/07/31/microsoft-sees-strong-cash-flow-lower-capex")
CAPEX_2027 = [
    # company, 2026 guide midpoint (Jul), 2027 analyst estimate, 2027 company guidance, what the company said, source
    ("Amazon", 220, 288, None,
     "\"We will still not have enough capacity to meet all the demand we have in 2026 ... this dynamic "
     "will also be true in 2027.\" No 2027 figure.", CITI_2027),
    ("Alphabet", 200, 308, None,
     "\"We continue to expect our CapEx to increase significantly in 2027\"; details later.", CITI_2027),
    ("Meta", 137.5, 205, None,
     "Plans \"geared towards maximizing 2026 and 2027 capacity\"; no 2027 guidance.", CITI_2027),
    ("Microsoft", 175, None, None,
     "FY27 (Jul 2026–Jun 2027) capex \"will grow year-over-year\"; ~$50B guided for Jul–Sep 2026; "
     "expects to stay free-cash-flow positive. 2026 figure is after the lease reclassification (~$190B like-for-like).",
     MSFT_Q2),
    ("Oracle", None, None, 92.5,
     "FY27 (Jun 2026–May 2027) capex guided at $90–95B.", ORACLE_FY27),
]
CAPEX_2027_TOTALS = [
    # label, value, detail, source
    ("Bloomberg consensus, 2027", "$1.08T", "Alphabet, Amazon, Meta, Microsoft and Oracle (as of Jul 31, 2026); "
     "$777B in 2026.", ("Vanguard calculations on Bloomberg data, via ai-CIO", "https://www.ai-cio.com/?p=106712")),
    ("Wall Street range, 2027", "$1.0–1.4T", "BofA, Moody's, Goldman above $1T; S&P >$1.3T; UBS ~$1.4T total AI capex.",
     ("Stocktwits (Sep 22, 2026)",
      "https://stocktwits.com/news-articles/markets/equity/jp-morgan-ceo-sees-hyperscaler-spending-hitting-1-trillion-next-year-and-still-growing-investors-are-shrugging-it-off-for-now/cZMPLi0RBeJ")),
    ("Citi: Alphabet + Amazon + Meta, 2027", "$801B", "Estimates raised 12–22% in July.", CITI_2027),
]

FIRM_FACTS = [
    # label, value, detail, source (name, url)
    ("Big-4 2026 capex guidance", "$735–750B",
     "Up from $640B+ in January; Q2 spend alone was ~$172B (+77% YoY).", PLATFORMONOMICS),
    ("Big-4 TTM free cash flow", "−24% YoY",
     "Down 18% from the prior quarter; Amazon negative on a TTM basis.", PLATFORMONOMICS),
    ("Capex funded by new debt, 2026", "≈ ⅓",
     "Goldman: ~$750B capex vs ~$778B operating cash flow; ~$250B bonds in 2026, ~$400B in 2027.",
     ("Reuters via KFGO (Jul 29, 2026)",
      "https://kfgo.com/2026/07/29/hyperscaler-debt-binge-pushes-yields-up-as-investor-demand-cools/")),
    ("Cloud backlog (AMZN, GOOGL, MSFT)", ">$1.4T",
     "Contracted demand behind the capex; a large share sits with a few AI labs.",
     ("Livewire Markets", "https://www.livewiremarkets.com/wires/no-ai-hyperscaler-hyperscare-here")),
    ("Oracle FY27 free operating cash flow", "−$42B",
     "S&P forecast; FY27 capex $90–95B, $260B lease commitments, $638B RPO (~half OpenAI).",
     ("PPC Land on S&P's Oracle downgrade (Jul 2026)",
      "https://ppc.land/s-p-cuts-oracle-to-bbb-as-ai-buildout-widens-cash-deficit-to-42bn/")),
]

VANGUARD_BONDS = ("Vanguard calculations on Bloomberg data, via ai-CIO",
                  "https://www.ai-cio.com/?p=106712")
# Annual IG bond issuance by Alphabet, Amazon, Meta, Microsoft, Oracle ($B) and share of US IG supply (%)
HYPERSCALER_BONDS = [
    ("2020", 50.0, 4), ("2021", 41.7, 4), ("2022", 47.9, 6), ("2023", 17.2, 2),
    ("2024", 20.1, 2), ("2025", 93.3, 6), ("2026 YTD (Jul 31)", 132.0, 11),
]

# ---------------------------------------------------------------------------
# Financial markets
# ---------------------------------------------------------------------------
REUTERS_SPREADS = ("Reuters via KFGO (Jul 29, 2026)",
                   "https://kfgo.com/2026/07/29/hyperscaler-debt-binge-pushes-yields-up-as-investor-demand-cools/")
# Median spreads (bp) on Amazon, Alphabet, Meta, Oracle bonds: 2025 vs 2026 issues
HYPERSCALER_SPREADS = [
    ("2–4 yr", 30, 40), ("5–7 yr", 50, 60), ("20+ yr", 108.5, 118), ("New-issue concession", 2.25, 12),
]

# ---------------------------------------------------------------------------
# AI-related bonds and loans, bond by bond. Market yields/prices are the latest published readings
# (no free daily bond-price feed exists; TRACE prices need a FINRA or vendor subscription). The dashboard
# computes each bond's spread over Treasuries from FRED's Treasury curve on the same date.
# Fields: issuer, group, instrument, rate (as text), rate type, coupon %, maturity (ISO), maturity label,
#         amount, secured?, price (per 100), yield to maturity %, price/yield as of (ISO), source
# ---------------------------------------------------------------------------
TV_BONDS = ("Benzinga / TradingView bond screener (prices as of Oct 5, 2026)",
            "https://www.tradingview.com/news/benzinga:7522ce132094b:0-highest-yielding-hyperscaler-bonds-in-october-2026-spacex-joins-oracle-above-7-5/")
BZ_ORCL = ("Benzinga, 'Oracle 20-year bond yields 8.1%' (Oct 2, 2026)",
           "https://www.benzinga.com/markets/bonds/26/10/62136978/oracle-20-year-bond-yields-8-percent-stock-return")
CNBC_CRWV = ("CNBC via Traders Union (Oct 19, 2026)",
             "https://tradersunion.com/news/companies/show/3882979-coreweave-bond-yields-credit-risk/")
CCIR = ("CCIR, CoreWeave's debt entity by entity (as of Oct 18, 2026; from SEC filings)",
        "https://ccir.io/research/coreweave-debt-by-entity")
CCIR_LEDGER = ("CCIR Compute Credit Tracker (as of Oct 19, 2026; from SEC filings and lender releases)", "https://ccir.io/credit")
ST_NEB = ("StockTitan, 'How much CoreWeave and Nebius owe' (Oct 15, 2026)",
          "https://www.stocktitan.net/articles/coreweave-nebius-ai-cloud-debt-when-it-comes-due")
CP_NEO = ("The Closing Print, neocloud credit deep dive (Oct 14, 2026)",
          "https://www.theclosingprint.net/2026/10/neoclouds-ai-hosting-deep-dive-2026-10-14/")
TP_BEIGNET = ("TokenPost: Hyperion project bond at record low (Oct 7, 2026)", "https://www.tokenpost.com/news/technology/27470")
AI_BONDS = [
    # --- hyperscalers: market yields
    ("Oracle", "Hyperscalers", "6.85% notes", "6.85% fixed", "Fixed", 6.85, "2066-02-04", "Feb 2066", None, False, 81.70, 8.45, "2026-10-05", TV_BONDS),
    ("Oracle", "Hyperscalers", "6.125% notes", "6.125% fixed", "Fixed", 6.125, "2065-08-03", "Aug 2065", None, False, 73.69, 8.43, "2026-10-05", TV_BONDS),
    ("Oracle", "Hyperscalers", "6.55% notes", "6.55% fixed", "Fixed", 6.55, "2046-02-15", "Feb 2046", None, False, 84.91, 8.11, "2026-10-01", BZ_ORCL),
    ("Meta", "Hyperscalers", "5.55% notes", "5.55% fixed", "Fixed", 5.55, "2064-08-15", "Aug 2064", None, False, 75.80, 7.48, "2026-10-05", TV_BONDS),
    ("Meta", "Hyperscalers", "5.75% notes", "5.75% fixed", "Fixed", 5.75, "2065-11-15", "Nov 2065", None, False, 78.30, 7.46, "2026-10-05", TV_BONDS),
    ("Amazon", "Hyperscalers", "6.05% notes", "6.05% fixed", "Fixed", 6.05, "2076-03-13", "Mar 2076", None, False, 87.50, 6.95, "2026-10-05", TV_BONDS),
    ("Amazon", "Hyperscalers", "6.25% notes", "6.25% fixed", "Fixed", 6.25, "2066-07-09", "Jul 2066", None, False, 90.80, 6.93, "2026-10-05", TV_BONDS),
    ("Alphabet", "Hyperscalers", "5.70% notes", "5.70% fixed", "Fixed", 5.70, "2075-11-15", "Nov 2075", None, False, 83.90, 6.84, "2026-10-05", TV_BONDS),
    ("Alphabet", "Hyperscalers", "6.50% notes", "6.50% fixed", "Fixed", 6.50, "2066-08-15", "Aug 2066", None, False, 95.70, 6.81, "2026-10-05", TV_BONDS),
    ("Microsoft", "Hyperscalers", "2.675% notes", "2.675% fixed", "Fixed", 2.675, "2060-06-01", "Jun 2060", None, False, 49.00, 6.36, "2026-10-05", TV_BONDS),
    ("Microsoft", "Hyperscalers", "3.041% notes", "3.041% fixed", "Fixed", 3.041, "2062-03-17", "Mar 2062", None, False, 53.60, 6.34, "2026-10-05", TV_BONDS),
    ("Meta (Hyperion JV)", "Hyperscalers", "Beignet Investor 6.58% secured amortizing bond", "6.58% fixed, amortizing", "Fixed", 6.58, "2049-05-30", "2049", "$27.3B", True, 91.0, None, "2026-10-07", TP_BEIGNET),
    # --- other AI borrowers with market yields
    ("SpaceX (incl. AI unit)", "Neoclouds & AI", "6.60% notes", "6.60% fixed", "Fixed", 6.60, "2046-07-15", "Jul 2046", None, False, 87.60, 7.84, "2026-10-05", TV_BONDS),
    ("SpaceX (incl. AI unit)", "Neoclouds & AI", "6.65% notes", "6.65% fixed", "Fixed", 6.65, "2056-07-15", "Jul 2056", None, False, 88.03, 7.67, "2026-10-05", TV_BONDS),
    # --- neoclouds
    ("CoreWeave", "Neoclouds & AI", "9.625% senior notes", "9.625% fixed", "Fixed", 9.625, "2032-06-01", "2032", "$1.25B", False, None, 14.9, "2026-10-19", CNBC_CRWV),
    ("CoreWeave", "Neoclouds & AI", "9.25% senior notes", "9.25% fixed", "Fixed", 9.25, "2030-06-01", "2030", "$2.00B", False, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "9.00% senior notes", "9.00% fixed", "Fixed", 9.00, "2031-06-01", "2031", "$1.75B", False, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "9.75% senior notes", "9.75% fixed", "Fixed", 9.75, "2031-06-01", "2031", "$2.75B", False, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "8.50% EUR senior notes", "8.50% fixed (EUR)", "Fixed", 8.50, "2032-06-01", "2032", "€2.0B", False, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Delayed-draw term loan 1.0", "SOFR + 9.62%", "Floating", None, "2028-03-28", "Mar 2028", "$1.30B", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Delayed-draw term loan 2.0", "SOFR + 6.00–13.00% by customer", "Floating", None, "2030-08-01", "Aug 2030", "$3.19B", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Delayed-draw term loan 2.1", "SOFR + 4.25%", "Floating", None, "2031-03-01", "Mar 2031", "$3.00B", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Delayed-draw term loan 3.0", "SOFR + 4.00%", "Floating", None, "2030-08-21", "Aug 2030", "$2.21B", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Delayed-draw term loan 4.0 (rated A3)", "SOFR + 2.25% (fixed tranche ~5.9%)", "Floating", None, "2032-03-31", "Mar 2032", "$2.84B", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Delayed-draw term loan 5.0 (rated Ba2/BB+)", "SOFR + 4.50%", "Floating", None, "2031-11-15", "Nov 2031", "$1.10B", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Delayed-draw term loan 5.5 (rated Ba2/BB+)", "SOFR + 5.50%", "Floating", None, "2031-09-01", "Sep 2031", "$2.6B signed", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "Revolving credit facility", "SOFR + 1.75%", "Floating", None, "2029-11-01", "Nov 2029", "$2.5B ($1.2B drawn Aug)", True, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "1.75% convertible notes", "1.75% fixed, convertible", "Convertible", 1.75, "2031-06-01", "2031", "$2.59B", False, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "1.75% convertible notes", "1.75% fixed, convertible", "Convertible", 1.75, "2032-06-01", "2032", "$4.00B", False, None, None, None, CCIR),
    ("CoreWeave", "Neoclouds & AI", "2.875% convertible notes", "2.875% fixed, convertible", "Convertible", 2.875, "2033-04-01", "Apr 2033", "$4.20B", False, None, None, None, CCIR),
    ("Nebius", "Neoclouds & AI", "Senior secured GPU facility", "SOFR + 2.50%", "Floating", None, "2030-10-31", "Oct 2030", "~$775M", True, None, None, None, ST_NEB),
    ("Nebius", "Neoclouds & AI", "0.50% convertible notes", "0.50% fixed, convertible (repay 110%)", "Convertible", 0.50, "2030-02-01", "Feb 2030", "part of $5.75B", False, None, None, None, ST_NEB),
    ("Nebius", "Neoclouds & AI", "4.50% convertible notes", "4.50% fixed, convertible (repay 125%)", "Convertible", 4.50, "2034-02-01", "Feb 2034", "part of $5.75B", False, None, None, None, ST_NEB),
    ("IREN", "Neoclouds & AI", "Hardware 3 senior secured notes (rated A)", "5.96% fixed", "Fixed", 5.96, "2031-12-31", "Dec 2031", "$2.10B", True, None, None, None, CCIR_LEDGER),
    ("IREN", "Neoclouds & AI", "Hardware 3 delayed-draw term loan", "SOFR + 2.25%", "Floating", None, "2031-12-31", "Dec 2031", "$1.55B", True, None, None, None, CCIR_LEDGER),
    ("Nscale", "Neoclouds & AI", "GPU-backed delayed-draw term loan", "SOFR + 5.00%", "Floating", None, "2032-09-30", "Sep 2032", "$1.42B", True, None, None, None, CCIR_LEDGER),
    ("Galaxy Digital", "Neoclouds & AI", "Helios Phase II senior secured notes", "9.875% fixed", "Fixed", 9.875, "2031-06-01", "2031", "$3.51B", True, None, None, None, CP_NEO),
    ("Applied Digital", "Neoclouds & AI", "ELN-04 secured notes", "7.00% fixed", "Fixed", 7.00, None, "—", "$1.59B", True, None, None, None, CP_NEO),
]

# Long-term issuer / senior unsecured ratings as reported. Notches above junk are computed in the
# dashboard from the S&P rating (Moody's if S&P is missing): BBB-/Baa3 = 0, junk is negative.
MB = ("MarketBeat, 'Oracle is one step from junk'", "https://www.marketbeat.com/articles/oracle-is-one-step-from-junkcan-it-afford-the-ai-boom/")
RATINGS = [
    # company, segment, S&P, Moody's, Fitch, as of, note, source
    ("Microsoft", "Hyperscalers", "AAA", "—", "—", "2026", "No new bonds in 2026 to date", MB),
    ("Alphabet", "Hyperscalers", "AA+", "—", "—", "2026", "Raised $85B of equity alongside debt", MB),
    ("Amazon", "Hyperscalers", "AA", "—", "—", "2026", "TTM free cash flow negative after Q2", MB),
    ("Meta", "Hyperscalers", "AA-", "Aa3", "—", "Aug 2026", "Off-balance-sheet data center JVs add to obligations",
     ("Financial News (Korea), Aug 30, 2026", "https://en.fnnews.com/news/202608291254188090")),
    ("Oracle", "Hyperscalers", "BBB-", "—", "—", "Jul 9, 2026", "S&P cut from BBB, stable; one notch above junk",
     ("PPC Land", "https://ppc.land/s-p-cuts-oracle-to-bbb-as-ai-buildout-widens-cash-deficit-to-42bn/")),
    ("Nvidia", "Chips", "AA", "Aa1", "—", "Jun 2026", "S&P upgraded from AA- (Jun 2026); Moody's Aa1, positive (Jan 2026)",
     ("Yahoo Finance: S&P upgrades Nvidia to AA (Jun 11, 2026)",
      "https://finance.yahoo.com/markets/stocks/articles/p-global-ratings-upgrades-nvidia-211417548.html")),
    ("TSMC", "Chips", "AA-", "Aa3", "—", "Oct 2026", "Both agencies on positive outlook",
     ("TSMC investor relations: credit ratings", "https://investor.tsmc.com/english/credit-rating")),
    ("Broadcom", "Chips", "A-", "A3", "BBB+", "Jun 2026", "S&P called its $35B AI XPV financing tranche 'credit negative' (Jun 2026)",
     ("KuCoin News: S&P on Broadcom AI tranche (Jun 11, 2026)",
      "https://www.kucoin.com/news/flash/s-p-global-ratings-flags-broadcom-s-ai-tranche-as-credit-negative")),
    ("AMD", "Chips", "A", "A3", "—", "2025", "Moody's A3 is the last confirmed action (2022)",
     ("Insider Monkey: S&P upgrades AMD to A",
      "https://www.insidermonkey.com/blog/sp-global-upgrades-advanced-micro-devices-inc-amd-to-a-rating-ai-growth-and-strong-market-share-propel-outlook-1421521/")),
    ("Micron", "Chips", "BBB+", "Baa1", "—", "Aug 2026", "Upgraded by both in Jul–Aug 2026 on AI memory demand; S&P outlook positive",
     ("Investing.com: Moody's upgrades Micron (Jul 30, 2026)",
      "https://www.investing.com/news/stock-market-news/moodys-upgrades-micron-rating-on-customer-agreements-ai-demand-93CH-4825934")),
    ("Intel", "Chips", "BBB", "Baa2", "BBB", "2025", "Downgraded by all three in 2024–25; Fitch outlook negative",
     ("Calcalist: Intel downgraded (Aug 2025)", "https://www.calcalistech.com/ctechnews/article/g8hxy1pev")),
    ("CoreWeave", "Neoclouds & AI", "B+", "Ba3", "—", "Apr 2026", "Junk. Its $8.5B GPU-backed facility got an investment-grade rating; 5-yr CDS >855bp",
     ("cbonds: Moody's affirms CoreWeave Ba3 (Apr 10, 2026)", "https://cbonds.com/news/3865521/")),
    ("SpaceX (incl. AI unit)", "Neoclouds & AI", "BBB", "Baa1", "BBB+", "Jun 18, 2026", "First ratings after IPO; bonds trade wider than BBB peers",
     ("IndexBox: SpaceX earns investment-grade ratings (Jun 2026)",
      "https://www.indexbox.io/blog/spacex-receives-first-investment-grade-credit-ratings-from-moodys-fitch-and-sp-global/")),
    ("Dell", "Servers & data centers", "BBB+", "Baa2", "BBB+", "Aug 14, 2026", "Moody's outlook positive",
     ("Dell fixed income information", "https://investors.delltechnologies.com/financial-information/fixed-income-information")),
    ("Equinix", "Servers & data centers", "BBB+", "—", "BBB+", "Mar 2026", "Largest data center REIT; stable outlooks",
     ("Benzinga: Equinix BBB+ (Mar 25, 2026)",
      "https://www.benzinga.com/Opinion/26/03/51456570/equinix-has-a-bbb-rating-and-a-51-percent-dividend-buffer-the-capex-cycle-is-the-variable-worth-watching")),
    ("Constellation Energy", "Power", "—", "Baa1", "—", "Apr 2024", "Moody's upgrade on nuclear and data center demand",
     ("Constellation: Moody's upgrade (Apr 3, 2024)",
      "https://investors.constellationenergy.com/news-releases/news-release-details/moodys-upgrades-constellations-credit-rating-policy-support-and")),
    ("Vistra", "Power", "BBB-", "—", "BBB-", "Mar 2026", "Became investment grade at S&P (Dec 2025) and Fitch (Mar 2026)",
     ("Vistra press release (Mar 17, 2026)",
      "https://www.prnewswire.com/news-releases/vistra-achieves-investmentgrade-credit-ratings-from-sp-and-fitch-302716271.html")),
]
RATING_SEGMENTS = ["Hyperscalers", "Chips", "Neoclouds & AI", "Servers & data centers", "Power"]
# 5-year CDS, bp. Public press readings only: dealer CDS quotes (Bloomberg, LSEG, S&P, ICE) are
# not free, so the latest public figures are from late July to mid-August 2026. Replace with
# current quotes from your terminal when you have them. None = no public figure found.
CDS_5Y = {
    # company: latest, latest label, as of, early-2026 baseline, baseline date, source
    # Updated Oct 20, 2026 from the latest press readings. Big Tech CDS hit record highs on Oct 15 (Reuters,
    # citing LSEG and S&P Global Market Intelligence), but levels for Amazon, Alphabet, Meta and Nvidia
    # weren't published; their figures below are still the late-July readings (see CDS_NOTES).
    "Oracle": (315, "315", "Oct 19, 2026", 144, "Start of 2026",
               ("CNBC via Traders Union (Oct 19, 2026): Oracle 5-yr CDS 315bp, up 311% YoY",
                "https://tradersunion.com/news/companies/show/3882979-coreweave-bond-yields-credit-risk/")),
    "CoreWeave": (1082, "~1,082", "Oct 19, 2026", None, None,
                  ("CNBC via Traders Union (Oct 19, 2026): ~1,082bp; record above 1,100bp on Oct 15 (S&P Global MI)",
                   "https://tradersunion.com/news/companies/show/3882979-coreweave-bond-yields-credit-risk/")),
    "Meta": (90, "~90", "Jul 28, 2026", None, None,
             ("KuCoin News, citing Bloomberg (Jul 28, 2026)",
              "https://www.kucoin.com/news/flash/meta-and-broadcom-cds-hit-record-highs-amid-ai-financing-risks")),
    "Alphabet": (67, "67", "Jul 28, 2026", 38, "Mid-Nov 2025",
                 ("Yahoo Finance / GuruFocus, LSEG data (Jul 28, 2026)",
                  "https://finance.yahoo.com/technology/ai/articles/big-tech-credit-risk-flashes-192645668.html")),
    "Amazon": (67.5, "65–70", "Jul 28, 2026", 38, "Mid-Nov 2025",
               ("KuCoin News, citing Bloomberg (Jul 28, 2026)",
                "https://www.kucoin.com/news/flash/meta-and-broadcom-cds-hit-record-highs-amid-ai-financing-risks")),
    "Nvidia": (82, "82", "Jul 27, 2026", None, None,
               ("Protos, citing CDS data (Jul 29, 2026)", "https://protos.com/credit-default-swaps-forecast-ai-bankruptcies/")),
    "Microsoft": (None, "—", None, 34, "Mid-Nov 2025",
                  ("ZeroHedge, citing S&P data (Nov 17, 2025)",
                   "https://www.zerohedge.com/markets/stocks-slide-after-amazon-shocks-another-massive-bond-offering-rebound-news-boaz-weinsten")),
}
CDS_OCT15 = ("Reuters via Investing.com (Oct 15, 2026): Oracle near 300bp, CoreWeave >1,100bp; Amazon, Alphabet, "
             "Meta at record highs (LSEG, S&P Global MI)",
             "https://www.investing.com/news/stock-market-news/ai-credit-default-swap-spreads-widen-sharply-4950549")
CDS_NOTES = {
    "Oracle": "Record 288bp on Oct 15 (S&P Global MI / LSEG), 315bp on Oct 19",
    "CoreWeave": "Record >1,100bp on Oct 15; above 1,000bp is distress territory",
    "Meta": "Record high on Oct 15 (Reuters); level not published since July",
    "Alphabet": "Record high on Oct 15 (Reuters); level not published since July",
    "Amazon": "Record high on Oct 15 (Reuters); level not published since July",
    "Nvidia": "Rose sharply on Oct 15 (Reuters); level not published since July",
}
CDS_BASELINE_SOURCE = ("ZeroHedge, citing S&P data (Nov 17, 2025): Alphabet ~38, Amazon ~38, Microsoft ~34bp",
                       "https://www.zerohedge.com/markets/stocks-slide-after-amazon-shocks-another-massive-bond-offering-rebound-news-boaz-weinsten")

ORACLE_CDS = {"latest_bp": 315, "year_ago_bp": 77, "note": "315bp on Oct 19, 2026, up 311% from a year earlier; record 288bp close on Oct 15 (S&P Global MI / LSEG)",
              "source": ("Thairath / ICE Data Services",
                         "https://en.thairath.co.th/money/tech_innovation/tech_companies/2947695")}

EPOCH = ("Epoch AI, LLM inference price trends", "https://epoch.ai/data-insights/ai-inference-price-trends")
# Cheapest model at GPT-4 level on MMLU, $ per 1M tokens
TOKEN_PRICE_GPT4 = [
    ("2023-03-14", 37.50, "GPT-4-0314"),
    ("2023-11-06", 15.00, "GPT-4 Turbo"),
    ("2024-05-13", 7.50, "GPT-4o"),
    ("2025-02-05", 0.18, "Gemini 2.0 Flash"),
]
# Silicon Data LLM Token Expenditure Index (Bloomberg: SDLLMTK): usage-weighted blended price,
# USD per 1M tokens, daily since Dec 2025. The full series is on Bloomberg / the Silicon Data
# portal only; these are the dated readings reported publicly. Dates marked ~ are approximate.
SILICON_DATA = ("Silicon Data, LLM Token Expenditure Index (SDLLMTK)",
                "https://www.silicondata.com/products/silicon-index/llm-token-expenditure-index")
SDLLMTK = [
    # date, $ per 1M tokens, note, source
    ("2025-12-15", 1.09, "~ Launch reading, Dec 2025",
     ("sanj.dev, SDLLMTK explained (Aug 19, 2026)", "https://sanj.dev/post/sdllmtk-llm-token-expenditure-index/")),
    ("2026-05-15", 2.12, "~ Peak, May 2026",
     ("sanj.dev, SDLLMTK explained (Aug 19, 2026)", "https://sanj.dev/post/sdllmtk-llm-token-expenditure-index/")),
    ("2026-07-03", 1.62, "CIO.com, Jul 3, 2026",
     ("CIO.com, 'AI token prices are cooling' (Jul 3, 2026)", "https://www.cio.com/article/4192834/ai-token-prices-are-cooling-but-why-2.html")),
    ("2026-08-19", 1.02, "Silicon Data dashboard, mid-Aug 2026",
     ("sanj.dev, SDLLMTK explained (Aug 19, 2026)", "https://sanj.dev/post/sdllmtk-llm-token-expenditure-index/")),
    ("2026-08-31", 0.97, "Record low since launch (CNBC)",
     ("TechJack Solutions, citing CNBC (Sep 3, 2026)", "https://techjacksolutions.com/ai-brief/llm-token-prices-record-low-below-1-per-million-tokens/")),
    ("2026-10-07", 0.99, "Silicon Data index page, Oct 7, 2026", SILICON_DATA),
]

BENCHLM = ("BenchLM LLM pricing statistics (Oct 7, 2026)", "https://benchlm.ai/md/stats/llm-pricing.md")
TOKEN_INDEX = {"frontier": 16, "mid": 30.1, "budget": 61.2, "frontier_yoy_pct": 72, "mid_yoy_pct": -44.5,
               "median_input": 0.95, "median_output": 3.75, "base": "Mar 2023 = 100", "source": BENCHLM}

# ---------------------------------------------------------------------------
# Leading signals
# ---------------------------------------------------------------------------
TSMC_SOURCE = ("TSMC monthly revenue reports (Form 6-K)",
               "https://www.sec.gov/Archives/edgar/data/0001046179/000104617926000680/tsm-revenue20261008.htm")
# month, revenue NT$B, YoY %
TSMC_MONTHLY = [("2026-07", 467.58, 44.7), ("2026-08", 514.81, 53.3), ("2026-09", 511.86, 54.6)]

NVIDIA = {"q2_fy27_rev_b": 96.2, "q2_yoy_pct": 106, "dc_rev_b": 89.0, "dc_yoy_pct": 117,
          "q3_guide_b": 108.0,
          "source": ("Nvidia Q2 FY27 results, via StorageNewsletter (Aug 27, 2026)",
                     "https://www.storagenewsletter.com/2026/08/27/nvidia-fiscal-2q27-financial-results/")}

KOREA_SOURCE = ("Korea Herald / Korea Customs Service", "https://mbiz.heraldcorp.com/article/10890372")
# 2026 monthly semiconductor export records, $B
KOREA_CHIP_LATEST_YOY = 262.8  # Sep 2026 vs Sep 2025
KOREA_CHIP_RECORDS = [("Feb", 25.1), ("Mar", 32.8), ("May", 37.2), ("Jun", 44.8), ("Aug", 46.7), ("Sep", 60.3)]

DRAM = {"q4_2026_dram_incl_hbm": "+15–20% QoQ", "q4_2026_conventional": "+10–15% QoQ",
        "source": ("TrendForce Q4 2026 memory forecast (Sep 30, 2026)", "https://tech.ifeng.com/c/8wqosax55jy")}

AI_REVENUE_SOURCE = ("Axios / Bloomberg / Reuters reporting compiled",
                     "https://axios.com/2026/08/17/anthropic-revenue-run-rate-ipo-openai")
# date, company, run-rate $B, note
AI_REVENUE = [
    ("2025-01-31", "Anthropic", 1, "~$1B, Jan 2025"),
    ("2025-12-31", "Anthropic", 9, "End of 2025"),
    ("2026-03-05", "Anthropic", 19, "Early Mar 2026"),
    ("2026-04-15", "Anthropic", 30, "Apr 2026"),
    ("2026-05-28", "Anthropic", 47, "Series H announcement"),
    ("2026-07-31", "Anthropic", 65, "End of Jul 2026"),
    ("2025-12-31", "OpenAI", 20, "2025 exit run-rate per CFO"),
    ("2026-02-28", "OpenAI", 25, "End of Feb 2026"),
    ("2026-08-10", "OpenAI", 40, "Aug 2026, internal message"),
]

OPENROUTER = [
    # date, trillion tokens per week, note, source
    ("2024-01-07", 0.01, "About 10B tokens per week",
     ("CryptoBriefing (Aug 24, 2026)", "https://cryptobriefing.com/openrouter-9000x-token-usage-growth/")),
    ("2025-11-26", 5, "About six months before May 2026",
     ("Pulse 2.0 (May 26, 2026)", "https://pulse2.com/openrouter-113-million-raised-for-ai-model-exchange-platform-as-weekly-volume-reaches-25-trillion-tokens/amp/")),
    ("2026-05-26", 25, "At Series B announcement",
     ("Pulse 2.0 (May 26, 2026)", "https://pulse2.com/openrouter-113-million-raised-for-ai-model-exchange-platform-as-weekly-volume-reaches-25-trillion-tokens/amp/")),
    ("2026-08-24", 90, "Over 90T per week",
     ("CryptoBriefing (Aug 24, 2026)", "https://cryptobriefing.com/openrouter-9000x-token-usage-growth/")),
]

BTOS_SOURCE = ("Census Business Trends and Outlook Survey", "https://www.census.gov/hfp/btos/data")
# collection-period end, % of firms using AI in any business function (past two weeks)
BTOS_AI_USE = [("2025-11-17", 17.3), ("2025-12-28", 17.7), ("2026-05-03", 19.8),
               ("2026-07-15", 21.7), ("2026-09-06", 23.8)]

# ---------------------------------------------------------------------------
# Labor
# ---------------------------------------------------------------------------
NYFED_GRADS = {"rate": 5.7, "all_workers": 4.1, "month": "Jun 2026",
               "source": ("NPR, citing New York Fed (Aug 18, 2026)", "https://www.npr.org/2026/08/18/nx-s1-5910677"),
               "page": "https://www.newyorkfed.org/research/college-labor-market"}

CHALLENGER = ("Challenger, Gray & Christmas monthly job-cut reports", "https://www.challengergray.com/")
# 2026 year-to-date announced cuts citing AI, by report month
AI_JOB_CUTS_YTD = [("Mar", 27645), ("May", 87714), ("Jun", 101743), ("Jul", 112713), ("Aug", 116175)]
AI_JOB_CUTS_2025 = 54836
TECH_JOB_CUTS_YTD_AUG = {"value": 155126, "yoy_pct": 52}
LABOR_SHARE = {"value": 52.9, "quarter": "Q2 2026", "note": "Lowest since 1947 (BLS nonfarm business)",
               "source": ("AI2Work on BLS productivity release (Aug 6, 2026)",
                          "https://ai2.work/blog/ai-capex-delivered-half-of-us-gdp-growth-in-the-second-quarter")}

# ---------------------------------------------------------------------------
# AI revenue vs capex (Leading signals)
# Hyperscalers don't report "AI revenue" separately; cloud segments are where AI demand is booked.
# Quarters are calendar quarters (Microsoft's fiscal quarters end in the same months). $B.
# ---------------------------------------------------------------------------
CLOUD_SOURCES = [
    ("Amazon quarterly results (AWS segment sales)", "https://www.businesswire.com/news/home/20260204777163/en/Amazon.com-Announces-Fourth-Quarter-Results"),
    ("Amazon Q1 2026 results", "https://www.nasdaq.com/press-release/amazoncom-announces-first-quarter-results-2026-04-29"),
    ("Alphabet Q1 2026 results (Google Cloud)", "https://www.sec.gov/Archives/edgar/data/0001652044/000165204426000043/googexhibit991q12026.htm"),
    ("Microsoft Cloud, Q2 FY26 (Business Today)", "https://www.businesstoday.in/amp/technology/news/story/microsoft-cloud-surpasses-50-billion-milestone-amid-global-ai-surge-profits-up-in-q2-26-513417-2026-01-29"),
    ("Microsoft Q4 FY26 (The Next Platform)", "https://www.nextplatform.com/cloud/2026/07/31/ai-dominates-the-microsoft-conversation-but-not-the-companys-business/5281992"),
    ("Q2 2026 cloud results (FourWeekMBA)", "https://fourweekmba.com/ai-google-cloud-aws-azure-q2-2026-ai-infrastructure/"),
]
CLOUD_REVENUE = {
    # quarter end: {segment: revenue}
    "2025-06-30": {"AWS": 30.87, "Google Cloud": 13.62, "Microsoft Cloud": 46.7},
    "2025-09-30": {"AWS": 33.0, "Google Cloud": 15.16, "Microsoft Cloud": 49.1},
    "2025-12-31": {"AWS": 35.6, "Google Cloud": 17.7, "Microsoft Cloud": 51.5},
    "2026-03-31": {"AWS": 37.6, "Google Cloud": 20.03, "Microsoft Cloud": 54.5},
    "2026-06-30": {"AWS": 42.2, "Google Cloud": 24.77, "Microsoft Cloud": 59.3},
}
CLOUD_OF = {"AWS": "Amazon", "Google Cloud": "Alphabet", "Microsoft Cloud": "Microsoft"}
# Cash purchases of property & equipment (excludes finance leases), from quarterly cash-flow statements
# (Financial Modeling Prep, pulled Oct 8, 2026)
CAPEX_SOURCE = ("Company cash-flow statements via Financial Modeling Prep (Oct 8, 2026)",
                "https://site.financialmodelingprep.com/")
CAPEX_QUARTERLY = {
    "2025-06-30": {"Amazon": 32.18, "Alphabet": 22.45, "Microsoft": 17.08, "Meta": 16.54},
    "2025-09-30": {"Amazon": 35.10, "Alphabet": 23.95, "Microsoft": 19.39, "Meta": 18.83},
    "2025-12-31": {"Amazon": 39.52, "Alphabet": 27.85, "Microsoft": 29.88, "Meta": 21.38},
    "2026-03-31": {"Amazon": 44.20, "Alphabet": 35.67, "Microsoft": 30.88, "Meta": 19.00},
    "2026-06-30": {"Amazon": 54.21, "Alphabet": 44.92, "Microsoft": 35.80, "Meta": 30.12},
}
# Explicit AI revenue disclosures (annualized run-rates), $B
AI_DISCLOSURES = [
    # date, company, label, run-rate $B, note, source
    ("2025-01-29", "Microsoft", "AI business run-rate", 13, "Disclosed on the Jan 2025 call",
     ("Microsoft FY25 Q2 earnings call", "https://www.microsoft.com/en-us/investor/earnings/fy-2025-q2/press-release-webcast")),
    ("2026-04-29", "Microsoft", "AI business run-rate", 37, "Up 123% YoY (Apr 2026 call)",
     ("Yahoo Finance: hyperscalers' Q1 2026", "https://finance.yahoo.com/sectors/technology/articles/hyperscalers-hit-700-billion-2026-111243744.html")),
    ("2026-07-29", "Microsoft", "AI business run-rate (estimate)", 44.5, "Not disclosed; The Next Platform estimate",
     ("The Next Platform (Jul 31, 2026)", "https://www.nextplatform.com/cloud/2026/07/31/ai-dominates-the-microsoft-conversation-but-not-the-companys-business/5281992")),
    ("2026-04-30", "Amazon", "Custom AI chips (Trainium) run-rate", 20, "Growing triple digits; one slice of AWS AI revenue",
     ("Yahoo Finance: hyperscalers' Q1 2026", "https://finance.yahoo.com/sectors/technology/articles/hyperscalers-hit-700-billion-2026-111243744.html")),
]
CLOUD_BACKLOG = [("Google Cloud", "Q1 2026", 460), ("Google Cloud", "Q2 2026", 514)]


# ---------------------------------------------------------------------------
# Compute rental prices ($ per GPU-hour, on-demand). Compiled Oct 18, 2026.
# Ornn's B200 / H200 / H100 / A100 history also loads live from its public API
# (trailing 3 months, no key); the figures here are the fallback and the
# longer history the free API doesn't cover.
# ---------------------------------------------------------------------------
COMPUTE_AS_OF = "Oct 17, 2026"
SILICON_INDEX = ("Silicon Data, Silicon Index GPU rental price indices",
                 "https://www.silicondata.com/products/silicon-index?gpu=h100")
SILICON_B300 = ("Silicon Data, B300 Rental Price Index", "https://www.silicondata.com/products/silicon-index/b300")
ORNN = ("Ornn Compute Price Index (OCPI)", "https://data.ornn.com/markets")
ORNN_B200 = ("Ornn OCPI-B200", "https://data.ornn.com/markets/b200")
ORNN_H200 = ("Ornn OCPI-H200", "https://data.ornn.com/markets/h200")
TUNGUZ = ("Tomasz Tunguz, 'GPU Spot Prices Surge 114% in Six Weeks' (Apr 2026), citing Ornn",
          "https://www.tomtunguz.com/b200-gpu-pricing-spot-market-model-releases/")
COMPUTE_DESK = ("Compute Desk DESKB300 index (Bloomberg), chart shared by @matthew_sigel", "https://compute-desk.com/")
CRYPTOBRIEFING = ("Crypto Briefing, 'Blackwell Ultra GPU rental prices climb 17 straight days to a record high'",
                  "https://cryptobriefing.com/blackwell-ultra-gpu-rental-prices-record-high/")

# Latest readings, Oct 17, 2026. Silicon Data: standardized blend of neocloud (and, where published,
# hyperscaler) rentals. Ornn: daily settle. None = not published.
GPU_RENTAL_LATEST = [
    # chip, generation, launched, SD neocloud, SD 7-day %, SD hyperscaler, Ornn, note
    ("B300", "Blackwell Ultra", 2025, 7.01, 0.9, None, None,
     "Compute Desk index hit a record 7.45 on Oct 14 after 17 straight daily gains"),
    ("B200", "Blackwell", 2024, 6.12, 7.0, None, 8.48, "Ornn up 12.6% in a week, 19.4% in a month"),
    ("H200", "Hopper", 2024, 3.51, 6.0, None, 6.39, "Ornn up 23.8% in a month"),
    ("H100", "Hopper", 2022, 2.82, 6.4, 7.15, 2.81, "Hyperscalers charge ~2.5x the neocloud rate"),
    ("MI300X", "AMD CDNA 3", 2023, 2.64, 0.0, None, None, "Cheapest current-gen accelerator; ROCm limits porting"),
    ("A100", "Ampere", 2020, 1.53, -3.2, 3.77, 0.97, "Two generations old, still above $1/hr"),
]

# Compute Desk B300 index (DESKB300). First and last points are stated on the Bloomberg chart;
# the ones in between (marked ~) are read off the chart and approximate.
DESK_B300 = [
    ("2025-11-03", 4.551, "52-week low"), ("2025-12-01", 4.83, "~"), ("2026-01-02", 4.86, "~"),
    ("2026-02-02", 4.94, "~"), ("2026-03-02", 5.21, "~"), ("2026-04-01", 5.64, "~"),
    ("2026-04-15", 5.99, "~ spring peak"), ("2026-05-01", 4.96, "~"), ("2026-05-15", 4.85, "~"),
    ("2026-06-01", 5.35, "~"), ("2026-07-01", 5.35, "~"), ("2026-08-03", 6.36, "~"),
    ("2026-09-01", 6.38, "~"), ("2026-09-15", 5.91, "~ September dip"),
    ("2026-10-14", 7.4534, "Record high, 17th straight daily gain"),
]

# Ornn B200 / H200 points (fallback when the live API is unreachable, and the pre-July history).
ORNN_HISTORY = [
    # gpu, date, $/GPU-hr, note, source
    ("B200", "2026-03-02", 2.31, "Early March", TUNGUZ),
    ("B200", "2026-04-27", 4.95, "Week of Apr 27", TUNGUZ),
    ("B200", "2026-08-31", 6.07, "August month-end", ORNN_B200),
    ("B200", "2026-09-30", 8.09, "September month-end", ORNN_B200),
    ("B200", "2026-10-11", 7.45, "", ORNN_B200), ("B200", "2026-10-12", 7.33, "", ORNN_B200),
    ("B200", "2026-10-13", 7.83, "", ORNN_B200), ("B200", "2026-10-14", 7.88, "", ORNN_B200),
    ("B200", "2026-10-15", 7.92, "", ORNN_B200), ("B200", "2026-10-16", 8.12, "", ORNN_B200),
    ("B200", "2026-10-17", 8.48, "Latest settle", ORNN_B200),
    ("H200", "2026-08-31", 4.42, "August month-end", ORNN_H200),
    ("H200", "2026-09-30", 5.58, "September month-end", ORNN_H200),
    ("H200", "2026-10-11", 5.61, "", ORNN_H200), ("H200", "2026-10-12", 5.24, "", ORNN_H200),
    ("H200", "2026-10-13", 5.51, "", ORNN_H200), ("H200", "2026-10-14", 6.12, "", ORNN_H200),
    ("H200", "2026-10-15", 6.51, "", ORNN_H200), ("H200", "2026-10-16", 6.34, "", ORNN_H200),
    ("H200", "2026-10-17", 6.39, "Latest settle", ORNN_H200),
]

# Plain-English guide to the chips on the Compute prices page, newest first.
# Announced = when the maker unveiled it; shipping = when it reached customers in volume.
CHIP_GUIDE = [
    # chip, maker, family (generation), announced, shipping in volume, memory, what it is
    ("B300", "Nvidia", "Blackwell Ultra", "Mar 2025", "Late 2025", "288 GB",
     "Nvidia's newest and most powerful chip. An upgraded B200 with 50% more memory, built for "
     "'reasoning' AI models that think through answers step by step."),
    ("B200", "Nvidia", "Blackwell", "Mar 2024", "Early 2025", "192 GB",
     "The generation after Hopper. Roughly 2–3 times faster than an H100 for training AI models, "
     "and more for answering questions. What the big AI labs are buying now."),
    ("H200", "Nvidia", "Hopper", "Nov 2023", "Mid 2024", "141 GB",
     "Same processor as the H100 but with more and faster memory, so it handles bigger models. "
     "A stopgap between Hopper and Blackwell."),
    ("H100", "Nvidia", "Hopper", "Mar 2022", "Early 2023", "80 GB",
     "The chip behind the post-ChatGPT boom and still the most widely installed AI chip. The "
     "industry's reference price for renting compute."),
    ("MI300X", "AMD", "CDNA 3 (AMD Instinct)", "Dec 2023", "Early 2024", "192 GB",
     "AMD's main rival to the H100 and H200: lots of memory for the money, but it runs on AMD's own "
     "software (ROCm) rather than Nvidia's (CUDA), so moving AI code onto it takes work."),
    ("A100", "Nvidia", "Ampere", "May 2020", "Mid 2020", "40–80 GB",
     "Two generations old. Trained GPT-3 and the first ChatGPT models. Still rented for smaller jobs; "
     "its price is a gauge of whether old chips are piling up unused."),
]
