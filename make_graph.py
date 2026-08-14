import os
import matplotlib.pyplot as plt
import numpy as np
import argparse
from model.Player import Player
from parse_data import operative_budget

def main():
    parser = argparse.ArgumentParser(description="Genera un grafico per l'analisi dinamica del prezzo di vendita di un giocatore.")
    parser.add_argument("--position", type=str, required=True, help="Posizione del giocatore (es. 'F', 'M', 'D', 'G')")
    parser.add_argument("--age", type=int, required=True, help="Età del giocatore")
    parser.add_argument("--main", type=int, required=True, help="Main stat del giocatore")
    parser.add_argument("--base_value", type=float, required=True, help="Valore base del giocatore in milioni")
    parser.add_argument("--market_value", type=float, required=True, help="Valore di mercato del giocatore in milioni")
    parser.add_argument("--matchday", type=int, default=1, help="Giornata di campionato (default: 1)")
    parser.add_argument("--budget", type=float, default=40.0, help="Budget totale disponibile in milioni (default: 40.0)")
    parser.add_argument("--free-slots", type=int, default=1, help="Numero di slot liberi nel budget operativo (default: 1)")
    args = parser.parse_args()

    # example usage: python make_graph.py --position F --age 25 --main 82 --base_value 12.5 --market_value 10.0 --matchday 1 --budget 40.0 --free-slots 1

    player = Player(
        name="Test Player",
        position=args.position,
        age=args.age,
        nationality="Testland",
        club="Test FC",
        attack=80,
        defense=70,
        overall=args.main,
        main_stat=args.main,
        market_value=args.market_value,
        base_value=args.base_value
    )
    make_graph(player, args.budget, args.matchday, args.free_slots)

def make_graph(player: Player, budget: float, matchday: int, free_slots: int):
    print(f"Generating graph for {player.name} (Position: {player.position}, Age: {player.age}, Main Stat: {player.main_stat}, Base Value: {player.base_value}M, Market Value: {player.market_value}M, Matchday: {matchday})")
    op_budget = operative_budget(budget, 0, 0, free_slots)

    # 2. Calcolo del punto ottimale secondo l'algoritmo
    sp_result = player.selling_price(budget=budget, operative_budget=op_budget, matchday=matchday)
    p_opt = sp_result["price"]
    score_opt = sp_result["score"]

    # 3. Generazione dell'asse X (Prezzi di vendita nell'intervallo ammissibile)
    start_price = player.base_value
    end_price = player.max_price()
    x = np.linspace(start_price, end_price, 500)

    # 4. Calcolo dei valori Y per ogni prezzo candidato
    p_sale_vals = []
    ev_vals = []
    roce_vals = []
    score_vals = []

    for p in x:
        details = player.score(p, matchday=matchday, budget=budget, operative_budget=op_budget)
        p_sale_vals.append(details["p_sale"])
        ev_vals.append(details["ev"])
        roce_vals.append(details["roce"])
        score_vals.append(details["final_score"])

    p_sale_vals = np.array(p_sale_vals)
    ev_vals = np.array(ev_vals)
    roce_vals = np.array(roce_vals)
    score_vals = np.array(score_vals)

    # 5. Creazione della figura con 3 Subplot sovrapposti
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    # --- Grafico 1: Probabilità di Vendita ---
    ax1.plot(x, p_sale_vals * 100, label=r"$P_{sale}\ (\%)$", color="#1f77b4", linewidth=2)
    ax1.set_ylabel("Prob. Vendita (%)", fontsize=11)
    ax1.set_title(f"Analisi Dinamica Prezzo di Vendita per {player.name} (Matchday {matchday})", fontsize=14, pad=12)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right")

    # --- Grafico 2: Estimated Value (EV) & ROCE ---
    ax2.plot(x, ev_vals, label=r"EV (Profitto $\times P_{sale}^2$)", color="#2ca02c", linewidth=2)
    ax2.set_ylabel("EV (M€)", fontsize=11)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left")

    # Asse secondario per il ROCE
    ax2_twin = ax2.twinx()
    ax2_twin.plot(x, roce_vals, label="ROCE", color="#ff7f0e", linestyle="--", linewidth=1.5)
    ax2_twin.set_ylabel("ROCE", fontsize=11)
    ax2_twin.legend(loc="upper right")

    # --- Grafico 3: Score Algoritmetico Finale ---
    ax3.plot(x, score_vals, label="Score Finale (Prezzo Ottimale)", color="#d62728", linewidth=2.5)
    ax3.set_xlabel("Prezzo di Vendita candidato $P$ (M€)", fontsize=12)
    ax3.set_ylabel("Algorithmic Score", fontsize=11)
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="upper left")

    # Highlight del Prezzo Ottimale P* su tutti i subplots
    for ax in (ax1, ax2, ax3):
        ax.axvline(p_opt, color="black", linestyle="--", alpha=0.7, linewidth=1.2)

    # Punto di massimo evidenziato sullo Score
    ax3.scatter([p_opt], [score_opt], color="black", zorder=5)
    ax3.annotate(
        f"$P^* = {p_opt:.1f}M$\nScore: {score_opt:.3f}",
        xy=(p_opt, score_opt),
        xytext=(p_opt + 0.8, score_opt * 0.8),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6),
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5)
    )

    # Layout e Salvataggio
    os.makedirs("./graphs", exist_ok=True)
    plt.tight_layout()
    plt.savefig("./graphs/analisi_prezzo_giocatore.png", dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Grafico salvato con successo! Prezzo consigliato: {p_opt:.1f}M")

if __name__ == "__main__":
    main()