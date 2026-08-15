import math

from rich.console import Console

from GameDifferentialAnalysis import GameDifferentialAnalysis

console = Console()

class GameOutcome:
    """
    Calcolatore delle probabilità di esito della partita (Vittoria, Pareggio, Sconfitta).
    
    Il modello trasforma l'indice di forza relativa k (dove k=0.5 è parità assoluta)
    in una distribuzione di probabilità utilizzando due curve matematiche distinte:
    1. Una distribuzione Gaussiana (a campana) per il Pareggio.
    2. Una funzione Logistica (Sigmoide) adattata per la Vittoria.
    """

    # =========================================================================
    # IPERPARAMETRI DEL MODELLO STATISTICO
    # =========================================================================
    # P_MAX_DRAW: Probabilità massima di pareggio quando le squadre sono identiche (k=0.5).
    # In OSM/calcio, un match perfettamente equilibrato ha circa il 30% di probabilità di X.
    MAX_DRAW_PROB = 0.30  
    
    # LAMBDA_DRAW: Controlla la "larghezza" della campana di pareggio.
    # Valori più alti fanno crollare le probabilità di X molto velocemente appena
    # una squadra diventa più forte. Valore 15.0 mantiene la X plausibile per piccoli scarti.
    DRAW_DECAY = 15.0 
    
    # ALPHA_WIN: Controlla la "ripidezza" della curva di vittoria.
    # Valori alti rendono il vantaggio marginale molto punitivo per l'avversario.
    WIN_STEEPNESS = 8.0

    def __init__(self, differential_analysis: GameDifferentialAnalysis, tactical_bonus: float = 0.0):
        """
        Inizializza le probabilità basandosi sull'analisi differenziale.
        
        :param differential_analysis: L'oggetto che contiene k e il delta OVR.
        :param tactical_bonus: Modificatore percentuale continuo (es. +0.05 per bonus casa/modulo perfetto).
                               Agisce traslando la curva logistica della vittoria.
        """
        self.p_draw = GameOutcome.calculate_draw_probability(
            differential_analysis.k
        )
        self.p_win = GameOutcome.calculate_win_probability(
            differential_analysis.k, self.p_draw, tactical_bonus
        )
        self.p_loss = 1.0 - self.p_win - self.p_draw

    def print(self):
        console.print("[bold]Match Outcome Probabilities:[/bold]")
        console.print(f"  [green]Win:[/green]  {self.p_win * 100:.1f}%")
        console.print(f"  [yellow]Draw:[/yellow] {self.p_draw * 100:.1f}%")
        console.print(f"  [red]Loss:[/red] {self.p_loss * 100:.1f}%")

    @staticmethod
    def calculate_draw_probability(k: float) -> float:
        """
        Calcola la probabilità di pareggio.
        
        EQUAZIONE:
        $$ P(Draw) = P_{max} \\cdot \\exp(-\\lambda \\cdot (k - 0.5)^2) $$

        INTERPRETAZIONE:
        Il pareggio è un evento di incertezza massima. La funzione Gaussiana centra 
        il picco (30%) esattamente a k=0.5. Essendo il termine (k - 0.5) elevato al quadrato, 
        la curva è simmetrica: la probabilità di pareggiare diminuisce alla stessa 
        velocità sia che tu sia molto più forte (k=0.8), sia che tu sia molto più debole (k=0.2).
        """
        return GameOutcome.MAX_DRAW_PROB * math.exp(
            -GameOutcome.DRAW_DECAY * ((k - 0.5) ** 2)
        )

    @staticmethod
    def calculate_win_probability(k: float, p_draw: float, tactical_bonus: float) -> float:
        """
        Calcola la probabilità di vittoria.
        
        EQUAZIONE RAW (Quota non-pareggio):
        $$ W_{raw} = \\frac{1}{1 + \\exp(-\\alpha \\cdot (k - 0.5 + \\beta))} $$
        Dove $\\alpha$ è WIN_STEEPNESS e $\\beta$ è tactical_bonus.
        
        EQUAZIONE FINALE:
        $$ P(Win) = (1 - P(Draw)) \\cdot W_{raw} $$

        INTERPRETAZIONE:
        Prima di calcolare chi vince, dobbiamo escludere la probabilità che la partita 
        finisca in parità (1 - P_Draw). Il restante blocco di probabilità viene conteso 
        tra le due squadre.
        La curva Logistica (W_raw) mappa il vantaggio (k - 0.5) in un range [0, 1].
        Se k=0.5 e bonus=0, W_raw = 0.5. Quindi P(Win) diventa esattamente la metà 
        dello spazio non-pareggio (es: se X è 30%, rimangono 70% di probabilità, divise 
        in 35% Vittoria e 35% Sconfitta). 
        Il tactical_bonus (beta) sposta l'intera curva artificialmente (es. neutralizzare 
        il modulo avversario ti comporta un vantaggio statistico come se k fosse più alto).
        """
        w_raw = 1.0 / (1.0 + math.exp(-GameOutcome.WIN_STEEPNESS * (k - 0.5 + tactical_bonus)))
        return (1.0 - p_draw) * w_raw