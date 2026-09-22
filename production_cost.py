import data
from datetime import datetime

BLOCKS_PER_DAY = {"ltc": 576, "btc": 144}
EFFICIENCY_UNIT = {"ltc": "J/MH", "btc": "J/TH"}

def calc_coin_production_cost(
    coin: str,
    hashrate: float,
    efficiency: float,
    elec_price: float,
    block_reward: float,
    overhead_factor: float = 1.0,
    ltc_rev_share: float = 1.0,
    doge_rev_share: float = 0.0,
) -> dict:
    power_watts = hashrate * efficiency
    daily_kwh = power_watts * 24 / 1000
    daily_elec_cost = daily_kwh * elec_price
    total_cost = daily_elec_cost * overhead_factor
    daily_mined = BLOCKS_PER_DAY[coin] * block_reward

    cost_elec = daily_elec_cost / daily_mined if daily_mined > 0 else None
    cost_total = total_cost / daily_mined if daily_mined > 0 else None

    cost_doge = None
    cost_ltc_allocated = None
    if doge_rev_share > 0:
        cost_allocated_ltc = total_cost * ltc_rev_share
        cost_ltc_allocated = cost_allocated_ltc / daily_mined if daily_mined > 0 else None
        effective_mined = daily_mined / ltc_rev_share if ltc_rev_share > 0 else float('inf')
        cost_doge = total_cost / effective_mined if effective_mined > 0 and ltc_rev_share > 0 else None

    phs = hashrate / 1_000_000 if coin == "btc" else hashrate / 1_000_000_000
    power_mw = power_watts / 1_000_000

    return {
        "hashrate": hashrate,
        "hashrate_display": phs,
        "hashrate_unit": "EH/s" if coin == "btc" else "PH/s",
        "power_watts": power_watts,
        "power_mw": power_mw,
        "daily_kwh": daily_kwh,
        "daily_elec_cost": daily_elec_cost,
        "daily_mined": daily_mined,
        "total_daily_cost": total_cost,
        "cost_per_coin_elec": cost_elec,
        "cost_per_coin_total": cost_total,
        "cost_per_coin_with_doge": cost_doge,
        "cost_per_coin_ltc_allocated": cost_ltc_allocated,
    }


def compute_historical_ltc(data_points: list[dict]) -> list[dict]:
    result = []
    for h in data_points:
        d = h["timestamp"].date()
        hashrate_mhs = h["hashrate"] * 1_000_000
        eff = data.ltc_efficiency_at_date(d)
        reward = data.ltc_reward_at_date(d)
        r = calc_coin_production_cost("ltc", hashrate_mhs, eff, 0.05, reward, 1.15)
        result.append({
            "timestamp": h["timestamp"],
            "price_usd": h["price_usd"],
            "cost_per_coin": r["cost_per_coin_total"],
            "hashrate_display": r["hashrate_display"],
            "efficiency": eff,
            "block_reward": reward,
        })
    return result


def compute_historical_btc(data_points: list[dict]) -> list[dict]:
    result = []
    for h in data_points:
        d = h["timestamp"].date()
        hashrate_ths = h["hashrate"]
        eff = data.btc_efficiency_at_date(d)
        reward = data.btc_reward_at_date(d)
        r = calc_coin_production_cost("btc", hashrate_ths, eff, 0.05, reward, 1.15)
        result.append({
            "timestamp": h["timestamp"],
            "price_usd": h["price_usd"],
            "cost_per_coin": r["cost_per_coin_total"],
            "hashrate_display": r["hashrate_display"],
            "efficiency": eff,
            "block_reward": reward,
        })
    return result


def calc_ltc_live():
    stats = data.fetch_ltc_stats()
    if not stats:
        return {"error": "Could not fetch LTC stats"}
    h_hs = data.get_hashrate_from_stats(stats)
    if not h_hs:
        return {"error": "Could not calc hashrate"}
    hashrate_mhs = h_hs / 1e6
    eff = data.estimate_avg_efficiency_J_MH()
    elec = data.estimate_electricity_price()
    overhead = data.estimate_overhead_factor()
    ltc_hr_ghs = h_hs / 1e9

    doge_stats = data.fetch_doge_stats()
    rev_share = data.calc_merged_revenue_share(stats, doge_stats, ltc_hr_ghs) if doge_stats else None

    if rev_share:
        result = calc_coin_production_cost(
            "ltc", hashrate_mhs, eff, elec, 6.25, overhead,
            ltc_rev_share=rev_share["ltc_share"],
            doge_rev_share=rev_share["doge_share"]
        )
    else:
        result = calc_coin_production_cost("ltc", hashrate_mhs, eff, elec, 6.25, overhead)

    ltc_price = stats.get("market_price_usd")
    result["price_usd"] = float(ltc_price) if ltc_price else None
    result["efficiency"] = eff
    result["elec_price"] = elec

    if rev_share:
        result["ltc_rev_share"] = rev_share["ltc_share"]
        result["doge_rev_share"] = rev_share["doge_share"]
        result["ltc_revenue"] = rev_share["ltc_revenue"]
        result["doge_revenue"] = rev_share["doge_revenue"]
        result["total_revenue"] = rev_share["total_revenue"]
        result["ltc_fees"] = rev_share["ltc_fees"]
        result["doge_fees"] = rev_share["doge_fees"]
    else:
        result["ltc_rev_share"] = 1.0
        result["doge_rev_share"] = 0.0

    if result.get("price_usd") and result.get("cost_per_coin_total"):
        result["ratio"] = result["price_usd"] / result["cost_per_coin_total"]
        result["gap"] = result["price_usd"] - result["cost_per_coin_total"]
    if result.get("price_usd") and result.get("cost_per_coin_with_doge"):
        result["ratio_doge"] = result["price_usd"] / result["cost_per_coin_with_doge"]
    if result.get("price_usd") and result.get("cost_per_coin_ltc_allocated"):
        result["ratio_allocated"] = result["price_usd"] / result["cost_per_coin_ltc_allocated"]
    return result


