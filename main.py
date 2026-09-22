import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data
from production_cost import calc_ltc_live, format_ltc_live, compute_historical_ltc, compute_historical_btc, calc_coin_production_cost
from chart import create_historical_chart_ltc, create_historical_chart_btc, create_live_chart
from adjusted_cost import compute_ltc_historical_with_doge
from chart_adjusted import create_adjusted_chart


def cmd_ltc_live(args):
    r = calc_ltc_live()
    print(format_ltc_live(r))


def cmd_ltc_chart(args):
    r = calc_ltc_live()
    if "error" in r:
        print(f"Error: {r['error']}")
        return
    doge_pct = r.get("doge_rev_share", 0) * 100
    ltc_share = r.get("ltc_rev_share", 1.0)
    doge_share = r.get("doge_rev_share", 0.0)
    p = create_live_chart(r["hashrate"], r["efficiency"], r["elec_price"], 6.25, "ltc",
                          price=r.get("price_usd"), doge_pct=doge_pct,
                          ltc_share=ltc_share, doge_share=doge_share,
                          save_path=args.output or "ltc_production_cost.png")
    print(f"Chart: {os.path.abspath(p)}")


def cmd_ltc_history(args):
    print("Fetching LTC historical data from Coin Metrics (2011-2026)...")
    raw = data.fetch_historical_data("ltc", "HashRate,PriceUSD", "2011-10-07")
    if not raw:
        print("Error: could not fetch")
        return
    print(f"  {len(raw)} daily records")
    costs = compute_historical_ltc(raw)
    p = create_historical_chart_ltc(costs, args.output or "ltc_historical_cost.png")
    print(f"Chart: {os.path.abspath(p)}")
    print(f"  Range: {costs[0]['timestamp'].strftime('%Y-%m-%d')} -> {costs[-1]['timestamp'].strftime('%Y-%m-%d')}")


def cmd_ltc_adjusted(args):
    print("Fetching LTC + DOGE historical data...")
    ltc_raw = data.fetch_historical_data("ltc", "HashRate,PriceUSD", "2011-10-07")
    doge_raw = data.fetch_historical_data("doge", "HashRate,PriceUSD", "2014-01-23")
    if not ltc_raw:
        print("Error: no LTC data")
        return
    print(f"  LTC: {len(ltc_raw)} records, DOGE: {len(doge_raw) if doge_raw else 0} records")
    costs = compute_ltc_historical_with_doge(ltc_raw, doge_raw or [])
    p = create_adjusted_chart(costs, args.output or "ltc_adjusted_cost.png")
    print(f"Chart: {os.path.abspath(p)}")
    if costs:
        print(f"  Range: {costs[0]['timestamp'].strftime('%Y-%m-%d')} -> {costs[-1]['timestamp'].strftime('%Y-%m-%d')}")


def cmd_btc_now(args):
    print("Fetching BTC live data...")
    raw = data.fetch_historical_data("btc", "HashRate,PriceUSD", "2026-06-20")
    if not raw or len(raw) < 2:
        print("Error: could not fetch")
        return
    latest = raw[-1]
    hashrate_ths = latest["hashrate"]
    price = latest["price_usd"]
    eff = data.btc_efficiency_at_date(latest["timestamp"].date())
    reward = data.btc_reward_at_date(latest["timestamp"].date())
    r = calc_coin_production_cost("btc", hashrate_ths, eff, 0.05, reward, 1.15)
    print(f"  Hashrate:       {r['hashrate_display']:.2f} {r['hashrate_unit']}")
    print(f"  Efficiency:     {eff:.3f} J/TH")
    print(f"  Elec Price:     $0.0500/kWh")
    print(f"  Block reward:   {reward} BTC")
    print(f"  Blocks/day:     144")
    print(f"  Cost per BTC:   ${r['cost_per_coin_total']:.2f}")
    print(f"  BTC Price:      ${price:.2f}")
    if price and r.get("cost_per_coin_total"):
        ratio = price / r["cost_per_coin_total"]
        gap = price - r["cost_per_coin_total"]
        print(f"  Ratio:          {ratio:.2f}x")
        print(f"  Gap:            ${gap:+.2f}")
        print(f"  STATUS:         {'ABOVE cost' if gap > 0 else 'BELOW cost'}")
    p = create_live_chart(hashrate_ths, eff, 0.05, reward, "btc", price=price,
                          save_path=args.output or "btc_current_cost.png")
    print(f"Chart: {os.path.abspath(p)}")


def cmd_btc_history(args):
    print("Fetching BTC historical data from Coin Metrics (2010-2026)...")
    raw = data.fetch_historical_data("btc", "HashRate,PriceUSD", "2010-01-01")
    if not raw:
        print("Error: could not fetch")
        return
    print(f"  {len(raw)} daily records")
    costs = compute_historical_btc(raw)
    p = create_historical_chart_btc(costs, args.output or "btc_historical_cost.png")
    print(f"Chart: {os.path.abspath(p)}")
    print(f"  Range: {costs[0]['timestamp'].strftime('%Y-%m-%d')} -> {costs[-1]['timestamp'].strftime('%Y-%m-%d')}")


def main():
    parser = argparse.ArgumentParser(description="Production Cost Analyzer")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("ltc", help="LTC commands")
    ltc_sub = p.add_subparsers(dest="subcommand")
    p1 = ltc_sub.add_parser("live", help="LTC current estimate")
    p1.set_defaults(func=cmd_ltc_live)
    p2 = ltc_sub.add_parser("chart", help="LTC current chart")
    p2.add_argument("-o", "--output")
    p2.set_defaults(func=cmd_ltc_chart)
    p3 = ltc_sub.add_parser("history", help="LTC historical chart (2011-2026)")
    p3.add_argument("-o", "--output")
    p3.set_defaults(func=cmd_ltc_history)
    p4 = ltc_sub.add_parser("adjusted", help="LTC historical chart with DOGE adjustment")
    p4.add_argument("-o", "--output")
    p4.set_defaults(func=cmd_ltc_adjusted)

    p = sub.add_parser("btc", help="BTC commands")
    btc_sub = p.add_subparsers(dest="subcommand")
    p1 = btc_sub.add_parser("now", help="BTC current estimate + chart")
    p1.add_argument("-o", "--output")
    p1.set_defaults(func=cmd_btc_now)
    p2 = btc_sub.add_parser("history", help="BTC historical chart (2010-2026)")
    p2.add_argument("-o", "--output")
    p2.set_defaults(func=cmd_btc_history)

    args = parser.parse_args()
    if hasattr(args, "func") and args.func:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
