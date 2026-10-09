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
    # company: latest, latest label, as of, early-2026 baseline, baseline date, source(s)
    "Oracle": (215, "215", "Jul 27, 2026", 144, "Start of 2026",
               ("Edward Conard macro roundup / LSEG (Jul 28, 2026)",
                "https://www.edwardconard.com/macro-roundup/big-tech-credit-risks-rise-sharply-as-ai-spending-soars/")),
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
    "CoreWeave": (855, "855+", "Jul 28, 2026", None, None,
                  ("Protos, citing CDS data (Jul 29, 2026)", "https://protos.com/credit-default-swaps-forecast-ai-bankruptcies/")),
    "Microsoft": (None, "—", None, 34, "Mid-Nov 2025",
                  ("ZeroHedge, citing S&P data (Nov 17, 2025)",
                   "https://www.zerohedge.com/markets/stocks-slide-after-amazon-shocks-another-massive-bond-offering-rebound-news-boaz-weinsten")),
}
CDS_BASELINE_SOURCE = ("ZeroHedge, citing S&P data (Nov 17, 2025): Alphabet ~38, Amazon ~38, Microsoft ~34bp",
                       "https://www.zerohedge.com/markets/stocks-slide-after-amazon-shocks-another-massive-bond-offering-rebound-news-boaz-weinsten")

ORACLE_CDS = {"latest_bp": 203, "year_ago_bp": 40, "note": "Record high since 2008 (ICE Data Services)",
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
