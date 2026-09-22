import data, adjusted_cost, chart_adjusted

print("Fetching LTC historical data (2011-2026)...")
ltc_raw = data.fetch_historical_data("ltc", "HashRate,PriceUSD", "2011-10-07")
if not ltc_raw:
    print("Error fetching LTC data"); exit(1)
print(f"  {len(ltc_raw)} LTC daily records")

print("Fetching DOGE historical data (2014-2026)...")
doge_raw = data.fetch_historical_data("doge", "HashRate,PriceUSD", "2013-12-08")
if not doge_raw:
    print("Error fetching DOGE data"); exit(1)
print(f"  {len(doge_raw)} DOGE daily records")

print("Calculating adjusted costs...")
costs = adjusted_cost.compute_ltc_historical_with_doge(ltc_raw, doge_raw)
print(f"  {len(costs)} data points computed")

print("Generating chart...")
path = chart_adjusted.create_adjusted_chart(costs, "ltc_adjusted_cost.png")
print(f"Chart saved: {path}")

# Print latest values
last = costs[-1]
print(f"\nDatos m\u00e1s recientes ({last['timestamp'].strftime('%Y-%m-%d')}):")
print(f"  Precio LTC:              ${last['price_usd']:.2f}" if last['price_usd'] else "  Precio LTC: N/A")
print(f"  Coste LTC solo:          ${last['cost_ltc_only']:.2f}" if last['cost_ltc_only'] else "")
print(f"  Bono DOGE:               +{last['doge_bonus_pct']:.1f}%" if last['doge_bonus_pct'] else "")
print(f"  Coste LTC con DOGE:      ${last['cost_ltc_with_doge']:.2f}" if last['cost_ltc_with_doge'] else "")

# Live check
print("\n--- DATOS EN VIVO ---")
live = adjusted_cost.calc_ltc_live_doge_adjusted()
if "error" not in live:
    print(f"  Precio LTC:     ${live['ltc_price']:.2f}")
    print(f"  Hashrate:       {live['hashrate_phs']:.2f} PH/s")
    print(f"  Coste solo LTC: ${live['cost_ltc_only']:.2f}")
    print(f"  Bono DOGE:      +{live['doge_bonus_pct']:.1f}%")
    print(f"  Coste con DOGE: ${live['cost_ltc_with_doge']:.2f}")
    if live['cost_ltc_with_doge'] and live['ltc_price']:
        ratio = live['ltc_price'] / live['cost_ltc_with_doge']
        print(f"  Ratio precio/coste (con DOGE): {ratio:.2f}x")
        print(f"  {'MINEROS RENTABLES (con DOGE)' if ratio > 1 else 'MINEROS EN PÉRDIDAS (incluso con DOGE)'}")
else:
    print(f"  Error: {live['error']}")
