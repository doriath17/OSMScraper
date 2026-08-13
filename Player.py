# # ['Haaland', '', 'ST', '26', 'Manchester City', '99', '18', '58', '99', '44.6M']

import math


MAX_PRICE_FACTOR = 2.5

class Player: 
    def __init__(self, name, position, age, nationality, club, attack, defense, overall, main_stat, market_value=0.0, base_value=0.0):
        self.name = name
        self.position = position
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

    def selling_price(self, matchday: int = 0) -> dict:
            max_price = self.max_price()

            # 1. Base Ratio in base al max_price e alla fase di stagione
            # 1. Base Ratio gestito direttamente tramite matchday
            if matchday == 0:  # Pre-stagione
                if max_price <= 10.0:
                    base_ratio = 1.0
                elif max_price <= 15.0:
                    base_ratio = 0.90
                elif max_price <= 24.0:
                    base_ratio = 0.80
                else:
                    base_ratio = 0.70
            else:  # Stagione in corso (matchday >= 1)
                season_discount = 0.0
                if matchday >= 30:
                    season_discount = 0.15
                elif matchday >= 22:
                    season_discount = 0.08
                elif matchday >= 12:
                    season_discount = 0.03

                if max_price <= 5.0:
                    base_ratio = 1.0
                elif max_price <= 12.0:
                    base_ratio = 0.90 - (season_discount * 0.5)
                elif max_price <= 18.0:
                    base_ratio = 0.80 - season_discount
                elif max_price <= 24.0:
                    base_ratio = 0.70 - season_discount
                else:
                    base_ratio = 0.60 - season_discount

            # 2. Modificatore Età (Decade con il progredire dei matchday)
            age_weight = max(0.0, 1.0 - (matchday / 32.0))
            age_mod = 0.0
            if self.age <= 21:
                raw_age_mod = +0.10 if max_price > 18.0 else +0.05
                age_mod = raw_age_mod * age_weight
            elif 22 <= self.age <= 25:
                age_mod = +0.03 * age_weight
            elif 29 <= self.age <= 32:
                age_mod = -0.05
            elif self.age >= 33:
                age_mod = -0.10

            # 3. Modificatore Rating / OVR (Aumenta d'importanza verso fine stagione)
            ovr_weight = 1.0 + (matchday / 35.0)
            ovr_mod = 0.0
            if self.overall >= 88:
                ovr_mod = +0.08 * ovr_weight
            elif self.overall >= 82:
                ovr_mod = +0.04 * ovr_weight
            elif self.overall <= 72:
                ovr_mod = +0.05 if matchday < 15 else -0.05

            # 4. Modificatore Ruolo
            pos_mod = 0.0
            position = getattr(self, 'position', '').upper()
            if position in ['FW', 'ATT']:
                pos_mod = +0.03
            elif position in ['GK', 'POR']:
                pos_mod = -0.05

            # 5. Calcolo finale e Clamp
            total_mod = age_mod + ovr_mod + pos_mod
            raw_final_ratio = base_ratio + total_mod
            final_ratio = min(1.0, max(0.45, raw_final_ratio))

            final_price = round(max_price * final_ratio, 1)

            return {
                "price": final_price,
                "max_price": max_price,
                "final_ratio": round(final_ratio, 3),
                "breakdown": {
                    "base_ratio": round(base_ratio, 3),
                    "age_modifier": round(age_mod, 3),
                    "ovr_modifier": round(ovr_mod, 3),
                    "pos_modifier": round(pos_mod, 3),
                }
            }

    def profit(self, matchday=0):
        return self.selling_price(matchday=matchday)["price"] - self.market_value

    def is_stricker(self) -> bool:
        return self.position in ["ST", "CF", "LW", "RW"]

    ## ======================================================
    # FUNZIONI PER LA PROBABILITA DI VENDITA
    ## ======================================================

    # Tende a 1 se il prezzo di vendita si avvicina al prezzo di base (piu facile da vendere)
    # Tende a 0 se il prezzo di vendita si avvicina al prezzo massimo (piu difficile da vendere) 
    def f_price(self, matchday=0) -> float:
        return 1 - (self.selling_price(matchday=matchday)["price"] - self.base_value) / (self.max_price() - self.base_value)

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

    W_INTERCEPT = -1.5 # Intercetta; Definisce la probabilità base di vendita in condizioni medie. 

    # Il peso di f_price; Maggiore è il peso, maggiore è l'influenza del prezzo sulla probabilità di vendita.
    # Impatto: Alto, circa 55% della probabilità di vendita è determinata dal prezzo.
    W_PRICE = 3.5 

    # Il peso di f_age; Maggiore è il peso, maggiore è l'influenza dell'età sulla probabilità di vendita.
    # Impatto: Medio, circa 20% della probabilità di vendita è determinata dall'età.
    W_AGE = 1.2 

    # Il peso di f_overall; Maggiore è il peso, maggiore è l'influenza dell'overall sulla probabilità di vendita.
    # Impatto: Basso, circa 10% della probabilità di vendita è determinata dall'overall.
    W_OVERALL = 0.6

    def z_score(self, matchday=0) -> float:
        return (Player.W_INTERCEPT +
            Player.W_PRICE * self.f_price(matchday=matchday) +
            Player.W_AGE * self.f_age() +
            Player.W_OVERALL * self.f_overall())

    # Questo valore indica la probabilità di vendita del giocatore in un singolo ciclo di mercato. 
    def prob_sale(self, matchday=0) -> float:
        z = self.z_score(matchday=matchday)
        return 1.0 / (1.0 + math.exp(-z))  # Sigmoid function to convert z to probability

    # questo e l indice primario con cui decidere se un giocatore è più o meno vendibile. 
    # Rispetto alla sola probabilita di vendita
    def exstimated_value(self, matchday=0) -> float:
        return self.profit(matchday=matchday) * (self.prob_sale(matchday=matchday) ** 2)

    # questo indice rappresenta il Return On Capital Employed (ROCE) del giocatore, ovvero il rapporto tra il valore stimato e il valore di mercato.
    # In pratica se per guadagnare ad esempio 2M ne devi bloccare 40M, il ROCE sarà 0.05 (5%), mentre se per guadagnare 2M ne devi bloccare solo 10M, il ROCE sarà 0.2 (20%).
    # Un ROCE più alto indica un investimento più efficiente, mentre un ROCE più basso indica un investimento meno efficiente. 
    # Il ROCE è utile per scegliere il miglior giocatore in base al capitale che sei disposto a bloccare. 
    def roce(self, matchday=0) -> float:
        ev = self.exstimated_value(matchday=matchday)
        if self.market_value == 0:
            return float('inf')  # Avoid division by zero; treat as infinite ROCE
        return ev / self.market_value

    def alpha(self, budget: float, operative_budget: float) -> float:
        """Calculate the alpha factor based on the ratio of operative budget to total budget."""
        if operative_budget == 0.0:
            operative_budget = 0.01  # Avoid division by zero
        return 1.0 / (1.0 + (budget / operative_budget))

    # Questo è lo score definitivo su cui si basa la scelta del giocatore da acquistare.
    # L'idea di questo indice è quella di favorire l'estimated value o il ROCE a seconda della disponibilità di budget.
    # Se il budget operativo è basso rispetto al budget totale, allora si favorisce il ROCE, altrimenti si favorisce l'estimated value. 
    # In pratica se hai poco budget operativo, conviene scegliere giocatori con un ROCE alto, mentre se hai molto budget operativo, conviene scegliere giocatori con un estimated value alto.  
    def score(self, matchday: int, budget: float, operative_budget: float) -> float:
        if self.market_value == 0:
            return float('inf')
        est_value = self.exstimated_value(matchday=matchday)
        alpha_exp = self.alpha(budget, operative_budget)
        return est_value * ((operative_budget / self.market_value) ** alpha_exp)


def to_number(value): 
    if value is None:
        raise ValueError("Value cannot be None")
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        clean_val = value.strip()
        
        if not clean_val:
            return None

        try:
            if clean_val.endswith("M"):
                return float(clean_val[:-1])
            elif clean_val.endswith("K"):
                return float(clean_val[:-1]) / 1000
            else:
                return float(clean_val)
        except ValueError:
            return None

    return float(value)

def get_selling_price(position, age, overall, base_value, matchday=1):
    player = Player(
        name="", position=position, age=age, nationality="", club="",
        attack=0, defense=0, overall=overall, main_stat=overall,
        market_value=0.0, base_value=base_value
    )
    return player.selling_price(matchday=matchday)