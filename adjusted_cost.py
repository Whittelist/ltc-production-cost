import data
from datetime import date

BLOCKS_LTC = {"day": 576, "reward": 6.25}
BLOCKS_DOGE = {"day": 1440, "reward": 10000}

def calc_coin_production_cost(hashrate, efficiency, elec_price, block_reward,
                               overhead=1.15, ltc_share=1.0, doge_share=0.0):
    power_w = hashrate * efficiency
    daily_kwh = power_w * 24 / 1000
    daily_elec = daily_kwh * elec_price
    daily_mined = BLOCKS_LTC["day"] * block_reward
    total_cost = daily_elec * overhead

    cost_elec = daily_elec / daily_mined if daily_mined else None
    cost_total = total_cost / daily_mined if daily_mined else None
    cost_doge = None
    cost_allocated = None

    if doge_share > 0:
        allocated = total_cost * ltc_share
        cost_allocated = allocated / daily_mined if daily_mined else None
        effective_mined = daily_mined / ltc_share if ltc_share > 0 else float('inf')
        cost_doge = total_cost / effective_mined if effective_mined and ltc_share > 0 else None

    return {
        "cost_ltc_only": cost_total,
        "cost_ltc_with_doge": cost_doge,
        "cost_ltc_allocated": cost_allocated,
        "daily_mined": daily_mined,
        "power_mw": power_w / 1e6,
        "daily_cost": total_cost,
        "ltc_share": ltc_share,
        "doge_share": doge_share,
    }

def calc_historic_revenue_share(ltc_hr, ltc_price, doge_hr, doge_price):
    if not all([ltc_hr, ltc_price, doge_hr, doge_price]):
        return {"ltc_share": 1.0, "doge_share": 0.0}
    if ltc_hr <= 0 or ltc_price <= 0:
        return {"ltc_share": 1.0, "doge_share": 0.0}
    ltc_rev = BLOCKS_LTC["day"] * BLOCKS_LTC["reward"] * ltc_price
    doge_rev = BLOCKS_DOGE["day"] * BLOCKS_DOGE["reward"] * doge_price
    total = ltc_rev + doge_rev
    if total == 0:
        return {"ltc_share": 0.5, "doge_share": 0.5}
    return {"ltc_share": ltc_rev / total, "doge_share": doge_rev / total}

def compute_ltc_historical_with_doge(ltc_data, doge_data):
    doge_map = {}
    for d in doge_data:
        key = d["timestamp"].strftime("%Y-%m-%d")
        doge_map[key] = {"hr": d["hashrate"], "price": d["price_usd"]}

    result = []
    for h in ltc_data:
        d = h["timestamp"]
        key = d.strftime("%Y-%m-%d")
        ltc_hr = h["hashrate"]
        ltc_price_val = h["price_usd"]
        eff = data.ltc_efficiency_at_date(d.date())
        reward = data.ltc_reward_at_date(d.date())

        doge_info = doge_map.get(key)
        if doge_info and doge_info.get("price"):
            rs = calc_historic_revenue_share(ltc_hr, ltc_price_val,
                                              doge_info["hr"], doge_info["price"])
        else:
            rs = {"ltc_share": 1.0, "doge_share": 0.0}

        r = calc_coin_production_cost(ltc_hr * 1_000_000, eff, 0.05, reward,
                                      1.15, rs["ltc_share"], rs["doge_share"])
        result.append({
            "timestamp": d,
            "price_usd": ltc_price_val,
            "cost_ltc_only": r["cost_ltc_only"],
            "cost_ltc_with_doge": r["cost_ltc_with_doge"],
            "cost_ltc_allocated": r["cost_ltc_allocated"],
            "doge_bonus_pct": rs["doge_share"] * 100,
            "ltc_share": rs["ltc_share"],
            "doge_share": rs["doge_share"],
        })
    return result

def calc_ltc_live_doge_adjusted():
    stats = data.fetch_ltc_stats()
    if not stats:
        return {"error": "no stats"}
    h_hs = data.get_hashrate_from_stats(stats)
    if not h_hs:
        return {"error": "no hashrate"}
    ltc_price = float(stats.get("market_price_usd", 0))
    ltc_ghs = h_hs / 1e9

    doge_stats = data.fetch_doge_stats()
    rs = {"ltc_share": 1.0, "doge_share": 0.0}
    doge_price = 0
    if doge_stats:
        dp = doge_stats.get("market_price_usd")
        doge_price = float(dp) if dp else 0
        rs = calc_historic_revenue_share(ltc_ghs, ltc_price, 1, doge_price)

    hashrate_mhs = h_hs / 1e6
    eff = data.estimate_avg_efficiency_J_MH()
    r = calc_coin_production_cost(hashrate_mhs, eff, 0.05, 6.25, 1.15,
                                   rs["ltc_share"], rs["doge_share"])

    return {
        "ltc_price": ltc_price,
        "cost_ltc_only": r["cost_ltc_only"],
        "cost_ltc_with_doge": r["cost_ltc_with_doge"],
        "cost_ltc_allocated": r["cost_ltc_allocated"],
        "doge_bonus_pct": rs["doge_share"] * 100,
        "doge_price": doge_price,
        "hashrate_phs": h_hs / 1e15,
        "ltc_share": rs["ltc_share"],
        "doge_share": rs["doge_share"],
    }
