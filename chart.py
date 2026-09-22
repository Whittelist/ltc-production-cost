import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date

def _style_ax(ax, title, ylabel):
    fig = ax.figure
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    ax.set_title(title, fontsize=15, fontweight="bold", color="white", pad=20)
    ax.set_ylabel(ylabel, fontsize=13, color="white")
    ax.tick_params(colors="white", labelsize=10)
    for s in ax.spines.values():
        s.set_color("#444")
    ax.grid(True, alpha=0.1, color="#555")

def create_historical_chart_ltc(historical, save_path="ltc_historical_cost.png"):
    fig, ax = plt.subplots(figsize=(16, 8))
    _style_ax(ax, "Litecoin: Price vs Estimated Production Cost (2011-2026)", "USD per LTC")

    dates = [h["timestamp"] for h in historical]
    prices = [h["price_usd"] for h in historical]
    costs = [h["cost_per_coin"] for h in historical]

    clean = [(d, p, c) for d, p, c in zip(dates, prices, costs) if p is not None and c is not None]
    if not clean:
        return
    cd, cp, cc = zip(*clean)

    ax.plot(cd, cp, color="#6bff6b", lw=0.8, alpha=0.7, label="LTC Price (USD)")
    ax.plot(cd, cc, color="#ff6b6b", lw=1.0, alpha=0.9, label="Est. Production Cost")
    ax.fill_between(cd, cc, cp, where=[p >= c for p, c in zip(cp, cc)], color="#6bff6b", alpha=0.04)
    ax.fill_between(cd, cc, cp, where=[p < c for p, c in zip(cp, cc)], color="#ff6b6b", alpha=0.04)

    ax.set_yscale("log")
    halvings = [(date(2015,8,25), "÷2"), (date(2019,8,25), "÷2"), (date(2023,8,2), "÷2")]
    for hd, hl in halvings:
        ax.axvline(x=hd, color="#ffd93d", lw=0.8, ls=":", alpha=0.5)
        ax.text(hd, ax.get_ylim()[1]*0.95, f" {hl}", color="#ffd93d", fontsize=8, alpha=0.7)

    ax.legend(fontsize=11, loc="upper left", facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path


def create_historical_chart_btc(historical, save_path="btc_historical_cost.png"):
    fig, ax = plt.subplots(figsize=(16, 8))
    _style_ax(ax, "Bitcoin: Price vs Estimated Production Cost (2010-2026)", "USD per BTC")

    dates = [h["timestamp"] for h in historical]
    prices = [h["price_usd"] for h in historical]
    costs = [h["cost_per_coin"] for h in historical]

    clean = [(d, p, c) for d, p, c in zip(dates, prices, costs) if p is not None and c is not None]
    if not clean:
        return
    cd, cp, cc = zip(*clean)

    ax.plot(cd, cp, color="#f7931a", lw=0.8, alpha=0.7, label="BTC Price (USD)")
    ax.plot(cd, cc, color="#ff6b6b", lw=1.0, alpha=0.9, label="Est. Production Cost")
    ax.fill_between(cd, cc, cp, where=[p >= c for p, c in zip(cp, cc)], color="#f7931a", alpha=0.04)
    ax.fill_between(cd, cc, cp, where=[p < c for p, c in zip(cp, cc)], color="#ff6b6b", alpha=0.04)

    ax.set_yscale("log")
    halvings = [(date(2012,11,28), "÷2"), (date(2016,7,9), "÷2"), (date(2020,5,11), "÷2"), (date(2024,4,20), "÷2")]
    for hd, hl in halvings:
        ax.axvline(x=hd, color="#ffd93d", lw=0.8, ls=":", alpha=0.5)
        ax.text(hd, ax.get_ylim()[1]*0.95, f" {hl}", color="#ffd93d", fontsize=8, alpha=0.7)

    ax.legend(fontsize=11, loc="upper left", facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path


def create_live_chart(hashrate, efficiency, elec_price, block_reward, coin, price=None,
                      doge_pct=0, ltc_share=1.0, doge_share=0.0, save_path=None):
    fig, ax = plt.subplots(figsize=(12, 7))
    unit = "J/MH (Scrypt)" if coin == "ltc" else "J/TH (SHA-256)"
    coin_name = "Litecoin" if coin == "ltc" else "Bitcoin"

    from production_cost import calc_coin_production_cost
    r = calc_coin_production_cost(coin, hashrate, efficiency, elec_price, block_reward)
    r_doge = calc_coin_production_cost(coin, hashrate, efficiency, elec_price, block_reward,
                                       ltc_rev_share=ltc_share, doge_rev_share=doge_share)

    elec_v = r["cost_per_coin_elec"] or 0
    total_v = r["cost_per_coin_total"] or 0
    doge_v = r_doge.get("cost_per_coin_with_doge")
    max_y = max(elec_v, total_v, doge_v or 0, price or 0) * 1.5 or 100

    ax.axhline(elec_v, color="#00d4ff", ls="--", lw=2, label=f"Electricity Only: ${elec_v:.2f}")
    ax.axhline(total_v, color="#ff6b6b", ls="--", lw=2, label=f"Total Cost: ${total_v:.2f}")
    if doge_v:
        ax.axhline(doge_v, color="#ffd93d", ls="--", lw=2, label=f"Cost w/ DOGE: ${doge_v:.2f}")
    if price:
        ax.axhline(price, color="#6bff6b", ls="-", lw=2.5, label=f"{coin_name} Price: ${price:.2f}")

    ax.set_xlim(0, 1); ax.set_ylim(0, max_y); ax.set_xticks([])
    _style_ax(ax, f"{coin_name} Production Cost vs Market Price", f"USD per {coin_name.upper()}")

    info = (f"Hashrate: {r['hashrate_display']:.2f} {r['hashrate_unit']}\n"
            f"Efficiency: {efficiency:.3f} {unit}\n"
            f"Elec: ${elec_price:.4f}/kWh\n"
            f"Reward: {block_reward} {coin_name[:3].upper()}\n"
            f"Rev share: LTC {ltc_share*100:.1f}% / DOGE {doge_share*100:.1f}%")
    ax.text(0.98, 0.95, info, transform=ax.transAxes, fontsize=10, va="top", ha="right",
            color="#aaa", family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#111", alpha=0.7, edgecolor="#333"))

    ax.legend(fontsize=11, loc="upper left", facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
    plt.tight_layout()
    fig.savefig(save_path or f"{coin}_cost.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path