def calc_btc_live():
    hashrate_ths = 600
    eff = data.estimate_btc_efficiency_J_TH()
    elec = data.estimate_electricity_price()
    overhead = data.estimate_overhead_factor()
    result = calc_coin_production_cost("btc", hashrate_ths, eff, elec, 3.125, overhead)
    result["efficiency"] = eff
    result["elec_price"] = elec
    return result


def format_ltc_live(r: dict) -> str:
    lines = ["=" * 60, "       LITECOIN PRODUCTION COST ESTIMATE", "=" * 60]
    if "error" in r:
        return f"ERROR: {r['error']}"
    lines.append(f"  Network Hashrate:       {r['hashrate_display']:.2f} {r['hashrate_unit']}")
    lines.append(f"  Avg Miner Efficiency:   {r['efficiency']:.3f} J/MH")
    lines.append(f"  Electricity Price:      ${r['elec_price']:.4f} /kWh")
    lines.append("")
    lines.append(f"  Network Power:          {r['power_mw']:.1f} MW")
    lines.append(f"  Daily Energy:           {r['daily_kwh']:,.0f} kWh")
    lines.append(f"  Daily Elec Cost:        ${r['daily_elec_cost']:,.0f}")
    lines.append(f"  Daily Total Cost:       ${r['total_daily_cost']:,.0f}")
    lines.append(f"  Daily LTC Mined:        {r['daily_mined']:,.1f} LTC")
    lines.append("")
    ce = r.get("cost_per_coin_elec")
    ct = r.get("cost_per_coin_total")
    if ce: lines.append(f"  Cost per LTC (elec):          ${ce:.2f}")
    if ct: lines.append(f"  Cost per LTC (total):         ${ct:.2f}")
    lines.append("")
    ltc_s = r.get("ltc_rev_share", 1.0)
    doge_s = r.get("doge_rev_share", 0.0)
    if doge_s > 0.01:
        lines.append(f"  --- REVENUE SHARE (merged mining LTC+DOGE) ---")
        tr = r.get("total_revenue", 0)
        lr = r.get("ltc_revenue", 0)
        dr = r.get("doge_revenue", 0)
        lf = r.get("ltc_fees", 0)
        df = r.get("doge_fees", 0)
        if tr:
            lines.append(f"  Total daily revenue:     ${tr:,.0f}")
            lines.append(f"    LTC blocks:            ${lr:,.0f}  ({ltc_s*100:.1f}%)")
            lines.append(f"      Block rewards:       ${lr-lf:,.0f}")
            lines.append(f"      Transaction fees:    ${lf:,.0f}")
            lines.append(f"    DOGE blocks:           ${dr:,.0f}  ({doge_s*100:.1f}%)")
            lines.append(f"      Block rewards:       ${dr-df:,.0f}")
            lines.append(f"      Transaction fees:    ${df:,.0f}")
        cw = r.get("cost_per_coin_with_doge")
        ca = r.get("cost_per_coin_ltc_allocated")
        if cw: lines.append(f"  Cost per LTC (effective, w/ DOGE): ${cw:.2f}")
        if ca: lines.append(f"  Cost per LTC (allocated LTC share): ${ca:.2f}")
    lines.append("")
    p = r.get("price_usd")
    if p: lines.append(f"  LTC Market Price:             ${p:.2f}")
    ratio = r.get("ratio")
    gap = r.get("gap")
    ratio_d = r.get("ratio_doge")
    if ratio is not None and gap is not None:
        lines.append(f"  Price/Cost (LTC only):        {ratio:.2f}x  (gap: ${gap:+.2f})")
        lines.append(f"  STATUS (LTC only):            {'PROFITABLE' if gap > 0 else 'BELOW COST'}")
    if ratio_d is not None:
        lines.append(f"  Price/Cost (w/ DOGE):         {ratio_d:.2f}x")
        pr = r.get("cost_per_coin_with_doge")
        if pr:
            g2 = p - pr if p else 0
            lines.append(f"  STATUS (w/ DOGE):             {'PROFITABLE' if g2 > 0 else 'BELOW COST'}")
    lines.append("=" * 60)
    return "\n".join(lines)
