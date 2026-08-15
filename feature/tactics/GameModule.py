import math

from rich.console import Console

from GamePlan import GamePlan

console = Console() 



class GameModule:
    def __init__(self, code: str, defenders: int, midfielders: int, attackers: int, k_optimal: float, sigma: float, game_plan: GamePlan):
        """
        Inizializza una nuova istanza di un modulo di gioco (GameModule).

        :param code: Codice identificativo del modulo (es. "4-3-3A", "4-5-1").
        :param defenders: Numero di difensori schierati nella linea arretrata.
        :param midfielders: Numero di centrocampisti schierati.
        :param attackers: Numero di attaccanti schierati.
        :param k_optimal: Il valore di forza relativa (k_optimal in [0.0, 1.0]) in cui il modulo 
                        esprime il suo massimo rendimento tattico (k_optimal). 
                        I valori alti (>0.70) indicano moduli dominanti/offensivi, 
                        mentre valori bassi (<0.40) identificano moduli difensivi o di contenimento.
        :param sigma: Parametro di dispersione (tolleranza) della curva gaussiana d'affinità.
                    Determina la "flessibilità" del modulo al variare del Delta: un valore
                    di sigma contenuto rende il modulo efficace solo in un range stretto di k_optimal,
                    mentre un sigma più ampio definisce un modulo tatticamente versatile.
        :param game_plan: Stile di gioco primario idealmente associato al modulo 
                            (es. 'FASCE', 'TIKI_TAKA', 'CONTROPIEDE', 'TIRO_DA_FUORI'). 
                            Sancisce la compatibilità nativa tra l'assetto posizionale 
                            e la modalità di transizione della palla.
        """
        self.code = code
        self.defenders = defenders
        self.midfielders = midfielders
        self.attackers = attackers
        self.k_optimal = k_optimal
        self.sigma = sigma
        self.game_plan = game_plan

    def print(self):
        console.print(f"Code: {self.code}")
        console.print(f"k_optimal: {self.k_optimal}")
        console.print(f"Sigma: {self.sigma}")
        console.print(f"Game Plan: {self.game_plan.value_name}")

    def calculate_f_fit(self, k: float) -> float:
        """
        Misura quanto un modulo mod sia adatto alla forza relativa della tua squadra rispetto all'avversario.
        Modella una "curva gaussiana normalizzata".
        Il rendimento del modulo tocca il picco assoluto (1.0) quando k coincide perfettamente con il k_optimal del modulo, e decade gradualmente man mano che ci si allontana da questo punto ottimale, con una velocità regolata dal valore sigma.
            
        formula: f_fit(M, delta) = exp(-((k - k_optimal)^2) / (2 * sigma^2))
        - k: valore restituito dalla sigmoide in base al delta (vedi GameAnalyzer.get_k())
        - k_optimal: valore ottimale del modulo (dove il modulo rende al massimo)
        - sigma: deviazione standard che definisce la tolleranza del modulo al variare del delta. 
            - es. sigma circa 0.15 -> modulo molto specializzato (perde subito efficacia fuori dal suo range ottimale, es. 4-5-1 o 3-4-3B)
            - es. sigma circa 0.25 / 0.30 -> modulo versatile (mantiene una buona efficacia anche fuori dal suo range ottimale, es. 4-2-2A)

        :param k: Valore restituito dalla sigmoide in base al delta (vedi GameAnalyzer.get_k()).
        :return: Valore di adattamento del modulo al k specifico.
        """

        delta_k = k - self.k_optimal
        exponent = -(delta_k ** 2) / (2 * (self.sigma ** 2))
        return round(math.exp(exponent), 4)  # Arrotondato a 4 decimali per maggiore leggibilità


