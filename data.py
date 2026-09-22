import requests
import time
from datetime import datetime, timezone, date
from typing import Optional

COINMETRICS = "https://community-api.coinmetrics.io/v4"
BLOCKCHAIR_LTC = "https://api.blockchair.com/litecoin"
BLOCKCHAIR_DOGE = "https://api.blockchair.com/dogecoin"
LTC_BLOCK_TIME = 150

session = requests.Session()
session.headers.update({"User-Agent": "Crypto-Mining-Cost/1.0"})
_last_call = 0

def _rate_get(url, params=None, timeout=60):
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < 0.3:
        time.sleep(0.3 - elapsed)
    _last_call = time.time()
    for attempt in range(3):
        try:
            resp = session.get(url, params=params, timeout=timeout)
            if resp.status_code == 429:
                time.sleep(3)
                continue
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(2 ** attempt)
        except requests.HTTPError:
            if attempt == 2:
                return None
            time.sleep(2 ** attempt)
    return None

# --- LTC LIVE ---
def fetch_ltc_stats():
    resp = _rate_get(f"{BLOCKCHAIR_LTC}/stats")
    return resp.json().get("data") if resp else None

def fetch_doge_stats():
    resp = _rate_get(f"{BLOCKCHAIR_DOGE}/stats")
    return resp.json().get("data") if resp else None

def get_hashrate_from_stats(stats):
    d = stats.get("difficulty")
    return float(d) * (2**32) / LTC_BLOCK_TIME if d is not None else None

def get_doge_hashrate_ghs(stats):
    hr = stats.get("hashrate_24h")
    if hr is not None:
        return float(hr) / 1e9
    diff = stats.get("difficulty")
    if diff is not None:
        return float(diff) * (2**32) / 60 / 1e9
    return None

def parse_fee_usd_24h(stats):
    fee = stats.get("average_transaction_fee_usd_24h")
    txs = stats.get("transactions_24h")
    if fee is not None and txs is not None and float(txs) > 0:
        return float(fee) * float(txs)
    return 0.0

def calc_merged_revenue_share(ltc_stats, doge_stats, ltc_hr_ghs):
    ltp = float(ltc_stats.get("market_price_usd", 0) or 0)
    dop = float(doge_stats.get("market_price_usd", 0) or 0)
    ltc_block_reward = 6.25
    doge_block_reward = 10000
    ltc_fees = parse_fee_usd_24h(ltc_stats)
    doge_fees = parse_fee_usd_24h(doge_stats)

    ltc_blocks_day = 576
    doge_blocks_day = 1440

    ltc_rev_total = ltc_blocks_day * ltc_block_reward * ltp + ltc_fees
    doge_rev_total = doge_blocks_day * doge_block_reward * dop + doge_fees

    total_rev = ltc_rev_total + doge_rev_total
    if total_rev == 0:
        return {
            "ltc_revenue": 0, "doge_revenue": 0, "total_revenue": 0,
            "ltc_share": 0.5, "doge_share": 0.5,
            "ltc_rev_per_ghs": 0, "doge_rev_per_ghs": 0,
            "ltc_fees": 0, "doge_fees": 0,
        }

    ltc_share = ltc_rev_total / total_rev
    doge_share = doge_rev_total / total_rev

    return {
        "ltc_revenue": ltc_rev_total,
        "doge_revenue": doge_rev_total,
        "total_revenue": total_rev,
        "ltc_share": ltc_share,
        "doge_share": doge_share,
        "ltc_rev_per_ghs": ltc_rev_total / ltc_hr_ghs if ltc_hr_ghs > 0 else 0,
        "doge_rev_per_ghs": doge_rev_total / ltc_hr_ghs if ltc_hr_ghs > 0 else 0,
        "ltc_fees": ltc_fees,
        "doge_fees": doge_fees,
    }

# --- HISTORICAL DATA (Coin Metrics) ---
def fetch_historical_data(asset="ltc", metrics="HashRate,PriceUSD", start="2011-10-07"):
    params = {
        "assets": asset,
        "metrics": metrics,
        "frequency": "1d",
        "start_time": start,
        "page_size": 10000,
        "pretty": "false"
    }
    resp = _rate_get(f"{COINMETRICS}/timeseries/asset-metrics", params=params, timeout=120)
    if resp is None:
        return None
    raw = resp.json().get("data", [])
    result = []
    for entry in raw:
        ts_str = entry.get("time", "")
        if ts_str:
            result.append({
                "timestamp": datetime.fromisoformat(ts_str.replace("Z", "+00:00")),
                "hashrate": float(entry.get("HashRate", 0)),
                "price_usd": float(entry["PriceUSD"]) if entry.get("PriceUSD") else None,
            })
    return result

# --- BTC PARAMS ---
BTC_HALVING_DATES = [
    (date(2009, 1, 3), 50),
    (date(2012, 11, 28), 25),
    (date(2016, 7, 9), 12.5),
    (date(2020, 5, 11), 6.25),
    (date(2024, 4, 20), 3.125),
]

def btc_reward_at_date(d):
    reward = 50
    for hd, hr in BTC_HALVING_DATES:
        if d >= hd:
            reward = hr
    return reward

def btc_efficiency_at_date(d):
    y = d.year + (d.timetuple().tm_yday - 1) / 366.0
    if y < 2011: return 5000000.0
    elif y < 2012: return 600000.0
    elif y < 2013: return 200000.0
    elif y < 2014: return 50000.0
    elif y < 2016: return 1000.0
    elif y < 2018: return 100.0
    elif y < 2020: return 40.0
    elif y < 2022: return 30.0
    elif y < 2024: return 22.0
    else: return 18.0

# --- LTC PARAMS ---
LTC_HALVING_DATES = [
    (date(2011, 10, 7), 50),
    (date(2015, 8, 25), 25),
    (date(2019, 8, 25), 12.5),
    (date(2023, 8, 2), 6.25),
]

def ltc_reward_at_date(d):
    reward = 50
    for hd, hr in LTC_HALVING_DATES:
        if d >= hd:
            reward = hr
    return reward

def ltc_efficiency_at_date(d):
    y = d.year + (d.timetuple().tm_yday - 1) / 366.0
    if y < 2013: return 20.0
    elif y < 2014: return 5.0
    elif y < 2015: return 1.5
    elif y < 2016: return 0.8
    elif y < 2018: return 0.5
    elif y < 2020: return 0.40
    elif y < 2022: return 0.36
    elif y < 2024: return 0.32
    elif y < 2025: return 0.28
    else: return 0.24

# --- LIVE ESTIMATES (current) ---
def estimate_avg_efficiency_J_MH():
    return 0.24

def estimate_btc_efficiency_J_TH():
    return 18.0

def estimate_electricity_price():
    return 0.05

def estimate_overhead_factor():
    return 1.15
