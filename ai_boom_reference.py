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

RATINGS = [
    # company, S&P, Moody's, notches above junk (S&P scale), as of, note, source
    ("Microsoft", "AAA", "—", 9, "2026", "No new bonds in 2026 to date",
     ("MarketBeat", "https://www.marketbeat.com/articles/oracle-is-one-step-from-junkcan-it-afford-the-ai-boom/")),
    ("Alphabet", "AA+", "—", 8, "2026", "Raised $85B of equity alongside debt",
     ("MarketBeat", "https://www.marketbeat.com/articles/oracle-is-one-step-from-junkcan-it-afford-the-ai-boom/")),
    ("Amazon", "AA", "—", 7, "2026", "TTM free cash flow negative after Q2",
     ("MarketBeat", "https://www.marketbeat.com/articles/oracle-is-one-step-from-junkcan-it-afford-the-ai-boom/")),
    ("Meta", "AA-", "Aa3", 6, "Aug 2026", "Off-balance-sheet data center JVs add to obligations",
     ("Financial News (Korea), Aug 30, 2026", "https://en.fnnews.com/news/202608291254188090")),
    ("Oracle", "BBB-", "—", 0, "Jul 9, 2026", "Cut from BBB, stable outlook; 5-yr CDS above 200bp",
     ("PPC Land", "https://ppc.land/s-p-cuts-oracle-to-bbb-as-ai-buildout-widens-cash-deficit-to-42bn/")),
]
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
