import math
from model.PlayerPosition import get_position
from model.PlayerRole import PlayerRole, get_role
import math


MAX_PRICE_FACTOR = 2.5

# # ['Haaland', '', 'ST', '26', 'Manchester City', '99', '18', '58', '99', '44.6M']
class Player: 
    def __init__(self, name, position, age, nationality, club, attack, defense, overall, main_stat, market_value=0.0, base_value=0.0):
        self.name = name
        self.position = get_position(position)
        self.role = get_role(self.position)
        self.age = age
        self.nationality = nationality
        self.club = club
        self.attack = attack
        self.defense = defense
        self.overall = overall
        self.main_stat = main_stat
        self.market_value: float = float(market_value)
        self.base_value: float = float(base_value)
        self.stats = (self.attack, self.defense, self.overall, self.main_stat)

    def __repr__(self):
        return (
            f"Player(name={self.name}, position={self.position}, age={self.age}, "
            f"nationality={self.nationality}, club={self.club}, attack={self.attack}, "
            f"defense={self.defense}, overall={self.overall}, main_stat={self.main_stat}, "
            f"market_value={self.market_value})"
        )

    def set_base_value(self, base_value):
        self.base_value = base_value

    def max_price(self) -> float:
        return self.base_value * MAX_PRICE_FACTOR

    """
FUNZIONI PER IL CALCOLO DEL PREZZO DI VENDITA

Siccome il prezzo di vendita, come visto viene influenzato da diversi fattori ed 
è alla base del calcolo della probabilità di vendita e dello score finale, 
l'algoritmo non può essere una semplice funzione lineare che applica delle 
regole fisse e spara fuori un valore, ma deve combinarsi con il modello della 
probabilità di vendita e dello score. 

L'idea fondamentale è che questo algoritmo cerca di indovinare il prezzo migliore 
a cui vendere un giocatore, cercando di massimizzare lo score. Questo equivale a 
dire che il prezzo finale favorisce la vendita rapida se hai poco budget op. e
devi ruotare velocemente il mercato per guadagnare; favorisce l'estimated value
se invece devi massimizzare il profitto, ad esempio quando hai tanto budget. 

L'algoritmo

Impatto del Capitale immobilizzato (C) rispetto al Budget Operativo (B_operativo)
sul fattore di penalizzazione: (B_operativo / C) ** alpha

Formulazione dello Score di Prezzo:

    Score(P) = EV(P) * (B_operativo / C) ** alpha(B, B_operativo)

    - P: prezzo di vendita

1. Capitale Alto / Vincolo di Liquidità (C > B_operativo):
   - Il fattore riduce drasticamente lo Score per prezzi elevati con P_sale incerta.
   - La curva dello Score sposta il picco verso prezzi vicini al valore base
     (P_sale più alta) per liberare rapidamente liquidità ed evitare il capital-lock.

2. Cassa Abbondante (C << B_operativo):
   - La penalizzazione del capitale diventa trascurabile (l'esponente alpha -> 0
     o il rapporto B_operativo/C cresce).
   - Il picco dello Score converge con il picco dell'EV puro.
   - Permette di fissare prezzi più alti (~2.5x base) per massimizzare il
     margine netto (Delta P).
"""
    def selling_price(self, budget: float, operative_budget: float, matchday: int = 0) -> dict:
        max_price = self.max_price()
        candidates = gen_prices_interval(self.base_value, max_price, step=0.1)

        # Genera per ogni prezzo candidato il dizionario dei dettagli
        evaluation_results = [
            (candidate_p, self.score(candidate_p, matchday, budget, operative_budget))
            for candidate_p in candidates
        ]

        # Trova il candidato con il 'final_score' massimo
        best_price, best_details = max(
            evaluation_results, 
            key=lambda item: item[1]["final_score"]
        )

        return {
            "price": round(best_price, 1),
            "score": best_details["final_score"],
            "details": best_details
        }

    def profit(self, candidate_p: float) -> float:
        return candidate_p - self.market_value

    def is_stricker(self) -> bool:
        return self.position in ["ST", "CF", "LW", "RW"]

    ## ======================================================
    # FUNZIONI PER LA PROBABILITA DI VENDITA
    ## ======================================================

    # Tende a 1 se il prezzo di vendita si avvicina al prezzo di base (piu facile da vendere)
    # Tende a 0 se il prezzo di vendita si avvicina al prezzo massimo (piu difficile da vendere) 
    def f_price(self, candidate_p: float) -> float:
        return 1 - (candidate_p - self.base_value) / (self.max_price() - self.base_value)

    MIN_AGE_TARGET = 18
    MAX_AGE_TARGET = 35

    # Tende a 1 se il giocatore è giovane (18 anni) e a 0 se il giocatore è vecchio (35 anni)
    # La funzione è lineare tra 18 e 35 anni
    def f_age(self) -> float:
        return max(0, (Player.MAX_AGE_TARGET - self.age) / (Player.MAX_AGE_TARGET - Player.MIN_AGE_TARGET))

    OVERALL_FACTOR_1 = 50
    OVERALL_FACTOR_2 = 100

    # Favorisce leggermente gli overall piu bassi/medi
    def f_overall(self) -> float:
        return 1 - (self.main_stat - Player.OVERALL_FACTOR_1) / (Player.OVERALL_FACTOR_2 - Player.OVERALL_FACTOR_1)

    LEAGUE_LENGTH = 38

    def f_matchday(self, matchday: int) -> float:
        return 1.0 - float(matchday) / Player.LEAGUE_LENGTH

    # restituisce il gradimento del mercato rispetto alla posizione
    def f_role(self) -> float: 
        match self.role:
            case PlayerRole.FORWARD: return 1.0
            case PlayerRole.MIDFIELD: return 0.5
            case PlayerRole.DEFENSE: return 0.5
            case PlayerRole.GOALKEEPER: return 0.0


    W_INTERCEPT = -1.8 # Intercetta; Definisce la probabilità base di vendita in condizioni medie. 

    # Il peso di f_price; Maggiore è il peso, maggiore è l'influenza del prezzo sulla probabilità di vendita.
    # Impatto: Alto, circa 50% della probabilità di vendita è determinata dal prezzo.
    W_PRICE = 3.8 

    # Il peso di f_age; Maggiore è il peso, maggiore è l'influenza dell'età sulla probabilità di vendita.
    # Impatto: Medio, circa 18% della probabilità di vendita è determinata dall'età.
    W_AGE = 1.2 

    # Il peso di f_overall; Maggiore è il peso, maggiore è l'influenza dell'overall sulla probabilità di vendita.
    # Impatto: Basso, circa 10% della probabilità di vendita è determinata dall'overall.
    W_OVERALL = 0.6

    # Il peso di f_matchday; Maggiore è il peso, maggiore è l'influenza del matchday sulla probabilità di vendita.
    # Impatto: Basso, circa 12% della probabilità di vendita è determinata dal matchday.
    W_MATCHDAY = 0.8

    # Il peso di f_pos; Maggiore è il peso, maggiore è l'influenza del ruolo sulla probabilità di vendita.
    # Impatto: Basso, circa 10% della probabilità di vendita è determinata dal ruolo.
    W_ROLE = 0.4 

    def z_score(self, candidate_p: float, matchday=0) -> float:
        return (Player.W_INTERCEPT +
            Player.W_PRICE * self.f_price(candidate_p) +
            Player.W_AGE * self.f_age() +
            Player.W_OVERALL * self.f_overall() + 
            Player.W_MATCHDAY * self.f_matchday(matchday) + 
            Player.W_ROLE * self.f_role())

    # Questo valore indica la probabilità di vendita del giocatore in un singolo ciclo di mercato. 
    def prob_sale(self, candidate_p: float, matchday=0) -> dict:
        z = self.z_score(candidate_p, matchday=matchday)
        result = 1.0 / (1.0 + math.exp(-z))  # Sigmoid function to convert z to probability
        return {
            "prob_sale": result,
            "z_score": z
        }

    # questo e l indice primario con cui decidere se un giocatore è più o meno vendibile. 
    # Rispetto alla sola probabilita di vendita tiene conto anche di quanto 
    # tempo (calcolato in cicli di mercato) ci impiega l'engine del gioco a comprare 
    # il giocatore dalla lista. 
    # Quindi mentre la prob_sale determina la prob di vendita su un singolo ciclo, 
    # questo indice rappresenta quanto 'vale' il giocatore ad ogni ciclo di mercato. 
    def exstimated_value(self, candidate_p: float, matchday=0) -> float:
        return self.profit(candidate_p) * (self.prob_sale(candidate_p, matchday=matchday)["prob_sale"] ** 2)

    # questo indice rappresenta il Return On Capital Employed (ROCE) del giocatore, ovvero il rapporto tra il valore stimato e il valore di mercato.
    # In pratica se per guadagnare ad esempio 2M ne devi bloccare 40M, il ROCE sarà 0.05 (5%), mentre se per guadagnare 2M ne devi bloccare solo 10M, il ROCE sarà 0.2 (20%).
    # Un ROCE più alto indica un investimento più efficiente, mentre un ROCE più basso indica un investimento meno efficiente. 
    # Il ROCE è utile per scegliere il miglior giocatore in base al capitale che sei disposto a bloccare. 
    def roce(self, candidate_p: float, matchday=0) -> float:
        ev = self.exstimated_value(candidate_p, matchday=matchday)
        if self.market_value == 0:
            return float('inf')  # Avoid division by zero; treat as infinite ROCE
        return ev / self.market_value

    def alpha(self, budget: float, operative_budget: float) -> float:
        """
        Ritorna un valore tra 0 e 1:
        - Tende a 1 se c'è molta cassa residua (privilegia EV -> Prezzi alti)
        - Tende a 0 se la cassa è risicata (privilegia ROCE -> Prezzi bassi e vendite veloci)
        """
        if budget <= 0:
            return 0.0
        return operative_budget / budget

    # Questo è lo score definitivo su cui si basa la scelta del giocatore da acquistare.
    # L'idea di questo indice è quella di favorire l'estimated value o il ROCE a seconda della disponibilità di budget.
    # Se il budget operativo è basso rispetto al budget totale, allora si favorisce il ROCE, altrimenti si favorisce l'estimated value. 
    # In pratica se hai poco budget operativo, conviene scegliere giocatori con un ROCE alto, mentre se hai molto budget operativo, conviene scegliere giocatori con un estimated value alto (non ti interessa quanto a lungo il giocatore stia sul mercato, vuoi solo aumentare i profitti).  
    #
    # NOTE: se vuoi vendere un giocatore rapidamente devi puntare ad aumentare questa
    # prob e al contrario, se vuoi massimizzare il profitto anche bloccando slot e 
    # denaro per diverso tempo, puoi favorire un estimated value piu alto (a discapito
    # della prob di vendita). Siccome basi questa scelta in base al budget e al budget 
    # operativo, lo score tendera al roce o all'estimated value per essere il piu 
    # efficiente possibile. 
    def score(self, candidate_p: float, matchday: int, budget: float, operative_budget: float) -> dict:
            if self.market_value == 0:
                return {
                    "profit": 0.0,
                    "z_score": 0.0,
                    "p_sale": 0.0,
                    "ev": 0.0,
                    "roce": float('inf'),
                    "capital_risk": 0.0,
                    "final_score": float('inf')
                }

            profit = self.profit(candidate_p)
            if profit <= 0:
                return {
                    "profit": profit,
                    "z_score": 0.0,
                    "p_sale": 0.0,
                    "ev": 0.0,
                    "roce": 0.0,
                    "capital_risk": 0.0,
                    "final_score": -1.0
                }

            p_sale = self.prob_sale(candidate_p, matchday=matchday)
            ev = self.exstimated_value(candidate_p, matchday=matchday)
            roce_val = self.roce(candidate_p, matchday=matchday)

            # Calcolo dinamico del rischio di cassa
            alpha_weight = min(1.0, max(0.0, operative_budget / (budget if budget > 0 else 0.01)))
            cap_ratio = self.market_value / (operative_budget if operative_budget > 0 else 0.01)
            capital_risk = (1.0 - alpha_weight) * math.log1p(cap_ratio)

            # Score finale basato sull'accelerazione della liquidità
            final_score = ev * (p_sale["prob_sale"] ** capital_risk)

            return {
                "profit": round(profit, 2),
                "z_score": round(p_sale["z_score"], 4),
                "p_sale": round(p_sale["prob_sale"], 4),
                "ev": round(ev, 4),
                "roce": round(roce_val, 4) if roce_val != float('inf') else float('inf'),
                "capital_risk": round(capital_risk, 4),
                "final_score": round(final_score, 4)
            }


    # def score(self, candidate_p: float, matchday: int, budget: float, operative_budget: float) -> float:
    #     if self.market_value == 0:
    #         return float('inf')

    #     ev = self.exstimated_value(candidate_p, matchday=matchday)
    #     roce_val = self.roce(candidate_p, matchday=matchday)
        
    #     a = self.alpha(budget, operative_budget)

    #     # Mix dinamico tra EV puro e ROCE
    #     # Nota: poichè EV e ROCE hanno scale diverse (milioni vs percentuale), 
    #     # scaliamo il ROCE moltiplicandolo per un capitale di riferimento
    #     return a * ev + (1 - a) * (roce_val * self.market_value)

def gen_prices_interval(base: float, max: float, step: float = 0.1) -> list[float]:
    prices = []
    current_price = base
    while current_price <= max:
        prices.append(round(current_price, 2))
        current_price += step
    return prices

# def get_selling_price(position, age, overall, base_value, matchday=1):
#     player = Player(
#         name="", position=position, age=age, nationality="", club="",
#         attack=0, defense=0, overall=overall, main_stat=overall,
#         market_value=0.0, base_value=base_value
#     )
#     return player.selling_price(matchday=matchday)