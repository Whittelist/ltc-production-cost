import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def create_adjusted_chart(historical, save_path="ltc_adjusted_cost.png"):
    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    dates = [h["timestamp"] for h in historical]
    prices = [h["price_usd"] for h in historical]
    costs_only = [h["cost_ltc_only"] for h in historical]
    costs_doge = [h["cost_ltc_with_doge"] for h in historical]
    costs_alloc = [h.get("cost_ltc_allocated") for h in historical]

    clean = [(d, p, c_l, c_d, c_a) for d, p, c_l, c_d, c_a
             in zip(dates, prices, costs_only, costs_doge, costs_alloc)
             if p is not None and c_l is not None and c_l > 0]

    if not clean:
        print("No valid data points")
        return
    cd, cp, cc_l, cc_d, cc_a = zip(*clean)

    ax.plot(cd, cp, color="#6bff6b", lw=0.8, alpha=0.7, label="LTC Price (USD)")
    ax.plot(cd, cc_l, color="#ff6b6b", lw=1.0, alpha=0.9, label="Cost LTC-only (sin DOGE)")

    valid_doge = [(d, c_d) for d, c_d in zip(cd, cc_d) if c_d is not None and c_d > 0]
    if valid_doge:
        dd, dc = zip(*valid_doge)
        ax.plot(dd, dc, color="#ffd93d", lw=1.0, alpha=0.9, label="Cost LTC (efectivo c/DOGE)")

    valid_alloc = [(d, c_a) for d, c_a in zip(cd, cc_a) if c_a is not None and c_a > 0]
    if valid_alloc:
        da, ca = zip(*valid_alloc)
        ax.plot(da, ca, color="#00d4ff", lw=0.8, ls="--", alpha=0.6, label="Cost LTC (coste asignado)")

    ax.fill_between(cd, cc_l, cp, where=[p >= c for p, c in zip(cp, cc_l)], color="#6bff6b", alpha=0.04)
    ax.fill_between(cd, cc_l, cp, where=[p < c for p, c in zip(cp, cc_l)], color="#ff6b6b", alpha=0.04)

    ax.set_yscale("log")
    ax.set_ylabel("USD per LTC (log scale)", fontsize=13, color="white")
    ax.set_title("Litecoin: Precio vs Coste de Producción Ajustado por DOGE", fontsize=14, fontweight="bold", color="white", pad=20)
    ax.tick_params(colors="white", labelsize=10)
    for s in ax.spines.values():
        s.set_color("#444")
    ax.grid(True, alpha=0.1, color="#555")
    ax.legend(fontsize=10, loc="upper left", facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path
