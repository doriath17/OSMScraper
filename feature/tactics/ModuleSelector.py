from dataclasses import dataclass

from rich.console import Console

from GameDifferentialAnalysis import GameDifferentialAnalysis
from GameModule import GameModuleType, GamePlan

console = Console()

@dataclass(frozen=True)
class ModuleScore:
    """Rappresenta il punteggio di un modulo candidato e il relativo breakdown."""
    module: GameModuleType
    score: float
    breakdown: dict[str, float]

class ModuleSelector: 

    def __init__(self, differential_analysis: GameDifferentialAnalysis):
        self.f_fit = differential_analysis.player.module.value.calculate_f_fit(differential_analysis.k)
        self.g_counter = ModuleSelector.calculate_g_counter(differential_analysis.player.module, differential_analysis.opponent.module)
        self.p_risk = ModuleSelector.calculate_p_risk(differential_analysis.k, differential_analysis.player.module, differential_analysis.opponent.module)
        self.h = ModuleSelector.calculate_h(differential_analysis.k, differential_analysis.player.module, differential_analysis.opponent.module)
        self.top_modules = ModuleSelector.select_top_modules(differential_analysis.k, differential_analysis.opponent.module, top_n=5)

    def print(self):
        console.print(f"[bold]f_fit:[/bold] {self.f_fit:.4f}, weighted: {self.h[1]['f_fit_weighted']:.2f}")
        console.print(f"[bold]g_counter:[/bold] {self.g_counter:.2f}, weighted: {self.h[1]['g_counter_weighted']:.2f}")
        console.print(f"[bold]p_risk:[/bold] {self.p_risk:.2f}, weighted: {self.h[1]['p_risk_weighted']:.2f}")
        console.print(f"[bold]h:[/bold] {self.h[0]:.2f}")
        console.print("\n[bold underline]Top 5 Modules[/bold underline]")
        for idx, module_score in enumerate(self.top_modules, start=1):
            console.print(f"{idx}. [bold]{module_score.module.value.code}[/bold] - Score: {module_score.score:.2f}")
            console.print(f"   Breakdown: f_fit={module_score.breakdown['f_fit_raw']:.4f}, g_counter={module_score.breakdown['g_counter_raw']:.2f}, p_risk={module_score.breakdown['p_risk_raw']:.2f}")

    W_MID = 1.2 # Peso scalare per il differenziale di centrocampo (default: 1.2)
    W1_FIT = 10.0
    W2_COUNTER = 1.0
    W3_RISK = 1.5

    @staticmethod
    def calculate_g_counter(candidate_module: GameModuleType, opponent_module: GameModuleType) -> float:
        """
        Calcola il punteggio analitico di controtattica g_counter(M, M_adv).

        Il modello mappa lo scontro tattico tra il modulo utente (M) e il modulo
        avversario (M_adv) sovrapponendo 4 sottosistemi di valutazione:
        
        1. Differenziale di Centrocampo  ->  Delta_{mid} = w_{mid} * (M_{mid} - M_{adv, mid})
        2. Margine Difensivo Strutturato ->  Delta_{def} = f(M_{def} - M_{adv, att})
        3. Affinity Matrix degli Stili   ->  Phi_{style}(S_M, S_{adv})
        4. Operatore di Saturazione      ->  Psi_{density}(M, M_{adv})

        :return: Punteggio complessivo di controtattica (range orientativo: [-5.0, +10.0]).
        """
        # Estrazione delle strutture dati interne dal valore dell'Enum
        my = candidate_module.value
        adv = opponent_module.value

        # =========================================================================
        # 1. DIFFERENZIALE DI CENTROCAMPO (\Delta_{mid})
        # =========================================================================
        # In OSM il centrocampo determina la percentuale di possesso palla e la
        # frequenza di generazione delle occasioni da rete.
        # Equazione: \Delta_{mid} = w_{mid} \cdot (midfielders_M - midfielders_{M_adv})
        mid_diff: int = my.midfielders - adv.midfielders
        score_mid: float = mid_diff * ModuleSelector.W_MID

        # =========================================================================
        # 2. COPERTURA DIFENSIVA SU ATTACCO AVVERSARIO (\Delta_{def})
        # =========================================================================
        # Calcola la capacità della linea difensiva di assorbire la pressione dell'attacco
        # avversario. La condizione ideale su OSM è la superiorità numerica esatta di +1 
        # (uomo libero di raddoppiare o impostare).
        #
        # Equazione della funzione a scaglioni f(d):
        #               ┌ +1.5  se  d = 1  (Rapporto ideale: uomo libero + marcatura)
        #   \Delta_{def}│ +0.5  se  d >= 2 (Copertura ultra-solida, leggero spreco di uomini)
        #               │ -0.5  se  d = 0  (Parità numerica: rischio duelli individuali)
        #               └ -2.5  se  d < 0  (Sotto-numerosità grave: buchi difensivi)
        def_margin: int = my.defenders - adv.attackers

        if def_margin == 1:
            score_def = 1.5
        elif def_margin >= 2:
            score_def = 0.5
        elif def_margin == 0:
            score_def = -0.5
        else:  # def_margin < 0
            score_def = -2.5

        # =========================================================================
        # 3. MATCHUP DEGLI STILI DI GIOCO (\Phi_{style})
        # =========================================================================
        # Modellazione delle controtattiche nativamente efficaci nel motore di gioco.
        # Mappa le interazioni tra lo stile del modulo M (S_M) e quello di M_adv (S_adv).
        my_style: GamePlan = my.game_plan
        adv_style: GamePlan = adv.game_plan
        score_style: float = 0.0

        # Case A: SHOOT_ON_SIGHT vs WING_PLAY
        # Il tiro da fuori blocca la ragnatela di passaggi esterni e punisce la perdita di palla.
        if my_style == GamePlan.SHOOT_ON_SIGHT and adv_style == GamePlan.WING_PLAY:
            score_style += 2.0

        # Case B: COUNTER_ATTACK vs WING_PLAY / LONG_BALL
        # Il contropiede sfrutta lo sbilanciamento e le transizioni sulle seconde palle.
        elif my_style == GamePlan.COUNTER_ATTACK and adv_style in (GamePlan.WING_PLAY, GamePlan.LONG_BALL):
            score_style += 2.0

        # Case C: WING_PLAY vs PASSING_GAME
        # Il gioco sulle ali allarga le maglie del Tiki-Taka centrale costringendolo a correre a vuoto.
        elif my_style == GamePlan.WING_PLAY and adv_style == GamePlan.PASSING_GAME:
            score_style += 1.5

        # Case D: PASSING_GAME vs SHOOT_ON_SIGHT
        # Il possesso palla prolungato riduce le transizioni avversarie e neutralizza i tiri da fuori.
        elif my_style == GamePlan.PASSING_GAME and adv_style == GamePlan.SHOOT_ON_SIGHT:
            score_style += 1.0

        # =========================================================================
        # 4. OPERATORE DI SATURAZIONE SUI TRIDENTI (\Psi_{density})
        # =========================================================================
        # Se l'avversario schiera 3 attaccanti (es. 4-3-3, 3-4-3), la saturazione della
        # propria metà campo tramite un blocco a 5 (centrocampo o difesa) spezza i flussi
        # di rifornimento alle ali.
        #
        # Equazione:
        #                 ┌ +2.5  se  attackers_{adv} = 3 AND (midfielders_M >= 5 OR defenders_M >= 5)
        # \Psi_{density} =│
        #                 └ 0.0   altrimenti
        score_density: float = 0.0
        if adv.attackers == 3 and (my.midfielders >= 5 or my.defenders >= 5):
            score_density += 2.5

        # =========================================================================
        # COMPOSIZIONE FINALE DEL PUNTEGGIO
        # =========================================================================
        # g_counter = \Delta_{mid} + \Delta_{def} + \Phi_{style} + \Psi_{density}
        total_g_counter: float = score_mid + score_def + score_style + score_density

        return round(total_g_counter, 2)

    @staticmethod
    def calculate_p_risk(k: float, candidate_module: GameModuleType, opponent_module: GameModuleType) -> float:
        """
        Calcola la penalità di rischio strutturale e sbilanciamento p_risk(M, M_adv, k1).

        La funzione applica penalizzazioni negative (<= 0.0) quando il modulo scelto (M)
        presenta fragilità tattiche intrinseche contro M_adv che non sono compensate da
        una forza relativa (k1) sufficientemente alta.

        Componenti del modello:
        1. Esposizione sulle Ali (Omega_{wing_exposure}): Difesa a 3 contro attacco a 3 ali.
        2. Crollo della Mediana (Omega_{mid_collapse}): Inferiorità >= 2 uomini a centrocampo.
        3. Presunzione Tattica (Omega_{overreach}): Moduli iper-offensivi usati con k1 basso.

        :return: Valore di penalità negativo o nullo (range tipico: [-8.0, 0.0]).
        """
        my = candidate_module.value
        adv = opponent_module.value

        # =========================================================================
        # 1. RISCHIO ESPOSIZIONE SULLE CORSIE ESTERNE (\Omega_{wing_exposure})
        # =========================================================================
        # Giocare con la difesa a 3 (defenders <= 3) contro moduli con 3 attaccanti (es. 4-3-3, 3-4-3)
        # lascia le fasce prive di raddoppi. Se k1 non è nettamente dominante (k1 < 0.65),
        # il rischio di subire imbucate laterali scala quadraticamente col divario di forza.
        #
        # Equazione:
        #                          ┌ -3.0 \cdot (0.65 - k1)  se defenders_M <= 3 AND attackers_{adv} == 3 AND k1 < 0.65
        # \Omega_{wing_exposure} = │
        #                          └ 0.0                     altrimenti
        penalty_wing: float = 0.0
        if my.defenders <= 3 and adv.attackers == 3:
            if k < 0.65:
                # La penalità aumenta quanto più k1 scende sotto la soglia di sicurezza di 0.65
                penalty_wing = -3.5 * (0.65 - k)

        # =========================================================================
        # 2. RISCHIO CROLLO DELLA MEDIANA (\Omega_{mid_collapse})
        # =========================================================================
        # Schierare solo 2 centrocampisti (es. 4-2-4, 5-2-3, 3-2-5) contro centrocampi folti
        # (>= 4 centrocampisti) porta all'isolamento dei reparti. Il motore di OSM punisce
        # severamente la perdita della mediana se non si ha una rosa nettamente superiore (k1 >= 0.70).
        #
        # Equazione:
        #                        ┌ -4.0 \cdot (0.70 - k1)  se midfielders_M <= 2 AND midfielders_{adv} >= 4 AND k1 < 0.70
        # \Omega_{mid_collapse} =│
        #                        └ 0.0                     altrimenti
        penalty_mid: float = 0.0
        if my.midfielders <= 2 and adv.midfielders >= 4:
            if k < 0.70:
                penalty_mid = -4.0 * (0.70 - k)

        # =========================================================================
        # 3. RISCHIO PRESUNZIONE / OVERREACH TATTICO (\Omega_{overreach})
        # =========================================================================
        # Schierare moduli iper-offensivi (k1_optimal >= 0.75, come 4-3-3, 3-4-3, 4-2-4, 3-2-5)
        # quando la squadra è inferiore o pari all'avversario (k1 < 0.50) crea uno sbilanciamento
        # sistemico.
        #
        # Equazione:
        #                    ┌ -5.0 \cdot (0.50 - k1)  se k1_{optimal, M} >= 0.75 AND k1 < 0.50
        # \Omega_{overreach} =│
        #                    └ 0.0                     altrimenti
        penalty_overreach: float = 0.0
        if my.k_optimal >= 0.75 and k < 0.50:
            penalty_overreach = -5.0 * (0.50 - k)

        # =========================================================================
        # COMPOSIZIONE FINALE DELLA PENALITÀ
        # =========================================================================
        # p_risk = \Omega_{wing_exposure} + \Omega_{mid_collapse} + \Omega_{overreach}
        total_p_risk: float = penalty_wing + penalty_mid + penalty_overreach

        return round(total_p_risk, 2)

    @staticmethod
    def calculate_h(k: float, candidate_module: GameModuleType, opponent_module: GameModuleType) -> tuple[float, dict[str, float]]:
        """
        Valuta la funzione di idoneità complessiva h per un singolo modulo candidato.

        Equazione:
        h(M) = w1 * f_fit(M, k1) + w2 * g_counter(M, M_adv) + w3 * p_risk(M, M_adv, k1)

        :return: Tupla contenente (punteggio_h_totale, dizionario_breakdown).
        """

        # 1. Calcolo affinità per la forza relativa (f_fit)
        # Utilizza il metodo nativo del modulo basato sulla curva gaussiana
        f_fit = candidate_module.value.calculate_f_fit(k)
        
        # 2. Calcolo vantaggio di controtattica sui reparti (g_counter)
        g_counter = ModuleSelector.calculate_g_counter(candidate_module, opponent_module)

        # 3. Calcolo penalità di rischio strutturale (p_risk)
        p_risk = ModuleSelector.calculate_p_risk(k, candidate_module, opponent_module)

        # Somma algebrica pesata delle componenti
        score_fit_weighted = ModuleSelector.W1_FIT * f_fit
        score_counter_weighted = ModuleSelector.W2_COUNTER * g_counter
        score_risk_weighted = ModuleSelector.W3_RISK * p_risk

        total_h = score_fit_weighted + score_counter_weighted + score_risk_weighted

        breakdown = {
            "f_fit_raw": round(f_fit, 4),
            "f_fit_weighted": round(score_fit_weighted, 2),
            "g_counter_raw": round(g_counter, 2),
            "g_counter_weighted": round(score_counter_weighted, 2),
            "p_risk_raw": round(p_risk, 2),
            "p_risk_weighted": round(score_risk_weighted, 2)
        }

        return round(total_h, 2), breakdown

    @staticmethod
    def select_best_module(k: float, candidate_module: GameModuleType, opponent_module: GameModuleType) -> GameModuleType:
        """
        Itera su tutti i moduli presenti nell'enum GameModuleType e seleziona
        il modulo M* che massimizza la funzione di scoring h.

        :return: Modulo ottimale (GameModuleType) che massimizza la funzione di scoring h.
        """
        best_module: GameModuleType = GameModuleType.M_442A
        best_score: float = -float('inf')
        best_breakdown: dict[str, float] = {}

        # Algoritmo di ricerca esaustiva sull'insieme discreto dei moduli
        for candidate_module in GameModuleType:
            score_h, breakdown = ModuleSelector.calculate_h(k, candidate_module, opponent_module)

            if score_h > best_score:
                best_score = score_h
                best_module = candidate_module
                best_breakdown = breakdown

        return best_module

    @staticmethod
    def select_top_modules(
        k: float, 
        opponent_module: GameModuleType, 
        top_n: int = 5
    ) -> list[ModuleScore]:
        """
        Itera su tutti i moduli presenti nell'enum GameModuleType, calcola la funzione 
        di scoring h per ciascuno e restituisce i primi N moduli ordinati per punteggio decrescente.

        :param k: Forza relativa della squadra in [0.0, 1.0].
        :param opponent_module: Modulo schierato dall'avversario M_adv.
        :param top_n: Numero di moduli top da restituire (default: 5).
        :return: Lista ordinata di oggetti ModuleScore (dal migliore al peggiore).
        """
        candidates: list[ModuleScore] = []

        # 1. Calcolo dello score per ogni modulo candidato
        for candidate_module in GameModuleType:
            score_h, breakdown = ModuleSelector.calculate_h(k, candidate_module, opponent_module)
            candidates.append(
                ModuleScore(
                    module=candidate_module,
                    score=score_h,
                    breakdown=breakdown
                )
            )

        # 2. Ordinamento decrescente in base a score_h
        candidates.sort(key=lambda x: x.score, reverse=True)

        # 3. Restituzione dei primi top_n moduli
        return candidates[:top_n]
