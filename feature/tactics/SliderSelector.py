from dataclasses import dataclass

from rich.console import Console

from GameDifferentialAnalysis import GameDifferentialAnalysis

console = Console()

class GameSliderSelector:

    def __init__(self, differential_analysis: GameDifferentialAnalysis):
        self.pressure = GameSliderSelector.get_pressure(differential_analysis.k)
        self.style = GameSliderSelector.get_style(differential_analysis.k)
        self.tempo = GameSliderSelector.get_tempo(differential_analysis.k)

    def print(self):
        console.print(f"[bold]Pressure:[/bold] {self.pressure}")
        console.print(f"[bold]Style:[/bold] {self.style}")
        console.print(f"[bold]Tempo:[/bold] {self.tempo}")

    @staticmethod
    def get_style(k: float, min_style: int = 25, max_style: int = 80) -> int:
        style = min_style + k * (max_style - min_style)
        return round(style)

    @staticmethod
    def get_pressure(k: float, min_pressure: int = 25, max_pressure: int = 75) -> int:
        pressure = min_pressure + k * (max_pressure - min_pressure)
        return round(pressure)

    
    @staticmethod
    def get_tempo(k: float, t_base: float = 50.0, max_boost: float = 40.0, eta: float = 0.75) -> int: # Definisce il calcolo del Tempo tramite scostamento da k.
        deviation = abs(k - 0.5) # Calcola la distanza assoluta tra k e il punto neutro 0.50.
        return round(t_base + max_boost * (deviation ** eta)) # Restituisce il valore del Tempo arrotondato all'intero più vicino.

    # ==============================================================================
    # DOCUMENTAZIONE DEL MODELLO E SPIEGAZIONE DELLA SCELTA
    # ==============================================================================
    #
    ## SLIDER
    #
    # Clamp: the clamp represents the minimum and maximum value that a function can return.
    # 
    # STYLE
    # formula: Style(delta) = min + k * (max - min)
    # - k: fattore forza relativa calcolato con un 'sigmoide' $$k = \frac{1}{1 + e^{-\lambda \cdot \Delta}}$$
    #   oscilla tra 0 e 1 e indica quanto puoi permetterti di essere aggressivo o difensivo in base al delta.
    # - 25 soglia minima siccome al di sotto hai uno stile di gioco troppo difensivo
    # - 80 soglia massima siccome al di sopra hai uno stile di gioco troppo aggressivo
    # - 50 soglia di partenza, rappresenta un bilanciamento (ricercato quando il delta è vicino a 0) tra difesa e attacco
    #
    # PRESSURE
    # formula: Pressure(delta) = min + k * (max - min)
    # NOTE: depending on the value of k, the pressure and style curves will change to be more or less steep. The lambda parameter controls the steepness of the curve, allowing for fine-tuning of the pressure and style adjustments based on the delta value.
    #
    # TEMPO
    # Per il calcolo del Tempo (Velocità di Passaggio) è stato scelto l'APPROCCIO 2
    # basato sulla deviazione assoluta del fattore k_1 dal punto di equilibrio (0.50).
    #
    # MOTIVAZIONE DELLA SCELTA:
    # In OSM, sia in forte svantaggio (difesa/contropiede) sia in forte vantaggio
    # (dominio/attacco di prima), serve una velocità di passaggio elevata. In fase di
    # equilibrio, invece, si preferisce un ritmo medio/costruttivo per il possesso.
    #
    # VANTAGGI DELL'APPROCCIO 2:
    # 1. COERENZA MATEMATICA: Utilizza k_1 come unica sorgente di verità condivisa
    #    per tutti e 3 gli slider (Stile, Pressing, Tempo).
    # 2. FLUIDITÀ SENZA IF/ELSE: Non richiede condizionali rigidi o clamping manuale,
    #    sfruttando la convergenza naturale della sigmoide.
    # 3. REATTIVITÀ DINAMICA: Con un esponente eta = 0.75, la risposta del ritmo è
    #    immediata appena ci si allontana dallo zero, garantendo transizioni veloci.
    #
    # TABELLA DELL'ANDAMENTO GENERATO (con eta = 0.75, T_base = 50, T_max_diff = 40):
    # ------------------------------------------------------------------------------
    # Delta   | k_1    | |k_1 - 0.5| | Stile (S) | Pressing (P) | Tempo (T) | Stato
    # ------------------------------------------------------------------------------
    # -16.0   | 0.128  | 0.372       | 31.4      | 35.8         | 68.6      | Def. Forte
    # -12.0   | 0.192  | 0.308       | 34.6      | 38.6         | 66.2      | Defensivo
    #  -4.0   | 0.382  | 0.118       | 44.1      | 47.2         | 58.0      | Svant. Lieve
    #   0.0   | 0.500  | 0.000       | 50.0      | 52.5         | 50.0      | Equilibrio
    #  +4.0   | 0.618  | 0.118       | 55.9      | 57.8         | 58.0      | Vant. Lieve
    # +12.0   | 0.808  | 0.308       | 65.4      | 66.4         | 66.2      | Offensivo
    # +16.0   | 0.872  | 0.372       | 68.6      | 69.2         | 68.6      | Off. Forte
    # ==============================================================================


    # $$T(k_1) = T_{\text{base}} + 40 \cdot \vert{}k_1 - 0.5\vert{}^\eta$$Se $\eta = 1.0$, la crescita è lineare rispetto alla deviazione.Se $\eta < 1.0$ (es. $0.7$), il tempo sale molto più velocemente appena ci si allontana dall'equilibrio (utile per garantire che in svantaggio si passi subito a ritmi di contropiede alti $\ge 68$).$\Delta = 0 \implies k_1 = 0.50 \implies T = 55$$\Delta = -12 \implies k_1 = 0.19 \implies \vert{}0.19 - 0.50\vert{} = 0.31 \implies T \approx 72$$\Delta = +12 \implies k_1 = 0.81 \implies \vert{}0.81 - 0.50\vert{} = 0.31 \implies T \approx 72$Pro: Mantiene la coerenza matematica dell'intero modello basandosi esclusivamente sul fattore $k_1$.

